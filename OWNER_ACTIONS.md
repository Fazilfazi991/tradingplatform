# Owner Actions

Only decisions or credentials that require owner authority are listed here. Ordinary engineering work remains with the implementation team.

1. Obtain written Upstox/provider confirmation for public redistribution and derived/commercial display rights, including caching and retention terms.
2. Approve the existing linked Vercel project for release and choose the canonical production
   domain. Add the exact GitHub environment `production-staging`; harden the existing `Production`
   environment with required reviewer approval and branch restrictions; add the scoped Vercel
   secrets and canonical URL variable to both workflow environments. Create a dedicated Vercel
   automation-bypass secret for the protected staging smoke and store it only as the corresponding
   GitHub environment secret. The Vercel project currently has no project variables. Standard
   Protection is enabled for generated deployment URLs, and the project root already matches the
   repository-root contract.
3. Arrange legal/compliance review of the actual informational-research perimeter, Terms, Privacy, Risk Disclosure, data-source wording, validation-status wording, and any future paid/security-specific research.
4. Decide whether synthetic demo forecasts may be publicly indexable or must remain unindexed/private during validation.
5. Decide whether privacy-conscious analytics are approved; if yes, approve provider, events, retention, cookie/consent behavior, and privacy disclosure.
6. Enable a `main` ruleset or classic branch protection with required `backend`, `web`, and
   `repository-safety` checks plus pull-request review. Hosted secret protection and push protection
   are already enabled.
7. Approve final public positioning and the evidence-linked claims ledger before any promotion is published.
8. Supply strong staging/production internal-access credentials through the hosting secret store; never commit or message their values.
9. Provide or approve the Linux worker host, locked service identity, persistent encrypted storage,
   and incident notification destinations needed to install the reviewed systemd service.
10. Arrange the final assistive-technology review and canonical-deployment performance acceptance;
    provide the resulting dated evidence for the release gate.
