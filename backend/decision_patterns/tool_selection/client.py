"""HTTP client for a Strands Decider 2B server (`strands-decider serve <model>`).

Talks to the real System One endpoint:  POST /v1/systemone  (+ GET /health).
Nothing here produces a decision itself. If the server cannot be reached or answers
with something that is not a valid choice answer, an exception is raised; the caller
must surface it. There is intentionally no fallback.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class DeciderError(Exception):
    """Base class for all Decider client failures."""


class DeciderUnavailable(DeciderError):
    """The server cannot be reached, is unhealthy, or timed out."""


class DeciderProtocolError(DeciderError):
    """The server answered, but not with a valid response to the question asked."""


@dataclass(frozen=True)
class ChoiceResult:
    """A validated `choice` answer, passed through exactly as the model returned it."""

    choice: str
    probabilities: dict[str, float]
    confidence: float
    model: str | None
    latency_ms: float | None  # server-side, as reported by the server; None if not reported
    roundtrip_ms: float  # measured here: request sent -> response parsed


class DeciderClient(Protocol):
    def health(self) -> dict[str, Any]: ...

    def ask_choice(
        self, state: str, question: str, options: Mapping[str, str], *, name: str = "choice"
    ) -> ChoiceResult: ...


class HttpDeciderClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        health_timeout: float = 2.0,
        http: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._health_timeout = health_timeout
        self._http = http or httpx.Client()

    def health(self) -> dict[str, Any]:
        try:
            r = self._http.get(f"{self.base_url}/health", timeout=self._health_timeout)
        except httpx.HTTPError as e:
            raise DeciderUnavailable(
                f"Cannot reach the Decider server at {self.base_url} ({type(e).__name__})."
            ) from e
        if r.status_code != 200:
            raise DeciderUnavailable(f"Decider /health returned HTTP {r.status_code}.")
        try:
            body = r.json()
        except ValueError as e:
            raise DeciderUnavailable("Decider /health returned a non-JSON body.") from e
        if not isinstance(body, dict) or body.get("status") != "ok":
            raise DeciderUnavailable("Decider /health did not report status 'ok'.")
        return body

    def ask_choice(
        self, state: str, question: str, options: Mapping[str, str], *, name: str = "choice"
    ) -> ChoiceResult:
        payload = {
            "state": state,
            "questions": {
                name: {"type": "choice", "instructions": question, "criteria": dict(options)}
            },
        }
        started = time.perf_counter()
        try:
            r = self._http.post(
                f"{self.base_url}/v1/systemone", json=payload, timeout=self._timeout
            )
        except httpx.HTTPError as e:
            raise DeciderUnavailable(
                f"Decider request failed ({type(e).__name__}) for {self.base_url}."
            ) from e
        if r.status_code != 200:
            raise DeciderProtocolError(f"Decider returned HTTP {r.status_code}: {r.text[:300]}")
        try:
            body = r.json()
        except ValueError as e:
            raise DeciderProtocolError("Decider returned a non-JSON body.") from e
        roundtrip_ms = (time.perf_counter() - started) * 1000
        return _parse_choice(body, name, options, roundtrip_ms)


def _parse_choice(
    body: Any, name: str, options: Mapping[str, str], roundtrip_ms: float
) -> ChoiceResult:
    def bad(msg: str) -> DeciderProtocolError:
        return DeciderProtocolError(f"Invalid Decider response: {msg}")

    if not isinstance(body, dict):
        raise bad("body is not an object")
    answers = body.get("answers")
    ans = answers.get(name) if isinstance(answers, dict) else None
    if not isinstance(ans, dict) or ans.get("type") != "choice":
        raise bad(f"no 'choice' answer named {name!r}")
    choice, probs, conf = ans.get("choice"), ans.get("probabilities"), ans.get("confidence")
    if not isinstance(choice, str) or choice not in options:
        raise bad(f"choice {choice!r} is not one of the offered options")
    if not isinstance(probs, dict) or set(probs) != set(options):
        raise bad("probabilities do not match the offered options")
    if not all(isinstance(v, int | float) and not isinstance(v, bool) for v in probs.values()):
        raise bad("probabilities must be numbers")
    if isinstance(conf, bool) or not isinstance(conf, int | float) or not 0.0 <= conf <= 1.0:
        raise bad("confidence missing or outside [0, 1]")
    latency = body.get("latency_ms")
    latency_ms = float(latency) if isinstance(latency, int | float) else None
    model = body.get("model") if isinstance(body.get("model"), str) else None
    return ChoiceResult(
        choice=choice,
        probabilities={k: float(v) for k, v in probs.items()},
        confidence=float(conf),
        model=model,
        latency_ms=latency_ms,
        roundtrip_ms=roundtrip_ms,
    )
