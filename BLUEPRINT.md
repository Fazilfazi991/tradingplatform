# Verified Edge — Product + Quant + Technical Blueprint

**Decision draft:** 1.0  
**As-of date:** 30 August 2026  
**Launch market:** India (NSE first)  
**V1 mode:** Liquid-equity swing research and forward paper signals only

> This is a product and research plan, not legal or investment advice. Before any public signal, paid research service, advertising campaign, or customer display of exchange data, obtain written advice from Indian securities counsel and written data-use approval from the relevant exchange/provider.

## Executive decision

Build an internal evidence engine before a public signal product. V1 covers the current constituents of the NIFTY 200, daily bars, long-only 2–10-session swing setups, four interpretable strategy families, and append-only paper signals. It excludes options, intraday strategies, personalized advice, portfolio allocation, broker execution, user-entered holdings, and claims of verified performance.

Use **Upstox V3 as the prototype research adapter**, because it presently offers daily history from January 2000, intraday history from January 2022, broad interval control, India VIX/global context, 50 standard REST requests/second, and a capable WebSocket feed. This is an engineering choice—not permission to redistribute its data. In parallel, request written commercial-use terms from Upstox and pricing from NSE Data. Keep Zerodha and Dhan adapters behind the same interface.

The public product should not publish security-specific paid signals until counsel confirms the operating model and, if required, the business is registered and operationally ready as a Research Analyst (RA). A generic “analytics” label does not neutralize substance. Personalized advice, suitability, or portfolio allocation moves the product toward the Investment Adviser (IA) perimeter.

The product promise is: **Backtested isn’t verified. Every setup shows what evidence exists—and what does not.**

## 1. Product vision

### The job to be done

For a self-directed Indian equity investor, answer: “What liquid swing setups exist now, why do they qualify, what happened in genuinely prior comparable cases, what evidence tier has the strategy reached, and what invalidates the thesis?”

### V1 is

- An internal quant lab, data-quality console, experiment registry, and timestamped paper-signal ledger.
- A later customer research experience showing market regime, screened setups, versioned methodology, evidence partitions, uncertainty, risk, and degradation.
- Daily/EOD-first. A post-close research run produces candidates for the next session; no latency claim is needed.
- Evidence-tiered: Experimental → Backtested → Validation Passed → Holdout Passed → Forward Testing → Forward Verified → Degraded/Paused/Rejected.

### V1 is not

- A price oracle, “sure-shot” tip service, trading terminal, order router, robo-adviser, copy-trading service, portfolio manager, or options platform.
- Personalized allocation or suitability advice.
- Real-money execution or a claim that paper fills equal executable returns.
- A polished paid SaaS before research, licensing, and compliance gates pass.

### North-star and guardrail metrics

The research north star is **net out-of-sample expectancy with uncertainty**, not win rate. Product metrics are weekly active research users, setup-to-evidence-detail rate, alert usefulness, free-to-paid intent, retention, and trust survey. Guardrails: data incident count, unreconciled bars, unsealed experiment mutations, correction rate, compliance incidents, and percentage of customer-visible numbers traceable to an immutable run.

## 2. India compliance and data perimeter

### Current official baseline

SEBI issued updated [Master Circulars for Research Analysts](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770375507051.pdf) and [Investment Advisers](https://www.sebi.gov.in/legal/master-circulars/feb-2026/master-circular-for-investment-advisers_99569.html) on 6 February 2026, following 2025 amendments. The RA circular treats research services provided “for consideration” broadly, including indirect consideration, requires research services to be corroborated by a maintained research report, and makes an RA responsible for AI-supported outputs, data security, confidentiality, and disclosure of AI use. It also describes client onboarding/KYC, disclosures, records, grievance handling, audits, website information, and advertisement-code duties.

SEBI’s investor explanation distinguishes an IA through [personalized guidance, risk profiling, and suitability](https://investor.sebi.gov.in/investment_advisor.html). Therefore:

- A non-personalized, security-specific recommendation sold directly or indirectly is high-risk RA territory.
- User-specific “buy this for your portfolio,” sizing, allocation, risk-fit, or financial-goal guidance is high-risk IA territory.
- Free signals used to acquire paid subscribers may still involve indirect consideration; “free tier” is not a safe harbor.
- A screener can cross into recommendation through ranking, direction, entry/invalidation, targets, confidence, or persuasive calls to act. Product substance, not labels, controls the risk.

### Recommended operating posture

1. **Internal alpha:** employees/contractors only; no public security-specific outputs.
2. **Public education/data utility:** only after counsel reviews each page, ranking, alert, disclaimer, and funnel. Prefer regime education and methodology before calls.
3. **Research service:** assume RA registration/RAASB supervision may be required if paid or indirectly monetized security-specific research is published. Design operations for that outcome now.
4. **No IA features in V1:** do not collect goals/risk profile to tailor securities; do not recommend allocations or rebalance portfolios.
5. **No execution:** revisit only through a separate regulatory, broker, exchange, cyber-risk, and retail-algo review.

### Compliance-by-design backlog

- Preserve the research report and evidence snapshot behind every customer-visible setup.
- Version disclosures, conflicts, terms, methodology, corrections, and AI-use statements.
- Log client/prospect research communications and consent where applicable.
- Separate editorial/research approval from growth; marketing cannot alter evidence labels.
- Add maker-checker approval, correction notices, complaint handling, record retention, KYC/payment gating if required, annual compliance audit workflow, and website disclosure registry.
- Ban guaranteed returns, selective winner screenshots, unverifiable testimonials, cherry-picked periods, misleading annualization, and “accuracy” without a precise denominator.
- Have counsel map the final model against the RA Regulations, IA Regulations, February 2026 master circulars, Advertisement Code, ASCI rules, consumer-protection law, privacy/data law, and current retail-algo framework.

### Market-data rights

The [NSE Data Sharing & Usage Policy](https://www.nseindia.com/static/market-data/nse-data-policy) covers real-time, delayed, EOD, historical, corporate, and derived uses. It requires an agreement for intended use and says redistribution is prohibited unless agreed; commercial access is priced. NSE also separately treats algorithmic/derived internal use as [non-display usage](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Non_Display_Policy.pdf). Accordingly:

- Broker API access is not evidence of display, redistribution, derived-data, or commercial SaaS rights.
- Obtain written answers covering internal research, storage duration, derived metrics, screenshots, customer display, alerts, caching, audit, affiliates, and number of end users.
- Prototype with broker data; procure exchange/licensed-vendor rights before customer launch if required.
- Store provenance and entitlement on every dataset. Build a display policy engine so restricted fields never leak to an unentitled surface.

## 3. Market-data API comparison

| Criterion | Upstox V3 | Zerodha Kite Connect | DhanHQ v2 |
|---|---|---|---|
| Daily history | From Jan 2000; up to 10 years/request | Several years; request-range constraints | Daily OHLCV/OI; confirm equity start dates in pilot |
| Intraday history | From Jan 2022; 1–300 minute and 1–5 hour intervals | Minute, 3/5/10/15/30/60 minute | Up to 5 years minute history stated |
| OI | Candle field for derivatives | Optional historical OI | Futures/options OI; expired-options capability |
| Live | Protobuf WebSocket; LTPC/full/greeks | Binary WebSocket; LTP/OHLC/5-depth | Binary WebSocket; quote/OI/depth; advanced depth products |
| Capacity | Normal: 2 connections; up to 5,000 LTPC or 2,000 full alone | 3 connections; 3,000 instruments each | Up to 5 connections/5,000 instruments stated |
| REST limits | Standard APIs 50/s, 500/min, 2,000/30 min | history 3/s; quote 1/s; most others 10/s | data 5/s and 100k/day; quote 1/s |
| Sandbox | Phased; currently order-oriented | Demo market/order environment; some historical availability varies | Developer kit; validate capabilities during spike |
| Published price | Core developer access appears free; Plus affects enhanced features—obtain written quote | Connect ₹500/month for WebSocket + history | Data API ₹499 + tax/month; trading APIs free |
| Commercial product | Must obtain business/data terms | Has a business/platform path; contact Zerodha | Explicit partner path; contact Dhan |
| V1 fit | Best research-data shape and throughput | Most mature alternative and strongest sandbox story | Strong depth/options and five-year intraday, but unnecessary for EOD V1 |

Official references: [Upstox historical V3](https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/), [Upstox WebSocket V3](https://upstox.com/developer/api-documentation/v3/get-market-data-feed/), [Upstox limits](https://upstox.com/developer/api-documentation/rate-limiting/), [Kite pricing](https://zerodha.com/products/api/), [Kite historical](https://kite.trade/docs/connect/v3/historical/), [Kite WebSocket](https://kite.trade/docs/connect/v3/websocket/), [Kite limits](https://kite.trade/docs/connect/v3/exceptions/), [Kite sandbox](https://kite.trade/docs/connect/v3/sandbox/), [Dhan docs/limits](https://dhanhq.co/docs/v2/), [Dhan releases](https://dhanhq.co/docs/v2/releases/), and [Dhan data pricing](https://dhan.co/support/platforms/dhanhq-api/how-does-the-dhanhq-data-api-subscription-work/).

### Recommendation and acceptance test

Select Upstox for a 10-day, read-only spike. It wins only if it passes: complete NIFTY 200 mapping; ≥99.95% expected daily bars after legitimate exceptions; timestamp/time-zone correctness; split/dividend reconciliation; index/VIX availability; stable auth and retry behavior; documented rate-limit behavior; and written confirmation of prototype use. A second-source sample of 20 symbols × 2 years must reconcile OHLC and volume within documented tolerances. Failure triggers a Zerodha spike, then Dhan.

## 4. Stock universe

Use **point-in-time NIFTY 200 membership**, NSE equity series, excluding suspended securities and observations that fail price/liquidity/history rules. NIFTY 50 is too concentrated for strategy samples; NIFTY 500 creates more corporate-action, survivorship, and liquidity burden; NIFTY 100 is a safe fallback but unnecessary if daily-only ingestion works.

At each signal date require: then-current membership; ≥252 valid prior sessions; median 20-day traded value ≥₹25 crore; close ≥₹50; no unresolved corporate action/data incident; and no entry when the next session cannot be modeled. These are frozen V1 thresholds and may be changed only in a new version. Store membership effective dates—never backtest today’s constituents through history. Add BSE only for reference/corporate-action reconciliation, not signal generation.

## 5. Exact data model

Use PostgreSQL/Supabase for metadata and product data; store research matrices/artifacts as immutable Parquet in object storage. Times are `timestamptz` UTC plus source exchange time/zone. Monetary values are `numeric`, not float.

| Table | Essential columns and key |
|---|---|
| `providers` | `id PK, name, environment, terms_version, entitlement_json, active` |
| `instruments` | `id UUID PK, isin, exchange, segment, symbol, company_name, tick_size, status, valid_from, valid_to`; unique `(exchange, segment, symbol, valid_from)` |
| `instrument_provider_ids` | `instrument_id, provider_id, provider_key, valid_from, valid_to`; composite PK |
| `index_memberships` | `index_code, instrument_id, effective_from, effective_to, source_artifact_id`; no overlapping periods |
| `corporate_actions` | `id, instrument_id, action_type, ex_date, record_date, ratio/cash_amount, currency, source, status, announced_at` |
| `daily_bars_raw` | `instrument_id, session_date, provider_id, open, high, low, close, volume, oi, source_ts, ingested_at, payload_hash`; PK `(instrument_id, session_date, provider_id, payload_hash)` |
| `daily_bars_canonical` | `instrument_id, session_date, raw_bar_id, OHLCV/OI, quality_status, canonical_version`; PK `(instrument_id, session_date, canonical_version)` |
| `adjustment_factors` | `instrument_id, session_date, price_factor, volume_factor, action_id, version`; composite PK |
| `trading_calendar` | `exchange, session_date, open_at, close_at, session_type, source_version`; PK |
| `data_quality_events` | `id, severity, check_code, instrument_id, session_date, observed, expected, status, opened_at, resolved_at, resolution` |
| `datasets` | `id, name, purpose, universe_version, start_date, end_date, manifest_uri, sha256, created_at, sealed_at, parent_id` |
| `feature_definitions` / `feature_values` | versioned expression, lookback, availability lag; values keyed by dataset/instrument/as_of/feature_version |
| `target_definitions` / `target_values` | versioned barrier/horizon definition; outcomes keyed by dataset/instrument/signal date |
| `strategy_definitions` | `id, family, version, hypothesis, preregistration_json, status, created_before_evaluation_at, git_sha` |
| `experiments` | `id, strategy_id, dataset_id, config_hash, hypothesis_count, started_at, completed_at, result_uri, decision, reviewer_id` |
| `validation_runs` | `id, experiment_id, partition_type, metrics_json, bootstrap_uri, leakage_checks_json, passed, signed_at` |
| `signals` | `id UUID, strategy_id, instrument_id, as_of, eligible_from, direction, entry_rule_json, invalidation_json, expires_at, regime_id, feature_snapshot_uri, evidence_status, payload_hash, created_at`; append-only |
| `paper_orders` / `paper_fills` | signal link, decision timestamp, modeled order, fill rule/version, price, quantity, costs, reason; append-only |
| `paper_positions` / `paper_trades` | lifecycle, MFE/MAE, gross/net P&L, exit reason; derived reproducibly |
| `strategy_metric_snapshots` | strategy/version/as_of/window, sample count, expectancy, CI, drawdown, calibration, status |
| `market_regimes` | as_of, model_version, label, probabilities, input_snapshot_hash |
| `model_artifacts` | URI, SHA-256, framework, environment lock hash, training dataset, code SHA |
| `audit_events` | actor, action, entity, before_hash, after_hash, reason, occurred_at; append-only |
| `users`, `organizations`, `memberships` | tenant identity and roles |
| `watchlists`, `watchlist_items`, `alert_rules`, `notification_deliveries` | user product state; RLS by organization/user |
| `subscriptions`, `entitlements` | plan state and separately versioned data/content rights |
| `research_reports`, `disclosures`, `approvals`, `corrections`, `complaints` | compliance evidence and maker-checker workflow |

Raw rows are never updated. Corrections create new canonical versions and audit events. Every dataset manifest lists exact rows, code SHA, calendar, membership version, corporate-action version, provider, and hashes.

## 6. Four preregistered strategies

Common convention: calculate after session `t` closes using only information available by the run cutoff; submit a hypothetical market-on-open order for `t+1`; one position per symbol; long-only; NIFTY 200 eligibility above; fixed 10-bps one-way sensitivity plus the current statutory/broker cost model; equal-risk sizing at 50 bps portfolio risk per trade; portfolio cap 10 concurrent positions and 25% per sector. When simultaneous candidates exceed capacity, rank only by the frozen score below and then symbol alphabetically. No parameter tuning after sealed validation is viewed.

### Momentum V1

- **Hypothesis:** medium-horizon relative strength with broad trend and volume confirmation persists for several sessions.
- **Entry at t:** close > SMA50 > SMA200; 20-session return between 8% and 30%; stock 60-session return minus NIFTY 200 return in top universe quintile; volume/20-day median ≥1.25; NIFTY 200 close > SMA100.
- **Rank:** percentile(60-day relative return) + percentile(volume ratio), equal weight.
- **Exit:** first of close < EMA20, 8 sessions, or next-open gap through a 2×ATR14 catastrophe stop. Signal expires if not entered next open.
- **Primary endpoint:** net mean trade return; secondary: expectancy, profit factor, max drawdown, turnover, regime/sector stability.

### Breakout V1

- **Hypothesis:** a fresh high emerging from compressed volatility with volume confirms information diffusion.
- **Entry at t:** close > maximum high of sessions t−55…t−1 by ≥0.25×ATR14; prior 20-day realized volatility below its own trailing 252-day 40th percentile; volume ≥1.5×20-day median; close in top 20% of daily range; NIFTY 200 > SMA100.
- **Rank:** breakout distance/ATR + volume percentile, equal weight.
- **Exit:** close below breakout level, close below EMA20, 10 sessions, or 2×ATR14 catastrophe stop.
- **Primary endpoint:** net expectancy; secondary: 5-day return, MFE/MAE, false-break rate, drawdown.

### Mean Reversion V1

- **Hypothesis:** sharp idiosyncratic selloffs within established liquid uptrends partially revert when the broad market is not stressed.
- **Entry at t:** close > SMA200; 3-day return ≤−6%; RSI2 ≤5; close ≤ lower 20-day Bollinger band (2σ); stock 1-day residual versus NIFTY 200 ≤−2%; India VIX not in its trailing-252-day top decile; no known ex-date on t or t+1.
- **Rank:** most negative volatility-scaled 3-day residual first.
- **Exit:** close ≥ EMA10, 5 sessions, or close falls another 1.5×ATR14 from entry.
- **Primary endpoint:** net expectancy; secondary: recovery probability, tail loss, gap sensitivity, performance in market drawdowns.

### Relative Strength V1

- **Hypothesis:** leaders within leading sectors outperform when both stock and sector trends agree.
- **Entry at t:** stock > SMA100; sector index > SMA100; stock 60-day excess return vs sector in top sector quintile; sector 60-day excess return vs NIFTY 200 in top three sectors; 20-day traded-value filter; NIFTY 200 not below SMA200.
- **Rank:** 60% stock-vs-sector percentile + 40% sector-vs-market percentile.
- **Exit:** stock relative-strength percentile falls below 50, close < EMA20, or 10 sessions.
- **Primary endpoint:** net excess return versus NIFTY 200 over matched holding period; secondary: net trade expectancy, sector concentration, turnover, drawdown.

All four are hypotheses, not approved strategies. Before execution, serialize these specifications, cost assumptions, candidate count (four families), endpoints, pass rules, and code SHA into the experiment registry and timestamp the hash.

## 7. Backtest and validation protocol

### Data partitions

Use only periods for which point-in-time membership and corporate actions pass audit. Provisional boundaries: discovery 1 Jan 2012–31 Dec 2019; internal rolling walk-forward 2020–2022; sealed validation 2023–2024; final holdout 2025–30 Jun 2026. The final dates are frozen before results are calculated. Forward paper evidence begins after the strategy and production signal code are frozen; it never includes simulated history.

### Mechanics

- Event-driven daily simulator with exchange calendar, next-session entry, gaps, suspension, circuits, partial/no-fill rules, delistings, and corporate actions.
- Survivorship-free membership; lag all fundamentals/events by actual availability time. Features declare `available_at`.
- Costs are versioned by date: brokerage, STT, exchange/clearing charges, GST, stamp duty, spread/slippage. Report base, optimistic, and 2× slippage stress; pass on base and remain non-catastrophic under stress.
- Compare against buy-and-hold NIFTY 200, random eligible entries matched by date/holding duration, and a simple trend baseline.
- Purge/embargo overlapping labels in supervised work; never use shuffled splits.

### Statistical controls and pass gates

The family of four V1 hypotheses is declared in advance. Primary tests use one-sided evidence only when direction was preregistered; report two-sided sensitivity. Control FDR across the four primary endpoints with Benjamini–Hochberg at 10%; report unadjusted and adjusted values. Use stationary/block bootstrap confidence intervals clustered by time; additionally cluster results by symbol and inspect dependence.

A candidate advances from internal walk-forward only if: ≥150 trades and ≥30 trades in at least three distinct calendar years; net expectancy >0; 95% bootstrap lower bound not materially below zero (economic floor preregistered as −5 bps/trade); profit factor ≥1.15; stress-cost expectancy ≥0; no single year, symbol, or sector contributes >35% of total net P&L; and parameter-neighborhood results are not a narrow spike.

Sealed validation passes only if the frozen candidate has net expectancy >0, profit factor ≥1.10, FDR-adjusted q≤0.10 for the family primary test, drawdown within preregistered risk budget, and no leakage/data critical finding. Holdout is opened once, by an independent approver, and requires positive net expectancy plus no material risk/control breach. A failed validation/holdout version is rejected; any redesign becomes a new version and new sealed data.

### Forward verification

Signals are written before the eligible entry and cryptographically hashed. Corrections never overwrite. “Forward Verified” requires at minimum 100 closed trades, 12 months, coverage of at least three regime labels and four sectors, positive net expectancy, 95% lower confidence bound ≥0 under the live fill/cost policy, profit factor ≥1.10, drawdown within limit, calibration/implementation audits passed, and no unresolved critical data incident. Until all are true, label “Forward Testing” and show sample size. Monitor rolling 50-trade expectancy, drawdown, feature drift, regime mix, and live-vs-backtest slippage. Two consecutive material breaches trigger Degraded; a risk-limit or integrity breach triggers immediate Pause.

## 8. Technical architecture

```text
Upstox / licensed feed ─► ingest workers ─► raw object store + raw DB
                                  │
                                  ├─► quality/reconciliation ─► canonical bars
                                  │                              │
                                  │                    feature/target jobs
                                  │                              │
                                  └─► live/EOD stream ─► frozen strategies
                                                               │
                                    append-only signals/paper ledger
                                                               │
Next.js web ◄─ API/BFF ◄─ read models / entitlements / approvals / audit
                         └─ notifications queue
```

- **Web:** Next.js/TypeScript/Tailwind on Vercel; server components for read-heavy pages; no secrets in client bundles.
- **API/BFF:** Next.js APIs for user/product reads; Python FastAPI research service for controlled internal jobs, never public arbitrary backtests.
- **Data:** Supabase Postgres with RLS; S3-compatible immutable object storage for raw payloads, Parquet, manifests, artifacts, and reports.
- **Workers:** Python containers on a persistent worker platform (AWS ECS/Fargate or a simpler Render/Railway pilot). Redis-backed queue only when job volume warrants it.
- **Scheduling:** managed cron triggers idempotent jobs; exchange-calendar-aware state machine. Streaming runs in a persistent container, not Vercel Functions.
- **Paper engine:** append-only deterministic state machine consuming signals and canonical prices; fill/cost policy version pinned to each order.
- **Notifications:** outbox table → worker → email/web push first; retries, dedupe key, delivery audit. No WhatsApp/Telegram until approval and consent design.
- **Observability:** structured logs, traces, job heartbeats, provider lag, bar completeness, reconciliation deltas, queue age, notification failures, and SLO alerts.
- **Security:** environment-separated projects/accounts, least privilege, RLS tests, secret manager, key rotation, MFA, encrypted backups, signed artifact URLs, rate limits, dependency/SAST scans, audit log, restore drills, and incident runbooks.

Service SLOs for beta: EOD pipeline complete by 18:00 IST on 99% of trading days; zero silent data rewrites; customer API 99.9% availability; critical integrity incident automatically suppresses affected signals.

## 9. MVP UX

### Primary journey

Landing page → methodology/transparency → free account → market regime dashboard → limited setup card → evidence detail → watchlist/alert → weekly outcome review → paid interest/waitlist. A setup card leads with status and uncertainty, not a green “Buy” button.

### Pages

1. **Landing:** “Backtested isn’t verified”; live methodology, evidence ladder, rejected-strategy example, no fabricated metrics.
2. **Today:** data freshness, regime, breadth, sector leaders, eligible setups grouped by evidence status.
3. **Setup detail:** timestamp, rules met, horizon, invalidation, delayed/current-data label, sample count, partitioned results, net-cost assumptions, regime fit, risks, methodology/version, disclosure.
4. **Strategy evidence:** preregistration, discovery/validation/holdout/forward partitions, equity/drawdown, year/sector/regime tables, failures and changes.
5. **Stock:** price/trend/volume/relative-strength analytics and active/expired setups; no personalized action.
6. **Watchlist/alerts:** user-selected symbols and factual setup-status changes.
7. **Paper record:** immutable platform-level signals, open/closed paper outcomes, correction log; no user claim of achieved return.
8. **Trust center:** data sources/rights, cost model, status definitions, AI use, conflicts, corrections, incidents, compliance details.
9. **Internal admin:** pipeline health, quarantines, experiment registry, approvals, entitlements, complaints, and audit exports.

Accessibility: WCAG 2.2 AA target, keyboard navigation, non-color status cues, plain-language risk summaries, IST timestamps, responsive tables, and “data unavailable” instead of inferred values.

## 10. Monetization experiments

Do not accept payment for research/signals until the subscription gate in §14 passes. Before that, use a free waitlist and willingness-to-pay interviews.

| Plan | Proposed boundary | Price experiment |
|---|---|---|
| Free | Regime/breadth, education, delayed limited setups, selected evidence reports | ₹0 |
| Pro | Full approved swing screener, watchlists, EOD alerts, full strategy evidence, exports within data rights | A/B ₹799 vs ₹1,199/month; annual 10 months |
| Trader | Do not launch in V1; later adds broader engines, advanced risk/portfolio analytics only after IA review | Van Westendorp/conjoint around ₹1,999 vs ₹2,499 |

Avoid artificial urgency, performance-based pricing, and a paywall that hides risk evidence. Charge for workflow, breadth, timeliness, and auditability—not promised profit.

## 11. Go-to-market

**Positioning:** “Most platforms show a backtest. We show whether a strategy survived validation and what happened after it went live on paper.”

**Lead magnet:** a weekly “NIFTY Regime & Strategy Reality Report”: regime/breadth, one setup anatomy, one rejected hypothesis, and a forward-vs-backtest audit. It must remain educational until the compliance gate permits recommendations.

**Content pillars:** leakage/survivorship, expectancy vs win rate, cost/slippage, regime dependence, rejected strategies, and paper-vs-live reality. Publish methodology before results. SEO starts with high-intent educational/tool pages—backtest validation, expectancy calculator, NIFTY regime methodology, swing-screening methodology—then security pages only when licensing and RA review permit them.

**Beta acquisition:** 20–30 research-literate traders from interviews/communities, then 100 invite-only users. Recruit for comprehension, not promotion. Weekly interviews measure whether users understand evidence status, uncertainty, and invalidation.

**Paid ads:** only after legal/ad approval. Test problem-first creative (“Would your strategy survive a forward test?”) to the report/waitlist. No profit imagery, targets, testimonials about returns, or retargeting based on sensitive financial behavior without review. Stop any campaign with misleading comments/creator claims that cannot be moderated.

## 12. Controlled development roadmap

| Batch | Deliverable | Exit evidence |
|---|---|---|
| 0A | Counsel memo and product perimeter | Written RA/IA, ads, data, privacy, and execution decisions |
| 0B | Provider/licensing diligence | Written permitted-use matrix and commercial quotes |
| 1 | Repo, CI, environments, schema foundations | Migrations, RLS tests, threat model, restore test |
| 2 | Upstox adapter + instrument/calendar master | Contract tests, rate-limit/retry evidence, mapping report |
| 3 | Raw/canonical daily ingestion | Reconciliation, gap/duplicate/corporate-action reports |
| 4 | Dataset manifests and point-in-time universe | Deterministic rebuild with matching SHA-256 |
| 5 | Feature/target library | Golden fixtures, availability/leakage tests |
| 6 | Event-driven backtester + costs | Independent hand-calculated cases and benchmark parity |
| 7 | Experiment registry, sealing, audit | Mutation blocked; approver-open workflow tested |
| 8 | Four preregistrations implemented | Code-to-spec review; no results opened prematurely |
| 9 | Walk-forward/discovery | Reproducible report including rejected models |
| 10 | Validation/holdout | Independent sign-off and immutable decisions |
| 11 | EOD signal + paper engine | Pre-outcome timestamps, replay determinism, fill audit |
| 12 | Internal dashboard | Operators can detect/quarantine incidents |
| 13 | Customer read-only beta | UX/accessibility/security/compliance approval |
| 14 | Entitlements, billing, notifications | Licensing, RA ops, refund/support, and audit readiness |
| 15 | Paid beta | Controlled cohort, no unsupported claims, incident drills |

Each batch gets its own Codex prompt: inspect scope, named files, invariants, exclusions, migrations, tests, evidence, and stop condition. No batch may silently widen product or regulatory scope.

## 13. Risk register

| Risk | Early indicator | Mitigation / owner |
|---|---|---|
| Broker data rights do not cover SaaS | provider will not answer in writing | licensed feed/authorized vendor; Product + Legal |
| RA/IA misclassification | product adds ranks, targets, personalization | counsel review and feature kill switch; Compliance |
| Survivorship/corporate-action bias | implausible old-universe performance | point-in-time membership, raw/adjusted lineage; Data |
| Look-ahead leakage | feature timestamp after decision cutoff | availability contracts and automated leakage tests; Quant QA |
| Multiple testing/overfit | many undocumented variants | registry, hypothesis budget, FDR, sealed sets; Validation |
| Paper/live execution gap | forward slippage exceeds stress | conservative fills, capacity model, no execution claim; Risk |
| Strategy decay/regime shift | rolling expectancy/drift breach | degrade/pause policy; Performance Audit |
| Provider outage/schema change | freshness/decoder failures | contract monitoring, replay buffer, second adapter; Platform |
| Audit evidence mutation | hash mismatch | immutable store, signed manifests, access separation; Security |
| Tenant/secret exposure | RLS or scan failure | least privilege, RLS suite, secret manager, incident plan |
| Misleading growth/creator content | return claims or cherry-picking | preapproval, creator clauses, monitoring, takedown; Growth/Compliance |
| Weak willingness to pay | low repeated use/interview intent | delay UI spend, test workflow utility; Product |
| Sample scarcity | few independent trades/regimes | remain Forward Testing; expand time, not parameter search |
| Vendor concentration | unreconciled provider anomalies | second-source audit and portable adapter; Data |
| Cost overrun | storage/egress/job spike | daily-only V1, budgets, partitioning, lifecycle policies; Engineering |

## 14. Decision gates

### Before building the paid product

All must be true: written product-perimeter counsel memo; written provider/exchange rights and cost; canonical daily pipeline meets SLO for 60 trading days; backtester and sealing independently audited; at least one frozen strategy passes sealed validation and holdout (it may still be labeled Forward Testing); beta interviews demonstrate evidence comprehension and willingness to pay; security threat model and cost model approved.

### Before publishing any security-specific signal

All must be true: RA/IA classification resolved and required registration/RAASB operations live; research report exists; data display/derived-data rights written; maker-checker approval; timestamped append-only signal generation; disclosures/conflicts/AI use current; cost/risk/invalidation shown; complaint/correction/incident processes tested; affected-data kill switch operational. Otherwise publish education and aggregate regime analytics only.

### Before accepting subscriptions

All signal-publication conditions plus: compliant client onboarding/KYC/terms/fees/refunds where applicable; billing, tax, grievance, privacy, retention, audit, and support workflows tested; advertisement/funnel/creator review complete; no fabricated evidence; customer entitlement and market-data reporting ready; at least 90 days of incident-free closed beta.

### Before claiming “Forward Verified”

The exact §7 forward threshold must be met by immutable, pre-outcome signals using the production strategy and fill policy. Display start/end dates, trade count, costs, confidence interval, drawdown, corrections, and distinction from customer-achievable performance. Compliance and independent validation must sign the status change.

### Before considering broker execution

Require a separate board decision after: demonstrable user demand; counsel review of current SEBI/exchange/broker retail-algo rules; broker partner agreement; order-management controls, suitability/perimeter decision, consent, kill switches, limits, reconciliation, cyber audit, disaster recovery, sandbox and staged certification; at least 12 additional months of stable forward evidence; and a clear liability/support model. Execution is a new product, not a V1 feature flag.

## Immediate next actions

1. Commission two written memos: regulatory perimeter and market-data licensing.
2. Send identical use-case questionnaires to Upstox, Zerodha, Dhan, and NSE Data.
3. Freeze this blueprint’s V1 universe and four hypotheses as decision record DR-001; changes require reasons and a new version.
4. Run the read-only Upstox data spike and second-source reconciliation.
5. Only after gates 1–4, draft Batch 1’s implementation prompt and repository plan.

The core business constraint is deliberate: **evidence can delay the product; the product cannot dilute the evidence.**
