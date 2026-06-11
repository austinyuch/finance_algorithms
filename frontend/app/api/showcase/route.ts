import { getShowcaseDashboard } from "../../../lib/showcase-fixture";

export async function GET(): Promise<Response> {
  return Response.json(getShowcaseDashboard());
}
