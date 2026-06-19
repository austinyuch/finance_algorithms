import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { LiveRerunStatus } from "../components/LiveRerunStatus";
import { InteractiveResearchPanel } from "../components/InteractiveResearchPanel";
import type { LiveRerunState } from "../lib/live-rerun";
import { getShowcaseDashboard } from "../lib/showcase-data";

function computedPayload() {
  return { ...getShowcaseDashboard().interactiveResearch, mode: "live_compute" as const };
}

describe("H-4 LiveRerunStatus renders every lifecycle state (AC-H4-04)", () => {
  it("idle", () => {
    const html = renderToStaticMarkup(<LiveRerunStatus state={{ lifecycle: "idle" }} />);
    expect(html).toContain('data-lifecycle="idle"');
    expect(html).toContain("static replay");
  });

  it("computing shows a busy spinner, never a stale result", () => {
    const html = renderToStaticMarkup(<LiveRerunStatus state={{ lifecycle: "computing" }} />);
    expect(html).toContain('data-lifecycle="computing"');
    expect(html).toContain('aria-busy="true"');
    expect(html).toContain("live-rerun-spinner");
    expect(html).not.toContain("checksum");
  });

  it("computed shows the live payload summary", () => {
    const state: LiveRerunState = { lifecycle: "computed", payload: computedPayload() };
    const html = renderToStaticMarkup(<LiveRerunStatus state={state} />);
    expect(html).toContain('data-lifecycle="computed"');
    expect(html).toContain("live_compute");
    expect(html).toContain("checksum");
    expect(html).toContain("rows");
  });

  it("fail_closed shows the message", () => {
    const html = renderToStaticMarkup(
      <LiveRerunStatus state={{ lifecycle: "fail_closed", message: "invalid parameters" }} />,
    );
    expect(html).toContain('data-lifecycle="fail_closed"');
    expect(html).toContain("invalid parameters");
  });

  it("error shows a visible error message (not a spinner)", () => {
    const html = renderToStaticMarkup(
      <LiveRerunStatus state={{ lifecycle: "error", message: "live rerun timed out" }} />,
    );
    expect(html).toContain('data-lifecycle="error"');
    expect(html).toContain("live rerun timed out");
    expect(html).not.toContain("live-rerun-spinner");
  });
});

describe("H-4 InteractiveResearchPanel wires the live lifecycle additively", () => {
  it("renders the run-live control and an idle lifecycle without breaking static replay", () => {
    const html = renderToStaticMarkup(
      <InteractiveResearchPanel data={getShowcaseDashboard().interactiveResearch} />,
    );
    expect(html).toContain('data-control="run-live-rerun"');
    expect(html).toContain('data-lifecycle="idle"');
    // static replay result still present
    expect(html).toContain('data-section="interactive-research"');
  });
});
