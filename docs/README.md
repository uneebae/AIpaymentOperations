# AI Payment Operations Engineer (APOE)

An investigation agent for payment infrastructure. Give it a transaction reference and it
reconstructs what happened across every system the payment touched, identifies where the
flow broke, explains why, shows the evidence, and recommends the next operational action.

This is **not** a chatbot bolted onto logs. It is a **deterministic correlation engine**
(the source of truth) with an **AI reasoning layer** on top (the explanation and
recommendation). The two are architecturally separate — see `GUARDRAILS.md`.

Read the docs in this folder in this order:

1. `README.md` — this file: product promise, scope boundary, repo layout
2. `ARCHITECTURE.md` — the four layers, tech stack, how they talk to each other
3. `DATA_MODEL.md` — the Transaction Digital Twin schema (the core abstraction)
4. `MVP_SCOPE.md` — exactly what ships in the 90-day MVP, and what explicitly doesn't
5. `GUARDRAILS.md` — hard constraints the implementation must never violate
6. `ROADMAP.md` — week-by-week build plan with concrete deliverables
7. `SETUP.md` — how to run the implemented MVP locally (backend + frontend)
8. `API.md` — REST endpoint reference for the implemented backend

## Implementation status

A working MVP implementation lives in `backend/` and `frontend/` at the
repo root (see `SETUP.md` to run it). It covers the Weeks 1-9 shape of
`ROADMAP.md`: all five connectors (fixture-backed, since no live bank
infrastructure is reachable from this environment — see `SETUP.md` for the
swap-to-live-source seam), the deterministic correlation engine, the
LangGraph reasoning agent (Claude-backed when `ANTHROPIC_API_KEY` is set,
deterministic fallback otherwise), failure-library matching, and PDF/JSON
evidence pack export. Local dev defaults to SQLite instead of Postgres to
avoid a hard Docker dependency; `docker-compose.yml` at the repo root
provides the Postgres-backed path described below.

## Product promise

> Give APOE a transaction/reference number and it reconstructs what happened to the
> payment, identifies where the flow broke, explains why, shows the evidence, and
> recommends the next operational action.

## Origin / context

This project responds to a real operational pattern: a payment fails
("customer was debited but the beneficiary never received the funds"), and a senior
engineer manually correlates 10-15 systems by hand — core banking, payment switch,
Raast, 1LINK, APIs, Kafka/MQ, Oracle/PostgreSQL, Keycloak, service logs, YAML config,
SWIFT/ISO 20022 messages, reconciliation reports, settlement files, server/network logs,
deployment artefacts — to find the break point. That correlation work is the product.

Pakistan-specific tailwinds (verify current figures before quoting externally):
- SBP FY2024-25: ~9.1bn retail transactions, ~PKR 612trn value, 88%+ digital.
- Raast: ~1.9bn transactions, ~PKR 44.3trn, since launch through June 2025.
- SBP's Technology Risk Management Framework for Payment Institutions (issued Oct 2025,
  compliance required by 31 March 2026) mandates incident records, root-cause analysis,
  audit trails, configuration/access/recovery/change evidence — which is exactly what
  an APOE investigation produces as a by-product.

## MVP boundary (one line)

**One rail (Raast P2P), one institution, five read-only connectors, no write actions.**
Full detail in `MVP_SCOPE.md`.

## Suggested repo layout

```
apoe/
├── backend/                  # FastAPI service
│   ├── app/
│   │   ├── connectors/       # one module per source system (read-only adapters)
│   │   ├── correlation/      # deterministic engine — no LLM calls in this package
│   │   ├── agent/            # LangGraph reasoning graph — explanation + recommendation
│   │   ├── models/           # Pydantic + SQLAlchemy models (Transaction Digital Twin)
│   │   ├── api/               # REST endpoints
│   │   └── evidence/          # incident/evidence pack generation (PDF/JSON export)
│   ├── tests/
│   └── alembic/               # DB migrations
├── frontend/                  # React app — timeline view, evidence panel
│   └── src/
├── failure-library/            # seed data: known failure patterns, keyed by rail/hop
│   └── raast-p2p/
├── docs/                       # this folder
└── docker-compose.yml           # local: postgres, backend, frontend
```

## Tech stack (proposed, matches existing internal stack)

- **Backend**: FastAPI + PostgreSQL (as used in SDLCAssist)
- **Agent orchestration**: LangGraph multi-agent workflow (as used in SDLCAssist)
- **Reasoning model**: Claude API (as used in OpenWire)
- **Frontend**: React (as used in OpenConnect Config UI, OpenWire)
- **Connector transport**: read-only DB connections, log-shipping/API pull — no
  write credentials anywhere in the connector layer

## Non-negotiable constraints (see GUARDRAILS.md for full detail)

- Every connector is **read-only**. No connector may hold write/delete credentials.
- The correlation engine is **deterministic** — rules and known message/field semantics,
  not model inference. The LLM never decides what happened; it explains what the
  deterministic layer already assembled.
- The agent **never** posts, reverses, retries, or releases a payment, and never writes
  to a production system.
- On-prem / bank-tenancy deployment. Transaction data does not leave the institution's
  boundary — no calling out to hosted infra with raw transaction data unless explicitly
  reconfigured by the design partner.
