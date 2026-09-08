import assert from "node:assert/strict";
import test from "node:test";

import { FixedWindowLimiter, MemoryTtlCache } from "./bounded-runtime.ts";

test("fixed-window limiter remains bounded and recovers after the window", () => {
  const limiter = new FixedWindowLimiter(2, 1_000);
  assert.equal(limiter.allow(10_000), true);
  assert.equal(limiter.allow(10_001), true);
  assert.equal(limiter.allow(10_002), false);
  assert.equal(limiter.allow(11_001), true);
});

test("memory cache expires without returning stale values", () => {
  const cache = new MemoryTtlCache<{ safe: boolean }>(100);
  assert.equal(cache.get(1_000), undefined);
  cache.set({ safe: true }, 1_000);
  assert.deepEqual(cache.get(1_099), { safe: true });
  assert.equal(cache.get(1_100), undefined);
});
