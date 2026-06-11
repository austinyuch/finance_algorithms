# Review — Epic A0:回測引擎 + Tier1 平行底座 + Tier2 追蹤

> SDD Phase 5。最終 acceptance / readiness verdict authority。
> 範圍:[requirements.md](./requirements.md) · [design.md](./design.md) · [tasks.md](./tasks.md)
> 驗證:`uv run pytest -q` → **137 passed**;`uv run mypy quantlab/ --ignore-missing-imports` → clean(40 files);`uv run lint-imports` → KEPT;mutation spot-check **5/5 killed**;mutation automation **3/3 killed**。

## Verdict:**PASSED**(地基就緒,可承接 Epic A)

A0 的核心保證(point-in-time 正確、可重現、框架無感、平行確定、OOS-net 誠實 leaderboard)全部有自動化測試與 mutation 證據支撐。下列 residual 皆為刻意降級、已記錄、且**不影響地基用途**。

## REQ / AC → Evidence

| 項目 | 證據 | 狀態 |
|---|---|---|
| IFC-001/002/003(框架無感介面) | `test_a0_0`;mypy import 隔離 | ✅ |
| PIT-001..004(bitemporal、survivorship、macro lag) | `test_a0_1`、AC-A0-01/02 | ✅ |
| BT-001..006(引擎、成本、walk-forward、指標) | `test_a0_2`、AC-A0-03 | ✅ |
| CR-A0 regime rebalance scheduling | `test_a0_2` regime policy tests;[CR-A0](./change-requests/cr-a0-regime-rebalance-scheduling.md) | ✅ |
| PAR-001/002(平行確定性) | `test_a0_3`、AC-A0-06 | ✅ |
| PAR-003(三框架環境隔離) | env 定義互斥測試 | ⚠️ 定義就緒;真機安裝/GPU 驗證延後 |
| TRK-001/002/003(log/get/leaderboard) | `test_a0_4`、AC-A0-07 | ✅(SQLite 後端) |
| NFR-CORRECT/REPRO/FWAGN/HONEST | PBT-2..6、`test_a0_5` 整合、mutation 5/5 | ✅ |
| FMEA-A0-01..06 | 對應測試見 [design.md §4](./design.md) | ✅ 皆有 Prevent/Detect 測試 |

## Residual / 已記錄的刻意降級(非阻塞)

1. **MLflow backend 延後**:Python 3.13 依賴衝突(protobuf 5 / setuptools 81 / mlflow 回退 1.27.0)。現用零依賴 SQLite `LocalResultStore`,走同 `ResultStore` Protocol;MLflow 待乾淨環境接入(含 `mlflow ui` 視覺化)。
2. **三框架環境**:`quantlab/envs/` 為環境宣告;各 lane 實際安裝與 GPU 驗證屬真機/容器,未在單一開發 venv 進行。
3. **成本模型 first-slice**:僅周轉型(手續費/滑價/台股證交稅);配息預扣、換匯點差為事件型,toy 無觸發,待 Epic B 接真實配息/匯率補上。
4. **Mutation 自動化**:mutmut 3.x sandbox 與本 layout 不相容;已新增 repo-local `scripts/run_mutation_spot_checks.py`,目前 3/3 configured mutations killed。完整 mutmut score 仍非本 slice 目標。
5. **import-linter**:框架隔離目前由 AST 測試守住(`test_a0_0`);import-linter 正式化列為待辦。
6. **spec contract/interfaces.py ↔ quantlab/contracts/interfaces.py**:目前手動同步;drift-guard 測試列為待辦。

## 交棒

地基可承接 **Epic A**(反台積電對衝 thin slice):真實策略/資料源接入時,A0 的 PIT 契約強制其正確性。`ResultStore.leaderboard()` 為未來 Epic F 前端消費接縫。
