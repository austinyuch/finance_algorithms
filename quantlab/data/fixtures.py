"""A0-1 toy bitemporal fixture(REQ-A0-PIT-004)。

刻意內含三個 point-in-time 驗證情境:
  - 價格的 available_date(此處與 event_date 同日,代表收盤即可得)
  - 一檔中途下市標的(BBB)→ survivorship 測試
  - 一條有「釋出 lag + 修訂」的總經序列(CPI)→ lookahead/revision 測試
"""
from __future__ import annotations

import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider


def build_toy_dataset() -> InMemoryPITDataProvider:
    ts = pd.Timestamp

    prices = pd.DataFrame(
        [
            {"symbol": "AAA", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"), "close": 100.0},
            {"symbol": "AAA", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"), "close": 110.0},
            {"symbol": "BBB", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"), "close": 50.0},
            {"symbol": "BBB", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"), "close": 55.0},
        ]
    )

    listings = pd.DataFrame(
        [
            {"symbol": "AAA", "list_date": ts("2019-01-01"), "delist_date": pd.NaT},
            {"symbol": "BBB", "list_date": ts("2019-01-01"), "delist_date": ts("2020-03-15")},
        ]
    )

    macro = pd.DataFrame(
        [
            # Jan CPI:首次釋出(lag ~6 週)→ 後續修訂(同 event_date,較晚 available)
            {"series": "CPI", "event_date": ts("2020-01-01"), "available_date": ts("2020-02-12"), "value": 256.0},
            {"series": "CPI", "event_date": ts("2020-01-01"), "available_date": ts("2020-03-11"), "value": 256.4},
            # Feb CPI
            {"series": "CPI", "event_date": ts("2020-02-01"), "available_date": ts("2020-03-12"), "value": 257.0},
        ]
    )

    return InMemoryPITDataProvider(prices=prices, listings=listings, macro=macro)
