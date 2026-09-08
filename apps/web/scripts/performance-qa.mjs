import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const host = "127.0.0.1";
const port = process.env.PERFORMANCE_QA_PORT ?? "3211";
const origin = `http://${host}:${port}`;
const webRoot = fileURLToPath(new URL("..", import.meta.url));
const configPath = fileURLToPath(
  new URL("../../../config/web-performance-budgets.json", import.meta.url),
);
const nextCli = fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url));
const config = JSON.parse(await readFile(configPath, "utf8"));
const server = spawn(process.execPath, [nextCli, "start", "--hostname", host, "--port", port], {
  cwd: webRoot,
  env: { ...process.env, NODE_ENV: "production" },
  stdio: ["ignore", "pipe", "pipe"],
});

let serverOutput = "";
server.stdout.on("data", (chunk) => { serverOutput += chunk.toString(); });
server.stderr.on("data", (chunk) => { serverOutput += chunk.toString(); });

async function waitUntilReady() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`server exited before readiness\n${serverOutput}`);
    try {
      const response = await fetch(origin);
      if (response.status === 200) return;
    } catch {
      // The production listener is not ready yet.
    }
    await delay(100);
  }
  throw new Error(`server readiness timed out\n${serverOutput}`);
}

function exceeded(metric, actual, maximum, route) {
  return actual > maximum ? `${route}: ${metric} ${actual} exceeded ${maximum}` : undefined;
}

let browser;
try {
  await waitUntilReady();
  browser = await chromium.launch({
    headless: true,
    channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL ?? "chrome",
  });
  const results = [];
  const failures = [];

  for (const route of config.routes) {
    const context = await browser.newContext({ viewport: config.viewport });
    const page = await context.newPage();
    await page.addInitScript(() => {
      window.__verifiedEdgePerformance = { cls: 0, lcp: 0, layoutShifts: [] };
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            window.__verifiedEdgePerformance.cls += entry.value;
            window.__verifiedEdgePerformance.layoutShifts.push({
              value: Math.round(entry.value * 10000) / 10000,
              sources: entry.sources.map((source) => ({
                node: source.node instanceof Element
                  ? `${source.node.tagName.toLowerCase()}${source.node.id ? `#${source.node.id}` : ""}${[...source.node.classList].map((name) => `.${name}`).join("")}`
                  : "unknown",
                previous: source.previousRect.toJSON(),
                current: source.currentRect.toJSON(),
              })),
            });
          }
        }
      }).observe({ type: "layout-shift", buffered: true });
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const latest = entries.at(-1);
        if (latest) window.__verifiedEdgePerformance.lcp = latest.startTime;
      }).observe({ type: "largest-contentful-paint", buffered: true });
    });
    const response = await page.goto(`${origin}${route}`, { waitUntil: "networkidle" });
    await delay(100);
    if (response?.status() !== 200) failures.push(`${route}: HTTP ${response?.status() ?? "missing"}`);
    const { metrics, layoutShifts } = await page.evaluate(() => {
      const navigation = performance.getEntriesByType("navigation")[0];
      const resources = performance.getEntriesByType("resource");
      const bytes = (suffix) => resources
        .filter((resource) => new URL(resource.name).pathname.endsWith(suffix))
        .reduce((total, resource) => total + resource.encodedBodySize, 0);
      const total = resources.reduce((sum, resource) => sum + resource.encodedBodySize, 0)
        + navigation.encodedBodySize;
      return {
        metrics: {
          navigation_response_ms: Math.round(navigation.responseEnd * 100) / 100,
          largest_contentful_paint_ms:
            Math.round(window.__verifiedEdgePerformance.lcp * 100) / 100,
          cumulative_layout_shift:
            Math.round(window.__verifiedEdgePerformance.cls * 10000) / 10000,
          document_encoded_bytes: navigation.encodedBodySize,
          javascript_encoded_bytes: bytes(".js"),
          css_encoded_bytes: bytes(".css"),
          font_encoded_bytes: resources
            .filter((resource) => /\.(woff2?|ttf|otf)$/.test(new URL(resource.name).pathname))
            .reduce((sum, resource) => sum + resource.encodedBodySize, 0),
          total_encoded_bytes: total,
        },
        layoutShifts: window.__verifiedEdgePerformance.layoutShifts,
      };
    });
    for (const [metric, actual] of Object.entries(metrics)) {
      if (!Number.isFinite(actual)) failures.push(`${route}: ${metric} was not measurable`);
    }
    if (metrics.navigation_response_ms <= 0) failures.push(`${route}: navigation timing was empty`);
    if (metrics.largest_contentful_paint_ms <= 0) failures.push(`${route}: LCP was empty`);
    for (const [metric, maximum] of Object.entries(config.budgets)) {
      const failure = exceeded(metric, metrics[metric], maximum, route);
      if (failure) failures.push(failure);
    }
    const includeShiftSources = metrics.cumulative_layout_shift
      > config.budgets.cumulative_layout_shift;
    results.push({
      route,
      ...metrics,
      ...(includeShiftSources ? { layout_shift_sources: layoutShifts } : {}),
    });
    await context.close();
  }

  console.log(JSON.stringify({ profile: config.profile, budgets: config.budgets, results, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
