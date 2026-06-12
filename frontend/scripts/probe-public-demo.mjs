import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const targetUrl = "https://austinyuch.github.io/finance_algorithms/";
const outPath = process.env.QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH
  ? join(process.cwd(), process.env.QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH)
  : join(process.cwd(), "out", "public-hosting-probe.json");

function readExpectedManifest() {
  const candidates = [
    join(process.cwd(), "out", "deployment-manifest.json"),
    join(process.cwd(), "..", "docs", "deployment-manifest.json"),
  ];
  for (const path of candidates) {
    if (!existsSync(path)) {
      continue;
    }
    const manifest = JSON.parse(readFileSync(path, "utf8"));
    if (typeof manifest.dataHash === "string") {
      return {
        dataHash: manifest.dataHash,
        targetUrl: manifest.targetUrl,
        artifactKind: manifest.artifactKind,
        claimBoundary: manifest.claimBoundary,
        dashboardClaim: manifest.dashboardClaim,
      };
    }
  }
  return undefined;
}

async function main() {
  const expectedManifest = readExpectedManifest();
  let httpStatus = 0;
  let deployedManifestStatus = 0;
  let deployedDataHash;
  let deployedTargetUrl;
  let deployedArtifactKind;
  let deployedClaimBoundary;
  let deployedDashboardClaim;
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
      if (typeof manifest.targetUrl === "string") {
        deployedTargetUrl = manifest.targetUrl;
      }
      if (typeof manifest.artifactKind === "string") {
        deployedArtifactKind = manifest.artifactKind;
      }
      if (typeof manifest.claimBoundary === "string") {
        deployedClaimBoundary = manifest.claimBoundary;
      }
      if (typeof manifest.dashboardClaim === "string") {
        deployedDashboardClaim = manifest.dashboardClaim;
      }
    }
  } catch {
    deployedManifestStatus = 0;
  }
  const manifestContractMatches =
    deployedTargetUrl === (expectedManifest?.targetUrl ?? targetUrl) &&
    deployedArtifactKind === (expectedManifest?.artifactKind ?? "github_pages_static_showcase") &&
    deployedClaimBoundary === (expectedManifest?.claimBoundary ?? "no_alpha_claim") &&
    deployedDashboardClaim === (expectedManifest?.dashboardClaim ?? "local_demo_only");
  const hashStatus =
    expectedManifest?.dataHash === undefined
      ? "not_checked"
      : deployedDataHash === undefined
        ? "missing"
        : deployedDataHash === expectedManifest.dataHash
          ? "matched"
          : "mismatched";
  const manifestContractStatus =
    deployedManifestStatus !== 200
      ? "missing"
      : manifestContractMatches
        ? "matched"
        : "mismatched";
  const observedAt = new Date().toISOString();
  const status =
    httpStatus === 200 && hashStatus === "matched" && manifestContractStatus === "matched"
      ? "proven"
      : "configured_not_observed";
  const evidence = {
    targetUrl,
    status,
    pagesConfigured: true,
    httpStatus,
    deployedManifestStatus,
    deployedDataHash,
    expectedDataHash: expectedManifest?.dataHash,
    hashStatus,
    deployedTargetUrl,
    deployedArtifactKind,
    deployedClaimBoundary,
    deployedDashboardClaim,
    manifestContractStatus,
    observedAt,
    claimBoundary: "no_alpha_claim",
  };
  writeFileSync(outPath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  console.log(`public-demo-probe: ${status} ${httpStatus} ${deployedManifestStatus} ${hashStatus} ${targetUrl}`);
  return status === "proven" ? 0 : 2;
}

main().then((code) => process.exit(code));
