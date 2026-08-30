# DR-012: News and event intelligence

Status: Accepted for internal engineering  
Date: 2026-08-30

News/event intelligence is an evidence engine, not a price-prediction engine. Positive event
sentiment must never automatically become positive return probability. Materiality, novelty,
confirmation, direction, surprise, known-state and attention remain distinct.

All derived interpretations require causal timestamps, analyzer/model version, hashes and evidence
references. Source facts and model interpretations are different claim kinds. Insufficient evidence
must produce `UNKNOWN` or `INSUFFICIENT_EVIDENCE`. Duplicate stories add no incremental evidence,
contradictions reduce certainty, and high-materiality ambiguity requires review.

The provider-neutral LLM router is optional. Deterministic fallback remains authoritative when no
provider is enabled. Research mode remains `ENGINEERING_FIXTURE`; customer publication, price
prediction, fusion and performance claims remain blocked.
