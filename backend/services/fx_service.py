from __future__ import annotations

from typing import Any

import requests

from backend.config import settings


class FXService:

    FX_MAP = {
        "USD": {
            "secid": "USD000UTSTOM",
            "display_name": "USD/RUB TOM",
            "aliases": [
                "доллар",
                "доллар сша",
                "usd",
                "usd/rub",
                "usdrub",
                "бакс",
            ],
        },
        "EUR": {
            "secid": "EUR_RUB__TOM",
            "display_name": "EUR/RUB TOM",
            "aliases": [
                "евро",
                "eur",
                "eur/rub",
                "eurrub",
            ],
        },
        "CNY": {
            "secid": "CNYRUB_TOM",
            "display_name": "CNY/RUB TOM",
            "aliases": [
                "юань",
                "китайский юань",
                "cny",
                "cny/rub",
                "cnyrub",
            ],
        },
    }

    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def resolve_fx_from_text(self, text: str) -> dict[str, Any] | None:
        text = (text or "").lower().replace("ё", "е").strip()

        for code, item in self.FX_MAP.items():
            for alias in item["aliases"]:
                if alias in text:
                    return {
                        "code": code,
                        "secid": item["secid"],
                        "display_name": item["display_name"],
                    }

        return None

    def get_fx_price(self, currency_code: str) -> dict[str, Any] | None:
        currency_code = (currency_code or "").upper().strip()
        item = self.FX_MAP.get(currency_code)
        if not item:
            return None

        secid = item["secid"]
        url = f"{self.base_url}/engines/currency/markets/selt/securities/{secid}.json"

        response = requests.get(
            url,
            params={"iss.meta": "off"},
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()

        marketdata = payload.get("marketdata", {})
        marketdata_columns = marketdata.get("columns", [])
        marketdata_rows = marketdata.get("data", [])

        securities = payload.get("securities", {})
        securities_columns = securities.get("columns", [])
        securities_rows = securities.get("data", [])

        marketdata_item = None
        if marketdata_columns and marketdata_rows:
            marketdata_item = dict(zip(marketdata_columns, marketdata_rows[0]))

        security_item = None
        if securities_columns and securities_rows:
            security_item = dict(zip(securities_columns, securities_rows[0]))

        if not marketdata_item and not security_item:
            return None

        price = None
        boardid = None
        trading_status = None
        last_update_time = None

        if marketdata_item:
            price = (
                marketdata_item.get("LAST")
                or marketdata_item.get("MARKETPRICE")
                or marketdata_item.get("LCLOSE")
                or marketdata_item.get("LASTTOPREVPRICE")
            )
            boardid = marketdata_item.get("BOARDID")
            trading_status = marketdata_item.get("TRADINGSTATUS")
            last_update_time = marketdata_item.get("UPDATETIME")

        # Дополнительный fallback на случай пустого marketdata price
        if price is None and security_item:
            price = (
                security_item.get("PREVPRICE")
                or security_item.get("FACEVALUE")
            )

        numeric_price = self._to_float(price)
        if numeric_price is None:
            return None

        return {
            "currency_code": currency_code,
            "secid": secid,
            "display_name": item["display_name"],
            "shortname": (security_item or {}).get("SHORTNAME"),
            "price": numeric_price,
            "boardid": boardid,
            "trading_status": trading_status,
            "last_update_time": last_update_time,
            "source_name": "moex_fx",
        }

    def build_fx_summary(self, fx_context: dict[str, Any] | None) -> str:
        if not fx_context or fx_context.get("price") is None:
            return "Данные по валюте не найдены."

        parts = [
            f"По валютной паре {fx_context.get('display_name')} текущая цена составляет {fx_context.get('price')}."
        ]

        if fx_context.get("last_update_time"):
            parts.append(f"Время обновления: {fx_context.get('last_update_time')}.")

        parts.append("Источник: MOEX.")
        return " ".join(parts)

    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except Exception:
            return None