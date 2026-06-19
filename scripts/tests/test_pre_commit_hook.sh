#!/bin/bash
# Regression tests for scripts/git-hooks/pre-commit secret-literal detection.

set -u

HOOK="$(cd "$(dirname "$0")/../.." && pwd)/scripts/git-hooks/pre-commit"
pass=0
fail=0

run_case() {
    local expect="$1" name="$2" fname="$3" content="$4"
    local repo rc
    repo="$(mktemp -d)"
    (
        cd "$repo" || exit 99
        git init -q
        mkdir -p "$(dirname "$fname")" 2>/dev/null || true
        printf '%s\n' "$content" > "$fname"
        git add -A
        printf 'n\n' | bash "$HOOK" >/dev/null 2>&1
    )
    rc=$?
    rm -rf "$repo"

    local ok=0
    if [ "$expect" = "block" ] && [ "$rc" -ne 0 ]; then ok=1; fi
    if [ "$expect" = "pass" ] && [ "$rc" -eq 0 ]; then ok=1; fi
    if [ "$ok" -eq 1 ]; then
        pass=$((pass+1)); echo "  PASS [$expect] $name"
    else
        fail=$((fail+1)); echo "  FAIL [$expect] $name (exit=$rc)"
    fi
}

echo "== pre-commit hook: must BLOCK real literals =="
run_case block "api key literal"        app.py        'API_KEY="not-a-real-secret-literal"'
run_case block "password literal quoted" config.py    'password = "not-a-real-password"'
run_case block "token literal yaml"      conf.yaml     'token: not-a-real-token'
run_case block ".env file"               .env         'API_KEY=changeme'

echo "== pre-commit hook: must PASS legitimate commits =="
run_case pass  "python typed field"      models.py     'def conn(self, password: str = None): ...'
run_case pass  "typescript typed field"  types.ts      '  apiKey: string;'
run_case pass  "placeholder env example" .env.example  'API_KEY=your-api-key-here'
run_case pass  "shell var ref"           compose.yml   'password=${DB_PASSWORD}'
run_case pass  "env pointer"             config.toml   'api_key = "env::OPENAI_API_KEY"'
run_case pass  "os.environ read"         db.py         'password=os.environ["POSTGRES_PASSWORD"]'
run_case pass  "redacted value"          log.txt       'token=REDACTED'

echo "== result: pass=$pass fail=$fail =="
[ "$fail" -eq 0 ]
