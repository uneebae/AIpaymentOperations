"""Fixture-backed connector implementations.

Each of these stands in for a read-only pull against a real source system
(DB read replica, log shipper, API pull) per docs/GUARDRAILS.md — read
data from a local JSON file, never write anywhere. Swapping a fixture
connector for a live one means implementing the same `fetch`/`healthcheck`
contract against a real (read-only) credential; no caller-side code changes.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.connectors.base import ConnectorHealth, TimeWindow
from app.models.schemas import RawArtifact, TransactionRef

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FixtureConnector:
    name: str = "fixture-connector"
    fixture_file: str = ""

    def __init__(self) -> None:
        path = FIXTURES_DIR / self.fixture_file
        with path.open(encoding="utf-8") as f:
            self._records: list[dict] = json.load(f)

    def fetch(self, ref: TransactionRef, window: TimeWindow | None = None) -> list[RawArtifact]:
        keys = {ref.reference}
        matches = [
            r
            for r in self._records
            if keys & {r.get("core_transaction_id"), r.get("rail_reference"), r.get("session_id")}
        ]
        artifacts = [
            RawArtifact(
                source=self.name,
                artifact_type=r["artifact_type"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                raw_payload=r["raw_payload"],
            )
            for r in matches
        ]
        if window is not None:
            if window.start:
                artifacts = [a for a in artifacts if a.timestamp >= window.start]
            if window.end:
                artifacts = [a for a in artifacts if a.timestamp <= window.end]
        return artifacts

    def healthcheck(self) -> ConnectorHealth:
        return ConnectorHealth(
            name=self.name,
            healthy=True,
            detail=f"{len(self._records)} fixture record(s) loaded from {self.fixture_file}",
        )


class OpenConnectLogsConnector(FixtureConnector):
    name = "openconnect-logs"
    fixture_file = "openconnect_logs.json"


class SwitchLogsConnector(FixtureConnector):
    name = "payment-switch-logs"
    fixture_file = "switch_logs.json"


class TransactionDBConnector(FixtureConnector):
    name = "transaction-db"
    fixture_file = "transaction_db.json"


class RaastResponseConnector(FixtureConnector):
    name = "raast-response"
    fixture_file = "raast_response.json"


class ReconciliationConnector(FixtureConnector):
    name = "reconciliation-file"
    fixture_file = "reconciliation.json"
