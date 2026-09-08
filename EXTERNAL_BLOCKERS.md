# External Blockers

Status date: 2026-09-08

| ID | Dependency / authority | Evidence required to close | Impact while open | Safe interim behavior | State |
|---|---|---|---|---|---|
| EXT-01 | Upstox/provider public redistribution and derived commercial rights | Written provider approval identifying permitted fields, transformations, caching, display, retention, and customer use | Live/provider-derived public data blocked | Internal analysis only; public UI uses clearly synthetic fixtures | OPEN |
| EXT-02 | Point-in-time NIFTY 200 membership and licensing | Licensed history with effective dates and reproducible universe snapshots | Predictive generalization and survivorship claims remain limited | Label current-universe survivorship bias; no verified-edge claim | OPEN |
| EXT-03 | Corporate-action adjustment semantics | Provider documentation or independently reconciled adjustment evidence | Returns/targets may be distorted | Preserve warning; do not promote predictive validation | OPEN |
| EXT-04 | Independent market-data reconciliation | Approved provider/contract and tolerance policy | Single-provider errors cannot be independently detected | Retain single-provider limitation | OPEN |
| EXT-05 | Legal and regulatory perimeter | Counsel approval of Terms, Privacy, Risk Disclosure, methodology/validation wording, public security-specific research, and any paid capability | Track A production and promotion blocked | Keep draft documents labelled; no public predictive activation | OPEN |
| EXT-06 | Hosting and domain | Owner-approved canonical domain, protected staging/production release environments with scoped credentials, successful staged build, production promotion, smoke and rollback evidence | The linked Vercel project has no project variables; Standard Protection covers generated deployment URLs but no automation-bypass secret is configured; GitHub lacks `production-staging`, while `Production` exists without reviewers, restrictions, secrets, or variables | Keep automatic Git deployment disabled; configure the exact protected environment contract before using the fail-closed manual release workflow | OPEN |
| EXT-07 | Repository controls | Owner enables a `main` ruleset or classic branch protection with required CI checks and pull-request review | Main can be changed without enforced review/checks | Secret protection and push protection are enabled; CI configuration is committed, but branch rules remain absent | OPEN |
| EXT-08 | Analytics and consent | Owner privacy decision, approved provider/configuration, retention and consent requirements | Funnel measurement unavailable | Ship no analytics and no tracking cookies | OPEN |
| EXT-09 | Public positioning and promotion | Owner approval of demo discoverability, claims ledger, launch copy and publication channels | Promotion blocked | Prepare drafts only; do not publish | OPEN |
| EXT-10 | Additional intelligence sources | Credentials, contracts, access and rights for Fundamental, Flow/Derivatives and broader macro inputs | Specialist live coverage incomplete | Report `ENGINEERING_ONLY`, `INSUFFICIENT_EVIDENCE`, or `ABSTAIN` | OPEN |
| EXT-11 | Prospective validation time | Sufficient immutable forward predictions, elapsed outcome windows and preregistered evaluation minimums | Track B remains unavailable | Continue internal forward paper collection; do not publish predictions | OPEN |
| EXT-12 | Manual accessibility and deployed performance acceptance | Screen-reader, forced-colors, 200%/400% zoom review plus production Web Vitals against the canonical deployment | Automated QA alone cannot prove the complete product gate | Keep automated accessibility, responsive, bundle, and smoke gates enforced; do not claim full production acceptance | OPEN |

Closing a blocker requires dated evidence and the accountable approver. A code change cannot close a rights, legal, domain, or elapsed-time dependency.
