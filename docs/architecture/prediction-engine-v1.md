# Prediction Engine V1

Prediction Engine V1 is a deterministic, statistical research system over the frozen Upstox daily-bar dataset. It is isolated from public product routes and from the evidence-fusion state. An evidence state explains observed information; a model forecast estimates a preregistered historical target. Neither substitutes for the other.

The pipeline is `frozen dataset → structural-action exclusion → causal features → volatility-neutral targets → purged chronological folds → train-only preprocessing → validation-only calibration → abstention/OOD → sealed holdout`. Raw symbol, company, ISIN, LLM output, and the short live history of specialist intelligence are excluded from predictive features.

Outputs conform to `PredictionResearchOutput` and are accepted only by `INTERNAL_RESEARCH` and `RESEARCH_REGISTRY` destinations. No BUY/SELL state, order path, public probability, target price, or position sizing exists.

Research scope is `SURVIVORSHIP_BIASED_CURRENT_UNIVERSE`. Point-in-time NIFTY 200 membership is unavailable, so this architecture cannot establish formally verified historical NIFTY 200 performance.
