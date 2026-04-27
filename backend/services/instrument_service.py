from __future__ import annotations

import re
from typing import Any

import requests
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import FinancialInstrument, InstrumentAlias


class InstrumentService:
    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def normalize_text(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.replace("ё", "е")
        text = re.sub(r"[^a-zA-Zа-яА-Я0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def looks_like_ticker(self, text: str) -> bool:
        text = (text or "").strip().upper()
        return bool(re.fullmatch(r"[A-Z0-9.\-]{1,20}", text))

    def resolve_or_create_instrument(self, db: Session, query: str) -> FinancialInstrument | None:
        query = (query or "").strip()
        if not query:
            return None

        local = self.find_local_instrument(db, query)
        if local:
            return local

        remote = None
        if self.looks_like_ticker(query):
            remote = self.fetch_instrument_by_ticker_from_moex(query)

        if not remote:
            remote = self.search_instrument_by_name_from_moex(query)

        if not remote:
            return None

        return self.upsert_local_instrument_from_remote(db, remote)

    def find_local_instrument(self, db: Session, query: str) -> FinancialInstrument | None:
        query_norm = self.normalize_text(query)
        query_upper = query.strip().upper()

        instrument = (
            db.query(FinancialInstrument)
            .filter(FinancialInstrument.ticker == query_upper)
            .first()
        )
        if instrument:
            return instrument

        aliases = db.query(InstrumentAlias).all()
        for alias in aliases:
            if self.normalize_text(alias.alias) == query_norm:
                instrument = (
                    db.query(FinancialInstrument)
                    .filter(FinancialInstrument.ticker == alias.ticker)
                    .first()
                )
                if instrument:
                    return instrument

        instruments = db.query(FinancialInstrument).all()
        for item in instruments:
            item_name_norm = self.normalize_text(item.name or "")
            if item_name_norm == query_norm:
                return item

        for item in instruments:
            item_name_norm = self.normalize_text(item.name or "")
            if query_norm and query_norm in item_name_norm:
                return item

        return None

    def fetch_instrument_by_ticker_from_moex(self, ticker: str) -> dict[str, Any] | None:
        ticker = ticker.upper().strip()
        url = f"{self.base_url}/securities/{ticker}.json"
        params = {
            "iss.meta": "off",
            "iss.only": "description,boards",
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code != 200:
            return None

        payload = response.json()

        description = self._extract_description(payload.get("description", {}))
        boards = self._extract_boards(payload.get("boards", {}))

        if not description and not boards:
            return None

        secid = description.get("SECID") or ticker
        shortname = description.get("SHORTNAME") or description.get("NAME") or ticker
        board = self._pick_best_board(boards)

        return {
            "ticker": secid.upper(),
            "name": shortname,
            "board": board or "TQBR",
            "engine": "stock",
            "market": "shares",
            "currency": "RUB",
            "type": "stock",
            "aliases": [shortname] if shortname else []
        }

    def search_instrument_by_name_from_moex(self, query: str) -> dict[str, Any] | None:
        url = f"{self.base_url}/securities.json"
        params = {
            "iss.meta": "off",
            "iss.only": "securities",
            "securities.columns": "secid,shortname,primary_boardid,is_traded,group",
            "q": query,
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code != 200:
            return None

        payload = response.json()
        securities = payload.get("securities", {})
        columns = securities.get("columns", [])
        rows = securities.get("data", [])

        if not rows:
            return None

        candidates = []
        for row in rows:
            item = {columns[i]: row[i] for i in range(len(columns))}
            candidates.append(item)

        best = self._pick_best_search_result(query, candidates)
        if not best:
            return None

        secid = (best.get("secid") or "").upper()
        if not secid:
            return None

        exact = self.fetch_instrument_by_ticker_from_moex(secid)
        if exact:
            return exact

        return {
            "ticker": secid,
            "name": best.get("shortname") or secid,
            "board": best.get("primary_boardid") or "TQBR",
            "engine": "stock",
            "market": "shares",
            "currency": "RUB",
            "type": "stock",
            "aliases": [best.get("shortname")] if best.get("shortname") else []
        }

    def upsert_local_instrument_from_remote(self, db: Session, remote: dict[str, Any]) -> FinancialInstrument:
        ticker = remote["ticker"].upper()

        instrument = (
            db.query(FinancialInstrument)
            .filter(FinancialInstrument.ticker == ticker)
            .first()
        )

        if not instrument:
            instrument = FinancialInstrument(
                ticker=ticker,
                name=remote.get("name") or ticker,
                type=remote.get("type") or "stock",
                currency=remote.get("currency") or "RUB"
            )
            db.add(instrument)
            db.commit()
            db.refresh(instrument)
        else:
            changed = False
            if remote.get("name") and instrument.name != remote["name"]:
                instrument.name = remote["name"]
                changed = True
            if remote.get("type") and instrument.type != remote["type"]:
                instrument.type = remote["type"]
                changed = True
            if remote.get("currency") and instrument.currency != remote["currency"]:
                instrument.currency = remote["currency"]
                changed = True
            if changed:
                db.commit()
                db.refresh(instrument)

        for alias in remote.get("aliases", []):
            alias = (alias or "").strip()
            if not alias:
                continue

            exists = (
                db.query(InstrumentAlias)
                .filter(
                    InstrumentAlias.ticker == ticker,
                    InstrumentAlias.alias == alias
                )
                .first()
            )
            if not exists:
                db.add(InstrumentAlias(ticker=ticker, alias=alias))

        db.commit()
        return instrument

    def _extract_description(self, section: dict[str, Any]) -> dict[str, Any]:
        columns = section.get("columns", [])
        rows = section.get("data", [])

        result = {}
        for row in rows:
            item = {columns[i]: row[i] for i in range(len(columns))}
            name = item.get("name")
            value = item.get("value")
            if name:
                result[name] = value
        return result

    def _extract_boards(self, section: dict[str, Any]) -> list[dict[str, Any]]:
        columns = section.get("columns", [])
        rows = section.get("data", [])
        result = []

        for row in rows:
            result.append({columns[i]: row[i] for i in range(len(columns))})

        return result

    def _pick_best_board(self, boards: list[dict[str, Any]]) -> str | None:
        if not boards:
            return None

        for board in boards:
            if board.get("boardid") == "TQBR":
                return "TQBR"

        for board in boards:
            if board.get("is_primary") == 1:
                return board.get("boardid")

        for board in boards:
            if board.get("is_traded") == 1:
                return board.get("boardid")

        return boards[0].get("boardid")

    def _pick_best_search_result(self, query: str, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        query_norm = self.normalize_text(query)

        scored = []
        for item in candidates:
            secid = self.normalize_text(item.get("secid") or "")
            shortname = self.normalize_text(item.get("shortname") or "")
            board = (item.get("primary_boardid") or "").upper()
            is_traded = item.get("is_traded", 0)

            score = 0
            if shortname == query_norm:
                score += 100
            if query_norm and query_norm in shortname:
                score += 50
            if secid == query_norm.upper():
                score += 120
            if board == "TQBR":
                score += 20
            if is_traded == 1:
                score += 20

            scored.append((score, item))

        if not scored:
            return None

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]