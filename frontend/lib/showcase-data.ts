import rawDashboard from "./showcase-payload.json";
import { assertDashboardPayload, ShowcaseDashboard } from "./showcase-contract";

const dashboard: ShowcaseDashboard = rawDashboard as ShowcaseDashboard;

export function getShowcaseDashboard(): ShowcaseDashboard {
  assertDashboardPayload(dashboard);
  return dashboard;
}
