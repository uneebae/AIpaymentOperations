"""Persistence for completed investigations. The stored payload is the
full InvestigationResult, keyed by the twin's own id — GET /investigations/{id}
reads it back and re-validates it through the Pydantic model on the way out.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String

from app.db import Base


class InvestigationRecord(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True)
    reference = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    result_json = Column(JSON, nullable=False)
