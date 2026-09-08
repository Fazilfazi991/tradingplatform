import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const host = "127.0.0.1";
const port = process.env.PUBLIC_BOUNDARY_QA_PORT ?? "3212";
const origin = `http://${host}:${port}`;
const webRoot = fileURLToPath(new URL("..", import.meta.url));
const configPath = fileURLToPath(
  new URL("../../../config/public-boundary-audit.json", import.meta.url),
);
const nextCli = fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url));
const config = JSON.parse(await readFile(configPath, "utf8"));
const forbiddenText = [
  ...config.forbidden_text,
  ["BEGIN", "PRIVATE", "KEY"].join(" "),
  ["BEGIN", "RSA", "PRIVATE", "KEY"].join(" "),
];
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
      if ((await fetch(origin)).status === 200) return;
    } catch {
      // The production listener is not ready yet.
    }
    await delay(100);
  }
  throw new Error(`server readiness timed out\n${serverOutput}`);
}

function inspectText(label, text, failures) {
  for (const forbidden of forbiddenText) {
    if (text.includes(forbidden)) failures.push(`${label}: exposed forbidden marker ${forbidden}`);
  }
  if (/file:\/\/\/(?:[A-Za-z]:\/|home\/|Users\/)/i.test(text)) {
    failures.push(`${label}: exposed local file URI`);
  }
  if (/[A-Za-z]:\\Users\\[^\\"' ]+/i.test(text)) failures.push(`${label}: exposed Windows user path`);
}

const failures = [];
const publicAssets = new Set();
try {
  await waitUntilReady();
  for (const route of config.public_routes) {
    const response = await fetch(`${origin}${route}`, { redirect: "manual" });
    const body = await response.text();
    if (response.status !== 200) failures.push(`${route}: expected 200, received ${response.status}`);
    inspectText(`public HTML ${route}`, body, failures);
    for (const match of body.matchAll(/(?:src|href)=["']([^"']+)["']/gi)) {
      const asset = match[1].replaceAll("&amp;", "&");
      if (asset.startsWith("/_next/static/")) publicAssets.add(new URL(asset, origin).pathname);
    }
  }

  for (const route of config.protected_routes) {
    const response = await fetch(`${origin}${route}`, { redirect: "manual" });
    const body = await response.text();
    if (response.status !== 401) failures.push(`${route}: expected 401, received ${response.status}`);
    if (response.headers.get("cache-control") !== "no-store") failures.push(`${route}: missing no-store`);
    inspectText(`protected denial ${route}`, body, failures);
  }

  let inspectedTextAssets = 0;
  let sourceMapsExposed = 0;
  for (const asset of publicAssets) {
    const response = await fetch(`${origin}${asset}`, { redirect: "manual" });
    if (response.status !== 200) {
      failures.push(`${asset}: public asset returned ${response.status}`);
      continue;
    }
    const type = response.headers.get("content-type") ?? "";
    if (type.includes("javascript") || type.includes("text/css")) {
      const body = await response.text();
      inspectedTextAssets += 1;
      inspectText(`public asset ${asset}`, body, failures);
      if (/sourceMappingURL=/i.test(body)) failures.push(`${asset}: embeds a source-map reference`);
    }
    if (asset.endsWith(".js")) {
      const mapResponse = await fetch(`${origin}${asset}.map`, { redirect: "manual" });
      if (mapResponse.status === 200) {
        sourceMapsExposed += 1;
        failures.push(`${asset}.map: production source map is publicly exposed`);
      }
    }
  }

  console.log(JSON.stringify({
    profile: "LOCAL_PRODUCTION_PUBLIC_BOUNDARY",
    public_routes: config.public_routes.length,
    protected_routes: config.protected_routes.length,
    public_assets: publicAssets.size,
    inspected_text_assets: inspectedTextAssets,
    source_maps_exposed: sourceMapsExposed,
    failures,
  }, null, 2));
  if (failures.length) process.exitCode = 1;
} finally {
  server.kill("SIGTERM");
}
