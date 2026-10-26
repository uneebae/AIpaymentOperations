"""HTTP-level tests for the FastAPI layer (app/api/routes.py).

Each test gets its own isolated SQLite file so investigation records from
one test can never leak into another — see the `client` fixture.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes import get_db
from app.db import Base
from app.main import app as fastapi_app
from app.models import orm  # noqa: F401  (registers InvestigationRecord on Base)


@pytest.fixture()
def client(tmp_path):
    """Each test gets its own SQLite file and its own engine/session, wired
    in via FastAPI's dependency_overrides — the app under test is otherwise
    unmodified, so this exercises the real routing/validation/serialization
    path end to end."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test_api.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        # Not entered as a context manager: that would run the app's lifespan
        # (init_db()), which binds the real DATABASE_URL engine and would
        # create/touch the production apoe.db file as a side effect of
        # running tests. Tables are already created above against the
        # test-only engine, so the lifespan hook isn't needed here.
        yield TestClient(fastapi_app)
    finally:
        fastapi_app.dependency_overrides.clear()
        engine.dispose()


KNOWN_REFERENCE = "TXN2026082000123456"
BROKEN_REFERENCE = "TXN2026082000123458"
UNKNOWN_REFERENCE = "TXN-DOES-NOT-EXIST"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_investigation_for_clean_reference_returns_201(client):
    response = client.post(
        "/api/investigations",
        json={"reference": KNOWN_REFERENCE, "reference_type": "core_transaction_id"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["twin"]["ref"]["reference"] == KNOWN_REFERENCE
    assert body["twin"]["break_hop_id"] is None
    assert body["root_causes"] == []


def test_create_investigation_for_broken_reference_has_root_causes(client):
    response = client.post(
        "/api/investigations",
        json={"reference": BROKEN_REFERENCE, "reference_type": "core_transaction_id"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["twin"]["break_hop_id"] is not None
    assert len(body["root_causes"]) >= 1


def test_create_investigation_for_unknown_reference_still_returns_a_twin(client):
    """No connector has data for this reference, so every hop should come
    back as an empty/break-like read rather than the API erroring out."""
    response = client.post(
        "/api/investigations",
        json={"reference": UNKNOWN_REFERENCE, "reference_type": "core_transaction_id"},
    )
    assert response.status_code == 201
    assert response.json()["twin"]["ref"]["reference"] == UNKNOWN_REFERENCE


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"reference": "TXN1", "reference_type": "not-a-real-type"},
    ],
)
def test_create_investigation_rejects_invalid_payload(client, payload):
    response = client.post("/api/investigations", json=payload)
    assert response.status_code == 422


def test_create_investigation_defaults_reference_type_to_rail_reference(client):
    """reference_type is optional on the request — confirms the declared
    default (InvestigationRequest.reference_type = 'rail_reference') is
    actually applied rather than the field silently becoming required."""
    response = client.post("/api/investigations", json={"reference": "TXN1"})
    assert response.status_code == 201
    assert response.json()["twin"]["ref"]["reference_type"] == "rail_reference"


def test_list_investigations_starts_empty(client):
    response = client.get("/api/investigations")
    assert response.status_code == 200
    assert response.json() == []


def test_list_investigations_returns_newest_first(client):
    first = client.post(
        "/api/investigations", json={"reference": KNOWN_REFERENCE, "reference_type": "core_transaction_id"}
    ).json()
    second = client.post(
        "/api/investigations", json={"reference": BROKEN_REFERENCE, "reference_type": "core_transaction_id"}
    ).json()

    response = client.get("/api/investigations")
    assert response.status_code == 200
    ids = [item["twin"]["id"] for item in response.json()]
    assert ids[0] == second["twin"]["id"]
    assert second["twin"]["id"] != first["twin"]["id"]


def test_get_investigation_by_id_round_trips(client):
    created = client.post(
        "/api/investigations", json={"reference": KNOWN_REFERENCE, "reference_type": "core_transaction_id"}
    ).json()
    investigation_id = created["twin"]["id"]

    response = client.get(f"/api/investigations/{investigation_id}")
    assert response.status_code == 200
    assert response.json()["twin"]["id"] == investigation_id


def test_get_investigation_unknown_id_returns_404(client):
    response = client.get(f"/api/investigations/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Investigation not found"


def test_evidence_pack_json_download(client):
    created = client.post(
        "/api/investigations", json={"reference": BROKEN_REFERENCE, "reference_type": "core_transaction_id"}
    ).json()
    investigation_id = created["twin"]["id"]

    response = client.get(f"/api/investigations/{investigation_id}/evidence-pack.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert f"evidence-pack-{investigation_id}.json" in response.headers["content-disposition"]
    assert response.json()["twin"]["id"] == investigation_id


def test_evidence_pack_pdf_download(client):
    created = client.post(
        "/api/investigations", json={"reference": BROKEN_REFERENCE, "reference_type": "core_transaction_id"}
    ).json()
    investigation_id = created["twin"]["id"]

    response = client.get(f"/api/investigations/{investigation_id}/evidence-pack.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_evidence_pack_for_unknown_id_returns_404(client):
    missing_id = uuid.uuid4()
    assert client.get(f"/api/investigations/{missing_id}/evidence-pack.json").status_code == 404
    assert client.get(f"/api/investigations/{missing_id}/evidence-pack.pdf").status_code == 404


def test_connectors_status_reports_all_five_connectors_healthy(client):
    response = client.get("/api/connectors/status")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert all(entry["healthy"] is True for entry in body)


def test_demo_references_returns_seeded_fixtures(client):
    response = client.get("/api/demo/references")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert {"reference", "reference_type", "label", "description"} <= body[0].keys()


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/api/demo/references",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
