# Real historical dataset methodology

Daily Upstox history is ingested in inclusive deterministic chunks, retained as normalized raw
observations, validated, and exported as canonical Parquet. Each manifest records source/API version,
current-universe hash, mapping hash, request payload hashes, date range, instrument and row counts,
quality results, corporate-action coverage, collection mode, and dataset hash.

States are `RAW`, `QUALITY_CHECKED`, `RESEARCH_ELIGIBLE`, `QUARANTINED`, and `SUPERSEDED`.
Mathematically impossible or negative OHLCV rows are quarantined, not repaired. Market holidays are
not missing sessions; session calendars/status determine completeness. Historical labels are produced
only when their entire 1D/3D/5D/10D future window exists. The latest rows retain null targets.

All current-constituent cross-sectional results are exploratory and labeled
`SURVIVORSHIP_BIASED_CURRENT_UNIVERSE`. Discovery, walk-forward, validation, sealed-holdout, and
forward-paper partitions remain logically separate; this activation does not create a formal holdout.
