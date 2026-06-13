export function assertPayload(payload) {
  if (payload.claimBoundary !== "no_alpha_claim") {
    throw new Error("dashboard payload overclaims alpha");
  }
  if (payload.demoReadiness?.publicHosting !== "not_proven") {
    throw new Error("public hosting must remain not_proven without deployed URL evidence");
  }
  if (payload.demoReadiness?.visualRegression !== "proven") {
    throw new Error("visual regression must be proven by committed browser visual evidence");
  }
  if (payload.demoReadiness?.dependencyAudit !== "clean") {
    throw new Error("dependency audit must be clean");
  }
  if (
    payload.sourceMetadata?.source !== "local_result_store" ||
    payload.sourceMetadata?.experimentRegistry !== "experiment_registry" ||
    payload.sourceMetadata?.sourceRecordCount < 2
  ) {
    throw new Error("dashboard payload must prove local_result_store source metadata");
  }
  if (payload.experiments?.[0]?.readiness !== "registry_only") {
    throw new Error("experiment registry must remain registry_only");
  }
}

function requireHtmlNeedle(html, needle, label) {
  const normalizedHtml = html.replace(/<!--.*?-->/gs, "");
  if (!normalizedHtml.includes(needle)) {
    throw new Error(`dashboard HTML smoke missing ${label}: ${needle}`);
  }
}

export function assertHtmlMatchesPayload(html, payload) {
  requireHtmlNeedle(html, "Experiment Registry", "experiment section");
  requireHtmlNeedle(html, "local_demo_only", "local demo boundary");
  requireHtmlNeedle(html, payload.activeRunId, "active run id");
  requireHtmlNeedle(html, payload.strategyName, "active strategy");
  requireHtmlNeedle(html, payload.regime?.label, "regime label");
  requireHtmlNeedle(html, `Public hosting: ${payload.demoReadiness?.publicHosting}`, "public hosting status");
  requireHtmlNeedle(html, `Visual regression: ${payload.demoReadiness?.visualRegression}`, "visual status");
  requireHtmlNeedle(html, payload.experiments?.[0]?.modelFamily, "experiment family");
  requireHtmlNeedle(html, payload.evidence?.tests?.[0], "first evidence gate");
}
