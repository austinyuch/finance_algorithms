import { spawn } from "node:child_process";
import { DEFAULT_SMOKE_HOST, selectSmokePort } from "./smoke-port.mjs";
import { assertHtmlMatchesPayload, assertPayload } from "./smoke-assertions.mjs";

const host = DEFAULT_SMOKE_HOST;
const port = await selectSmokePort(process.env, host);
const baseUrl = `http://${host}:${port}`;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchText(path) {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }
  return response.text();
}

async function waitForServer() {
  const deadline = Date.now() + 20_000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      await fetchText("/");
      return;
    } catch (error) {
      lastError = error;
      await sleep(300);
    }
  }
  throw lastError || new Error("server did not become ready");
}

const server = spawn("npm", ["run", "start", "--", "--port", String(port)], {
  stdio: "inherit",
});

try {
  await waitForServer();
  const html = await fetchText("/");
  const payloadText = await fetchText("/api/showcase");
  const payload = JSON.parse(payloadText);
  assertPayload(payload);
  assertHtmlMatchesPayload(html, payload);
  console.log(`public-demo-smoke: PASS ${baseUrl}`);
} finally {
  server.kill("SIGTERM");
}
