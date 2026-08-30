import { chromium } from "file:///C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const base = "http://localhost:3000";
const routes = ["/", "/predictions", "/stocks/RELIANCE", "/intelligence", "/sectors", "/historical", "/models", "/research", "/data-health", "/settings"];
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const errors = [];
const results = [];

async function verify(viewport, prefix, screenshot) {
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`${prefix} console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`${prefix} page: ${error.message}`));
  for (const route of routes) {
    const response = await page.goto(`${base}${route}`, { waitUntil: "domcontentloaded" });
    results.push({
      viewport: prefix,
      route,
      status: response?.status(),
      content: (await page.locator("body").innerText()).length,
      overflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
      overlay: await page.locator("[data-nextjs-dialog]").count(),
    });
  }
  await page.goto(base, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1600);
  await page.screenshot({ path: screenshot, fullPage: true });
  await page.close();
}

await verify({ width: 1440, height: 1000 }, "desktop", "../../.impeccable/review/desktop.png");
await verify({ width: 390, height: 844 }, "mobile", "../../.impeccable/review/mobile.png");
await browser.close();

console.log(JSON.stringify({ results, errors }, null, 2));
if (errors.length || results.some((result) => result.status !== 200 || result.content < 100 || result.overflow || result.overlay)) process.exitCode = 1;
