import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

describe("public demo export script", () => {
  it("exports artifacts to absolute output directories without repo-relative path corruption", () => {
    const absoluteOutDir = mkdtempSync(join(tmpdir(), "quantlab-public-demo-export-"));
    const corruptedOutDir = join(process.cwd(), absoluteOutDir.replace(/^\/+/, ""));
    const transcriptPath = join(absoluteOutDir, "gate-frontend-test.txt");
    writeFileSync(transcriptPath, "Tests 44 passed\n", "utf8");
    try {
      const result = spawnSync(join(process.cwd(), "node_modules", ".bin", "tsx"), ["scripts/export-public-demo.tsx"], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          QUANTLAB_PUBLIC_DEMO_OUT_DIR: absoluteOutDir,
          QUANTLAB_FRONTEND_GATE_TRANSCRIPT_PATH: transcriptPath,
        },
        encoding: "utf8",
      });

      expect(result.status, result.stderr).toBe(0);
      expect(existsSync(join(absoluteOutDir, "index.html"))).toBe(true);
      expect(existsSync(join(absoluteOutDir, "showcase.json"))).toBe(true);
      expect(existsSync(join(absoluteOutDir, "deployment-manifest.json"))).toBe(true);
      expect(existsSync(join(absoluteOutDir, "visual-snapshot.json"))).toBe(true);
      const exported = JSON.parse(readFileSync(join(absoluteOutDir, "showcase.json"), "utf8"));
      expect(exported.evidence.tests).toContain("frontend tests 44 passed");
      expect(existsSync(join(corruptedOutDir, "index.html"))).toBe(false);
    } finally {
      rmSync(absoluteOutDir, { recursive: true, force: true });
      rmSync(corruptedOutDir, { recursive: true, force: true });
    }
  });

  it("fails closed on stale frontend gate evidence before writing export artifacts", () => {
    const script = readFileSync(join(process.cwd(), "scripts", "export-public-demo.tsx"), "utf8");

    expect(script).toContain("const expected = `frontend tests ${currentFrontendTestCount()} passed`;");
    expect(script).toContain("QUANTLAB_FRONTEND_GATE_TRANSCRIPT_PATH");
    expect(script).toContain("if (!dashboard.evidence.tests.includes(expected)) {");
    expect(script).toContain("dashboard payload stale frontend test evidence");
    expect(script.indexOf("assertDashboardEvidenceFresh(dashboard);")).toBeLessThan(
      script.indexOf("mkdirSync(outDir"),
    );
  });
});
