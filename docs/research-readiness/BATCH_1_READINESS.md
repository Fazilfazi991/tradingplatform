# Batch 1 research-readiness scorecard

Evidence date: 2026-08-30. `PASS` means directly demonstrated. `PASS WITH CONDITION` identifies
fixture/static or current-snapshot evidence that is useful but does not close its live gate.

| Area | Control | Score | Evidence / condition |
|---|---|---|---|
| Data provider | Upstox authentication | BLOCKED | `UPSTOX_ACCESS_TOKEN` absent |
| Data provider | Instrument mapping | PASS | Official current list; 200/200 exact Upstox mappings |
| Data provider | Daily-history retrieval | BLOCKED | Authenticated endpoint not run |
| Data provider | Rate limits | PASS WITH CONDITION | Bounded 429 tests; no live headers/throughput |
| Data provider | Error handling | PASS WITH CONDITION | 401/429/5xx/timeout/schema tests; live behavior pending |
| Data provider | Schema stability | PASS WITH CONDITION | Missing/extra/malformed fixture cases covered |
| Data integrity | Raw preservation and canonicalization | PASS | Immutable models, append-only SQL, replay tests |
| Data integrity | Missing sessions, duplicates, conflicts | PASS WITH CONDITION | Deterministic fixture tests; live coverage pending |
| Data integrity | OHLC/timestamp validity and quarantine | PASS | Invalid/future cases cannot silently enter canonical data |
| Reproducibility | Manifest, hash, code SHA | PASS | Versioned manifest and SHA-256 contracts |
| Reproducibility | Deterministic rebuild and replay | PASS WITH CONDITION | Byte-identical fixture rebuild; live dataset blocked |
| Database | Runtime migration | BLOCKED | No approved DB URL, PostgreSQL, Docker, or Supabase CLI |
| Database | Append-only, sealing, access, constraints | BLOCKED | Static tests pass; real PostgreSQL execution absent |
| Universe | Current NIFTY 200 | PASS | 200 official symbols, 100% exact mapping |
| Universe | Point-in-time NIFTY 200 | BLOCKED | No effective-dated licensed history; see DR-005 |
| Corporate actions | Detection | PASS WITH CONDITION | Extreme-move flag exists; not enriched against live actions |
| Corporate actions | Licensed source / adjustment correctness | BLOCKED | No source configured; unadjusted data only |
| Reconciliation | Independent source / 20 symbols | BLOCKED | Deferred under DR-006 |
| Causal model | `available_at` protection | PASS | Decision-time selector excludes `available_at > T` |
| Causal model | Future-source compatibility | PASS WITH CONDITION | Required timestamps modeled; future adapters not built |

## Gate decision

**NOT READY FOR BATCH 2**

Blocking evidence is absent for real authenticated daily history, real PostgreSQL controls,
effective-dated universe membership, licensed corporate actions, and independent reconciliation.
Current-universe mapping and deterministic fixture safety materially reduce risk but cannot replace
those runtime and research-validity gates.

