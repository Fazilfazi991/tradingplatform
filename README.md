# Verified Edge

Verified Edge combines a public, synthetic research demonstration with internal market-data,
intelligence, and prediction-research infrastructure. The public product explains evidence,
contradiction, uncertainty, provenance, and abstention; it does not publish live predictions,
recommendations, target prices, performance claims, or orders.

Current predictive state: **HOLDOUT VALIDATED — FORWARD REQUIRED**. A sealed historical holdout
passed, but prospective validation has not yet established a verified future edge.

Start with:

- `PRODUCTION_READINESS_MASTER_PLAN.md` for release gates and priorities.
- `docs/architecture/data-foundation.md` for the data architecture.
- `docs/runbooks/upstox-ingestion.md` for bounded internal market-data collection.
- `docs/runbooks/deployment.md` for the deployment and rollback contract.

## Local verification

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
pnpm test:web
pnpm lint
pnpm typecheck
pnpm build
```

Never commit `.env` files or expose server credentials with a `NEXT_PUBLIC_` prefix.
