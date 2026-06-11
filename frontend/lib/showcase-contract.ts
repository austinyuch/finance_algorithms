export type ClaimBoundary = "no_alpha_claim";

export interface LeaderboardRow {
  runId: string;
  strategyName: string;
  oosNetSharpe: number;
  isBaseline: boolean;
  claimBoundary: ClaimBoundary;
}

export interface ShowcaseDashboard {
  activeRunId: string;
  strategyName: string;
  claimBoundary: ClaimBoundary;
  regime: {
    label: string;
    confidence: number;
  };
  allocation: Record<string, number>;
  rebalanceDates: string[];
  leaderboard: LeaderboardRow[];
  warnings: string[];
  evidence: {
    readiness: "local_runtime_only";
    tests: string[];
  };
  demoReadiness: {
    publicHosting: "not_proven";
    visualRegression: "not_proven";
    dependencyAudit: "moderate_advisory";
    claim: "local_demo_only";
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isLeaderboardSorted(rows: LeaderboardRow[]): boolean {
  return rows.every((row, index) => index === 0 || rows[index - 1].oosNetSharpe >= row.oosNetSharpe);
}

export function assertDashboardPayload(value: unknown): asserts value is ShowcaseDashboard {
  if (!isRecord(value)) {
    throw new Error("dashboard payload must be an object");
  }
  if (value.claimBoundary !== "no_alpha_claim") {
    throw new Error("dashboard claimBoundary must remain no_alpha_claim");
  }
  if (!Array.isArray(value.leaderboard)) {
    throw new Error("dashboard leaderboard must be an array");
  }
  for (const row of value.leaderboard) {
    if (!isRecord(row) || row.claimBoundary !== "no_alpha_claim") {
      throw new Error("leaderboard rows must preserve no_alpha_claim");
    }
  }
  if (!isLeaderboardSorted(value.leaderboard as LeaderboardRow[])) {
    throw new Error("leaderboard must be sorted by descending OOS-net Sharpe");
  }
  if (!isRecord(value.evidence) || value.evidence.readiness !== "local_runtime_only") {
    throw new Error("dashboard evidence must be local_runtime_only");
  }
  if (!isRecord(value.demoReadiness)) {
    throw new Error("dashboard demoReadiness must be present");
  }
  if (value.demoReadiness.publicHosting !== "not_proven") {
    throw new Error("public hosting must remain not_proven until deployment evidence exists");
  }
  if (value.demoReadiness.visualRegression !== "not_proven") {
    throw new Error("visual regression must remain not_proven until screenshot evidence exists");
  }
}
