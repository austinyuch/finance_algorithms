# quantlab — TESTS.md(folder-level test registry)

Spec: [a0-backtest-foundation](../.agents/specs/a0-backtest-foundation/) · Canonical command: `uv run pytest -q`
最後刷新:2026-06-10 · 全套 **66 passed** · mypy 24 檔 clean · mutation spot-check 5/5 killed

| Test ID / 檔案 | 涵蓋 | REQ / AC | Evidence |
|---|---|---|---|
| `test_a0_0_contract` | Strategy Protocol 相容、schema 往返+約束、AST 框架隔離 | IFC-001/002/003, FWAGN-001 | 3 pass |
| `test_a0_1_pit_dataprovider` | lookahead golden、survivorship、macro lag/修訂、PBT-2 | PIT-001..004, AC-A0-01/02 | 4 pass |
| `test_a0_2_engine` | 玩具對拍、PBT-1 成本不變量、PBT-5 指標、PBT-6 walk-forward、event_driven stub | BT-001..006, AC-A0-03 | 6 pass |
| `test_a0_3_parallel` | PBT-4 平行==序列、seed 衍生、三框架 env 定義互斥 | PAR-001/002/003, AC-A0-06 | 3 pass |
| `test_a0_4_tracking` | log→get 往返、leaderboard OOS-net 排序、FMEA-A0-05、PBT-3 重現 | TRK-001/002/003, AC-A0-07 | 4 pass |
| `test_a0_5_integration` | 全鏈 happy/lookahead/重現/平行一致 | AC-A0-01..07 整合 | 4 pass |
| `test_daily_snapshot` | vintage snapshot bitemporal/append-only/解析/降級 | data governance | 9 pass |
| `test_algo_pyramid`(既有) | 金字塔加碼 | (legacy) | 33 pass |

## Mutation spot-check(A0-6,手動)
mutmut 3.x sandbox 與本 layout 不相容(只複製受變異檔,top-level import 失敗)→ 改用手動代表性變異,5/5 全被殺:
M1 PIT `<=`→`>=`、M2 成本 turnover→0、M3 walk-forward `<`→`<=`、M4 累積報酬 `-1`→`+1`、M5 survivorship `>`→`<`。
> 待辦:mutmut 自動 runner 於乾淨 layout 重接(非阻塞)。
