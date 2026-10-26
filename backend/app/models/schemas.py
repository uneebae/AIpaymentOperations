"""Core Pydantic schemas — the Transaction Digital Twin data model.

Mirrors docs/DATA_MODEL.md exactly. This module has no I/O and no LLM
dependency: it is pure data shape plus the citation-integrity validator
that is the schema-level backstop described in docs/GUARDRAILS.md.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class TransactionRef(BaseModel):
    reference: str
    reference_type: Literal["rail_reference", "core_transaction_id", "session_id"]
    rail: Literal["raast_p2p"] = "raast_p2p"


class RawArtifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    artifact_type: str
    timestamp: datetime
    raw_payload: dict


class HopStage(StrEnum):
    CUSTOMER_CHANNEL = "customer_channel"
    AUTHENTICATION = "authentication"
    PAYMENT_API = "payment_api"
    PAYMENT_SWITCH = "payment_switch"
    PAYMENT_RAIL = "payment_rail"
    RECEIVING_INSTITUTION = "receiving_institution"
    CORE_BANKING = "core_banking"
    SETTLEMENT_RECONCILIATION = "settlement_reconciliation"


# Canonical ordering used by the correlation engine to sequence hops.
HOP_STAGE_ORDER: list[HopStage] = [
    HopStage.CUSTOMER_CHANNEL,
    HopStage.AUTHENTICATION,
    HopStage.PAYMENT_API,
    HopStage.PAYMENT_SWITCH,
    HopStage.PAYMENT_RAIL,
    HopStage.RECEIVING_INSTITUTION,
    HopStage.CORE_BANKING,
    HopStage.SETTLEMENT_RECONCILIATION,
]


class Hop(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sequence: int
    stage: HopStage
    status: Literal["ok", "break", "unknown"]
    artifacts: list[RawArtifact]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _ok_requires_artifacts(self) -> Hop:
        if self.status == "ok" and not self.artifacts:
            raise ValueError("a hop with no artifacts cannot be marked 'ok'")
        return self


class TransactionDigitalTwin(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ref: TransactionRef
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hops: list[Hop]
    break_hop_id: UUID | None = None
    correlation_version: str

    @model_validator(mode="after")
    def _break_hop_must_exist(self) -> TransactionDigitalTwin:
        if self.break_hop_id is not None:
            hop_ids = {h.id for h in self.hops}
            if self.break_hop_id not in hop_ids:
                raise ValueError("break_hop_id must reference a real Hop.id in this twin")
        return self


class RootCauseCandidate(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    cited_hop_ids: list[UUID]
    pattern_id: str | None = None

    @field_validator("cited_hop_ids")
    @classmethod
    def _non_empty_citation(cls, v: list[UUID]) -> list[UUID]:
        if not v:
            raise ValueError("every root cause candidate must cite at least one hop")
        return v


class InvestigationResult(BaseModel):
    twin: TransactionDigitalTwin
    explanation: str
    root_causes: list[RootCauseCandidate]
    recommendation: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str
    self_corrected: bool = False

    @model_validator(mode="after")
    def _citations_resolve_to_real_hops(self) -> InvestigationResult:
        """Schema-level enforcement from GUARDRAILS.md: every cited_hop_id in
        every root cause must resolve to a real Hop.id in the twin. This is
        the backstop — the agent cannot emit an uncited or fabricated claim
        and have it survive validation."""
        hop_ids = {h.id for h in self.twin.hops}
        for cause in self.root_causes:
            unknown = [str(hid) for hid in cause.cited_hop_ids if hid not in hop_ids]
            if unknown:
                raise ValueError(
                    f"root cause '{cause.label}' cites unknown hop id(s): {unknown}"
                )
        return self


class ConnectorStatus(BaseModel):
    name: str
    healthy: bool
    detail: str | None = None


class InvestigationRequest(BaseModel):
    reference: str
    reference_type: Literal["rail_reference", "core_transaction_id", "session_id"] = "rail_reference"
