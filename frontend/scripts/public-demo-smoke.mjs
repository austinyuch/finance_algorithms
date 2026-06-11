import { spawn } from "node:child_process";

const host = "127.0.0.1";
const port = Number(process.env.QUANTLAB_FRONTEND_SMOKE_PORT || 3044);
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

function assertPayload(payload) {
  if (payload.claimBoundary !== "no_alpha_claim") {
    throw new Error("dashboard payload overclaims alpha");
  }
  if (payload.demoReadiness?.publicHosting !== "not_proven") {
    throw new Error("public hosting must remain not_proven without deployed URL evidence");
  }
  if (payload.demoReadiness?.visualRegression !== "not_proven") {
    throw new Error("visual regression must remain not_proven without screenshot baseline evidence");
  }
  if (payload.demoReadiness?.dependencyAudit !== "clean") {
    throw new Error("dependency audit must be clean");
  }
  if (payload.experiments?.[0]?.readiness !== "registry_only") {
    throw new Error("experiment registry must remain registry_only");
  }
}

const server = spawn("npm", ["run", "start", "--", "--port", String(port)], {
  stdio: "inherit",
});

try {
  await waitForServer();
  const html = await fetchText("/");
  if (!html.includes("Experiment Registry") || !html.includes("local_demo_only")) {
    throw new Error("dashboard HTML smoke did not include expected sections");
  }
  const payloadText = await fetchText("/api/showcase");
  assertPayload(JSON.parse(payloadText));
  console.log(`public-demo-smoke: PASS ${baseUrl}`);
} finally {
  server.kill("SIGTERM");
}
