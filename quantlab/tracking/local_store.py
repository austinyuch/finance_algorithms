"""LocalResultStore — 零重依賴的 Tier2 追蹤後端(stdlib sqlite3)。

實作 quantlab.contracts.ResultStore Protocol。每筆 ResultRecord 存成一列;
leaderboard **只依 out_of_sample + net 的 Sharpe 排序**(FMEA-A0-05:杜絕用高
in_sample/full 指標灌水),NULL(無 OOS-net)排末。run_id 缺則生成,確保可追溯。
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Mapping


def _oos_net_sharpe(record: Mapping[str, Any]) -> float | None:
    """擷取 out_of_sample + net 的 Sharpe;不存在回 None(leaderboard 排末)。"""
    for m in record.get("metrics", []):
        if m.get("segment") == "out_of_sample" and m.get("basis") == "net":
            return float(m.get("sharpe"))
    return None


class LocalResultStore:
    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS runs ("
            "run_id TEXT PRIMARY KEY, strategy_name TEXT, oos_net_sharpe REAL, "
            "is_baseline INTEGER, record_json TEXT)"
        )
        self._conn.commit()

    def log(self, record: Mapping[str, Any]) -> str:
        run_id = str(record.get("run_id") or uuid.uuid4().hex)
        rec = {**dict(record), "run_id": run_id}
        self._conn.execute(
            "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?)",
            (run_id, rec.get("strategy_name"), _oos_net_sharpe(rec),
             1 if rec.get("is_baseline") else 0, json.dumps(rec, ensure_ascii=False)),
        )
        self._conn.commit()
        return run_id

    def get(self, run_id: str) -> dict:
        row = self._conn.execute(
            "SELECT record_json FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def leaderboard(self, metric: str = "oos_net_sharpe", descending: bool = True) -> list[dict]:
        order = "DESC" if descending else "ASC"
        rows = self._conn.execute(
            "SELECT run_id, strategy_name, oos_net_sharpe, is_baseline FROM runs "
            f"ORDER BY oos_net_sharpe IS NULL, oos_net_sharpe {order}"
        ).fetchall()
        return [{"run_id": r[0], "strategy_name": r[1], "oos_net_sharpe": r[2],
                 "is_baseline": bool(r[3])} for r in rows]
