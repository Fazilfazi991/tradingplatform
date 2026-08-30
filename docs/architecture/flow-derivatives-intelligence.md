# Flow and Derivatives Intelligence Architecture

Status: **ENGINEERING / READY**. Outputs are positioning evidence, not prediction.

```text
official/licensed candidate report
  -> immutable causal observation
  -> flow / futures / option deterministic calculations
  -> expiry- and contract-aware snapshots
  -> multi-axis positioning state
  -> FlowDerivativesEvidenceEngine (abstains when incomplete)
```

Flow observations retain the represented period separately from publication and system-observation
times. Futures retain contract and expiry; options retain underlying, expiry, strike, type, source and
corporate-action adjustment lineage. Late EOD files cannot enter earlier intraday snapshots.

The specialist registry now contains `TECHNICAL`, `HISTORICAL`, `NEWS_EVENT`, `MACRO_GLOBAL`,
`FUNDAMENTAL`, `PSYCHOLOGY`, and `FLOW_DERIVATIVES`. This is a future comparison interface only; it does
not combine scores.
