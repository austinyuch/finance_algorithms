export type ProbeFreshnessStatus = "fresh" | "stale" | "missing" | "invalid";
export type ProbeStatus = "proven" | "configured_not_observed";
export type ProbeHashStatus = "matched" | "mismatched" | "missing" | "not_checked";
export type ProbeManifestContractStatus = "matched" | "mismatched" | "missing" | "not_checked";

export interface ExpectedPublicDemoManifest {
  dataHash: string;
  targetUrl: string;
  artifactKind: string;
  claimBoundary: string;
  dashboardClaim: string;
}

export interface DeployedPublicDemoManifestContract {
  deployedTargetUrl?: string;
  deployedArtifactKind?: string;
  deployedClaimBoundary?: string;
  deployedDashboardClaim?: string;
}

export function resolveProbeOutputPath(pathFromEnv?: string, cwd?: string): string;

export function publicHostingFreshness(
  observedAt: string | undefined,
  now: string,
  maxAgeHours?: number,
): { freshnessStatus: ProbeFreshnessStatus; maxAgeHours: number };

export function classifyProbeStatus(input: {
  httpStatus: number;
  hashStatus: ProbeHashStatus;
  manifestContractStatus: ProbeManifestContractStatus;
  freshnessStatus: ProbeFreshnessStatus;
}): ProbeStatus;

export function classifyManifestContractStatus(input: {
  expected?: Partial<ExpectedPublicDemoManifest>;
  deployed?: DeployedPublicDemoManifestContract;
}): ProbeManifestContractStatus;

export function readExpectedManifest(probeOutputPath?: string): ExpectedPublicDemoManifest | undefined;
