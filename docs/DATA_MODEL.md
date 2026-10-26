# Data Model — the Transaction Digital Twin

The twin is the single object that the correlation engine produces and everything else
(agent, evidence pack, frontend) reads. It never contains model-generated content —
only what the deterministic layer assembled from real artifacts.

## Core entities

### `TransactionRef`
The user-supplied starting point.
```python
class TransactionRef(BaseModel):
    reference: str            # what the ops engineer typed in — rail ref, core ref, etc.
    reference_type: Literal["rail_reference", "core_transaction_id", "session_id"]
    rail: Literal["raast_p2p"]  # MVP: single rail
```

### `RawArtifact`
What a connector returns — unmodified, source-agnostic.
```python
class RawArtifact(BaseModel):
    id: UUID
    source: str                # connector name, e.g. "openconnect-logs"
    artifact_type: str          # e.g. "log_line", "db_row", "response_code", "recon_entry"
    timestamp: datetime
    raw_payload: dict           # untouched source data
```

### `Hop`
One step in the payment's journey, built by the correlation engine from one or more
`RawArtifact`s.
```python
class Hop(BaseModel):
    id: UUID
    sequence: int                       # ordering within the twin
    stage: HopStage                     # enum, see below
    status: Literal["ok", "break", "unknown"]
    artifacts: list[RawArtifact]         # every artifact backing this hop — required
                                          # for evidence citation; a hop with no
                                          # artifacts cannot be marked "ok"
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None                    # deterministic-layer notes only, not agent text

class HopStage(str, Enum):
    CUSTOMER_CHANNEL = "customer_channel"
    AUTHENTICATION = "authentication"
    PAYMENT_API = "payment_api"
    PAYMENT_SWITCH = "payment_switch"
    PAYMENT_RAIL = "payment_rail"
    RECEIVING_INSTITUTION = "receiving_institution"
    CORE_BANKING = "core_banking"
    SETTLEMENT_RECONCILIATION = "settlement_reconciliation"
```

### `TransactionDigitalTwin`
```python
class TransactionDigitalTwin(BaseModel):
    id: UUID
    ref: TransactionRef
    created_at: datetime
    hops: list[Hop]                      # ordered by sequence
    break_hop_id: UUID | None            # set by correlation engine, not the agent
    correlation_version: str             # rule-set version that produced this twin
```

### Agent output (kept separate from the twin — never merged in)
```python
class RootCauseCandidate(BaseModel):
    label: str
    confidence: float                    # from failure-library match strength
    cited_hop_ids: list[UUID]            # must reference real hops — no orphan claims
    pattern_id: str | None               # matched entry in failure-library/, if any

class InvestigationResult(BaseModel):
    twin: TransactionDigitalTwin
    explanation: str                     # plain-language narrative of the twin
    root_causes: list[RootCauseCandidate]
    recommendation: str                  # drafted next action — never auto-executed
    generated_at: datetime
    model_version: str
```

## Why this separation matters for implementation

- Unit tests for the correlation engine operate entirely on `RawArtifact` → `Hop` →
  `TransactionDigitalTwin`, with zero mocking of the LLM.
- The agent layer's contract is narrow: it receives a `TransactionDigitalTwin` and
  returns an `InvestigationResult`. It cannot mutate the twin it was given.
- Every claim in `RootCauseCandidate.cited_hop_ids` must resolve to a real `Hop.id` in
  the twin — enforce this at the schema/validation level so the agent literally cannot
  emit an uncited claim.
- The evidence pack is a pure serialization of `InvestigationResult` — no new content
  is generated at export time.

## Failure-pattern library shape

`failure-library/raast-p2p/*.yaml` — one file per known pattern, matched against a
twin's break signature (which hop broke, what artifact was missing/contradictory).

```yaml
id: raast-timeout-no-callback
label: "Rail timeout — no callback received from Raast within SLA window"
rail: raast_p2p
break_stage: payment_rail
signature:
  missing_artifact_type: "response_code"
  expected_within_seconds: 30
typical_recommendation: >
  Confirm with 1LINK/Raast operations whether the transaction was received.
  If unconfirmed after {sla_window}, initiate a status-enquiry message before
  advising the customer.
seed_source: "internal incident history"   # fill in during Weeks 4-8, see ROADMAP.md
```
