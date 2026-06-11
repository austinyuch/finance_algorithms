# CR-B5 — pit_strictness(對 a0-backtest-foundation 的 contract overlay)

- **CR ID:** CR-B5
- **Status:** Open → (本次)Implemented
- **Owner spec:** `b-data-platform`(active)
- **Target baseline:** `a0-backtest-foundation`(Completed,immutable)
- **Type:** external/shared contract overlay — 修改 a0 `contract/schemas/backtest_config.json`

## 動機
資料治理政策(Hybrid 分層)區分 PIT-clean(`is_approximate=false`)與估算可得日(`is_approximate=true`)。
回測需能選擇嚴格度:`strict` 只用 clean 資料;`lenient` 含 approximate(歷史較長,須揭露假設)。

## 變更(impact triage)
1. **a0 `contract/schemas/backtest_config.json`**:新增非必填 `pit_strictness: strict|lenient`(default `lenient`)。
   - 向後相容:既有 config 不含此欄 → 預設 lenient,行為不變。
   - 須 **re-codegen** Pydantic models(`quantlab/contracts/_generated/`)+ 全型別檢查(mypy)找漂移。
2. **`quantlab/data/provider.py`**:`InMemoryPITDataProvider` 加 `strict: bool=False`(additive);
   strict 時排除 `is_approximate=true` 列。get/macro/history 行為其餘不變。
3. **`quantlab/data/vintage.py`**:loader 寫入 `is_approximate` 欄、可傳 `strict`。

## Re-sync / freshness gate
- 變更前後各重讀 SPECS.md 確認無新增 overlapping CR。✅(僅此 CR)
- contract drift-guard(interfaces.py Protocol 結構)不受影響(改的是 schema 非 Protocol)。✅

## Closure
- 全套測試綠 + mypy clean + import-linter KEPT → CR 標記 **Implemented**;SPECS.md Open CR 收斂。
