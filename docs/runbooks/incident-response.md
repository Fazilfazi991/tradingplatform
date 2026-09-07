# Production incident response

This runbook applies to the public web service and internal data/intelligence workers. It does not
authorize customer predictions, broker execution, new sources, credential disclosure, or a bypass
of the release gates.

## Severity and ownership

| Severity | Meaning | Initial response target | Default owner |
|---|---|---:|---|
| CRITICAL | Public safety/security boundary, secret exposure, corrupted immutable evidence, or total production outage | 15 minutes | Incident commander + service owner |
| HIGH | Provider/collector down, repeated scheduler failure, stale critical data, schema spike, or failed deployment | 30 minutes | Service owner |
| WARNING | Budget threshold, isolated timeout, degraded source, or delayed non-critical job | Same operating day | Operations owner |
| INFO | Expected abstention, disabled optional provider, or review item | Next review cycle | Named component owner |

The first responder assigns an incident commander, records UTC start time, affected commit,
environment, sanitized symptoms, and containment. Never paste tokens, provider response bodies,
raw licensed payloads, personal data, or local paths into tickets or chat.

## Standard response

1. Confirm the signal from an independent health surface; do not repeatedly retry a failing provider.
2. Contain customer risk: disable the affected public-derived surface, preserve `ABSTAIN`, or roll
   back the web deployment. Collection may continue when semantic budget is exhausted, but output
   remains `UNKNOWN` / `PENDING_ANALYSIS`.
3. Preserve immutable executions, raw-artifact hashes, incidents, provider/task telemetry, and the
   exact application/config/prompt/model versions. Never rewrite forward predictions or research
   registration records.
4. Diagnose using sanitized logs, worker `--status`, source freshness, execution ledger, cost ledger,
   and deployment identifiers.
5. Recover using the bounded action for the incident class below. Verify health and data boundaries
   before resolving. Reopening is required if the same signal recurs.
6. For CRITICAL/HIGH incidents, write a post-incident record with cause, detection gap, impact,
   timeline, corrective action, owner, and due date.

## Incident-specific containment

| Signal | Immediate action | Recovery proof |
|---|---|---|
| `LLM_PROVIDER_DOWN` / auth expired | Keep collection running; disable semantic calls; output UNKNOWN | Auth/model health succeeds without exposing values; one bounded structured-output canary passes |
| `LLM_RATE_LIMITED` | Respect backoff; do not add a provider solely to clear the alert | Rate-limit window clears and bounded retry succeeds |
| `LLM_SCHEMA_FAILURE_SPIKE` | Quarantine affected outputs; freeze prompt/model/schema versions | Regression fixture passes and a new measurement window is explicitly versioned |
| Cost warning/exceeded | Stop optional LLM calls; retain deterministic ingestion | Ledger reconciles and configured budget resets or owner approves a new limit |
| Hallucination quarantine | Block affected event/snapshot from Fusion | Evidence-reference and numeric/entity review passes; regression fixture added |
| `SOURCE_STALE` / collection failure | Block promotion from that source; preserve last-good timestamp | Multiple cadence-appropriate collections succeed and incident resolves |
| `SCHEDULER_MISSED_RUN` / stale worker heartbeat | Inspect supervisor and lease/execution state; restart once | Heartbeat is fresh, interrupted run is recorded, next due execution succeeds |
| Market-data anomaly | Quarantine rows/symbols; do not weaken tolerances | Deterministic validation and, where required, independent reconciliation pass |
| Snapshot/Fusion failure | Preserve `ABSTAIN`; do not reuse fixtures | Snapshot rebuild uses eligible real evidence and provenance checks pass |
| Bad deployment | Promote recorded previous healthy immutable deployment | Public smoke/security/data-boundary suite passes on rollback target |
| Suspected secret exposure | Revoke/rotate through provider, restrict access, preserve sanitized evidence | New credentials stored server-side; secret scan and bundle/response inspection pass |

## Recovery boundaries

Database restore requires the backup/restore runbook, an isolated verification target, and an
approved maintenance/rollback window. A code rollback never rolls back or deletes append-only
research, forward-validation, cost, or incident records. Provider fallback credentials are optional;
their absence must not break primary operation.

Resolve an incident only after the triggering condition has cleared and the relevant smoke or
integrity check passes. Resolution records include UTC close time, approver, evidence reference, and
whether follow-up work remains. Production notification routing and paging destinations require the
owner's hosting/operations configuration and are not simulated by Codex.
