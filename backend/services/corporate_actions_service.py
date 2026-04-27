from __future__ import annotations

from datetime import datetime
import requests

from backend.config import settings


class CorporateActionsService:

    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def get_dividend_context(
        self,
        ticker: str,
        current_price: float | None = None
    ) -> dict:
        ticker = (ticker or "").upper().strip()

        latest = self._fetch_latest_dividend(ticker)

        if not latest:
            return {
                "ticker": ticker,
                "dividend_found": False,
                "dividend_per_share": None,
                "record_date": None,
                "payment_date": None,
                "payment_timing_note": None,
                "currency": None,
                "dividend_yield_percent": None,
                "source_name": "moex_iss",
            }

        dividend_per_share = latest.get("value")
        record_date = latest.get("registryclosedate")
        currency = latest.get("currencyid")

        dividend_yield_percent = None
        if dividend_per_share is not None and current_price not in [None, 0]:
            try:
                dividend_yield_percent = round((float(dividend_per_share) / float(current_price)) * 100, 4)
            except Exception:
                dividend_yield_percent = None

        payment_timing_note = None
        if record_date:
            payment_timing_note = (
                f"после даты закрытия реестра обычно в срок до 25 рабочих дней "
                f"(отсечка: {record_date})"
            )

        return {
            "ticker": ticker,
            "dividend_found": True,
            "dividend_per_share": float(dividend_per_share) if dividend_per_share is not None else None,
            "record_date": record_date,
            "payment_date": None,
            "payment_timing_note": payment_timing_note,
            "currency": currency,
            "dividend_yield_percent": dividend_yield_percent,
            "source_name": "moex_iss",
        }

    def build_dividend_text_summary(self, dividend_context: dict | None) -> str | None:
        if not dividend_context:
            return None

        if not dividend_context.get("dividend_found"):
            return "Данные по дивидендам не найдены."

        ticker = dividend_context.get("ticker")
        dividend_per_share = dividend_context.get("dividend_per_share")
        record_date = dividend_context.get("record_date")
        payment_timing_note = dividend_context.get("payment_timing_note")
        dividend_yield = dividend_context.get("dividend_yield_percent")
        source_name = dividend_context.get("source_name")

        parts = [f"По бумаге {ticker} найдены дивиденды."]

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда: {dividend_per_share}.")

        if record_date:
            parts.append(f"Дата закрытия реестра: {record_date}.")

        if payment_timing_note:
            parts.append(
                "Поступление дивидендов обычно ожидается "
                "в срок до месяца после даты закрытия реестра."
            )

        if dividend_yield is not None:
            parts.append(f"Оценочная дивидендная доходность: {dividend_yield}%.")

        if source_name:
            parts.append(f"Источник: {source_name}.")

        return " ".join(parts)

    def is_dividend_date_close(
        self,
        dividend_context: dict | None,
        days_threshold: int = 21
    ) -> bool:
        if not dividend_context:
            return False

        record_date = dividend_context.get("record_date")
        if not record_date:
            return False

        try:
            record_dt = datetime.fromisoformat(record_date)
            now = datetime.utcnow()
            delta = (record_dt - now).days
            return 0 <= delta <= days_threshold
        except Exception:
            return False

    def _fetch_latest_dividend(self, ticker: str) -> dict | None:
        url = f"{self.base_url}/securities/{ticker}/dividends.json"

        response = requests.get(
            url,
            timeout=self.timeout,
            params={"iss.meta": "off"}
        )
        response.raise_for_status()

        data = response.json()
        dividends = data.get("dividends", {})
        columns = dividends.get("columns", [])
        rows = dividends.get("data", [])

        if not columns or not rows:
            return None

        parsed = []
        for row in rows:
            item = dict(zip(columns, row))

            registryclosedate = item.get("registryclosedate")
            value = item.get("value")

            if not registryclosedate or value is None:
                continue

            parsed.append(item)

        if not parsed:
            return None

        parsed.sort(
            key=lambda x: x.get("registryclosedate") or "",
            reverse=True
        )

        return parsed[0]