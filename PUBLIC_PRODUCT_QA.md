# Public Product QA

Status date: 2026-09-08  
Target: local optimized production build at `127.0.0.1:3200`  
Browser: Chrome

## Responsive route matrix

The public route inventory was exercised at these exact viewport sizes:

- 1920 × 1080
- 1440 × 900
- 1366 × 768
- 1024 × 768
- 430 × 932
- 390 × 844
- 375 × 812

Routes covered: `/`, `/predictions`, `/stocks/RELIANCE`, `/fusion`, `/models`,
`/methodology`, `/data-sources`, `/validation`, `/about`, `/faq`, `/risk`, `/privacy`,
`/terms`, and `/contact`.

Result: 98/98 combinations had meaningful body content, one visible H1, no horizontal
document overflow, and no framework error overlay. Screenshot review covered the homepage at
all seven required viewports. The 1280px diagnostic viewport initially exposed a 24px layout
overflow; the desktop/two-column breakpoint was corrected and reverified.

The matrix is now reproducible with `pnpm --filter @verified-edge/web visual:qa`. It uses the
project-managed Playwright package and the installed Chrome channel rather than a machine-specific
cache path. A fresh optimized build completed all 98 checks with zero route failures, structural
failures, console errors, page errors, or non-cancellation network failures. Chrome's expected
`ERR_ABORTED` cancellation of Next prefetch requests during immediate scripted navigation is the
only explicitly ignored transport condition.

The production smoke gate also crawls every internal anchor rendered by the public route inventory.
It initially found seven forecast rows pointing to intentionally unsupported stock routes. The demo
was constrained to its one complete RELIANCE walkthrough, inert horizon/universe filters were
removed, and an honest no-result search state was added. The rebuilt smoke gate verified all 14
discovered internal links; the post-fix Chrome matrix again passed 98/98 with zero errors.

The same production-build gate now inspects response headers rather than treating configuration as
proof. It requires the deployed CSP to retain self-only defaults plus blocked framing and objects,
and verifies the frame, referrer, permissions, MIME-sniffing, and production HSTS policies. A
missing header or required directive fails the release smoke run.

## Mobile interaction

At 390 × 844, every visible link and button measured at least 44px high after remediation.
The disclosure banner now participates in document flow and the mobile header sticks at 0px,
preventing overlap when the disclosure wraps.

## Accessibility checks

The skip link is the first keyboard focus target at desktop width, is 44px high, and receives a
visible 2px focus outline. Its target is programmatically focusable. Across all 14 public routes,
an automated structural check found no unlabeled buttons or form fields, missing image
alternatives, duplicate IDs, heading-level skips, missing main landmark, or unlabeled navigation
landmarks. Reduced-motion CSS disables animation, transitions, and smooth scrolling.

The optimized-build accessibility gate is reproducible with `pnpm accessibility:web` and runs in
hosted CI. It additionally checks every visible mobile link/button against a 44px target minimum,
tests 200% and 400% reflow at their equivalent 640px and 320px CSS viewports, verifies forced-colors
mode remains structurally usable without horizontal overflow, and confirms that the homepage and
Fusion animations stop under the reduced-motion preference. The gate identified and corrected an
18px-tall stock-to-Fusion link before acceptance.

## Indexing boundary

Public methodology/information routes are indexable. Synthetic forecast, stock, Fusion,
historical, intelligence, and sector demos emit `noindex, nofollow` and are excluded through
`robots.txt`. Internal/admin/API routes remain disallowed and return 401 anonymously.

The sitemap contains only approved informational routes when a validated canonical origin is
available. Explicit HTTPS configuration is preferred; Vercel's production-domain environment
is the safe fallback. Unsafe non-local HTTP origins are rejected. All seven sitemap routes emit an
explicit self-referential canonical URL, and the production smoke gate rejects a missing canonical,
wrong origin or path, or canonical containing search/hash state.

## Public payload boundary

The production-build audit at `pnpm public-boundary:web` fetches all 14 public routes, verifies the
six internal/admin/API denial surfaces, and follows every referenced Next.js static asset. The
current run inspected 14 text assets and found no credential identifiers, private-key markers,
local machine paths, internal forward-model paths, or runtime-state paths. It also probed every
public JavaScript chunk for a corresponding source map and found zero exposed maps. This is a local
release gate; the same inspection remains mandatory against staging and the canonical deployment.

## Remaining QA

- Complete manual screen-reader behavior and human visual review of contrast, 200%/400% browser
  zoom, and Windows forced-colors across every interactive public route. Automated structural,
  reflow, target-size, forced-colors, and reduced-motion gates now pass but do not replace that review.
- Preserve launch screenshots only after the canonical staging domain and final legal copy are
  approved.
- Measure production Web Vitals and server/API latency against staging and the final domain.

## Local production performance gate

`pnpm performance:web` starts the optimized production build and measures six representative routes
in a clean Chrome context against versioned budgets in `config/web-performance-budgets.json`. The
current run recorded a maximum 168.9ms navigation response, 588ms LCP, 0.0765 CLS, 251,286 bytes of
route JavaScript, 98,040 bytes of fonts, and 394,162 total encoded bytes. Every route passed.

These measurements are reproducible local lab evidence, not production TTFB or real-user evidence.
INP requires representative deployed interaction data and remains part of the canonical deployment
acceptance rather than being inferred from a synthetic click.

## Share and installed-app assets

The canonical metadata now resolves generated 1200 × 630 Open Graph and Twitter PNG cards plus a
180 × 180 Apple touch icon. The production smoke gate reads the URLs from rendered metadata,
fetches each asset, verifies its PNG response, and rejects unexpectedly small social images. The
share card uses the existing Evidence Lens visual system and limits its message to the platform's
evidence, contradiction, provenance, uncertainty, and no-trading-signals boundaries. Bundled
Newsreader and Manrope font subsets retain their SIL Open Font License notices.
