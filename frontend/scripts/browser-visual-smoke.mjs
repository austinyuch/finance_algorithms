import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const htmlPath = join(root, "out", "index.html");
const screenshotPath = join(root, "out", "browser-visual.png");
const evidencePath = join(root, "out", "browser-visual.json");
const chromium = process.env.CHROMIUM_BIN || "/snap/bin/chromium";

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

if (!existsSync(htmlPath)) {
  throw new Error("browser visual smoke requires npm run visual output first");
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
console.log(`browser-visual-smoke: PASS ${evidence.screenshotHash}`);
