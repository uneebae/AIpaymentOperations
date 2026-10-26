"""Static list of the seeded fixture references, surfaced to the frontend
so the local demo is usable immediately without a live bank connection.
Clearly a fixture/demo affordance, not a claim of real production data.
"""
from __future__ import annotations

DEMO_REFERENCES = [
    {
        "reference": "TXN2026082000123456",
        "reference_type": "core_transaction_id",
        "label": "Clean transaction",
        "description": "Fully successful Raast P2P transfer — every hop confirmed, no break.",
    },
    {
        "reference": "TXN2026082000123457",
        "reference_type": "core_transaction_id",
        "label": "Rail timeout",
        "description": "Customer debited, but Raast never returned a response code within SLA.",
    },
    {
        "reference": "TXN2026082000123458",
        "reference_type": "core_transaction_id",
        "label": "Switch decline",
        "description": "Payment switch declined the transaction — funds-hold mismatch with core banking.",
    },
    {
        "reference": "TXN2026082000123459",
        "reference_type": "core_transaction_id",
        "label": "Auth token expired",
        "description": "Session token expired before payment initiation — no funds ever moved.",
    },
    {
        "reference": "TXN2026082000123460",
        "reference_type": "core_transaction_id",
        "label": "Reconciliation gap",
        "description": "Both legs posted and confirmed, but the EOD reconciliation file has no matching entry.",
    },
]
