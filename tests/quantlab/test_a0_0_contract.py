"""A0-0 Contract — RED 階段測試。

對應 tasks.md A0-0 / REQ-A0-IFC-001/002/003 與 NFR-A0-FWAGN-001。
這些測試在 quantlab 骨架建立前**應全部失敗**(RED)。

驗收三件事:
  1. dummy 策略型別相容於框架無感的 Strategy Protocol。
  2. ResultRecord 等 Pydantic models 與 JSON schema 往返、required 驗證。
  3. quantlab.engine / quantlab.data 的原始碼不得 import torch/tensorflow/jax(框架隔離)。
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


# --- 1. Strategy Protocol 相容(REQ-A0-IFC-001/002) ---

def test_buyandhold_conforms_to_strategy_protocol():
    from quantlab.contracts import Strategy
    from quantlab.strategies import BuyAndHold

    bh = BuyAndHold(["AAA", "BBB"])
    assert isinstance(bh, Strategy)                 # runtime_checkable 結構檢查
    assert hasattr(bh, "fit")
    assert hasattr(bh, "generate_signal")
    assert isinstance(bh.metadata, dict)


# --- 2. Pydantic models 與 schema 往返 + required 驗證(REQ-A0-IFC-003） ---

def test_result_record_roundtrip_and_required_validation():
    from pydantic import ValidationError
    from quantlab.contracts import (
        BacktestConfig,
        CostConfig,
        PerformanceMetrics,
        ResultRecord,
    )

    cfg = BacktestConfig(
        start="2020-01-01", end="2024-01-01", rebalance="monthly",
        fill="next_open", mode="net",
        cost_config=CostConfig(
            commission_bps=2, slippage_bps=1, tw_transaction_tax_bps=30,
            us_dividend_withholding_pct=0.21, fx_spread_bps=5,
        ),
        seed=42, data_version="v0",
        walk_forward={"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    )
    metric = PerformanceMetrics(
        cumulative_return=0.5, annualized_return=0.1, annualized_vol=0.2,
        max_drawdown=-0.3, sharpe=0.5, turnover=1.2, basis="net", segment="out_of_sample",
    )
    rec = ResultRecord(run_id="r1", strategy_name="BuyAndHold", config=cfg, metrics=[metric])

    # round-trip:dump → reload → 相等
    reloaded = ResultRecord.model_validate_json(rec.model_dump_json())
    assert reloaded == rec

    # required 驗證:缺 run_id 應拋 ValidationError
    with pytest.raises(ValidationError):
        ResultRecord(strategy_name="x", config=cfg, metrics=[metric])  # type: ignore[call-arg]

    # 約束驗證:max_drawdown 必須 <= 0
    with pytest.raises(ValidationError):
        PerformanceMetrics(
            cumulative_return=0, annualized_return=0, annualized_vol=0.1,
            max_drawdown=0.3, sharpe=0, turnover=0, basis="net", segment="full",
        )


# --- 3. 框架隔離:engine/data 不得 import ML 框架(NFR-A0-FWAGN-001) ---

FORBIDDEN = {"torch", "tensorflow", "jax", "flax"}


def _imports_in(pkg_dir: Path) -> set[str]:
    found: set[str] = set()
    for py in pkg_dir.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
    return found


def test_engine_and_data_have_no_ml_framework_imports():
    quantlab_dir = Path(importlib.import_module("quantlab").__file__).parent
    for sub in ("engine", "data"):
        pkg = quantlab_dir / sub
        assert pkg.is_dir(), f"quantlab/{sub} 必須存在"
        leaked = _imports_in(pkg) & FORBIDDEN
        assert not leaked, f"quantlab/{sub} 洩漏框架 import: {leaked}"
