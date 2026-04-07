from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from backend.config import settings


class MarketProviderService:
    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.engine = settings.MOEX_SHARES_ENGINE
        self.market = settings.MOEX_SHARES_MARKET
        self.default_board = settings.MOEX_DEFAULT_BOARD
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def fetch_latest_share_quote(self, ticker: str, board: str | None = None) -> dict[str, Any]:
        ticker = ticker.upper().strip()
        board = (board or self.default_board).upper().strip()

        url = (
            f"{self.base_url}/engines/{self.engine}/markets/{self.market}"
            f"/boards/{board}/securities/{ticker}.json"
        )

        params = {
            "iss.meta": "off",
            "iss.only": "marketdata,securities",
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        marketdata = payload.get("marketdata", {})
        securities = payload.get("securities", {})

        market_columns = marketdata.get("columns", [])
        market_rows = marketdata.get("data", [])
        sec_columns = securities.get("columns", [])
        sec_rows = securities.get("data", [])

        market_row = self._row_to_dict(market_columns, market_rows[0]) if market_rows else {}
        sec_row = self._row_to_dict(sec_columns, sec_rows[0]) if sec_rows else {}

        last_price = market_row.get("LAST")
        if last_price is None:
            last_price = market_row.get("LCURRENTPRICE")
        if last_price is None:
            last_price = market_row.get("MARKETPRICE")

        volume = market_row.get("VALTODAY") or market_row.get("VOLTODAY")
        last_time = market_row.get("LASTTIME")
        update_time = market_row.get("UPDATETIME")

        recorded_at = self._build_recorded_at(last_time=last_time, update_time=update_time)

        return {
            "ticker": ticker,
            "board": board,
            "shortname": sec_row.get("SHORTNAME") or sec_row.get("SECNAME") or ticker,
            "price": float(last_price) if last_price is not None else None,
            "volume": float(volume) if volume is not None else None,
            "recorded_at": recorded_at,
            "source_name": "moex_iss",
            "raw_marketdata": market_row,
            "raw_security": sec_row,
        }

    def _row_to_dict(self, columns: list[str], row: list[Any]) -> dict[str, Any]:
        return {col: row[idx] for idx, col in enumerate(columns)}

    def _build_recorded_at(self, last_time: str | None, update_time: str | None) -> datetime:
        now = datetime.utcnow()

        time_str = last_time or update_time
        if not time_str:
            return now

        try:
            hh, mm, ss = [int(x) for x in time_str.split(":")]
            return now.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        except Exception:
            return now