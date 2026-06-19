import type { ResearchParameters } from "../../../../lib/showcase-contract";

// H-4 (REQ-H4-001/005, FMEA-H4-07): thin proxy to the Python live-rerun backend. When no
// backend URL is configured (the public static export) or the backend is unreachable, we
// return an honest non-computed response — the UI falls back to H-3 static replay and shows
// the "no live backend" boundary, never a fabricated "computed" panel. No experiment math here.

const BACKEND_ENV = "QUANTLAB_RERUN_BACKEND_URL";
const PROXY_TIMEOUT_MS = 20000;

function backendUrl(): string | null {
  const raw = process.env[BACKEND_ENV];
  return raw && raw.trim() ? raw.trim().replace(/\/$/, "") : null;
}

export async function POST(request: Request): Promise<Response> {
  const url = backendUrl();
  if (!url) {
    return Response.json(
      {
        mode: "static_replay",
        status: "fail_closed",
        lifecycle: "fail_closed",
        computeSource: "static_fallback",
        claimBoundary: "no_alpha_claim",
        message: "no live backend configured; falling back to static replay",
        reason: "no_live_backend",
      },
      { status: 200 },
    );
  }

  let body: { parameters?: ResearchParameters };
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { mode: "live_compute", status: "fail_closed", lifecycle: "fail_closed",
        computeSource: "live_backend", claimBoundary: "no_alpha_claim",
        message: "invalid JSON body", reason: "bad_request" },
      { status: 400 },
    );
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROXY_TIMEOUT_MS);
  try {
    const upstream = await fetch(`${url}/api/experiment/rerun`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ parameters: body.parameters }),
      signal: controller.signal,
    });
    const data = await upstream.json().catch(() => null);
    if (!data) {
      return Response.json(
        { mode: "live_compute", status: "error", lifecycle: "error",
          computeSource: "live_backend", claimBoundary: "no_alpha_claim",
          message: "live backend returned an unreadable response", reason: "bad_upstream" },
        { status: 502 },
      );
    }
    return Response.json(data, { status: upstream.status });
  } catch (error) {
    const name = (error as { name?: string })?.name;
    const message = name === "AbortError"
      ? "live backend timed out"
      : "live backend unreachable";
    return Response.json(
      { mode: "live_compute", status: "error", lifecycle: "error",
        computeSource: "live_backend", claimBoundary: "no_alpha_claim",
        message, reason: "backend_unreachable" },
      { status: 504 },
    );
  } finally {
    clearTimeout(timer);
  }
}
