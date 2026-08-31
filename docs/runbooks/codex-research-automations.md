# Codex Research Automations

All schedules use Asia/Kolkata and are created paused until the feature branch is approved, merged,
deployed, and `CODEX_RESEARCH_OPERATOR_ENABLED=true` is explicitly configured.

- Pre-market: weekdays at 07:45 IST.
- Hourly differential: weekdays from 09:00 through 18:00 IST.
- EOD review: weekdays at 16:45 IST.
- Operations audit: weekdays at 18:00 IST.
- Optional Saturday deep review and Sunday pre-week review remain paused.

Every automation first inspects platform state, respects per-run web budgets, writes deterministic
run/candidate JSON under `research/codex/YYYY-MM-DD/`, and never commits code. A collector repair uses
a dedicated `codex/` branch, runs tests, and stops at `PREPARE_FIX_ONLY`.

If the feature flag is false, the run exits successfully with `DISABLED_BY_FEATURE_FLAG`. Browser
failure is recorded without affecting platform workers. A missed expected heartbeat records
`CODEX_RESEARCH_RUN_MISSED`.
