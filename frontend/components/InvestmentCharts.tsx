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
  green: "#1d6f5f",
  copper: "#b84f2f",
  gold: "#8c6f2f",
  slate: "#52635a",
  line: "#d7dfd9",
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
              backgroundColor: data.leaderboard.map((row) => (row.isBaseline ? palette.slate : palette.green)),
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
              backgroundColor: [palette.green, palette.gold, palette.copper, palette.slate],
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
              backgroundColor: data.realData?.rows.map((row) => (row.isBaseline ? palette.slate : palette.copper)) ?? [],
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
              backgroundColor: selectedRows.map((row) => (row.isBaseline ? palette.slate : palette.green)),
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
              borderColor: palette.green,
              backgroundColor: palette.green,
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
              borderColor: palette.copper,
              backgroundColor: palette.copper,
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

  return (
    <section className="panel investment-charts-panel" data-section="investment-charts" data-hydrated={hydrated}>
      <div className="panel-heading">
        <h2>Algorithm Results Dashboard</h2>
        <p>{data.sourceMetadata.source} · {data.interactiveResearch.mode} · {data.claimBoundary}</p>
      </div>

      <div className="dashboard-controls" aria-label="Algorithm dashboard controls">
        <label>
          View
          <select value={view} onChange={(event) => setView(event.target.value as DashboardView)}>
            <option value="overview">Overview</option>
            <option value="real_data">Real-data OOS</option>
            <option value="interactive_research">Interactive research</option>
          </select>
        </label>
        <label>
          Research metric
          <select value={researchMetric} onChange={(event) => setResearchMetric(event.target.value as ResearchMetric)}>
            <option value="sharpe">OOS net Sharpe</option>
            <option value="cagr">OOS net CAGR</option>
            <option value="drawdown">Max drawdown</option>
          </select>
        </label>
        <label>
          Backend
          <select
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
        <label>
          Hidden
          <input
            data-control="dashboard-hiddenUnits"
            type="number"
            value={params.hiddenUnits}
            min={data.interactiveResearch.parameterRanges.hiddenUnits.min}
            max={data.interactiveResearch.parameterRanges.hiddenUnits.max}
            step={data.interactiveResearch.parameterRanges.hiddenUnits.step}
            onChange={(event) => setParams(setNumber(params, "hiddenUnits", event.target.value))}
          />
        </label>
        <label>
          Lookback
          <input
            data-control="dashboard-lookback"
            type="number"
            value={params.lookback}
            min={data.interactiveResearch.parameterRanges.lookback.min}
            max={data.interactiveResearch.parameterRanges.lookback.max}
            step={data.interactiveResearch.parameterRanges.lookback.step}
            onChange={(event) => setParams(setNumber(params, "lookback", event.target.value))}
          />
        </label>
        <label>
          Epochs
          <input
            data-control="dashboard-epochs"
            type="number"
            value={params.epochs}
            min={data.interactiveResearch.parameterRanges.epochs.min}
            max={data.interactiveResearch.parameterRanges.epochs.max}
            step={data.interactiveResearch.parameterRanges.epochs.step}
            onChange={(event) => setParams(setNumber(params, "epochs", event.target.value))}
          />
        </label>
        <label>
          Seed
          <input
            data-control="dashboard-seed"
            type="number"
            value={params.seed}
            min={data.interactiveResearch.parameterRanges.seed.min}
            max={data.interactiveResearch.parameterRanges.seed.max}
            step={data.interactiveResearch.parameterRanges.seed.step}
            onChange={(event) => setParams(setNumber(params, "seed", event.target.value))}
          />
        </label>
        <label>
          Rebalance
          <select
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

      <div className="dashboard-result-strip" data-status={selection.status}>
        <span>{selection.status}</span>
        <span>{selection.message}</span>
        <span>artifact {data.interactiveResearch.artifact.experimentId}</span>
        <span>checksum {data.interactiveResearch.artifact.reportChecksum.slice(0, 12)}</span>
        <span>{data.interactiveResearch.dataLineage.warning}</span>
      </div>

      {!validation.ok && (
        <div className="warnings" role="status">
          {validation.errors.map((error) => (
            <span key={error}>{error}</span>
          ))}
        </div>
      )}

      <div className="chart-grid">
        {(view === "overview" || view === "real_data") && (
          <div className="chart-card chart-wide">
            <strong>Leaderboard: OOS net Sharpe</strong>
            <canvas ref={leaderboardRef} />
          </div>
        )}
        {(view === "overview" || view === "real_data") && data.realData && (
          <div className="chart-card">
            <strong>Real-data OOS-net comparison</strong>
            <canvas ref={realDataRef} />
          </div>
        )}
        {view === "overview" && (
          <div className="chart-card">
            <strong>Current allocation</strong>
            <canvas ref={allocationRef} />
          </div>
        )}
        {view === "overview" &&
          (selection.status === "computed" && modelRow && baselineRow ? (
            <div className="chart-card">
              <strong>Interactive research: {metricLabel(researchMetric)}</strong>
              <canvas ref={researchMetricRef} />
            </div>
          ) : (
            <div className="chart-card chart-fail-closed">
              <strong>Interactive research</strong>
              <span>fail_closed</span>
              <p>{selection.message}</p>
            </div>
          ))}
        {view === "interactive_research" &&
          (selection.status === "computed" && modelRow && baselineRow ? (
            <>
              <div className="chart-card chart-wide">
                <strong>Interactive research: {metricLabel(researchMetric)}</strong>
                <canvas ref={researchMetricRef} />
              </div>
              <div className="chart-card">
                <strong>Interactive research equity curve</strong>
                <canvas ref={equityRef} />
              </div>
              <div className="chart-card">
                <strong>Drawdown path</strong>
                <canvas ref={drawdownRef} />
              </div>
            </>
          ) : (
            <div className="chart-card chart-wide chart-fail-closed">
              <strong>Interactive research</strong>
              <span>fail_closed</span>
              <p>{selection.message}</p>
            </div>
          ))}
      </div>

      {selection.status === "computed" && selectedRows.length > 0 && (
        <table className="dashboard-result-table">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>OOS-net Sharpe</th>
              <th>OOS-net CAGR</th>
              <th>Max drawdown</th>
              <th>Baseline</th>
            </tr>
          </thead>
          <tbody>
            {selectedRows.map((row) => (
              <tr key={row.strategyName}>
                <td>{row.strategyName}</td>
                <td>{row.oosNetSharpe.toFixed(2)}</td>
                <td>{pct(row.oosNetCagr)}</td>
                <td>{pct(row.maxDrawdown)}</td>
                <td>{row.isBaseline ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
