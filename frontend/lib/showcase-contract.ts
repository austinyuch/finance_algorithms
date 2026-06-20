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

export interface RealDataOosRow {
  strategyName: string;
  oosNetSharpe: number;
  isBaseline: boolean;
}

export interface RealDataComparison {
  source: "real_data_oos_backtest_artifact";
  status: "computed";
  claimBoundary: ClaimBoundary;
  assetSet: string[];
  overlapStart: string;
  overlapEnd: string;
  overlapMonths: number;
  rows: RealDataOosRow[];
}

export type ResearchBackend = "reference" | "pytorch" | "jax" | "tensorflow";
export type ResearchRebalance = "monthly" | "quarterly";

export interface ResearchParameters {
  backend: ResearchBackend;
  hiddenUnits: number;
  lookback: number;
  epochs: number;
  seed: number;
  rebalance: ResearchRebalance;
  symbols: string[];
}

export interface IntegerRange {
  min: number;
  max: number;
  step: number;
}

export interface ResearchParameterRanges {
  hiddenUnits: IntegerRange;
  lookback: IntegerRange;
  epochs: IntegerRange;
  seed: IntegerRange;
  rebalance: ResearchRebalance[];
  backend: ResearchBackend[];
}

export interface ResearchPoint {
  label: string;
  value: number;
}

export interface InteractiveResearchRow {
  strategyName: string;
  isBaseline: boolean;
  oosNetSharpe: number;
  oosNetCagr: number;
  maxDrawdown: number;
  equityCurve: ResearchPoint[];
  drawdown: ResearchPoint[];
  returnDistribution: number[];
  learningCurve: ResearchPoint[];
}

export type ResearchLifecycle = "idle" | "computing" | "computed" | "fail_closed" | "error";
export type ResearchComputeSource = "static_fallback" | "live_backend";

export interface InteractiveResearchPayload {
  // H-4: additive `live_compute` mode for live backend reruns; `static_replay` stays the
  // fallback contract. Honesty literals below are enforced identically on both modes.
  mode: "static_replay" | "live_compute";
  // optional H-4 live lifecycle / provenance; absent on the H-3 static payload.
  lifecycle?: ResearchLifecycle;
  computeSource?: ResearchComputeSource;
  status: "computed" | "fail_closed";
  claimBoundary: ClaimBoundary;
  metricAuthority: "out_of_sample_net_only";
  parameters: ResearchParameters;
  parameterRanges: ResearchParameterRanges;
  resolvedBackend: {
    requested: ResearchBackend;
    resolved: ResearchBackend;
    fallbackReason: string | null;
  };
  dataLineage: {
    source: "cr_b21_approximate_backfill";
    dataWindow: {
      start: string;
      end: string;
    };
    approximateAvailability: true;
    strictPitExcluded: true;
    warning: "research_mode_approximate_availability";
  };
  artifact: {
    experimentId: string;
    reportChecksum: string;
    artifactPath: string;
    vizPath: string;
  };
  rows: InteractiveResearchRow[];
  warnings: string[];
}

export interface ShowcaseDashboard {
  activeRunId: string;
  strategyName: string;
  claimBoundary: ClaimBoundary;
  realData?: RealDataComparison;
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
  interactiveResearch: InteractiveResearchPayload;
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

function isInteractiveRowsSorted(rows: InteractiveResearchRow[]): boolean {
  return rows.every((row, index) => index === 0 || rows[index - 1].oosNetSharpe >= row.oosNetSharpe);
}

function isSha256(value: unknown): value is string {
  return typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
}

function assertInteractiveResearch(value: unknown): asserts value is InteractiveResearchPayload {
  if (!isRecord(value)) {
    throw new Error("interactive research payload must be an object");
  }
  if (
    !["static_replay", "live_compute"].includes(String(value.mode)) ||
    !["computed", "fail_closed"].includes(String(value.status))
  ) {
    throw new Error("interactive research must declare a supported mode (static_replay|live_compute) and status");
  }
  if (value.claimBoundary !== "no_alpha_claim") {
    throw new Error("interactive research must preserve no_alpha_claim");
  }
  if (value.metricAuthority !== "out_of_sample_net_only") {
    throw new Error("interactive research must use out_of_sample_net_only metrics");
  }
  if (!isRecord(value.dataLineage)) {
    throw new Error("interactive research must include data lineage");
  }
  if (
    value.dataLineage.source !== "cr_b21_approximate_backfill" ||
    value.dataLineage.approximateAvailability !== true ||
    value.dataLineage.strictPitExcluded !== true ||
    value.dataLineage.warning !== "research_mode_approximate_availability"
  ) {
    throw new Error("interactive research must disclose approximate CR-B21 data and strict PIT exclusion");
  }
  if (
    !isRecord(value.artifact) ||
    typeof value.artifact.experimentId !== "string" ||
    value.artifact.experimentId.length < 8 ||
    !isSha256(value.artifact.reportChecksum)
  ) {
    throw new Error("interactive research artifact lineage must include experiment id and checksum");
  }
  if (!Array.isArray(value.rows) || value.rows.length < 2) {
    throw new Error("interactive research must include model and baseline rows");
  }
  if (!value.rows.some((row) => isRecord(row) && row.isBaseline === true)) {
    throw new Error("interactive research must keep a visible baseline row");
  }
  if (!isInteractiveRowsSorted(value.rows as InteractiveResearchRow[])) {
    throw new Error("interactive research rows must be ranked by descending OOS-net Sharpe");
  }
  if (!Array.isArray(value.warnings) || !value.warnings.includes("no_alpha_claim")) {
    throw new Error("interactive research warnings must preserve no_alpha_claim");
  }
  if (!value.warnings.includes("research_mode_approximate_availability")) {
    throw new Error("interactive research warnings must include approximate data disclosure");
  }
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
  assertInteractiveResearch(value.interactiveResearch);
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
  if (value.realData !== undefined) {
    const real = value.realData;
    if (
      !isRecord(real) ||
      real.source !== "real_data_oos_backtest_artifact" ||
      real.status !== "computed" ||
      real.claimBoundary !== "no_alpha_claim"
    ) {
      throw new Error("realData must be a computed real_data_oos_backtest_artifact under no_alpha_claim");
    }
    if (!Array.isArray(real.rows) || real.rows.length < 2) {
      throw new Error("realData must carry the candidate and baseline rows");
    }
    if (!real.rows.some((row) => isRecord(row) && row.isBaseline === true)) {
      throw new Error("realData must keep a visible baseline row");
    }
    const sharpes = (real.rows as RealDataOosRow[]).map((row) => row.oosNetSharpe);
    if (!sharpes.every((value, index) => index === 0 || sharpes[index - 1] >= value)) {
      throw new Error("realData rows must be ranked by descending OOS-net Sharpe");
    }
  }
}
