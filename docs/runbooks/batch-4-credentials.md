# Batch 4 credential setup

Never commit credentials or paste them into issues, reports, or browser code.

## PostgreSQL

Use a project-specific Supabase development project or local PostgreSQL database. Apply least
privilege and place its connection string in the server process as `DATABASE_URL` (or
`SUPABASE_DB_URL`). Then run:

```powershell
.venv\Scripts\python.exe scripts\verify_postgres_runtime.py
```

The verifier applies migrations 0001–0003 and reports schema object counts without printing the
URL. Do not point it at an unrelated or production database.

## Upstox

1. Sign in to the Upstox developer area and create/select the project application.
2. Obtain a token authorized for read-only historical market data and fundamentals. Prefer the
   eligible analytics/read-only product; confirm current expiry and terms.
3. Set `UPSTOX_ACCESS_TOKEN` in the server process or ignored local environment file.
4. Run `ve-data upstox-health`, followed by the documented five-symbol Stage A spike.

Do not grant or call order, funds, portfolio-mutation, placement, modification, or cancellation
APIs.

## Licensed historical inputs

Contact NSE Indices for an entitled historical constituent subscription and NSE Data & Analytics
for licensed EOD/historical data if selected as the independent source. Record contract, permitted
research use, retention, redistribution, effective coverage dates, and source versions before
placing files in controlled storage.
