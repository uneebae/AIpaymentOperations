# MVP Scope — 90 days

One rail. One institution. One journey. Read-only. Replayed against history before
it ever touches anything live.

## In scope

- **Rail**: Raast P2P only — highest volume, cleanest failure taxonomy.
- **Connectors (five, exactly)**:
  1. OpenConnect service logs
  2. Payment switch logs
  3. Transaction database (read replica or reporting DB — never primary)
  4. Raast rail response codes
  5. Reconciliation file
- **Correlation**: deterministic stitching of a reference number across those five
  sources (see `ARCHITECTURE.md` / `DATA_MODEL.md`).
- **UI**: timeline view + break detection + evidence panel (React, single
  investigation view — no multi-tenant admin, no user management beyond basic auth).
- **Failure-pattern library**: seeded from internal production incident history for
  Raast P2P specifically. Doesn't need to be exhaustive — needs to cover the patterns
  that actually recur.
- **Agent**: explanation + ranked root causes + drafted recommendation, human-approved
  before any action is taken outside the tool.
- **Export**: incident record as PDF and JSON.

## Explicitly out of scope for v1

- **Any write action** — no posting, reversing, retrying, or releasing payments; no
  config changes; no writes to any connected system, ever, in this milestone or any
  future one without a separate design/security review.
- **Multi-rail correlation** — RTGS, SWIFT, 1LINK etc. are follow-on scope only after
  Raast P2P proves the correlation approach works.
- **Real-time streaming alerts** — MVP is pull-based, on-demand investigation, not a
  monitoring/alerting product.
- **Fraud or AML scoring** — out of scope entirely; this is an operational
  investigation tool, not a risk-scoring tool.
- **Self-serve onboarding** — the design partner is onboarded manually; no
  multi-institution SaaS flow in v1.

## Success criterion

On a replayed set of real historical failures from the design partner, APOE identifies
the correct break point and cause in the large majority of cases, with the evidence a
senior engineer would have cited. Agree the exact accuracy threshold and the replay
test set with the design partner before Week 9 — don't hardcode a number here without
their sign-off, since it becomes the gate for productisation funding.

## Definition of done for the 90-day milestone

- [ ] All five connectors implemented, each independently unit-tested against fixture
      data (no live system required to run the test suite)
- [ ] Correlation engine passes a fixed regression set of hand-labelled historical
      transactions (both clean and broken) with deterministic, reproducible output
- [ ] Failure-pattern library covers the patterns actually observed in the design
      partner's historical incident set — not a hypothetical list
- [ ] Agent output always cites real hops from the twin (enforced at schema level,
      see `DATA_MODEL.md`) — zero uncited claims in a manual audit of the replay set
- [ ] Evidence pack export (PDF + JSON) reviewed against the SBP Technology Risk
      Management Framework's evidence categories for basic structural fit
- [ ] Demo: live walkthrough of 3-5 replayed historical failures, timeline + evidence
      + recommendation, end to end
- [ ] Accuracy result against the agreed threshold, presented plainly — including
      cases where it got it wrong
