# Prediction data foundation

## Scope and invariant

Batch 1 is internal, read-only and EOD-first. It cannot place orders or produce predictions,
signals, recommendations, public market-data displays or performance claims. Provider access is
not a redistribution licence.

## Data flow

```text
provider response
  -> immutable raw artifact / market_observations_raw
  -> quality checks
       -> critical: quarantine + incident
       -> accepted/warning: versioned canonical bar
  -> deterministic selection manifest
  -> sorted Parquet research export
  -> sealed manifest + SHA-256
```

Raw observations are evidence and are append-only. Canonical rows are reproducible projections,
never silent corrections. A changed source payload is a new raw observation; a changed transform is
a new canonical version. Corporate action adjustments remain separate factors.

## Provider abstraction

`MarketDataProvider` is the only market-data boundary used by research code. Upstox-specific keys
exist only in provider mappings and the adapter. Future Zerodha, Dhan or licensed NSE adapters can
implement the same interface. The Upstox adapter uses GET endpoints only, bounded exponential
backoff and redacted authentication metadata.

## Information time

`InformationEvent` represents future news, fundamentals, macro, sentiment, flow, derivatives and
corporate events with `event_time`, `published_at`, `observed_at`, `available_at`, `effective_at`
and `ingested_at`. `available_at >= published_at` is enforced. Research must join features using
`available_at <= prediction_cutoff`; revisions become new events and do not replace prior vintages.

## Quality and quarantine

Checks cover duplicate/conflicting bars, missing sessions, OHLC logic, negative/malformed values,
zero volume, timestamp/session validity, future data, extreme returns, stale/missing series, provider
mapping uniqueness, required fields and schema errors. Critical observations cannot canonicalize.
Warnings are preserved without automatic repair. Quarantine records retain reason, check, severity,
review state and resolution.

## Dataset identity and sealing

A manifest pins the point-in-time universe/version, instrument IDs, date range, canonical versions,
calendar/corporate-action/adjustment/quality versions, code SHA, environment fingerprint, row counts,
file hashes and providers. Canonical rows are sorted by symbol/session before Parquet export. The
manifest is canonical JSON hashed with SHA-256. Sealing changes the hash once; a sealed dataset is
immutable and any rebuild creates a new identity/version.

## Database security

All tables live in the private `verified_edge` schema. Access for `public`, `anon` and
`authenticated` is revoked; provider access remains server-side. The schema is Supabase-compatible
but deliberately not exposed through the Data API. Raw, canonical and information-event tables
have update/delete prevention triggers. A real PostgreSQL migration test remains required before a
hosted deployment because this workstation has no PostgreSQL/Docker runtime.

## Current universe limitation

`NIFTY200_V1` supports current-membership ingestion testing only. It is not a historical universe.
Formal research remains blocked until effective-dated, point-in-time membership and a licensed
corporate-action source are available.

