# News evidence methodology

`NewsEventEvidenceEngine` consumes only intelligence available by the cutoff. Contributions combine
materiality, confirmation, certainty and relevance. Duplicate clusters receive zero incremental
weight; contradictions reduce certainty; low-quality repeated sources cannot outvote an official
filing by count.

The directional evidence score is bounded orientation metadata. It is explicitly not a probability
of price movement, expected return, recommendation or trading score. Time-decay records event type
and horizon but leaves final predictive constants unselected. Supported horizon labels include
intraday through medium term.

QA reports classification coverage, unknown/materiality-unknown rates, entity match, contradiction,
duplicate suppression, LLM validation failures and processing latency.
