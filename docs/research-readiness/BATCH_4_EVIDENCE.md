# Batch 4 real market data evidence

Date: 2026-08-30

| Gate | Status | Evidence |
| --- | --- | --- |
| PostgreSQL runtime | BLOCKED | No URL, local service, Docker, Podman, or WSL database. User-scope PostgreSQL 17 installer was unavailable. |
| Upstox Stage A | BLOCKED | `UPSTOX_ACCESS_TOKEN` absent. |
| Upstox Stage B | BLOCKED | Stage A prerequisite not met. |
| Upstox Stage C | BLOCKED | Stage A/B prerequisites not met. |
| Current NIFTY 200 | PASS | Existing exact 200/200 mapping evidence under DR-005. |
| Point-in-time NIFTY 200 | BLOCKED | Official historical constituent subscription identified; no entitlement/data acquired. |
| Corporate actions | PARTIAL | Authenticated Upstox endpoint and adjustment ledger implemented; no live coverage validation. |
| Second source | BLOCKED | Official licensed NSE EOD/historical product identified; no subscription/data. |
| Reconciliation | BLOCKED | Metrics and policy implemented; no independent observations available. |
| Research dataset | NOT CREATED | Required source evidence does not overlap. |
| Research mode | ENGINEERING_FIXTURE | Gate policy rejects `EXPLORATORY_REAL`. |

## Source classifications

- NIFTY Indices historical constituent subscription: `REVIEW_REQUIRED`; official, effective-dated
  product appears suitable, but commercial terms and entitlement must be completed.
- Upstox Corporate Actions API: `PROVISIONAL_INTERNAL`; official authenticated endpoint, pending
  live scope, completeness, corrections, and retention validation.
- NSE EOD/Historical market data: `REVIEW_REQUIRED`; official licensed subscription candidate for
  independent reconciliation.
- Random websites and reconstructed current-member history: `BLOCKED`.

No real bars or corporate-action payloads were fabricated, downloaded, or promoted.
