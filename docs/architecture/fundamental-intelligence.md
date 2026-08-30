# Fundamental Intelligence Architecture

Status: **ENGINEERING / READY**. Predictive validation: **NOT STARTED**.

The engine is an internal, point-in-time evidence system. It does not estimate returns, rank
companies, or emit recommendations.

```text
official/licensed filing candidate
  -> immutable document + availability timestamps
  -> structured parser (XBRL preferred; PDF/HTML/JSON/CSV contracts)
  -> typed FundamentalObservation (original value preserved)
  -> period/unit/currency/scope validation
  -> calculations, guidance, quality warnings, valuation context
  -> build_fundamental_snapshot(entity, cutoff)
  -> FundamentalEvidenceEngine (internal evidence, not prediction)
```

`available_at = max(source_available_at, system_observed_at)`. Restated values carry a separate
`restatement_available_at`; reconstruction uses the original until that instant. Snapshot grouping
also retains accounting standard, consolidation scope and period type, preventing silent quarter /
annual, standalone / consolidated, or vendor-definition mixing.

The generic metric vocabulary covers revenue, EBITDA, EBIT, PBT, PAT, EPS, gross/operating profit,
finance cost, tax, other income, assets, net worth, debt, cash, receivables, inventory, payables,
cash-flow components, capex and FCF. Extensible metric IDs support bank (NIM, GNPA, NNPA, CASA,
provisions, capital adequacy), insurance (premium, APE/VNB, solvency, claims), segment and geographic
disclosures without forcing industrial-company ratios on financial institutions.

Source disagreements are preserved as separate observations. Authority precedence is exchange XBRL,
signed exchange result, signed issuer result, annual report, licensed vendor, then derived
interpretation. Values are never averaged.

Schedulers define six-hour discovery/processing, daily snapshots and QA, and weekly restatement
checks. All are fixture-only until a source is approved; polling is deliberately non-aggressive.
