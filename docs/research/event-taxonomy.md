# Event taxonomy

The engine supports corporate events including earnings, guidance, orders, capex, M&A, governance,
capital actions, financing, legal/regulatory, supply-chain and operational incidents. Macro events
include RBI policy, rates, liquidity, inflation, output, fiscal/tax/trade policy, currency,
commodities and geopolitics.

Story stages are `RUMOUR`, `ANNOUNCEMENT`, `CONFIRMATION`, `UPDATE`, `CLARIFICATION`, `CORRECTION`,
`WITHDRAWAL`, `COMPLETION` and `POST_EVENT_RESULT`. Root, parent and sequence fields preserve one
evolving story rather than treating each update as independent evidence.

Direction describes event interpretation only and may be positive, negative, mixed, neutral or
unknown. It is not expected return. Surprise remains `UNKNOWN` without a timestamp-valid benchmark.
