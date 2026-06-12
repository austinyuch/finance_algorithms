import { describe, expect, it } from "vitest";

import {
  classifyManifestContractStatus,
  classifyProbeStatus,
  publicHostingFreshness,
} from "../scripts/probe-public-demo.mjs";

describe("public demo probe script helpers", () => {
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
});
