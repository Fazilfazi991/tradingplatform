# Upstox read-only ingestion runbook

## Prerequisites

Use Python 3.12+. Create a virtual environment and install `.[dev]`. Copy `.env.example` to a local
`.env`; `.env` is ignored. Set `UPSTOX_ACCESS_TOKEN` only in the server/process environment. Never
paste it into commands, logs, issues or client code. Standard Upstox tokens expire at 03:30 IST the
following day; an eligible Analytics Token is a separate read-only product. Confirm applicable terms.

## Fixture verification

```powershell
python -m pytest
```

No token is required. Contract tests use `httpx.MockTransport` and cannot contact Upstox.

## Health and staged spike

```powershell
ve-data upstox-health
ve-data upstox-spike --symbols RELIANCE,TCS,HDFCBANK,INFY,ITC --start 2024-08-30 --end 2026-08-30
```

Stage A is five symbols/two years. Review mapping, raw artifacts, all quality events and quarantine
before Stage B (20 symbols/two years). Stage C (current NIFTY 200 recent history) is allowed only
after A/B pass and current-membership provenance is recorded. Do not request intraday data.

If `UPSTOX_ACCESS_TOKEN` is absent, the command exits with status 2 and says the live spike was not
run. It must never substitute fixture results for live evidence.

## Review checklist

Record requested/mapped/failed symbols, expected sessions, received/missing/duplicate/invalid/zero-
volume/extreme bars, critical incidents, API/retry counts, duration, canonical/quarantine counts and
dataset SHA. Completeness target is 99.95% after documented legitimate exceptions; never repair data
to reach the target.

## Dataset and SHA

Call `export_parquet` with accepted/warning canonical bars, then `build_manifest` with the Git SHA
and all version identifiers. Write the manifest as canonical JSON, verify `manifest_hash`, and call
`seal_manifest` once approved. Store exports under ignored `data/exports/` and manifests under
ignored `data/manifests/`; promote only reviewed hashes/artifacts to controlled storage.

Second-source reconciliation is **PENDING EXTERNAL SOURCE**. The `reconcile` function compares
session dates, OHLC and volume when licensed secondary bars are supplied.

