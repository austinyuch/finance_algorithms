"""H-1 deep-learning research lab — statistical performance report + self-contained viz.

Requirements: REQ-H-STATREPORT-001, REQ-H-VIZ-001.
"""
from __future__ import annotations

import math

import numpy as np
import pytest


def _series():
    rng = np.random.default_rng(3)
    model = list(rng.normal(0.010, 0.03, 60))
    base = list(rng.normal(0.004, 0.02, 60))
    return {"DeepForecastAllocationStrategy": model, "StaticWeights": base}


def _learning_curve():
    return [0.9, 0.6, 0.45, 0.4, 0.38]


# --- REQ-H-STATREPORT-001 ------------------------------------------------------

def test_report_ranks_oos_net_only_and_keeps_baseline_visible():
    from quantlab.research import build_deep_model_performance_report

    report = build_deep_model_performance_report(
        _series(), learning_curve=_learning_curve(),
        model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
    )

    assert report["claim_boundary"] == "no_alpha_claim"
    assert report["metric_authority"] == "out_of_sample_net_only"
    rows = report["rows"]
    names = [r["strategy_name"] for r in rows]
    assert "StaticWeights" in names  # baseline stays visible
    sharpes = [r["oos_net_sharpe"] for r in rows]
    assert sharpes == sorted(sharpes, reverse=True)  # ranked desc on OOS-net only


def test_report_stat_fields_present_and_finite():
    from quantlab.research import build_deep_model_performance_report

    report = build_deep_model_performance_report(
        _series(), learning_curve=_learning_curve(),
        model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
    )

    for row in report["rows"]:
        dist = row["distribution"]
        for key in ("mean", "volatility", "skew", "excess_kurtosis", "var_5pct"):
            assert key in dist and np.isfinite(dist[key])
        assert row["rolling_sharpe"] and all(np.isfinite(v) for v in row["rolling_sharpe"])
        assert row["drawdown"] and all(np.isfinite(v) and v <= 1e-9 for v in row["drawdown"])
        assert row["equity_curve"] and all(np.isfinite(v) for v in row["equity_curve"])
        assert np.isfinite(row["oos_net_sharpe"])

    model_row = next(r for r in report["rows"] if r["strategy_name"] == "DeepForecastAllocationStrategy")
    assert model_row["learning_curve"] == _learning_curve()


def test_report_checksum_is_deterministic():
    from quantlab.research import build_deep_model_performance_report

    kwargs = dict(learning_curve=_learning_curve(),
                  model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights")
    r1 = build_deep_model_performance_report(_series(), **kwargs)
    r2 = build_deep_model_performance_report(_series(), **kwargs)

    assert r1["checksum"] == r2["checksum"]
    assert len(r1["checksum"]) == 64


def test_report_fails_closed_on_degenerate_series():
    from quantlab.research import build_deep_model_performance_report

    with pytest.raises(ValueError):
        build_deep_model_performance_report(
            {"DeepForecastAllocationStrategy": [0.0] * 30, "StaticWeights": [0.0] * 30},
            learning_curve=_learning_curve(),
            model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
        )

    with pytest.raises(ValueError):
        build_deep_model_performance_report(
            {"DeepForecastAllocationStrategy": [], "StaticWeights": []},
            learning_curve=_learning_curve(),
            model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
        )


def test_report_var_matches_historical_percentile():
    from quantlab.research import build_deep_model_performance_report

    series = {"DeepForecastAllocationStrategy": list(np.linspace(-0.1, 0.1, 50)),
              "StaticWeights": list(np.linspace(-0.05, 0.05, 50))}
    report = build_deep_model_performance_report(
        series, learning_curve=_learning_curve(),
        model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
    )
    row = next(r for r in report["rows"] if r["strategy_name"] == "StaticWeights")
    expected = float(-np.percentile(np.asarray(series["StaticWeights"]), 5))
    assert row["distribution"]["var_5pct"] == pytest.approx(expected, rel=1e-6)


# --- REQ-H-VIZ-001 -------------------------------------------------------------

def test_viz_svg_is_self_contained():
    from quantlab.research import build_deep_model_performance_report
    from quantlab.research import render_performance_report_svg

    report = build_deep_model_performance_report(
        _series(), learning_curve=_learning_curve(),
        model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
    )
    svg = render_performance_report_svg(report)

    assert svg.lstrip().startswith("<svg")
    assert "</svg>" in svg
    # no network fetch / CDN / external script dependency
    for forbidden in ("src=", "<script", "cdn", 'href="http', "url(http"):
        assert forbidden not in svg
    # the ONLY permitted "http" is the SVG namespace identifier (never fetched)
    assert svg.count("http") == svg.count('xmlns="http://www.w3.org/2000/svg"') == 1
    # accessible text-equivalent labels present
    assert "Learning curve" in svg
    assert "Drawdown" in svg


def test_viz_is_deterministic_and_html_wraps_svg():
    from quantlab.research import build_deep_model_performance_report
    from quantlab.research import render_performance_report_html, render_performance_report_svg

    report = build_deep_model_performance_report(
        _series(), learning_curve=_learning_curve(),
        model_name="DeepForecastAllocationStrategy", baseline_name="StaticWeights",
    )
    assert render_performance_report_svg(report) == render_performance_report_svg(report)
    html = render_performance_report_html(report)
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "<svg" in html
    assert "no_alpha_claim" in html
    for forbidden in ("src=", "<script", "cdn", 'href="http', "url(http"):
        assert forbidden not in html
    # only the embedded SVG namespace identifier may contain "http"
    assert html.count("http") == html.count('xmlns="http://www.w3.org/2000/svg"') == 1
