"use client";

import { useEffect, useMemo, useReducer, useState } from "react";

import {
  resolveInteractiveResearchSelection,
  validateInteractiveResearchParameters,
} from "../lib/interactive-research";
import {
  initialLiveRerunState,
  liveRerunReducer,
  requestLiveRerun,
} from "../lib/live-rerun";
import type {
  InteractiveResearchPayload,
  ResearchBackend,
  ResearchParameters,
  ResearchRebalance,
} from "../lib/showcase-contract";
import { LiveRerunStatus } from "./LiveRerunStatus";

function metric(value: number): string {
  return value.toFixed(2);
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function setNumber<K extends keyof ResearchParameters>(
  params: ResearchParameters,
  key: K,
  value: string,
): ResearchParameters {
  return { ...params, [key]: Number(value) };
}

function seriesBars(points: { label: string; value: number }[], scale = 1) {
  return points.map((point) => (
    <span key={`${point.label}-${point.value}`} title={`${point.label} ${point.value}`}>
      <i style={{ inlineSize: `${Math.max(4, Math.min(100, Math.abs(point.value * scale)))}%` }} />
    </span>
  ));
}

export function InteractiveResearchPanel({ data }: { data: InteractiveResearchPayload }) {
  const [params, setParams] = useState<ResearchParameters>(data.parameters);
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    setHydrated(true);
  }, []);
  const validation = useMemo(
    () => validateInteractiveResearchParameters(params, data.parameterRanges),
    [data.parameterRanges, params],
  );
  const selection = useMemo(() => resolveInteractiveResearchSelection(data, params), [data, params]);
  const modelRow = selection.rows?.find((row) => !row.isBaseline);
  const baselineRow = selection.rows?.find((row) => row.isBaseline);

  // H-4 (REQ-H4-001/004): additive live backend rerun. When no backend is configured the
  // proxy route returns a static-replay fallback and the lifecycle settles on fail_closed,
  // so the static replay above stays the visible result. A live computed result never
  // overwrites the honesty guards — the payload is contract-validated server-side.
  const [liveState, dispatch] = useReducer(liveRerunReducer, initialLiveRerunState);
  const runLive = async () => {
    if (!validation.ok) {
      dispatch({ type: "fail_closed", message: validation.errors.join("; ") });
      return;
    }
    dispatch({ type: "submit" });
    dispatch(await requestLiveRerun(params));
  };

  return (
    <section className="panel interactive-panel" data-section="interactive-research" data-hydrated={hydrated}>
      <div className="panel-heading">
        <h2>Interactive Research</h2>
        <p>
          {data.mode} · {data.claimBoundary} · {data.metricAuthority}
        </p>
      </div>

      <div className="research-grid">
        <label>
          Backend
          <select
            data-control="backend"
            value={params.backend}
            onChange={(event) => setParams({ ...params, backend: event.target.value as ResearchBackend })}
          >
            {data.parameterRanges.backend.map((backend) => (
              <option key={backend} value={backend}>
                {backend}
              </option>
            ))}
          </select>
        </label>
        <label>
          Hidden
          <input
            data-control="hiddenUnits"
            type="number"
            value={params.hiddenUnits}
            min={data.parameterRanges.hiddenUnits.min}
            max={data.parameterRanges.hiddenUnits.max}
            step={data.parameterRanges.hiddenUnits.step}
            onChange={(event) => setParams(setNumber(params, "hiddenUnits", event.target.value))}
          />
        </label>
        <label>
          Lookback
          <input
            data-control="lookback"
            type="number"
            value={params.lookback}
            min={data.parameterRanges.lookback.min}
            max={data.parameterRanges.lookback.max}
            step={data.parameterRanges.lookback.step}
            onChange={(event) => setParams(setNumber(params, "lookback", event.target.value))}
          />
        </label>
        <label>
          Epochs
          <input
            data-control="epochs"
            type="number"
            value={params.epochs}
            min={data.parameterRanges.epochs.min}
            max={data.parameterRanges.epochs.max}
            step={data.parameterRanges.epochs.step}
            onChange={(event) => setParams(setNumber(params, "epochs", event.target.value))}
          />
        </label>
        <label>
          Seed
          <input
            data-control="seed"
            type="number"
            value={params.seed}
            min={data.parameterRanges.seed.min}
            max={data.parameterRanges.seed.max}
            step={data.parameterRanges.seed.step}
            onChange={(event) => setParams(setNumber(params, "seed", event.target.value))}
          />
        </label>
        <label>
          Rebalance
          <select
            data-control="rebalance"
            value={params.rebalance}
            onChange={(event) => setParams({ ...params, rebalance: event.target.value as ResearchRebalance })}
          >
            {data.parameterRanges.rebalance.map((rebalance) => (
              <option key={rebalance} value={rebalance}>
                {rebalance}
              </option>
            ))}
          </select>
        </label>
        <label className="artifact-select">
          Artifact
          <select value={data.artifact.experimentId} onChange={() => undefined}>
            <option value={data.artifact.experimentId}>{data.artifact.experimentId}</option>
          </select>
        </label>
      </div>

      <div className="live-rerun-controls">
        <button type="button" data-control="run-live-rerun" onClick={runLive} disabled={!hydrated}>
          Run live rerun
        </button>
        <LiveRerunStatus state={liveState} />
      </div>

      <div className="research-status" data-status={selection.status}>
        <span>{selection.status}</span>
        <span>{selection.message}</span>
        <span>
          resolved backend: {data.resolvedBackend.resolved}
          {data.resolvedBackend.fallbackReason ? ` (${data.resolvedBackend.fallbackReason})` : ""}
        </span>
        <span>{data.dataLineage.warning}</span>
        <span>checksum {data.artifact.reportChecksum.slice(0, 12)}</span>
      </div>

      {!validation.ok && (
        <div className="warnings" role="status">
          {validation.errors.map((error) => (
            <span key={error}>{error}</span>
          ))}
        </div>
      )}

      {selection.status === "computed" && modelRow && baselineRow ? (
        <>
          <table>
            <thead>
              <tr>
                <th>Strategy</th>
                <th>OOS-net Sharpe</th>
                <th>CAGR</th>
                <th>Max drawdown</th>
                <th>Baseline</th>
              </tr>
            </thead>
            <tbody>
              {selection.rows?.map((row) => (
                <tr key={row.strategyName}>
                  <td>{row.strategyName}</td>
                  <td>{metric(row.oosNetSharpe)}</td>
                  <td>{pct(row.oosNetCagr)}</td>
                  <td>{pct(row.maxDrawdown)}</td>
                  <td>{row.isBaseline ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="research-chart-grid">
            <div>
              <strong>Equity</strong>
              <div className="mini-bars">{seriesBars(modelRow.equityCurve, 70)}</div>
            </div>
            <div>
              <strong>Drawdown</strong>
              <div className="mini-bars drawdown">{seriesBars(modelRow.drawdown, 420)}</div>
            </div>
            <div>
              <strong>Distribution</strong>
              <div className="mini-bars">{seriesBars(modelRow.returnDistribution.map((value, index) => ({
                label: `r${index}`,
                value,
              })), 900)}</div>
            </div>
            <div>
              <strong>Learning Curve</strong>
              <div className="mini-bars">{seriesBars(modelRow.learningCurve, 2600)}</div>
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">fail_closed</div>
      )}
    </section>
  );
}
