# Initial intelligence source catalog

| Source | Category | Access | Status | Internal basis | Retention / redistribution |
|---|---|---|---|---|---|
| RBI press releases | Macro/central bank | Official RSS | ACTIVE_INTERNAL | RBI explicitly provides RSS subscription | Feed metadata/hash; no customer republication |
| SEBI releases/circulars/orders | Regulatory events | Official RSS | ACTIVE_INTERNAL | SEBI explicitly provides RSS subscription | Feed metadata/hash; no customer republication |
| Fixture timeline | All contracts | Local fixture | ACTIVE_FIXTURE | Generated test data | Repository fixture |
| NSE announcements | Filings/events | Official web/file candidate | REVIEW_REQUIRED | Specific automated access/retention not approved | No collector |
| BSE announcements | Filings/events | Official web/file candidate | REVIEW_REQUIRED | Specific automated access/retention not approved | No collector |
| NSE index constituents | Universe | Official file | REVIEW_REQUIRED | Current QA only under DR-005 | No historical claim |
| Government/MOSPI macro | Macro | Official files/publications | REVIEW_REQUIRED | Dataset-by-dataset review required | No collector |
| Company IR | Corporate events | Official company pages | REVIEW_REQUIRED | Per-site terms/robots vary | No crawler |
| Professional news | News | Licensed API | BLOCKED_LICENSE | Commercial agreement required | None |
| Fundamentals | Fundamental | Licensed/public filings | PLANNED | Rights and point-in-time revisions required | Fixture only |
| FII/DII and ETF flows | Flow | Official/licensed file/API | PLANNED | Rights and timing validation required | Fixture only |
| OI/IV/skew | Derivatives | Licensed exchange/vendor | BLOCKED_LICENSE | Entitlement required | Fixture only |
| Social/search attention | Sentiment/psychology | Vendor/official API | REVIEW_REQUIRED | No scraping approval | Contract only |
| Cross-market context | Global market | Licensed/public API | REVIEW_REQUIRED | Instrument-specific rights required | Contract only |

Reliability tier reflects factual provenance. Potential predictive value and actual validated
predictive value are separate scorecard fields; every catalog entry currently has predictive status
`UNKNOWN`.
