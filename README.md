# AI Payment Operations Engineer (APOE)

An investigation agent for payment infrastructure. Give it a transaction
reference and it reconstructs what happened across every system the
payment touched, identifies where the flow broke, explains why, shows the
evidence, and recommends the next operational action — for Raast P2P, MVP
scope.

Full product docs live in [`docs/`](docs/README.md) — start there for the
product promise, architecture, data model, guardrails, and roadmap.

## Quick start

```bash
# backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # or: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and click one of the seeded fixture
references. Full instructions, including the optional Postgres/Docker path
and enabling real Claude-powered reasoning: [`docs/SETUP.md`](docs/SETUP.md).

## Repo layout

```
├── backend/            FastAPI service — connectors, correlation engine,
│                        LangGraph agent, evidence pack export, REST API
├── frontend/            React + TypeScript — timeline, evidence, and
│                        recommendation UI
├── docs/                 Product and architecture documentation
└── docker-compose.yml     Optional Postgres-backed local stack
```

## Non-negotiable constraints

Every connector is read-only. The correlation engine is deterministic —
the AI reasoning layer only ever explains and drafts recommendations for a
human to approve; it never posts, reverses, retries, or releases a payment,
and never writes to any connected system. Full detail in
[`docs/GUARDRAILS.md`](docs/GUARDRAILS.md).
