# Corporate-action adjustment policy

Raw bars are immutable. Corporate actions preserve their effective date and the time Verified Edge
observed them. Split and bonus adjustments may be calculated only from an explicit, validated ratio
into a separate research series with a transformation ledger. Dividends remain contextual unless an
explicit total-return method and reference price are validated.

Upstox candle adjustment semantics are not documented strongly enough for Verified Edge to claim
adjusted or total-return history. The active state is `PRICE_ADJUSTMENT_STATUS_UNVERIFIED`.
Split/bonus windows must therefore be flagged or excluded from unadjusted return calculations. A
provider OHLCV anomaly is quarantined; it is never explained away as a corporate action.
