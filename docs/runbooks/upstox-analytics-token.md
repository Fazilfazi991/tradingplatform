# Upstox Analytics Token runbook

Store the one-year read-only credential only as `UPSTOX_ANALYTICS_TOKEN` in ignored `.env` or the
server environment. Never expose it to client JavaScript, logs, reports, tests, Git, or browser storage.

Health uses `GET /v2/market/status/NSE`, not an account profile endpoint. HTTP 401/403 creates
`MARKET_DATA_AUTH_FAILURE`; do not fall back to trading OAuth. HTTP 429 and 5xx use bounded exponential
backoff. Repeated failure opens an operational incident while preserving prior datasets.
