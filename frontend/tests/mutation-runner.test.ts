import { describe, expect, it } from "vitest";

import {
  mutations,
  parseMutationArgs,
  selectMutations,
} from "../scripts/run-mutation-checks.mjs";

describe("frontend mutation runner CLI selection", () => {
  it("selects all configured mutations by default", () => {
    expect(selectMutations()).toHaveLength(mutations.length);
    expect(mutations).toHaveLength(29);
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-public-demo-probe-manifest-colocation",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-public-demo-probe-incomplete-manifest-failclosed",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-public-demo-probe-absolute-output-path",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-public-demo-export-absolute-output-dir",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-public-demo-export-stale-evidence-gate",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-smoke-html-api-parity-regression",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-h3-interactive-claim-boundary",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-h3-approximate-warning-gate",
    );
    expect(mutations.map((mutation) => mutation.name)).toContain(
      "frontend-h3-e2e-failclosed-status-gate",
    );
  });

  it("supports focused --only mutation runs", () => {
    const options = parseMutationArgs(["--only", "frontend-static-export-showcase-sync"]);
    const selected = selectMutations(options);

    expect(selected.map((mutation) => mutation.name)).toEqual([
      "frontend-static-export-showcase-sync",
    ]);
  });

  it("supports listing without selecting a mutation and rejects unknown selectors", () => {
    expect(parseMutationArgs(["--list"])).toEqual({ list: true, only: [] });
    expect(() => parseMutationArgs(["--only"])).toThrow(/requires a mutation name/);
    expect(() => parseMutationArgs(["--bogus"])).toThrow(/unknown argument/);
    expect(() => selectMutations({ only: ["missing-mutation"] })).toThrow(/unknown mutation/);
  });
});
