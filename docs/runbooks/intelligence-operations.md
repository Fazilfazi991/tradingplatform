# Intelligence operations runbook

Default schedules are in `config/intelligence-schedules.json`: RBI and SEBI RSS every 15 minutes,
health hourly, universe daily, intelligence build 16:30 IST, quality audit 17:00, failure review 17:15,
summary 17:30, and source discovery weekly.

Run one scheduler pass with `python scripts/run_intelligence_worker.py --once`. Run continuously by
omitting `--once`; stop with Ctrl+C. Local state is `data/local/intelligence-operations.sqlite3` and is
not committed. Validate approved feeds with `python scripts/validate_live_intelligence_sources.py`.

Backfills require source, bounded start/end, reason, operator identity, and `BACKFILL`; they may never
be relabelled as prospectively observed. Daily archives are immutable. Reprocessing the same raw
artifacts must reproduce the same semantic hash or open a replay incident.
