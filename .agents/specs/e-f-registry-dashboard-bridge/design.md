# Design — E/F Registry Dashboard Bridge

## Classification

`continue active spec` across E-lite and F showcase surfaces. This is an additive bridge, not full Tier3 MLOps.

## Design

- `ShowcaseReadAPI(..., experiment_registry=...)` accepts an optional E-lite registry.
- `ShowcaseReadAPI.experiments()` returns read-only dictionaries sorted deterministically.
- `build_dashboard_summary(..., experiments=...)` includes the registry summary in the dashboard payload.
- The Next.js contract adds `ExperimentRegistryRow` with fixed conservative literals.
- The dashboard renders a full-width table section.

## FMEA

| Risk ID | Failure Mode | Effect | Control |
|---|---|---|---|
| EF-FM-01 | Registry rows imply alpha or Tier3 readiness | False-green public/demo claim | Literal contract checks and mutation tests |
| EF-FM-02 | Dashboard omits registry evidence | E-lite not visible in showcase | Python and frontend tests require `experiments` |
