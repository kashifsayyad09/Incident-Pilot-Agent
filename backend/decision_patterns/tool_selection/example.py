"""Minimal standalone use of the pattern (no IncidentPilot code needed).

strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000
python -m decision_patterns.tool_selection.example
"""

from decision_patterns.tool_selection import HttpDeciderClient, ToolSelectionPattern

pattern = ToolSelectionPattern(
    question="Which tool should the agent call next?",
    options={
        "search_orders": "The user asks about an existing order, delivery or refund.",
        "search_docs": "The user asks how a product or policy works.",
        "collect_more_evidence": "The request is too vague to pick a tool.",
    },
    client=HttpDeciderClient("http://localhost:9000"),
    confidence_threshold=0.6,
)

if __name__ == "__main__":
    d = pattern.decide("Where is my package? It was due on Tuesday.")
    print(d.selected, f"confidence={d.confidence:.3f}", d.action.value, d.latency_ms)
