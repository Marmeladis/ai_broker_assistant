from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import requests

from backend.config import settings


class DividendService:
    """
    Строгая работа с дивидендами через MOEX ISS.

    Принципы:
    - не подменять запрошенный год предыдущим годом;
    - не выдавать старые выплаты за "ожидаемые";
    - не считать дивдоходность по устаревшим дивидендам;
    - отсеивать явно нереалистичные yield в рейтингах.
    """

    # сколько лет назад максимум считаем "свежей" дивидендную запись для рейтингов
    MAX_RANKING_DIVIDEND_AGE_DAYS = 550

    # защитный потолок для дивдоходности в рейтингах, чтобы не было 600%+
    MAX_REASONABLE_DIVIDEND_YIELD_PERCENT = 35.0

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
        """
        Только точное совпадение по году.
        Никаких "похожих" или "ближайших" годов.
        """
        items = self.get_all_dividends(ticker)

        exact_matches = [x for x in items if x.get("year") == year]
        if not exact_matches:
            return None

        exact_matches.sort(
            key=lambda x: x.get("record_date") or "",
            reverse=True
        )
        return exact_matches[0]

    def get_expected_dividend(self, ticker: str, year: int | None = None):
        # если спрашивают конкретный год → используем календарь
        if year:
            return None  # теперь логика выше

        return self.get_last_dividend(ticker)

    def get_top_dividend_stocks(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Рейтинг акций по дивидендной доходности, но только по свежим и реалистичным данным.

        Правила:
        - берём только бумаги с текущей ценой;
        - берём только последний дивиденд;
        - дивиденд должен быть достаточно свежим;
        - yield должен быть > 0 и <= MAX_REASONABLE_DIVIDEND_YIELD_PERCENT.
        """
        shares = self._get_share_universe(limit_universe=120)
        ranked = []

        for item in shares:
            ticker = item.get("ticker")
            price = item.get("price")
            shortname = item.get("name")

            if not ticker or price in [None, 0]:
                continue

            try:
                last_dividend = self.get_last_dividend(ticker)
            except Exception:
                last_dividend = None

            if not last_dividend:
                continue

            if not self._is_recent_dividend(last_dividend):
                continue

            dividend_per_share = last_dividend.get("dividend_per_share")
            if dividend_per_share in [None, 0]:
                continue

            try:
                dividend_yield_percent = round((float(dividend_per_share) / float(price)) * 100, 4)
            except Exception:
                continue

            if dividend_yield_percent <= 0:
                continue

            if dividend_yield_percent > self.MAX_REASONABLE_DIVIDEND_YIELD_PERCENT:
                continue

            ranked.append({
                "ticker": ticker,
                "name": shortname,
                "price": float(price),
                "dividend_per_share": float(dividend_per_share),
                "dividend_yield_percent": dividend_yield_percent,
                "record_date": last_dividend.get("record_date"),
                "year": last_dividend.get("year"),
                "currency": last_dividend.get("currency"),
                "source_name": "moex_iss",
            })

        ranked.sort(
            key=lambda x: x.get("dividend_yield_percent") or 0,
            reverse=True
        )

        return ranked[:limit]

    def get_dividend_aristocrats(self, min_years: int = 3, limit: int = 10) -> list[dict[str, Any]]:
        """
        Устойчивые дивидендные компании:
        - есть выплаты min_years лет подряд;
        - история должна быть относительно свежей;
        - текущая yield в разумном диапазоне.
        """
        shares = self._get_share_universe(limit_universe=120)
        result = []
        current_year = datetime.utcnow().year

        for item in shares:
            ticker = item.get("ticker")
            price = item.get("price")
            name = item.get("name")

            if not ticker or price in [None, 0]:
                continue

            try:
                dividends = self.get_all_dividends(ticker)
            except Exception:
                continue

            if not dividends:
                continue

            # берём только относительно свежую историю по годам
            years = sorted(list({
                d.get("year")
                for d in dividends
                if d.get("year") is not None and d.get("year") >= current_year - 6
            }))

            if len(years) < min_years:
                continue

            consecutive = 1
            max_consecutive = 1

            for i in range(1, len(years)):
                if years[i] == years[i - 1] + 1:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive)
                else:
                    consecutive = 1

            if max_consecutive < min_years:
                continue

            last_div = dividends[0]
            if not self._is_recent_dividend(last_div):
                continue

            div_value = last_div.get("dividend_per_share")
            if div_value in [None, 0]:
                continue

            try:
                dy = round((float(div_value) / float(price)) * 100, 4)
            except Exception:
                continue

            if dy <= 0:
                continue

            if dy > self.MAX_REASONABLE_DIVIDEND_YIELD_PERCENT:
                continue

            result.append({
                "ticker": ticker,
                "name": name,
                "years": max_consecutive,
                "dividend_yield": dy,
                "last_dividend": div_value,
                "record_date": last_div.get("record_date"),
                "year": last_div.get("year"),
            })

        result.sort(
            key=lambda x: (x["years"], x["dividend_yield"]),
            reverse=True
        )

        return result[:limit]

    def _get_share_universe(self, limit_universe: int = 120) -> list[dict[str, Any]]:
        """
        Universe акций через MOEX shares market с текущей ценой.
        """
        url = f"{self.base_url}/engines/stock/markets/shares/securities.json"

        response = requests.get(
            url,
            params={
                "iss.meta": "off",
                "iss.only": "marketdata,securities",
                "marketdata.columns": "SECID,LAST,BOARDID",
                "securities.columns": "SECID,SHORTNAME,PRIMARY_BOARDID",
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()

        marketdata = payload.get("marketdata", {})
        md_cols = marketdata.get("columns", [])
        md_rows = marketdata.get("data", [])

        securities = payload.get("securities", {})
        sec_cols = securities.get("columns", [])
        sec_rows = securities.get("data", [])

        market_map = {}
        for row in md_rows:
            item = dict(zip(md_cols, row))
            secid = item.get("SECID")
            if not secid:
                continue
            market_map[secid] = item

        result = []
        for row in sec_rows:
            item = dict(zip(sec_cols, row))
            secid = item.get("SECID")
            if not secid:
                continue

            md = market_map.get(secid, {})
            last_price = self._to_float(md.get("LAST"))

            if last_price is None or last_price <= 0:
                continue

            result.append({
                "ticker": secid,
                "name": item.get("SHORTNAME"),
                "price": last_price,
                "boardid": md.get("BOARDID") or item.get("PRIMARY_BOARDID"),
            })

        return result[:limit_universe]

    def _is_recent_dividend(self, dividend_item: dict[str, Any]) -> bool:
        record_date = dividend_item.get("record_date")
        if not record_date:
            return False

        try:
            dt = datetime.fromisoformat(record_date)
        except Exception:
            return False

        cutoff = datetime.utcnow() - timedelta(days=self.MAX_RANKING_DIVIDEND_AGE_DAYS)
        return dt >= cutoff

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

    def get_expected_dividend_with_calendar(
            self,
            db,
            ticker: str,
            year: int
    ):
        """
        Приоритет:
        1. Сначала смотрим календарь (БД)
        2. Если нет — НЕ ВРЁМ, возвращаем None
        """

        from backend.services.dividend_calendar_service import DividendCalendarService

        calendar_service = DividendCalendarService()

        item = calendar_service.get_by_ticker(db, ticker, year)

        if not item:
            return None

        return {
            "ticker": item.ticker,
            "year": item.year,
            "dividend_per_share": item.dividend_per_share,
            "currency": "RUB",
            "record_date": None,  # честно — у нас только T+1
            "t1_buy_date": item.t1_buy_date.isoformat(),
            "status": item.status,
            "source_name": item.source_name,
            "dividend_found": True,
        }