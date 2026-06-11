import { assertDashboardPayload, ShowcaseDashboard } from "./showcase-contract";

const dashboard: ShowcaseDashboard = {
  activeRunId: "forecast-run",
  strategyName: "ForecastAllocationStrategy",
  claimBoundary: "no_alpha_claim",
  regime: {
    label: "risk_on",
    confidence: 0.6
  },
  allocation: {
    GROWTH: 0.62,
    STEADY: 0.38
  },
  rebalanceDates: ["2022-01-31", "2022-02-28", "2022-03-31"],
  leaderboard: [
    {
      runId: "forecast-run",
      strategyName: "ForecastAllocationStrategy",
      oosNetSharpe: 1.21,
      isBaseline: false,
      claimBoundary: "no_alpha_claim"
    },
    {
      runId: "baseline-run",
      strategyName: "StaticWeights",
      oosNetSharpe: 0.74,
      isBaseline: true,
      claimBoundary: "no_alpha_claim"
    }
  ],
  warnings: ["local_runtime_only"],
  evidence: {
    readiness: "local_runtime_only",
    tests: [
      "156 passed",
      "mutation 8/8 killed",
      "F Next.js coverage 84.37%",
      "E-lite coverage 97.3%",
      "B source-health coverage 97.6%"
    ]
  },
  demoReadiness: {
    publicHosting: "not_proven",
    visualRegression: "not_proven",
    dependencyAudit: "moderate_advisory",
    claim: "local_demo_only"
  }
};

export function getShowcaseDashboard(): ShowcaseDashboard {
  assertDashboardPayload(dashboard);
  return dashboard;
}
