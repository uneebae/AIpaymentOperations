# How AI Is Used in This Project, and Why It Matters for Banking

This document explains, concretely, where and how AI is used inside **AI
Payment Operations Engineer (APOE)**, what problem it solves for a payments
organization, and why the specific way it's used — bounded, cited,
non-executing — is the part that actually matters for a regulated banking
environment.

Repo: [github.com/uneebae/AIpaymentOperations](https://github.com/uneebae/AIpaymentOperations)

---

## 1. The problem this project solves

When a Raast P2P (person-to-person) payment fails or behaves unexpectedly,
finding out *why* today typically means a payment operations engineer
manually:

1. Pulling logs from the customer channel / mobile app backend
2. Pulling logs from the authentication service
3. Querying the core transaction database
4. Pulling switch logs from the payment switch
5. Checking the rail's (Raast) response codes
6. Checking the end-of-day reconciliation file
7. Manually lining all of this up by timestamp and transaction ID, by hand,
   across five different systems with five different data shapes
8. Pattern-matching the failure against institutional memory of "we've seen
   this before" — often tribal knowledge that lives in one or two senior
   engineers' heads
9. Writing up an incident record for audit, compliance, and the customer
   complaint process

This is slow (minutes to hours per case), inconsistent (two engineers
investigating the same failure can reach different conclusions depending on
experience), and poorly documented (the reasoning behind "why we think this
broke here" often isn't captured anywhere durable).

At scale — a bank processing thousands of P2P transactions a day, with even
a small failure rate — this becomes a real operational cost center and a
real audit-trail gap.

---

## 2. Where AI is actually used — and where it deliberately is not

This is the single most important design decision in the project, so it's
worth stating plainly: **most of the system is not AI at all.**

```
┌─────────────────────────────────────────────────────────────┐
│  4. Evidence Pack            — pure serialization, no AI     │
├─────────────────────────────────────────────────────────────┤
│  3. Reasoning Agent          — AI lives here, and ONLY here  │
├─────────────────────────────────────────────────────────────┤
│  2. Correlation Engine       — deterministic rules, no AI    │
├─────────────────────────────────────────────────────────────┤
│  1. Connectors               — read-only data pulls, no AI   │
└─────────────────────────────────────────────────────────────┘
```

**Layers 1, 2, and 4 — no AI, by design.** Pulling data from source systems,
stitching it into a timeline, and detecting *where* a flow broke is done
entirely with deterministic, rule-based code (`backend/app/correlation/`).
Given the same inputs, this layer produces the exact same output every
single time — it's unit-tested like any other business logic, with no
network or model call involved. This is the part of the system a bank's
model-risk and audit functions can treat as ordinary software, not as an AI
system requiring model governance.

**Layer 3 — this is where AI is used.** Once the facts are already
established (what happened, in what order, where it broke), a reasoning
agent built with **LangGraph** and **Claude** (`claude-sonnet-5`) is used
for exactly three things:

1. **Narrating the timeline in plain language** — turning eight structured
   `Hop` records into a readable paragraph a non-technical stakeholder
   (compliance, a customer-facing agent, an auditor) can understand without
   reading raw logs.
2. **Ranking which known failure pattern this most resembles** — matching
   against a YAML-based failure-pattern library (`backend/failure-library/`)
   and expressing a confidence score.
3. **Drafting one recommended next action** for a human engineer to review
   — e.g., "escalate to the switch team; this matches a funds-hold decline
   pattern" — never executing it.

That's the entire footprint of generative AI in this system. Everything
upstream of it (data gathering, break detection) and downstream of it
(evidence export) is ordinary deterministic code.

---

## 3. How the AI layer is implemented

### 3.1 The agent only ever reads — it never writes

The reasoning agent (`backend/app/agent/graph.py`) is given a
`TransactionDigitalTwin` — the already-assembled, already-validated record
of what happened. It has:

- **No tool binding to any write operation.** It cannot post, reverse,
  retry, or release a payment. This isn't a prompt instruction asking it
  nicely not to — there is no tool in its LangGraph tool set that performs a
  write, anywhere in the codebase.
- **No ability to alter the facts it's reasoning about.** The twin it reads
  was already built by the deterministic correlation engine before the
  agent ever runs.

### 3.2 Every AI-generated claim is schema-enforced to cite real evidence

This is the guardrail that makes the AI output trustworthy enough to use in
an audit context. Every `RootCauseCandidate` the agent proposes must cite a
real `Hop.id` from the twin — and this isn't checked by the prompt or by
convention, it's enforced by a Pydantic model validator
(`InvestigationResult._citations_resolve_to_real_hops` in
`backend/app/models/schemas.py`) that runs on *every construction* of the
result object, including when it's read back out of the database later.

```python
@model_validator(mode="after")
def _citations_resolve_to_real_hops(self) -> InvestigationResult:
    hop_ids = {h.id for h in self.twin.hops}
    for cause in self.root_causes:
        unknown = [str(hid) for hid in cause.cited_hop_ids if hid not in hop_ids]
        if unknown:
            raise ValueError(f"root cause '{cause.label}' cites unknown hop id(s): {unknown}")
    return self
```

If a model (now or in some future version) ever produced a fabricated or
uncited claim, the object simply fails to construct. The hallucination
cannot reach the API response, the database, or the exported evidence pack
— it's rejected before it exists as output.

### 3.3 A bounded self-correction loop, grounded in facts, not opinion

The LangGraph state machine includes a `critique_node` that checks the
agent's own free-text output against the same facts the deterministic
`evidence_node` already assembled:

- Does the explanation actually name the stage where the break occurred?
- Does the recommendation actually reference the top-matched failure
  pattern?

If not, it's sent back for exactly one revision (`MAX_REVISIONS = 1`) with
specific, factual feedback — not "try again," but "you must name the stage
where the break occurred: the payment switch." This is self-correction
against ground truth, not model-vs-model debate, and it's capped so the
loop is guaranteed to terminate. Whether a revision fired is recorded on
every result (`self_corrected: bool`) for audit purposes.

### 3.4 The AI is optional, and the system is useful either way

If no `ANTHROPIC_API_KEY` is configured, `backend/app/agent/fallback.py`
produces the same *shape* of output — explanation, ranked causes,
recommendation — using deterministic string templates instead of a model
call. This means:

- The system is fully functional and demoable with zero API dependency.
- A bank that wants to pilot the deterministic correlation/evidence layers
  first, before approving any model usage at all, can do so — the AI layer
  is additive, not load-bearing for the core value.
- The one component allowed to send data outside the deployment perimeter
  (`claude_reasoning.py`) is isolated behind a narrow two-function interface
  specifically so a bank requiring a self-hosted or air-gapped model can
  swap it in without touching anything else in the system.

---

## 4. Why this matters for the banking domain specifically

### 4.1 It targets a real, expensive, recurring operational cost

Payment investigation is not a hypothetical use case — it's a standing cost
center at every bank that runs a real-time payment rail. Every minute an
ops engineer spends manually correlating five systems by hand is a minute
not spent on the next case, and P2P rails like Raast generate investigation
volume proportional to transaction volume. Automating the "what happened and
where" part of this — the 80% that's mechanical, not judgment-based — is
where the time actually goes.

### 4.2 It respects the thing banks actually care about: auditability over autonomy

A common failure mode of "AI for banking" pitches is proposing systems that
are impressive but ungovernable — a model that takes actions, or whose
output can't be traced back to a specific, inspectable fact. This project
is built the opposite way:

- **Every factual claim is traceable.** Open the evidence pack PDF/JSON for
  any investigation and every root cause links to a specific artifact from
  a specific source system at a specific timestamp — not "the model said
  so."
- **The deterministic core can be audited without reference to the AI at
  all.** A risk/compliance reviewer can verify the correlation engine's
  break-detection logic the same way they'd review any other piece of
  transaction-monitoring code — because it is exactly that: ordinary rule
  based logic, versioned (`correlation_version`) and unit-tested, with no
  model in the loop.
- **The AI's blast radius is scoped to narration and ranking**, the two
  tasks LLMs are actually good at and where a wrong answer is
  "a confusing paragraph," not "an incorrect financial action." The tasks
  with real consequences — what happened, where it broke, what the
  evidence is — stay deterministic.

### 4.3 It maps directly onto existing regulatory evidence categories

The evidence pack (`backend/app/evidence/pdf_export.py`) is structured to
align with standard technology risk-management evidence categories: an
incident record, root-cause analysis, an incident timeline, and an audit
trail of evidence artifacts. That's a deliberate choice — the output of an
AI-assisted investigation should slot into the same audit and complaint
handling workflows a bank already runs, not require a new one.

### 4.4 It demonstrates a reusable pattern for AI adoption in regulated environments

Beyond this specific tool, the architecture is a template for how a bank
can adopt generative AI in *any* operational workflow without taking on
model risk it can't explain to a regulator:

1. Keep deterministic, auditable logic doing anything where correctness is
   load-bearing.
2. Give the model only already-verified facts to work with — never let it
   be the source of a fact.
3. Enforce any claim the model makes against those same facts at the
   schema/data layer, not just the prompt layer.
4. Never grant the model a tool capable of a write/execute action.
5. Make the model swap-able (including swapping it out entirely) without
   an architecture change, so model-risk policy can evolve independently of
   the rest of the system.

### 4.5 Concrete time/consistency gains

- **Narration**: a plain-language summary of an 8-hop timeline that would
  otherwise require a human to read and reconcile five raw log formats —
  generated in seconds, consistently formatted every time.
- **Pattern matching**: ranking a break against a growing, versioned
  failure-pattern library turns "does this look like something we've seen
  before" from tribal knowledge into a queryable, auditable artifact
  (`backend/failure-library/raast-p2p/*.yaml`) that survives staff turnover.
- **First-draft recommendations**: engineers review and approve a drafted
  action instead of composing one from scratch for every case — faster,
  without removing the human decision point the regulator (and the bank's
  own risk appetite) requires.

---

## 5. Summary

AI in this project is used for exactly one thing: **turning
already-verified facts into a readable explanation, a ranked hypothesis,
and a draft recommendation** — never for determining what the facts are,
never for taking an action, and never in a way that can't be traced back to
specific evidence. That narrow, bounded scope is precisely what makes it
viable in a banking context: it removes real manual effort from a real
operational bottleneck, while leaving every decision a bank is regulated on
— what happened, and what to do about it — fully auditable and in human
hands.
