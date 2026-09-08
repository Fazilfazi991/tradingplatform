import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const deploymentOrigin = normalizeOrigin(process.argv[2], "deployment URL");
const canonicalOrigin = normalizeOrigin(process.argv[3], "canonical URL");
const bypass = process.env.VERCEL_AUTOMATION_BYPASS_SECRET?.trim();
const configPath = fileURLToPath(
  new URL("../../../config/public-boundary-audit.json", import.meta.url),
);
const boundaryConfig = JSON.parse(await readFile(configPath, "utf8"));
const forbiddenText = [
  ...boundaryConfig.forbidden_text,
  ["BEGIN", "PRIVATE", "KEY"].join(" "),
  ["BEGIN", "RSA", "PRIVATE", "KEY"].join(" "),
];

function normalizeOrigin(raw, label) {
  if (!raw) throw new Error(`${label} is required`);
  const parsed = new URL(raw);
  if (parsed.protocol !== "https:" || !parsed.hostname || parsed.username || parsed.password) {
    throw new Error(`${label} must be an uncredentialed HTTPS origin`);
  }
  if (parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new Error(`${label} must not contain a path, query, or fragment`);
  }
  if (parsed.hostname === "localhost" || parsed.hostname.endsWith(".localhost")) {
    throw new Error(`${label} cannot be localhost`);
  }
  return parsed.origin;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function request(path) {
  // Every CI request carries the bypass header directly. Do not request a bypass
  // cookie: Vercel establishes it through a redirect, while this audit keeps
  // redirects manual so that unexpected protection or application redirects fail.
  const headers = bypass ? { "x-vercel-protection-bypass": bypass } : {};
  return fetch(`${deploymentOrigin}${path}`, { headers, redirect: "manual" });
}

function inspectText(label, value, failures) {
  for (const forbidden of forbiddenText) {
    if (value.includes(forbidden)) failures.push(`${label}: exposed forbidden marker ${forbidden}`);
  }
  if (/file:\/\/\/(?:[A-Za-z]:\/|home\/|Users\/)/i.test(value)) {
    failures.push(`${label}: exposed local file URI`);
  }
  if (/[A-Za-z]:\\Users\\[^\\"' ]+/i.test(value)) failures.push(`${label}: exposed Windows user path`);
}

const publicRoutes = boundaryConfig.public_routes;
const indexableRoutes = ["/", "/methodology", "/data-sources", "/validation", "/models", "/about", "/faq"];
const protectedRoutes = boundaryConfig.protected_routes;
const demoRoutes = [
  "/predictions", "/stocks/RELIANCE", "/fusion", "/historical", "/intelligence", "/sectors",
];
const publicAssets = new Set();
const boundaryFailures = [];

for (const path of publicRoutes) {
  const response = await request(path);
  const body = await response.text();
  assert(response.status === 200, `${path} returned ${response.status}`);
  assert(/<h1[ >]/i.test(body), `${path} has no rendered H1`);
  assert(!body.includes("Application error"), `${path} rendered an application error`);
  inspectText(`public HTML ${path}`, body, boundaryFailures);
  for (const match of body.matchAll(/(?:src|href)=["']([^"']+)["']/gi)) {
    const asset = match[1].replaceAll("&amp;", "&");
    if (asset.startsWith("/_next/static/")) publicAssets.add(new URL(asset, deploymentOrigin).pathname);
  }
}

for (const path of protectedRoutes) {
  const response = await request(path);
  assert(response.status === 401, `${path} did not deny anonymous access`);
  assert(response.headers.get("cache-control") === "no-store", `${path} is cacheable`);
  assert(response.headers.get("x-robots-tag")?.includes("noindex"), `${path} is indexable`);
  inspectText(`protected denial ${path}`, await response.text(), boundaryFailures);
}

for (const asset of publicAssets) {
  const response = await request(asset);
  assert(response.status === 200, `${asset} returned ${response.status}`);
  const type = response.headers.get("content-type") ?? "";
  if (type.includes("javascript") || type.includes("text/css")) {
    inspectText(`public asset ${asset}`, await response.text(), boundaryFailures);
  }
  if (asset.endsWith(".js")) {
    const sourceMap = await request(`${asset}.map`);
    assert(sourceMap.status !== 200, `${asset}.map exposed a production source map`);
  }
}
assert(boundaryFailures.length === 0, boundaryFailures.join("\n"));

for (const path of demoRoutes) {
  const response = await request(path);
  const body = await response.text();
  assert(response.status === 200, `${path} returned ${response.status}`);
  assert(/<meta name="robots" content="noindex, nofollow"/i.test(body), `${path} lacks noindex`);
}

for (const path of indexableRoutes) {
  const response = await request(path);
  const body = await response.text();
  const canonicalMatch = body.match(/<link rel="canonical" href="([^"]+)"/i);
  assert(canonicalMatch, `${path} omitted its canonical URL`);
  const canonical = new URL(canonicalMatch[1].replaceAll("&amp;", "&"));
  assert(canonical.origin === canonicalOrigin, `${path} canonical used ${canonical.origin}`);
  assert(canonical.pathname === path, `${path} canonical pointed to ${canonical.pathname}`);
  assert(!canonical.search && !canonical.hash, `${path} canonical included search or hash state`);
}

const unknownStock = await request("/stocks/NOT-A-REAL-SYMBOL");
assert(unknownStock.status === 404, `unknown stock returned ${unknownStock.status}`);

const root = await request("/");
const requiredHeaders = {
  "content-security-policy": ["default-src 'self'", "frame-ancestors 'none'", "object-src 'none'"],
  "permissions-policy": ["camera=()", "microphone=()", "geolocation=()", "payment=()"],
  "referrer-policy": ["strict-origin-when-cross-origin"],
  "strict-transport-security": ["max-age=63072000", "includeSubDomains", "preload"],
  "x-content-type-options": ["nosniff"],
  "x-frame-options": ["DENY"],
};
for (const [header, directives] of Object.entries(requiredHeaders)) {
  const value = root.headers.get(header);
  assert(value, `missing ${header}`);
  for (const directive of directives) assert(value.includes(directive), `${header} lacks ${directive}`);
}

const robots = await request("/robots.txt");
const robotsBody = await robots.text();
assert(robots.status === 200, `/robots.txt returned ${robots.status}`);
assert(robotsBody.includes(`${canonicalOrigin}/sitemap.xml`), "robots sitemap uses the wrong origin");

const sitemap = await request("/sitemap.xml");
const sitemapBody = await sitemap.text();
assert(sitemap.status === 200, `/sitemap.xml returned ${sitemap.status}`);
for (const path of indexableRoutes) {
  assert(sitemapBody.includes(`<loc>${canonicalOrigin}${path}</loc>`), `sitemap omitted ${path}`);
}
for (const path of protectedRoutes) {
  assert(!sitemapBody.includes(`<loc>${canonicalOrigin}${path}</loc>`), `sitemap exposed ${path}`);
}

console.log(JSON.stringify({
  status: "PASS",
  deployment_origin: deploymentOrigin,
  canonical_origin: canonicalOrigin,
  public_routes: publicRoutes.length,
  protected_routes: protectedRoutes.length,
  public_assets: publicAssets.size,
  checks: [
    "public_routes", "internal_auth_boundary", "public_payload_boundary", "security_headers",
    "robots_sitemap_canonical", "unknown_stock_404", "demo_noindex", "source_map_boundary",
  ],
}));
