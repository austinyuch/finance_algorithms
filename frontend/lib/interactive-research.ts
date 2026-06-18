import type {
  InteractiveResearchPayload,
  ResearchParameterRanges,
  ResearchParameters,
} from "./showcase-contract";

export type ValidationResult = { ok: true; errors: [] } | { ok: false; errors: string[] };

export interface ResearchReplaySelection {
  status: "computed" | "fail_closed";
  message: string;
  artifact?: InteractiveResearchPayload["artifact"];
  rows?: InteractiveResearchPayload["rows"];
}

function inIntegerRange(value: number, range: { min: number; max: number; step: number }): boolean {
  return Number.isInteger(value) && value >= range.min && value <= range.max && (value - range.min) % range.step === 0;
}

function sameParameters(a: ResearchParameters, b: ResearchParameters): boolean {
  return (
    a.backend === b.backend &&
    a.hiddenUnits === b.hiddenUnits &&
    a.lookback === b.lookback &&
    a.epochs === b.epochs &&
    a.seed === b.seed &&
    a.rebalance === b.rebalance &&
    JSON.stringify(a.symbols) === JSON.stringify(b.symbols)
  );
}

function hasValidChecksum(payload: InteractiveResearchPayload): boolean {
  return /^[a-f0-9]{64}$/.test(payload.artifact.reportChecksum) && !/^0+$/.test(payload.artifact.reportChecksum);
}

export function validateInteractiveResearchParameters(
  parameters: ResearchParameters,
  ranges: ResearchParameterRanges,
): ValidationResult {
  const errors: string[] = [];
  if (!ranges.backend.includes(parameters.backend)) {
    errors.push("backend is unsupported");
  }
  if (!ranges.rebalance.includes(parameters.rebalance)) {
    errors.push("rebalance is unsupported");
  }
  if (!inIntegerRange(parameters.hiddenUnits, ranges.hiddenUnits)) {
    errors.push("hiddenUnits is outside the supported range");
  }
  if (!inIntegerRange(parameters.lookback, ranges.lookback)) {
    errors.push("lookback is outside the supported range");
  }
  if (!inIntegerRange(parameters.epochs, ranges.epochs)) {
    errors.push("epochs is outside the supported range");
  }
  if (!inIntegerRange(parameters.seed, ranges.seed)) {
    errors.push("seed is outside the supported range");
  }
  if (!Array.isArray(parameters.symbols) || parameters.symbols.length < 2) {
    errors.push("symbols requires at least two assets");
  }
  return errors.length === 0 ? { ok: true, errors: [] } : { ok: false, errors };
}

export function resolveInteractiveResearchSelection(
  payload: InteractiveResearchPayload,
  parameters: ResearchParameters,
): ResearchReplaySelection {
  const validation = validateInteractiveResearchParameters(parameters, payload.parameterRanges);
  if (!validation.ok) {
    return {
      status: "fail_closed",
      message: validation.errors.join("; "),
    };
  }
  if (!sameParameters(payload.parameters, parameters)) {
    return {
      status: "fail_closed",
      message: "No deterministic replay artifact exists for the selected parameters.",
    };
  }
  if (!hasValidChecksum(payload)) {
    return {
      status: "fail_closed",
      message: "Artifact checksum failed closed.",
    };
  }
  if (
    payload.claimBoundary !== "no_alpha_claim" ||
    payload.metricAuthority !== "out_of_sample_net_only" ||
    payload.dataLineage.approximateAvailability !== true ||
    payload.dataLineage.strictPitExcluded !== true
  ) {
    return {
      status: "fail_closed",
      message: "Artifact evidence boundary failed closed.",
    };
  }
  return {
    status: "computed",
    message: "static_replay artifact selected",
    artifact: payload.artifact,
    rows: payload.rows,
  };
}
