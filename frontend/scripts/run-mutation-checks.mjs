import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

export const mutations = [
  {
    name: "frontend-claim-boundary",
    path: "lib/showcase-payload.json",
    original: '  "claimBoundary": "no_alpha_claim",\n  "demoReadiness":',
    mutated: '  "claimBoundary": "alpha_claim",\n  "demoReadiness":',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx"]
  },
  {
    name: "frontend-experiment-registry-claim-boundary",
    path: "lib/showcase-payload.json",
    original: '      "claimBoundary": "no_alpha_claim",\n      "experimentId": "7bb2f220f757ed89",',
    mutated: '      "claimBoundary": "alpha_claim",\n      "experimentId": "7bb2f220f757ed89",',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx"]
  },
  {
    name: "frontend-public-hosting-overclaim",
    path: "lib/showcase-payload.json",
    original: '"publicHosting": "not_proven",',
    mutated: '"publicHosting": "proven",',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx"]
  },
  {
    name: "frontend-visual-regression-underclaim",
    path: "lib/showcase-payload.json",
    original: '"visualRegression": "proven"',
    mutated: '"visualRegression": "not_proven"',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "visual-regression underclaims"]
  },
  {
    name: "frontend-dependency-audit-regression",
    path: "lib/showcase-payload.json",
    original: '"dependencyAudit": "clean",',
    mutated: '"dependencyAudit": "moderate_advisory",',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx"]
  },
  {
    name: "frontend-dashboard-stale-gate-evidence",
    path: "lib/showcase-payload.json",
    original: '"frontend mutation 29/29 killed"',
    mutated: '"mutation 9/9 killed"',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "gate evidence"]
  },
  {
    name: "frontend-coverage-artifact-drift",
    path: "../docs/review/assets/gate-frontend-coverage.txt",
    original: "F Next.js line coverage 84.12%",
    mutated: "F Next.js line coverage 88.00%",
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "gate evidence"]
  },
  {
    name: "frontend-dashboard-source-regression",
    path: "lib/showcase-payload.json",
    original: '"source": "local_result_store",',
    mutated: '"source": "fixture_records",',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "serves validated"]
  },
  {
    name: "frontend-h3-interactive-claim-boundary",
    path: "lib/showcase-payload.json",
    original: '    "claimBoundary": "no_alpha_claim",\n    "dataLineage": {',
    mutated: '    "claimBoundary": "alpha_claim",\n    "dataLineage": {',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "interactive research sections"]
  },
  {
    name: "frontend-h3-approximate-warning-gate",
    path: "lib/showcase-payload.json",
    original: '      "approximateAvailability": true,',
    mutated: '      "approximateAvailability": false,',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx", "-t", "interactive research sections"]
  },
  {
    name: "frontend-h3-e2e-failclosed-status-gate",
    path: "scripts/interactive-research-e2e.mjs",
    original: "setter.call(seedInput, String(Number(seedInput.value) + 1));",
    mutated: "setter.call(seedInput, String(Number(seedInput.value)));",
    command: ["npm", "run", "e2e:interactive"]
  },
  {
    name: "frontend-public-demo-hosting-classifier",
    path: "lib/public-demo.ts",
    original: "probe.httpStatus === 200 &&\n    hashStatus === \"matched\" &&\n    manifestContractStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"",
    mutated: "probe.httpStatus !== 200 &&\n    hashStatus === \"matched\" &&\n    manifestContractStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx"]
  },
  {
    name: "frontend-public-demo-hosting-hash-gate",
    path: "lib/public-demo.ts",
    original: "probe.httpStatus === 200 &&\n    hashStatus === \"matched\" &&\n    manifestContractStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"",
    mutated: "probe.httpStatus === 200 &&\n    hashStatus !== \"missing\" &&\n    manifestContractStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "deployed data hashes"]
  },
  {
    name: "frontend-public-demo-hosting-manifest-contract-gate",
    path: "lib/public-demo.ts",
    original: "if (\n    probe.httpStatus === 200 &&\n    hashStatus === \"matched\" &&\n    manifestContractStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"\n  )",
    mutated: "if (\n    probe.httpStatus === 200 &&\n    hashStatus === \"matched\" &&\n    freshness.freshnessStatus === \"fresh\"\n  )",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "weakens claim metadata"]
  },
  {
    name: "frontend-public-demo-hosting-freshness-gate",
    path: "lib/public-demo.ts",
    original: 'freshness.freshnessStatus === "fresh"',
    mutated: 'true',
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "probe evidence is stale"]
  },
  {
    name: "frontend-public-demo-probe-freshness-status-gate",
    path: "scripts/probe-public-demo.mjs",
    original: 'freshnessStatus === "fresh"',
    mutated: 'true',
    command: ["npm", "test", "--", "--run", "tests/probe-public-demo.test.ts", "-t", "observation is stale"]
  },
  {
    name: "frontend-public-demo-probe-absolute-output-path",
    path: "scripts/probe-public-demo.mjs",
    original: "return pathFromEnv ? resolve(cwd, pathFromEnv) : join(cwd, \"out\", \"public-hosting-probe.json\");",
    mutated: "return pathFromEnv ? join(cwd, pathFromEnv) : join(cwd, \"out\", \"public-hosting-probe.json\");",
    command: ["npm", "test", "--", "--run", "tests/probe-public-demo.test.ts", "-t", "absolute paths"]
  },
  {
    name: "frontend-public-demo-export-absolute-output-dir",
    path: "scripts/export-public-demo.tsx",
    original: "  ? resolve(root, process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR)\n  : join(root, \"out\");",
    mutated: "  ? join(root, process.env.QUANTLAB_PUBLIC_DEMO_OUT_DIR)\n  : join(root, \"out\");",
    command: ["npm", "test", "--", "--run", "tests/export-public-demo.test.ts", "-t", "absolute output directories"]
  },
  {
    name: "frontend-public-demo-export-stale-evidence-gate",
    path: "scripts/export-public-demo.tsx",
    original: "if (!dashboard.evidence.tests.includes(expected)) {",
    mutated: "if (false && !dashboard.evidence.tests.includes(expected)) {",
    command: ["npm", "test", "--", "--run", "tests/export-public-demo.test.ts", "-t", "stale frontend gate evidence"]
  },
  {
    name: "frontend-public-demo-expected-manifest-gate",
    path: "scripts/probe-public-demo.mjs",
    original: "if (!deployed || !hasCompleteExpectedManifest(expected)) {",
    mutated: "if (!deployed) {",
    command: ["npm", "test", "--", "--run", "tests/probe-public-demo.test.ts", "-t", "complete expected manifest"]
  },
  {
    name: "frontend-public-demo-probe-manifest-colocation",
    path: "scripts/probe-public-demo.mjs",
    original: 'join(dirname(probeOutputPath), "deployment-manifest.json"),\n    join(process.cwd(), "out", "deployment-manifest.json"),',
    mutated: 'join(process.cwd(), "out", "deployment-manifest.json"),',
    command: ["npm", "test", "--", "--run", "tests/probe-public-demo.test.ts", "-t", "beside the requested probe output"]
  },
  {
    name: "frontend-public-demo-probe-incomplete-manifest-failclosed",
    path: "scripts/probe-public-demo.mjs",
    original: "    return undefined;\n  }\n  return undefined;\n}",
    mutated: "    continue;\n  }\n  return undefined;\n}",
    command: ["npm", "test", "--", "--run", "tests/probe-public-demo.test.ts", "-t", "beside the requested probe output"]
  },
  {
    name: "frontend-static-export-showcase-sync",
    path: "lib/public-demo.ts",
    original: "if (JSON.stringify(showcase) !== canonicalJson) {",
    mutated: "if (false && JSON.stringify(showcase) !== canonicalJson) {",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "static export artifacts"]
  },
  {
    name: "frontend-visual-baseline-alpha-claim",
    path: "visual-baselines/showcase.visual.json",
    original: '"claimBoundary": "no_alpha_claim",',
    mutated: '"claimBoundary": "alpha_claim",',
    command: ["npm", "run", "visual"]
  },
  {
    name: "frontend-browser-visual-hash-gate",
    path: "lib/public-demo.ts",
    original: "/^[a-f0-9]{64}$/.test(input.screenshotHash)",
    mutated: "/^.+$/.test(input.screenshotHash)",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "rejects malformed visual baselines"]
  },
  {
    name: "frontend-browser-visual-diff-threshold",
    path: "lib/public-demo.ts",
    original: 'status: input.mismatchRatio <= input.maxMismatchRatio ? "passed" : "failed",',
    mutated: 'status: input.mismatchRatio <= input.maxMismatchRatio ? "failed" : "passed",',
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "visual diff status"]
  },
  {
    name: "frontend-browser-pixel-mismatch-count",
    path: "lib/public-demo.ts",
    original: "mismatchedPixels += 1;",
    mutated: "mismatchedPixels += 0;",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "pixel mismatch ratio"]
  },
  {
    name: "frontend-smoke-port-hardcode-regression",
    path: "scripts/smoke-port.mjs",
    original: "    return await assertPortAvailable(requested, host);",
    mutated: "    return requested;",
    command: ["npm", "test", "--", "--run", "tests/smoke-port.test.ts", "-t", "occupied governed smoke ports"]
  },
  {
    name: "frontend-smoke-html-api-parity-regression",
    path: "scripts/smoke-assertions.mjs",
    original: "  if (!normalizedHtml.includes(needle)) {\n    throw new Error(`dashboard HTML smoke missing ${label}: ${needle}`);\n  }",
    mutated: "  if (false && !normalizedHtml.includes(needle)) {\n    throw new Error(`dashboard HTML smoke missing ${label}: ${needle}`);\n  }",
    command: ["npm", "test", "--", "--run", "tests/smoke-port.test.ts", "-t", "explicit governed smoke port"]
  }
];

export function parseMutationArgs(argv) {
  const only = [];
  let list = false;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--only") {
      const name = argv[index + 1];
      if (!name || name.startsWith("--")) {
        throw new Error("--only requires a mutation name");
      }
      only.push(name);
      index += 1;
    } else if (arg === "--list") {
      list = true;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return { only, list };
}

export function selectMutations({ only = [] } = {}) {
  if (only.length === 0) {
    return mutations;
  }
  const selectedNames = new Set(only);
  const selected = mutations.filter((mutation) => selectedNames.has(mutation.name));
  const missing = only.filter((name) => !mutations.some((mutation) => mutation.name === name));
  if (missing.length > 0) {
    throw new Error(`unknown mutation(s): ${missing.join(", ")}`);
  }
  return selected;
}

export function runMutations(selectedMutations) {
  let killed = 0;

  for (const mutation of selectedMutations) {
    const target = join(root, mutation.path);
    const originalText = readFileSync(target, "utf8");
    const occurrences = originalText.split(mutation.original).length - 1;
    if (occurrences !== 1) {
      throw new Error(`${mutation.name}: expected exactly one mutation target, found ${occurrences}`);
    }
    writeFileSync(target, originalText.replace(mutation.original, mutation.mutated), "utf8");
    try {
      const result = spawnSync(mutation.command[0], mutation.command.slice(1), {
        cwd: root,
        stdio: "inherit"
      });
      const isKilled = result.status !== 0;
      console.log(`${mutation.name}: ${isKilled ? "KILLED" : "SURVIVED"}`);
      if (isKilled) {
        killed += 1;
      }
    } finally {
      writeFileSync(target, originalText, "utf8");
    }
  }

  return { killed, total: selectedMutations.length };
}

export function main(argv = process.argv.slice(2)) {
  const options = parseMutationArgs(argv);
  if (options.list) {
    for (const mutation of mutations) {
      console.log(mutation.name);
    }
    return 0;
  }
  const selected = selectMutations(options);
  const result = runMutations(selected);
  return result.killed === result.total ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    process.exit(main());
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  }
}
