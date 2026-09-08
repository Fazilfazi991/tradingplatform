import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const host = "127.0.0.1";
const port = "3230";
const origin = `http://${host}:${port}`;
const root = fileURLToPath(new URL("..", import.meta.url));
const nextCli = fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url));
const routes = [
  "/", "/predictions", "/stocks/RELIANCE", "/fusion", "/models", "/methodology",
  "/data-sources", "/validation", "/about", "/faq", "/risk", "/privacy", "/terms",
  "/contact",
];
const server = spawn(process.execPath, [nextCli, "start", "--hostname", host, "--port", port], {
  cwd: root,
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
      if ((await fetch(origin)).status === 200) return;
    } catch {
      // The listener is not ready yet.
    }
    await delay(100);
  }
  throw new Error(`server readiness timed out\n${serverOutput}`);
}

const browser = await chromium.launch({
  headless: true,
  channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL ?? "chrome",
});
const failures = [];

function record(path, check, details = "") {
  failures.push(`${path}: ${check}${details ? ` (${details})` : ""}`);
}

try {
  await waitUntilReady();
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await desktop.newPage();

  for (const path of routes) {
    const response = await page.goto(`${origin}${path}`, { waitUntil: "networkidle" });
    if (response?.status() !== 200) record(path, "HTTP status", String(response?.status()));
    const result = await page.evaluate(() => {
      const visible = (element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      const interactiveName = (element) =>
        element.getAttribute("aria-label")?.trim()
        || element.getAttribute("aria-labelledby")?.trim()
        || element.textContent?.trim()
        || "";
      const controlName = (element) =>
        element.getAttribute("aria-label")?.trim()
        || element.getAttribute("aria-labelledby")?.trim()
        || element.getAttribute("title")?.trim()
        || (element.id ? document.querySelector(`label[for="${CSS.escape(element.id)}"]`)?.textContent?.trim() : "")
        || "";
      const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
      const duplicates = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
      const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")]
        .filter(visible)
        .map((heading) => Number(heading.tagName.slice(1)));
      const headingSkips = headings.filter((level, index) => index > 0 && level > headings[index - 1] + 1);
      return {
        buttons: [...document.querySelectorAll("button")].filter(visible).filter((element) => !interactiveName(element)).length,
        controls: [...document.querySelectorAll("input,select,textarea")].filter(visible).filter((element) => !controlName(element)).length,
        images: [...document.querySelectorAll("img")].filter((element) => !element.hasAttribute("alt")).length,
        navs: [...document.querySelectorAll("nav")].filter(visible).filter((element) =>
          !element.getAttribute("aria-label")?.trim() && !element.getAttribute("aria-labelledby")?.trim(),
        ).length,
        mains: document.querySelectorAll("main").length,
        h1s: [...document.querySelectorAll("h1")].filter(visible).length,
        duplicates,
        headingSkips: headingSkips.length,
      };
    });
    if (result.buttons) record(path, "unlabelled buttons", String(result.buttons));
    if (result.controls) record(path, "unlabelled form controls", String(result.controls));
    if (result.images) record(path, "images without alt", String(result.images));
    if (result.navs) record(path, "unlabelled navigation landmarks", String(result.navs));
    if (result.mains !== 1) record(path, "main landmark count", String(result.mains));
    if (result.h1s !== 1) record(path, "visible H1 count", String(result.h1s));
    if (result.duplicates.length) record(path, "duplicate IDs", result.duplicates.join(", "));
    if (result.headingSkips) record(path, "heading-level skips", String(result.headingSkips));
  }

  await page.goto(origin, { waitUntil: "networkidle" });
  await page.keyboard.press("Tab");
  const skip = await page.evaluate(() => {
    const active = document.activeElement;
    const style = active ? getComputedStyle(active) : undefined;
    const target = active instanceof HTMLAnchorElement
      ? document.querySelector(active.getAttribute("href") ?? "")
      : null;
    return {
      className: active?.className ?? "",
      height: active?.getBoundingClientRect().height ?? 0,
      outline: Number.parseFloat(style?.outlineWidth ?? "0"),
      targetFocusable: target?.getAttribute("tabindex") === "-1",
    };
  });
  if (skip.className !== "skip-link") record("/", "skip link is not first focus target");
  if (skip.height < 44) record("/", "skip link target is below 44px", String(skip.height));
  if (skip.outline < 2) record("/", "skip link lacks visible focus outline", String(skip.outline));
  if (!skip.targetFocusable) record("/", "skip-link target is not programmatically focusable");
  await desktop.close();

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobilePage = await mobile.newPage();
  for (const path of routes) {
    await mobilePage.goto(`${origin}${path}`, { waitUntil: "networkidle" });
    const undersized = await mobilePage.locator("a:visible,button:visible").evaluateAll((elements) =>
      elements
        .map((element) => ({ text: element.textContent?.trim().slice(0, 40), height: element.getBoundingClientRect().height }))
        .filter((item) => item.height < 44),
    );
    if (undersized.length) record(path, "mobile interactive targets below 44px", JSON.stringify(undersized));
  }
  await mobile.close();

  for (const [label, width] of [["200%", 640], ["400%", 320]]) {
    const zoomContext = await browser.newContext({ viewport: { width, height: 1024 } });
    const zoomPage = await zoomContext.newPage();
    for (const path of routes) {
      await zoomPage.goto(`${origin}${path}`, { waitUntil: "networkidle" });
      const overflow = await zoomPage.evaluate(() =>
        document.documentElement.scrollWidth > document.documentElement.clientWidth,
      );
      if (overflow) record(path, `${label} reflow horizontal overflow`);
    }
    await zoomContext.close();
  }

  const forced = await browser.newContext({ viewport: { width: 1280, height: 800 }, forcedColors: "active" });
  const forcedPage = await forced.newPage();
  for (const path of routes) {
    await forcedPage.goto(`${origin}${path}`, { waitUntil: "networkidle" });
    const state = await forcedPage.evaluate(() => ({
      text: document.body.innerText.trim().length,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      forced: matchMedia("(forced-colors: active)").matches,
    }));
    if (!state.forced) record(path, "forced-colors emulation inactive");
    if (state.text < 100) record(path, "forced-colors content missing", String(state.text));
    if (state.overflow) record(path, "forced-colors horizontal overflow");
  }
  await forced.close();

  const reduced = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: "reduce" });
  const reducedPage = await reduced.newPage();
  for (const path of ["/", "/fusion"]) {
    await reducedPage.goto(`${origin}${path}`, { waitUntil: "networkidle" });
    const moving = await reducedPage.locator("*").evaluateAll((elements) => elements.filter((element) => {
      const style = getComputedStyle(element);
      return style.animationName !== "none" || style.transitionDuration.split(",").some((value) => Number.parseFloat(value) > 0);
    }).length);
    if (moving) record(path, "motion remains under reduced-motion preference", String(moving));
  }
  await reduced.close();

  console.log(JSON.stringify({ routes: routes.length, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
} finally {
  await browser.close();
  server.kill("SIGTERM");
}
