import { describe, expect, it } from "vitest";
import fc from "fast-check";

import {
  resolveInteractiveResearchSelection,
  validateInteractiveResearchParameters,
} from "../lib/interactive-research";
import { getShowcaseDashboard } from "../lib/showcase-data";

describe("H-3 interactive research workflow", () => {
  it("accepts the committed replay parameters and resolves the artifact", () => {
    const data = getShowcaseDashboard().interactiveResearch;
    const validation = validateInteractiveResearchParameters(data.parameters, data.parameterRanges);
    const selection = resolveInteractiveResearchSelection(data, data.parameters);

    expect(validation.ok).toBe(true);
    expect(selection.status).toBe("computed");
    expect(selection.artifact?.experimentId).toBe(data.artifact.experimentId);
    expect(selection.artifact?.reportChecksum).toBe(data.artifact.reportChecksum);
    expect(selection.message).toContain("static_replay");
  });

  it("fails closed for valid parameters without a deterministic replay artifact", () => {
    const data = getShowcaseDashboard().interactiveResearch;
    const selection = resolveInteractiveResearchSelection(data, {
      ...data.parameters,
      seed: data.parameters.seed + 1,
    });

    expect(selection.status).toBe("fail_closed");
    expect(selection.artifact).toBeUndefined();
    expect(selection.message).toMatch(/No deterministic replay artifact/);
  });

  it("fails closed for invalid parameters and unknown backends", () => {
    const data = getShowcaseDashboard().interactiveResearch;

    expect(
      validateInteractiveResearchParameters(
        { ...data.parameters, backend: "alpha-engine" as never },
        data.parameterRanges,
      ),
    ).toEqual({
      ok: false,
      errors: ["backend is unsupported"],
    });
    expect(
      resolveInteractiveResearchSelection(data, { ...data.parameters, hiddenUnits: 0 }).status,
    ).toBe("fail_closed");
  });

  it("fails closed on checksum mismatch instead of rendering stale evidence", () => {
    const data = getShowcaseDashboard().interactiveResearch;
    const selection = resolveInteractiveResearchSelection(
      {
        ...data,
        artifact: { ...data.artifact, reportChecksum: "0".repeat(64) },
      },
      data.parameters,
    );

    expect(selection.status).toBe("fail_closed");
    expect(selection.message).toMatch(/checksum/);
  });

  it("PBT: integer parameter ranges define the accepted validation boundary", () => {
    const data = getShowcaseDashboard().interactiveResearch;
    fc.assert(
      fc.property(
        fc.record({
          hiddenUnits: fc.integer({ min: -5, max: 70 }),
          lookback: fc.integer({ min: -5, max: 40 }),
          epochs: fc.integer({ min: -5, max: 230 }),
          seed: fc.integer({ min: -1, max: 1000 }),
        }),
        (candidate) => {
          const params = { ...data.parameters, ...candidate };
          const result = validateInteractiveResearchParameters(params, data.parameterRanges);
          const expected =
            candidate.hiddenUnits >= data.parameterRanges.hiddenUnits.min &&
            candidate.hiddenUnits <= data.parameterRanges.hiddenUnits.max &&
            candidate.hiddenUnits % data.parameterRanges.hiddenUnits.step === 0 &&
            candidate.lookback >= data.parameterRanges.lookback.min &&
            candidate.lookback <= data.parameterRanges.lookback.max &&
            candidate.lookback % data.parameterRanges.lookback.step === 0 &&
            candidate.epochs >= data.parameterRanges.epochs.min &&
            candidate.epochs <= data.parameterRanges.epochs.max &&
            candidate.epochs % data.parameterRanges.epochs.step === 0 &&
            candidate.seed >= data.parameterRanges.seed.min &&
            candidate.seed <= data.parameterRanges.seed.max &&
            candidate.seed % data.parameterRanges.seed.step === 0;

          expect(result.ok).toBe(expected);
        },
      ),
    );
  });
});
