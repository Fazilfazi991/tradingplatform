# Upstox market-data policy

Documentation was reviewed on 2026-09-07 against current official Upstox Developer pages.

- The Analytics Token is a one-year, one-per-account, read-only credential and supports GET requests.
- Historical Candle V3 supports daily interval 1, history from January 2000, and at most one decade per daily request.
- The BOD JSON master and `instrument_key` are canonical; deprecated CSV is not the primary source.
- Standard APIs are documented at 50 requests/second, 500/minute, and 2,000/30 minutes.
- NSE market status is checked before treating an EOD bar as finalized.
- Corporate actions are retrieved by ISIN and preserve event details and observed time.

Access does not establish a redistribution licence. Status is `INTERNAL_RESEARCH_USE`; public raw-data
display, resale, redistribution, and derived commercial entitlement remain `NOT_APPROVED` pending
written rights review. Same-provider quote checks are consistency checks, not independent sourcing.
