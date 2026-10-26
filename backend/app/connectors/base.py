"""The Connector protocol — one module per source system, pull-only.

Per docs/ARCHITECTURE.md and docs/GUARDRAILS.md: a connector exposes only
`fetch()` and `healthcheck()`. There is no write method on this protocol,
anywhere in this package, by design — that is the static enforcement the
guardrails doc asks for.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from app.models.schemas import RawArtifact, TransactionRef


class TimeWindow(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class ConnectorHealth(BaseModel):
    name: str
    healthy: bool
    detail: str | None = None


class Connector(Protocol):
    name: str

    def fetch(self, ref: TransactionRef, window: TimeWindow | None = None) -> list[RawArtifact]: ...

    def healthcheck(self) -> ConnectorHealth: ...
