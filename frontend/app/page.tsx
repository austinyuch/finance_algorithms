import { Dashboard } from "../components/Dashboard";
import { getShowcaseDashboard } from "../lib/showcase-data";

export default function Home() {
  return <Dashboard data={getShowcaseDashboard()} />;
}
