import { createHash } from "node:crypto";

import type { ShowcaseDashboard } from "./showcase-contract";

export const PUBLIC_SHOWCASE_URL = "https://austinyuch.github.io/finance_algorithms/";

export interface PublicDemoManifest {
  targetUrl: string;
  artifactKind: "github_pages_static_showcase";
  hostingEvidence: {
    status: "configured_not_observed";
    sourcePath: "docs/";
    publishMode: "github_pages_branch_source";
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

export function buildPublicDemoManifest(dashboard: ShowcaseDashboard): PublicDemoManifest {
  if (dashboard.claimBoundary !== "no_alpha_claim") {
    throw new Error("public demo manifest must preserve no_alpha_claim");
  }
  if (dashboard.demoReadiness.publicHosting !== "not_proven") {
    throw new Error("public hosting remains unobserved until the deployed URL is checked");
  }
  return {
    targetUrl: PUBLIC_SHOWCASE_URL,
    artifactKind: "github_pages_static_showcase",
    hostingEvidence: {
      status: "configured_not_observed",
      sourcePath: "docs/",
      publishMode: "github_pages_branch_source",
    },
    claimBoundary: "no_alpha_claim",
    dashboardClaim: dashboard.demoReadiness.claim,
    sections: dashboardSections(dashboard),
    dataHash: sha256(JSON.stringify(dashboard)),
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
