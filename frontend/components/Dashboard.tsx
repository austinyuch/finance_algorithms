import type { ShowcaseDashboard } from "../lib/showcase-contract";

function formatWeight(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatSharpe(value: number): string {
  return value.toFixed(2);
}

export function Dashboard({ data }: { data: ShowcaseDashboard }) {
  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p>QuantLab Showcase</p>
        <h1>Research Dashboard</h1>
        <span>{data.claimBoundary}</span>
      </header>

      <section className="panel leaderboard-panel" data-section="leaderboard">
        <div className="panel-heading">
          <h2>Leaderboard</h2>
          <p>OOS net Sharpe, sorted descending</p>
        </div>
        <table>
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Run</th>
              <th>Sharpe</th>
              <th>Baseline</th>
            </tr>
          </thead>
          <tbody>
            {data.leaderboard.map((row) => (
              <tr key={row.runId}>
                <td>{row.strategyName}</td>
                <td>{row.runId}</td>
                <td>{formatSharpe(row.oosNetSharpe)}</td>
                <td>{row.isBaseline ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel" data-section="allocation-regime">
        <div className="panel-heading">
          <h2>Allocation / Regime</h2>
          <p>{data.regime.label} · confidence {data.regime.confidence.toFixed(2)}</p>
        </div>
        <div className="allocation-grid">
          {Object.entries(data.allocation).map(([symbol, weight]) => (
            <div className="allocation-row" key={symbol}>
              <span>{symbol}</span>
              <strong>{formatWeight(weight)}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" data-section="rebalance">
        <div className="panel-heading">
          <h2>Rebalance</h2>
          <p>{data.rebalanceDates.length} scheduled dates</p>
        </div>
        <ol className="date-list">
          {data.rebalanceDates.map((date) => (
            <li key={date}>{date}</li>
          ))}
        </ol>
      </section>

      <section className="panel experiments-panel" data-section="experiments">
        <div className="panel-heading">
          <h2>Experiment Registry</h2>
          <p>{data.experiments.length} research entries</p>
        </div>
        <table>
          <thead>
            <tr>
              <th>Family</th>
              <th>Strategy</th>
              <th>Readiness</th>
              <th>Claim</th>
            </tr>
          </thead>
          <tbody>
            {data.experiments.map((row) => (
              <tr key={row.experimentId}>
                <td>{row.modelFamily}</td>
                <td>{row.strategyName}</td>
                <td>{row.readiness}</td>
                <td>{row.claimBoundary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel evidence-panel" data-section="evidence">
        <div className="panel-heading">
          <h2>Evidence</h2>
          <p>{data.evidence.readiness}</p>
        </div>
        <div className="readiness-grid">
          <span>{data.demoReadiness.claim}</span>
          <span>Public hosting: {data.demoReadiness.publicHosting}</span>
          <span>Visual regression: {data.demoReadiness.visualRegression}</span>
          <span>Dependency audit: {data.demoReadiness.dependencyAudit}</span>
        </div>
        <ul>
          {data.evidence.tests.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {data.warnings.length > 0 && (
          <div className="warnings" role="status">
            {data.warnings.map((warning) => (
              <span key={warning}>{warning}</span>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
