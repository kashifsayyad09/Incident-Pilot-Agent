"""Deterministic grounding checks on model output.

The model is untrusted. Before anything is shown as a *confirmed fact*, we verify:
  1. it cites at least one real evidence id, and
  2. every number it states appears in the cited evidence.
Failing items are demoted to hypotheses, never silently kept and never silently dropped.
This is deliberately conservative: a derived number (e.g. a percentage the model
computed) is demoted, because it is not stated by the evidence.
"""

from __future__ import annotations

import re

from .evidence import EvidenceBundle
from .report import Fact, GroundingReport, Hypothesis, IncidentAnalysis, RootCause

_NUM = re.compile(r"\d+(?:\.\d+)?")


def _numbers(text: str) -> set[float]:
    return {float(m) for m in _NUM.findall(text)}


def _clean_ids(ids: list[str], valid: set[str], rep: GroundingReport, where: str) -> list[str]:
    kept = [i for i in dict.fromkeys(ids) if i in valid]
    removed = [i for i in ids if i not in valid]
    if removed:
        rep.evidence_ids_removed += len(removed)
        rep.warnings.append(f"{where}: removed unknown evidence id(s) {sorted(set(removed))}.")
    return kept


def ground(
    analysis: IncidentAnalysis, bundle: EvidenceBundle
) -> tuple[IncidentAnalysis, GroundingReport]:
    rep = GroundingReport()
    items = bundle.by_id()
    valid = set(items)

    facts: list[Fact] = []
    hypotheses: list[Hypothesis] = list(analysis.hypotheses)

    for f in analysis.confirmed_facts:
        ids = _clean_ids(f.evidence_ids, valid, rep, f"fact {f.statement[:40]!r}")
        reason = None
        if not ids:
            reason = "cites no valid evidence"
        else:
            cited = set().union(*(_numbers(items[i].text) for i in ids))
            missing = sorted(n for n in _numbers(f.statement) if n not in cited)
            if missing:
                reason = f"states number(s) {missing} not present in the cited evidence"
        if reason is None:
            facts.append(Fact(statement=f.statement, evidence_ids=ids))
            rep.facts_kept += 1
        else:
            rep.facts_demoted += 1
            rep.warnings.append(f"Demoted to hypothesis: {f.statement[:70]!r} ({reason}).")
            hypotheses.append(
                Hypothesis(
                    statement=f.statement,
                    evidence_ids=ids,
                    what_would_confirm="Not established by the cited evidence; verify directly.",
                    plausibility="possible",
                )
            )

    clean_h = [
        h.model_copy(update={"evidence_ids": _clean_ids(h.evidence_ids, valid, rep, "hypothesis")})
        for h in hypotheses
    ]

    causes: list[RootCause] = []
    for c in analysis.probable_root_causes:
        ids = _clean_ids(c.evidence_ids, valid, rep, "root cause")
        basis = c.basis
        if basis == "confirmed" and not ids:
            basis = "hypothesis"
            rep.root_causes_demoted += 1
            rep.warnings.append(
                f"Root cause marked hypothesis (no valid evidence): {c.description[:70]!r}."
            )
        causes.append(c.model_copy(update={"evidence_ids": ids, "basis": basis}))

    actions = [
        a.model_copy(update={"evidence_ids": _clean_ids(a.evidence_ids, valid, rep, "action")})
        for a in analysis.recommended_actions
    ]

    return (
        analysis.model_copy(
            update={
                "confirmed_facts": facts,
                "hypotheses": clean_h,
                "probable_root_causes": causes,
                "recommended_actions": actions,
            }
        ),
        rep,
    )
