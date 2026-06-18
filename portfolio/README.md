# Deep-Learning Course Portfolio · 深度學習課程作品集

Bilingual (繁中 + English) presentation about the **QuantLab Epic H — Deep-Learning
Research Lab**: a framework-free reference model → real PyTorch training → an
interactive research UI, all under `no_alpha_claim`.

雙語簡報，介紹 **QuantLab Epic H 深度學習研究實驗室**：framework-free 參考模型 →
真實 PyTorch 訓練 → 互動研究 UI，全程 `no_alpha_claim`。

## Files

| File | What |
|---|---|
| `QuantLab-EpicH-DeepLearning-Portfolio.pptx` | The deck — 13 slides, 16:9 wide, bilingual |
| `build-deck.js` | Generator (PptxGenJS). `node build-deck.js` rebuilds the `.pptx` |
| `assets/perf-report.png` | **Real** DL performance report (`run_dl_experiment.py` output: equity / drawdown / learning-curve / return-distribution) |
| `assets/ui-h3.png` | **Real** Research Dashboard screenshot (Next.js static export, `no_alpha_claim` badge) |

Both screenshots are genuine artifacts of the Epic H work, not mock-ups.
兩張截圖皆為 Epic H 真實產物,非示意圖。

## Rebuild

```bash
npm install pptxgenjs react react-dom react-icons sharp   # one-time
node build-deck.js                                         # → QuantLab-EpicH-DeepLearning-Portfolio.pptx
```

Honesty note: the deck deliberately shows the trained model **under-performing**
buy-and-hold on OOS-net Sharpe (0.092 vs 0.129) — mechanism evidence, not a
strategy verdict, `no_alpha_claim`.
誠實說明:簡報刻意呈現訓練後模型在 OOS-net Sharpe 上**輸給** buy-and-hold
(0.092 vs 0.129)— 機制證據,非策略勝負。
