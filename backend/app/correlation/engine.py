"""The deterministic correlation engine.

No LLM calls anywhere in this module — see docs/ARCHITECTURE.md, Layer 2.
Given a TransactionRef and the set of connectors, it resolves artifacts
across all five sources, assembles them into ordered Hops per
HOP_STAGE_ORDER, and detects the first break: the first hop where an
expected artifact is missing, or where a present artifact reports a
non-success outcome. Pure function of its inputs — same fixtures in,
same twin out, every time.
"""
from __future__ import annotations

from app.connectors.base import Connector, TimeWindow
from app.correlation.rules import STAGE_ARTIFACT_RULES, extract_outcome
from app.models.schemas import HOP_STAGE_ORDER, Hop, RawArtifact, TransactionDigitalTwin, TransactionRef

CORRELATION_VERSION = "2026.08.1"


def correlate(ref: TransactionRef, connectors: list[Connector]) -> TransactionDigitalTwin:
    artifacts_by_connector: dict[str, list[RawArtifact]] = {
        c.name: c.fetch(ref, TimeWindow()) for c in connectors
    }

    hops: list[Hop] = []
    break_hop_id = None
    already_broken = False

    for seq, stage in enumerate(HOP_STAGE_ORDER, start=1):
        stage_artifacts: list[RawArtifact] = []
        for connector_name, artifact_type, payload_filter in STAGE_ARTIFACT_RULES[stage]:
            for artifact in artifacts_by_connector.get(connector_name, []):
                if artifact.artifact_type != artifact_type:
                    continue
                if payload_filter is not None and not payload_filter(artifact.raw_payload):
                    continue
                stage_artifacts.append(artifact)
        stage_artifacts.sort(key=lambda a: a.timestamp)

        if already_broken:
            status: str = "unknown"
            notes = "Not reached — an upstream break already occurred at an earlier hop."
            visible_artifacts: list[RawArtifact] = []
        elif not stage_artifacts:
            status = "break"
            notes = "Expected artifact not found for this stage within the investigation window."
            visible_artifacts = []
            already_broken = True
        else:
            outcomes = [extract_outcome(a.raw_payload) for a in stage_artifacts]
            failing = [(a, o) for a, o in zip(stage_artifacts, outcomes, strict=True) if o != "success"]
            if failing:
                status = "break"
                bad_artifact, bad_outcome = failing[0]
                reason = bad_artifact.raw_payload.get("reason") or bad_artifact.raw_payload.get("detail")
                notes = f"Artifact reported non-success outcome '{bad_outcome}'" + (f": {reason}" if reason else ".")
                visible_artifacts = stage_artifacts
                already_broken = True
            else:
                status = "ok"
                notes = None
                visible_artifacts = stage_artifacts

        hop = Hop(
            sequence=seq,
            stage=stage,
            status=status,
            artifacts=visible_artifacts,
            started_at=stage_artifacts[0].timestamp if stage_artifacts else None,
            completed_at=stage_artifacts[-1].timestamp if stage_artifacts else None,
            notes=notes,
        )
        hops.append(hop)
        if status == "break" and break_hop_id is None:
            break_hop_id = hop.id

    return TransactionDigitalTwin(
        ref=ref,
        hops=hops,
        break_hop_id=break_hop_id,
        correlation_version=CORRELATION_VERSION,
    )
