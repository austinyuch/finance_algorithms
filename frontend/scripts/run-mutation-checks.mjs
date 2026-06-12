import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

const mutations = [
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
    name: "frontend-dependency-audit-regression",
    path: "lib/showcase-payload.json",
    original: '"dependencyAudit": "clean",',
    mutated: '"dependencyAudit": "moderate_advisory",',
    command: ["npm", "test", "--", "--run", "tests/dashboard.test.tsx"]
  },
  {
    name: "frontend-dashboard-stale-gate-evidence",
    path: "lib/showcase-payload.json",
    original: '"frontend mutation 13/13 killed"',
    mutated: '"mutation 9/9 killed"',
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
    name: "frontend-public-demo-hosting-classifier",
    path: "lib/public-demo.ts",
    original: "probe.httpStatus === 200 && hashStatus === \"matched\" && manifestContractStatus === \"matched\"",
    mutated: "probe.httpStatus !== 200 && hashStatus === \"matched\" && manifestContractStatus === \"matched\"",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx"]
  },
  {
    name: "frontend-public-demo-hosting-hash-gate",
    path: "lib/public-demo.ts",
    original: "probe.httpStatus === 200 && hashStatus === \"matched\" && manifestContractStatus === \"matched\"",
    mutated: "probe.httpStatus === 200 && hashStatus !== \"missing\" && manifestContractStatus === \"matched\"",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "deployed data hashes"]
  },
  {
    name: "frontend-public-demo-hosting-manifest-contract-gate",
    path: "lib/public-demo.ts",
    original: "if (probe.httpStatus === 200 && hashStatus === \"matched\" && manifestContractStatus === \"matched\")",
    mutated: "if (probe.httpStatus === 200 && hashStatus === \"matched\")",
    command: ["npm", "test", "--", "--run", "tests/public-demo.test.tsx", "-t", "weakens claim metadata"]
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
  }
];

let killed = 0;

for (const mutation of mutations) {
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

if (killed !== mutations.length) {
  process.exit(1);
}
