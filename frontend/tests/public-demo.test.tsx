import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import fc from "fast-check";

import { Dashboard } from "../components/Dashboard";
import {
  PUBLIC_SHOWCASE_URL,
  assertVisualSnapshotMatchesBaseline,
  buildPublicDemoManifest,
  buildVisualSnapshot,
  dashboardSections,
} from "../lib/public-demo";
import { getShowcaseDashboard } from "../lib/showcase-fixture";

describe("F public static showcase proof", () => {
  it("builds a GitHub Pages manifest without overclaiming live hosting", () => {
    const manifest = buildPublicDemoManifest(getShowcaseDashboard());

    expect(manifest.targetUrl).toBe(PUBLIC_SHOWCASE_URL);
    expect(manifest.artifactKind).toBe("github_pages_static_showcase");
    expect(manifest.hostingEvidence.status).toBe("configured_not_observed");
    expect(manifest.claimBoundary).toBe("no_alpha_claim");
    expect(manifest.dashboardClaim).toBe("local_demo_only");
    expect(manifest.sections).toEqual([
      "leaderboard",
      "allocation-regime",
      "rebalance",
      "experiments",
      "evidence",
    ]);
    expect(manifest.dataHash).toMatch(/^[a-f0-9]{64}$/);
  });

  it("creates a deterministic static visual contract baseline", () => {
    const dashboard = getShowcaseDashboard();
    const html = renderToStaticMarkup(<Dashboard data={dashboard} />);
    const snapshot = buildVisualSnapshot(html, dashboard);

    expect(snapshot.baselineKind).toBe("static_visual_contract");
    expect(snapshot.publicHosting).toBe("configured_not_observed");
    expect(snapshot.htmlHash).toMatch(/^[a-f0-9]{64}$/);
    expect(snapshot.sections).toContain("experiments");
    expect(() => assertVisualSnapshotMatchesBaseline(snapshot, snapshot)).not.toThrow();
  });

  it("rejects static visual contract drift", () => {
    const dashboard = getShowcaseDashboard();
    const snapshot = buildVisualSnapshot(renderToStaticMarkup(<Dashboard data={dashboard} />), dashboard);

    expect(() =>
      assertVisualSnapshotMatchesBaseline(
        { ...snapshot, htmlHash: "0".repeat(64) },
        snapshot,
      ),
    ).toThrow(/hash changed/);
  });

  it("rejects manifest overclaims before deployed URL evidence exists", () => {
    const dashboard = {
      ...getShowcaseDashboard(),
      demoReadiness: {
        ...getShowcaseDashboard().demoReadiness,
        publicHosting: "proven" as never,
      },
    };

    expect(() => buildPublicDemoManifest(dashboard)).toThrow(/unobserved/);
  });

  it("rejects missing public showcase sections and conservative labels", () => {
    const dashboard = {
      ...getShowcaseDashboard(),
      experiments: [],
    };

    expect(() => dashboardSections(dashboard)).toThrow(/leaderboard and experiment/);
    expect(() => buildVisualSnapshot("<main data-section=\"leaderboard\"></main>", getShowcaseDashboard())).toThrow(
      /missing section/,
    );
    expect(() =>
      buildVisualSnapshot(
        renderToStaticMarkup(<Dashboard data={getShowcaseDashboard()} />).replaceAll("no_alpha_claim", "alpha_claim"),
        getShowcaseDashboard(),
      ),
    ).toThrow(/conservative claim/);
  });

  it("rejects malformed visual baselines", () => {
    const dashboard = getShowcaseDashboard();
    const snapshot = buildVisualSnapshot(renderToStaticMarkup(<Dashboard data={dashboard} />), dashboard);

    expect(() =>
      assertVisualSnapshotMatchesBaseline(snapshot, {
        ...snapshot,
        baselineKind: "pixel" as never,
      }),
    ).toThrow(/unknown/);
    expect(() =>
      assertVisualSnapshotMatchesBaseline(snapshot, {
        ...snapshot,
        claimBoundary: "alpha_claim" as never,
      }),
    ).toThrow(/no_alpha_claim/);
    expect(() =>
      assertVisualSnapshotMatchesBaseline(snapshot, {
        ...snapshot,
        sections: ["leaderboard"],
      }),
    ).toThrow(/sections changed/);
    expect(() =>
      assertVisualSnapshotMatchesBaseline(snapshot, {
        ...snapshot,
        viewportContracts: ["desktop-1440x900"],
      }),
    ).toThrow(/viewports changed/);
  });

  it("PBT: visual hash changes when rendered HTML content changes", () => {
    const dashboard = getShowcaseDashboard();
    const html = renderToStaticMarkup(<Dashboard data={dashboard} />);
    const base = buildVisualSnapshot(html, dashboard);

    fc.assert(
      fc.property(fc.string({ minLength: 1, maxLength: 40 }), (suffix) => {
        const changed = buildVisualSnapshot(`${html}<span>${suffix}</span>`, dashboard);
        expect(changed.htmlHash === base.htmlHash).toBe(false);
        expect(changed.sections).toEqual(base.sections);
      }),
    );
  });
});
