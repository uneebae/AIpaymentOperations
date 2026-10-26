"""Deterministic, template-based reasoning — no model call.

Used whenever ANTHROPIC_API_KEY is not configured, so the whole
investigation flow works out of the box in local dev. Also serves as the
documented "self-hosted model swap" seam described in docs/GUARDRAILS.md:
this module can be replaced by a call to a self-hosted model without
touching any caller.
"""
from __future__ import annotations

from app.models.schemas import TransactionDigitalTwin

STAGE_LABELS = {
    "customer_channel": "the customer channel",
    "authentication": "authentication",
    "payment_api": "the payment initiation API",
    "payment_switch": "the payment switch",
    "payment_rail": "the Raast rail",
    "receiving_institution": "the receiving institution",
    "core_banking": "core banking (ledger posting)",
    "settlement_reconciliation": "settlement reconciliation",
}


def explain(twin: TransactionDigitalTwin) -> str:
    parts = [
        f"Investigation of reference {twin.ref.reference} ({twin.ref.reference_type}, "
        f"rail {twin.ref.rail}) across {len(twin.hops)} hops."
    ]
    for hop in twin.hops:
        label = STAGE_LABELS.get(hop.stage.value, hop.stage.value)
        if hop.status == "ok":
            n = len(hop.artifacts)
            plural = "s" if n != 1 else ""
            parts.append(f"{label.capitalize()} completed successfully ({n} artifact{plural} confirmed).")
        elif hop.status == "break":
            reason = hop.notes or "an unspecified failure"
            parts.append(f"The flow broke at {label}: {reason}")
            break
        else:
            break
    return " ".join(parts)


def recommend(twin: TransactionDigitalTwin, matches: list[tuple[dict, float]]) -> str:
    if matches:
        pattern, confidence = matches[0]
        rec = (pattern.get("typical_recommendation") or "").strip()
        if rec:
            return (
                f"{rec} (matched failure pattern '{pattern['label']}', confidence "
                f"{confidence:.0%} — human review required before any action is taken.)"
            )

    break_hop = next((h for h in twin.hops if h.id == twin.break_hop_id), None)
    if break_hop is None:
        return "No break detected — no operational action required."
    return (
        f"No matching failure-library pattern for the break at {break_hop.stage.value}. "
        "Recommend manual escalation to the relevant systems owner with the evidence "
        "pack attached; a senior ops engineer should review before any customer "
        "communication or corrective action."
    )
