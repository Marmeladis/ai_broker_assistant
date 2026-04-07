from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import requests

from backend.config import settings


class PriceHistoryService:
    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS
        self.engine = "stock"
        self.market = "shares"
        self.board = "TQBR"

    def get_candles(
        self,
        ticker: str,
        interval: str = "24",
        limit: int = 30
    ) -> list[dict[str, Any]]:
        """
        interval:
        24 = дневные свечи
        60 = часовые свечи
        """

        ticker = ticker.upper().strip()

        days_back = self._estimate_days_back(interval=interval, limit=limit)

        till_dt = datetime.utcnow().date()
        from_dt = till_dt - timedelta(days=days_back)

        url = (
            f"{self.base_url}/engines/{self.engine}/markets/{self.market}"
            f"/boards/{self.board}/securities/{ticker}/candles.json"
        )

        params = {
            "interval": interval,
            "from": from_dt.isoformat(),
            "till": till_dt.isoformat(),
            "iss.meta": "off",
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        candles = data.get("candles", {})
        columns = candles.get("columns", [])
        rows = candles.get("data", [])

        if not rows:
            return []

        result: list[dict[str, Any]] = []
        for row in rows:
            item = {columns[i]: row[i] for i in range(len(columns))}
            result.append(item)

        result = sorted(result, key=lambda x: x.get("begin") or "")

        return result[-limit:]

    def _estimate_days_back(self, interval: str, limit: int) -> int:
        if interval == "24":
            # запас по дням, чтобы хватило торговых свечей
            return max(limit * 3, 90)

        if interval == "60":
            return max(limit * 5, 30)

        return max(limit * 3, 90)