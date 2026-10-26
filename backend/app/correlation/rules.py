"""Stage -> expected-artifact rules and outcome extraction.

These are the "known message/field semantics" referenced in
docs/ARCHITECTURE.md: which connector and artifact_type is expected to
back each hop stage, and how to read a success/failure outcome out of a
raw artifact's payload. No model inference anywhere in this module.
"""
from __future__ import annotations

from collections.abc import Callable

from app.models.schemas import HopStage

PayloadFilter = Callable[[dict], bool]

# stage -> list of (connector_name, artifact_type, optional payload filter)
STAGE_ARTIFACT_RULES: dict[HopStage, list[tuple[str, str, PayloadFilter | None]]] = {
    HopStage.CUSTOMER_CHANNEL: [
        ("openconnect-logs", "channel_request", None),
    ],
    HopStage.AUTHENTICATION: [
        ("openconnect-logs", "auth_event", None),
    ],
    HopStage.PAYMENT_API: [
        ("openconnect-logs", "api_call", None),
        ("transaction-db", "db_row", lambda p: p.get("table") == "payment_initiation"),
    ],
    HopStage.PAYMENT_SWITCH: [
        ("payment-switch-logs", "switch_log", None),
    ],
    HopStage.PAYMENT_RAIL: [
        ("raast-response", "response_code", None),
    ],
    HopStage.RECEIVING_INSTITUTION: [
        ("raast-response", "beneficiary_ack", None),
    ],
    HopStage.CORE_BANKING: [
        ("transaction-db", "db_row", lambda p: p.get("table") == "ledger_posting"),
    ],
    HopStage.SETTLEMENT_RECONCILIATION: [
        ("reconciliation-file", "recon_entry", None),
    ],
}

SUCCESS_VALUES = {"success", "ok", "completed", "accepted", "matched", "valid", "passed", "credited", "confirmed"}


def extract_outcome(payload: dict) -> str:
    """Read a canonical outcome out of a raw artifact payload.

    Looks at status/outcome/result, in that order. Anything not in
    SUCCESS_VALUES is treated as a failing outcome and returned verbatim
    (e.g. "declined", "expired", "timeout") so it can be surfaced in the
    hop's notes and matched against the failure library.
    """
    for key in ("status", "outcome", "result"):
        if key in payload:
            value = str(payload[key]).lower()
            return "success" if value in SUCCESS_VALUES else value
    return "success"
