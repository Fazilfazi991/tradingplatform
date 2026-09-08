# Verified Edge SEO and Search-Intent Strategy

Status: **DRAFT — ACTIVATION REQUIRES CANONICAL DOMAIN AND OWNER APPROVAL**

Scope: public informational Track A pages only

Evidence date: 2026-09-08

This plan maps legitimate product questions to the small set of public pages that already answer
them. It contains no search-volume, ranking, traffic, or conversion estimate. Those values have not
been measured. It does not authorize indexing synthetic forecast demonstrations, internal research,
operator tooling, or data-health diagnostics.

## Search audience and intent

The intended audience is an India-focused reader evaluating market-research software and the
quality of its methodology. The useful questions are:

- What is a market-intelligence or stock-market research platform?
- How can technical, historical, event, macro, fundamental, sentiment, and positioning evidence be
  assessed together?
- Why is a backtest different from a sealed holdout or prospective validation?
- How should uncertainty, contradiction, provenance, and abstention appear in market research?
- What data classes and rights boundaries apply to a research platform covering NSE securities?

These are candidate search themes derived from the product and its intended audience—not measured
keywords. Google recommends people-first content, descriptive titles and headings, concise internal
links, and words that users would naturally use; it does not justify manufacturing pages merely to
capture queries. See [Search Essentials](https://developers.google.com/search/docs/essentials),
[people-first content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content),
and [sitelinks guidance](https://developers.google.com/search/docs/appearance/sitelinks).

## Canonical page map

| Canonical route | Primary intent | Natural theme vocabulary | Required content boundary |
|---|---|---|---|
| `/` | Understand the product | market intelligence platform; stock market research platform; India market research | No accuracy, return, recommendation, or live-data claim |
| `/methodology` | Understand evidence fusion and verification | market research methodology; evidence-based stock research; walk-forward and holdout validation | Explain process, not predictive superiority |
| `/data-sources` | Understand provenance and permitted use | stock market data research; NSE research data; market-data provenance | Do not expose or imply redistribution rights |
| `/validation` | Understand current predictive status | market prediction research; forward paper validation; model validation | Lead with `HOLDOUT VALIDATED — FORWARD REQUIRED` and limitations |
| `/models` | Understand the seven evidence lenses | technical market intelligence; historical stock analysis; market sentiment intelligence | Identify demo, partial, insufficient, and unavailable inputs |
| `/about` | Understand purpose and operating principles | transparent market research; uncertainty-aware market intelligence | No founder, customer, registration, or performance facts without evidence |
| `/faq` | Resolve safety and product-boundary questions | AI market research FAQ; stock research platform questions | Preserve no-advice, no-execution, demo, and rights language |

Each intent has one canonical destination. Do not create city, exchange, sector, stock, or near-copy
landing pages until there is distinct, rights-cleared, people-first content for them. Demo routes such
as `/predictions`, `/stocks/RELIANCE`, `/fusion`, `/historical`, `/intelligence`, and `/sectors`
remain `noindex`; internal routes remain authenticated and `noindex`.

## Editorial rules

1. Write the title and H1 for the reader's question, then use theme vocabulary only where it reads
   naturally. Do not repeat keyword variants mechanically.
2. Prefer evidence-backed explanations, limitations, examples, and links to the relevant
   methodology or data-rights page.
3. Map every quantitative, comparative, accuracy, freshness, coverage, customer, or regulatory
   statement to `CLAIMS_LEDGER.md` before publication.
4. Never use “best stock predictor,” “accurate stock predictions,” “profitable signals,” “BUY/SELL,”
   “target price,” “guaranteed returns,” “proven alpha,” or “SEBI approved.”
5. Treat “Verified Edge” only as the brand name; never imply that the name proves an investment edge.
6. Keep page titles compact and descriptive, summaries specific, headings semantic, and anchor text
   meaningful. Do not auto-generate mass content or rewrite third-party sources.
7. Public content may explain the architecture at a high level but must not disclose internal raw
   research artifacts, credentials, provider payloads, prompt details, or operational telemetry.

## Technical publishing contract

- Publish only the routes emitted by the canonical sitemap and ensure every sitemap URL is absolute,
  HTTPS, self-canonical, and served by the production domain.
- Keep one responsive URL per page. Do not create separate mobile URLs or query-string duplicates.
- Keep internal and demo pages out of the sitemap. Preserve route-level `noindex` and authenticated
  access controls; `robots.txt` is not a substitute for either protection.
- Validate titles, descriptions, canonical links, social images, structured data, response headers,
  internal links, 404 behavior, and public-payload boundaries in the deployed smoke run.
- Submit the canonical sitemap only after the production domain and legal/data-rights gates pass.

Google describes sitemaps as hints and recommends including preferred canonical URLs; it also notes
that `noindex` must be observable by a crawler to take effect. See the official
[sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap),
[canonical guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls),
and [`noindex` guidance](https://developers.google.com/search/docs/crawling-indexing/block-indexing).

## Measurement and change control

No analytics or Search Console integration is active. After the owner approves the privacy model,
canonical domain, and indexing:

1. verify ownership and submit the sitemap in Search Console;
2. record indexed URLs, excluded URLs, query impressions, clicks, click-through rate, and page-level
   search appearance without collecting sensitive research data;
3. review actual query language and user usefulness quarterly;
4. update titles or content only from measured mismatch or genuine product change—not short-term
   ranking churn;
5. open a claim review before expanding into predictive, security-specific, or performance language.

Until those external approvals exist, the correct state is **TECHNICAL SEO READY LOCALLY — INDEXING
NOT ACTIVATED**. No traffic or ranking outcome is promised.
