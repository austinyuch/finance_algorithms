# 反台積電對衝 Thin Slice —— 一頁誠實 Writeup

> Epic A 作品集門面。**資料為合成**(strategy C:僅驗證管線,非真實 alpha)。
> 重現:`uv run python scripts/run_tsmc_hedge_slice.py`

## 做了什麼

一條端到端、point-in-time 正確的研究管線:

```
共整合-反向篩選(Engle-Granger, hedge ratio<0)
  → 對衝部位(target 核心 + 反向候選)
  → LSTM 擇時(PyTorch)+ 笨 baselines
  → A0 PIT 回測(walk-forward, 成本後)
  → leaderboard(OOS net Sharpe)
```

合成資料:TSMC(輕微上漲隨機漫步)、PLANT(= 150 − 0.5·TSMC + 平穩噪音,與 TSMC 共整合且反向)、RAND(獨立隨機漫步)。

## 結果(OOS net Sharpe,可重現)

| 策略 | OOS net Sharpe |
|---|---|
| BuyAndHold(買進持有 TSMC) | **0.3911** |
| LSTMStrategy(PyTorch 擇時) | 0.3911 |
| HedgeStrategy(共整合-反向對衝) | 0.3528 |
| StaticWeights(等權) | 0.2759 |
| RandomStrategy(隨機,seed) | −0.0092 |

## 誠實結論(這才是重點)

1. **LSTM 沒有打贏買進持有(0.3911 = 0.3911)。** 在這個輕微上漲的序列,LSTM 學到的最佳策略就是「一直持有」——它複製了 buy-and-hold,沒有增加價值。**任何人都能 train 一個 LSTM;它贏不過最笨的 baseline 才是常態。**
2. **對衝降低了 Sharpe(0.3528 < 0.3911)。** 在上漲行情,對衝把資金分到反向資產 → 拖累報酬。對衝降的是波動,但**天下沒有白吃的午餐**:降風險就是用報酬換來的。它在這個情境「輸」,完全合理且誠實。
3. **隨機是地板(−0.0092)。** 確認 leaderboard 與成本後計算正常運作。

## 這證明了什麼(以及沒證明什麼)

- ✅ **管線與方法論是對的**:PIT 無 lookahead、誠實對笨 baseline 並排、成本後、可重現。它**如實顯示「花俏 ≠ 更好」**——這正是嚴謹回測該有的誠實。
- ❌ **沒有宣稱 alpha**。資料是合成的;這是管線驗證,不是賺錢證據。

## 限制(刻意標註)

- 合成資料,單一情境、單次 run;真實資料源接入屬 Epic B。
- LSTM 為第一切片(單次訓練於首個足量視窗;週期性重訓、超參搜尋為後續)。
- 成本僅周轉型;配息/換匯事件型待 Epic B。
- 下沉真實個股前,需依 strategy C 補齊真實 PIT 資料正確性。

## 驗證

```
uv run python scripts/run_tsmc_hedge_slice.py     # 重現上表
uv run pytest -q                                  # 全套測試
```
