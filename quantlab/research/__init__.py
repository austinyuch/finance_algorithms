"""研究工具(篩選 / 分析)。可用 numpy/pandas/statsmodels;非回測核心(不受框架隔離鐵律約束)。"""
from quantlab.research.align import align_asof
from quantlab.research.real_data_oos import (
    DataSufficiency,
    assess_data_sufficiency,
    resolve_cotemporal_universe,
    build_insufficient_data_report,
    build_real_data_oos_artifact,
    build_real_data_oos_report,
    validate_real_data_oos_artifact,
    write_real_data_oos_artifact,
)
from quantlab.research.model_performance_report import build_deep_model_performance_report
from quantlab.research.model_report_viz import (
    render_performance_report_html,
    render_performance_report_svg,
)
from quantlab.research.screen import screen_cointegration_hedge, screen_one_candidate

__all__ = [
    "screen_cointegration_hedge",
    "screen_one_candidate",
    "align_asof",
    "build_deep_model_performance_report",
    "render_performance_report_html",
    "render_performance_report_svg",
    "DataSufficiency",
    "assess_data_sufficiency",
    "resolve_cotemporal_universe",
    "build_real_data_oos_report",
    "build_insufficient_data_report",
    "build_real_data_oos_artifact",
    "validate_real_data_oos_artifact",
    "write_real_data_oos_artifact",
]
