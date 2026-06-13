export type ClaimBoundary = "no_alpha_claim";

export interface LeaderboardRow {
  runId: string;
  strategyName: string;
  oosNetSharpe: number;
  isBaseline: boolean;
  claimBoundary: ClaimBoundary;
}

export interface ExperimentRegistryRow {
  experimentId: string;
  modelFamily: string;
  strategyName: string;
  runIds: string[];
  claimBoundary: ClaimBoundary;
  status: "research_only";
  readiness: "registry_only";
  tags: string[];
}

export interface ShowcaseDashboard {
  activeRunId: string;
  strategyName: string;
  claimBoundary: ClaimBoundary;
  sourceMetadata: {
    source: "local_result_store";
    sourceRecordCount: number;
    experimentRegistry: "experiment_registry";
  };
  regime: {
    label: string;
    confidence: number;
  };
  allocation: Record<string, number>;
  rebalanceDates: string[];
  leaderboard: LeaderboardRow[];
  experiments: ExperimentRegistryRow[];
  warnings: string[];
  evidence: {
    readiness: "local_runtime_only";
    tests: string[];
  };
  demoReadiness: {
    publicHosting: "not_proven";
    visualRegression: "proven";
    dependencyAudit: "clean";
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
  if (
    !isRecord(value.sourceMetadata) ||
    value.sourceMetadata.source !== "local_result_store" ||
    value.sourceMetadata.experimentRegistry !== "experiment_registry" ||
    typeof value.sourceMetadata.sourceRecordCount !== "number" ||
    value.sourceMetadata.sourceRecordCount < 2
  ) {
    throw new Error("dashboard sourceMetadata must prove local_result_store artifact source");
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
  if (!Array.isArray(value.experiments)) {
    throw new Error("experiment registry must be an array");
  }
  for (const row of value.experiments) {
    if (
      !isRecord(row) ||
      row.claimBoundary !== "no_alpha_claim" ||
      row.status !== "research_only" ||
      row.readiness !== "registry_only"
    ) {
      throw new Error("experiment registry rows must remain research_only registry_only no_alpha_claim");
    }
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
  if (value.demoReadiness.visualRegression !== "proven") {
    throw new Error("visual regression must be proven by browser visual evidence");
  }
  if (value.demoReadiness.dependencyAudit !== "clean") {
    throw new Error("dependency audit must remain clean after remediation");
  }
}
