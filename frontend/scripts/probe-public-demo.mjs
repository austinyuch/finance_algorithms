import { writeFileSync } from "node:fs";
import { join } from "node:path";

const targetUrl = "https://austinyuch.github.io/finance_algorithms/";
const outPath = join(process.cwd(), "out", "public-hosting-probe.json");

async function main() {
  let httpStatus = 0;
  let deployedManifestStatus = 0;
  let deployedDataHash;
  try {
    const response = await fetch(targetUrl, { redirect: "follow" });
    httpStatus = response.status;
  } catch {
    httpStatus = 0;
  }
  try {
    const manifestResponse = await fetch(new URL("deployment-manifest.json", targetUrl), { redirect: "follow" });
    deployedManifestStatus = manifestResponse.status;
    if (manifestResponse.status === 200) {
      const manifest = await manifestResponse.json();
      if (typeof manifest.dataHash === "string") {
        deployedDataHash = manifest.dataHash;
      }
    }
  } catch {
    deployedManifestStatus = 0;
  }
  const observedAt = new Date().toISOString();
  const status = httpStatus === 200 && deployedDataHash ? "proven" : "configured_not_observed";
  const evidence = {
    targetUrl,
    status,
    pagesConfigured: true,
    httpStatus,
    deployedManifestStatus,
    deployedDataHash,
    observedAt,
    claimBoundary: "no_alpha_claim",
  };
  writeFileSync(outPath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  console.log(`public-demo-probe: ${status} ${httpStatus} ${deployedManifestStatus} ${targetUrl}`);
  return status === "proven" ? 0 : 2;
}

main().then((code) => process.exit(code));
