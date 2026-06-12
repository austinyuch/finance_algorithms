import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";

import { Dashboard } from "../components/Dashboard";
import {
  PUBLIC_SHOWCASE_URL,
  assertVisualSnapshotMatchesBaseline,
  buildPublicDemoManifest,
  buildVisualSnapshot,
  type PublicHostingProbe,
} from "../lib/public-demo";
import { getShowcaseDashboard } from "../lib/showcase-fixture";

const root = process.cwd();
const outDir = process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR
  ? join(root, process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR)
  : join(root, "out");
const baselinePath = join(root, "visual-baselines", "showcase.visual.json");

function hostingProbeFromEnv(): PublicHostingProbe | undefined {
  if (
    process.env.QUANTLAB_PUBLIC_HOSTING_PAGES_STATUS === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_HTTP_STATUS === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_OBSERVED_AT === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_DATA_HASH === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_TARGET_URL === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_ARTIFACT_KIND === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_CLAIM_BOUNDARY === undefined &&
    process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_DASHBOARD_CLAIM === undefined
  ) {
    return undefined;
  }
  return {
    pagesConfigured: true,
    pagesStatus: process.env.QUANTLAB_PUBLIC_HOSTING_PAGES_STATUS,
    httpStatus: process.env.QUANTLAB_PUBLIC_HOSTING_HTTP_STATUS
      ? Number(process.env.QUANTLAB_PUBLIC_HOSTING_HTTP_STATUS)
      : undefined,
    observedAt: process.env.QUANTLAB_PUBLIC_HOSTING_OBSERVED_AT,
    deployedDataHash: process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_DATA_HASH,
    deployedTargetUrl: process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_TARGET_URL,
    deployedArtifactKind: process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_ARTIFACT_KIND,
    deployedClaimBoundary: process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_CLAIM_BOUNDARY,
    deployedDashboardClaim: process.env.QUANTLAB_PUBLIC_HOSTING_DEPLOYED_DASHBOARD_CLAIM,
  };
}

function hostingProbeFromExistingArtifact(): PublicHostingProbe | undefined {
  const probePath = join(outDir, "public-hosting-probe.json");
  if (!existsSync(probePath)) {
    return undefined;
  }
  const parsed = JSON.parse(readFileSync(probePath, "utf8")) as Record<string, unknown>;
  if (parsed.targetUrl !== PUBLIC_SHOWCASE_URL) {
    throw new Error("public hosting probe targetUrl does not match showcase URL");
  }
  if (parsed.claimBoundary !== "no_alpha_claim") {
    throw new Error("public hosting probe must preserve no_alpha_claim");
  }
  if (parsed.status === "proven" && parsed.httpStatus !== 200) {
    throw new Error("public hosting probe cannot be proven without HTTP 200");
  }
  if (parsed.status === "proven" && typeof parsed.observedAt !== "string") {
    throw new Error("public hosting probe requires observedAt when proven");
  }
  if (parsed.status === "proven" && typeof parsed.deployedDataHash !== "string") {
    throw new Error("public hosting probe requires deployedDataHash when proven");
  }
  if (parsed.status === "proven" && parsed.deployedTargetUrl !== PUBLIC_SHOWCASE_URL) {
    throw new Error("public hosting probe requires matching deployedTargetUrl when proven");
  }
  if (parsed.status === "proven" && parsed.deployedArtifactKind !== "github_pages_static_showcase") {
    throw new Error("public hosting probe requires deployedArtifactKind when proven");
  }
  if (parsed.status === "proven" && parsed.deployedClaimBoundary !== "no_alpha_claim") {
    throw new Error("public hosting probe requires no_alpha_claim deployedClaimBoundary when proven");
  }
  if (parsed.status === "proven" && parsed.deployedDashboardClaim !== "local_demo_only") {
    throw new Error("public hosting probe requires local_demo_only deployedDashboardClaim when proven");
  }
  return {
    pagesConfigured: parsed.pagesConfigured === true,
    pagesStatus: typeof parsed.pagesStatus === "string" ? parsed.pagesStatus : undefined,
    httpStatus: typeof parsed.httpStatus === "number" ? parsed.httpStatus : undefined,
    observedAt: typeof parsed.observedAt === "string" ? parsed.observedAt : undefined,
    deployedDataHash: typeof parsed.deployedDataHash === "string" ? parsed.deployedDataHash : undefined,
    deployedTargetUrl: typeof parsed.deployedTargetUrl === "string" ? parsed.deployedTargetUrl : undefined,
    deployedArtifactKind: typeof parsed.deployedArtifactKind === "string" ? parsed.deployedArtifactKind : undefined,
    deployedClaimBoundary: typeof parsed.deployedClaimBoundary === "string" ? parsed.deployedClaimBoundary : undefined,
    deployedDashboardClaim: typeof parsed.deployedDashboardClaim === "string" ? parsed.deployedDashboardClaim : undefined,
  };
}

const dashboard = getShowcaseDashboard();
const html = renderToStaticMarkup(<Dashboard data={dashboard} />);
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>QuantLab Showcase</title></head><body>${html}</body></html>`;
const manifest = buildPublicDemoManifest(dashboard, {
  pagesConfigured: true,
  ...(hostingProbeFromEnv() ?? hostingProbeFromExistingArtifact()),
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
