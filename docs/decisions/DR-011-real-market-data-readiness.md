# DR-011: Real market data readiness

Status: Partially ready; `EXPLORATORY_REAL` not authorized  
Date: 2026-08-30

## Decision

The platform remains in `ENGINEERING_FIXTURE`. Real market research is blocked because no approved
PostgreSQL runtime or Upstox credential is configured, no entitled effective-dated NIFTY 200
history has been acquired, corporate-action coverage has not been validated over the intended
period, and no licensed independent bar source is configured.

The Upstox historical and corporate-action adapters may be used only for staged read-only
validation after authentication. Current NIFTY 200 membership remains valid only for present-day
mapping QA under DR-005. The NSE Indices historical constituent subscription is
`REVIEW_REQUIRED`. NSE historical/EOD market data is a candidate licensed second source and is
`REVIEW_REQUIRED`. These findings add status evidence; they do not supersede DR-005 or DR-006.

No trustworthy historical start date or eligible `REAL_MARKET_RESEARCH_V0` universe can be stated
until all components overlap. Consequently no real dataset is created and no feature, analogue,
strategy, validation, holdout, forward, or customer prediction claim is authorized.

## Promotion rule

`EXPLORATORY_REAL` requires runtime PostgreSQL verification, Upstox stages A and B, acceptable bar
quality, an entitled effective-dated universe for the claimed period, validated corporate-action
treatment, and independent reconciliation or a separately approved documented risk decision.
Formal discovery and later modes remain blocked even if these gates pass.
