from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from backend.config import settings


class DividendService:


    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def get_all_dividends(self, ticker: str) -> list[dict[str, Any]]:
        ticker = (ticker or "").upper().strip()
        if not ticker:
            return []

        url = f"{self.base_url}/securities/{ticker}/dividends.json"

        response = requests.get(
            url,
            params={"iss.meta": "off"},
            timeout=self.timeout
        )
        response.raise_for_status()

        payload = response.json()
        dividends = payload.get("dividends", {})
        columns = dividends.get("columns", [])
        rows = dividends.get("data", [])

        if not columns or not rows:
            return []

        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(zip(columns, row))

            record_date = item.get("registryclosedate")
            dividend_value = item.get("value")

            if not record_date or dividend_value is None:
                continue

            result.append({
                "ticker": ticker,
                "secid": item.get("secid"),
                "isin": item.get("isin"),
                "record_date": record_date,
                "declared_date": item.get("decisiondate"),
                "dividend_per_share": self._to_float(dividend_value),
                "currency": item.get("currencyid"),
                "year": self._extract_year(record_date),
                "source_name": "moex_iss",
            })

        result.sort(
            key=lambda x: x.get("record_date") or "",
            reverse=True
        )
        return result

    def get_last_dividend(self, ticker: str) -> dict[str, Any] | None:
        items = self.get_all_dividends(ticker)
        if not items:
            return None
        return items[0]

    def get_dividend_by_year(self, ticker: str, year: int) -> dict[str, Any] | None:
        items = self.get_all_dividends(ticker)

        exact_matches = [x for x in items if x.get("year") == year]
        if exact_matches:
            exact_matches.sort(
                key=lambda x: x.get("record_date") or "",
                reverse=True
            )
            return exact_matches[0]

        return None

    def get_expected_dividend(self, ticker: str, year: int | None = None) -> dict[str, Any] | None:

        #Если есть запись за нужный год, возвращаем её, если год не задан, возвращаем последний доступный

        if year is not None:
            return self.get_dividend_by_year(ticker, year)
        return self.get_last_dividend(ticker)

    def build_last_dividend_summary(self, dividend: dict[str, Any] | None) -> str:
        if not dividend:
            return "Данные по последнему дивиденду не найдены."

        parts = [
            f"Последний известный дивиденд по бумаге {dividend.get('ticker')} составил {dividend.get('dividend_per_share')} {dividend.get('currency') or ''}."
        ]

        if dividend.get("record_date"):
            parts.append(f"Дата закрытия реестра: {dividend.get('record_date')}.")

        if dividend.get("declared_date"):
            parts.append(f"Дата решения: {dividend.get('declared_date')}.")

        if dividend.get("year"):
            parts.append(f"Год в контексте выплаты: {dividend.get('year')}.")

        return " ".join(parts)

    def build_year_dividend_summary(self, dividend: dict[str, Any] | None, year: int) -> str:
        if not dividend:
            return f"Данные по дивиденду за {year} год не найдены."

        parts = [
            f"По бумаге {dividend.get('ticker')} за {year} год найден дивиденд {dividend.get('dividend_per_share')} {dividend.get('currency') or ''}."
        ]

        if dividend.get("record_date"):
            parts.append(f"Дата отсечки: {dividend.get('record_date')}.")

        if dividend.get("declared_date"):
            parts.append(f"Дата решения: {dividend.get('declared_date')}.")

        return " ".join(parts)

    def _extract_year(self, record_date: str | None) -> int | None:
        if not record_date:
            return None
        try:
            return datetime.fromisoformat(record_date).year
        except Exception:
            return None

    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except Exception:
            return None