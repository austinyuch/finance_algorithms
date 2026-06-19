# Contributing

This project uses a spec-governed workflow. Start with:

1. `AGENTS.md`
2. `.agents/specs/SPECS.md`
3. `.agents/specs/NEXT_STEPS.md`
4. the relevant spec folder under `.agents/specs/`
5. `quantlab/CORRECTNESS_CHECKLIST.md`
6. `quantlab/TESTS.md`

## Branch Workflow

- Use pull requests for `dev` and `main`.
- Target normal development PRs at `dev`.
- Promote `dev` to `main` only through reviewed PRs.
- Do not force-push or delete protected branches.

## Local Gates

Use the narrowest gate that covers your change. For broad QuantLab changes:

```bash
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
```

For frontend or public demo changes:

```bash
cd frontend
npm test -- --run
npm run build
npm run smoke
```

For documentation-only edits, a full test run is not required, but readiness
claims must still be copied from current spec review evidence.

## Secrets

Install the local pre-commit hook before contributing:

```bash
./scripts/install-git-hooks.sh
```

The hook blocks `.env` files and common secret literals. CI also runs secret and
security scans on pull requests.

## License

This project is licensed under the [Apache License, Version 2.0](./LICENSE). By
submitting a contribution, you agree that it is provided under the same license
(Apache-2.0 Section 5), without any additional terms.
