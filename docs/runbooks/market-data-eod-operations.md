# Market-data EOD operations

The platform-owned schedule is versioned in `config/market-data-eod.json`. On NSE weekdays it starts
after the regular session, confirms an exchange-complete status, ingests the latest completed bar,
archives the forward observation, checks revisions and quality, and then builds Technical and
Historical snapshots. Internal Fusion may run only after successful upstream completion.

Historical downloads use `BACKFILLED_MARKET_DATA`; observations collected after activation use
`FORWARD_COLLECTED_MARKET_DATA`. If a past provider row changes, store old/new hashes and observed
times. Never overwrite. Auth failure, stale bars, missed sessions, rate limiting, and snapshot failure
are operational incidents. Collection continues on the next eligible session; no order capability exists.
