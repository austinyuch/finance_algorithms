import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";

import { Dashboard } from "../components/Dashboard";
import {
  assertVisualSnapshotMatchesBaseline,
  buildPublicDemoManifest,
  buildVisualSnapshot,
} from "../lib/public-demo";
import { getShowcaseDashboard } from "../lib/showcase-fixture";

const root = process.cwd();
const outDir = process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR
  ? join(root, process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR)
  : join(root, "out");
const baselinePath = join(root, "visual-baselines", "showcase.visual.json");

const dashboard = getShowcaseDashboard();
const html = renderToStaticMarkup(<Dashboard data={dashboard} />);
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>QuantLab Showcase</title></head><body>${html}</body></html>`;
const manifest = buildPublicDemoManifest(dashboard, {
  pagesConfigured: true,
  pagesStatus: process.env.QUANTLAB_PUBLIC_HOSTING_PAGES_STATUS,
  httpStatus: process.env.QUANTLAB_PUBLIC_HOSTING_HTTP_STATUS
    ? Number(process.env.QUANTLAB_PUBLIC_HOSTING_HTTP_STATUS)
    : undefined,
  observedAt: process.env.QUANTLAB_PUBLIC_HOSTING_OBSERVED_AT,
});
const snapshot = buildVisualSnapshot(html, dashboard);

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, "index.html"), page, "utf8");
writeFileSync(join(outDir, "showcase.json"), `${JSON.stringify(dashboard, null, 2)}\n`, "utf8");
writeFileSync(join(outDir, "deployment-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
writeFileSync(join(outDir, "visual-snapshot.json"), `${JSON.stringify(snapshot, null, 2)}\n`, "utf8");

const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
assertVisualSnapshotMatchesBaseline(snapshot, baseline);
console.log(`export-public-demo: PASS ${outDir}`);
