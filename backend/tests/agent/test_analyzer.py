import boto3
import pytest
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    NoCredentialsError,
    ProfileNotFound,
)
from botocore.stub import Stubber
from pydantic import ValidationError
from strands.models import BedrockModel
from strands.types.exceptions import (
    ContextWindowOverflowException,
    MaxTokensReachedException,
    ModelThrottledException,
    StructuredOutputException,
)

from app.agent.analyzer import (
    AnalysisError,
    AnalysisUnavailable,
    StrandsBedrockAnalyzer,
    bedrock_status,
    build_prompt,
    map_exception,
)
from app.agent.evidence import bundle_from_state
from app.agent.report import IncidentAnalysis
from app.config import Mode, Settings
from app.simulation.evidence import get_evidence


def bundle():
    return bundle_from_state(get_evidence("sim-alb-503"), Mode.SIMULATION)


def client_error(code, msg="m"):
    return ClientError({"Error": {"Code": code, "Message": msg}}, "Converse")


def test_prompt_contains_every_evidence_item_and_guards_injection():
    b = bundle()
    p = build_prompt(b, None)
    for i in b.items:
        assert i.id in p and i.text in p
    assert "<evidence>" in p and "</evidence>" in p
    assert "Routing note" not in p


@pytest.mark.parametrize(
    "exc,cls,retryable",
    [
        (NoCredentialsError(), AnalysisUnavailable, False),
        (ProfileNotFound(profile="x"), AnalysisUnavailable, False),
        (ModelThrottledException("t"), AnalysisUnavailable, True),
        (EndpointConnectionError(endpoint_url="u"), AnalysisUnavailable, True),
        (ConnectTimeoutError(endpoint_url="u"), AnalysisUnavailable, True),
        (client_error("AccessDeniedException"), AnalysisUnavailable, False),
        (client_error("ResourceNotFoundException"), AnalysisUnavailable, False),
        (client_error("ThrottlingException"), AnalysisUnavailable, True),
        (client_error("ServiceUnavailableException"), AnalysisUnavailable, True),
        (client_error("SomethingElse"), AnalysisError, None),
        (StructuredOutputException("x"), AnalysisError, None),
        (MaxTokensReachedException("x"), AnalysisError, None),
        (ContextWindowOverflowException("x"), AnalysisError, None),
        (RuntimeError("boom"), AnalysisError, None),
    ],
)
def test_map_exception(exc, cls, retryable):
    out = map_exception(exc)
    assert isinstance(out, cls)
    if retryable is not None:
        assert out.retryable is retryable


def test_validation_error_maps_to_analysis_error():
    try:
        IncidentAnalysis.model_validate({})
    except ValidationError as e:
        assert isinstance(map_exception(e), AnalysisError)


def test_real_strands_path_without_credentials_is_unavailable(monkeypatch, tmp_path):
    """No stub: the real Strands + botocore stack with no credentials available."""
    for k in list(__import__("os").environ):
        if k.startswith("AWS_"):
            monkeypatch.delenv(k)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "none"))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "none2"))
    a = StrandsBedrockAnalyzer("any-model", "us-east-1")
    with pytest.raises(AnalysisUnavailable) as ei:
        a.analyze(bundle(), None)
    assert "credentials" in str(ei.value).lower()


PAYLOAD = {
    "summary": "s",
    "confirmed_facts": [{"statement": "x", "evidence_ids": ["E1"]}],
    "hypotheses": [],
    "probable_root_causes": [],
    "recommended_actions": [],
    "impact_assessment": "Not determinable from the available evidence.",
    "evidence_gaps": [],
}


def stubbed_factory(response=None, error=None):
    """TEST DOUBLE of Amazon Bedrock's HTTP reply (botocore Stubber on the real Strands model).
    Verifies our wiring (structured output parsing), not Bedrock's behaviour."""

    def factory():
        sess = boto3.Session(
            aws_access_key_id="testing", aws_secret_access_key="testing", region_name="us-east-1"
        )
        m = BedrockModel(model_id="test-model", streaming=False, boto_session=sess)
        st = Stubber(m.client)
        if error:
            st.add_client_error("converse", service_error_code=error)
        else:
            st.add_response(
                "converse",
                {
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "toolUse": {
                                        "toolUseId": "t1",
                                        "name": "IncidentAnalysis",
                                        "input": response,
                                    }
                                }
                            ],
                        }
                    },
                    "stopReason": "tool_use",
                    "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                    "metrics": {"latencyMs": 1},
                },
            )
        st.activate()
        return m

    return factory


def test_strands_structured_output_is_parsed_from_a_stubbed_converse_reply():
    a = StrandsBedrockAnalyzer("test-model", "us-east-1", model_factory=stubbed_factory(PAYLOAD))
    out = a.analyze(bundle(), None)
    assert out.analysis.confirmed_facts[0].evidence_ids == ["E1"]
    assert out.model_id == "test-model" and out.latency_ms >= 0


def test_strands_access_denied_is_unavailable():
    a = StrandsBedrockAnalyzer(
        "test-model", "us-east-1", model_factory=stubbed_factory(error="AccessDeniedException")
    )
    with pytest.raises(AnalysisUnavailable):
        a.analyze(bundle(), None)


def test_bedrock_status_requires_model_id(monkeypatch):
    ok, detail = bedrock_status(Settings(bedrock_model_id=""))
    assert not ok and "BEDROCK_MODEL_ID" in detail


@pytest.mark.live_bedrock
def test_live_bedrock_roundtrip():
    """Real Bedrock call. Skipped unless INCIDENTPILOT_BEDROCK_MODEL_ID and credentials exist."""
    s = Settings()
    ok, _ = bedrock_status(s)
    if not ok:
        pytest.skip("Bedrock model id or AWS credentials not configured")
    a = StrandsBedrockAnalyzer(s.bedrock_model_id, s.aws_region)
    out = a.analyze(bundle(), None)
    assert out.analysis.summary
