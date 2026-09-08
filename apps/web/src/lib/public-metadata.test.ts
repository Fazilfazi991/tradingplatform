import assert from "node:assert/strict";
import test from "node:test";

import { publicWebsiteStructuredData, serializeStructuredData } from "./public-metadata.ts";

test("public structured data describes only the informational website", () => {
  const data = publicWebsiteStructuredData("https://verified.example");
  assert.equal(data["@type"], "WebSite");
  assert.equal(data.url, "https://verified.example/");
  const serialized = serializeStructuredData(data);
  for (const prohibited of ["InvestmentProduct", "BuyAction", "SellAction", "prediction accuracy"])
    assert.equal(serialized.includes(prohibited), false);
});

test("structured data serialization cannot terminate its script element", () => {
  const serialized = serializeStructuredData({ unsafe: "</script><script>alert(1)</script>" });
  assert.equal(serialized.includes("<"), false);
  assert.equal(JSON.parse(serialized).unsafe, "</script><script>alert(1)</script>");
});
