import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { PNG } from "pngjs";

const root = process.cwd();
const htmlPath = join(root, "out", "index.html");
const screenshotPath = join(root, "out", "browser-visual.png");
const evidencePath = join(root, "out", "browser-visual.json");
const diffPath = join(root, "out", "browser-visual-diff.json");
const baselineImagePath = join(root, "visual-baselines", "browser-visual.png");
const chromium = process.env.CHROMIUM_BIN || "/snap/bin/chromium";
const maxMismatchRatio = Number(process.env.QUANTLAB_BROWSER_VISUAL_MAX_MISMATCH_RATIO || "0.001");

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function readPng(path) {
  return PNG.sync.read(readFileSync(path));
}

function comparePixels(baseline, current) {
  if (baseline.width !== current.width || baseline.height !== current.height) {
    throw new Error(
      `browser visual baseline dimensions changed: baseline=${baseline.width}x${baseline.height} current=${current.width}x${current.height}`,
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

if (!existsSync(htmlPath)) {
  throw new Error("browser visual smoke requires npm run visual output first");
}
if (!existsSync(baselineImagePath)) {
  throw new Error("browser visual smoke requires frontend/visual-baselines/browser-visual.png baseline");
}
if (!Number.isFinite(maxMismatchRatio) || maxMismatchRatio < 0 || maxMismatchRatio > 1) {
  throw new Error("QUANTLAB_BROWSER_VISUAL_MAX_MISMATCH_RATIO must be within [0,1]");
}
mkdirSync(join(root, "out"), { recursive: true });

const result = spawnSync(chromium, [
  "--headless",
  "--no-sandbox",
  "--disable-gpu",
  "--window-size=1440,900",
  `--screenshot=${screenshotPath}`,
  `file://${htmlPath}`,
], { encoding: "utf8" });

if (result.status !== 0 || !existsSync(screenshotPath)) {
  throw new Error(`chromium screenshot failed: ${result.stderr || result.stdout}`);
}

const evidence = {
  status: "proven",
  claimBoundary: "no_alpha_claim",
  screenshotHash: sha256(screenshotPath),
  viewport: "desktop-1440x900",
  source: "chromium-headless",
  observedAt: new Date().toISOString(),
};
writeFileSync(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
const pixelDiff = comparePixels(readPng(baselineImagePath), readPng(screenshotPath));
const baselineImageHash = sha256(baselineImagePath);
const diff = {
  artifactKind: "browser_visual_diff",
  claimBoundary: "no_alpha_claim",
  status: pixelDiff.mismatchRatio <= maxMismatchRatio ? "passed" : "failed",
  baselineHash: baselineImageHash,
  currentHash: evidence.screenshotHash,
  baselineImageHash,
  currentImageHash: evidence.screenshotHash,
  mismatchedPixels: pixelDiff.mismatchedPixels,
  totalPixels: pixelDiff.totalPixels,
  mismatchRatio: pixelDiff.mismatchRatio,
  maxMismatchRatio,
  viewport: evidence.viewport,
  source: evidence.source,
};
writeFileSync(diffPath, `${JSON.stringify(diff, null, 2)}\n`, "utf8");
if (diff.status !== "passed") {
  throw new Error(`browser visual diff failed: mismatchRatio=${pixelDiff.mismatchRatio}`);
}
console.log(`browser-visual-smoke: PASS ${evidence.screenshotHash} mismatchRatio=${pixelDiff.mismatchRatio}`);
