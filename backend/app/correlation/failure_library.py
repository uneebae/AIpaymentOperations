"""Break-signature matching against the failure-pattern library.

Still deterministic/rule-based, per docs/ROADMAP.md Weeks 4-8 — no model
call is involved in deciding which known pattern a break resembles.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from app.models.schemas import TransactionDigitalTwin

LIBRARY_ROOT = Path(__file__).resolve().parent.parent.parent / "failure-library"


def load_failure_library(rail: str) -> list[dict]:
    rail_dir = LIBRARY_ROOT / rail.replace("_", "-")
    if not rail_dir.exists():
        return []
    patterns = []
    for path in sorted(rail_dir.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            patterns.append(yaml.safe_load(f))
    return patterns


def match_patterns(twin: TransactionDigitalTwin) -> list[tuple[dict, float]]:
    """Return (pattern, confidence) pairs, highest confidence first."""
    if twin.break_hop_id is None:
        return []
    break_hop = next((h for h in twin.hops if h.id == twin.break_hop_id), None)
    if break_hop is None:
        return []

    candidates: list[tuple[dict, float]] = []
    for pattern in load_failure_library(twin.ref.rail):
        if pattern.get("break_stage") != break_hop.stage.value:
            continue
        signature = pattern.get("signature", {})
        break_type = signature.get("break_type")

        if break_type == "missing_artifact":
            if not break_hop.artifacts:
                candidates.append((pattern, 0.9))
        elif break_type == "contradictory_status":
            note = (break_hop.notes or "").lower()
            needle = str(signature.get("status_contains", "")).lower()
            if needle and needle in note:
                candidates.append((pattern, 0.88))
            elif break_hop.artifacts:
                candidates.append((pattern, 0.4))

    candidates.sort(key=lambda c: -c[1])
    return candidates
