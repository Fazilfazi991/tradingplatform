# Intelligence operations runbook

Default schedules are in `config/intelligence-schedules.json`: RBI and SEBI RSS every 15 minutes,
health hourly, universe daily, intelligence build 16:30 IST, quality audit 17:00, failure review 17:15,
summary 17:30, and source discovery weekly.

Run one scheduler pass with `python scripts/run_intelligence_worker.py --once`. Run continuously by
omitting `--once`; stop with Ctrl+C. Local state is `data/local/intelligence-operations.sqlite3` and is
not committed. Validate approved feeds with `python scripts/validate_live_intelligence_sources.py`.

Check the platform-owned worker heartbeat without exposing job payloads or credentials:

```powershell
.\.venv\Scripts\python.exe scripts\run_intelligence_worker.py --status
```

`RUNNING` means the latest heartbeat is no more than 30 seconds old. `STALE` means the process did
not shut down cleanly or is no longer making progress; inspect the service manager and incidents,
then restart under the approved host supervisor. `STOPPED` is a graceful exit and `NOT_STARTED`
means this state database has never hosted a continuous worker. The heartbeat is a health signal,
not a process manager: production must use the hosting platform's restart policy and least-privilege
service identity.

On the intended Linux worker host, each Python job runs under a `SIGALRM` deadline and a timeout is
recorded immediately as `SCHEDULER_JOB_TIMEOUT`; the handler does not continue after the exception.
Windows has no equivalent signal and is explicitly reported as a cooperative local fallback, where
the timeout is detected after return. Production supervision must additionally apply a process-level
stop timeout and restart policy so native code or an uninterruptible system call cannot hang the
service indefinitely.

Backfills require source, bounded start/end, reason, operator identity, and `BACKFILL`; they may never
be relabelled as prospectively observed. Daily archives are immutable. Reprocessing the same raw
artifacts must reproduce the same semantic hash or open a replay incident.
