import type { ShowcaseDashboard } from "../lib/showcase-contract";
import { InvestmentCharts } from "./InvestmentCharts";
import { InteractiveResearchPanel } from "./InteractiveResearchPanel";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Table, TBody, TD, TH, THead, TR } from "./ui/table";

function formatWeight(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatSharpe(value: number): string {
  return value.toFixed(2);
}

function PanelHeading({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <CardHeader>
      <div className="min-w-0">
        <CardTitle>{title}</CardTitle>
        {subtitle ? (
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </CardHeader>
  );
}

export function Dashboard({ data }: { data: ShowcaseDashboard }) {
  return (
    <main className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:py-10">
      {/* Dark brand hero */}
      <header className="hero-gradient relative overflow-hidden rounded-3xl px-7 py-9 text-white shadow-[0_20px_60px_-24px_rgba(10,14,26,0.7)] sm:px-10 sm:py-12">
        <div className="relative z-10 flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-brand-sky">
              QuantLab Showcase
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Research Dashboard
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-300">
              Historical mechanism evidence from the local result store — out-of-sample net
              metrics only. No live trading, no current allocation guidance.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="brand" className="border-white/20 bg-white/10 text-white">
              {data.claimBoundary}
            </Badge>
            <Badge variant="default" className="border-white/15 bg-white/5 text-slate-200">
              {data.evidence.readiness}
            </Badge>
          </div>
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-sky/20 blur-3xl"
        />
      </header>

      <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Investment charts span the full width */}
        <div className="lg:col-span-2">
          <InvestmentCharts data={data} />
        </div>

        {/* Leaderboard — full width */}
        <Card className="lg:col-span-2" data-section="leaderboard">
          <PanelHeading
            title="Leaderboard"
            subtitle="OOS net Sharpe, sorted descending"
          />
          <CardContent className="pt-1">
            <Table>
              <THead>
                <TR className="hover:bg-transparent">
                  <TH>Strategy</TH>
                  <TH>Run</TH>
                  <TH className="text-right">Sharpe</TH>
                  <TH>Baseline</TH>
                </TR>
              </THead>
              <TBody>
                {data.leaderboard.map((row) => (
                  <TR key={row.runId}>
                    <TD className="font-medium text-[#0f172a]">{row.strategyName}</TD>
                    <TD className="font-mono text-xs text-slate-500">{row.runId}</TD>
                    <TD className="text-right font-semibold text-brand-blue">
                      {formatSharpe(row.oosNetSharpe)}
                    </TD>
                    <TD>
                      {row.isBaseline ? (
                        <Badge variant="base">Yes</Badge>
                      ) : (
                        <span className="text-slate-400">No</span>
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </CardContent>
        </Card>

        {/* Allocation / Regime */}
        <Card data-section="allocation-regime">
          <PanelHeading
            title="Allocation / Regime"
            subtitle={
              <span>
                {data.regime.label} ·{" "}
                <span className="tabular-nums">confidence {data.regime.confidence.toFixed(2)}</span>
              </span>
            }
            action={<Badge variant="brand">{data.regime.label}</Badge>}
          />
          <CardContent className="space-y-3">
            {Object.entries(data.allocation).map(([symbol, weight]) => (
              <div key={symbol} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-700">{symbol}</span>
                  <strong className="tabular-nums text-brand-blue">{formatWeight(weight)}</strong>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-sky"
                    style={{ width: formatWeight(weight) }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Rebalance */}
        <Card data-section="rebalance">
          <PanelHeading
            title="Rebalance"
            subtitle={`${data.rebalanceDates.length} scheduled dates`}
          />
          <CardContent>
            <ol className="space-y-0">
              {data.rebalanceDates.map((date) => (
                <li
                  key={date}
                  className="flex items-center gap-3 border-b border-brand-line/70 py-2.5 text-sm last:border-0"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-sky" aria-hidden />
                  <span className="font-mono tabular-nums text-slate-600">{date}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>

        {/* Experiment registry — full width */}
        <Card className="lg:col-span-2" data-section="experiments">
          <PanelHeading
            title="Experiment Registry"
            subtitle={`${data.experiments.length} research entries`}
          />
          <CardContent className="pt-1">
            <Table>
              <THead>
                <TR className="hover:bg-transparent">
                  <TH>Family</TH>
                  <TH>Strategy</TH>
                  <TH>Readiness</TH>
                  <TH>Claim</TH>
                </TR>
              </THead>
              <TBody>
                {data.experiments.map((row) => (
                  <TR key={row.experimentId}>
                    <TD className="font-mono text-xs text-slate-500">{row.modelFamily}</TD>
                    <TD className="font-medium text-[#0f172a]">{row.strategyName}</TD>
                    <TD>
                      <Badge variant="cond">{row.readiness}</Badge>
                    </TD>
                    <TD>
                      <Badge variant="default">{row.claimBoundary}</Badge>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </CardContent>
        </Card>

        {/* Real-data OOS-net */}
        {data.realData && (
          <Card className="lg:col-span-2" data-section="real-data">
            <PanelHeading
              title="Real-Data OOS-Net (research)"
              subtitle={
                <>
                  {data.realData.assetSet.join(" / ")} · {data.realData.overlapStart}–
                  {data.realData.overlapEnd} ({data.realData.overlapMonths.toFixed(1)} mo)
                </>
              }
              action={<Badge variant="default">{data.realData.claimBoundary}</Badge>}
            />
            <CardContent className="pt-1">
              <Table>
                <THead>
                  <TR className="hover:bg-transparent">
                    <TH>Strategy</TH>
                    <TH className="text-right">OOS-net Sharpe</TH>
                    <TH>Baseline</TH>
                  </TR>
                </THead>
                <TBody>
                  {data.realData.rows.map((row) => (
                    <TR key={row.strategyName}>
                      <TD className="font-medium text-[#0f172a]">{row.strategyName}</TD>
                      <TD className="text-right font-semibold text-brand-orange">
                        {formatSharpe(row.oosNetSharpe)}
                      </TD>
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
            </CardContent>
          </Card>
        )}

        {/* Interactive research panel — full width */}
        <div className="lg:col-span-2">
          <InteractiveResearchPanel data={data.interactiveResearch} />
        </div>

        {/* Evidence + readiness — full width */}
        <Card className="lg:col-span-2" data-section="evidence">
          <PanelHeading
            title="Evidence"
            subtitle={data.evidence.readiness}
            action={<Badge variant="pass">{data.demoReadiness.visualRegression}</Badge>}
          />
          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Dashboard claim", value: data.demoReadiness.claim },
                { label: "Public hosting", value: data.demoReadiness.publicHosting },
                { label: "Visual regression", value: data.demoReadiness.visualRegression },
                { label: "Dependency audit", value: data.demoReadiness.dependencyAudit },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-brand-line bg-brand-surface/60 px-4 py-3"
                >
                  <p className="text-[0.7rem] font-semibold uppercase tracking-wider text-slate-400">
                    {item.label}
                  </p>
                  <p className="mt-1 font-mono text-sm text-slate-700">{item.value}</p>
                </div>
              ))}
            </div>

            <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {data.evidence.tests.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2 rounded-lg border border-brand-line/70 bg-white px-3 py-2 text-sm text-slate-600"
                >
                  <span
                    className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-green"
                    aria-hidden
                  />
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            {data.warnings.length > 0 && (
              <div className="flex flex-wrap gap-2" role="status">
                {data.warnings.map((warning) => (
                  <Badge key={warning} variant="cond">
                    {warning}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
