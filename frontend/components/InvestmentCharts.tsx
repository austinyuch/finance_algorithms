"use client";

import { useEffect, useMemo, useRef, useState, type DependencyList } from "react";
import {
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  DoughnutController,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

import {
  resolveInteractiveResearchSelection,
  validateInteractiveResearchParameters,
} from "../lib/interactive-research";
import type {
  InteractiveResearchRow,
  ResearchBackend,
  ResearchParameters,
  ResearchRebalance,
  ShowcaseDashboard,
} from "../lib/showcase-contract";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Table, TBody, TD, TH, THead, TR } from "./ui/table";
import { cn } from "../lib/utils";

Chart.register(
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  DoughnutController,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
);

const palette = {
  blue: "#005EB8",
  orange: "#FF6A39",
  sky: "#04A9FB",
  slate: "#3B4559",
  line: "#e3e8f0",
};

type DashboardView = "overview" | "real_data" | "interactive_research";
type ResearchMetric = "sharpe" | "cagr" | "drawdown";

function useChart(render: (canvas: HTMLCanvasElement) => Chart, deps: DependencyList) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!ref.current) {
      return undefined;
    }

    const chart = render(ref.current);
    return () => chart.destroy();
  }, deps);

  return ref;
}

function baseOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false as const,
    plugins: {
      legend: {
        labels: {
          boxWidth: 10,
          color: palette.slate,
        },
      },
      tooltip: {
        intersect: false,
        mode: "index" as const,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: palette.slate },
      },
      y: {
        grid: { color: palette.line },
        ticks: { color: palette.slate },
      },
    },
  };
}

function setNumber<K extends keyof ResearchParameters>(
  params: ResearchParameters,
  key: K,
  value: string,
): ResearchParameters {
  return { ...params, [key]: Number(value) };
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function metricValue(row: InteractiveResearchRow, metric: ResearchMetric): number {
  if (metric === "cagr") {
    return row.oosNetCagr;
  }
  if (metric === "drawdown") {
    return row.maxDrawdown;
  }
  return row.oosNetSharpe;
}

function metricLabel(metric: ResearchMetric): string {
  if (metric === "cagr") {
    return "OOS net CAGR";
  }
  if (metric === "drawdown") {
    return "Max drawdown";
  }
  return "OOS net Sharpe";
}

export function InvestmentCharts({ data }: { data: ShowcaseDashboard }) {
  const [view, setView] = useState<DashboardView>("overview");
  const [researchMetric, setResearchMetric] = useState<ResearchMetric>("sharpe");
  const [params, setParams] = useState<ResearchParameters>(data.interactiveResearch.parameters);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  const validation = useMemo(
    () => validateInteractiveResearchParameters(params, data.interactiveResearch.parameterRanges),
    [data.interactiveResearch.parameterRanges, params],
  );
  const selection = useMemo(
    () => resolveInteractiveResearchSelection(data.interactiveResearch, params),
    [data.interactiveResearch, params],
  );
  const selectedRows = selection.rows ?? [];
  const modelRow = selectedRows.find((row) => !row.isBaseline);
  const baselineRow = selectedRows.find((row) => row.isBaseline);

  const leaderboardRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: data.leaderboard.map((row) => row.strategyName),
          datasets: [
            {
              label: "OOS net Sharpe",
              data: data.leaderboard.map((row) => row.oosNetSharpe),
              backgroundColor: data.leaderboard.map((row) => (row.isBaseline ? palette.slate : palette.blue)),
              borderRadius: 5,
            },
          ],
        },
        options: baseOptions(),
      }),
    [data.leaderboard],
  );

  const allocationRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "doughnut",
        data: {
          labels: Object.keys(data.allocation),
          datasets: [
            {
              label: "Allocation",
              data: Object.values(data.allocation).map((value) => value * 100),
              backgroundColor: [palette.blue, palette.sky, palette.orange, palette.slate],
              borderColor: "#ffffff",
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { color: palette.slate, boxWidth: 10 },
            },
          },
        },
      }),
    [data.allocation],
  );

  const realDataRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: data.realData?.rows.map((row) => row.strategyName) ?? [],
          datasets: [
            {
              label: "Real-data OOS-net Sharpe",
              data: data.realData?.rows.map((row) => row.oosNetSharpe) ?? [],
              backgroundColor: data.realData?.rows.map((row) => (row.isBaseline ? palette.slate : palette.orange)) ?? [],
              borderRadius: 5,
            },
          ],
        },
        options: baseOptions(),
      }),
    [data.realData],
  );

  const researchMetricRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: selectedRows.map((row) => row.strategyName),
          datasets: [
            {
              label: metricLabel(researchMetric),
              data: selectedRows.map((row) => metricValue(row, researchMetric)),
              backgroundColor: selectedRows.map((row) => (row.isBaseline ? palette.slate : palette.blue)),
              borderRadius: 5,
            },
          ],
        },
        options: baseOptions(),
      }),
    [selectedRows, researchMetric],
  );

  const equityRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "line",
        data: {
          labels: modelRow?.equityCurve.map((point) => point.label) ?? [],
          datasets: [
            {
              label: modelRow?.strategyName ?? "Model",
              data: modelRow?.equityCurve.map((point) => point.value) ?? [],
              borderColor: palette.blue,
              backgroundColor: palette.blue,
              tension: 0.25,
            },
            {
              label: baselineRow?.strategyName ?? "Baseline",
              data: baselineRow?.equityCurve.map((point) => point.value) ?? [],
              borderColor: palette.slate,
              backgroundColor: palette.slate,
              tension: 0.25,
            },
          ],
        },
        options: baseOptions(),
      }),
    [modelRow, baselineRow],
  );

  const drawdownRef = useChart(
    (canvas) =>
      new Chart(canvas, {
        type: "line",
        data: {
          labels: modelRow?.drawdown.map((point) => point.label) ?? [],
          datasets: [
            {
              label: `${modelRow?.strategyName ?? "Model"} drawdown`,
              data: modelRow?.drawdown.map((point) => point.value) ?? [],
              borderColor: palette.orange,
              backgroundColor: palette.orange,
              tension: 0.25,
            },
            {
              label: `${baselineRow?.strategyName ?? "Baseline"} drawdown`,
              data: baselineRow?.drawdown.map((point) => point.value) ?? [],
              borderColor: palette.slate,
              backgroundColor: palette.slate,
              tension: 0.25,
            },
          ],
        },
        options: baseOptions(),
      }),
    [modelRow, baselineRow],
  );

  const fieldClass =
    "h-10 w-full rounded-lg border border-brand-line bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20";
  const labelClass =
    "grid gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-400";

  const ChartCard = ({
    title,
    wide,
    children,
  }: {
    title: string;
    wide?: boolean;
    children: React.ReactNode;
  }) => (
    <div
      className={cn(
        "rounded-xl border border-brand-line bg-white p-3.5",
        wide && "sm:col-span-2",
      )}
    >
      <strong className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </strong>
      {children}
    </div>
  );

  return (
    <Card data-section="investment-charts" data-hydrated={hydrated}>
      <CardHeader>
        <div className="min-w-0">
          <CardTitle>Algorithm Results Dashboard</CardTitle>
          <p className="mt-1 text-sm text-slate-500">
            {data.sourceMetadata.source} · {data.interactiveResearch.mode} · {data.claimBoundary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="brand">{data.interactiveResearch.mode}</Badge>
          <Badge variant="default">{data.claimBoundary}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div
          className="grid grid-cols-2 gap-3 sm:grid-cols-4"
          aria-label="Algorithm dashboard controls"
        >
          <label className={labelClass}>
            View
            <select
              className={fieldClass}
              value={view}
              onChange={(event) => setView(event.target.value as DashboardView)}
            >
              <option value="overview">Overview</option>
              <option value="real_data">Real-data OOS</option>
              <option value="interactive_research">Interactive research</option>
            </select>
          </label>
          <label className={labelClass}>
            Research metric
            <select
              className={fieldClass}
              value={researchMetric}
              onChange={(event) => setResearchMetric(event.target.value as ResearchMetric)}
            >
              <option value="sharpe">OOS net Sharpe</option>
              <option value="cagr">OOS net CAGR</option>
              <option value="drawdown">Max drawdown</option>
            </select>
          </label>
          <label className={labelClass}>
            Backend
            <select
              className={fieldClass}
              data-control="dashboard-backend"
              value={params.backend}
              onChange={(event) => setParams({ ...params, backend: event.target.value as ResearchBackend })}
            >
              {data.interactiveResearch.parameterRanges.backend.map((backend) => (
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
              data-control="dashboard-hiddenUnits"
              type="number"
              value={params.hiddenUnits}
              min={data.interactiveResearch.parameterRanges.hiddenUnits.min}
              max={data.interactiveResearch.parameterRanges.hiddenUnits.max}
              step={data.interactiveResearch.parameterRanges.hiddenUnits.step}
              onChange={(event) => setParams(setNumber(params, "hiddenUnits", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Lookback
            <input
              className={fieldClass}
              data-control="dashboard-lookback"
              type="number"
              value={params.lookback}
              min={data.interactiveResearch.parameterRanges.lookback.min}
              max={data.interactiveResearch.parameterRanges.lookback.max}
              step={data.interactiveResearch.parameterRanges.lookback.step}
              onChange={(event) => setParams(setNumber(params, "lookback", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Epochs
            <input
              className={fieldClass}
              data-control="dashboard-epochs"
              type="number"
              value={params.epochs}
              min={data.interactiveResearch.parameterRanges.epochs.min}
              max={data.interactiveResearch.parameterRanges.epochs.max}
              step={data.interactiveResearch.parameterRanges.epochs.step}
              onChange={(event) => setParams(setNumber(params, "epochs", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Seed
            <input
              className={fieldClass}
              data-control="dashboard-seed"
              type="number"
              value={params.seed}
              min={data.interactiveResearch.parameterRanges.seed.min}
              max={data.interactiveResearch.parameterRanges.seed.max}
              step={data.interactiveResearch.parameterRanges.seed.step}
              onChange={(event) => setParams(setNumber(params, "seed", event.target.value))}
            />
          </label>
          <label className={labelClass}>
            Rebalance
            <select
              className={fieldClass}
              data-control="dashboard-rebalance"
              value={params.rebalance}
              onChange={(event) => setParams({ ...params, rebalance: event.target.value as ResearchRebalance })}
            >
              {data.interactiveResearch.parameterRanges.rebalance.map((rebalance) => (
                <option key={rebalance} value={rebalance}>
                  {rebalance}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div
          className="flex flex-wrap items-center gap-2 rounded-xl border border-brand-line bg-brand-surface/60 px-4 py-3 text-sm"
          data-status={selection.status}
        >
          <Badge variant={selection.status === "computed" ? "pass" : "cond"}>
            {selection.status}
          </Badge>
          <span className="text-slate-600">{selection.message}</span>
          <span className="text-slate-400">·</span>
          <span className="font-mono text-xs text-slate-500">
            artifact {data.interactiveResearch.artifact.experimentId}
          </span>
          <span className="font-mono text-xs text-slate-500">
            checksum {data.interactiveResearch.artifact.reportChecksum.slice(0, 12)}
          </span>
          <Badge variant="default">{data.interactiveResearch.dataLineage.warning}</Badge>
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

        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {(view === "overview" || view === "real_data") && (
            <ChartCard title="Leaderboard: OOS net Sharpe" wide>
              <div className="h-[180px]">
                <canvas ref={leaderboardRef} />
              </div>
            </ChartCard>
          )}
          {(view === "overview" || view === "real_data") && data.realData && (
            <ChartCard title="Real-data OOS-net comparison">
              <div className="h-[180px]">
                <canvas ref={realDataRef} />
              </div>
            </ChartCard>
          )}
          {view === "overview" && (
            <ChartCard title="Allocation mix">
              <div className="h-[180px]">
                <canvas ref={allocationRef} />
              </div>
            </ChartCard>
          )}
          {view === "overview" &&
            (selection.status === "computed" && modelRow && baselineRow ? (
              <ChartCard title={`Interactive research: ${metricLabel(researchMetric)}`}>
                <div className="h-[180px]">
                  <canvas ref={researchMetricRef} />
                </div>
              </ChartCard>
            ) : (
              <div className="grid content-start gap-1.5 rounded-xl border border-brand-orange/40 bg-brand-orange/5 p-3.5">
                <strong className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Interactive research
                </strong>
                <Badge variant="cond" className="w-fit">
                  fail_closed
                </Badge>
                <p className="text-sm text-slate-500">{selection.message}</p>
              </div>
            ))}
          {view === "interactive_research" &&
            (selection.status === "computed" && modelRow && baselineRow ? (
              <>
                <ChartCard title={`Interactive research: ${metricLabel(researchMetric)}`} wide>
                  <div className="h-[180px]">
                    <canvas ref={researchMetricRef} />
                  </div>
                </ChartCard>
                <ChartCard title="Interactive equity path">
                  <div className="h-[180px]">
                    <canvas ref={equityRef} />
                  </div>
                </ChartCard>
                <ChartCard title="Drawdown path">
                  <div className="h-[180px]">
                    <canvas ref={drawdownRef} />
                  </div>
                </ChartCard>
              </>
            ) : (
              <div className="grid content-start gap-1.5 rounded-xl border border-brand-orange/40 bg-brand-orange/5 p-3.5 sm:col-span-2">
                <strong className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Interactive research
                </strong>
                <Badge variant="cond" className="w-fit">
                  fail_closed
                </Badge>
                <p className="text-sm text-slate-500">{selection.message}</p>
              </div>
            ))}
        </div>

        {selection.status === "computed" && selectedRows.length > 0 && (
          <Table>
            <THead>
              <TR className="hover:bg-transparent">
                <TH>Strategy</TH>
                <TH className="text-right">OOS-net Sharpe</TH>
                <TH className="text-right">OOS-net CAGR</TH>
                <TH className="text-right">Max drawdown</TH>
                <TH>Baseline</TH>
              </TR>
            </THead>
            <TBody>
              {selectedRows.map((row) => (
                <TR key={row.strategyName}>
                  <TD className="font-medium text-[#0f172a]">{row.strategyName}</TD>
                  <TD className="text-right font-semibold text-brand-blue">{row.oosNetSharpe.toFixed(2)}</TD>
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
        )}
      </CardContent>
    </Card>
  );
}
