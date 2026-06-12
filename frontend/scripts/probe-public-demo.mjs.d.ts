export type ProbeFreshnessStatus = "fresh" | "stale" | "missing" | "invalid";
export type ProbeStatus = "proven" | "configured_not_observed";

export function publicHostingFreshness(
  observedAt: string | undefined,
  now: string,
  maxAgeHours?: number,
): { freshnessStatus: ProbeFreshnessStatus; maxAgeHours: number };

export function classifyProbeStatus(input: {
  httpStatus: number;
  hashStatus: "matched" | "mismatched" | "missing" | "not_checked";
  manifestContractStatus: "matched" | "mismatched" | "missing" | "not_checked";
  freshnessStatus: ProbeFreshnessStatus;
}): ProbeStatus;
