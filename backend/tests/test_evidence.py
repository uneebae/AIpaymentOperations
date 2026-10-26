"""Evidence pack export (app/evidence/json_export.py, pdf_export.py) —
pure serialization of an already-validated InvestigationResult."""
from __future__ import annotations

import json

from app.agent.graph import investigate
from app.connectors.registry import CONNECTORS
from app.correlation.engine import correlate
from app.evidence.json_export import to_json_bytes
from app.evidence.pdf_export import to_pdf_bytes
from app.models.schemas import TransactionRef


def _result(reference: str):
    ref = TransactionRef(reference=reference, reference_type="core_transaction_id")
    twin = correlate(ref, CONNECTORS)
    return investigate(twin)


def test_json_export_round_trips_through_json_parser():
    result = _result("TXN2026082000123458")
    payload = json.loads(to_json_bytes(result))
    assert payload["twin"]["id"] == str(result.twin.id)
    assert payload["root_causes"][0]["label"] == result.root_causes[0].label


def test_json_export_is_utf8_encoded_bytes():
    result = _result("TXN2026082000123456")
    raw = to_json_bytes(result)
    assert isinstance(raw, bytes)
    raw.decode("utf-8")  # must not raise


def test_pdf_export_produces_a_valid_pdf_header():
    result = _result("TXN2026082000123458")
    raw = to_pdf_bytes(result)
    assert isinstance(raw, bytes)
    assert raw.startswith(b"%PDF-")
    assert raw.rstrip().endswith(b"%%EOF")


def test_pdf_export_handles_clean_transaction_with_no_root_causes():
    result = _result("TXN2026082000123456")
    assert result.root_causes == []
    raw = to_pdf_bytes(result)
    assert raw.startswith(b"%PDF-")


def test_pdf_export_is_non_trivial_size_for_a_full_investigation():
    result = _result("TXN2026082000123460")
    raw = to_pdf_bytes(result)
    assert len(raw) > 1000
