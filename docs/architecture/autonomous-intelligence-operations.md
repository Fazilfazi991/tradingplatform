# Autonomous intelligence operations

The operational network runs as platform-owned workers under `FIXTURE` or `INTERNAL_LIVE` mode.
`PRODUCTION_INTERNAL` and `CUSTOMER_VISIBLE` are blocked. SQLite provides local durable schedules,
execution records, leases, checkpoints, and incidents while PostgreSQL remains unavailable; the tables
and lease semantics map directly to later PostgreSQL job leasing.

Versioned schedules use `Asia/Kolkata` for Indian-market work. A worker loads definitions, recovers
interrupted executions, claims expiring leases, creates an idempotent scheduled-execution key, runs a
bounded handler, records sanitized results, advances the schedule, and releases the lease. SIGINT and
SIGTERM request graceful shutdown.

Approved RSS collectors feed normalized append-only events. Health and circuit state gate promotion.
Daily processing builds summaries, entity snapshots, clusters, source states, incidents, universe
state, and an immutable semantic manifest. Backfilled and prospectively observed events remain
explicitly distinct, as do source availability and the time this system actually observed an item.
