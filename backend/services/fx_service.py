from __future__ import annotations

from typing import Any

import requests

from backend.config import settings


class FXService:

    FX_MAP = {
        "USD": {
            "secid": "USD000UTSTOM",
            "display_name": "USD/RUB TOM",
            "aliases": ["доллар", "usd", "usd/rub", "доллар сша", "бакс"],
            "rate_field": "CBRF_USD_LAST",
        },
        "EUR": {
            "secid": "EUR_RUB__TOM",
            "display_name": "EUR/RUB TOM",
            "aliases": ["евро", "eur", "eur/rub"],
            "rate_field": "CBRF_EUR_LAST",
        },
        "CNY": {
            "secid": "CNYRUB_TOM",
            "display_name": "CNY/RUB TOM",
            "aliases": ["юань", "cny", "cny/rub", "китайский юань"],
            "rate_field": None,
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

        live_quote = self._get_live_fx_quote(item)
        if live_quote and live_quote.get("price") is not None and live_quote.get("price") > 0:
            return live_quote

        rates_quote = self._get_rates_fallback(currency_code, item)
        if rates_quote and rates_quote.get("price") is not None and rates_quote.get("price") > 0:
            return rates_quote

        return live_quote or rates_quote

    def _get_live_fx_quote(self, item: dict[str, Any]) -> dict[str, Any] | None:
        secid = item["secid"]
        url = f"{self.base_url}/engines/currency/markets/selt/securities/{secid}.json"

        response = requests.get(
            url,
            params={"iss.meta": "off"},
            timeout=self.timeout
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

        if not marketdata_item:
            return None

        price = self._extract_best_live_price(marketdata_item)

        return {
            "currency_code": self._find_code_by_secid(secid),
            "secid": secid,
            "display_name": item["display_name"],
            "shortname": (security_item or {}).get("SHORTNAME"),
            "price": price,
            "boardid": marketdata_item.get("BOARDID"),
            "trading_status": marketdata_item.get("TRADINGSTATUS"),
            "last_update_time": marketdata_item.get("UPDATETIME"),
            "source_name": "moex_fx",
            "source_kind": "live_marketdata",
            "raw_price_fields": {
                "LAST": self._to_float(marketdata_item.get("LAST")),
                "MARKETPRICE": self._to_float(marketdata_item.get("MARKETPRICE")),
                "LASTTOPREVPRICE": self._to_float(marketdata_item.get("LASTTOPREVPRICE")),
                "LCLOSE": self._to_float(marketdata_item.get("LCLOSE")),
                "LEGALCLOSEPRICE": self._to_float(marketdata_item.get("LEGALCLOSEPRICE")),
                "WAPRICE": self._to_float(marketdata_item.get("WAPRICE")),
            }
        }

    def _get_rates_fallback(self, currency_code: str, item: dict[str, Any]) -> dict[str, Any] | None:
        rate_field = item.get("rate_field")
        if not rate_field:
            return None

        url = f"{self.base_url}/statistics/engines/currency/markets/selt/rates.json"

        response = requests.get(
            url,
            params={"iss.meta": "off"},
            timeout=self.timeout
        )
        response.raise_for_status()

        payload = response.json()

        cbrf = payload.get("cbrf", {})
        columns = cbrf.get("columns", [])
        rows = cbrf.get("data", [])

        if columns and rows:
            row = dict(zip(columns, rows[0]))
            price = self._to_float(row.get(rate_field))
            if price is not None:
                return {
                    "currency_code": currency_code,
                    "secid": item["secid"],
                    "display_name": item["display_name"],
                    "shortname": item["display_name"],
                    "price": price,
                    "boardid": "RATES",
                    "trading_status": "statistics",
                    "last_update_time": "10:00:00",
                    "source_name": "moex_fx_rates",
                    "source_kind": "rates_fallback",
                    "raw_price_fields": {
                        rate_field: price,
                    }
                }

        return None

    def build_fx_summary(self, fx_context: dict[str, Any] | None) -> str:
        if not fx_context:
            return "Данные по валюте не найдены."

        parts = [
            f"По валютной паре {fx_context.get('display_name')} текущая цена составляет {fx_context.get('price')}."
        ]

        if fx_context.get("last_update_time"):
            parts.append(f"Время обновления: {fx_context.get('last_update_time')}.")

        if fx_context.get("source_name"):
            parts.append(f"Источник: {fx_context.get('source_name')}.")

        return " ".join(parts)

    def _extract_best_live_price(self, marketdata_item: dict[str, Any]) -> float | None:

        candidates = [
            self._to_float(marketdata_item.get("LAST")),
            self._to_float(marketdata_item.get("MARKETPRICE")),
            self._to_float(marketdata_item.get("LASTTOPREVPRICE")),
            self._to_float(marketdata_item.get("LCLOSE")),
            self._to_float(marketdata_item.get("LEGALCLOSEPRICE")),
            self._to_float(marketdata_item.get("WAPRICE")),
        ]

        for value in candidates:
            if value is not None and value > 0:
                return value

        for value in candidates:
            if value is not None:
                return value

        return None

    def _find_code_by_secid(self, secid: str) -> str | None:
        for code, item in self.FX_MAP.items():
            if item["secid"] == secid:
                return code
        return None

    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except Exception:
            return None