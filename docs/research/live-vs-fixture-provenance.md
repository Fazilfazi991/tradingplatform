# Live versus fixture provenance

`ALL_FIXTURE` contains no live specialist state. `PARTIAL_LIVE` contains at least one live engine and at least one engineering-only, insufficient or blocked engine. `ALL_LIVE` requires every contributing engine to be genuinely live.

Fixture engines never fill missing live orientations. Internal partial-live Fusion must retain each engine status and default to `ABSTAIN`. Public/customer prediction gates remain unchanged.

As of Batch 11, RBI and SEBI RSS metadata are approved for internal collection. NSE publishes Corporate Information RSS subscriptions for feed readers, but the exact automated internal path and downstream rights remain `REVIEW_REQUIRED`; it is not activated. RBI DBIE, MOSPI, FRED/ALFRED, PIB, BLS, BEA and company IR feeds remain candidates pending endpoint-specific access, licensing and retention review. FRED notes that individual series may carry third-party restrictions.

References: https://www.nseindia.com/static/rss-feed ; https://fred.stlouisfed.org/legal/terms/ ; https://data.rbi.org.in/

