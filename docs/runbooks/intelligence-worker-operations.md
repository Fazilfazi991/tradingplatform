# Intelligence worker operations

This runbook operates the platform-owned internal RBI/SEBI collector and Luna semantic runtime. It
does not start Codex research automation, Forward Paper, brokerage access, or public predictions.

## Windows workstation supervisor

Install or repair the approved current-user Task Scheduler worker and independent health monitor:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install_intelligence_worker_task.ps1
```

The worker task is `VerifiedEdge-IntelligenceWorker`. It runs at logon, ignores duplicate starts,
has a bounded restart policy, and is parented by the Windows Task Scheduler service rather than a
Codex or terminal process. The monitor task is `VerifiedEdge-IntelligenceWorker-HealthMonitor` and
regenerates current health every five minutes even when the worker is unavailable.

```powershell
# Status and current health
Get-ScheduledTask -TaskName "VerifiedEdge-IntelligenceWorker*"
Get-ScheduledTaskInfo -TaskName VerifiedEdge-IntelligenceWorker
.\.venv\Scripts\python.exe scripts\run_intelligence_worker.py --status
.\.venv\Scripts\python.exe scripts\build_current_intelligence_health.py

# Sanitized logs and heartbeat
Get-Content data\local\intelligence-worker\worker.log -Tail 100
Get-Content data\local\intelligence\current-intelligence-health.json

# Graceful stop, start, and restart
.\.venv\Scripts\python.exe scripts\run_intelligence_worker.py --stop
Start-ScheduledTask -TaskName VerifiedEdge-IntelligenceWorker
.\.venv\Scripts\python.exe scripts\run_intelligence_worker.py --stop
Start-ScheduledTask -TaskName VerifiedEdge-IntelligenceWorker
```

The ignored `.env` must contain a usable `OPENAI_API_KEY` and the approved `OPENAI_MODEL`. The
supervised runner validates presence and model identity without printing either value. It enables
only the internal LLM runtime. Forward Paper remains controlled separately and disabled.

## Safe recovery

1. Inspect task state, last result, current health, and sanitized log.
2. Check the worker heartbeat; do not infer source or semantic health from process state alone.
3. Request a graceful stop once and confirm `STOPPED`.
4. Start the registered task once. The runtime singleton rejects a second live owner.
5. Confirm configuration drift is `PASS` and both source freshness thresholds come from configured
   cadence.
6. Observe at least three scheduled RBI and SEBI cycles. Reconcile scheduled time, start time,
   terminal result, records seen, canonical events, duplicates, and forensic attempt records.
7. Run a bounded production-path canary only when a genuine new event does not require Luna. Canary
   IDs are explicit and excluded from live canonical-event counts.
8. Review incidents individually. Never delete a database, cache, tombstone, or history to make an
   incident disappear.

## Diagnosis

- Credential failure: confirm required variables are `PRESENT`; never print values. A transport
  authentication failure is provider health, not semantic failure.
- RBI/SEBI failure: inspect the collection attempt ledger for transport, parser, retry, recovery,
  and terminal disposition. Keep the source incident open until a later scheduled success.
- Luna failure: separate transport state from schema/grounding validation. Quarantined responses
  retain fingerprints and usage, cannot enter the success cache, and remain excluded downstream.
- Policy-change recovery: current semantic health is computed only from attempts matching the latest
  exact provider/model/prompt/schema/routing/config/retry/grounding identity. Historical attempts
  remain visible under `historical_window_totals` but cannot contaminate the new rate. A canary proves
  connectivity and basic validation only; it is excluded from the configured 40-attempt operational
  closure sample. Until that sample completes, report `INSUFFICIENT_SAMPLE` and keep prior semantic
  incidents open. A changed policy identity boundedly re-evaluates prior terminal results under the
  existing per-cycle and daily-budget limits; an unchanged successful result is not reprocessed.
  Events deferred as `NOT_ANALYZED_BY_POLICY` when the daily budget is exhausted return to the queue
  when budget becomes available, while collection continues independently.
- Supervisor failure: inspect Task Scheduler history and process ancestry. A current worker must be
  descended from the Task Scheduler service. A singleton rejection normally means another healthy
  worker already owns the runtime.
- Stale heartbeat: inspect the supervised process and lease state. Restart only after the prior
  instance is stopped or stale.
- Configuration drift: compare the mismatch list in current health with
  `config/intelligence-runtime-lock.json`; review and update the lock only as part of an approved,
  tested runtime change.

## Persistence boundary

The Windows task survives terminal and Codex-session closure and restarts at the current user's next
logon. It is not an unattended pre-logon Windows service, so reboot-to-logon delay remains an
operations limitation. The reviewed `infra/systemd/verified-edge-intelligence.service` is the
production-host mechanism for unattended boot persistence and least-privilege identity.

Runtime databases, caches, PID/process state, logs, and secrets stay under ignored local or
host-owned paths and must never be committed.
