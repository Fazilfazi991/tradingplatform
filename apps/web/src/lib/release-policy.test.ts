import assert from "node:assert/strict";
import test from "node:test";
import { internalAccessAudit, validBasicAuthorization } from "./internal-auth.ts";
import { assertPublicDelivery, PublicDeliveryRejected } from "./public-delivery.ts";
import { classifySurface, isInternalPath } from "./route-policy.ts";

test("internal routes are classified and matched fail-closed", () => {
  for (const path of ["/research", "/research/prediction-v1", "/research-desk", "/data-health", "/settings", "/api/research-desk"]) {
    assert.equal(isInternalPath(path), true, path);
  }
  assert.equal(isInternalPath("/predictions"), false);
  assert.equal(classifySurface("/stocks/RELIANCE"), "DEMO");
  assert.equal(classifySurface("/fusion"), "PUBLIC");
});

test("internal authorization is disabled when either credential is absent", () => {
  const valid = `Basic ${btoa("operator:correct horse battery staple")}`;
  assert.equal(validBasicAuthorization(valid, undefined, undefined), false);
  assert.equal(validBasicAuthorization(valid, "operator", undefined), false);
  assert.equal(validBasicAuthorization(valid, "operator", "correct horse battery staple"), true);
  assert.equal(validBasicAuthorization(valid, "operator", "wrong"), false);
  assert.equal(validBasicAuthorization("Bearer token", "operator", "correct horse battery staple"), false);
});

test("internal access audit contains no identity, credential, query, or payload", () => {
  const record = internalAccessAudit(
    "GET",
    "/research/prediction-v1",
    "AUTHORIZED",
    new Date("2026-09-08T00:00:00Z"),
  );
  assert.deepEqual(record, {
    event: "INTERNAL_ROUTE_ACCESS",
    outcome: "AUTHORIZED",
    method: "GET",
    path: "/research/prediction-v1",
    occurred_at: "2026-09-08T00:00:00.000Z",
    sensitive_values_logged: false,
  });
  assert.equal(JSON.stringify(record).includes("authorization"), false);
});

test("public delivery accepts only fresh, rights-approved, unmixed content", () => {
  const payload = { label: "Synthetic demonstration" };
  assert.deepEqual(assertPublicDelivery({
    contentClass: "SYNTHETIC_DEMO",
    rightsState: "PUBLIC_APPROVED",
    validationState: "DEMO_SYNTHETIC",
    stale: false,
    mixedFixtureAndLive: false,
    payload,
  }), payload);

  for (const envelope of [
    { contentClass: "INTERNAL_LIVE", rightsState: "NOT_APPROVED", validationState: "PREDICTIVELY_VALIDATED", stale: false, mixedFixtureAndLive: false },
    { contentClass: "SYNTHETIC_DEMO", rightsState: "PUBLIC_APPROVED", validationState: "DEMO_SYNTHETIC", stale: true, mixedFixtureAndLive: false },
    { contentClass: "SYNTHETIC_DEMO", rightsState: "PUBLIC_APPROVED", validationState: "DEMO_SYNTHETIC", stale: false, mixedFixtureAndLive: true },
    { contentClass: "INTERNAL_RESEARCH", rightsState: "PUBLIC_APPROVED", validationState: "HOLDOUT_VALIDATED_FORWARD_REQUIRED", stale: false, mixedFixtureAndLive: false },
  ] as const) {
    assert.throws(() => assertPublicDelivery({ ...envelope, payload }), PublicDeliveryRejected);
  }
});
