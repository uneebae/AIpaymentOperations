"""The five MVP connectors, matched to docs/MVP_SCOPE.md, instantiated once."""
from __future__ import annotations

from app.connectors.fixture_connectors import (
    OpenConnectLogsConnector,
    RaastResponseConnector,
    ReconciliationConnector,
    SwitchLogsConnector,
    TransactionDBConnector,
)

CONNECTORS = [
    OpenConnectLogsConnector(),
    SwitchLogsConnector(),
    TransactionDBConnector(),
    RaastResponseConnector(),
    ReconciliationConnector(),
]
