# Market-data EOD operations

The platform-owned schedule is versioned in `config/market-data-eod.json`. On NSE weekdays it starts
after the regular session, confirms an exchange-complete status, ingests the latest completed bar,
archives the forward observation, checks revisions and quality, and then builds Technical and
Historical snapshots. Internal Fusion may run only after successful upstream completion.

Historical downloads use `BACKFILLED_MARKET_DATA`; observations collected after activation use
`FORWARD_COLLECTED_MARKET_DATA`. If a past provider row changes, store old/new hashes and observed
times. Never overwrite. Auth failure, stale bars, missed sessions, rate limiting, and snapshot failure
are operational incidents. Collection continues on the next eligible session; no order capability exists.

Inspect the committed gate without reading credentials or creating runtime state:

```powershell
.\.venv\Scripts\python.exe scripts\run_market_eod.py --status
```

The append-only EOD ledger stores a run and its validated bars atomically. The collector requires
the exact current-universe mapping, the configured NSE close state, the configured India-local time,
one bar for the explicit session, read-only analytics credentials, and `public_delivery=BLOCKED`.
Missing bars and invalid rows are explicit and make the run degraded; incomplete/ambiguous universe
mapping fails the run. Duplicate session/config/provider runs are rejected and prior rows cannot be
updated or deleted.

`--run` remains fail-closed while `execution_operations` is false. Do not enable it until the host
supervisor, incident routing, token rotation, eligible close-window schedule, backup/retention, and
restart rehearsal are approved. Enabling this collector does not enable forward predictions.
