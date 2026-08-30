# Batch 1.1 evidence ledger

Date: 2026-08-30  
Starting commit: `2f605662cd315479a84036b577a49be78796846b`

## Environment and stop conditions

- Repository: `C:\Users\User\Desktop\Projects\Trading Platform`; branch `main`; clean at start.
- Starting commit is the required baseline. No remotes are configured.
- Python 3.12.13; project dependencies installed in `.venv`.
- `UPSTOX_ACCESS_TOKEN`, `SUPABASE_URL`, `SUPABASE_DB_URL`, `DATABASE_URL`, and PostgreSQL credential
  variables were absent. Values were never printed.
- `psql`, Docker, and Supabase CLI were absent. No database was contacted or mutated.
- Supabase's current changelog was checked before database work; no configured project existed to
  verify as belonging to Verified Edge.

## Executed evidence

- Official current NIFTY 200 snapshot SHA-256:
  `76b8b127931953ce7e5e5511c99c3b73775140eeb83b6b293085b4a9483dce1a`.
- Exact mapping: total 200; mapped 200; unmapped 0; ambiguous 0; duplicate symbols 0;
  inactive 0; rate 100%. Bulk source and provider payloads remain ignored.
- Failure injection covers authentication absence, 429, 500/503, network timeout, malformed JSON,
  missing fields, unexpected fields, missing instruments, duplicates, conflicts, future timestamps,
  and invalid OHLC. Transport and retry failures end explicitly; no fallback values are fabricated.
- Raw replay produces identical accepted bars, quarantine rows, and semantic quality events.
  Two exports from identical inputs are byte-identical and their manifests have identical hashes.
- A decision-time test proves an event one microsecond after T is unavailable at T.
- Test result: 38 passed, 0 failed; statement coverage 90.11%; Ruff passed.

## Blocked evidence

- Migration: BLOCKED. Table/index/trigger counts, database version, access, append-only, sealing,
  causal constraints, idempotency, and transaction rollback have no runtime result.
- Upstox Stage A: BLOCKED — TOKEN REQUIRED. Therefore Stage B and Stage C were not run.
- Live provider behavior, session coverage, latency, rate-limit headers, endpoint boundaries, and
  live corporate-action discontinuities remain unmeasured.
- Corporate-action enrichment is BLOCKED; second-source reconciliation is DEFERRED.
