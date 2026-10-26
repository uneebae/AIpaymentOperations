# Roadmap — 90-day MVP

Three phases, matched to the pitch deck's timeline. Each phase ends with something
demonstrable, not just code merged.

## Weeks 1-3 — Foundation: connectors + deterministic correlation

**Goal**: given a fixture set of raw artifacts, the correlation engine produces a
correct, deterministic `TransactionDigitalTwin` — with zero live systems and zero
LLM calls involved.

- [ ] Set up repo skeleton per `README.md` layout, Docker Compose (Postgres + backend)
- [ ] Define core schemas from `DATA_MODEL.md` (`RawArtifact`, `Hop`, `TransactionDigitalTwin`)
- [ ] Implement the `Connector` protocol and one connector against a fixture (not live)
- [ ] Implement remaining four connectors against fixtures
- [ ] Implement the correlation engine: reference resolution, hop assembly, break
      detection — pure functions, fully unit-tested against hand-built fixture sets
      covering both clean and broken transactions
- [ ] Wire one connector to a real (read-only) source in a dev/UAT environment, confirm
      `RawArtifact`s coming back match what fixtures assumed
- **Exit check**: correlation engine passes a regression suite of ~10-15 hand-labelled
  fixture transactions with reproducible output; no LLM in the loop yet.

## Weeks 4-8 — Investigation surface: timeline, break detection, failure library

**Goal**: an operations engineer can enter a reference number and see a real timeline
with a break clearly marked, backed by real evidence — no agent narration yet.

- [ ] Remaining connectors wired to real (read-only) sources in dev/UAT
- [ ] `POST /investigations`, `GET /investigations/{id}` endpoints
- [ ] React timeline view: hops rendered in sequence, break hop visually flagged,
      evidence panel showing the artifacts backing each hop
- [ ] Seed `failure-library/raast-p2p/` from internal production incident history —
      this is a data-collection task as much as a code task; work with whoever holds
      the historical incident tickets
- [ ] Break-signature matching: given a twin's break hop, find candidate matches in the
      failure library (this can still be deterministic/rule-based, not LLM-based)
- **Exit check**: a real (replayed, not live) transaction reference produces a correct
  timeline and break flag in the UI, matched against a failure-library entry where one
  applies.

## Weeks 9-12 — Reasoning layer, evidence pack, accuracy test

**Goal**: full pipeline demo against replayed real historical failures, with an
accuracy result to bring to the decision gate.

- [ ] LangGraph agent: explain_node, match_node, recommend_node, evidence_node (see
      `ARCHITECTURE.md`)
- [ ] Enforce citation requirements at the schema level (`RootCauseCandidate.cited_hop_ids`)
- [ ] Evidence pack export: PDF + JSON, structured to map onto SBP Technology Risk
      Management Framework evidence categories
- [ ] Agree the replay test set and accuracy threshold with the design partner
- [ ] Run the replay test set end to end; record accuracy, and characterise the misses
      honestly — this result is what the decision-gate demo is built on
- [ ] Prepare the demo: 3-5 replayed historical failures walked through live, plus the
      accuracy result across the full replay set
- **Exit check**: accuracy result against the agreed threshold, demo-ready.

## After the gate

Everything past this point is out of scope for this roadmap and depends on the
decision-gate outcome — see `MVP_SCOPE.md` for what's explicitly excluded from v1
(multi-rail correlation, real-time alerts, write actions, fraud/AML scoring,
self-serve onboarding).
