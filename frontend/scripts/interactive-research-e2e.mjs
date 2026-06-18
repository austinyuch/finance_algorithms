import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { PNG } from "pngjs";

const root = process.cwd();
const htmlPath = join(root, "out", "index.html");
const screenshotPath = join(root, "out", "interactive-research-failclosed.png");
const evidencePath = join(root, "out", "interactive-research-e2e.json");
const baselinePath = join(root, "visual-baselines", "interactive-research-failclosed.png");
const chromiumCandidates = [
  process.env.CHROMIUM_BIN,
  "/opt/google/chrome/chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/snap/bin/chromium",
].filter(Boolean);
const chromium = chromiumCandidates.find((candidate) => existsSync(candidate));
if (!chromium) {
  throw new Error(`chromium executable not found; checked ${chromiumCandidates.join(", ")}`);
}
const updateBaseline = process.env.QUANTLAB_INTERACTIVE_RESEARCH_E2E_UPDATE_BASELINE === "1";
const maxMismatchRatio = Number(process.env.QUANTLAB_INTERACTIVE_RESEARCH_E2E_MAX_MISMATCH_RATIO || "0.001");
const host = "127.0.0.1";

function sha256Bytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function sha256File(path) {
  return sha256Bytes(readFileSync(path));
}

function readPng(path) {
  return PNG.sync.read(readFileSync(path));
}

function comparePixels(baseline, current) {
  if (baseline.width !== current.width || baseline.height !== current.height) {
    throw new Error(
      `interactive research e2e baseline dimensions changed: baseline=${baseline.width}x${baseline.height} current=${current.width}x${current.height}`,
    );
  }
  const totalPixels = baseline.width * baseline.height;
  let mismatchedPixels = 0;
  for (let offset = 0; offset < baseline.data.length; offset += 4) {
    if (
      baseline.data[offset] !== current.data[offset] ||
      baseline.data[offset + 1] !== current.data[offset + 1] ||
      baseline.data[offset + 2] !== current.data[offset + 2] ||
      baseline.data[offset + 3] !== current.data[offset + 3]
    ) {
      mismatchedPixels += 1;
    }
  }
  return {
    mismatchedPixels,
    totalPixels,
    mismatchRatio: mismatchedPixels / totalPixels,
  };
}

async function reservePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        server.close();
        reject(new Error("could not reserve a debugging port"));
        return;
      }
      const { port } = address;
      server.close(() => resolve(port));
    });
  });
}

async function waitForJson(url, child) {
  const deadline = Date.now() + 10_000;
  let lastError;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`chromium exited before DevTools became ready: ${child.exitCode}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) {
        return response.json();
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw lastError || new Error(`DevTools endpoint did not become ready: ${url}`);
}

async function waitForHttp(url, child) {
  const deadline = Date.now() + 20_000;
  let lastError;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`server exited before becoming ready: ${child.exitCode}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw lastError || new Error(`server did not become ready: ${url}`);
}

function createCdpClient(webSocketDebuggerUrl) {
  let nextId = 1;
  const pending = new Map();
  const socket = new WebSocket(webSocketDebuggerUrl);

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) {
        reject(new Error(message.error.message));
      } else {
        resolve(message.result);
      }
    }
  });

  return new Promise((resolve, reject) => {
    socket.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const id = nextId++;
          socket.send(JSON.stringify({ id, method, params }));
          return new Promise((resolveCommand, rejectCommand) => {
            pending.set(id, { resolve: resolveCommand, reject: rejectCommand });
          });
        },
        close() {
          socket.close();
        },
      });
    });
    socket.addEventListener("error", () => reject(new Error("DevTools WebSocket failed")));
  });
}

async function evaluate(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "browser evaluation failed");
  }
  return result.result.value;
}

async function runBrowserFlow() {
  const appPort = await reservePort();
  const debugPort = await reservePort();
  const app = spawn("npm", ["run", "start", "--", "--hostname", host, "--port", String(appPort)], {
    stdio: ["ignore", "ignore", "pipe"],
  });
  await waitForHttp(`http://${host}:${appPort}/`, app);
  const child = spawn(chromium, [
    "--headless",
    "--no-sandbox",
    "--disable-gpu",
    "--window-size=1440,900",
    `--remote-debugging-port=${debugPort}`,
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });

  try {
    const targets = await waitForJson(`http://127.0.0.1:${debugPort}/json`, child);
    const target = targets.find((item) => item.type === "page") ?? targets[0];
    if (!target?.webSocketDebuggerUrl) {
      throw new Error("DevTools page target was not available");
    }
    const client = await createCdpClient(target.webSocketDebuggerUrl);
    try {
      await client.send("Page.enable");
      await client.send("Runtime.enable");
      await client.send("Page.navigate", { url: `http://${host}:${appPort}/` });
      await evaluate(client, `
        (async () => {
          const deadline = Date.now() + 10000;
          while (Date.now() < deadline) {
            const panel = document.querySelector('[data-section="interactive-research"]');
            if (panel?.dataset.hydrated === 'true' && panel.querySelector('[data-control="seed"]') && panel.textContent.includes('static_replay')) {
              return true;
            }
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
          throw new Error('interactive research panel did not hydrate');
        })()
      `);
      const before = await evaluate(client, `
        (() => {
          const panel = document.querySelector('[data-section="interactive-research"]');
          return {
            status: panel.querySelector('.research-status')?.dataset.status,
            text: panel.textContent,
          };
        })()
      `);
      const after = await evaluate(client, `
        (async () => {
          const panel = document.querySelector('[data-section="interactive-research"]');
          const seedInput = panel.querySelector('[data-control="seed"]');
          if (!seedInput) {
            throw new Error('seed input not found');
          }
          const previousValue = seedInput.value;
          const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
          setter.call(seedInput, String(Number(seedInput.value) + 1));
          if (seedInput._valueTracker) {
            seedInput._valueTracker.setValue(previousValue);
          }
          seedInput.dispatchEvent(new Event('input', { bubbles: true }));
          seedInput.dispatchEvent(new Event('change', { bubbles: true }));
          const deadline = Date.now() + 5000;
          while (Date.now() < deadline) {
            const status = panel.querySelector('.research-status')?.dataset.status;
            if (status === 'fail_closed') {
              break;
            }
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
          return {
            status: panel.querySelector('.research-status')?.dataset.status,
            text: panel.textContent,
            hasEmptyState: panel.querySelector('.empty-state')?.textContent === 'fail_closed',
          };
        })()
      `);
      if (before.status !== "computed") {
        throw new Error(`interactive research e2e expected computed initial state, got ${before.status}`);
      }
      if (after.status !== "fail_closed" || !after.hasEmptyState || !after.text.includes("No deterministic replay artifact")) {
        throw new Error(
          `interactive research e2e did not fail closed after unsupported parameter change: ${JSON.stringify(after)}`,
        );
      }
      const screenshot = await client.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
      const screenshotBytes = Buffer.from(screenshot.data, "base64");
      writeFileSync(screenshotPath, screenshotBytes);
      return { before, after, screenshotHash: sha256Bytes(screenshotBytes) };
    } finally {
      client.close();
    }
  } finally {
    child.kill("SIGTERM");
    app.kill("SIGTERM");
  }
}

if (!existsSync(htmlPath)) {
  throw new Error("interactive research e2e requires npm run visual output first");
}
if (!Number.isFinite(maxMismatchRatio) || maxMismatchRatio < 0 || maxMismatchRatio > 1) {
  throw new Error("QUANTLAB_INTERACTIVE_RESEARCH_E2E_MAX_MISMATCH_RATIO must be within [0,1]");
}
mkdirSync(join(root, "out"), { recursive: true });

const flow = await runBrowserFlow();
if (updateBaseline || !existsSync(baselinePath)) {
  writeFileSync(baselinePath, readFileSync(screenshotPath));
}
const pixelDiff = comparePixels(readPng(baselinePath), readPng(screenshotPath));
const evidence = {
  artifactKind: "interactive_research_browser_e2e",
  claimBoundary: "no_alpha_claim",
  mode: "static_replay",
  status: pixelDiff.mismatchRatio <= maxMismatchRatio ? "passed" : "failed",
  initialStatus: flow.before.status,
  afterParameterChangeStatus: flow.after.status,
  failClosedMessageObserved: flow.after.text.includes("No deterministic replay artifact"),
  screenshotHash: flow.screenshotHash,
  baselineHash: sha256File(baselinePath),
  mismatchedPixels: pixelDiff.mismatchedPixels,
  totalPixels: pixelDiff.totalPixels,
  mismatchRatio: pixelDiff.mismatchRatio,
  maxMismatchRatio,
  viewport: "desktop-1440x900",
  source: "chromium-headless-devtools",
  observedAt: new Date().toISOString(),
};
writeFileSync(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
if (evidence.status !== "passed") {
  throw new Error(`interactive research e2e VRT failed: mismatchRatio=${pixelDiff.mismatchRatio}`);
}
console.log(`interactive-research-e2e: PASS ${evidence.screenshotHash} mismatchRatio=${pixelDiff.mismatchRatio}`);
process.exit(0);
