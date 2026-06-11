import { Dashboard } from "../components/Dashboard";
import { getShowcaseDashboard } from "../lib/showcase-fixture";

export default function Home() {
  return <Dashboard data={getShowcaseDashboard()} />;
}
