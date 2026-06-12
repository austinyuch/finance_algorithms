# 回測正確性 Checklist(作品集 artifact)

> quantlab A0 地基如何避免「業餘 quant 回測 90% 的靜默錯誤」。每一項都有自動化測試把關。

| # | 業餘陷阱 | quantlab 的防護 | 證據 |
|---|---|---|---|
| 1 | **Lookahead bias**(用未來資料) | bitemporal 儲存,`get(asof)` 一律 `available_date <= asof` | `test_a0_1` lookahead golden + PBT-2;端到端 `test_a0_5` |
| 2 | **Survivorship bias**(排除下市股) | universe 由上市/下市日表算,含已下市 | `test_a0_1` survivorship |
| 3 | **總經 release lag / 修訂** | 總經以公布日索引,取當時版本 | `test_a0_1` macro lag/修訂 |
| 4 | **成本/稅/匯灌水報酬** | net 含手續費/滑價/台股證交稅;`cost=0→net==gross` | `test_a0_2` AC-A0-03、PBT-1 |
| 5 | **Walk-forward 洩漏** | 訓練窗結束 ≤ 測試窗開始,保證不重疊 | `test_a0_2` PBT-6 |
| 6 | **只報 in-sample / gross** | 指標強制標 basis+segment;leaderboard 只認 **OOS+net** | `test_a0_4` FMEA-A0-05 |
| 7 | **不可重現** | 同 seed+config+data_version → 指標一致 | `test_a0_4`/`test_a0_5` PBT-3 |
| 8 | **黑箱/框架綁死** | 回測核心對框架無感(Protocol);engine/data 禁 import torch/tf/jax | `test_a0_0` AST 隔離 |
| 9 | **平行結果不一致** | 母 seed 衍生子 seed,平行==序列 | `test_a0_3`/`test_a0_5` PBT-4 |
| 10 | **測試假綠** | mutation spot checks kill representative domain/governance mutations; current configured suite is 30/30, including root Torch dependency, stale governance evidence, scheduled-run observer guards, E Tier3 readiness overclaim, E serving smoke health gating, E retraining smoke status gating, and stale E-gate promotion memo regression | `scripts/run_mutation_spot_checks.py`; `quantlab/TESTS.md` |

驗證指令:`uv run pytest -q`(204 passed, 1 skipped; PyTorch LSTM optional lane skipped in default env)· `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports`(clean)· `uv run lint-imports`(KEPT)· `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py`(100% line coverage)· `uv run python scripts/run_mutation_spot_checks.py --only e-retraining-smoke-status-gate`(killed; full configured suite now 30/30)
