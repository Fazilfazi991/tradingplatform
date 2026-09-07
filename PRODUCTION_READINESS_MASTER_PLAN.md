# VERIFIED EDGE Production Readiness Master Plan

Status date: 2026-09-08  
Audit baseline: `main` at `1a067f0937abb73cf432a39eda05548f3ec1c3b5`  
Last reconciled implementation: `main` at `0398554c9dabace63417aec991978a0885b6f70b`  
Scope: public Track A platform, promotion readiness, and separately gated Track B predictive research  
Current overall decision: **PRODUCTION / PROMOTION BLOCKED**  
Track B: **HOLDOUT VALIDATED — FORWARD REQUIRED**

This is the controlling plan for the production-readiness mission. It was created after a full repository, product, runtime, security, data-rights, research, and deployment audit. Work must follow the priority and release gates below. Passing a code check alone never implies production readiness.

## 1. Audited baseline

### What is already credible

- Prediction Engine V1 has a sealed dataset hash, causal feature controls, baselines, purged/embargoed validation, calibration, abstention and OOD controls. Its holdout result passed, while its authoritative report correctly records that forward predictions have not started.
- Real-market manifests preserve provider, collection mode, dataset hash, warnings, provenance, and `public_redistribution: NOT_APPROVED`.
- Public prediction emission is blocked by the research-core destination policy.
- OpenAI structured output, evidence-reference containment, sanitized errors, cost telemetry, unsupported-number quarantine, and prompt-injection boundaries exist.
- RBI/SEBI collectors enforce HTTPS and exact hosts, disable redirects, restrict content type/size, and reject credentialed, nonstandard-port, and private-literal URLs.
- A genuine historical 24-hour qualifying soak artifact exists. It demonstrates a completed experiment, not current continuous operations.
- The frontend has a coherent visual foundation, explicit synthetic/demo banners, cautious abstention language, responsive rules, and reduced-motion handling.
- At audit time: frontend build, typecheck, and lint passed; npm production audit found no known vulnerability; 88 focused offline backend tests passed; tracked-tree secret scan found no high-confidence secret.

### Current operating truth

- No intelligence worker or market-data EOD worker is running.
- The intelligence database contains schedules but zero executions, raw artifacts, events, or incidents.
- Market-data execution operations are disabled and no EOD scheduler consumes the configuration.
- The normal intelligence worker does not invoke the live LLM/forensic semantic pipeline.
- Research Operator has historical pilot ledger entries but is not a supervised autonomous process.
- Internal/admin pages and `/api/research-desk` are publicly reachable without authentication.
- Public redistribution rights for Upstox/provider data are not approved.
- There is no repository CI workflow, explicit hosting configuration, staging/production contract, deployment runbook, rollback runbook, or post-deploy smoke gate.
- A Next-generated change to `apps/web/next-env.d.ts` was present during the audit and must be normalized before the clean-tree gate is evaluated.

## 2. Route and surface classification

| Surface | Intended class | Launch disposition |
|---|---|---|
| `/` | PUBLIC | Rebuild as public product homepage |
| `/fusion` | PUBLIC / DEMO | Keep public with evidence/abstention language |
| `/models` | PUBLIC METHODOLOGY | Reconcile status vocabulary before release |
| `/predictions` | DEMO / EXPERIMENTAL | Public only if demo state dominates and no live implication exists |
| `/stocks/[symbol]` | DEMO / EXPERIMENTAL | Validate supported symbols; unknown symbols must 404 |
| `/sectors`, `/intelligence`, `/historical` | DEMO / EDUCATIONAL | Preserve only with explicit synthetic provenance |
| `/research`, `/research/prediction-v1` | INTERNAL RESEARCH | Authenticate and exclude from indexing/public navigation |
| `/research-desk`, `/data-health`, `/settings` | INTERNAL ADMIN | Authenticate and exclude from indexing/public navigation |
| `/api/research-desk` | INTERNAL API | Deny by default; authenticate/authorize and bound resource use |

No live or licensed raw provider payload may be serialized to a public route merely because that route is visually labelled internal or demo.

## 3. Explicit release gates

Gate states are `PASS`, `FAIL`, or `EXTERNAL`. A track releases only when every required gate is `PASS`; an external dependency remains an explicit blocker rather than being silently waived.

### Engineering gate — FAIL

- [ ] Clean main branch and reproducible dependency installation.
- [ ] CI runs backend tests, Ruff, Mypy, frontend lint/typecheck/build, secret scan, dependency audit, link checks, and required security tests.
- [ ] No critical Python/TypeScript errors, console errors, broken links, or dead routes.
- [ ] Database migrations/state initialization and reproducibility documented and tested.
- [ ] Supervised schedulers/workers stable; missing handlers fail closed; timeouts are enforceable; retries are bounded.
- [ ] Provider errors and runtime failures create actionable incidents.
- [ ] Health monitoring and post-deploy verification work.

### Data gate — FAIL / EXTERNAL

- [ ] Upstox authentication health verified without exposing credentials.
- [ ] Current-universe mapping and point-in-time membership validated.
- [ ] Freshness enforcement, stale blocking, deterministic manifests, provenance, and corporate-action warnings verified end to end.
- [ ] Live/demo separation enforced in serializers and tests.
- [ ] Data health visible to authorized operators.
- [ ] Public redistribution/derived-data rights approved or public output limited to independently safe content. **EXTERNAL**

### Intelligence gate — FAIL

- [ ] RBI/SEBI collection runs under the supervised platform scheduler.
- [ ] Luna structured-analysis runtime is wired into the normal worker under frozen prompt/model/schema controls.
- [ ] Hallucination quarantine, provider cost ledger, source provenance, Research Desk, and strict Fusion abstention operate continuously.
- [ ] No unverified input is silently promoted; source staleness and collection failures open and resolve incidents.

### Public safety gate — FAIL / EXTERNAL

- [ ] No fixture/live mixing or fabricated metrics.
- [ ] Claims never exceed `HOLDOUT VALIDATED — FORWARD REQUIRED`.
- [ ] No BUY/SELL, target price, return probability, recommendation, or misleading confidence wording.
- [ ] Public-data rights are enforced in code and verified by negative tests.
- [ ] Risk, privacy, terms, data-source, methodology, and validation disclosures match the actual perimeter. Final legal/compliance wording approval is **EXTERNAL**.

### Product gate — FAIL

- [ ] Public homepage explains the product, evidence process, limitations, and primary journey in plain language.
- [ ] Navigation cleanly separates public and authenticated internal areas.
- [ ] Desktop and mobile layouts pass screenshot QA at 1920, 1440, 1366, 1024, 430, 390, and 375 px.
- [ ] Every data surface has honest empty, loading, stale, offline, and error states; custom 404 exists.
- [ ] Metadata, accessibility, performance budgets, sitemap/robots, and canonical behavior pass.

### Operations gate — FAIL

- [ ] Authorized health dashboard covers provider, collectors, spend, scheduler, sources, incidents, and last-success timestamps.
- [ ] Incident taxonomy, thresholds, deduplication, resolution, escalation, and runbooks operate.
- [ ] Deployment, rollback, backup, restore, retention, and archive policies are tested.
- [ ] Staging and production are separate, documented, and smoke-tested.
- [ ] Codex maintenance routines do not substitute for a platform-owned scheduler.

## 4. P0 — blockers that must be resolved before Track A production

### P0.1 Public/internal security boundary

1. Introduce an explicit route policy with `PUBLIC`, `DEMO`, `INTERNAL_RESEARCH`, and `INTERNAL_ADMIN` classifications.
2. Remove internal links from the public shell and create a separate authenticated internal shell.
3. Protect internal routes and APIs with server-side authentication and authorization; deny by default when configuration is absent.
4. Make `/api/research-desk` bounded, cached, rate-limited, non-indexable, and unable to leak local paths, hashes, candidate details, credentials, or operational internals to unauthorized callers.
5. Add route-policy, unauthenticated-denial, authorization, indexing, and public-payload tests.

Acceptance: anonymous requests cannot discover or retrieve internal pages/API payloads; public bundles contain no internal study data; authenticated operator access is logged without sensitive data.

### P0.2 Public-safe data contract

1. Define and version a narrow public serializer that accepts only approved synthetic/demo or rights-cleared derived fields.
2. Enforce provenance, content class, rights state, freshness, and validation state before serialization.
3. Reject `NOT_APPROVED`, stale, fixture/live-mixed, unverified, or internal-only data at the boundary.
4. Add adversarial tests proving raw Upstox payloads, internal source content, research hashes, and hidden fixture data cannot cross it.

Acceptance: public delivery is technically impossible unless the record is explicitly public-safe; approval is machine-verifiable, not a UI label.

### P0.3 Authoritative state vocabulary

Create one shared registry for lifecycle and evidence labels. Minimum canonical states:

- `DEMO — SYNTHETIC DATA`
- `ENGINEERING_FIXTURE`
- `INTERNAL_LIVE`
- `PARTIAL_LIVE — ABSTAIN`
- `HOLDOUT VALIDATED — FORWARD REQUIRED`
- `FORWARD VALIDATION IN PROGRESS`
- `PREDICTIVELY VALIDATED`
- `INSUFFICIENT_EVIDENCE`
- `UNKNOWN`
- `STALE`
- `UNAVAILABLE`

Replace contradictory model, research, prediction, and data-health strings. Never display `FORWARD VALIDATION IN PROGRESS` until the immutable registry contains issued forward predictions.

### P0.4 Supervised data/intelligence operations

1. Build one platform-owned service entrypoint for market collection, RBI/SEBI collection, deterministic processing, selective LLM analysis, snapshots, Fusion abstention, archival, and reports.
2. Replace silent `NOOP` handlers with startup/configuration failures.
3. Implement enforceable handler cancellation/timeouts, bounded retry/backoff, circuit behavior, checkpoints, idempotency, and leases.
4. Persist source health and create/resolve the required incident types on provider, collector, schema, staleness, scheduler, cost, quarantine, and snapshot failures.
5. Wire Luna through the normal scheduler with the existing budget, cache, schema, evidence, and quarantine policies. Missing fallback credentials must remain non-fatal.
6. Keep unavailable specialist engines honestly `ENGINEERING_ONLY`, `INSUFFICIENT`, or `ABSTAIN`.
7. Provide service install/start/stop/status procedures and prove restart/recovery behavior.

Acceptance: a real bounded soak under the production-shaped service shows scheduled executions, artifacts, cost/cache telemetry, incidents, recovery, and immutable reports without a human or Codex acting as scheduler.

### P0.5 Market-data EOD and forward-paper runtime

1. Implement and activate the disabled EOD workflow only in approved internal mode.
2. Add immutable forward-prediction issuance before outcomes, dataset/model/prompt/config hashes, issued-at timestamps, eligibility/abstention reasons, and append-only storage.
3. Add delayed outcome resolution that cannot rewrite predictions, plus coverage, calibration, error, regime, drift, and abstention reporting.
4. Separate prediction issuance, outcome resolution, and report generation into independently recoverable jobs.
5. Do not publish predictive outputs during this mission.

Acceptance: forward observations accumulate prospectively from real timestamps; no backfill can masquerade as a forward prediction; Track B remains gated until elapsed time and sample sufficiency are met.

### P0.6 CI/CD and deployment safety

1. Add CI with pinned/reproducible Python dependencies and the complete engineering/security test matrix.
2. Resolve hosting root/runtime ambiguity explicitly for the Next application; never rely on provider auto-detection in this mixed Python/Next repository.
3. Add environment validation, staging/production separation, protected production deploys, migration/state initialization, rollback, and post-deploy smoke tests.
4. Add security headers (CSP, frame, referrer, permissions, content-type, transport in production) and automated verification.
5. Add dependency and secret scanning; document branch protection and required checks.

Acceptance: a clean commit promotes through CI to staging, passes full smoke/security/data-boundary checks, and can be rolled back without data loss. Production remains blocked until external hosting/domain configuration is available.

### P0.7 Legal, compliance, and claims perimeter

Create draft Terms, Privacy, Risk Disclosure, Data Sources, Methodology, Prediction Validation Status, and Contact surfaces. State clearly that the product is informational research, experimental where applicable, not investment advice, and does not provide execution. Do not invent permissions or imply regulatory avoidance through wording.

Acceptance: routes exist, match actual behavior and data rights, and receive owner/legal approval before public production. Until approval, mark them draft and keep the production gate failed.

## 5. P1 — required before promotion

### Public information architecture and homepage

- Replace the dashboard-first home with a plain-language launch page: proposition, how evidence is assembled, seven engine overview, validation status, limitations, trust/data provenance, FAQ, and a primary CTA to explore a demo stock or methodology.
- Add coherent public navigation and footer: Product, Methodology, Data Sources, Validation Status, About, FAQ, Risk, Privacy, Terms, Contact.
- Explain differentiation through verification, contradiction handling, abstention, provenance, and uncertainty—not unsupported performance claims.
- Keep implementation secrets and internal operational detail out of public copy.

### Stock and prediction experience

- Validate the stock universe; unknown symbols return a genuine 404 instead of RELIANCE-like fixtures.
- Make research/experimental status more visually prominent than direction or range.
- Replace inert controls with functional filters or remove them; add no-result states.
- Show evidence, provenance, freshness, data class, validation state, uncertainty, contradictions, and abstention reasons consistently.
- Keep fixture/demo mode unmistakable at page, card, chart, and export level.

### Reliability, accessibility, and responsive QA

- Add route/global error boundaries, loading states, offline/network failure, stale data, insufficient history, unavailable provider, and abstention states.
- Add a skip link, keyboard/focus verification, semantic chart/figure/table alternatives, accessible active filters, labels, contrast checks, and reduced-motion validation.
- Execute screenshot-driven QA at every required viewport and preserve approved desktop/mobile launch captures.
- Remove hard-coded misleading timestamps; show explicit snapshot times and stale states.

### SEO, indexing, performance, and brand

- Add route metadata, canonical strategy, OpenGraph/Twitter assets, manifest, favicon family, structured data where accurate, sitemap, and robots rules.
- Index only approved public information pages. Never index internal routes, admin surfaces, research ledgers, data health, or settings.
- Define search intent and content around evidence-based market research, uncertainty, validation, and methodology; avoid fabricated or performance-seeking claims.
- Establish performance budgets and measure production builds for bundle size, LCP/INP/CLS, image/font loading, route payloads, and API latency.
- Standardize naming, typography, tone, badges, colors, and evidence terminology.

### Monitoring, incidents, and maintenance

- Implement provider, collector, freshness, scheduler, cost, schema, quarantine, snapshot, backup, and deployment monitoring.
- Version thresholds; deduplicate and resolve incidents; document severity, ownership, response, rollback, and postmortem flow.
- Add privacy-conscious analytics only after owner approval. If enabled, track CTA, search, demo exploration, methodology, validation, and waitlist/contact funnels without sensitive research data.
- Define safe Codex maintenance routines and periodic audits; scheduled Codex work may inspect/report but must not be the production runtime.

### Promotion package

- Produce approved desktop/mobile screenshots, short and long product descriptions, founder talking points, launch post, walkthrough script, FAQ answers, trust/validation copy, and a claims ledger mapping each public statement to evidence.
- Do not publish or schedule promotion until the promotion gate is explicitly `PASS`.

## 6. P2 — post-launch improvements

- Conditional RSS fetches using ETag/Last-Modified and stronger DNS/private-address verification.
- Provider-neutral persistent semantic cache shared by generic and forensic runtimes.
- Archive rebuild versioning, richer incident lifecycle, and off-host retention analytics.
- Full product search/autocomplete and accessible chart exploration.
- Further server/client component splitting and reusable responsive layout primitives.
- Deeper recovery chaos tests, capacity tests, and long-window SLO/error-budget reporting.
- Additional promotion formats and content only after approved claims and observed user needs.

## 7. External blockers

These require owner, provider, legal, or hosting authority and cannot be manufactured in code:

1. Written Upstox/provider public redistribution and derived/commercial data rights.
2. Point-in-time NIFTY 200 membership/licensing and corporate-action adjustment confirmation.
3. Independent market-data source/reconciliation agreement if required by release policy.
4. Legal/compliance approval of product perimeter, Terms, Privacy, Risk Disclosure, public security-specific wording, and any future paid research.
5. Canonical production domain, hosting project, production/staging credentials, and environment separation.
6. Git hosting branch protection, required checks, and repository secret-scanning configuration.
7. Privacy/analytics/cookie decision and any required consent mechanism.
8. Approval of public positioning, demo-forecast discoverability, launch claims, and promotion publication.
9. Credentials/contracts and rights for currently inactive Fundamental, Flow/Derivatives, or broader macro sources.
10. Real elapsed forward-validation time and a sufficient immutable prospective sample.

All external items must be recorded in `EXTERNAL_BLOCKERS.md`; owner decisions only belong in `OWNER_ACTIONS.md`.

## 8. Delivery sequence

Work should be executed in independently reviewable slices, with no unnecessary rewrite of components that already pass their acceptance criteria.

1. **Release control foundation:** route registry, state vocabulary, public-data contract, gate manifest, external/owner registers.
2. **Security boundary:** public/internal shells, authentication/authorization, API containment, noindex and security tests.
3. **Operations foundation:** supervised worker, real handler wiring, incidents, timeouts/retries/checkpoints, health contract.
4. **Forward-paper foundation:** immutable issue/resolve/report pipeline and scheduler integration.
5. **Public product:** public IA, homepage, methodology/data/legal drafts, stock/prediction honesty, errors/404/accessibility.
6. **Deployment foundation:** CI, dependency lock/audit, environment validation, hosting config, runbooks, staging.
7. **QA and promotion:** responsive/visual/browser/performance/link/SEO checks, smoke tests, claims audit, approved promotion assets.
8. **Production decision:** evaluate Track A and Promotion gates independently from Track B; deploy only if every applicable non-external gate passes and required external approvals are documented.

Parallel work must use isolated `codex/` worktrees/branches with one owner per slice. Integration happens only after tests and conflict review. Existing research worktrees must not be deleted or repurposed without confirmation.

## 9. Required evidence and reports

The following are release artifacts, not aspirational prose:

- `PROMOTION_READINESS_REPORT.md`: public route inventory, claims ledger, responsive screenshots, accessibility, links, SEO, performance, legal approval state, promotion assets, and explicit pass/fail.
- `PREDICTIVE_FEATURE_READINESS_REPORT.md`: immutable forward sample, coverage, accuracy/error, calibration, abstention, OOD/drift, regimes, failures, and separate Track B verdict.
- `EXTERNAL_BLOCKERS.md`: authority, evidence needed, owner, impact, safe interim behavior, and resolution state for every external dependency.
- `OWNER_ACTIONS.md`: only concrete owner decisions/actions, prioritized and linked to the relevant gate.
- Production/deployment runbooks and a smoke report containing commit, environment, checks, timestamp, and rollback reference.
- Final master report with starting/final SHA, tests, deployment evidence, Track A verdict, promotion verdict, Track B verdict, remaining external blockers, and exactly one overall acceptance decision.

## 10. Current track decisions

| Track | Current state | Reason |
|---|---|---|
| Track A — public informational platform | **BLOCKED** | Code-level public/internal separation, public serializer, CI, local QA, environment validation, recovery tooling, and worker heartbeat are implemented; hosting/domain, production-shaped service supervision, legal/data-rights approval, and deployed smoke evidence remain open |
| Promotion | **BLOCKED** | Track A remains blocked; legal/claims approval, canonical production evidence, final launch captures, and publication approval are absent |
| Track B — predictive feature | **HOLDOUT VALIDATED — FORWARD REQUIRED** | Sealed holdout passed and an append-only forward ledger exists, but no frozen deployable model issuer/outcome resolver or sufficient elapsed prospective evidence exists |

## 11. Reconciled implementation evidence

- Public/internal route classification, fail-closed Basic authentication, safe serialization, anonymous denial, no-store/noindex, and negative payload tests are implemented.
- Public information architecture, draft policy pages, honest demo state, unknown-stock 404, responsive repair, keyboard skip navigation, and restricted sitemap/robots are implemented and locally verified.
- GitHub CI uses pinned actions and reproducible Python/Node dependency contracts; backend, frontend, audit, secret-scan, build, and production smoke jobs passed on hosted Actions.
- Release environment validation fails closed by deployment profile and never prints values. A canonical domain, separate hosted environments, and production credentials are still external.
- The intelligence worker rejects missing handlers, records sanitized incidents, uses bounded source retries/checkpoints/leases, and now persists start/heartbeat/stop state. A local start/status/stop rehearsal passed; production host supervision and a new production-shaped soak remain unproved.
- SQLite online backup, integrity/hash manifest verification, traversal-safe restore verification, and non-overwriting restore tests are implemented. Managed production retention, off-host encryption, RPO/RTO, and restore evidence remain external to the local SQLite tool.
- The forward-validation ledger is append-only and causal, but automatic issuance and delayed outcome resolution are intentionally not activated.

The next resolvable work is operational/deployment evidence and final release documentation. Prediction research gates, research mode, brokerage connectivity, BUY/SELL outputs, target prices, and public predictive activation remain unchanged.
