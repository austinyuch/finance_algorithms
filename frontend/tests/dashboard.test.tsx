import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import fc from "fast-check";

import { Dashboard } from "../components/Dashboard";
import { GET } from "../app/api/showcase/route";
import { assertDashboardPayload, isLeaderboardSorted } from "../lib/showcase-contract";
import { getShowcaseDashboard } from "../lib/showcase-data";

function currentFrontendLineCoveragePercent() {
  const transcript = readFileSync(
    new URL("../../docs/review/assets/gate-frontend-coverage.txt", import.meta.url),
    "utf8"
  );
  const match = transcript.match(/F Next\.js line coverage (?<coverage>\d+\.\d+%)/);
  if (!match?.groups?.coverage) {
    throw new Error("gate-frontend-coverage.txt must publish F Next.js line coverage");
  }
  return match.groups.coverage;
}

describe("F Next.js showcase dashboard", () => {
  it("renders dashboard sections, warnings, and no-alpha evidence", () => {
    const html = renderToStaticMarkup(<Dashboard data={getShowcaseDashboard()} />);

    expect(html).toContain("data-section=\"leaderboard\"");
    expect(html).toContain("data-section=\"allocation-regime\"");
    expect(html).toContain("data-section=\"rebalance\"");
    expect(html).toContain("data-section=\"experiments\"");
    expect(html).toContain("data-section=\"interactive-research\"");
    expect(html).toContain("data-section=\"evidence\"");
    expect(html).toContain("no_alpha_claim");
    expect(html).toContain("static_replay");
    expect(html).toContain("research_mode_approximate_availability");
    expect(html).toContain("registry_only");
    expect(html).toContain("local_runtime_only");
    expect(html).toContain("not_proven");
    expect(html).toContain("local_demo_only");
  });

  it("serves validated dashboard payload from the API route", async () => {
    const response = await GET();
    const payload = await response.json();

    expect(response.status).toBe(200);
    expect(() => assertDashboardPayload(payload)).not.toThrow();
    expect(payload.sourceMetadata).toEqual({
      source: "local_result_store",
      sourceRecordCount: 2,
      experimentRegistry: "experiment_registry"
    });
    expect(payload.claimBoundary).toBe("no_alpha_claim");
    expect(payload.experiments[0].readiness).toBe("registry_only");
    expect(payload.experiments[0].claimBoundary).toBe("no_alpha_claim");
    expect(payload.interactiveResearch.mode).toBe("static_replay");
    expect(payload.interactiveResearch.claimBoundary).toBe("no_alpha_claim");
    expect(payload.interactiveResearch.metricAuthority).toBe("out_of_sample_net_only");
    expect(payload.interactiveResearch.rows.some((row) => row.isBaseline)).toBe(true);
    expect(payload.demoReadiness.dependencyAudit).toBe("clean");
    expect(payload.demoReadiness.publicHosting).toBe("not_proven");
    expect(payload.demoReadiness.visualRegression).toBe("proven");
  });

  it("keeps dashboard gate evidence aligned with current governed proof", () => {
    const payload = getShowcaseDashboard();
    const frontendCoverage = currentFrontendLineCoveragePercent();

    expect(payload.evidence.tests).toContain("frontend mutation 29/29 killed");
    expect(payload.evidence.tests).not.toContain("frontend mutation 21/21 killed");
    expect(payload.evidence.tests).toContain(`F Next.js coverage ${frontendCoverage}`);
    expect(payload.evidence.tests).not.toContain("mutation 9/9 killed");
    expect(payload.evidence.tests).not.toContain("frontend mutation 18/18 killed");
    expect(payload.evidence.tests).not.toContain("frontend mutation 14/14 killed");
    expect(payload.evidence.tests).not.toContain("F Next.js coverage 91.42%");
  });

  it("rejects malformed claim boundaries", () => {
    const payload = { ...getShowcaseDashboard(), claimBoundary: "alpha_claim" };

    expect(() => assertDashboardPayload(payload)).toThrow(/no_alpha_claim/);
    expect(() => assertDashboardPayload(null)).toThrow(/object/);
    expect(() => assertDashboardPayload({ ...getShowcaseDashboard(), leaderboard: "bad" })).toThrow(/leaderboard/);
    expect(() =>
      assertDashboardPayload({
        ...getShowcaseDashboard(),
        leaderboard: [
          {
            ...getShowcaseDashboard().leaderboard[0],
            claimBoundary: "alpha_claim"
          }
        ]
      })
    ).toThrow(/leaderboard rows/);
    expect(() =>
      assertDashboardPayload({
        ...getShowcaseDashboard(),
        leaderboard: [...getShowcaseDashboard().leaderboard].reverse()
      })
    ).toThrow(/sorted/);
  });

  it("surfaces the real-data OOS-net comparison panel under no_alpha_claim", () => {
    const payload = getShowcaseDashboard();
    expect(payload.realData).toBeDefined();
    const html = renderToStaticMarkup(<Dashboard data={payload} />);
    expect(html).toContain('data-section="real-data"');
    expect(html).toContain("Real-Data OOS-Net");
    expect(payload.realData?.claimBoundary).toBe("no_alpha_claim");
    expect(payload.realData?.source).toBe("real_data_oos_backtest_artifact");
    expect(payload.realData?.rows.some((row) => row.isBaseline)).toBe(true);
  });

  it("rejects malformed realData sections", () => {
    const base = getShowcaseDashboard();
    expect(() =>
      assertDashboardPayload({ ...base, realData: { ...base.realData, claimBoundary: "alpha_claim" } })
    ).toThrow(/no_alpha_claim/);
    expect(() =>
      assertDashboardPayload({ ...base, realData: { ...base.realData, rows: [base.realData?.rows[0]] } })
    ).toThrow(/candidate and baseline/);
    expect(() =>
      assertDashboardPayload({
        ...base,
        realData: { ...base.realData, rows: base.realData?.rows.map((r) => ({ ...r, isBaseline: false })) },
      })
    ).toThrow(/visible baseline/);
  });

  it("rejects malformed interactive research sections", () => {
    const base = getShowcaseDashboard();
    expect(() =>
      assertDashboardPayload({
        ...base,
        interactiveResearch: { ...base.interactiveResearch, claimBoundary: "alpha_claim" },
      }),
    ).toThrow(/interactive research.*no_alpha_claim/);
    expect(() =>
      assertDashboardPayload({
        ...base,
        interactiveResearch: {
          ...base.interactiveResearch,
          dataLineage: {
            ...base.interactiveResearch.dataLineage,
            approximateAvailability: false,
          },
        },
      }),
    ).toThrow(/approximate/);
    expect(() =>
      assertDashboardPayload({
        ...base,
        interactiveResearch: {
          ...base.interactiveResearch,
          rows: base.interactiveResearch.rows.map((row) => ({ ...row, isBaseline: false })),
        },
      }),
    ).toThrow(/visible baseline/);
  });

  it("rejects overclaimed public demo readiness", () => {
    const payload = {
      ...getShowcaseDashboard(),
      demoReadiness: {
        ...getShowcaseDashboard().demoReadiness,
        publicHosting: "proven"
      }
    };

    expect(() => assertDashboardPayload(payload)).toThrow(/public hosting/);
  });

  it("rejects experiment registry overclaims", () => {
    const payload = {
      ...getShowcaseDashboard(),
      experiments: [
        {
          ...getShowcaseDashboard().experiments[0],
          claimBoundary: "alpha_claim"
        }
      ]
    };

    expect(() => assertDashboardPayload(payload)).toThrow(/experiment registry/);
    expect(() => assertDashboardPayload({ ...getShowcaseDashboard(), experiments: "bad" })).toThrow(/experiment/);
    expect(() =>
      assertDashboardPayload({
        ...getShowcaseDashboard(),
        evidence: { readiness: "tier3_ready", tests: [] }
      })
    ).toThrow(/local_runtime_only/);
  });

  it("rejects missing demo readiness and stale visual-regression underclaims", () => {
    const { demoReadiness: _missing, ...withoutReadiness } = getShowcaseDashboard();
    expect(() => assertDashboardPayload(withoutReadiness)).toThrow(/demoReadiness/);

    expect(() =>
      assertDashboardPayload({
        ...getShowcaseDashboard(),
        demoReadiness: {
          ...getShowcaseDashboard().demoReadiness,
          visualRegression: "not_proven"
        }
      })
    ).toThrow(/visual regression/);
  });

  it("PBT: leaderboard sorted validator matches descending scores", () => {
    fc.assert(
      fc.property(
        fc.array(fc.float({ min: -5, max: 5, noNaN: true, noDefaultInfinity: true }), {
          minLength: 1,
          maxLength: 20
        }),
        (scores) => {
          const rows = scores.map((score, index) => ({
            runId: `run-${index}`,
            strategyName: `strategy-${index}`,
            oosNetSharpe: score,
            isBaseline: false,
            claimBoundary: "no_alpha_claim" as const
          }));
          const sortedRows = [...rows].sort((a, b) => b.oosNetSharpe - a.oosNetSharpe);
          expect(isLeaderboardSorted(sortedRows)).toBe(true);
          if (rows.some((row, index) => row !== sortedRows[index])) {
            expect(isLeaderboardSorted(rows)).toBe(false);
          }
        }
      )
    );
  });
});
