# Source onboarding runbook

1. Add a source candidate; candidates cannot activate themselves.
2. Record official URL, category, access method, potential value, legal/technical status, cost, and
   reviewer decision.
3. Verify terms, robots where relevant, authentication, rate limits, retention, derived-use, internal
   use, redistribution, and approved hosts. Unclear answers remain `REVIEW_REQUIRED`.
4. Implement fixture and contract tests first. Add network code only for approved structured access.
5. Test timeouts, malformed content, redirects, content type, size limits, idempotency, replay, schema
   change, entity ambiguity, causal timestamps, and circuit behavior.
6. Activate internally through human review. Customer use requires separate licensing/compliance
   approval. Predictive status starts `UNKNOWN` regardless of source reputation.

Codex may discover, propose, implement, test, and audit integrations. It may not activate a source,
change production models or thresholds, promote features, publish predictions, or change compliance
gates autonomously.
