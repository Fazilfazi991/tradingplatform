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

## Mobile interaction

At 390 × 844, every visible link and button measured at least 44px high after remediation.
The disclosure banner now participates in document flow and the mobile header sticks at 0px,
preventing overlap when the disclosure wraps.

## Indexing boundary

Public methodology/information routes are indexable. Synthetic forecast, stock, Fusion,
historical, intelligence, and sector demos emit `noindex, nofollow` and are excluded through
`robots.txt`. Internal/admin/API routes remain disallowed and return 401 anonymously.

The sitemap contains only approved informational routes when a validated canonical origin is
available. Explicit HTTPS configuration is preferred; Vercel's production-domain environment
is the safe fallback. Unsafe non-local HTTP origins are rejected.

## Remaining QA

- Run keyboard order, screen-reader landmarks/names, zoom, high-contrast, and reduced-motion
  checks across every interactive public route.
- Collect a clean-browser console trace without unrelated extension message-channel errors.
- Preserve launch screenshots only after the canonical staging domain and final legal copy are
  approved.
- Measure production Web Vitals and server/API latency against staging and the final domain.
