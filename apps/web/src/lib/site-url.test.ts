import assert from "node:assert/strict";
import test from "node:test";
import { canonicalSiteOrigin } from "./site-url.ts";

test("uses an explicit canonical origin and removes paths", () => {
  assert.equal(
    canonicalSiteOrigin({ NEXT_PUBLIC_SITE_URL: "https://example.com/path" }),
    "https://example.com",
  );
});

test("uses Vercel's production domain when explicit configuration is absent", () => {
  assert.equal(
    canonicalSiteOrigin({ VERCEL_PROJECT_PRODUCTION_URL: "verified-edge.vercel.app" }),
    "https://verified-edge.vercel.app",
  );
});

test("rejects unsafe public origins but permits local QA", () => {
  assert.equal(canonicalSiteOrigin({ NEXT_PUBLIC_SITE_URL: "http://example.com" }), undefined);
  assert.equal(
    canonicalSiteOrigin({ NEXT_PUBLIC_SITE_URL: "http://127.0.0.1:3200" }),
    "http://127.0.0.1:3200",
  );
});
