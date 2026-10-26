"""LangGraph reasoning graph — explain_node, match_node, recommend_node,
evidence_node, critique_node, matching the shape suggested in
docs/ARCHITECTURE.md plus a bounded self-correction loop.

This module only ever *reads* the TransactionDigitalTwin it is given (see
docs/ARCHITECTURE.md, "Why the split matters"). It has no tool binding
capable of a write operation, and every RootCauseCandidate it emits is
validated at the schema level (app/models/schemas.py) to cite a real
Hop.id — an uncited or fabricated claim cannot survive construction of
InvestigationResult.

Self-correction: after evidence_node assembles the citation-backed root
causes, critique_node checks the free-text explanation/recommendation
against those same facts (does the explanation name the actual break
stage? does the recommendation reference the actual top failure-library
match?) and, if not, sends the agent back to revise — at most
MAX_REVISIONS times, so the loop always terminates. This never grants new
tool access and never touches root_causes, which stay deterministic.
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agent import claude_reasoning, fallback
from app.correlation.failure_library import match_patterns
from app.models.schemas import InvestigationResult, RootCauseCandidate, TransactionDigitalTwin

FALLBACK_MODEL_VERSION = "apoe-fallback-reasoning-2026.08.1"
CLAUDE_MODEL_VERSION = f"{claude_reasoning.MODEL_NAME}+apoe-agent-2026.08.1"

MAX_REVISIONS = 1


class CritiqueNotes(TypedDict):
    explanation: list[str]
    recommendation: list[str]


class AgentState(TypedDict):
    twin: TransactionDigitalTwin
    matches: list[tuple[dict, float]]
    explanation: str
    root_causes: list[RootCauseCandidate]
    recommendation: str
    critique_notes: CritiqueNotes
    revision_count: int


def _match_node(state: AgentState) -> AgentState:
    state["matches"] = match_patterns(state["twin"])
    return state


def _explain_node(state: AgentState) -> AgentState:
    client = claude_reasoning.get_client()
    twin = state["twin"]
    feedback = state["critique_notes"]["explanation"]
    state["explanation"] = (
        claude_reasoning.explain(client, twin, feedback=feedback) if client else fallback.explain(twin)
    )
    return state


def _recommend_node(state: AgentState) -> AgentState:
    client = claude_reasoning.get_client()
    twin, matches = state["twin"], state["matches"]
    feedback = state["critique_notes"]["recommendation"]
    state["recommendation"] = (
        claude_reasoning.recommend(client, twin, matches, feedback=feedback)
        if client
        else fallback.recommend(twin, matches)
    )
    return state


def _evidence_node(state: AgentState) -> AgentState:
    twin, matches = state["twin"], state["matches"]
    break_hop = next((h for h in twin.hops if h.id == twin.break_hop_id), None)
    root_causes: list[RootCauseCandidate] = []
    if break_hop is not None:
        if matches:
            for pattern, confidence in matches[:3]:
                root_causes.append(
                    RootCauseCandidate(
                        label=pattern["label"],
                        confidence=confidence,
                        cited_hop_ids=[break_hop.id],
                        pattern_id=pattern["id"],
                    )
                )
        else:
            root_causes.append(
                RootCauseCandidate(
                    label=f"Unclassified break at {break_hop.stage.value}",
                    confidence=0.3,
                    cited_hop_ids=[break_hop.id],
                    pattern_id=None,
                )
            )
    state["root_causes"] = root_causes
    return state


def _critique_node(state: AgentState) -> AgentState:
    """Ground-check the free-text output against the same facts evidence_node
    used — never against model opinion. Only checks explanation/recommendation;
    root_causes are already schema-enforced and are not revisited here."""
    twin = state["twin"]
    explanation = state["explanation"].lower()
    recommendation = state["recommendation"].lower()
    matches = state["matches"]
    break_hop = next((h for h in twin.hops if h.id == twin.break_hop_id), None)

    notes: CritiqueNotes = {"explanation": [], "recommendation": []}

    if break_hop is not None:
        label = fallback.STAGE_LABELS.get(break_hop.stage.value, break_hop.stage.value)
        stage_words = break_hop.stage.value.replace("_", " ")
        if label.lower() not in explanation and stage_words not in explanation:
            notes["explanation"].append(
                f"It must name the stage where the break occurred: {label} "
                f"(hop {break_hop.sequence}, stage={break_hop.stage.value})."
            )

    if matches:
        top_label = matches[0][0]["label"]
        if top_label.lower() not in recommendation:
            notes["recommendation"].append(
                f"It must reference the top matched failure-library pattern: '{top_label}'."
            )

    state["critique_notes"] = notes
    return state


def _should_revise(state: AgentState) -> str:
    notes = state["critique_notes"]
    has_issues = bool(notes["explanation"] or notes["recommendation"])
    if has_issues and state["revision_count"] < MAX_REVISIONS:
        state["revision_count"] += 1
        return "revise"
    return "done"


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        graph = StateGraph(AgentState)
        graph.add_node("match", _match_node)
        graph.add_node("explain", _explain_node)
        graph.add_node("recommend", _recommend_node)
        graph.add_node("evidence", _evidence_node)
        graph.add_node("critique", _critique_node)
        graph.set_entry_point("match")
        graph.add_edge("match", "explain")
        graph.add_edge("explain", "recommend")
        graph.add_edge("recommend", "evidence")
        graph.add_edge("evidence", "critique")
        graph.add_conditional_edges("critique", _should_revise, {"revise": "explain", "done": END})
        _compiled_graph = graph.compile()
    return _compiled_graph


def investigate(twin: TransactionDigitalTwin) -> InvestigationResult:
    initial_state: AgentState = {
        "twin": twin,
        "matches": [],
        "explanation": "",
        "root_causes": [],
        "recommendation": "",
        "critique_notes": {"explanation": [], "recommendation": []},
        "revision_count": 0,
    }
    final_state = _get_graph().invoke(initial_state)
    model_version = CLAUDE_MODEL_VERSION if claude_reasoning.get_client() else FALLBACK_MODEL_VERSION
    return InvestigationResult(
        twin=twin,
        explanation=final_state["explanation"],
        root_causes=final_state["root_causes"],
        recommendation=final_state["recommendation"],
        model_version=model_version,
        self_corrected=final_state["revision_count"] > 0,
    )
