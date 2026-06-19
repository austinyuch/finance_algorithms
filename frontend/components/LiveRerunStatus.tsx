import type { LiveRerunState } from "../lib/live-rerun";

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

export function LiveRerunStatus({ state }: { state: LiveRerunState }) {
  const { lifecycle, payload, message } = state;
  return (
    <div className="live-rerun-status" data-lifecycle={lifecycle} role="status" aria-busy={lifecycle === "computing"}>
      <span className="live-rerun-label">{LABEL[lifecycle]}</span>
      {lifecycle === "computing" && <span className="live-rerun-spinner" aria-hidden="true" />}
      {lifecycle === "computed" && payload && (
        <span className="live-rerun-detail">
          {payload.mode} · {payload.claimBoundary} · checksum {payload.artifact.reportChecksum.slice(0, 12)} ·{" "}
          {payload.rows.length} rows
        </span>
      )}
      {(lifecycle === "fail_closed" || lifecycle === "error") && message && (
        <span className="live-rerun-message">{message}</span>
      )}
    </div>
  );
}
