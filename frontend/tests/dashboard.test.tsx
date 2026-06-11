import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import fc from "fast-check";

import { Dashboard } from "../components/Dashboard";
import { GET } from "../app/api/showcase/route";
import { assertDashboardPayload, isLeaderboardSorted } from "../lib/showcase-contract";
import { getShowcaseDashboard } from "../lib/showcase-fixture";

describe("F Next.js showcase dashboard", () => {
  it("renders dashboard sections, warnings, and no-alpha evidence", () => {
    const html = renderToStaticMarkup(<Dashboard data={getShowcaseDashboard()} />);

    expect(html).toContain("data-section=\"leaderboard\"");
    expect(html).toContain("data-section=\"allocation-regime\"");
    expect(html).toContain("data-section=\"rebalance\"");
    expect(html).toContain("data-section=\"experiments\"");
    expect(html).toContain("data-section=\"evidence\"");
    expect(html).toContain("no_alpha_claim");
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
    expect(payload.claimBoundary).toBe("no_alpha_claim");
    expect(payload.experiments[0].readiness).toBe("registry_only");
    expect(payload.experiments[0].claimBoundary).toBe("no_alpha_claim");
    expect(payload.demoReadiness.dependencyAudit).toBe("clean");
    expect(payload.demoReadiness.publicHosting).toBe("not_proven");
    expect(payload.demoReadiness.visualRegression).toBe("not_proven");
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

  it("rejects missing demo readiness and visual-regression overclaims", () => {
    const { demoReadiness: _missing, ...withoutReadiness } = getShowcaseDashboard();
    expect(() => assertDashboardPayload(withoutReadiness)).toThrow(/demoReadiness/);

    expect(() =>
      assertDashboardPayload({
        ...getShowcaseDashboard(),
        demoReadiness: {
          ...getShowcaseDashboard().demoReadiness,
          visualRegression: "proven"
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
