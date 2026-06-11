"""D-3 real-data-shaped regime benchmark via vintage loader."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from hypothesis import HealthCheck, given, settings, strategies as st


def _fred_csv(series: str, rows: list[tuple[pd.Timestamp, float]]) -> str:
    body = "\n".join(f"{d.date()},{v}" for d, v in rows)
    return f"observation_date,{series}\n{body}\n"


def _write_vintage(root: Path, available: pd.Timestamp, source: str, raw: str) -> None:
    d = root / str(available.date())
    d.mkdir(parents=True, exist_ok=True)
    safe = source.replace(":", "_")
    (d / f"{safe}.json").write_text(json.dumps({
        "source": source,
        "available_date": str(available.date()),
        "is_approximate": False,
        "captured_at": available.isoformat(),
        "raw": raw,
    }), encoding="utf-8")


def _vintage_root(tmp_path: Path, n: int = 30) -> tuple[Path, list[pd.Timestamp]]:
    dates = list(pd.date_range("2020-01-31", periods=n, freq="ME"))
    sp500 = [100.0 + i * 2.0 if i < n // 2 else 100.0 + n - i for i in range(n)]
    copper = [80.0 + i * 0.5 for i in range(n)]
    curve = [0.8 if i < n // 2 else -0.4 for i in range(n)]
    root = tmp_path / "raw"
    for i, available in enumerate(dates):
        _write_vintage(root, available, "fred:SP500", _fred_csv("SP500", list(zip(dates[: i + 1], sp500[: i + 1]))))
        _write_vintage(root, available, "fred:PCOPPUSDM",
                       _fred_csv("PCOPPUSDM", list(zip(dates[: i + 1], copper[: i + 1]))))
        _write_vintage(root, available, "fred:T10Y2Y", _fred_csv("T10Y2Y", list(zip(dates[: i + 1], curve[: i + 1]))))
    return root, dates


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(n=st.integers(min_value=8, max_value=36), asof_idx=st.integers(min_value=0, max_value=35))
def test_pbt_benchmark_dates_are_sorted_and_asof_gated(tmp_path, n, asof_idx):
    from quantlab.data.vintage import build_provider_from_vintage
    from quantlab.models.regime_benchmark import benchmark_price_dates

    root, dates = _vintage_root(tmp_path, n=n)
    asof = dates[min(asof_idx, n - 1)]
    data = build_provider_from_vintage(root, fred_price_series={"SP500", "PCOPPUSDM"})

    selected = benchmark_price_dates(data, ["SP500", "PCOPPUSDM"], asof)

    assert selected == sorted(selected)
    assert all(d <= asof for d in selected)
    assert set(selected).issubset(set(dates[: dates.index(asof) + 1]))


def test_real_data_regime_benchmark_logs_oos_baseline_and_no_alpha_claim(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage
    from quantlab.models.regime_benchmark import benchmark_price_dates, run_real_data_regime_benchmark
    from quantlab.tracking import LocalResultStore

    root, dates = _vintage_root(tmp_path)
    data = build_provider_from_vintage(root, fred_price_series={"SP500", "PCOPPUSDM"})
    benchmark_dates = benchmark_price_dates(data, ["SP500", "PCOPPUSDM"], dates[-1])
    store = LocalResultStore(tmp_path / "runs.sqlite")

    report = run_real_data_regime_benchmark(data, benchmark_dates, store)

    assert report["claim_boundary"] == "no_alpha_claim"
    assert {row["strategy_name"] for row in report["leaderboard"]} == {
        "RegimeAllocationStrategy",
        "StaticWeights",
    }
    assert all(row["oos_net_sharpe"] is not None for row in report["leaderboard"])
    assert report["data_version"] == "vintage-loader-real-source-format"
    assert report["regime_rebalance_dates"]
