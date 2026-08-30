# Fundamental Evidence Methodology

Fundamental evidence describes business condition, not future stock returns. The multi-axis output
keeps growth, margins, profitability, cash flow, balance sheet, working capital, capital efficiency,
guidance, earnings quality and valuation separate, with evidence IDs and contradictions.

At cutoff T, only observations whose system `available_at <= T` may enter a snapshot. A fiscal period
end is never treated as publication time. Restatements take effect only from their own availability
time. Expectations must be from a legitimate source and available strictly before the result; without
that, surprise is `UNKNOWN`. Management guidance and commentary remain separate from accounting facts.

Directional evidence is orientation only. The score remains null in the engineering implementation
and is explicitly not a probability, expected return, recommendation or alpha claim. Horizons (`1D`,
`3D`, `5D`, `10D`, quarterly, medium term) are context labels only; no decay is optimized against price.

QA reports coverage, missing periods, restatement rate, unit/period conflicts, source disagreements,
LLM extraction failures, warning counts, staleness and snapshot completeness.
