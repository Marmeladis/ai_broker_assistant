from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.services.price_history_service import PriceHistoryService


class HistoricalMarketService:

    def __init__(self):
        self.price_history_service = PriceHistoryService()

    def get_price_extremes(
        self,
        ticker: str,
        interval: str = "24",
        limit: int = 365
    ) -> dict[str, Any]:
        candles = self.price_history_service.get_candles(
            ticker=ticker,
            interval=interval,
            limit=limit
        )

        if not candles:
            return {
                "ticker": ticker,
                "found": False,
                "min_price": None,
                "min_price_date": None,
                "max_price": None,
                "max_price_date": None,
                "period_candles": 0
            }

        min_candle = None
        max_candle = None

        for candle in candles:
            low = candle.get("low")
            high = candle.get("high")

            if low is not None:
                if min_candle is None or float(low) < float(min_candle["low"]):
                    min_candle = candle

            if high is not None:
                if max_candle is None or float(high) > float(max_candle["high"]):
                    max_candle = candle

        return {
            "ticker": ticker,
            "found": True,
            "min_price": float(min_candle["low"]) if min_candle and min_candle.get("low") is not None else None,
            "min_price_date": self._extract_date(min_candle),
            "max_price": float(max_candle["high"]) if max_candle and max_candle.get("high") is not None else None,
            "max_price_date": self._extract_date(max_candle),
            "period_candles": len(candles)
        }

    def get_max_turnover_day(
        self,
        ticker: str,
        interval: str = "24",
        limit: int = 365
    ) -> dict[str, Any]:
        candles = self.price_history_service.get_candles(
            ticker=ticker,
            interval=interval,
            limit=limit
        )

        if not candles:
            return {
                "ticker": ticker,
                "found": False,
                "max_turnover": None,
                "turnover_date": None,
                "period_candles": 0
            }

        best_candle = None

        for candle in candles:
            value = candle.get("value")
            if value is None:
                continue

            if best_candle is None or float(value) > float(best_candle["value"]):
                best_candle = candle

        if not best_candle:
            return {
                "ticker": ticker,
                "found": False,
                "max_turnover": None,
                "turnover_date": None,
                "period_candles": len(candles)
            }

        return {
            "ticker": ticker,
            "found": True,
            "max_turnover": float(best_candle["value"]),
            "turnover_date": self._extract_date(best_candle),
            "period_candles": len(candles)
        }

    def build_price_extremes_summary(self, data: dict[str, Any]) -> str:
        if not data or not data.get("found"):
            return "Исторические экстремумы цены не найдены."

        parts = [f"По бумаге {data.get('ticker')} за выбранный период найдены ценовые экстремумы."]

        if data.get("min_price") is not None:
            parts.append(
                f"Минимальная цена была {data.get('min_price')} "
                f"на дату {data.get('min_price_date')}."
            )

        if data.get("max_price") is not None:
            parts.append(
                f"Максимальная цена была {data.get('max_price')} "
                f"на дату {data.get('max_price_date')}."
            )

        return " ".join(parts)

    def build_max_turnover_summary(self, data: dict[str, Any]) -> str:
        if not data or not data.get("found"):
            return "Данные по максимальному торговому обороту не найдены."

        return (
            f"По бумаге {data.get('ticker')} максимальный торговый оборот за день "
            f"составил {data.get('max_turnover')} на дату {data.get('turnover_date')}."
        )

    def _extract_date(self, candle: dict | None) -> str | None:
        if not candle:
            return None

        begin_value = candle.get("begin")
        if not begin_value:
            return None

        try:
            return str(datetime.fromisoformat(begin_value).date())
        except Exception:
            return str(begin_value)