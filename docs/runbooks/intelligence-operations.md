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

## Linux service installation

The reviewed unit template is `infra/systemd/verified-edge-intelligence.service`. On the approved
host, create the locked `verified-edge` service account, `/var/lib/verified-edge` owned only by that
account, `/etc/verified-edge/intelligence.env` readable only by root/service group, and an immutable
release symlink at `/opt/verified-edge/current`. Never put secrets in the unit file or repository.

After adapting only the approved installation paths:

```text
sudo systemctl daemon-reload
sudo systemctl enable --now verified-edge-intelligence.service
sudo systemctl status verified-edge-intelligence.service
sudo journalctl -u verified-edge-intelligence.service --since today
sudo systemctl stop verified-edge-intelligence.service
```

The unit runs the production environment-name preflight before startup, writes durable state outside
the release directory, restarts boundedly on failure, kills the whole process group after a 30-second
graceful stop, and applies filesystem/kernel privilege restrictions. After start, corroborate systemd
status with the worker `--status --state /var/lib/verified-edge/intelligence-operations.sqlite3`
heartbeat. Installation and notification destinations remain production-host owner actions.

Backfills require source, bounded start/end, reason, operator identity, and `BACKFILL`; they may never
be relabelled as prospectively observed. Daily archives are immutable. Reprocessing the same raw
artifacts must reproduce the same semantic hash or open a replay incident.
