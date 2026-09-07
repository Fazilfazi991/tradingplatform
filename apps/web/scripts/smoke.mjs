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
  for (const path of publicRoutes) {
    const response = await request(path);
    const body = await response.text();
    assert(response.status === 200, `${path} returned ${response.status}`);
    assert(/<h1[ >]/i.test(body), `${path} has no rendered H1`);
    assert(!body.includes("Application error"), `${path} rendered an application error`);
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
  assert((await request("/stocks/NOT-A-SYMBOL")).status === 404, "unknown stock did not 404");
  const sitemap = await (await request("/sitemap.xml")).text();
  assert(sitemap.includes("/methodology"), "sitemap omitted public methodology");
  assert(!sitemap.includes("/predictions"), "sitemap exposed synthetic predictions");
  const robots = await (await request("/robots.txt")).text();
  assert(robots.includes("Disallow: /research"), "robots omitted internal route policy");
  assert(robots.includes("Disallow: /predictions"), "robots omitted demo route policy");
  console.log("Public release smoke checks passed.");
} finally {
  server.kill("SIGTERM");
}
