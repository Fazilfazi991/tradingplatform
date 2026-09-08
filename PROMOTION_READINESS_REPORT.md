# Promotion Readiness Report

Status date: 2026-09-08  
Decision: **BLOCKED**

## Current evidence

- A public homepage, coherent public navigation, methodology, data-source, validation, About, FAQ, draft Risk, draft Privacy, draft Terms, and draft Contact surfaces now exist.
- Anonymous access to internal research/admin routes and `/api/research-desk` returns `401` with `noindex`, `nofollow`, `noarchive`, and `no-store` controls.
- Public delivery policy tests reject stale data, fixture/live mixing, internal research, unapproved rights, and live predictive output without predictive validation.
- Unknown stock symbols return a real `404` rather than a plausible RELIANCE fixture.
- The production Next build, frontend typecheck, lint, and release-policy tests pass.
- Chrome desktop review confirms the homepage and methodology render without a framework error surface. The homepage preserves the established Evidence Lens visual system.
- Chrome screenshot review now covers the homepage at all seven required desktop, tablet, and
  mobile viewports. A detected 1280px overflow and undersized mobile navigation/link targets
  were repaired; the 98-combination public route/viewport matrix passes overflow, content, H1,
  and framework-overlay checks.
- Synthetic demo routes now emit `noindex, nofollow`; the sitemap is limited to approved
  informational routes and supports validated explicit or Vercel production origins. Each sitemap
  route now emits a smoke-verified self-referential canonical URL.
- Keyboard-first skip navigation and automated structural accessibility checks now pass across
  all 14 public routes; local optimized-build response and bundle baselines are recorded in
  `PUBLIC_PRODUCT_QA.md`.
- Reproducible GitHub CI runs pinned backend, frontend, repository-safety, dependency-audit,
  environment-contract, production-build, smoke, public-boundary, and local-performance gates.
  Every release candidate remains subject to a successful hosted run at its exact commit.
- Local SQLite backup/restore integrity checks and a real intelligence-worker
  start/heartbeat/graceful-stop rehearsal pass. These do not substitute for managed production
  storage, retention, host supervision, or deployed recovery evidence.
- `CLAIMS_LEDGER.md` and `PROMOTION_PACKAGE_DRAFT.md` now provide evidence-linked safe claims,
  prohibited claims, short/long descriptions, founder notes, launch copy, walkthrough, and a final
  capture list. Both remain explicitly unapproved and unpublished.
- A project-managed Chrome/Playwright verifier now reproduces the 14-route × 7-viewport matrix.
  Against a fresh optimized build it recorded 98/98 passes and zero console, page, structural, or
  actionable network failures. The earlier extension/stale-build console uncertainty is closed.
- The production smoke gate now crawls rendered internal links. It caught and closed unsupported
  stock links and inert forecast filters; the public demo exposes only its complete RELIANCE
  walkthrough and an explicit no-result state. It also verifies the effective CSP, frame, referrer,
  permissions, content-type, and HSTS response policies from the optimized production server.
- Versioned local performance budgets now gate representative routes on navigation response, LCP,
  CLS, and encoded document/JavaScript/CSS/font/total payload. A separate production-build boundary
  audit inspects every public HTML response and referenced text asset, verifies protected denials,
  and rejects credential identifiers, machine paths, internal runtime paths, and exposed source maps.
- Generated Open Graph, Twitter, and Apple touch assets now ship from the production build. Smoke
  coverage resolves and validates those rendered metadata URLs, while the share-card copy preserves
  the no-trading-signals and evidence-boundary language. This is technical asset readiness, not
  authorization to publish promotion.
- The India-focused search-intent plan now assigns one people-first purpose to each indexable public
  page, rejects fabricated volume/ranking claims and keyword-spam expansion, and keeps Search Console
  activation dependent on the canonical domain, privacy decision, and owner approval.

## Still required

- Legal/compliance approval of all perimeter and policy language.
- Public data-rights approval or proof that the launched payload contains only independently safe data.
- Authenticated-route review in staging with production-shaped secrets and logs.
- Manual screen-reader, contrast, Windows forced-colors, and 200%/400% zoom checks across the
  full interactive public route inventory.
- Production performance and real-user Web Vitals measurements on staging/canonical hosting.
- Canonical domain, canonical metadata, real sitemap, Search Console decision, staging/production smoke evidence, and rollback proof.
- Production host supervision, notification destinations, managed backup/retention policy, and a
  production-shaped worker soak/restart record.
- Owner/legal approval of the draft claims ledger and promotion package, plus final canonical-build
  launch screenshots.
- Owner approval of demo forecast discoverability and analytics/privacy choices.

## Claims boundary

Approved current factual state: `HOLDOUT VALIDATED — FORWARD REQUIRED`. Do not publish BUY/SELL calls, target prices, return probabilities, “verified edge,” customer confidence scores, or performance claims.

## Gate

### PROMOTION NOT READY
