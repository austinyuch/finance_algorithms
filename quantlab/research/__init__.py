"""研究工具(篩選 / 分析)。可用 numpy/pandas/statsmodels;非回測核心(不受框架隔離鐵律約束)。"""
from quantlab.research.screen import screen_cointegration_hedge, screen_one_candidate

__all__ = ["screen_cointegration_hedge", "screen_one_candidate"]
