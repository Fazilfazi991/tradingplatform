import { spawn } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const managedServer = !process.env.VISUAL_QA_BASE_URL;
const base = process.env.VISUAL_QA_BASE_URL ?? "http://127.0.0.1:3240";
const root = fileURLToPath(new URL("..", import.meta.url));
const nextCli = fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url));
const routes = [
  "/", "/predictions", "/stocks/RELIANCE", "/fusion", "/models", "/methodology",
  "/data-sources", "/validation", "/about", "/faq", "/risk", "/privacy", "/terms",
  "/contact",
];
const viewports = [
  ["1920", { width: 1920, height: 1080 }],
  ["1440", { width: 1440, height: 900 }],
  ["1366", { width: 1366, height: 768 }],
  ["1024", { width: 1024, height: 768 }],
  ["430", { width: 430, height: 932 }],
  ["390", { width: 390, height: 844 }],
  ["375", { width: 375, height: 812 }],
];
const output = resolve(process.cwd(), "../../.impeccable/review");
await mkdir(output, { recursive: true });
const server = managedServer
  ? spawn(process.execPath, [nextCli, "start", "--hostname", "127.0.0.1", "--port", "3240"], {
      cwd: root,
      env: { ...process.env, NODE_ENV: "production" },
      stdio: ["ignore", "pipe", "pipe"],
    })
  : undefined;
let serverOutput = "";
server?.stdout.on("data", (chunk) => { serverOutput += chunk.toString(); });
server?.stderr.on("data", (chunk) => { serverOutput += chunk.toString(); });

async function waitUntilReady() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (server?.exitCode !== null && server?.exitCode !== undefined) {
      throw new Error(`server exited before readiness\n${serverOutput}`);
    }
    try {
      if ((await fetch(base)).status === 200) return;
    } catch {
      // The listener is not ready yet.
    }
    await delay(100);
  }
  throw new Error(`server readiness timed out\n${serverOutput}`);
}

await waitUntilReady();
const browser = await chromium.launch({
  headless: true,
  channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL ?? "chrome",
});
const errors = [];
const results = [];

try {
  for (const [label, viewport] of viewports) {
    const page = await browser.newPage({ viewport });
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(`${label} console: ${message.text()}`);
    });
    page.on("pageerror", (error) => errors.push(`${label} page: ${error.message}`));
    page.on("requestfailed", (request) => {
      const failure = request.failure()?.errorText ?? "failed";
      // Next prefetch requests are intentionally cancelled when this audit immediately
      // navigates to the next route. Transport failures other than cancellation remain fatal.
      if (failure !== "net::ERR_ABORTED") {
        errors.push(`${label} request: ${request.url()} ${failure}`);
      }
    });
    for (const route of routes) {
      const response = await page.goto(`${base}${route}`, { waitUntil: "networkidle" });
      results.push({
        viewport: label,
        route,
        status: response?.status(),
        content: (await page.locator("body").innerText()).length,
        h1: await page.locator("h1:visible").count(),
        overflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
        overlay: await page.locator("[data-nextjs-dialog]").count(),
      });
    }
    await page.goto(base, { waitUntil: "networkidle" });
    await page.screenshot({ path: resolve(output, `home-${label}.png`), fullPage: true });
    await page.goto(`${base}/methodology`, { waitUntil: "networkidle" });
    await page.screenshot({ path: resolve(output, `public-doc-${label}.png`), fullPage: true });
    await page.close();
  }

  const failed = results.filter(
    (result) =>
      result.status !== 200 || result.content < 100 || result.h1 !== 1 || result.overflow || result.overlay,
  );
  console.log(JSON.stringify({ checks: results.length, failed, errors }, null, 2));
  if (errors.length || failed.length) process.exitCode = 1;
} finally {
  await browser.close();
  server?.kill("SIGTERM");
}
