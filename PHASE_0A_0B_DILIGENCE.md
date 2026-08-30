# Verified Edge — Phase 0A/0B Diligence

**Regulatory perimeter + market-data licensing**  
**Status date:** 30 August 2026  
**Governing specification:** [BLUEPRINT.md](./BLUEPRINT.md)

> Decision-support research, not a legal opinion. “Counsel required” means Indian securities counsel must confirm the conclusion against the final product, copy, contracts, and operating entity. Public documentation cannot grant data rights; only an executed licence or written provider/exchange confirmation can.

## Executive conclusion

**Regulatory gate: CONDITIONAL PASS** for internal R&D and a narrowly educational public product; **BLOCKED** for public security-specific recommendations, paid screeners/signals, setup alerts, or public performance marketing until counsel resolves the RA perimeter and the required RA operating controls are live.

**Data-licensing gate: BLOCKED** for a customer market-data product. Internal prototype research may proceed conservatively on an individual broker API, but none of the reviewed retail API subscriptions publicly grants the full storage, derived-use, customer-display, alert, marketing, and redistribution rights required by the proposed SaaS. Zerodha expressly restricts external display/redistribution. Upstox and Dhan require written commercial confirmation. NSE Data/licensed vendors are the proper commercial path.

No post–6 February 2026 final RA amendment located in the official search changes the core analysis. SEBI issued a 26 February 2026 social-media identity circular effective 1 May 2026 and a May 2026 consultation on institutional call-record relief; a June 2026 common advertisement code was still a proposal, not treated here as operative law.

## A. Regulatory perimeter

### A1. Authorities used

- SEBI [RA Regulations, last amended 25 November 2025](https://www.sebi.gov.in/legal/regulations/nov-2025/securities-and-exchange-board-of-india-research-analysts-regulations-2014-last-amended-on-november-25-2025-_98248.html).
- SEBI [RA Master Circular, 6 February 2026](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770375507051.pdf).
- SEBI [RA FAQs, 23 July 2025](https://www.sebi.gov.in/legal/circulars/jul-2025/frequently-asked-questions-faqs-related-to-regulatory-provisions-for-research-analysts_95549.html).
- SEBI [Advertisement Code, 5 April 2023](https://www.sebi.gov.in/legal/circulars/apr-2023/advertisement-code-for-investment-advisers-ia-and-research-analysts-ra-_69798.html) and [research-report clarification, 24 October 2024](https://www.sebi.gov.in/legal/circulars/oct-2024/clarification-with-respect-to-advertisement-code-for-research-analysts-ras-_87945.html), as consolidated in the 2026 circular.
- SEBI [interim past-performance arrangement, 30 October 2025](https://www.sebi.gov.in/legal/circulars/oct-2025/ease-of-doing-business-interim-arrangement-for-certified-past-performance-of-investment-advisers-and-research-analysts-prior-to-operationalisation-of-past-risk-and-return-verification-agency-parrv-_97556.html).
- SEBI [IA Master Circular, 6 February 2026](https://www.sebi.gov.in/legal/master-circulars/feb-2026/master-circular-for-investment-advisers_99569.html) and [IA investor guide](https://investor.sebi.gov.in/investment_advisor.html).
- SEBI [association/finfluencer clarification, 29 January 2025](https://www.sebi.gov.in/sebi_data/attachdocs/jan-2025/1738152590849.pdf).
- SEBI [social-media registered-name/number circular, 26 February 2026](https://www.sebi.gov.in/legal/circulars/feb-2026/ease-of-doing-investment-eodi-disclosure-of-registered-name-and-registration-number-by-sebi-regulated-entities-and-their-agents-on-social-media-platforms-smps-_100005.html).
- CCPA [Misleading Advertisements and Endorsements Guidelines, 9 June 2022](https://consumeraffairs.nic.in/latestnews/guidelines-prevention-misleading-advertisements-and-endorsements-misleading).

### A2. Material-conclusion register

| Topic | Source/date and relevant rule | Our interpretation | Confidence | Counsel? |
|---|---|---|---|---|
| Security-specific research | RA Regulations (25 Nov 2025); RA FAQs (23 Jul 2025), FAQ 5: regulation is methodology-agnostic and includes security-specific buy/sell/hold research | Algorithmic, technical, fundamental, ranked, or human-written method does not change the perimeter. A setup card expressing a security view is likely research service/research report. | High | Yes, final UI |
| Direct/indirect consideration | RA Master Circular (6 Feb 2026), §1.8: “consideration” includes direct or indirect consideration; even another paid intermediary service can qualify | Paid subscription is clear consideration. Free signals used as acquisition for a paid tier, sponsorship, affiliate revenue, lead sale, or bundled service are not safely “free.” | High | Yes |
| Screeners/rankings | Same definition plus FAQ’s methodology-neutral treatment; no official blanket screener exemption located | Pure user-controlled factual filters are lower risk. Platform-curated ranks, Edge Scores, confidence, bullish/bearish direction, or “top opportunities” can communicate a recommendation. | Medium-high | Yes |
| Entry/target/stop | RA framework covers recommendations/research services; public-media disclosure duties apply | Entry zone, target, or stop-loss makes the action implication explicit and is high-risk pre-registration. “Invalidation” can be analytically useful but paired with a bullish card still functions like a recommendation. | High | Yes |
| Model portfolios | RA Master Circular (6 Feb 2026), §1.11 and Annexure A expressly place model-portfolio recommendations within RA services and prescribe a framework | Model portfolios are not an educational workaround. Block before RA readiness; personalization may create added IA risk. | High | Yes |
| Research report evidence | RA Master Circular §1.8: research services must be corroborated by a report containing relevant data/analysis and the report maintained | Every published setup needs a reproducible, retained research report; a UI card alone is insufficient evidence. | High | No for control; yes for format |
| AI responsibility | RA Master Circular §1.7 cites Regs. 24(7), 19(vii): RA is solely responsible for security, confidentiality, integrity, data and AI-based output; disclose extent of AI use | “AI generated” does not transfer responsibility. Vendor and in-house models need validation, controls, security, records, and client disclosure. | High | No |
| Social publication | RA Regulations/FAQs public-appearance/public-media duties; Advertisement Code covers websites, email, messages, social, radio/TV; 26 Feb 2026 circular requires registered name/number on social profiles/posts from 1 May 2026 | YouTube, Instagram, X, Telegram, WhatsApp, email, and creator content are not informal exceptions. Treat each as controlled research/advertising publication. | High | Yes, channel playbooks |
| Research vs advertisement | 24 Oct 2024 clarification: research report/recommendation is not an ad unless it expressly or impliedly promotes RA products/services | A report becomes an ad when it contains sales copy, trials, pricing, CTA, or implied promotion. Separate editorial evidence from conversion modules. | High | No |
| Past/risk-return claims | RA Master Circular advertising code §11: prohibited unless metrics are PaRRVA-verified and used as SEBI specifies | Public backtest, validation, holdout, or forward-paper return metrics used to promote the service are blocked absent the prescribed verification route. Calling them “simulated” is disclosure, not permission. | High | Yes |
| Interim performance route | SEBI circular 30 Oct 2025: certified historical performance can be sent one-to-one only after a client/prospect specifically requests it; not general public/website; required disclaimer; transitional | This does not authorize a public performance dashboard. Confirm whether and when PaRRVA is operational for the intended metrics before any release. | High | Yes |
| Influencer association | SEBI circular 29 Jan 2025: regulated persons/MIIs and agents cannot associate with an unregistered person giving securities advice/recommendations or return claims; investor education exception is narrow | Once registered, do not pay or partner with unregistered finfluencers who recommend securities or claim returns. Creator education needs a written content boundary and approval. | High | Yes |
| Personalization | IA framework: advice based on goals, risk appetite and suitability is the defining feature; risk profiling/suitability are IA controls | Holdings/goals/capital/risk-derived recommendations, sizing, allocation, or rebalancing are IA territory even if the underlying research began as RA output. | High | Yes |
| Disclaimer effect | Substance of RA/IA definitions and enforcement framework | “Not financial advice,” “education only,” paper trading, delayed data, or an AI label does not cure a functional recommendation. | High | No |

### A3. Feature-specific RA analysis

| Output | Risk before RA registration | Reason / required posture |
|---|---|---|
| Generic market regime and broad-index commentary | Low–caution | RA FAQ excludes general market trends, broad indices, economic/political/market commentary; do not attach security calls or return promotion. |
| Market breadth / index or sector demand-supply analysis | Low–caution | Statistical summaries and sector/index technical analysis are identified exclusions; data licence still applies. |
| User-selected factual screener | Caution | Limit to objective facts and transparent filters; no platform rank, direction, “opportunity,” action language, target, or confidence. Counsel review. |
| Platform stock ranking / Edge Score | High | Selection and ordering communicate preference/recommendation. |
| Bullish/bearish signal | High | Directional security-specific research. |
| Entry, target, stop loss | High | Actionable recommendation characteristics. |
| Invalidation level | Caution–high | Safer as methodology education; high-risk when attached to a current security setup. |
| Free current signals as paid-funnel acquisition | High | Indirect consideration and advertising concerns. |
| Paid setup cards/screener | High | Direct consideration for security-specific research. |
| Paper/forward signal ledger | High if public | Paper status does not change the security recommendation; public performance adds claim restrictions. Internal ledger is permitted R&D subject to data terms. |
| Model portfolio | High | Expressly governed RA research service; IA risk if individualized. |

## A4. Investment Adviser feature matrix

| Feature | Rating | Boundary |
|---|---|---|
| Same non-personalized report for all clients | SAFE from IA, not necessarily RA | No user-specific recommendation or allocation. |
| Watchlist chosen entirely by user | SAFE–CAUTION | Store/alert factual events only; do not infer suitability. |
| User imports holdings for factual aggregation | CAUTION | Analytics can imply advice; isolate from recommendation engine and obtain counsel. |
| Generic educational position-sizing calculator | CAUTION | No security recommendation, saved risk profile, or “you should invest” output. |
| Risk profiling | HIGH-RISK | Core IA function when used for advice. |
| Recommendation based on holdings/goals/time horizon | HIGH-RISK | Personalized advice/suitability. |
| Position size based on user capital or loss tolerance | HIGH-RISK | Personalized allocation/risk advice. |
| Asset allocation or portfolio rebalancing | HIGH-RISK | IA perimeter. |
| User-specific risk level attached to a security | HIGH-RISK | Suitability conclusion. |
| Broker execution | HIGH-RISK / separate perimeter | Adds broker, retail-algo, consent, cyber, and possible IA/RA issues. |

## A5. AI and automated research control standard

Algorithms, ML, and LLMs are all tools; the registered entity remains accountable. Required design posture:

- Disclose where AI materially participates in research services and explanations.
- Human maker-checker approval for strategy versions, public templates, exceptional outputs, and corrections. The official rule assigns responsibility; it does not create a general “human in every loop” safe harbor, so the exact approval model needs counsel/RAASB confirmation.
- Retain input dataset/version, model/artifact hash, prompt/template, retrieved sources, output, reviewer, timestamps, decision, and research report.
- Validate hallucination, arithmetic, consistency, bias, drift, injection, and restricted-data leakage. LLM prose may explain approved structured facts; it must not invent or silently alter the signal.
- Contractually assess AI vendors; prohibit training on client/confidential data unless expressly approved; apply least privilege, encryption, retention and deletion controls.
- Keep reproducible structured results authoritative. An LLM cannot be the system of record.

## A6. Performance-display classification

These categories address public/customer use, especially promotion; internal audit reporting remains possible under controlled access and data rights.

| Item | Category | Conditions / reason |
|---|---|---|
| Methodology with no performance number | ALLOWED/CONDITIONAL | Truthful, non-promotional research; compliance approval and data rights. |
| Backtest, validation, holdout returns or curves | HIGH-RISK | Risk/return metric and simulated-claim risk; PaRRVA/prescribed framework and counsel required. |
| Forward paper returns/curves | HIGH-RISK | Still hypothetical/non-executed and a performance claim; verification label does not replace PaRRVA. |
| CAGR, Sharpe, win rate, expectancy, profit factor, drawdown | HIGH-RISK | Each is a performance/risk-return metric when used for RA service promotion. |
| Benchmark comparison | HIGH-RISK | Can be unfair/cherry-picked; requires prescribed verification, matched methodology and full disclosure. |
| Number of timestamped signals without outcomes | CONDITIONAL | Factual but can imply scale/quality; audit, context, no promotion. |
| “Forward Testing” status | CONDITIONAL | Describe process only; no implied profitability or superiority. |
| “Forward Verified” | HIGH-RISK | May imply regulatory/independent verification. Do not use publicly until counsel, PaRRVA and naming review; identify verifier precisely. |
| Customer profit screenshots/testimonials | DO NOT USE | Selective, non-representative, unverifiable, privacy/endorsement and performance-claim risk. |
| Certified performance sent after specific request | CONDITIONAL | Only under current SEBI interim terms: one-to-one, requested, certified, prescribed disclaimer; counsel confirms current availability. |

Minimum disclosure, if a metric is ever permitted: simulated/paper/actual status; gross/net; all fee, tax, spread and slippage assumptions; exact dates; universe and survivorship treatment; benchmark; sample size; cash/exposure; methodology/version; corrections; uncertainty; limitations; and “past performance does not indicate future results.” Disclosure never cures a prohibited claim.

## A7. Advertising and proposed copy

The RA Advertisement Code demands truthful, fair, clear, unambiguous content; prohibits misleading claims, assured/risk-free returns, unfair comparisons, superlatives, and unverified risk-return metrics; and requires supervisory-body approval where applicable. CCPA rules separately require truthful substantiated advertising and genuine, adequately informed endorsements.

| Line | Rating | Treatment |
|---|---|---|
| “Backtested isn’t verified.” | LOW RISK | Educational claim; do not imply SEBI/PaRRVA verification of this product. |
| “See the evidence behind every setup.” | NEEDS QUALIFICATION | Use only when every displayed setup has accessible, complete evidence and the setup itself is lawfully published. Prefer “See the methodology and evidence status…” |
| “Most backtests fail when reality arrives.” | NEEDS QUALIFICATION | “Most” is an empirical comparative claim. Replace with “Backtests can fail out of sample and in forward use.” |
| “Forward-tested market intelligence.” | NEEDS QUALIFICATION | Define paper-only, dates/sample, and no performance implication; avoid until public forward records are legally cleared. |

Website, Meta/Google ads, YouTube, Instagram, X, Telegram, WhatsApp, email, affiliates and creators all enter the controlled publication inventory. Require versioned copy, substantiation, conflicts, approval ID, expiry/review date, channel owner and archive. From 1 May 2026, regulated entities/agents must prominently disclose registered name and registration number on social-media profiles/posts as specified. Platform ad policies are additional, not substitutes for law.

## A8. Registered-RA onboarding/operations

| Requirement | Classification | Basis / note |
|---|---|---|
| SEBI registration and RAASB enlistment | REQUIRED | RA Regulations; BSE recognized as RAASB. |
| Qualification/NISM certification; principal officer | REQUIRED | Regulation 7 and Master Circular §1.1. |
| Deposit linked to client count | REQUIRED | Master Circular §1.2: ₹1 lakh up to 150 clients, scaling to ₹10 lakh at 1,001+. |
| Client KYC for fee-paying clients | REQUIRED | Investor Charter/onboarding duties. |
| Terms, MITC and affirmative client consent before service/fee | REQUIRED | Reg. 24(6); Master Circular §1.12 and annexures. |
| Fee ceiling/method/refund controls for individual/HUF clients | REQUIRED | Master Circular §1.9; current maximum ₹1,51,000/year/family excluding statutory charges. |
| Research report behind service | REQUIRED | Reg. 20(4); §1.8. |
| Disclosures: business, discipline, associates, risks, conflicts, AI use | REQUIRED | Regulations/Master Circular/Investor Charter. |
| Records and digitally signed/timestamped research records | REQUIRED | RA recordkeeping framework; exact implementation to be confirmed. |
| Client/prospect communication recording | REQUIRED, with scoped exceptions | Master Circular; May 2026 institutional relaxation was consultation at search date. |
| Grievance officer, SCORES/ODR, complaint disclosures | REQUIRED | Master Circular investor-grievance sections/charter. |
| Website and prescribed disclosures/complaint data | REQUIRED | Reg. 19A and Master Circular. |
| Annual compliance audit and adverse-finding publication/reporting | REQUIRED | Master Circular §1.14. |
| Compliance officer/independent professional | POSSIBLY REQUIRED | Depends on entity form; non-individual framework. |
| PMLA/KYC reporting stack | POSSIBLY REQUIRED | Confirm exact RA obligations and KRA workflow with counsel/compliance vendor. |
| Personalized suitability/risk profiling | NOT APPLICABLE TO CURRENT MODEL | Must remain absent; becomes IA analysis if introduced. |
| Execution/order handling | NOT APPLICABLE | RA MITC states RA cannot execute client trades. |

## A9. Maximum conservative pre-registration public product

Potentially publish, after counsel and data-rights review:

- Investor education on leakage, overfitting, expectancy, costs and validation.
- Methodology pages using synthetic or properly licensed non-current examples.
- Broad-index market-regime commentary, aggregate breadth, and sector/index technical demand-supply analysis without security calls.
- Delayed factual data only under an express licence; otherwise no exchange-derived public dashboard.
- Rejected-strategy reports without current security recommendations or public performance promotion; avoid metrics until reviewed.
- Waitlist, interviews, product principles, status definitions, and evidence-process demonstrations.

Do not include current security ranks, setup cards, bullish/bearish labels, Edge/Confidence scores, entry/invalidation/target/stop, setup alerts, model portfolios, or any paid/free funnel signal.

## B. Market-data rights

### B1. Governing facts

NSE’s [Data Sharing & Usage Policy, updated 11 December 2025](https://www.nseindia.com/static/market-data/nse-data-policy) covers live, delayed, EOD, historical and corporate data; usage, display and redistribution are controlled by the executed agreement, and redistribution is not allowed unless agreed. NSE’s [non-display policy](https://nsearchives.nseindia.com/s3fs-public/inline-files/Non_Display.pdf) expressly includes derived values used for internal analysis. [Tariffs effective 1 April 2026](https://www.nseindia.com/static/market-data/products-tariff) exist for domestic/international products; exact SaaS, display, derived and end-user charges require a quote.

Zerodha’s [Kite terms](https://kite.trade/terms/) prohibit public-at-large live display, redistribution, permanent/cached copies intended for redistribution, derivative works/public display/sublicensing absent permission, and virtual/mock trading apps; its [official support answer](https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/can-i-use-historical-and-live-data-taken-from-kite-connect-api-on-other-platforms) says Kite data cannot be displayed on other platforms and directs users to an exchange-authorized vendor.

Public Upstox and Dhan API documentation describes API capability, not a sufficiently specific commercial market-data licence. Therefore all externally facing rights are unresolved.

### B2. Provider rights matrix

| Provider | Internal research | Storage | Derived analytics | Customer display | Alerts | Commercial SaaS | Redistribution | Written approval required |
|---|---|---|---|---|---|---|---|---|
| Upstox retail API | LIKELY ALLOWED for individual prototype | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | LIKELY RESTRICTED | **Yes, all commercial/retention/derived uses** |
| Zerodha Kite retail | LIKELY ALLOWED for personal research | LIKELY RESTRICTED beyond necessary cache | LIKELY RESTRICTED for commercial derivative work | **CONFIRMED RESTRICTED** on external platforms | LIKELY RESTRICTED commercially | **CONFIRMED RESTRICTED** under retail terms | **CONFIRMED RESTRICTED** | **Yes; business agreement + exchange/vendor rights** |
| DhanHQ retail data API | LIKELY ALLOWED for individual research | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | LIKELY RESTRICTED | **Yes, partner/data licence** |
| NSE Data direct | CONFIRMED ALLOWED only as contracted | CONFIRMED ALLOWED only as contracted | Contract/non-display licence required | Contract/display licence required | Contract required | Contract required | Contract-specific | **Yes; executed relevant agreement** |
| NSE authorized vendor | Contract-specific | Contract-specific | Contract-specific | Contract-specific | Contract-specific | Contract-specific | Contract-specific | **Yes; vendor + exchange pass-through rights** |

For each provider, public charts, authenticated display, real-time/delayed/EOD display, email/push alerts, screenshots/social, API outputs, white label, permanent/termination retention, DR/audit copies, ML training and trained-artifact retention remain **WRITTEN CONFIRMATION REQUIRED** unless the executed contract explicitly grants them. “Derived signal” is not automatically free of exchange rights.

### B3. Licensed-vendor path

Ask NSE Data for a direct quote and solicit at least two current [authorized real-time data vendors](https://www.nseindia.com/static/market-data/real-time-data-subscription) for EOD/delayed display plus non-display/derived use. Evaluate vendors on point-in-time index constituents, corporate actions/adjustment methodology, survivorship-free history, entitlement enforcement, redistribution/API/white-label rights, geographic scope, audit/reporting, SLA, correction feed, termination retention, and total exchange + vendor + per-user cost. No public source establishes that one named vendor is “materially better” for this exact SaaS; selection requires RFP responses.

## C. Provider comparison update / BLUEPRINT errata

| Original claim | Current finding (30 Aug 2026) | Change? | Reason/source |
|---|---|---|---|
| Upstox daily from Jan 2000; intraday from Jan 2022 | Confirmed | No | [Historical V3](https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/) |
| Upstox India VIX/global context | Confirmed; global indicators also documented | No | Historical V3/WebSocket docs |
| Upstox standard REST 50/s, 500/min, 2,000/30m | Confirmed for standard APIs | No | [Rate limits](https://upstox.com/developer/api-documentation/rate-limiting/) |
| Upstox normal WebSocket 2 connections; 5,000 LTPC / 2,000 full alone | Confirmed; combined limits differ and Plus permits 5 connections/Full D30 conditions | Clarify | [WebSocket V3](https://upstox.com/developer/api-documentation/v3/get-market-data-feed/) |
| Upstox daily token | Standard token expires 3:30 AM next day; **new Analytics Token has one-year read-only validity** | **Yes** | [Get Token](https://upstox.com/developer/api-documentation/get-token/); [17 Mar/6 Jun 2026 announcement](https://upstox.com/developer/api-documentation/announcements/) |
| Upstox sandbox order-oriented | Confirmed phased; order APIs currently highlighted | No | [Sandbox](https://upstox.com/developer/api-documentation/sandbox/) |
| Upstox core access appears free | Public docs still do not provide a complete commercial-data price/licence | Clarify | WRITTEN CONFIRMATION REQUIRED |
| Kite ₹500/month for history + WebSocket | Confirmed | No | [Kite pricing](https://zerodha.com/products/api/) |
| Kite several years, OI, intervals | Confirmed; exact historical depth not guaranteed by a single universal start date | Clarify | [Historical docs](https://kite.trade/docs/connect/v3/historical/) |
| Kite 3 WS connections, 3,000 instruments/connection, 5-depth | Confirmed | No | [WebSocket docs](https://kite.trade/docs/connect/v3/websocket/) |
| Kite limits history 3/s, quote 1/s, other 10/s | Confirmed | No | [Limits](https://kite.trade/docs/connect/v3/exceptions/) |
| Kite token daily | Confirmed: expires 6 AM next day; long-lived read permission only for approved platforms | Clarify | [User/auth docs](https://www.kite.trade/docs/connect/v3/user/) |
| Kite sandbox is strongest | Sandbox exists, but historical availability may vary and retail terms prohibit virtual/mock trading apps in production data | Clarify | [Sandbox](https://kite.trade/docs/connect/v3/sandbox/); Kite terms |
| Dhan daily/OI, up to five years minute history | Confirmed by release notes | No | [Dhan releases](https://dhanhq.co/docs/v2/releases/) |
| Dhan data 5/s, 100k/day; quote 1/s | Confirmed current docs | No | [Dhan docs](https://dhanhq.co/docs/v2/) |
| Dhan up to 5 connections/5,000 instruments; advanced depth | Confirm capability, but product/add-on entitlements require quote | Clarify | Dhan docs/releases |
| Dhan ₹499 + tax/month data | Confirmed | No | [Dhan support](https://dhan.co/support/platforms/dhanhq-api/how-does-the-dhanhq-data-api-subscription-work/) |
| Dhan token details not stated | 24-hour access token; API key/secret 12 months; renewal/generation flows documented | **Yes** | [Authentication](https://dhanhq.co/docs/v2/authentication/) |
| Upstox recommended prototype adapter | Still reasonable technically, but only for conservative internal spike | No, strengthen caveat | Commercial and long-term rights unresolved |

## D. Master regulatory feature matrix

| Feature | Pre-RA educational product | RA product | Possible IA territory | Data-licence dependency | Recommendation |
|---|---|---|---|---|---|
| Market regime | Yes, broad-index/general | Yes | Low | High if exchange-derived display | Build after licence/counsel review |
| Breadth | Yes, aggregate | Yes | Low | High | Build internally; public only licensed |
| Sector leaderboard | Caution: objective sector/index facts | Yes | Low | High | Avoid “buy leaders” framing |
| Stock screener | Caution: user-selected facts | Yes | Medium if personalized | High | Internal now; public after counsel |
| Stock ranking | No | Yes with controls | Medium | High | Block pre-RA |
| Bullish/bearish label | No | Yes with research report | Medium | High | Block pre-RA |
| Entry/target/stop/invalidation | No for current stocks | Yes with controls | High if tailored | High | Block pre-RA |
| Edge/Confidence Score | No | Conditional, methodology and calibration | Medium | High | Block; rename/review |
| Watchlist | Factual user list | Yes | Medium if used to tailor | High for alerts/data | Basic list only |
| Alerts | Aggregate education only | Conditional | High if personalized | High | Block setup alerts |
| Paper portfolio | Internal only | Model-portfolio rules may apply | High if tailored | High | Block public |
| Model portfolio | No | Express RA framework | High if personalized | High | Block |
| Portfolio import | No initially | Caution | High | Broker/data/privacy | Block V1 |
| Personalized sizing | No | Not safely RA-only | High | Derived price/data | Block |
| Risk profiling | No | Not RA feature | High | Low | Block |
| Broker execution | No | RA cannot execute for client | High/separate algo | High | Block |
| Strategy/forward performance | Education without public metrics | Only prescribed verification/disclosure | Medium | High | Block public metrics |

## E. Decision records

### DR-002 — Regulatory Operating Perimeter

**Status:** CONDITIONAL PASS (internal + narrow education); BLOCKED (signals/paid research)

**Decision:** Build only internal research infrastructure and a separable educational content shell. No current security-specific rank, setup, signal, target, stop, Edge Score, setup alert, model portfolio, public paper ledger, or performance metric until counsel signs the perimeter and required RA operations are live.

**Rationale / known facts:** RA rules are methodology-neutral, cover direct and indirect consideration, expressly regulate model portfolios and AI responsibility, and constrain performance advertising. IA risk begins with user-specific suitability/allocation.

**Assumptions:** V1 remains non-personalized, no execution, no holdings/goals/capital inputs, and no public signals before approval.

**Unresolved / blockers:** entity structure; whether each proposed factual screener/rank is research; PaRRVA operational route and permitted metrics; exact advertising/approval workflow; RAASB interpretation; DPDP/PMLA/KYC implementation; final copy/channel rules.

**Required external confirmation:** written Indian securities counsel opinion; RAASB/SEBI clarification where counsel advises; compliance professional onboarding plan.

**Next review:** 30 November 2026 or immediately on a SEBI/RAASB amendment, final common advertisement code, PaRRVA change, or material product change.

**Engineering may begin:** internal data-quality architecture, experiment registry, backtest/validation design using licensed/prototype data, audit controls, synthetic-data UI components, and educational CMS isolated from signal services.

**Remains blocked:** customer signal engine/surfaces, personalization, payments for research, public performance, signal marketing, creator campaigns, and execution.

### DR-003 — Market Data Licensing Strategy

**Status:** BLOCKED for customer product; CONDITIONAL internal prototype

**Decision:** Use Upstox only for a small internal technical/reconciliation spike under its applicable account terms. In parallel run an RFP with NSE Data and at least two authorized vendors. Do not expose, market, or permanently rely on broker API data until rights are executed.

**Rationale / known facts:** NSE controls display, redistribution and non-display/derived usage contractually. Zerodha expressly prohibits external display/redistribution under retail access. Upstox/Dhan public API capability pages do not grant the needed commercial rights.

**Assumptions:** prototype is internal, access-controlled, no public display, no resale, no API, minimal necessary retention, and deleted/migrated if terms require.

**Unresolved / blockers:** storage/termination, derived metrics/signals, ML artifacts, display delay, alerts, screenshots, geography, end-user fees/reporting, audit, DR copies, white label, API and exchange pass-through charges.

**Required external confirmation:** signed provider/vendor agreement and exchange entitlements; written answers to the questionnaires in `provider-questionnaires/`.

**Next review:** 31 October 2026 or on first binding commercial response.

**Engineering may begin:** provider-neutral interfaces, entitlement metadata schema, synthetic fixtures, ingestion spike, reconciliation and provenance controls.

**Remains blocked:** production historical archive, customer charts/prices, derived setup display/alerts, public screenshots, paid SaaS, external API and white label.

## F. Go / no-go handoff

### What we can safely build now

- Provider-neutral schemas/interfaces, synthetic fixtures, audit/provenance/entitlement controls, experiment registry, sealed validation workflow, and educational CMS separated from recommendations.
- A minimal internal Upstox spike if account terms are accepted and retention is minimized.

### What we can research internally now

- Data quality, point-in-time universe, corporate actions, cost model, four preregistered hypotheses, simulator correctness and provider reconciliation—without publishing signals or performance.

### What we should not build yet

- Customer stock ranks/setups, entry/target/stop, Edge/Confidence scores, signal alerts, paper/model portfolios, performance dashboards, paid research checkout, personalization, creator campaigns, API/white label, or execution.

### Written provider confirmation required

- Every raw/derived storage, training, artifact, display, delay, alert, screenshot, geographic, termination, DR/audit, subscription, API and white-label right listed in the questionnaires.

### Indian securities counsel required

- Final RA/IA classification; pre-registration public scope; screener/rank/score design; free-funnel signals; performance/PaRRVA; advertisements and creators; entity/RAASB/KYC/PMLA/DPDP operations; and all product copy/disclosures.

### RA registration if counsel agrees

- Before any direct/indirectly monetized security-specific research, ranks, signals, setup cards, model portfolios, or related alerts; implement the full onboarding, reporting, research-record, disclosure, audit, grievance, website, social-media and advertisement controls counsel/RAASB specifies.

## Final gates

**REGULATORY GATE: CONDITIONAL PASS** — internal R&D and the narrowly defined educational product only. Security-specific public/paid research remains blocked pending counsel and, if advised, RA registration/readiness.

**DATA LICENSING GATE: BLOCKED** — customer display, commercial derived outputs, alerts, screenshots, API and white label remain blocked until an executed licence grants each intended use.
