"""Harness tests use FAKE arms and a stubbed Bedrock reply. They check arithmetic, error
handling and output labelling; they never write benchmark/results and prove nothing about
Decider 2B or Bedrock performance."""

import boto3
import pytest
from botocore.stub import Stubber
from strands.models import BedrockModel

from benchmark.harness import (
    BedrockArm,
    BenchmarkResult,
    Sample,
    per_call_cost_usd,
    percentile,
    render_markdown,
    routing_prompt,
    run_arm,
    run_benchmark,
    summarize,
)

STATES = {"a": "state a", "b": "state b"}
REF = {"a": "x", "b": "y"}


class FakeArm:
    def __init__(self, name, choices, fail_on=None, **extra):
        self.name, self.choices, self.fail_on, self.extra = name, choices, fail_on, extra

    def call(self, scenario, state_text):
        if scenario == self.fail_on:
            raise TimeoutError("boom")
        return {"choice": self.choices[scenario], **self.extra}


def test_percentile_interpolates_and_handles_empty():
    assert percentile([], 50) is None
    assert percentile([10.0], 95) == 10.0
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([1, 2, 3, 4, 5], 95) == pytest.approx(4.8)


def test_run_arm_records_errors_instead_of_hiding_them():
    got = run_arm(FakeArm("f", {"a": "x", "b": "y"}, fail_on="b"), STATES, repeat=2)
    assert len(got) == 4
    assert [s.error is None for s in got] == [True, True, False, False]
    assert "TimeoutError" in got[2].error and got[2].choice is None


def test_summary_agreement_counts_only_successful_calls():
    s = summarize(run_arm(FakeArm("f", {"a": "x", "b": "WRONG"}), STATES, 3), REF)
    assert s["agreement_with_reference"] == {"matches": 3, "of": 6}
    assert s["errors"] == 0 and s["wall_ms"]["p50"] is not None
    e = summarize(run_arm(FakeArm("f", {"a": "x", "b": "y"}, fail_on="a"), STATES, 1), REF)
    assert e["errors"] == 1 and e["agreement_with_reference"] == {"matches": 1, "of": 1}


def test_cost_needs_prices_and_measured_tokens():
    s = {"mean_input_tokens": 1000.0, "mean_output_tokens": 100.0}
    assert per_call_cost_usd(s, None, 15.0) is None
    assert per_call_cost_usd(s, 3.0, 15.0) == pytest.approx(0.0045)
    assert per_call_cost_usd({"mean_input_tokens": None, "mean_output_tokens": 1}, 3, 15) is None


def test_comparison_only_when_both_arms_have_latency():
    r = run_benchmark(
        [FakeArm("decider", {"a": "x", "b": "y"}), FakeArm("bedrock", {"a": "x", "b": "y"})],
        STATES,
        REF,
        repeat=2,
        meta={},
    )
    assert "bedrock_p50_over_decider_p50" in r.comparison
    only = run_benchmark([FakeArm("decider", {"a": "x", "b": "y"})], STATES, REF, repeat=1, meta={})
    assert only.comparison == {}


def test_markdown_never_prints_numbers_that_were_not_measured():
    r = run_benchmark(
        [FakeArm("bedrock", {"a": "x", "b": "y"})], STATES, REF, repeat=1, meta={"k": "v"}
    )
    md = render_markdown(r)
    assert "not measured" in md  # no tokens/cost were returned by the fake arm
    assert "Read this first" in md and "smoke check" in md and "self-hosted" in md
    assert isinstance(r, BenchmarkResult) and isinstance(r.samples[0], Sample)


def test_routing_prompt_lists_every_option_and_the_state():
    p = routing_prompt("STATE-TEXT")
    for opt in (
        "investigate_load_balancer",
        "investigate_ec2",
        "investigate_database",
        "investigate_cloudwatch_logs",
        "collect_more_evidence",
    ):
        assert opt in p
    assert "STATE-TEXT" in p


def stub_factory(choice, in_tok=321, out_tok=21):
    """TEST DOUBLE of Bedrock's reply. Checks our parsing and token extraction only."""

    def f():
        sess = boto3.Session(
            aws_access_key_id="t", aws_secret_access_key="t", region_name="us-east-1"
        )
        m = BedrockModel(model_id="test", streaming=False, boto_session=sess)
        st = Stubber(m.client)
        st.add_response(
            "converse",
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "1",
                                    "name": "RoutingChoice",
                                    "input": {"choice": choice, "reason": "r"},
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {
                    "inputTokens": in_tok,
                    "outputTokens": out_tok,
                    "totalTokens": in_tok + out_tok,
                },
                "metrics": {"latencyMs": 5},
            },
        )
        st.activate()
        return m

    return f


def test_bedrock_arm_extracts_choice_and_token_usage():
    arm = BedrockArm("test", "us-east-1", model_factory=stub_factory("investigate_ec2"))
    r = arm.call("sim-ec2-cpu", "state")
    assert r == {"choice": "investigate_ec2", "input_tokens": 321, "output_tokens": 21}


def test_bedrock_arm_rejects_a_choice_outside_the_option_set_as_an_error():
    arm = BedrockArm("test", "us-east-1", model_factory=stub_factory("restart_everything"))
    got = run_arm(arm, {"s": "state"}, 1)
    assert got[0].error is not None and got[0].choice is None
