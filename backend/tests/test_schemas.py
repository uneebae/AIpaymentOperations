"""Schema-level guardrail enforcement (app/models/schemas.py).

Per docs/GUARDRAILS.md, citation integrity and a few other invariants are
enforced by Pydantic validators, not by convention — these tests exercise
that every invalid construction actually raises, not just the happy path.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    Hop,
    HopStage,
    InvestigationResult,
    RawArtifact,
    RootCauseCandidate,
    TransactionDigitalTwin,
    TransactionRef,
)


def _artifact() -> RawArtifact:
    return RawArtifact(
        source="core_banking",
        artifact_type="ledger_entry",
        timestamp=datetime.now(UTC),
        raw_payload={"status": "success"},
    )


def _ref() -> TransactionRef:
    return TransactionRef(reference="TXN1", reference_type="core_transaction_id")


def test_hop_ok_status_requires_at_least_one_artifact():
    with pytest.raises(ValidationError, match="cannot be marked 'ok'"):
        Hop(sequence=1, stage=HopStage.CUSTOMER_CHANNEL, status="ok", artifacts=[])


def test_hop_break_status_allows_empty_artifacts():
    hop = Hop(sequence=1, stage=HopStage.PAYMENT_RAIL, status="break", artifacts=[])
    assert hop.artifacts == []


def test_twin_break_hop_id_must_reference_a_real_hop():
    hop = Hop(sequence=1, stage=HopStage.CUSTOMER_CHANNEL, status="ok", artifacts=[_artifact()])
    with pytest.raises(ValidationError, match="must reference a real Hop.id"):
        TransactionDigitalTwin(
            ref=_ref(),
            hops=[hop],
            break_hop_id=uuid4(),
            correlation_version="test-1",
        )


def test_twin_accepts_break_hop_id_matching_a_real_hop():
    hop = Hop(sequence=1, stage=HopStage.CUSTOMER_CHANNEL, status="break", artifacts=[])
    twin = TransactionDigitalTwin(
        ref=_ref(),
        hops=[hop],
        break_hop_id=hop.id,
        correlation_version="test-1",
    )
    assert twin.break_hop_id == hop.id


def test_root_cause_candidate_requires_at_least_one_citation():
    with pytest.raises(ValidationError, match="must cite at least one hop"):
        RootCauseCandidate(label="Some failure", confidence=0.5, cited_hop_ids=[])


def test_root_cause_candidate_confidence_must_be_within_unit_interval():
    with pytest.raises(ValidationError):
        RootCauseCandidate(label="Some failure", confidence=1.5, cited_hop_ids=[uuid4()])
    with pytest.raises(ValidationError):
        RootCauseCandidate(label="Some failure", confidence=-0.1, cited_hop_ids=[uuid4()])


def test_investigation_result_rejects_root_cause_citing_unknown_hop():
    hop = Hop(sequence=1, stage=HopStage.CUSTOMER_CHANNEL, status="break", artifacts=[])
    twin = TransactionDigitalTwin(ref=_ref(), hops=[hop], correlation_version="test-1")
    fabricated_cause = RootCauseCandidate(label="Fabricated", confidence=0.9, cited_hop_ids=[uuid4()])

    with pytest.raises(ValidationError, match="cites unknown hop id"):
        InvestigationResult(
            twin=twin,
            explanation="x",
            root_causes=[fabricated_cause],
            recommendation="x",
            model_version="test",
        )


def test_investigation_result_accepts_root_cause_citing_real_hop():
    hop = Hop(sequence=1, stage=HopStage.CUSTOMER_CHANNEL, status="break", artifacts=[])
    twin = TransactionDigitalTwin(ref=_ref(), hops=[hop], correlation_version="test-1")
    valid_cause = RootCauseCandidate(label="Real", confidence=0.9, cited_hop_ids=[hop.id])

    result = InvestigationResult(
        twin=twin,
        explanation="x",
        root_causes=[valid_cause],
        recommendation="x",
        model_version="test",
    )
    assert result.root_causes[0].cited_hop_ids == [hop.id]


def test_transaction_ref_rejects_unknown_reference_type():
    with pytest.raises(ValidationError):
        TransactionRef(reference="TXN1", reference_type="not-a-real-type")


def test_transaction_ref_defaults_rail_to_raast_p2p():
    ref = TransactionRef(reference="TXN1", reference_type="core_transaction_id")
    assert ref.rail == "raast_p2p"
