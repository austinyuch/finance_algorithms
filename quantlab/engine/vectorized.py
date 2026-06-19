"""向量化/低頻事件回測引擎(REQ-A0-BT-001..006)。

流程:依 config 產生再平衡日(calendar-driven)→ 各日 strategy.generate_signal(僅 PIT)
→ 以下一再平衡日的價格實現報酬 → 套成本(net 模式)→ 計指標(full + walk-forward IS/OOS)。

event_driven 目前支援低頻 event-date replay;高頻/order-book 撮合仍非 A0 範圍。
⚠️ 框架隔離:不得 import torch/tensorflow/jax。
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import pandas as pd

from quantlab.costs import trading_cost
from quantlab.engine.metrics import compute_metrics
from quantlab.engine.walkforward import walk_forward_splits
from quantlab.portfolio import select_rebalance_dates

_FREQ = {"monthly": ("ME", 12.0), "quarterly": ("QE", 4.0), "semiannual": ("2QE", 2.0)}


class VectorizedEngine:
    def run(self, strategy: Any, data: Any, config: Mapping[str, Any]) -> dict:
        freq, ppy = _FREQ[config["rebalance"]]
        mode = config.get("mode", "gross")
        cost_config = config.get("cost_config") or {}
        candidates = self._candidate_dates(config, freq)
        rebal = self._rebalance_dates(candidates, data, config)

        # 訓練:把訓練窗交給 strategy.fit(buy-and-hold 為 no-op);此處以全期 fit 一次。
        strategy.fit(None)

        returns, turnovers = self._simulate(strategy, data, rebal, cost_config, mode)
        total_turnover = float(turnovers.sum()) if len(turnovers) else 0.0

        metrics = [compute_metrics(returns, total_turnover, ppy, mode, "full")]
        metrics += self._walk_forward_metrics(returns, turnovers, rebal, config, ppy, mode)

        return {"run_id": "", "strategy_name": str(strategy.metadata.get("name", "?")),
                "strategy_metadata": dict(strategy.metadata), "config": self._result_config(config),
                "rebalance_dates": [str(d.date()) for d in rebal], "metrics": metrics}

    # --- internals ---

    @staticmethod
    def _close(data: Any, asof: pd.Timestamp, symbol: str) -> float | None:
        df = data.get(asof, ["close"], [symbol])
        if df.empty or symbol not in df.index:
            return None
        value = float(df.loc[symbol, "close"])
        # Chaos hardening (CR-A0-CHAOS-001): a non-finite (NaN/±inf) or non-positive
        # close is invalid market data, not a tradable price. Treat it as missing so the
        # simulator skips the leg instead of fabricating a NaN/bogus return that would
        # silently corrupt OOS-net metrics on the dashboard. `_simulate`'s `if p0 and p1`
        # guard already drops missing legs.
        if not math.isfinite(value) or value <= 0.0:
            return None
        return value

    @staticmethod
    def _result_config(config: Mapping[str, Any]) -> dict:
        out = dict(config)
        policy = out.get("rebalance_policy")
        if isinstance(policy, Mapping) and "classifier" in policy:
            clean_policy = dict(policy)
            classifier = clean_policy.pop("classifier")
            clean_policy["classifier"] = getattr(classifier, "__class__", type(classifier)).__name__
            out["rebalance_policy"] = clean_policy
        return out

    @staticmethod
    def _candidate_dates(config: Mapping[str, Any], freq: str) -> list[pd.Timestamp]:
        engine = config.get("engine", "vectorized")
        if engine not in {"vectorized", "event_driven"}:
            raise ValueError(f"unsupported engine: {engine}")
        if engine != "event_driven" or "event_dates" not in config:
            return pd.date_range(config["start"], config["end"], freq=freq).tolist()

        start = pd.Timestamp(config["start"])
        end = pd.Timestamp(config["end"])
        dates = sorted({pd.Timestamp(date) for date in config["event_dates"]})
        in_range = [date for date in dates if start <= date <= end]
        if not in_range:
            raise ValueError("event_driven requires at least one event_date within start/end")
        return in_range

    def _rebalance_dates(self, candidates: list[pd.Timestamp], data: Any,
                         config: Mapping[str, Any]) -> list[pd.Timestamp]:
        policy = config.get("rebalance_policy")
        if not policy:
            return candidates
        if not isinstance(policy, Mapping):
            raise ValueError("rebalance_policy must be a mapping")
        if policy.get("kind") != "regime":
            raise ValueError(f"unsupported rebalance_policy kind: {policy.get('kind')}")

        frequency = policy.get("frequency", config["rebalance"])
        labels = self._policy_labels(candidates, data, policy)
        return select_rebalance_dates(candidates, labels, frequency=frequency)

    @staticmethod
    def _policy_labels(candidates: list[pd.Timestamp], data: Any,
                       policy: Mapping[str, Any]) -> list[str]:
        if "labels" in policy:
            labels = policy["labels"]
            if not isinstance(labels, Mapping):
                raise ValueError("rebalance_policy.labels must be a mapping")
            out = []
            for date in candidates:
                key = str(date.date())
                if key not in labels:
                    raise ValueError(f"missing regime label for {key}")
                out.append(str(labels[key]))
            return out

        classifier = policy.get("classifier")
        if classifier is None:
            raise ValueError("regime rebalance_policy requires labels or classifier")
        return [str(classifier.predict(asof, data).label) for asof in candidates]

    def _simulate(self, strategy: Any, data: Any, rebal: list, cost_config: Mapping[str, Any],
                  mode: str) -> tuple[pd.Series, pd.Series]:
        returns: dict[pd.Timestamp, float] = {}
        turnovers: dict[pd.Timestamp, float] = {}
        prev_w: dict[str, float] = {}

        for k, t in enumerate(rebal):
            w = {s: float(x) for s, x in strategy.generate_signal(t, data).items()}
            syms = set(w) | set(prev_w)
            turnover = sum(abs(w.get(s, 0.0) - prev_w.get(s, 0.0)) for s in syms)
            turnovers[t] = turnover
            prev_w = w

            if k == len(rebal) - 1:
                break
            t_next = rebal[k + 1]
            port_ret = 0.0
            for s, wt in w.items():
                p0 = self._close(data, t, s)
                p1 = self._close(data, t_next, s)
                if p0 and p1:
                    port_ret += wt * (p1 / p0 - 1.0)
            cost = trading_cost(turnover, cost_config) if mode == "net" else 0.0
            returns[t] = port_ret - cost

        return pd.Series(returns, dtype="float64"), pd.Series(turnovers, dtype="float64")

    def _walk_forward_metrics(self, returns: pd.Series, turnovers: pd.Series, rebal: list,
                              config: Mapping[str, Any], ppy: float, mode: str) -> list[dict]:
        wf = config.get("walk_forward")
        if not wf or returns.empty:
            return []
        splits = walk_forward_splits(rebal, wf["train_window_months"],
                                     wf["test_window_months"], wf["step_months"])
        is_dates, oos_dates = set(), set()
        for train, test in splits:
            is_dates.update(train)
            oos_dates.update(test)
        out = []
        for seg, dates in (("in_sample", is_dates), ("out_of_sample", oos_dates)):
            sub = returns[returns.index.isin(dates)]
            sub_to = float(turnovers[turnovers.index.isin(dates)].sum())
            if len(sub):
                out.append(compute_metrics(sub, sub_to, ppy, mode, seg))
        return out
