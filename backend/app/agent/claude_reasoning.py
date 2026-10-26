"""Claude-backed reasoning — used only when ANTHROPIC_API_KEY is set.

Per docs/GUARDRAILS.md, this is the one component that may send data
outside the deployment perimeter in a hosted-model configuration, and it
is kept behind this narrow interface (not hardcoded into the graph nodes)
so a design partner requiring air-gapping can swap it for a self-hosted
model. The model is given the twin's already-assembled facts and asked
only to narrate/rank/recommend — it has no tool access and cannot alter
the twin (see AgentState in graph.py, which only ever reads twin).
"""
from __future__ import annotations

import os

from app.models.schemas import TransactionDigitalTwin

# Read live (not via app.core.config.Settings) so tests can toggle this via
# os.environ per-run without fighting Settings' process-wide lru_cache.

MODEL_NAME = "claude-sonnet-5"

EXPLAIN_SYSTEM_PROMPT = (
    "You are a payment operations investigation assistant. You are given a "
    "deterministically-assembled transaction timeline (a 'twin'). Narrate what "
    "happened in plain language, in hop order. Only state facts present in the "
    "timeline below — never invent a hop, system, or outcome that isn't there. "
    "Be concise (4-8 sentences)."
)

RECOMMEND_SYSTEM_PROMPT = (
    "You are a payment operations investigation assistant. Draft ONE recommended "
    "next operational action for a human engineer to review and approve. Never "
    "claim the action has been taken — you are drafting a recommendation only, "
    "never executing one. You have no ability to post, reverse, retry, or release "
    "a payment. Ground the recommendation strictly in the timeline and "
    "failure-library matches given below. 2-4 sentences."
)


def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _twin_summary(twin: TransactionDigitalTwin) -> str:
    lines = [f"Reference: {twin.ref.reference} ({twin.ref.reference_type}, rail={twin.ref.rail})"]
    for hop in twin.hops:
        suffix = f" — {hop.notes}" if hop.notes else ""
        lines.append(f"{hop.sequence}. [{hop.stage.value}] status={hop.status}{suffix}")
        for a in hop.artifacts:
            lines.append(
                f"    evidence: source={a.source} type={a.artifact_type} "
                f"at={a.timestamp.isoformat()} payload={a.raw_payload}"
            )
    return "\n".join(lines)


def _with_feedback(prompt: str, feedback: list[str] | None) -> str:
    if not feedback:
        return prompt
    notes = "\n".join(f"- {f}" for f in feedback)
    return f"{prompt}\n\nYour previous draft did not satisfy self-review. Revise it to fix:\n{notes}"


def explain(client, twin: TransactionDigitalTwin, feedback: list[str] | None = None) -> str:
    prompt = _with_feedback(_twin_summary(twin), feedback)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=500,
        system=EXPLAIN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def recommend(
    client, twin: TransactionDigitalTwin, matches: list[tuple[dict, float]], feedback: list[str] | None = None
) -> str:
    match_text = "\n".join(
        f"- {p['label']} (confidence {c:.2f}): {(p.get('typical_recommendation') or '').strip()}"
        for p, c in matches[:3]
    ) or "No failure-library match found."
    prompt = _with_feedback(f"{_twin_summary(twin)}\n\nCandidate failure-library matches:\n{match_text}", feedback)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=300,
        system=RECOMMEND_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
