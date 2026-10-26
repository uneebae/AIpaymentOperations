import os

from app.agent import graph as agent_graph
from app.agent.graph import investigate
from app.connectors.registry import CONNECTORS
from app.correlation.engine import correlate
from app.models.schemas import TransactionRef

os.environ.pop("ANTHROPIC_API_KEY", None)  # force deterministic fallback in tests


def _twin(reference: str):
    ref = TransactionRef(reference=reference, reference_type="core_transaction_id")
    return correlate(ref, CONNECTORS)


def _result(reference: str):
    return investigate(_twin(reference))


def test_investigation_result_citations_resolve_to_real_hops():
    result = _result("TXN2026082000123457")
    hop_ids = {h.id for h in result.twin.hops}
    for cause in result.root_causes:
        assert all(hid in hop_ids for hid in cause.cited_hop_ids)


def test_clean_transaction_has_no_root_causes():
    result = _result("TXN2026082000123456")
    assert result.root_causes == []


def test_broken_transaction_has_at_least_one_root_cause():
    result = _result("TXN2026082000123458")
    assert len(result.root_causes) >= 1
    assert result.root_causes[0].pattern_id == "switch-decline-funds-hold"


def test_fallback_path_never_self_corrects():
    """The deterministic fallback narration is grounded by construction, so
    critique_node should never find an issue to revise (guards against a
    spurious/infinite revision loop when no Claude client is configured)."""
    result = _result("TXN2026082000123458")
    assert result.self_corrected is False


def test_critique_node_flags_ungrounded_explanation_and_recommendation():
    from app.correlation.failure_library import match_patterns

    twin = _twin("TXN2026082000123458")
    matches = match_patterns(twin)
    state: agent_graph.AgentState = {
        "twin": twin,
        "matches": matches,
        "explanation": "Everything about this transaction is a mystery.",
        "root_causes": [],
        "recommendation": "Escalate to someone, somewhere.",
        "critique_notes": {"explanation": [], "recommendation": []},
        "revision_count": 0,
    }
    state = agent_graph._critique_node(state)
    assert state["critique_notes"]["explanation"], "should flag explanation missing the break stage"
    assert state["critique_notes"]["recommendation"], "should flag recommendation missing the matched pattern"
    assert agent_graph._should_revise(state) == "revise"
    assert state["revision_count"] == 1
    # a second pass still has issues, but MAX_REVISIONS is exhausted
    assert agent_graph._should_revise(state) == "done"


def test_critique_node_passes_grounded_text():
    twin = _twin("TXN2026082000123458")
    from app.correlation.failure_library import match_patterns

    matches = match_patterns(twin)
    break_hop = next(h for h in twin.hops if h.id == twin.break_hop_id)
    stage_label = agent_graph.fallback.STAGE_LABELS[break_hop.stage.value]
    top_label = matches[0][0]["label"]
    state: agent_graph.AgentState = {
        "twin": twin,
        "matches": matches,
        "explanation": f"The transaction broke at {stage_label}.",
        "root_causes": [],
        "recommendation": f"This matches the '{top_label}' pattern; escalate for review.",
        "critique_notes": {"explanation": [], "recommendation": []},
        "revision_count": 0,
    }
    state = agent_graph._critique_node(state)
    assert state["critique_notes"] == {"explanation": [], "recommendation": []}
    assert agent_graph._should_revise(state) == "done"
