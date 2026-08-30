# Feature catalog V1

All features are computed per instrument after session close and inherit the input row's
`available_at`. Warm-up rows remain null and carry `INCOMPLETE`; they are never silently filled by
the feature engine.

| Family | Features |
|---|---|
| Returns | 1, 2, 3, 5, 10, 20, 60-session returns |
| Trend | Distance from SMA 20/50/100/200 and EMA 10/20/50 |
| Momentum | ROC10, RSI2, RSI14, MACD/ATR |
| Volatility | ATR14, ATR/price, realized volatility 10/20/60, range expansion, gap/ATR |
| Volume | Volume/median20, z-score20, traded-value percentile60, volume trend |
| Structure | Distance from highs 20/50/100 and lows 20/50, breakout20, close location, range/ATR |
| Relative strength | Stock/market, stock/sector, sector/market over 20 and 60 sessions |
| Drawdown | Distance from rolling peak over 20, 60, and 252 sessions |

Forbidden feature-name patterns include future, forward, next, post-event, and target-derived fields.
The matrix preserves as-of, availability, dataset version, input range, null count, quality state,
implementation version, and a feature-set hash.
