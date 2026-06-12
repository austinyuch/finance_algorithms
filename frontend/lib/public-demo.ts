import { createHash } from "node:crypto";

import type { ShowcaseDashboard } from "./showcase-contract";

export const PUBLIC_SHOWCASE_URL = "https://austinyuch.github.io/finance_algorithms/";

export type PublicHostingStatus = "not_configured" | "configured_not_observed" | "proven";

export interface PublicHostingProbe {
  pagesConfigured: boolean;
  pagesStatus?: string;
  httpStatus?: number;
  observedAt?: string;
  deployedDataHash?: string;
}

export interface PublicDemoManifest {
  targetUrl: string;
  artifactKind: "github_pages_static_showcase";
  hostingEvidence: {
    status: PublicHostingStatus;
    sourcePath: "docs/";
    publishMode: "github_pages_branch_source";
    pagesStatus?: string;
    httpStatus?: number;
    observedAt?: string;
    deployedDataHash?: string;
    expectedDataHash?: string;
    hashStatus?: "matched" | "mismatched" | "missing" | "not_checked";
  };
  claimBoundary: "no_alpha_claim";
  dashboardClaim: "local_demo_only";
  sections: string[];
  dataHash: string;
}

export interface VisualSnapshot {
  baselineKind: "static_visual_contract";
  claimBoundary: "no_alpha_claim";
  publicHosting: "configured_not_observed";
  htmlHash: string;
  sections: string[];
  viewportContracts: string[];
}

export interface BrowserVisualEvidence {
  status: "proven";
  claimBoundary: "no_alpha_claim";
  screenshotHash: string;
  viewport: string;
  source: "chromium-headless";
  observedAt: string;
}

export interface BrowserVisualDiffEvidence {
  artifactKind: "browser_visual_diff";
  claimBoundary: "no_alpha_claim";
  status: "passed" | "failed";
  baselineHash: string;
  currentHash: string;
  mismatchedPixels: number;
  totalPixels: number;
  mismatchRatio: number;
  maxMismatchRatio: number;
  viewport: string;
  source: "chromium-headless";
}

export interface PixelMismatchInput {
  baseline: Uint8Array;
  current: Uint8Array;
  width: number;
  height: number;
}

export interface PixelMismatchResult {
  mismatchedPixels: number;
  totalPixels: number;
  mismatchRatio: number;
}

function sha256(text: string): string {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

export function dashboardSections(dashboard: ShowcaseDashboard): string[] {
  const sections = [
    "leaderboard",
    "allocation-regime",
    "rebalance",
    "experiments",
    "evidence",
  ];
  if (dashboard.leaderboard.length === 0 || dashboard.experiments.length === 0) {
    throw new Error("public demo requires leaderboard and experiment sections");
  }
  return sections;
}

export function classifyPublicHostingEvidence(
  probe?: PublicHostingProbe,
  expectedDataHash?: string,
): PublicDemoManifest["hostingEvidence"] {
  if (!probe?.pagesConfigured) {
    return {
      status: "not_configured",
      sourcePath: "docs/",
      publishMode: "github_pages_branch_source",
    };
  }
  const base = {
    sourcePath: "docs/" as const,
    publishMode: "github_pages_branch_source" as const,
    pagesStatus: probe.pagesStatus,
    httpStatus: probe.httpStatus,
    observedAt: probe.observedAt,
    deployedDataHash: probe.deployedDataHash,
    expectedDataHash,
  };
  const hashStatus =
    expectedDataHash === undefined
      ? "not_checked"
      : probe.deployedDataHash === undefined
        ? "missing"
        : probe.deployedDataHash === expectedDataHash
          ? "matched"
          : "mismatched";
  if (probe.httpStatus === 200 && hashStatus === "matched") {
    return { ...base, hashStatus, status: "proven" };
  }
  return { ...base, hashStatus, status: "configured_not_observed" };
}

export function buildPublicDemoManifest(
  dashboard: ShowcaseDashboard,
  hostingProbe?: PublicHostingProbe,
): PublicDemoManifest {
  if (dashboard.claimBoundary !== "no_alpha_claim") {
    throw new Error("public demo manifest must preserve no_alpha_claim");
  }
  if (dashboard.demoReadiness.publicHosting !== "not_proven") {
    throw new Error("public hosting remains unobserved until the deployed URL is checked");
  }
  const dataHash = sha256(JSON.stringify(dashboard));
  return {
    targetUrl: PUBLIC_SHOWCASE_URL,
    artifactKind: "github_pages_static_showcase",
    hostingEvidence: classifyPublicHostingEvidence(hostingProbe ?? { pagesConfigured: true }, dataHash),
    claimBoundary: "no_alpha_claim",
    dashboardClaim: dashboard.demoReadiness.claim,
    sections: dashboardSections(dashboard),
    dataHash,
  };
}

export function buildBrowserVisualEvidence(input: {
  screenshotHash: string;
  viewport: string;
  source: "chromium-headless";
  observedAt: string;
}): BrowserVisualEvidence {
  if (!/^[a-f0-9]{64}$/.test(input.screenshotHash)) {
    throw new Error("browser visual screenshot hash must be sha256 hex");
  }
  if (!input.viewport.trim() || !input.observedAt.trim()) {
    throw new Error("browser visual evidence requires viewport and observedAt");
  }
  return {
    status: "proven",
    claimBoundary: "no_alpha_claim",
    screenshotHash: input.screenshotHash,
    viewport: input.viewport,
    source: input.source,
    observedAt: input.observedAt,
  };
}

export function buildBrowserVisualDiffEvidence(input: {
  baseline: BrowserVisualEvidence;
  current: BrowserVisualEvidence;
  mismatchedPixels: number;
  totalPixels: number;
  mismatchRatio: number;
  maxMismatchRatio: number;
}): BrowserVisualDiffEvidence {
  for (const evidence of [input.baseline, input.current]) {
    if (evidence.claimBoundary !== "no_alpha_claim") {
      throw new Error("browser visual diff must preserve no_alpha_claim");
    }
    if (!/^[a-f0-9]{64}$/.test(evidence.screenshotHash)) {
      throw new Error("browser visual diff requires screenshot hash evidence");
    }
  }
  if (input.baseline.viewport !== input.current.viewport) {
    throw new Error("browser visual diff requires matching viewport");
  }
  if (
    input.mismatchRatio < 0 ||
    input.mismatchRatio > 1 ||
    input.maxMismatchRatio < 0 ||
    input.maxMismatchRatio > 1
  ) {
    throw new Error("browser visual diff mismatch ratio must be within [0,1]");
  }
  if (!Number.isInteger(input.mismatchedPixels) || !Number.isInteger(input.totalPixels)) {
    throw new Error("browser visual diff pixel counts must be integers");
  }
  if (input.totalPixels <= 0 || input.mismatchedPixels < 0 || input.mismatchedPixels > input.totalPixels) {
    throw new Error("browser visual diff pixel counts are inconsistent");
  }
  return {
    artifactKind: "browser_visual_diff",
    claimBoundary: "no_alpha_claim",
    status: input.mismatchRatio <= input.maxMismatchRatio ? "passed" : "failed",
    baselineHash: input.baseline.screenshotHash,
    currentHash: input.current.screenshotHash,
    mismatchedPixels: input.mismatchedPixels,
    totalPixels: input.totalPixels,
    mismatchRatio: input.mismatchRatio,
    maxMismatchRatio: input.maxMismatchRatio,
    viewport: input.current.viewport,
    source: input.current.source,
  };
}

export function computePixelMismatchRatio(input: PixelMismatchInput): PixelMismatchResult {
  const { baseline, current, width, height } = input;
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
    throw new Error("browser visual pixel comparison requires positive integer dimensions");
  }
  const totalPixels = width * height;
  const expectedBytes = totalPixels * 4;
  if (baseline.length !== expectedBytes || current.length !== expectedBytes) {
    throw new Error("browser visual pixel comparison buffer size does not match dimensions");
  }

  let mismatchedPixels = 0;
  for (let offset = 0; offset < expectedBytes; offset += 4) {
    if (
      baseline[offset] !== current[offset] ||
      baseline[offset + 1] !== current[offset + 1] ||
      baseline[offset + 2] !== current[offset + 2] ||
      baseline[offset + 3] !== current[offset + 3]
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

export function buildVisualSnapshot(html: string, dashboard: ShowcaseDashboard): VisualSnapshot {
  const sections = dashboardSections(dashboard);
  for (const section of sections) {
    if (!html.includes(`data-section="${section}"`)) {
      throw new Error(`visual snapshot missing section ${section}`);
    }
  }
  if (!html.includes("no_alpha_claim") || !html.includes("local_demo_only")) {
    throw new Error("visual snapshot must preserve conservative claim labels");
  }
  return {
    baselineKind: "static_visual_contract",
    claimBoundary: "no_alpha_claim",
    publicHosting: "configured_not_observed",
    htmlHash: sha256(html),
    sections,
    viewportContracts: [
      "desktop-1440x900",
      "tablet-768x1024",
      "mobile-390x844",
    ],
  };
}

export function assertVisualSnapshotMatchesBaseline(
  current: VisualSnapshot,
  baseline: VisualSnapshot,
): void {
  if (baseline.baselineKind !== "static_visual_contract") {
    throw new Error("unknown visual baseline kind");
  }
  if (current.claimBoundary !== "no_alpha_claim" || baseline.claimBoundary !== "no_alpha_claim") {
    throw new Error("visual baseline must preserve no_alpha_claim");
  }
  if (current.htmlHash !== baseline.htmlHash) {
    throw new Error("static visual contract hash changed");
  }
  if (JSON.stringify(current.sections) !== JSON.stringify(baseline.sections)) {
    throw new Error("static visual contract sections changed");
  }
  if (JSON.stringify(current.viewportContracts) !== JSON.stringify(baseline.viewportContracts)) {
    throw new Error("static visual contract viewports changed");
  }
}
