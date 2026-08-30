# Intelligence source policy

Default priority: official API, official feed, official file, official RSS/publication feed, licensed
commercial API, permitted public web access, permitted crawling, then browser automation as a last
resort. Authentication, robots restrictions, rate limits, paywalls, CAPTCHAs, technical controls, and
contractual restrictions may never be bypassed.

Activation requires an explicit access method, terms/robots status where applicable, internal-use
basis, retention and redistribution rules, authentication secret name, conservative request limits,
approved hosts, content types, and bounded downloads. Unclear rights produce `REVIEW_REQUIRED`, not a
best-effort scraper. Commercial permission is never inferred from public visibility.

RBI and SEBI official RSS feeds are active for internal metadata ingestion because their official RSS
pages explicitly invite automated subscription. Fifteen minutes is the minimum polling cadence. Raw
article bodies and customer republication are outside this approval. NSE/BSE/company IR and all
commercial, fundamental, flow, derivative, news, and sentiment sources remain unactivated pending
source-specific rights review.

Source factual reliability and predictive value are scored independently under a versioned policy.
No source receives validated predictive value before formal, chronologically controlled research.
