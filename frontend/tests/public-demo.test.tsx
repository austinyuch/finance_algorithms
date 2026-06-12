import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import fc from "fast-check";

import { Dashboard } from "../components/Dashboard";
import {
  PUBLIC_SHOWCASE_URL,
  assertVisualSnapshotMatchesBaseline,
  buildBrowserVisualEvidence,
  buildBrowserVisualDiffEvidence,
  buildPublicDemoManifest,
  buildVisualSnapshot,
  classifyPublicHostingEvidence,
  computePixelMismatchRatio,
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

  it("records proven public hosting only when Pages and URL evidence agree", () => {
    const manifest = buildPublicDemoManifest(getShowcaseDashboard(), {
      pagesConfigured: true,
      pagesStatus: "built",
      httpStatus: 200,
      observedAt: "2026-06-11T14:50:00Z",
    });

    expect(manifest.hostingEvidence.status).toBe("proven");
    expect(manifest.hostingEvidence.pagesStatus).toBe("built");
    expect(manifest.hostingEvidence.httpStatus).toBe(200);
    expect(manifest.hostingEvidence.observedAt).toBe("2026-06-11T14:50:00Z");
  });

  it("keeps public hosting unobserved when Pages is configured but URL is not live", () => {
    expect(
      classifyPublicHostingEvidence({
        pagesConfigured: true,
        pagesStatus: "building",
        httpStatus: 404,
      }).status,
    ).toBe("configured_not_observed");
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

  it("creates browser visual evidence from a real screenshot hash", () => {
    const evidence = buildBrowserVisualEvidence({
      screenshotHash: "a".repeat(64),
      viewport: "desktop-1440x900",
      source: "chromium-headless",
      observedAt: "2026-06-11T15:00:00Z",
    });

    expect(evidence.status).toBe("proven");
    expect(evidence.claimBoundary).toBe("no_alpha_claim");
    expect(evidence.screenshotHash).toMatch(/^[a-f0-9]{64}$/);
  });

  it("compares browser visual evidence against a threshold", () => {
    const baseline = buildBrowserVisualEvidence({
      screenshotHash: "a".repeat(64),
      viewport: "desktop-1440x900",
      source: "chromium-headless",
      observedAt: "2026-06-11T15:00:00Z",
    });
    const current = { ...baseline, screenshotHash: "b".repeat(64) };

    const failed = buildBrowserVisualDiffEvidence({
      baseline,
      current,
      mismatchedPixels: 2,
      totalPixels: 100,
      mismatchRatio: 0.02,
      maxMismatchRatio: 0.01,
    });
    const passed = buildBrowserVisualDiffEvidence({
      baseline,
      current,
      mismatchedPixels: 5,
      totalPixels: 1000,
      mismatchRatio: 0.005,
      maxMismatchRatio: 0.01,
    });

    expect(failed.status).toBe("failed");
    expect(passed.status).toBe("passed");
    expect(failed.baselineHash).toBe("a".repeat(64));
    expect(failed.currentHash).toBe("b".repeat(64));
  });

  it("computes browser visual mismatch ratio from pixels", () => {
    const baseline = new Uint8Array([
      0, 0, 0, 255,
      255, 255, 255, 255,
      10, 20, 30, 255,
      40, 50, 60, 255,
    ]);
    const current = new Uint8Array(baseline);
    current[4] = 0;

    expect(computePixelMismatchRatio({ baseline, current, width: 2, height: 2 }).mismatchRatio).toBe(0.25);
  });

  it("rejects browser visual pixel comparison when dimensions or buffer sizes drift", () => {
    const baseline = new Uint8Array([0, 0, 0, 255]);
    const current = new Uint8Array([0, 0, 0, 255]);

    expect(() => computePixelMismatchRatio({ baseline, current, width: 0, height: 1 })).toThrow(/dimensions/);
    expect(() => computePixelMismatchRatio({ baseline, current: new Uint8Array(8), width: 1, height: 1 })).toThrow(
      /buffer size/,
    );
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
    expect(() =>
      buildBrowserVisualEvidence({
        screenshotHash: "not-a-hash",
        viewport: "desktop-1440x900",
        source: "chromium-headless",
        observedAt: "2026-06-11T15:00:00Z",
      }),
    ).toThrow(/screenshot hash/);
    const baseline = buildBrowserVisualEvidence({
      screenshotHash: "a".repeat(64),
      viewport: "desktop-1440x900",
      source: "chromium-headless",
      observedAt: "2026-06-11T15:00:00Z",
    });
    expect(() =>
      buildBrowserVisualDiffEvidence({
        baseline,
        current: baseline,
        mismatchedPixels: 0,
        totalPixels: 1,
        mismatchRatio: -0.1,
        maxMismatchRatio: 0.01,
      }),
    ).toThrow(/mismatch ratio/);
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

  it("PBT: public hosting classifier never proves non-200 responses", () => {
    fc.assert(
      fc.property(fc.integer({ min: 100, max: 599 }).filter((status) => status !== 200), (httpStatus) => {
        const evidence = classifyPublicHostingEvidence({
          pagesConfigured: true,
          pagesStatus: "built",
          httpStatus,
        });
        expect(evidence.status).not.toBe("proven");
      }),
    );
  });

  it("PBT: visual diff status follows configured threshold", () => {
    const baseline = buildBrowserVisualEvidence({
      screenshotHash: "a".repeat(64),
      viewport: "desktop-1440x900",
      source: "chromium-headless",
      observedAt: "2026-06-11T15:00:00Z",
    });
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1, noNaN: true }),
        fc.float({ min: 0, max: 1, noNaN: true }),
        (mismatchRatio, maxMismatchRatio) => {
          const evidence = buildBrowserVisualDiffEvidence({
            baseline,
            current: baseline,
            mismatchedPixels: Math.round(mismatchRatio * 10000),
            totalPixels: 10000,
            mismatchRatio,
            maxMismatchRatio,
          });
          expect(evidence.status).toBe(mismatchRatio <= maxMismatchRatio ? "passed" : "failed");
        },
      ),
    );
  });

  it("PBT: pixel mismatch ratio equals changed-pixel count over total pixels", () => {
    fc.assert(
      fc.property(fc.integer({ min: 1, max: 24 }), fc.integer({ min: 0, max: 24 }), (totalPixels, changedSeed) => {
        const changedPixels = changedSeed % (totalPixels + 1);
        const baseline = new Uint8Array(totalPixels * 4);
        const current = new Uint8Array(totalPixels * 4);
        for (let pixel = 0; pixel < changedPixels; pixel += 1) {
          current[pixel * 4] = 255;
        }

        const result = computePixelMismatchRatio({ baseline, current, width: totalPixels, height: 1 });
        expect(result.totalPixels).toBe(totalPixels);
        expect(result.mismatchedPixels).toBe(changedPixels);
        expect(result.mismatchRatio).toBe(changedPixels / totalPixels);
      }),
    );
  });
});
