# Review — Epic A:反台積電對衝 thin slice

> SDD Phase 5。最終 verdict authority。
> 驗證:`uv run pytest -q` → **83 passed**;`uv run mypy quantlab/ --ignore-missing-imports` → clean(29 檔)。

## Verdict:**PASSED**(完整 vertical slice,作品集中心就緒)

端到端管線(篩選 → 對衝 → LSTM/baselines → A0 PIT 回測 → leaderboard → 一頁誠實 writeup)全部完成、有測試、可重現。**完成的深度 > 未完成的廣度**達成。

## REQ / AC → Evidence

| 項目 | 證據 |
|---|---|
| REQ-A-SCREEN-001/002(共整合-反向篩選,可平行) | `test_a_1_screen`(AC-A-01/02/03) |
| REQ-A-DATA-001(PIT history()) | `test_a_1_screen` PIT |
| REQ-A-BASE-001(笨 baseline 群) | `test_a_3_baselines` |
| REQ-A-HEDGE-001(對衝部位 + 降波動) | `test_a_4_hedge` |
| REQ-A-INT-001(全鏈 leaderboard) | `test_a_5_slice` |
| REQ-A-LSTM-001(PyTorch LSTM,可重現) | `test_a_2_lstm` |
| REQ-A-DOC-001(一頁誠實 writeup) | [writeup.md](./writeup.md) + `scripts/run_tsmc_hedge_slice.py` |

## 誠實結論(作品集價值核心)

合成資料 leaderboard:**LSTM 沒打贏買進持有(tie)、對衝在上漲期降 Sharpe(降風險的代價)、隨機是地板**。管線如實顯示「花俏 ≠ 更好」——這正是嚴謹回測的誠實,也是與 99% 業餘 quant 作品集的差異化。**未宣稱 alpha**。

## Residual / 刻意降級(非阻塞)

- 資料合成(真實源屬 Epic B);LSTM 單次訓練(週期重訓/超參搜尋待後);成本僅周轉型;
  框架隔離以 AST 測試守住(import-linter 待正式化);三框架真機 GPU 驗證待辦。

## 交棒

完整 slice 可作為 Epic B(真實資料)接入的驗收骨架:把合成 provider 換成真實 PIT 資料即可重跑同一 leaderboard。`run_hedge_slice` / `run_tsmc_hedge_slice.py` 為可重現入口。
