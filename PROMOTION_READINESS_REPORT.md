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
- Automatic Git deployments are disabled. The manual release workflow verifies those exact hosted
  checks, stages a production build without assigning public domains, smoke-tests the deployed
  boundary, rechecks Track A authorization, and only then reaches the protected production approval.
  It has not been run because the required external gates and hosted environment configuration are
  still open.
- The manual workflow now requires a previous healthy deployment ID and successful rollback-rehearsal
  attestation before staging. After promotion it runs HTTP and real-browser console/network checks,
  seals and validates `deployment-evidence-v1`, and retains it as a commit-addressed artifact. A
  smoke, sealing, or upload failure restores the exact recorded healthy deployment, re-smokes the
  canonical boundary, and rejects the release.
- Authenticated Vercel inspection confirms Standard Protection covers the staged generated URL.
  The workflow now requires a dedicated automation-bypass secret before build and sends it only in
  the protection-bypass header; the project and GitHub release environments do not yet contain that
  credential.
- Local SQLite backup/restore integrity checks and a real intelligence-worker
  start/heartbeat/graceful-stop rehearsal pass. These do not substitute for managed production
  storage, retention, host supervision, or deployed recovery evidence.
- `CLAIMS_LEDGER.md` and `PROMOTION_PACKAGE_DRAFT.md` now provide evidence-linked safe claims,
  prohibited claims, short/long descriptions, founder notes, launch copy, walkthrough, and a final
  capture list. Both remain explicitly unapproved and unpublished.
- A project-managed Chrome/Playwright verifier now reproduces the 14-route × 7-viewport matrix.
  It owns its local optimized-build server lifecycle and runs as a required hosted CI gate. Against
  a fresh build it recorded 98/98 passes and zero console, page, structural, or actionable network
  failures. The earlier extension/stale-build console uncertainty is closed.
- The production smoke gate now crawls rendered internal links. It caught and closed unsupported
  stock links and inert forecast filters; the public demo exposes only its complete RELIANCE
  walkthrough and an explicit no-result state. It also verifies the effective CSP, frame, referrer,
  permissions, content-type, and HSTS response policies from the optimized production server.
- Versioned local performance budgets now gate representative routes on navigation response, LCP,
  CLS, and encoded document/JavaScript/CSS/font/total payload. A separate production-build boundary
  audit inspects every public HTML response and referenced text asset, verifies protected denials,
  and rejects credential identifiers, machine paths, internal runtime paths, and exposed source maps.
- A hosted Fusion CLS regression was source-attributed to the streamed shell footer and corrected by
  reserving stable shell geometry. Repeated Fusion CLS measurements now remain well below the frozen
  `0.08` budget, and the replacement exact-commit hosted run passes.
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
- Manual screen-reader and human visual review of contrast, Windows forced-colors, and 200%/400%
  browser zoom across the full interactive public route inventory. Automated structural,
  target-size, reflow, forced-colors, and reduced-motion gates pass but do not replace this review.
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
