# DR-004 — Prediction data foundation

**Status:** Accepted  
**Date:** 30 August 2026

## Decision

Verified Edge is a market-prediction intelligence research system, not an execution platform. Its
foundation separates immutable source evidence, quality-controlled canonical observations and
sealed research datasets. Market price is one source category among future news, corporate,
fundamental, macro, sentiment, flow, derivatives and alternative evidence.

All evidence uses a canonical information-time contract. Models may consume an observation only
after `available_at`; revisions remain separate vintages. Provider identifiers never become domain
identifiers. Customer display, paid use and redistribution remain blocked by DR-002/DR-003.

## Consequences

- More storage and lineage metadata, but reproducible and auditable research.
- Critical quality incidents quarantine data; no silent repair.
- Current NIFTY 200 membership cannot be projected backward.
- Upstox is a conservative read-only prototype adapter, not the production data licence.
- Prediction features, targets and models are deferred to Batch 2.

## Allowed next work

Internal ingestion, quality, provenance, deterministic export, provider reconciliation architecture
and multi-source contracts. No order APIs, customer UI, public signals or performance outputs.

