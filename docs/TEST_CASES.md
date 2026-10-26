# Test Cases

Full inventory of the automated test suite: **79 tests, 79 passing, 0 failing**
as of the last run (backend: 53, frontend: 26).

Run them yourself:

```bash
# backend (from backend/)
pytest -q

# frontend (from frontend/)
npm run test
```

---

## Backend — `pytest` (53 tests)

### `tests/test_agent.py` — reasoning graph / self-correction (6)

| # | Test | Result |
|---|------|--------|
| 1 | `test_investigation_result_citations_resolve_to_real_hops` | ✅ Pass |
| 2 | `test_clean_transaction_has_no_root_causes` | ✅ Pass |
| 3 | `test_broken_transaction_has_at_least_one_root_cause` | ✅ Pass |
| 4 | `test_fallback_path_never_self_corrects` | ✅ Pass |
| 5 | `test_critique_node_flags_ungrounded_explanation_and_recommendation` | ✅ Pass |
| 6 | `test_critique_node_passes_grounded_text` | ✅ Pass |

### `tests/test_api.py` — HTTP layer / FastAPI routes (17)

| # | Test | Result |
|---|------|--------|
| 1 | `test_health_check` | ✅ Pass |
| 2 | `test_create_investigation_for_clean_reference_returns_201` | ✅ Pass |
| 3 | `test_create_investigation_for_broken_reference_has_root_causes` | ✅ Pass |
| 4 | `test_create_investigation_for_unknown_reference_still_returns_a_twin` | ✅ Pass |
| 5 | `test_create_investigation_rejects_invalid_payload[payload0]` (`{}`) | ✅ Pass |
| 6 | `test_create_investigation_rejects_invalid_payload[payload1]` (bad `reference_type`) | ✅ Pass |
| 7 | `test_create_investigation_defaults_reference_type_to_rail_reference` | ✅ Pass |
| 8 | `test_list_investigations_starts_empty` | ✅ Pass |
| 9 | `test_list_investigations_returns_newest_first` | ✅ Pass |
| 10 | `test_get_investigation_by_id_round_trips` | ✅ Pass |
| 11 | `test_get_investigation_unknown_id_returns_404` | ✅ Pass |
| 12 | `test_evidence_pack_json_download` | ✅ Pass |
| 13 | `test_evidence_pack_pdf_download` | ✅ Pass |
| 14 | `test_evidence_pack_for_unknown_id_returns_404` | ✅ Pass |
| 15 | `test_connectors_status_reports_all_five_connectors_healthy` | ✅ Pass |
| 16 | `test_demo_references_returns_seeded_fixtures` | ✅ Pass |
| 17 | `test_cors_allows_configured_frontend_origin` | ✅ Pass |

### `tests/test_connectors.py` — fixture connectors (4)

| # | Test | Result |
|---|------|--------|
| 1 | `test_all_connectors_healthy` | ✅ Pass |
| 2 | `test_known_reference_returns_artifacts` | ✅ Pass |
| 3 | `test_unknown_reference_returns_nothing` | ✅ Pass |
| 4 | `test_fetch_is_read_only_interface` | ✅ Pass |

### `tests/test_correlation.py` — correlation engine (11)

| # | Test | Result |
|---|------|--------|
| 1 | `test_clean_transaction_has_no_break` | ✅ Pass |
| 2 | `test_rail_timeout_breaks_at_payment_rail` | ✅ Pass |
| 3 | `test_switch_decline_breaks_at_payment_switch` | ✅ Pass |
| 4 | `test_auth_expired_breaks_at_authentication` | ✅ Pass |
| 5 | `test_recon_gap_breaks_at_settlement_reconciliation` | ✅ Pass |
| 6 | `test_correlation_is_deterministic` | ✅ Pass |
| 7 | `test_twin_hop_sequence_is_always_full_and_ordered[TXN2026082000123456]` | ✅ Pass |
| 8 | `test_twin_hop_sequence_is_always_full_and_ordered[TXN2026082000123457]` | ✅ Pass |
| 9 | `test_twin_hop_sequence_is_always_full_and_ordered[TXN2026082000123458]` | ✅ Pass |
| 10 | `test_twin_hop_sequence_is_always_full_and_ordered[TXN2026082000123459]` | ✅ Pass |
| 11 | `test_twin_hop_sequence_is_always_full_and_ordered[TXN2026082000123460]` | ✅ Pass |

### `tests/test_evidence.py` — JSON/PDF export (5)

| # | Test | Result |
|---|------|--------|
| 1 | `test_json_export_round_trips_through_json_parser` | ✅ Pass |
| 2 | `test_json_export_is_utf8_encoded_bytes` | ✅ Pass |
| 3 | `test_pdf_export_produces_a_valid_pdf_header` | ✅ Pass |
| 4 | `test_pdf_export_handles_clean_transaction_with_no_root_causes` | ✅ Pass |
| 5 | `test_pdf_export_is_non_trivial_size_for_a_full_investigation` | ✅ Pass |

### `tests/test_schemas.py` — Pydantic guardrails (10)

| # | Test | Result |
|---|------|--------|
| 1 | `test_hop_ok_status_requires_at_least_one_artifact` | ✅ Pass |
| 2 | `test_hop_break_status_allows_empty_artifacts` | ✅ Pass |
| 3 | `test_twin_break_hop_id_must_reference_a_real_hop` | ✅ Pass |
| 4 | `test_twin_accepts_break_hop_id_matching_a_real_hop` | ✅ Pass |
| 5 | `test_root_cause_candidate_requires_at_least_one_citation` | ✅ Pass |
| 6 | `test_root_cause_candidate_confidence_must_be_within_unit_interval` | ✅ Pass |
| 7 | `test_investigation_result_rejects_root_cause_citing_unknown_hop` | ✅ Pass |
| 8 | `test_investigation_result_accepts_root_cause_citing_real_hop` | ✅ Pass |
| 9 | `test_transaction_ref_rejects_unknown_reference_type` | ✅ Pass |
| 10 | `test_transaction_ref_defaults_rail_to_raast_p2p` | ✅ Pass |

**Backend total: 53 / 53 passing**

---

## Frontend — `vitest` (26 tests)

### `src/api/client.test.ts` — fetch wrapper (8)

| # | Test | Result |
|---|------|--------|
| 1 | `createInvestigation posts to /api/investigations with the reference payload` | ✅ Pass |
| 2 | `createInvestigation resolves with the parsed JSON body` | ✅ Pass |
| 3 | `createInvestigation rejects with a descriptive error on a non-ok response` | ✅ Pass |
| 4 | `listInvestigations calls GET /api/investigations` | ✅ Pass |
| 5 | `getConnectorStatus calls GET /api/connectors/status` | ✅ Pass |
| 6 | `getDemoReferences calls GET /api/demo/references` | ✅ Pass |
| 7 | `evidencePackUrl builds a json evidence-pack URL` | ✅ Pass |
| 8 | `evidencePackUrl builds a pdf evidence-pack URL` | ✅ Pass |

### `src/hooks/useTheme.test.ts` — theme persistence hook (5)

| # | Test | Result |
|---|------|--------|
| 1 | `defaults to 'system' when nothing is stored` | ✅ Pass |
| 2 | `reads a previously stored theme on mount` | ✅ Pass |
| 3 | `ignores a corrupted/unexpected stored value and falls back to system` | ✅ Pass |
| 4 | `setTheme updates state, persists to localStorage, and sets the DOM attribute` | ✅ Pass |
| 5 | `switching back to 'system' removes the DOM attribute` | ✅ Pass |

### `src/components/ReferenceSearch.test.tsx` — search form (5)

| # | Test | Result |
|---|------|--------|
| 1 | `submits the typed reference with reference_type core_transaction_id` | ✅ Pass |
| 2 | `does not submit when the input is empty or whitespace-only` | ✅ Pass |
| 3 | `trims leading/trailing whitespace from the submitted reference` | ✅ Pass |
| 4 | `clicking a demo chip investigates it with its own reference_type` | ✅ Pass |
| 5 | `disables the submit button and demo chips while loading` | ✅ Pass |

### `src/components/RootCausePanel.test.tsx` — root cause display (5)

| # | Test | Result |
|---|------|--------|
| 1 | `shows a 'no break detected' message when there are no causes` | ✅ Pass |
| 2 | `renders each candidate's label and confidence as a rounded percentage` | ✅ Pass |
| 3 | `omits the pattern tag when pattern_id is null` | ✅ Pass |
| 4 | `scrolls to the cited hop element when its citation link is clicked` | ✅ Pass |
| 5 | `renders one citation link per cited hop id` | ✅ Pass |

### `src/components/ConnectorStatusBar.test.tsx` — connector health pills (3)

| # | Test | Result |
|---|------|--------|
| 1 | `renders nothing when there are no statuses` | ✅ Pass |
| 2 | `renders a pill per connector, named after it` | ✅ Pass |
| 3 | `marks a healthy connector's pill with the 'healthy' class and an unhealthy one with 'unhealthy'` | ✅ Pass |

**Frontend total: 26 / 26 passing**

---

## Summary

| Suite | Total | Pass | Fail |
|---|---|---|---|
| Backend (`pytest`) | 53 | 53 | 0 |
| Frontend (`vitest`) | 26 | 26 | 0 |
| **Grand total** | **79** | **79** | **0** |

## Coverage gaps (not yet tested)

Documented here rather than left implicit, per docs/GUARDRAILS.md's spirit of
being explicit about what is and isn't verified:

- **Frontend components without tests**: `App.tsx` (top-level orchestration),
  `ExplanationPanel`, `HopCard`, `RecommendationPanel`, `ThemeToggle`,
  `Timeline` — mostly presentational; would need either component tests or a
  higher-value integration test driving `App` end-to-end with a mocked
  `client.ts`.
- **`claude_reasoning.py`**: the real Claude API path (`explain`/`recommend`)
  is exercised only implicitly by the fallback path being the one under test
  in CI (no `ANTHROPIC_API_KEY` set) — there's no test that mocks the
  `anthropic` client and asserts the prompt/response wiring.
- **`correlation/rules.py`** and **`correlation/failure_library.py`**: covered
  indirectly through `test_correlation.py`'s end-to-end fixture scenarios, not
  via direct unit tests of rule-matching edge cases (e.g. two competing
  failure-library patterns with equal confidence).
- **`db.py`**: `init_db()` itself (table creation against a fresh engine) is
  exercised implicitly, not directly asserted.
