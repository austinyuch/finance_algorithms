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
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Table, TBody, TD, TH, THead, TR } from "./ui/table";
import { cn } from "../lib/utils";

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

  const fieldClass =
    "h-10 w-full rounded-lg border border-brand-line bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20";
  const labelClass =
    "grid gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-400";

  return (
    <Card data-section="interactive-research" data-hydrated={hydrated}>
      <CardHeader>
        <div className="min-w-0">
          <CardTitle>Interactive Research</CardTitle>
          <p className="mt-1 text-sm text-slate-500">
            {data.mode} · {data.claimBoundary} · {data.metricAuthority}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="brand">{data.mode}</Badge>
          <Badge variant="default">{data.metricAuthority}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <label className={labelClass}>
            Backend
            <select
              className={fieldClass}
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
          <label className={labelClass}>
            Hidden
            <input
              className={fieldClass}
              data-control="hiddenUnits"
              type="number"
              value={params.hiddenUnits}
              min={data.parameterRanges.hiddenUnits.min}
              max={data.parameterRanges.hiddenUnits.max}
              step={data.parameterRanges.hiddenUnits.step}
              onChange={(event) => setParams(setNumber(params, "hiddenUnits", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Lookback
            <input
              className={fieldClass}
              data-control="lookback"
              type="number"
              value={params.lookback}
              min={data.parameterRanges.lookback.min}
              max={data.parameterRanges.lookback.max}
              step={data.parameterRanges.lookback.step}
              onChange={(event) => setParams(setNumber(params, "lookback", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Epochs
            <input
              className={fieldClass}
              data-control="epochs"
              type="number"
              value={params.epochs}
              min={data.parameterRanges.epochs.min}
              max={data.parameterRanges.epochs.max}
              step={data.parameterRanges.epochs.step}
              onChange={(event) => setParams(setNumber(params, "epochs", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Seed
            <input
              className={fieldClass}
              data-control="seed"
              type="number"
              value={params.seed}
              min={data.parameterRanges.seed.min}
              max={data.parameterRanges.seed.max}
              step={data.parameterRanges.seed.step}
              onChange={(event) => setParams(setNumber(params, "seed", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Rebalance
            <select
              className={fieldClass}
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
          <label className={cn(labelClass, "sm:col-span-2")}>
            Artifact
            <select
              className={fieldClass}
              value={data.artifact.experimentId}
              onChange={() => undefined}
            >
              <option value={data.artifact.experimentId}>{data.artifact.experimentId}</option>
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-brand-line bg-brand-surface/60 px-4 py-3">
          <button
            type="button"
            data-control="run-live-rerun"
            onClick={runLive}
            disabled={!hydrated}
            className="inline-flex h-9 items-center rounded-lg bg-brand-blue px-4 text-sm font-medium text-white shadow-sm transition hover:bg-brand-blue/90 focus:outline-none focus:ring-2 focus:ring-brand-blue/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Run live rerun
          </button>
          <LiveRerunStatus state={liveState} />
        </div>

        <div
          className="flex flex-wrap items-center gap-2 rounded-xl border border-brand-line bg-white px-4 py-3 text-sm"
          data-status={selection.status}
        >
          <Badge variant={selection.status === "computed" ? "pass" : "cond"}>
            {selection.status}
          </Badge>
          <span className="text-slate-600">{selection.message}</span>
          <span className="text-slate-400">·</span>
          <span className="text-xs text-slate-500">
            resolved backend: {data.resolvedBackend.resolved}
            {data.resolvedBackend.fallbackReason ? ` (${data.resolvedBackend.fallbackReason})` : ""}
          </span>
          <Badge variant="default">{data.dataLineage.warning}</Badge>
          <span className="font-mono text-xs text-slate-500">
            checksum {data.artifact.reportChecksum.slice(0, 12)}
          </span>
        </div>

        {!validation.ok && (
          <div className="flex flex-wrap gap-2" role="status">
            {validation.errors.map((error) => (
              <Badge key={error} variant="cond">
                {error}
              </Badge>
            ))}
          </div>
        )}

        {selection.status === "computed" && modelRow && baselineRow ? (
          <>
            <Table>
              <THead>
                <TR className="hover:bg-transparent">
                  <TH>Strategy</TH>
                  <TH className="text-right">OOS-net Sharpe</TH>
                  <TH className="text-right">CAGR</TH>
                  <TH className="text-right">Max drawdown</TH>
                  <TH>Baseline</TH>
                </TR>
              </THead>
              <TBody>
                {selection.rows?.map((row) => (
                  <TR key={row.strategyName}>
                    <TD className="font-medium text-[#0f172a]">{row.strategyName}</TD>
                    <TD className="text-right font-semibold text-brand-blue">{metric(row.oosNetSharpe)}</TD>
                    <TD className="text-right">{pct(row.oosNetCagr)}</TD>
                    <TD className="text-right text-brand-orange">{pct(row.maxDrawdown)}</TD>
                    <TD>
                      {row.isBaseline ? (
                        <Badge variant="base">yes</Badge>
                      ) : (
                        <span className="text-slate-400">no</span>
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { title: "Equity", className: "mini-bars", node: seriesBars(modelRow.equityCurve, 70) },
                { title: "Drawdown", className: "mini-bars drawdown", node: seriesBars(modelRow.drawdown, 420) },
                {
                  title: "Distribution",
                  className: "mini-bars",
                  node: seriesBars(
                    modelRow.returnDistribution.map((value, index) => ({ label: `r${index}`, value })),
                    900,
                  ),
                },
                {
                  title: "Learning Curve",
                  className: "mini-bars",
                  node: seriesBars(modelRow.learningCurve, 2600),
                },
              ].map((panel) => (
                <div
                  key={panel.title}
                  className="rounded-xl border border-brand-line bg-white p-4"
                >
                  <strong className="mb-3 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {panel.title}
                  </strong>
                  <div className={panel.className}>{panel.node}</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="grid place-items-center rounded-xl border border-brand-orange/40 bg-brand-orange/5 px-4 py-8 text-sm font-semibold text-[#b8431f]">
            fail_closed
          </div>
        )}
      </CardContent>
    </Card>
  );
}
