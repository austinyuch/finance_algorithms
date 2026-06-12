import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const targetUrl = "https://austinyuch.github.io/finance_algorithms/";
const publicHostingEvidenceMaxAgeHours = 24;
const outPath = process.env.QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH
  ? join(process.cwd(), process.env.QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH)
  : join(process.cwd(), "out", "public-hosting-probe.json");

export function publicHostingFreshness(observedAt, now, maxAgeHours = publicHostingEvidenceMaxAgeHours) {
  if (!observedAt) {
    return { freshnessStatus: "missing", maxAgeHours };
  }
  const observedMs = Date.parse(observedAt);
  const nowMs = Date.parse(now);
  if (!Number.isFinite(observedMs) || !Number.isFinite(nowMs) || observedMs > nowMs) {
    return { freshnessStatus: "invalid", maxAgeHours };
  }
  const ageHours = (nowMs - observedMs) / (1000 * 60 * 60);
  return { freshnessStatus: ageHours <= maxAgeHours ? "fresh" : "stale", maxAgeHours };
}

export function classifyProbeStatus({ httpStatus, hashStatus, manifestContractStatus, freshnessStatus }) {
  return httpStatus === 200 &&
    hashStatus === "matched" &&
    manifestContractStatus === "matched" &&
    freshnessStatus === "fresh"
    ? "proven"
    : "configured_not_observed";
}

function hasCompleteExpectedManifest(manifest) {
  return Boolean(
    manifest &&
      typeof manifest.dataHash === "string" &&
      typeof manifest.targetUrl === "string" &&
      typeof manifest.artifactKind === "string" &&
      typeof manifest.claimBoundary === "string" &&
      typeof manifest.dashboardClaim === "string",
  );
}

export function classifyManifestContractStatus({ expected, deployed }) {
  if (!deployed || !hasCompleteExpectedManifest(expected)) {
    return "missing";
  }
  return deployed.deployedTargetUrl === expected.targetUrl &&
    deployed.deployedArtifactKind === expected.artifactKind &&
    deployed.deployedClaimBoundary === expected.claimBoundary &&
    deployed.deployedDashboardClaim === expected.dashboardClaim
    ? "matched"
    : "mismatched";
}

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
    if (hasCompleteExpectedManifest(manifest)) {
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
  const deployedManifestContract = {
    deployedTargetUrl,
    deployedArtifactKind,
    deployedClaimBoundary,
    deployedDashboardClaim,
  };
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
      : classifyManifestContractStatus({
          expected: expectedManifest,
          deployed: deployedManifestContract,
        });
  const now = process.env.QUANTLAB_PUBLIC_DEMO_PROBE_NOW ?? new Date().toISOString();
  const observedAt = process.env.QUANTLAB_PUBLIC_DEMO_PROBE_OBSERVED_AT ?? now;
  const freshness = publicHostingFreshness(observedAt, now);
  const status = classifyProbeStatus({
    httpStatus,
    hashStatus,
    manifestContractStatus,
    freshnessStatus: freshness.freshnessStatus,
  });
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
    ...freshness,
    claimBoundary: "no_alpha_claim",
  };
  writeFileSync(outPath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  console.log(`public-demo-probe: ${status} ${httpStatus} ${deployedManifestStatus} ${hashStatus} ${targetUrl}`);
  return status === "proven" ? 0 : 2;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => process.exit(code));
}
