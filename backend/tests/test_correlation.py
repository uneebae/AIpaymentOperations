import pytest

from app.connectors.registry import CONNECTORS
from app.correlation.engine import correlate
from app.correlation.failure_library import match_patterns
from app.models.schemas import HopStage, TransactionRef


def _twin(reference: str):
    ref = TransactionRef(reference=reference, reference_type="core_transaction_id")
    return correlate(ref, CONNECTORS)


def test_clean_transaction_has_no_break():
    twin = _twin("TXN2026082000123456")
    assert twin.break_hop_id is None
    assert all(h.status == "ok" for h in twin.hops)


def test_rail_timeout_breaks_at_payment_rail():
    twin = _twin("TXN2026082000123457")
    break_hop = next(h for h in twin.hops if h.id == twin.break_hop_id)
    assert break_hop.stage == HopStage.PAYMENT_RAIL
    assert break_hop.artifacts == []
    matches = match_patterns(twin)
    assert matches[0][0]["id"] == "raast-timeout-no-callback"


def test_switch_decline_breaks_at_payment_switch():
    twin = _twin("TXN2026082000123458")
    break_hop = next(h for h in twin.hops if h.id == twin.break_hop_id)
    assert break_hop.stage == HopStage.PAYMENT_SWITCH
    matches = match_patterns(twin)
    assert matches[0][0]["id"] == "switch-decline-funds-hold"


def test_auth_expired_breaks_at_authentication():
    twin = _twin("TXN2026082000123459")
    break_hop = next(h for h in twin.hops if h.id == twin.break_hop_id)
    assert break_hop.stage == HopStage.AUTHENTICATION
    matches = match_patterns(twin)
    assert matches[0][0]["id"] == "auth-token-expired"


def test_recon_gap_breaks_at_settlement_reconciliation():
    twin = _twin("TXN2026082000123460")
    break_hop = next(h for h in twin.hops if h.id == twin.break_hop_id)
    assert break_hop.stage == HopStage.SETTLEMENT_RECONCILIATION
    # Core banking (the hop before) must be OK — funds genuinely moved.
    core_banking_hop = next(h for h in twin.hops if h.stage == HopStage.CORE_BANKING)
    assert core_banking_hop.status == "ok"
    matches = match_patterns(twin)
    assert matches[0][0]["id"] == "recon-entry-missing"


def test_correlation_is_deterministic():
    twin_a = _twin("TXN2026082000123457")
    twin_b = _twin("TXN2026082000123457")
    assert [h.stage for h in twin_a.hops] == [h.stage for h in twin_b.hops]
    assert [h.status for h in twin_a.hops] == [h.status for h in twin_b.hops]


@pytest.mark.parametrize(
    "reference",
    [
        "TXN2026082000123456",
        "TXN2026082000123457",
        "TXN2026082000123458",
        "TXN2026082000123459",
        "TXN2026082000123460",
    ],
)
def test_twin_hop_sequence_is_always_full_and_ordered(reference):
    twin = _twin(reference)
    assert [h.sequence for h in twin.hops] == list(range(1, 9))
