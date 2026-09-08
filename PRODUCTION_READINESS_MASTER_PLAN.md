# VERIFIED EDGE Production Readiness Master Plan

Status date: 2026-09-08  
Audit baseline: `main` at `1a067f0937abb73cf432a39eda05548f3ec1c3b5`  
Last reconciled implementation: see the current Git commit reported by `scripts/audit_release_gates.py`
Scope: public Track A platform, promotion readiness, and separately gated Track B predictive research  
Current overall decision: **PRODUCTION / PROMOTION BLOCKED**  
Track B: **HOLDOUT VALIDATED — FORWARD REQUIRED**

This is the controlling plan for the production-readiness mission. It was created after a full repository, product, runtime, security, data-rights, research, and deployment audit. Work must follow the priority and release gates below. Passing a code check alone never implies production readiness.

The machine-readable authority for current gate states is `config/release-gates.json`. Run
`python scripts/audit_release_gates.py` to validate its evidence references, external-blocker
references, Git state, and independent Track A, promotion, and prediction decisions. The validator
fails closed when evidence is missing or the manifest is inconsistent.

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

- No production intelligence worker is installed or running. The local worker rehearsal is stopped.
- Historical local operations/soak databases contain real executions and evidence, but they do not
  prove current production continuity.
- Market-data EOD and provider-health jobs are owned by the platform scheduler. EOD execution remains
  deliberately disabled; the read-only health canary passed a bounded check on 8 September 2026.
- The normal intelligence worker invokes the configured semantic pipeline under explicit activation,
  budget, schema, cache, grounding, and quarantine controls.
- Research Operator has historical pilot ledger entries but is not installed as a supervised
  production process.
- Internal/admin pages and `/api/research-desk` deny anonymous access, are no-store/noindex, and log
  sanitized authorization outcomes.
- Public redistribution rights for Upstox/provider data are not approved.
- Reproducible GitHub CI, explicit Vercel root configuration, environment contracts, deployment and
  rollback runbooks, a hash-sealed deployment-evidence validator, and post-build smoke gates exist.
  No canonical staging/production deployment evidence has been supplied.
- The branch is clean and synchronized at the commit reported by the machine-readable gate audit.

## 2. Route and surface classification

| Surface | Intended class | Launch disposition |
|---|---|---|
| `/` | PUBLIC | Public launch page implemented; final deployment/legal gates remain |
| `/fusion` | PUBLIC / DEMO | Synthetic, abstaining, and noindex |
| `/models` | PUBLIC METHODOLOGY | Canonical status vocabulary applied |
| `/predictions` | DEMO / EXPERIMENTAL | Synthetic state dominates; noindex and no live implication |
| `/stocks/[symbol]` | DEMO / EXPERIMENTAL | Supported demo symbols only; unknown symbols return 404 |
| `/sectors`, `/intelligence`, `/historical` | DEMO / EDUCATIONAL | Explicit synthetic provenance and noindex |
| `/research`, `/research/prediction-v1` | INTERNAL RESEARCH | Authenticated, noindex, absent from public navigation |
| `/research-desk`, `/data-health`, `/settings` | INTERNAL ADMIN | Authenticated, noindex, absent from public navigation |
| `/api/research-desk` | INTERNAL API | Deny by default; authenticated, bounded, cached, and rate-limited |

No live or licensed raw provider payload may be serialized to a public route merely because that route is visually labelled internal or demo.

## 3. Explicit release gates

Gate states are `PASS`, `FAIL`, or `EXTERNAL`. A track releases only when every required gate is `PASS`; an external dependency remains an explicit blocker rather than being silently waived.

### Engineering gate — EXTERNAL

- [x] Clean main branch and reproducible dependency installation.
- [x] CI runs backend tests, Ruff, Mypy, frontend lint/typecheck/build, secret scan, dependency audit, link checks, and required security tests.
- [x] No known critical Python/TypeScript errors, automated console errors, broken links, or dead public routes.
- [x] Local durable state initialization, restart recovery, backup, and reproducibility are documented and tested.
- [x] Missing handlers fail closed; Linux deadlines are enforceable; retries, leases, and checkpoints are bounded.
- [x] Provider errors and runtime failures create sanitized actionable incidents.
- [ ] Production supervision, monitoring continuity, deployment promotion, and post-deploy verification require the external host/domain and repository controls.

### Data gate — EXTERNAL

- [x] Upstox authentication health verified through a bounded read-only canary without exposing credentials.
- [ ] Current-universe mapping is 200/200 exact; point-in-time historical membership remains external.
- [x] Freshness enforcement, stale blocking, deterministic manifests, provenance, and corporate-action warnings are implemented and tested at local boundaries.
- [x] Live/demo separation is enforced in serializers and negative tests.
- [x] Data-health evidence is visible only to authorized operators and does not pretend to be a live browser probe.
- [ ] Public redistribution/derived-data rights approved or public output limited to independently safe content. **EXTERNAL**

### Intelligence gate — EXTERNAL

- [ ] RBI/SEBI collection is wired to the supervised platform scheduler; continuous production execution requires the external worker host.
- [x] Luna structured analysis is wired into the normal worker under frozen prompt/model/schema controls.
- [ ] Hallucination quarantine, provider cost ledger, provenance, Research Desk, and Fusion abstention are implemented; continuous production operation is not yet evidenced.
- [x] Unverified inputs remain blocked; source staleness and collection failures open and resolve incidents.

### Public safety gate — EXTERNAL

- [x] No fixture/live mixing or fabricated metrics pass the public serializer.
- [x] Claims never exceed `HOLDOUT VALIDATED — FORWARD REQUIRED`.
- [x] No BUY/SELL, target price, return probability, recommendation, or misleading confidence wording is public.
- [x] Public-data rights are enforced in code and verified by negative tests.
- [ ] Risk, privacy, terms, data-source, methodology, and validation drafts match the implemented perimeter; final legal/compliance approval is **EXTERNAL**.

### Product gate — EXTERNAL

- [x] Public homepage explains the product, evidence process, limitations, and primary journey in plain language.
- [x] Navigation cleanly separates public and authenticated internal areas.
- [x] Automated screenshot QA passes at 1920, 1440, 1366, 1024, 430, 390, and 375 px.
- [x] Data surfaces preserve honest empty, stale, unavailable, insufficient, and abstention states; custom 404 exists.
- [ ] Metadata (including generated Open Graph, Twitter, and Apple touch assets), automated accessibility, local performance budgets, sitemap/robots, and canonical behavior pass; manual assistive-technology and deployed Web Vitals acceptance remain external.

### Operations gate — EXTERNAL

- [ ] Authorized health surfaces exist, but live provider/collector/spend/scheduler/incident continuity awaits the production worker and storage host.
- [x] Incident taxonomy, thresholds, deduplication, resolution, and runbooks are implemented and locally tested.
- [ ] Deployment evidence, rollback, backup, restore, retention, and archive contracts are implemented; managed off-host retention and deployed recovery evidence remain external.
- [ ] Staging and production are separate, documented, and smoke-tested.
- [x] Platform-owned schedules are distinct from Codex review/maintenance work.

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
- Public information architecture, draft policy pages, honest demo state, unknown-stock 404, responsive repair, keyboard skip navigation, restricted sitemap/robots, a public web manifest, and claim-bounded `WebSite` structured data are implemented and locally verified.
- The production smoke gate validates effective CSP, frame, referrer, permissions, MIME-sniffing,
  and HSTS response headers; security-header verification no longer relies on configuration review.
- `SEO_CONTENT_STRATEGY.md` maps India-focused, people-first search intents to the existing canonical
  public pages, prohibits unsupported query/claims expansion, and leaves Search Console and
  measurement inactive until the canonical domain, privacy, and owner gates are approved.
- A read-only weekly Codex readiness audit is installed against the saved local project and recorded
  in `CODEX_MAINTENANCE_AUTOMATIONS.md`. Its prompt prohibits mutation, deployment, publication,
  runtime activation, and predictions; it remains separate from platform-owned scheduling.
- `docs/runbooks/chatgpt-work-research.md` defines optional local/cloud Work boundaries, a bounded
  research brief, a candidate-only handoff contract, and independent verification before any source
  can enter the platform evidence pipeline. No Work task is represented as active.
- All seven sitemap routes now emit explicit self-referential canonical URLs. Production smoke tests
  reject absent canonicals, origin/path mismatches, and search/hash state; the actual production
  origin still depends on the external canonical-domain configuration.
- All six secondary indexable routes now expose accessible visible breadcrumbs and canonical
  `BreadcrumbList` structured data; production smoke rejects missing navigation or schema drift.
- Hosted CI now runs an optimized-build accessibility gate across all 14 public routes, including
  semantics, keyboard skip navigation, mobile target size, 200%/400% reflow, forced colors, and
  reduced motion; manual assistive-technology acceptance remains external.
- The 14-route × 7-viewport visual matrix now owns its optimized-build server lifecycle and runs in
  hosted CI, rejecting route, H1, overflow, framework-overlay, console, page, and network failures.
- The pinned pnpm setup action now uses its Node 24-backed v6.0.10 commit, removing the hosted
  Node 20 action-runtime deprecation without changing the project's pnpm 11.19.0 contract.
- A versioned production-build browser budget now gates representative public routes on navigation response, LCP, CLS, document, JavaScript, CSS, font, and total encoded payload; deployed field Web Vitals and INP remain external acceptance evidence.
- GitHub CI uses pinned actions and reproducible Python/Node dependency contracts; backend, frontend, audit, secret-scan, build, and production smoke jobs passed on hosted Actions.
- Release environment validation fails closed by deployment profile and never prints values. A canonical domain, separate hosted environments, and production credentials are still external.
- A hardened systemd service template now provides environment preflight, persistent state outside
  release directories, bounded restart, process-group stop, and least-privilege filesystem/kernel
  controls. Installation and notification routing require the production worker host.
- Deployment evidence now has a hash-sealed validator requiring the exact commit, immutable
  deployment and rollback identifiers, HTTPS origin, environment contract, public/internal and
  payload boundaries, headers/indexing/404/console checks, migration state, and rollback rehearsal.
  No staging or production evidence has been fabricated.
- The intelligence worker rejects missing handlers, records sanitized incidents, uses bounded source retries/checkpoints/leases, and now persists start/heartbeat/stop state. A local start/status/stop rehearsal passed; production host supervision and a new production-shaped soak remain unproved.
- A read-only EOD market collector and append-only ledger are wired into the platform scheduler. They
  enforce the India close window, exchange-complete status, exact current-universe mapping, atomic
  run/bar persistence, quarantine/missing disclosure, and blocked public delivery. The committed
  execution gate remains false; no EOD collection or forward prediction was started.
- SQLite online backup, integrity/hash manifest verification, traversal-safe restore verification, and non-overwriting restore tests are implemented. Managed production retention, off-host encryption, RPO/RTO, and restore evidence remain external to the local SQLite tool.
- The forward-validation ledger is append-only and causal. A disabled, fail-closed runtime now gates
  atomic issuance on an approved hash-sealed package and resolves exact completed-session evidence
  separately; no package, schedule, or forward prediction has been activated.

The next resolvable work is operational/deployment evidence and final release documentation. Prediction research gates, research mode, brokerage connectivity, BUY/SELL outputs, target prices, and public predictive activation remain unchanged.
