import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import {
  classifyManifestContractStatus,
  classifyProbeStatus,
  publicHostingFreshness,
  readExpectedManifest,
  resolveProbeOutputPath,
} from "../scripts/probe-public-demo.mjs";

function writeManifest(path: string, dataHash: string): void {
  writeFileSync(
    path,
    JSON.stringify({
      dataHash,
      targetUrl: "https://austinyuch.github.io/finance_algorithms/",
      artifactKind: "github_pages_static_showcase",
      claimBoundary: "no_alpha_claim",
      dashboardClaim: "local_demo_only",
    }),
    "utf8",
  );
}

describe("public demo probe script helpers", () => {
  it("resolves configured probe output paths without corrupting absolute paths", () => {
    expect(resolveProbeOutputPath(undefined, "/workspace/frontend")).toBe(
      "/workspace/frontend/out/public-hosting-probe.json",
    );
    expect(resolveProbeOutputPath("../docs/public-hosting-probe.json", "/workspace/frontend")).toBe(
      "/workspace/docs/public-hosting-probe.json",
    );
    expect(resolveProbeOutputPath("/tmp/public-hosting-probe.json", "/workspace/frontend")).toBe(
      "/tmp/public-hosting-probe.json",
    );
  });

  it("classifies probe observations by freshness window", () => {
    expect(publicHostingFreshness("2026-06-11T14:50:00Z", "2026-06-11T15:00:00Z")).toEqual({
      freshnessStatus: "fresh",
      maxAgeHours: 24,
    });
    expect(publicHostingFreshness("2026-06-09T14:50:00Z", "2026-06-11T15:00:00Z")).toEqual({
      freshnessStatus: "stale",
      maxAgeHours: 24,
    });
  });

  it("marks missing or future observations invalid for proof", () => {
    expect(publicHostingFreshness(undefined, "2026-06-11T15:00:00Z").freshnessStatus).toBe("missing");
    expect(publicHostingFreshness("2026-06-11T15:30:00Z", "2026-06-11T15:00:00Z").freshnessStatus).toBe("invalid");
  });

  it("keeps otherwise matching public probe unobserved when observation is stale", () => {
    expect(
      classifyProbeStatus({
        httpStatus: 200,
        hashStatus: "matched",
        manifestContractStatus: "matched",
        freshnessStatus: "stale",
      }),
    ).toBe("configured_not_observed");
    expect(
      classifyProbeStatus({
        httpStatus: 200,
        hashStatus: "matched",
        manifestContractStatus: "matched",
        freshnessStatus: "fresh",
      }),
    ).toBe("proven");
  });

  it("does not match deployed manifest metadata without a complete expected manifest", () => {
    const deployed = {
      deployedTargetUrl: "https://austinyuch.github.io/finance_algorithms/",
      deployedArtifactKind: "github_pages_static_showcase",
      deployedClaimBoundary: "no_alpha_claim",
      deployedDashboardClaim: "local_demo_only",
    };

    expect(classifyManifestContractStatus({ deployed })).toBe("missing");
    expect(
      classifyManifestContractStatus({
        expected: {
          dataHash: "a".repeat(64),
          targetUrl: "https://austinyuch.github.io/finance_algorithms/",
          artifactKind: "github_pages_static_showcase",
          claimBoundary: "no_alpha_claim",
        },
        deployed,
      }),
    ).toBe("missing");
  });

  it("reads the manifest beside the requested probe output before stale fallback manifests", () => {
    const root = mkdtempSync(join(tmpdir(), "quantlab-probe-manifest-"));
    try {
      const staleOut = join(root, "out");
      const freshDocs = join(root, "docs");
      const originalCwd = process.cwd();
      process.chdir(root);
      try {
        mkdirSync(staleOut);
        mkdirSync(freshDocs);
        writeManifest(join(staleOut, "deployment-manifest.json"), "a".repeat(64));
        writeManifest(join(freshDocs, "deployment-manifest.json"), "b".repeat(64));

        expect(readExpectedManifest(join(freshDocs, "public-hosting-probe.json"))?.dataHash).toBe("b".repeat(64));
        writeFileSync(join(freshDocs, "deployment-manifest.json"), JSON.stringify({ dataHash: "c".repeat(64) }), "utf8");
        expect(readExpectedManifest(join(freshDocs, "public-hosting-probe.json"))).toBeUndefined();
      } finally {
        process.chdir(originalCwd);
      }
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});
