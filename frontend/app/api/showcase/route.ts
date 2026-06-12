import { getShowcaseDashboard } from "../../../lib/showcase-data";

export async function GET(): Promise<Response> {
  return Response.json(getShowcaseDashboard());
}
