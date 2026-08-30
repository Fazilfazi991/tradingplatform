# Fundamental Metric Catalog

Every calculated value records input observation IDs and a methodology version. Incompatible period,
unit, currency, consolidation scope, or accounting-standard inputs fail closed.

| Family | Metrics / formulas |
|---|---|
| Growth | `(current-prior)/abs(prior)`; YoY, QoQ, CAGR, TTM and acceleration require comparable periods |
| Margins | gross profit, EBITDA, EBIT, PAT or segment profit divided by revenue |
| Profitability | ROE = profit / average equity; ROA = profit / average assets; ROCE = EBIT / (assets-current liabilities); ROIC only with a documented capital definition |
| Cash flow | CFO/PAT; FCF = CFO - absolute capex; capex intensity; cash conversion |
| Leverage | debt/equity; net debt/EBITDA; interest coverage; current/quick ratio; maturity metadata |
| Working capital | receivable days, inventory days, payable days, cash conversion cycle and intensity |
| Share count | outstanding shares, issuance, buyback and ESOP dilution, separately from operating EPS growth |
| Capital allocation | capex, acquisitions, dividends, buybacks, debt reduction and fundraising; no automatic positive label |
| Valuation | P/E, EV/EBITDA, P/B, P/S, FCF/earnings/dividend yields; requires a valid point-in-time price |

Valuation context uses explicit historical, sector, and versioned peer percentiles. Allowed states are
`LOW_RELATIVE`, `NORMAL`, `HIGH_RELATIVE`, `EXTREME`, and `UNKNOWN`; “cheap” and “expensive” are not
methodology-free labels.
