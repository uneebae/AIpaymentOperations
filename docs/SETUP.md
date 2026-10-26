# Local Development Setup

This is the fastest path to a running instance: no Docker required. A Docker
Compose path (Postgres-backed) is also documented below for a more
production-like setup.

## Prerequisites

- Python 3.11+
- Node.js 20+ (tested with Node 24)
- (Optional) Docker + Docker Compose, for the Postgres-backed path
- (Optional) an `ANTHROPIC_API_KEY`, for real Claude-generated reasoning

## 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements-dev.txt   # includes requirements.txt + pytest/ruff

cp .env.example .env   # edit if you have an ANTHROPIC_API_KEY

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now live at `http://127.0.0.1:8000`, with interactive docs at
`http://127.0.0.1:8000/docs`. A local `apoe.db` SQLite file is created
automatically on first run — no external database needed.

For a production deployment, install `requirements.txt` only (no test/lint
tooling) — that's what `Dockerfile` does.

Run the test suite (connectors, correlation engine determinism,
schema-level citation enforcement) and linter:

```bash
pytest
ruff check .
```

## 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Run the frontend test suite (Vitest + React Testing Library), and lint/format
checks (all run in CI):

```bash
npm run test
npm run lint
npm run format:check
```

The app is now live at `http://localhost:5173`. Vite proxies `/api/*`
requests to the backend at `127.0.0.1:8000` (see `vite.config.ts`) — no CORS
configuration needed beyond what's already in `app/main.py`.

Open `http://localhost:5173`, click one of the seeded "fixture reference"
chips, and you'll see a full investigation: timeline, evidence, root cause,
and a drafted recommendation.

## 3. Enabling real Claude-powered reasoning (optional)

By default the reasoning agent (`backend/app/agent/graph.py`) uses a
deterministic, template-based fallback (`backend/app/agent/fallback.py`) —
no API key needed, fully functional offline. To use the real Claude API
instead:

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
```

Restart the backend. `model_version` in the investigation result will
switch from `apoe-fallback-reasoning-*` to `claude-sonnet-5+apoe-agent-*`,
and the explanation/recommendation text will be model-generated (still
strictly grounded in the twin — see the system prompts in
`backend/app/agent/claude_reasoning.py`).

## 4. Docker Compose path (Postgres-backed)

For a setup closer to the intended deployment shape in `README.md`
(Postgres instead of SQLite):

```bash
# from the repo root
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
```

This starts Postgres, the backend (pointed at Postgres via `DATABASE_URL`),
and the frontend, on the same ports as above. Requires Docker Desktop (or
another Docker daemon) running.

## Seeded demo data

Since there's no live bank infrastructure connected in this environment,
the five MVP connectors read from fixture files under
`backend/app/connectors/fixtures/`, covering five reference scenarios:

| Reference              | Scenario                                                      |
|-------------------------|-----------------------------------------------------------------|
| `TXN2026082000123456`   | Clean — every hop OK, no break                                  |
| `TXN2026082000123457`   | Break at the Raast rail — no response code within SLA (timeout)  |
| `TXN2026082000123458`   | Break at the payment switch — funds-hold mismatch decline         |
| `TXN2026082000123459`   | Break at authentication — session token expired, no funds moved   |
| `TXN2026082000123460`   | Break at settlement reconciliation — legs posted, recon file gap  |

Swapping any fixture connector for a live one means implementing the same
`fetch()`/`healthcheck()` contract (`backend/app/connectors/base.py`)
against a real read-only credential — no changes needed anywhere else in
the correlation engine, agent, or API layers.

## Known issues

- `npm audit` flags a moderate/high advisory in `esbuild` (bundled by Vite
  5.4.x) — [GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99).
  It only affects the Vite **dev server** (`npm run dev`) accepting
  cross-origin requests from a browser tab, not the production build. Low
  risk for local-only use; fixing it requires a breaking Vite 8 upgrade,
  which hasn't been taken here to avoid destabilizing the MVP tooling.
