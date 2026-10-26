# Guardrails

These are implementation constraints, not aspirations. Code review should block a
merge that violates any of these, and it's worth writing an automated check for the
ones that can be checked mechanically (marked below).

## What the system may do

- Assemble and replay a transaction timeline from read-only sources
- Explain what an artifact means in plain language
- Rank probable root causes with confidence and evidence, citing real hops
- Draft an operational recommendation for a human to review
- Draft the incident/evidence record
- Surface similar past incidents from the failure-pattern library

## What the system must never do

- **Post, reverse, retry, or release a payment** — no code path anywhere in the system
  should be capable of this, not just "the agent won't be prompted to." *(Check: audit
  every outbound network call in the codebase; none should target a payment-mutating
  endpoint.)*
- **Change configuration in a live environment** — connectors are read-only at the
  credential level. *(Check: grep connector configs for write-capable credentials/roles;
  fail CI if found.)*
- **Make a compliance or AML determination** — the agent explains and recommends; it
  does not conclude "this is fraud" or "this is compliant."
- **Decide customer remediation or refunds** — out of scope for the agent's output
  entirely.
- **Write to any connected production system** — no connector, no agent tool, no export
  function should hold a write path to a source system. *(Check: this should be
  enforceable as a static property of the connector interface — see `Connector`
  protocol in `ARCHITECTURE.md`, which only exposes `fetch()` and `healthcheck()`.)*
- **Act on an unverified inference** — every claim the agent makes must cite a specific
  artifact already present in the twin. *(Check: enforced at the `RootCauseCandidate`
  schema level — `cited_hop_ids` must resolve to real `Hop.id`s in the twin; reject at
  validation if not.)*

## Data boundary

- Transaction data does not leave the institution's boundary by default. The Claude API
  call is the one component that, in a hosted-model configuration, sends data outside
  the deployment perimeter — this must be:
  - Clearly disclosed in any security review, not discovered by the bank later
  - Configurable, so a design partner requiring full air-gapping can swap in a
    self-hosted model without an architecture rewrite (keep the model call behind an
    interface, not hardcoded to the Claude API directly)
- No raw transaction data should appear in logs, error messages, or telemetry sent
  outside the deployment. Redact or hash reference numbers and account details in
  anything that leaves the perimeter (application logs, crash reporting, etc.).

## Review checklist for any new connector

Before merging a new connector, confirm:
- [ ] Uses a credential that is read-only at the source-system level (DB role, API
      scope), not just "the code happens not to call write methods"
- [ ] `fetch()` returns unmodified `RawArtifact`s — no interpretation, no filtering
      logic that could hide a relevant artifact
- [ ] Has fixture-based unit tests that don't require a live connection
- [ ] Logs its own activity without leaking raw transaction data outside the perimeter

## Review checklist for any change to the agent layer

- [ ] No new tool binding gives the agent a write-capable function
- [ ] Every new claim type the agent can emit has a corresponding citation requirement
- [ ] Prompts are additive to these guardrails, never a substitute for the schema-level
      enforcement above — assume the prompt will eventually be bypassed by an edge case
      and the schema is the real backstop
