# Design — Epic A:反台積電對衝 thin slice

> SDD Phase 2。**註:本檔為 as-built 整理**(Epic A 已實作於 PR #2;此文件補齊 SDD 文件鏈,
> 反映實際設計決策與 traceability)。需求:[requirements.md](./requirements.md)。

## 1. 架構與模組

於 A0 地基(`quantlab/`)之上新增,**不改 A0 既有行為**(僅 additive impact):

```
quantlab/research/screen.py     共整合-反向篩選(Engle-Granger)
quantlab/strategies/
  baselines.py                  StaticWeights / RandomStrategy(笨 baseline)
  hedge.py                      build_hedge_weights + HedgeStrategy
  lstm.py                       LSTMStrategy(PyTorch,torch 僅在此)
quantlab/runner.py              run_hedge_slice(編排:Hedge+baselines → leaderboard)
scripts/run_tsmc_hedge_slice.py 可重現執行器(A-6 writeup 數字來源)
```

資料流:
```
合成 data(PIT)─history(asof)→ screen(Engle-Granger) ─selected→ build_hedge_weights
                                                                      │
LSTM / baselines ──────────────────────────────────────┐            ▼
                                                        ▼      HedgeStrategy.generate_signal
                                              VectorizedEngine.run(A0,PIT,成本後)
                                                        ▼
                                          LocalResultStore → leaderboard(OOS-net)
```

## 2. 關鍵設計決策

### 2.1 反指標 = 共整合 + 反向(REQ-A-SCREEN-001)
- Engle-Granger:`OLS(candidate ~ target)` 取 hedge ratio(斜率);殘差 `adfuller` p-value。
- 入選 = `adf_p < pmax`(共整合)**且 `hedge_ratio < 0`(反向 spread)**;依 adf_p 升冪排名。
- `min_obs` 守護:樣本 < 門檻不檢定、不入選(防 ADF 在短序列報錯)。
- PIT:只用 `data.history(asof)`(available_date<=asof)。

### 2.2 PIT history 存取器(REQ-A-DATA-001,[Impacts: a0])
`InMemoryPITDataProvider.history(asof, field, symbols)` 回 index=event_date 寬表,
同 (symbol,event_date) 取最新可得版本。additive,不改 A0 既有方法。

### 2.3 對衝建構(REQ-A-HEDGE-001)
`build_hedge_weights`:target 核心 `1-f` + selected 候選均分 `f`,正規化;空 selected → 全 target。
`HedgeStrategy` 每個 asof 即時跑 PIT 篩選 → 建權重(相容 A0 Strategy Protocol)。

### 2.4 LSTM(REQ-A-LSTM-001)
- 小型 LSTM 回歸下一期報酬;預測>0→持有 target,否則現金。
- **PIT 懶訓練**:首個足量視窗訓練一次,之後預測(週期重訓為後續精修)。
- **可重現**:CPU + `torch.manual_seed` + 不洗牌 → 同 seed 同訊號。
- **框架隔離**:torch 僅存在 `strategies/lstm`;`strategies/__init__` 不 import 它 → `import quantlab.strategies` 不需 torch;engine/data 由 import-linter 契約禁 torch。

### 2.5 metrics robustness（[Impacts: a0]）
`compute_metrics` 加 `wealth<=0 → annualized_return=-1.0` 防護,避免負底分數冪變複數。

## 3. Lightweight FMEA(stakeholder-facing showcase → 觸發)

| Risk ID | Failure Mode | Effect | Control | Task |
|---|---|---|---|---|
| FMEA-A-01 | 合成資料被誤當真實 alpha | overclaim | writeup 顯著標註「合成、未宣稱 alpha」 | A-6 |
| FMEA-A-02 | LSTM 只報 in-sample 漂亮 | false green | 一律 OOS-net、對笨 baseline 並排 | A-2/A-5 |
| FMEA-A-03 | 篩選用到未來資料 | lookahead | 只用 `history(asof)`,A0 PIT 守門 | A-1 |
| FMEA-A-04 | 對衝宣稱降風險但實未降 | overclaim | A-4 顯式測 vol_hedge<vol_target | A-4 |
| FMEA-A-05 | torch 滲入回測核心 | 破壞框架無感 | import-linter 契約 + AST 測試 | (residual PR#3) |

## 4. REQ → Design / Test
| REQ | Design | Test |
|---|---|---|
| SCREEN-001/002 | §2.1 | test_a_1_screen |
| DATA-001 | §2.2 | test_a_1_screen |
| BASE-001 | baselines.py | test_a_3_baselines |
| HEDGE-001 | §2.3 | test_a_4_hedge |
| INT-001 | runner.run_hedge_slice | test_a_5_slice |
| LSTM-001 | §2.4 | test_a_2_lstm |
| DOC-001 | scripts + writeup | writeup.md |
