import type {
  InteractiveResearchPayload,
  ResearchLifecycle,
  ResearchParameters,
} from "./showcase-contract";

// H-4 (REQ-H4-004): an explicit lifecycle state machine for live backend reruns. A slow
// or dead backend degrades to a visible `error` state (never a spinner-forever), and a new
// submission clears any prior `computed` payload so a stale result can never linger.

export interface LiveRerunState {
  lifecycle: ResearchLifecycle;
  payload?: InteractiveResearchPayload;
  message?: string;
}

export type LiveRerunAction =
  | { type: "submit" }
  | { type: "computed"; payload: InteractiveResearchPayload }
  | { type: "fail_closed"; message: string }
  | { type: "error"; message: string }
  | { type: "reset" };

export const initialLiveRerunState: LiveRerunState = { lifecycle: "idle" };

export const DEFAULT_RERUN_ENDPOINT = "/api/experiment/rerun";
export const DEFAULT_RERUN_TIMEOUT_MS = 20000;

export function liveRerunReducer(state: LiveRerunState, action: LiveRerunAction): LiveRerunState {
  switch (action.type) {
    case "submit":
      // drop any prior payload/message: while computing nothing stale is shown
      return { lifecycle: "computing" };
    case "computed":
      return { lifecycle: "computed", payload: action.payload };
    case "fail_closed":
      return { lifecycle: "fail_closed", message: action.message };
    case "error":
      return { lifecycle: "error", message: action.message };
    case "reset":
      return initialLiveRerunState;
    default:
      return state;
  }
}

export interface RequestLiveRerunOptions {
  endpoint?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
}

/**
 * Call the live backend rerun endpoint with a bounded timeout and map the response to a
 * reducer action. Never throws: timeout/abort/network/parse failures all resolve to an
 * `error` action so the UI can render a visible error state instead of hanging.
 */
export async function requestLiveRerun(
  parameters: ResearchParameters,
  options: RequestLiveRerunOptions = {},
): Promise<LiveRerunAction> {
  const endpoint = options.endpoint ?? DEFAULT_RERUN_ENDPOINT;
  const timeoutMs = options.timeoutMs ?? DEFAULT_RERUN_TIMEOUT_MS;
  const fetchImpl = options.fetchImpl ?? fetch;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ parameters }),
      signal: controller.signal,
    });
    const data: unknown = await response.json().catch(() => null);
    const record = (data && typeof data === "object") ? (data as Record<string, unknown>) : null;
    const status = record ? String(record.status) : "";
    if (response.ok && status === "computed") {
      return { type: "computed", payload: data as InteractiveResearchPayload };
    }
    if (status === "fail_closed") {
      return { type: "fail_closed", message: String(record?.message ?? "rerun failed closed") };
    }
    return {
      type: "error",
      message: String(record?.message ?? `live rerun error (status ${response.status})`),
    };
  } catch (error) {
    const name = (error as { name?: string })?.name;
    const message = name === "AbortError"
      ? "live rerun timed out"
      : `live rerun unreachable: ${(error as Error)?.message ?? "unknown error"}`;
    return { type: "error", message };
  } finally {
    clearTimeout(timer);
  }
}
