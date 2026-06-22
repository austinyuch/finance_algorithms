import type { LiveRerunState } from "../lib/live-rerun";

import { cn } from "../lib/utils";

// H-4 (REQ-H4-004, AC-H4-04): a pure presentational view of the live-rerun lifecycle.
// Kept free of async/effects so every state (idle/computing/computed/fail_closed/error)
// is directly render-testable. The async orchestration (button → requestLiveRerun →
// dispatch) lives in InteractiveResearchPanel; this component only maps state → markup.

const LABEL: Record<LiveRerunState["lifecycle"], string> = {
  idle: "live backend idle — showing static replay",
  computing: "computing live rerun…",
  computed: "live rerun computed",
  fail_closed: "live rerun failed closed",
  error: "live rerun error",
};

// `computing` shows a spinner (not a dot), so it is intentionally excluded here.
const DOT: Record<Exclude<LiveRerunState["lifecycle"], "computing">, string> = {
  idle: "bg-slate-400",
  computed: "bg-brand-green",
  fail_closed: "bg-brand-orange",
  error: "bg-red-500",
};

export function LiveRerunStatus({ state }: { state: LiveRerunState }) {
  const { lifecycle, payload, message } = state;
  return (
    <div
      className="inline-flex flex-wrap items-center gap-2 text-sm text-slate-600"
      data-lifecycle={lifecycle}
      role="status"
      aria-busy={lifecycle === "computing"}
    >
      {lifecycle !== "computing" && (
        <span className={cn("h-2 w-2 rounded-full", DOT[lifecycle as Exclude<LiveRerunState["lifecycle"], "computing">])} aria-hidden="true" />
      )}
      <span className="font-medium text-slate-700">{LABEL[lifecycle]}</span>
      {lifecycle === "computing" && <span className="live-rerun-spinner" aria-hidden="true" />}
      {lifecycle === "computed" && payload && (
        <span className="font-mono text-xs text-slate-500">
          {payload.mode} · {payload.claimBoundary} · checksum {payload.artifact.reportChecksum.slice(0, 12)} ·{" "}
          {payload.rows.length} rows
        </span>
      )}
      {(lifecycle === "fail_closed" || lifecycle === "error") && message && (
        <span className="text-[#b8431f]">{message}</span>
      )}
    </div>
  );
}
