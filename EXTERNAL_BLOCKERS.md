# External Blockers

Status date: 2026-09-08

| ID | Dependency / authority | Evidence required to close | Impact while open | Safe interim behavior | State |
|---|---|---|---|---|---|
| EXT-01 | Upstox/provider public redistribution and derived commercial rights | Written provider approval identifying permitted fields, transformations, caching, display, retention, and customer use | Live/provider-derived public data blocked | Internal analysis only; public UI uses clearly synthetic fixtures | OPEN |
| EXT-02 | Point-in-time NIFTY 200 membership and licensing | Licensed history with effective dates and reproducible universe snapshots | Predictive generalization and survivorship claims remain limited | Label current-universe survivorship bias; no verified-edge claim | OPEN |
| EXT-03 | Corporate-action adjustment semantics | Provider documentation or independently reconciled adjustment evidence | Returns/targets may be distorted | Preserve warning; do not promote predictive validation | OPEN |
| EXT-04 | Independent market-data reconciliation | Approved provider/contract and tolerance policy | Single-provider errors cannot be independently detected | Retain single-provider limitation | OPEN |
| EXT-05 | Legal and regulatory perimeter | Counsel approval of Terms, Privacy, Risk Disclosure, methodology/validation wording, public security-specific research, and any paid capability | Track A production and promotion blocked | Keep draft documents labelled; no public predictive activation | OPEN |
| EXT-06 | Hosting and domain | Canonical domain, linked Vercel/hosting project, owner-approved staging/production envs and scoped credentials | Canonical metadata and real deployment/smoke proof unavailable | Build and test locally; never infer production success | OPEN |
| EXT-07 | Repository controls | Owner enables branch protection, required CI checks, and hosted secret scanning | Main can be changed without enforced review/checks | CI configuration committed; report hosted setting as unverified | OPEN |
| EXT-08 | Analytics and consent | Owner privacy decision, approved provider/configuration, retention and consent requirements | Funnel measurement unavailable | Ship no analytics and no tracking cookies | OPEN |
| EXT-09 | Public positioning and promotion | Owner approval of demo discoverability, claims ledger, launch copy and publication channels | Promotion blocked | Prepare drafts only; do not publish | OPEN |
| EXT-10 | Additional intelligence sources | Credentials, contracts, access and rights for Fundamental, Flow/Derivatives and broader macro inputs | Specialist live coverage incomplete | Report `ENGINEERING_ONLY`, `INSUFFICIENT_EVIDENCE`, or `ABSTAIN` | OPEN |
| EXT-11 | Prospective validation time | Sufficient immutable forward predictions, elapsed outcome windows and preregistered evaluation minimums | Track B remains unavailable | Continue internal forward paper collection; do not publish predictions | OPEN |

Closing a blocker requires dated evidence and the accountable approver. A code change cannot close a rights, legal, domain, or elapsed-time dependency.
