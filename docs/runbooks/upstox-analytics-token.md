# Upstox Analytics Token runbook

Store the one-year read-only credential only as `UPSTOX_ANALYTICS_TOKEN` in ignored `.env` or the
server environment. Never expose it to client JavaScript, logs, reports, tests, Git, or browser storage.

Health uses `GET /v2/market/status/NSE`, not an account profile endpoint. HTTP 401/403 creates
`MARKET_DATA_AUTH_FAILURE`; do not fall back to trading OAuth. HTTP 429 and 5xx use bounded exponential
backoff. Repeated failure opens an operational incident while preserving prior datasets.

The platform scheduler runs `market-provider-health` every 15 minutes on the production worker.
Results are appended to `data/local/market-provider-health.sqlite3`; only provider state, exchange,
latency, sanitized error class, timestamps, and integrity hashes are stored. Use
`python scripts/check_market_provider_health.py --status` without credentials for the latest local
state or `--check` for one explicit read-only canary. Neither command prints credential values.
