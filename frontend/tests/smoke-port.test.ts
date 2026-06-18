import { createServer } from "node:net";
import { afterEach, describe, expect, it } from "vitest";

import {
  DEFAULT_SMOKE_HOST,
  LEGACY_SMOKE_PORT,
  requestedSmokePort,
  selectSmokePort,
} from "../scripts/smoke-port.mjs";
import { assertHtmlMatchesPayload, assertPayload } from "../scripts/smoke-assertions.mjs";

const servers: Array<ReturnType<typeof createServer>> = [];

function occupy(port: number, host = DEFAULT_SMOKE_HOST) {
  return new Promise<ReturnType<typeof createServer>>((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(port, host, () => {
      servers.push(server);
      resolve(server);
    });
  });
}

afterEach(async () => {
  await Promise.all(
    servers.splice(0).map(
      (server) =>
        new Promise<void>((resolve) => {
          server.close(() => resolve());
        }),
    ),
  );
});

describe("public demo smoke port selection", () => {
  it("honors an explicit governed smoke port", () => {
    expect(requestedSmokePort({ QUANTLAB_FRONTEND_SMOKE_PORT: "32123" })).toBe(32123);

    const payload = {
      activeRunId: "forecast-run",
      strategyName: "ForecastAllocationStrategy",
      claimBoundary: "no_alpha_claim",
      regime: { label: "risk_on" },
      sourceMetadata: {
        source: "local_result_store",
        sourceRecordCount: 2,
        experimentRegistry: "experiment_registry",
      },
      demoReadiness: {
        publicHosting: "not_proven",
        visualRegression: "proven",
        dependencyAudit: "clean",
      },
      experiments: [{ readiness: "registry_only", modelFamily: "return-risk-forecast" }],
      interactiveResearch: {
        artifact: { experimentId: "h3-static-fixture" },
      },
      evidence: { tests: ["279 passed"] },
    };
    const html = [
      "Experiment Registry",
      "Interactive Research",
      "local_demo_only",
      "static_replay",
      "research_mode_approximate_availability",
      "forecast-run",
      "ForecastAllocationStrategy",
      "risk_on",
      "Public hosting: <!-- -->not_proven",
      "Visual regression: <!-- -->proven",
      "return-risk-forecast",
      "h3-static-fixture",
      "279 passed",
    ].join("\n");

    expect(() => assertPayload(payload)).not.toThrow();
    expect(() => assertHtmlMatchesPayload(html, payload)).not.toThrow();
    expect(() => assertHtmlMatchesPayload(html.replace("forecast-run", "stale-run"), payload)).toThrow(
      /active run id/,
    );
  });

  it("rejects invalid or occupied governed smoke ports", async () => {
    expect(() => requestedSmokePort({ QUANTLAB_FRONTEND_SMOKE_PORT: "not-a-port" })).toThrow(/TCP port/);
    expect(() => requestedSmokePort({ QUANTLAB_FRONTEND_SMOKE_PORT: "70000" })).toThrow(/TCP port/);

    const occupied = await occupy(0);
    const address = occupied.address();
    if (!address || typeof address === "string") {
      throw new Error("test could not allocate an occupied TCP port");
    }

    await expect(
      selectSmokePort({ QUANTLAB_FRONTEND_SMOKE_PORT: String(address.port) }, DEFAULT_SMOKE_HOST),
    ).rejects.toThrow(/already in use/);
  });

  it("chaos: avoids the legacy hard-coded smoke port when it is already occupied", async () => {
    await occupy(LEGACY_SMOKE_PORT);

    const selected = await selectSmokePort({}, DEFAULT_SMOKE_HOST);

    expect(selected).not.toBe(LEGACY_SMOKE_PORT);
    expect(selected).toBeGreaterThan(0);
  });
});
