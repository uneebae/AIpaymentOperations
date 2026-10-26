# API Reference

Base URL (local dev): `http://127.0.0.1:8000/api`. Interactive OpenAPI docs
are auto-served at `http://127.0.0.1:8000/docs`.

All endpoints are read/investigate only — see `GUARDRAILS.md`. There is no
endpoint anywhere in this API that posts, reverses, retries, releases a
payment, or writes to any connected system.

## `POST /investigations`

Runs the full pipeline (correlate → reason) synchronously and returns the
result.

**Request**
```json
{
  "reference": "TXN2026082000123457",
  "reference_type": "core_transaction_id"
}
```
`reference_type` is one of `rail_reference`, `core_transaction_id`,
`session_id` (default `rail_reference`).

**Response** `201` — an `InvestigationResult` (see `DATA_MODEL.md`):
```json
{
  "twin": {
    "id": "…",
    "ref": {"reference": "…", "reference_type": "…", "rail": "raast_p2p"},
    "created_at": "…",
    "hops": [ { "sequence": 1, "stage": "customer_channel", "status": "ok", "artifacts": [...], "notes": null } ],
    "break_hop_id": "… | null",
    "correlation_version": "2026.08.1"
  },
  "explanation": "…",
  "root_causes": [ { "label": "…", "confidence": 0.9, "cited_hop_ids": ["…"], "pattern_id": "raast-timeout-no-callback" } ],
  "recommendation": "…",
  "generated_at": "…",
  "model_version": "apoe-fallback-reasoning-2026.08.1"
}
```

## `GET /investigations`

Returns the 20 most recent investigations (newest first).

## `GET /investigations/{id}`

Returns a single previously-run `InvestigationResult` by its twin id.
`404` if not found.

## `GET /investigations/{id}/evidence-pack.json`

Downloads the same `InvestigationResult`, byte-for-byte serialized — no new
content generated at export time (see `ARCHITECTURE.md`, Layer 4).

## `GET /investigations/{id}/evidence-pack.pdf`

Downloads a formatted incident/evidence record: explanation, timeline
table, root cause candidates, drafted recommendation, and the full
evidence-artifact audit trail, structured to map onto SBP Technology Risk
Management Framework evidence categories.

## `GET /connectors/status`

Healthcheck for all five configured connectors.
```json
[{"name": "openconnect-logs", "healthy": true, "detail": "14 fixture record(s) loaded from openconnect_logs.json"}]
```

## `GET /demo/references`

Static list of the seeded fixture references (see `SETUP.md`), for the
frontend's quick-select chips. Not a production endpoint.

## `GET /health`

Liveness check (outside the `/api` prefix). `{"status": "ok"}`.
