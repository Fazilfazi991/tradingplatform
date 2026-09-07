# Real market-data runtime

Reviewed 2026-09-07. Upstox is the first provider behind the provider-neutral market-data interface.
The server-side adapter permits GET operations for the BOD JSON instrument master, Historical Candle
V3 (`days/1`), NSE market status, LTP validation, and corporate actions. It has no order, GTT,
portfolio-action, position-management, or fund-transfer methods.

The runtime preserves provider rows and request metadata in ignored local storage, canonicalizes only
valid daily OHLCV rows, exports deterministic Parquet, and hashes every dataset manifest. Backfill and
forward collection are distinct provenance states. PostgreSQL remains deferred.

Technical features are deterministic and cutoff-bound. Historical analogues must precede their query
cutoff. Real observations change data provenance to `REAL_MARKET_DATA_INTERNAL`; predictive validation
remains `NOT_PREDICTIVELY_VALIDATED`. Missing real snapshots become `INSUFFICIENT`, never fixtures.
