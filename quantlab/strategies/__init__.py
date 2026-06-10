"""策略實作。底層框架(PyTorch/TF/JAX/sklearn…)封裝於各策略內,經 Strategy Protocol 解耦。"""
from quantlab.strategies.baselines import RandomStrategy, StaticWeights
from quantlab.strategies.buyandhold import BuyAndHold
from quantlab.strategies.hedge import HedgeStrategy, build_hedge_weights

__all__ = ["BuyAndHold", "StaticWeights", "RandomStrategy", "HedgeStrategy", "build_hedge_weights"]
