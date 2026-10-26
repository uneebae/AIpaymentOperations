from app.connectors.registry import CONNECTORS
from app.models.schemas import TransactionRef

KNOWN_REF = TransactionRef(reference="TXN2026082000123456", reference_type="core_transaction_id")
UNKNOWN_REF = TransactionRef(reference="TXN-DOES-NOT-EXIST", reference_type="core_transaction_id")


def test_all_connectors_healthy():
    for connector in CONNECTORS:
        health = connector.healthcheck()
        assert health.healthy is True


def test_known_reference_returns_artifacts():
    total = sum(len(c.fetch(KNOWN_REF)) for c in CONNECTORS)
    assert total > 0


def test_unknown_reference_returns_nothing():
    for connector in CONNECTORS:
        assert connector.fetch(UNKNOWN_REF) == []


def test_fetch_is_read_only_interface():
    for connector in CONNECTORS:
        assert not hasattr(connector, "write")
        assert not hasattr(connector, "post")
        assert not hasattr(connector, "delete")
