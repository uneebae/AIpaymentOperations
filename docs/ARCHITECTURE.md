# Architecture

APOE has four layers. Only one of them is a model.

```
┌─────────────────────────────────────────────────────────────┐
│  4. Evidence Pack                                            │
│     Exportable incident record: timeline, artefacts,         │
│     root cause, actions, recovery. PDF / JSON.                │
├─────────────────────────────────────────────────────────────┤
│  3. Reasoning Agent (LangGraph + Claude API)                  │
│     Explains the assembled timeline in plain language.        │
│     Ranks probable causes against the failure-pattern         │
│     library. Drafts (never executes) a recommendation.        │
├─────────────────────────────────────────────────────────────┤
│  2. Correlation Engine (deterministic — NO LLM calls here)    │
│     Stitches artefacts from every connector to one             │
│     transaction reference, using IDs, message fields,          │
│     timestamps, and known rail semantics. Produces the         │
│     Transaction Digital Twin (see DATA_MODEL.md).              │
├─────────────────────────────────────────────────────────────┤
│  1. Connectors (read-only adapters)                            │
│     One module per source system. Pull-only. No write          │
│     credentials anywhere in this layer.                        │
└─────────────────────────────────────────────────────────────┘
```

## Why the split matters

Layer 2 (correlation) is a hard boundary. It must produce the same output for the same
inputs every time, and it must be independently testable and auditable without ever
calling the model. Layer 3 (reasoning) only ever *reads* the twin that Layer 2 produced —
it cannot alter it, and it cannot fabricate hops that Layer 2 didn't find. If the agent
says "the payment reached the switch," that claim must be traceable to a specific
artefact Layer 2 attached to the twin, not to model inference alone.

This is what "AI investigates, rules and humans decide" means at the code level.

## 1. Connectors

Each connector is a Python module under `backend/app/connectors/` implementing a common
interface:

```python
class Connector(Protocol):
    name: str                     # e.g. "openconnect-logs", "raast-response"
    def fetch(self, ref: TransactionRef, window: TimeWindow) -> list[RawArtifact]: ...
    def healthcheck(self) -> ConnectorStatus: ...
```

- `RawArtifact` is source-agnostic: `{source, timestamp, raw_payload, artifact_type}`.
- Connectors never transform or interpret — that's Layer 2's job. A connector's only
  responsibility is "find everything related to this reference in my system, within
  this time window, and hand it over unmodified."
- Every connector is read-only at the credential level, not just by convention — use a
  DB role or API key that physically cannot write, where the source system supports it.
- MVP connectors (five, matched to MVP_SCOPE.md): OpenConnect service logs, switch logs,
  transaction database, Raast rail response codes, reconciliation file.

## 2. Correlation Engine

Deterministic. Given a transaction reference:

1. Resolve the reference across connectors (some sources key by internal transaction ID,
   some by rail-level reference, some by session ID — resolution rules live here).
2. Assemble `RawArtifact`s into an ordered sequence of `Hop`s (see DATA_MODEL.md).
3. Detect a **break**: the first hop where an expected downstream artifact is missing,
   contradictory, or outside an expected time window, per rule set (not model judgment).
4. Emit a `TransactionDigitalTwin` — the single object everything downstream reads.

Rules are versioned and testable in isolation: given a fixed set of `RawArtifact`s,
the correlation engine's output must be deterministic and unit-testable without any
network or LLM call.

## 3. Reasoning Agent (LangGraph)

Reads a `TransactionDigitalTwin` and produces:
- A plain-language explanation of the timeline
- A ranked list of probable root causes, each citing the specific artifact(s) it's
  drawing on from the twin (no unsourced claims)
- A confidence score per cause, drawn from the failure-pattern library match strength
- A drafted operational recommendation (never auto-executed)

Graph shape (LangGraph), mirroring the multi-agent pattern used in SDLCAssist:
- `explain_node` — narrates the twin's timeline
- `match_node` — matches the twin's break signature against `failure-library/`
- `recommend_node` — drafts the next action, conditioned on match confidence
- `evidence_node` — assembles citations for every claim made above
- `critique_node` — self-correction step: checks the free-text `explanation` and
  `recommendation` against the same facts `evidence_node` used (does the explanation
  name the actual break stage? does the recommendation reference the actual top
  failure-library match?). If not grounded, routes back to `explain_node` with the
  specific gap as feedback; bounded to `MAX_REVISIONS` (currently 1) so the loop always
  terminates. This never touches `root_causes` — those stay deterministic and were
  already schema-enforced before this node runs — it only re-drafts prose.
  `InvestigationResult.self_corrected` records whether a revision pass fired, for audit.

The agent has **no tool access to any write operation**. It can only read the twin and
the failure library, and it can only emit text/structured output. This should be
enforced at the LangGraph tool-binding level, not just by prompt instruction.

## 4. Evidence Pack

Serializes the twin + agent output into an exportable incident record (PDF and JSON).
This is also where SBP Technology Risk Management Framework alignment lives — the export
schema should map cleanly onto: incident record, root-cause analysis, incident timeline,
audit trail, configuration/access/recovery/change evidence.

## API surface (MVP)

```
POST /investigations              # { reference: str } -> starts an investigation
GET  /investigations/{id}         # returns twin + agent output once ready
GET  /investigations/{id}/evidence-pack.pdf
GET  /investigations/{id}/evidence-pack.json
GET  /connectors/status           # healthcheck for all configured connectors
```

## Deployment

On-prem or bank-tenancy. Docker Compose for local/dev. No component should require
egress to a public cloud service except the Claude API call itself — flag this
explicitly in any bank-facing security review, and make the Claude API endpoint
configurable (so a design partner requiring full air-gapping can substitute a
self-hosted model later without an architecture change).
