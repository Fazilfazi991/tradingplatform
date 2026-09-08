import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const host = "127.0.0.1";
const port = "3210";
const origin = `http://${host}:${port}`;
const root = fileURLToPath(new URL("..", import.meta.url));
const nextCli = fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url));
const server = spawn(process.execPath, [nextCli, "start", "--hostname", host, "--port", port], {
  cwd: root,
  env: { ...process.env, NODE_ENV: "production" },
  stdio: ["ignore", "pipe", "pipe"],
});

let serverOutput = "";
server.stdout.on("data", (chunk) => { serverOutput += chunk.toString(); });
server.stderr.on("data", (chunk) => { serverOutput += chunk.toString(); });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function request(path) {
  return fetch(`${origin}${path}`, { redirect: "manual" });
}

async function waitUntilReady() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`server exited before readiness\n${serverOutput}`);
    try {
      const response = await request("/");
      if (response.status === 200) return;
    } catch {
      // The listener is not ready yet.
    }
    await delay(100);
  }
  throw new Error(`server readiness timed out\n${serverOutput}`);
}

const publicRoutes = [
  "/", "/methodology", "/data-sources", "/validation", "/models", "/about", "/faq",
  "/risk", "/privacy", "/terms", "/contact", "/predictions", "/stocks/RELIANCE", "/fusion",
];
const protectedRoutes = [
  "/research", "/research/prediction-v1", "/research-desk", "/data-health", "/settings",
  "/api/research-desk",
];
const demoRoutes = [
  "/predictions", "/stocks/RELIANCE", "/fusion", "/historical", "/intelligence", "/sectors",
];

try {
  await waitUntilReady();
  const linkedPaths = new Set();
  for (const path of publicRoutes) {
    const response = await request(path);
    const body = await response.text();
    assert(response.status === 200, `${path} returned ${response.status}`);
    assert(/<h1[ >]/i.test(body), `${path} has no rendered H1`);
    assert(!body.includes("Application error"), `${path} rendered an application error`);
    for (const match of body.matchAll(/<a\b[^>]*\bhref=["']([^"']+)["']/gi)) {
      const href = match[1].replaceAll("&amp;", "&");
      if (href.startsWith("/") && !href.startsWith("//")) {
        linkedPaths.add(new URL(href, origin).pathname);
      }
    }
  }
  for (const path of linkedPaths) {
    assert(!protectedRoutes.includes(path), `public page links to protected route ${path}`);
    const response = await request(path);
    assert(response.status === 200, `rendered link ${path} returned ${response.status}`);
  }
  for (const path of protectedRoutes) {
    const response = await request(path);
    assert(response.status === 401, `${path} did not deny anonymous access`);
    assert(response.headers.get("cache-control") === "no-store", `${path} is cacheable`);
    assert(response.headers.get("x-robots-tag")?.includes("noindex"), `${path} is indexable`);
  }
  for (const path of demoRoutes) {
    const response = await request(path);
    const body = await response.text();
    assert(/<meta name="robots" content="noindex, nofollow"/i.test(body), `${path} lacks noindex`);
  }
  const securityResponse = await request("/");
  const requiredSecurityHeaders = {
    "content-security-policy": ["default-src 'self'", "frame-ancestors 'none'", "object-src 'none'"],
    "permissions-policy": ["camera=()", "microphone=()", "geolocation=()", "payment=()"],
    "referrer-policy": ["strict-origin-when-cross-origin"],
    "strict-transport-security": ["max-age=63072000", "includeSubDomains", "preload"],
    "x-content-type-options": ["nosniff"],
    "x-frame-options": ["DENY"],
  };
  for (const [header, directives] of Object.entries(requiredSecurityHeaders)) {
    const value = securityResponse.headers.get(header);
    assert(value, `homepage omitted ${header}`);
    for (const directive of directives) {
      assert(value.includes(directive), `${header} omitted ${directive}`);
    }
  }
  assert((await request("/stocks/NOT-A-SYMBOL")).status === 404, "unknown stock did not 404");
  const sitemap = await (await request("/sitemap.xml")).text();
  assert(sitemap.includes("/methodology"), "sitemap omitted public methodology");
  assert(!sitemap.includes("/predictions"), "sitemap exposed synthetic predictions");
  const robots = await (await request("/robots.txt")).text();
  assert(robots.includes("Disallow: /research"), "robots omitted internal route policy");
  assert(robots.includes("Disallow: /predictions"), "robots omitted demo route policy");
  const homepage = await securityResponse.text();
  assert(homepage.includes('rel="manifest" href="/manifest.webmanifest"'), "homepage omitted manifest");
  const structuredMatch = homepage.match(/<script type="application\/ld\+json">(.*?)<\/script>/);
  assert(structuredMatch, "homepage omitted structured data");
  const structuredData = JSON.parse(structuredMatch[1]);
  assert(structuredData["@type"] === "WebSite", "structured data misclassified the product");
  assert(structuredData.url === `${origin}/`, "structured data used a non-canonical URL");
  const manifestResponse = await request("/manifest.webmanifest");
  assert(manifestResponse.status === 200, "web manifest unavailable");
  assert(manifestResponse.headers.get("content-type")?.includes("application/manifest+json"), "web manifest has wrong content type");
  const manifest = await manifestResponse.json();
  assert(manifest.name === "Verified Edge — Market Prediction Intelligence", "web manifest has wrong identity");
  assert(manifest.start_url === "/" && manifest.scope === "/", "web manifest escapes public root");
  for (const [property, expectedType] of [
    ["og:image", "image/png"],
    ["twitter:image", "image/png"],
  ]) {
    const match = homepage.match(new RegExp(`<meta (?:property|name)="${property}" content="([^"]+)"`));
    assert(match, `homepage omitted ${property}`);
    const imageResponse = await fetch(new URL(match[1].replaceAll("&amp;", "&"), origin));
    assert(imageResponse.status === 200, `${property} image unavailable`);
    assert(imageResponse.headers.get("content-type")?.includes(expectedType), `${property} has wrong content type`);
    assert((await imageResponse.arrayBuffer()).byteLength > 10_000, `${property} image is unexpectedly small`);
  }
  const appleIconMatch = homepage.match(/<link rel="apple-touch-icon" href="([^"]+)"/);
  assert(appleIconMatch, "homepage omitted Apple touch icon");
  const appleIconResponse = await fetch(new URL(appleIconMatch[1].replaceAll("&amp;", "&"), origin));
  assert(appleIconResponse.status === 200, "Apple touch icon unavailable");
  assert(appleIconResponse.headers.get("content-type")?.includes("image/png"), "Apple touch icon has wrong content type");
  console.log(`Public release smoke checks passed; ${linkedPaths.size} internal links verified.`);
} finally {
  server.kill("SIGTERM");
}
