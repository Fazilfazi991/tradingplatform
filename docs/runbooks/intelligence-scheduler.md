# Intelligence scheduler runbook

Run the fixture demonstration with `run-intelligence-demo`. It performs no network requests and
produces no prediction. Local schedules support interval, cron-like, market-session, event-triggered,
and manual/replay jobs. Recommended development cadence is hourly health, 15-minute official RSS,
daily universe review, release-aware macro collection, and post-close EOD processing.

Every execution writes a job-ledger entry with source, mode (`BACKFILL`, `LIVE`, `REPLAY`, `FIXTURE`),
times, counts, retries, error class, versions, and code SHA. Repeated windows are idempotent by source
event ID/content identity. Failures preserve fetched raw artifacts but stop canonical promotion.

Three consecutive failures by default open the circuit. Investigate allowlist, status, content type,
size, XML/schema, empty-volume, authentication, and rate-limit evidence. Recovery requires a passing
health check and explicit breaker reset; replay preserved artifacts under a new parser version without
overwriting earlier derived events.

Production migration: persistent worker processes, PostgreSQL job leases, durable checkpoints,
object-storage artifacts, OpenTelemetry metrics, and internal incident notifications.
