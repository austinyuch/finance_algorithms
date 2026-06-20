import { describe, expect, it } from "vitest";

import {
  DEFAULT_RERUN_ENDPOINT,
  initialLiveRerunState,
  liveRerunReducer,
  requestLiveRerun,
  type LiveRerunState,
} from "../lib/live-rerun";
import { assertDashboardPayload } from "../lib/showcase-contract";
import type { InteractiveResearchPayload, ResearchParameters } from "../lib/showcase-contract";
import { getShowcaseDashboard } from "../lib/showcase-data";

const PARAMS: ResearchParameters = {
  backend: "reference",
  hiddenUnits: 4,
  lookback: 6,
  epochs: 20,
  seed: 0,
  rebalance: "monthly",
  symbols: ["GROWTH", "STEADY"],
};

function computedPayload(): InteractiveResearchPayload {
  // reuse the H-3 static block shape but tag it as a live computed result
  return {
    ...getShowcaseDashboard().interactiveResearch,
    mode: "live_compute",
    lifecycle: "computed",
    computeSource: "live_backend",
  };
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("H-4 live rerun lifecycle reducer", () => {
  it("starts idle", () => {
    expect(initialLiveRerunState.lifecycle).toBe("idle");
  });

  it("submit transitions to computing and clears any stale payload", () => {
    const stale: LiveRerunState = { lifecycle: "computed", payload: computedPayload() };
    const next = liveRerunReducer(stale, { type: "submit" });
    expect(next.lifecycle).toBe("computing");
    expect(next.payload).toBeUndefined();
    expect(next.message).toBeUndefined();
  });

  it("computed/fail_closed/error/reset transitions", () => {
    const payload = computedPayload();
    expect(liveRerunReducer(initialLiveRerunState, { type: "computed", payload }).lifecycle).toBe("computed");
    expect(liveRerunReducer(initialLiveRerunState, { type: "fail_closed", message: "bad" })).toEqual({
      lifecycle: "fail_closed",
      message: "bad",
    });
    expect(liveRerunReducer(initialLiveRerunState, { type: "error", message: "boom" })).toEqual({
      lifecycle: "error",
      message: "boom",
    });
    expect(liveRerunReducer({ lifecycle: "error", message: "x" }, { type: "reset" })).toEqual(
      initialLiveRerunState,
    );
  });
});

describe("H-4 requestLiveRerun bounded client", () => {
  it("maps a computed response to a computed action", async () => {
    const fetchImpl = (async () => jsonResponse(200, computedPayload())) as unknown as typeof fetch;
    const action = await requestLiveRerun(PARAMS, { fetchImpl });
    expect(action.type).toBe("computed");
  });

  it("posts to the default endpoint with a parameters body", async () => {
    let captured: { url?: string; body?: string } = {};
    const fetchImpl = (async (url: string, init: RequestInit) => {
      captured = { url, body: String(init.body) };
      return jsonResponse(200, computedPayload());
    }) as unknown as typeof fetch;
    await requestLiveRerun(PARAMS, { fetchImpl });
    expect(captured.url).toBe(DEFAULT_RERUN_ENDPOINT);
    expect(JSON.parse(captured.body ?? "{}").parameters.backend).toBe("reference");
  });

  it("maps a fail_closed response to a fail_closed action", async () => {
    const fetchImpl = (async () =>
      jsonResponse(422, { status: "fail_closed", message: "invalid" })) as unknown as typeof fetch;
    const action = await requestLiveRerun(PARAMS, { fetchImpl });
    expect(action).toEqual({ type: "fail_closed", message: "invalid" });
  });

  it("maps a non-ok non-fail-closed response to an error action", async () => {
    const fetchImpl = (async () => jsonResponse(500, { status: "error", message: "kaboom" })) as unknown as typeof fetch;
    const action = await requestLiveRerun(PARAMS, { fetchImpl });
    expect(action).toEqual({ type: "error", message: "kaboom" });
  });

  it("maps a timeout/abort to an error action (never hangs)", async () => {
    const fetchImpl = (async (_url: string, init: RequestInit) =>
      await new Promise<Response>((_resolve, reject) => {
        init.signal?.addEventListener("abort", () => {
          const err = new Error("aborted");
          err.name = "AbortError";
          reject(err);
        });
      })) as unknown as typeof fetch;
    const action = await requestLiveRerun(PARAMS, { fetchImpl, timeoutMs: 5 });
    expect(action.type).toBe("error");
    expect(action).toMatchObject({ message: expect.stringContaining("timed out") });
  });

  it("maps a network rejection to an error action", async () => {
    const fetchImpl = (async () => {
      throw new Error("ECONNREFUSED");
    }) as unknown as typeof fetch;
    const action = await requestLiveRerun(PARAMS, { fetchImpl });
    expect(action.type).toBe("error");
  });
});

describe("H-4 contract: live_compute mode shares the static honesty guards", () => {
  it("accepts a dashboard whose interactiveResearch is live_compute", () => {
    const dashboard = getShowcaseDashboard();
    const live = {
      ...dashboard,
      interactiveResearch: {
        ...dashboard.interactiveResearch,
        mode: "live_compute" as const,
        lifecycle: "computed" as const,
        computeSource: "live_backend" as const,
      },
    };
    expect(() => assertDashboardPayload(live)).not.toThrow();
  });

  it("rejects a live_compute payload that drops no_alpha_claim", () => {
    const dashboard = getShowcaseDashboard();
    const overclaim = {
      ...dashboard,
      interactiveResearch: {
        ...dashboard.interactiveResearch,
        mode: "live_compute" as const,
        claimBoundary: "alpha_claim",
      },
    };
    expect(() => assertDashboardPayload(overclaim)).toThrow();
  });
});
