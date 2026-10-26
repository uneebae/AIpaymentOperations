from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.agent.graph import investigate
from app.api.demo_data import DEMO_REFERENCES
from app.connectors.registry import CONNECTORS
from app.correlation.engine import correlate
from app.db import SessionLocal
from app.evidence.json_export import to_json_bytes
from app.evidence.pdf_export import to_pdf_bytes
from app.models.orm import InvestigationRecord
from app.models.schemas import ConnectorStatus, InvestigationRequest, InvestigationResult, TransactionRef

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/investigations", response_model=InvestigationResult, status_code=201)
def create_investigation(payload: InvestigationRequest, db: Session = Depends(get_db)) -> InvestigationResult:
    ref = TransactionRef(reference=payload.reference, reference_type=payload.reference_type)
    twin = correlate(ref, CONNECTORS)
    result = investigate(twin)

    record = InvestigationRecord(
        id=str(twin.id),
        reference=ref.reference,
        result_json=result.model_dump(mode="json"),
    )
    db.merge(record)
    db.commit()
    return result


@router.get("/investigations", response_model=list[InvestigationResult])
def list_investigations(db: Session = Depends(get_db)) -> list[InvestigationResult]:
    records = db.query(InvestigationRecord).order_by(InvestigationRecord.created_at.desc()).limit(20).all()
    return [InvestigationResult.model_validate(r.result_json) for r in records]


@router.get("/investigations/{investigation_id}", response_model=InvestigationResult)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)) -> InvestigationResult:
    record = db.get(InvestigationRecord, investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationResult.model_validate(record.result_json)


def _load_result(investigation_id: str, db: Session) -> InvestigationResult:
    record = db.get(InvestigationRecord, investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationResult.model_validate(record.result_json)


@router.get("/investigations/{investigation_id}/evidence-pack.json")
def get_evidence_json(investigation_id: str, db: Session = Depends(get_db)) -> Response:
    result = _load_result(investigation_id, db)
    return Response(
        content=to_json_bytes(result),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=evidence-pack-{investigation_id}.json"},
    )


@router.get("/investigations/{investigation_id}/evidence-pack.pdf")
def get_evidence_pdf(investigation_id: str, db: Session = Depends(get_db)) -> Response:
    result = _load_result(investigation_id, db)
    return Response(
        content=to_pdf_bytes(result),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=evidence-pack-{investigation_id}.pdf"},
    )


@router.get("/connectors/status", response_model=list[ConnectorStatus])
def connectors_status() -> list[ConnectorStatus]:
    statuses = []
    for connector in CONNECTORS:
        health = connector.healthcheck()
        statuses.append(ConnectorStatus(name=health.name, healthy=health.healthy, detail=health.detail))
    return statuses


@router.get("/demo/references")
def demo_references() -> list[dict]:
    return DEMO_REFERENCES
