# DR-006: Second-source reconciliation

Status: Deferred; mandatory before formal validation  
Date: 2026-08-30

## Decision

No independent, legitimately usable market-data source is configured. A random public website will
not be scraped to manufacture a pass. The required 20-symbol, two-year comparison is deferred.

The risk is undetected provider omissions, timestamp/date errors, unannounced adjustment policy,
and price or volume corruption. Temporary controls are immutable raw payloads, strict OHLC and
timestamp validation, gap/duplicate/conflict detection, quarantine, deterministic replay, and
provider-specific manifests. Conflicting providers must never be silently averaged.

Before formal model validation, a licensed independent source must be approved and the same 20
symbols and sessions compared for dates, OHLC, volume, missing bars, and corporate-action
discontinuities. All unexplained differences must be resolved or quarantined under a versioned
policy. Until then, `SECOND SOURCE = DEFERRED`.

