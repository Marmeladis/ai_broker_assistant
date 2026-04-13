import re
from sqlalchemy.orm import Session

from backend.models import FinancialInstrument, InstrumentAlias


class InstrumentResolverService:
    def normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = text.replace("ё", "е")
        text = re.sub(r"[^a-zA-Zа-яА-Я0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> list[str]:
        return self.normalize_text(text).split()

    def resolve(self, db: Session, text: str) -> dict:
        """
        Главный метод (использовать ВЕЗДЕ)
        """
        if not text:
            return {
                "tickers": [],
                "primary_ticker": None,
                "display_names": {}
            }

        normalized_text = self.normalize_text(text)
        tokens = self.tokenize(text)

        instruments = db.query(FinancialInstrument).all()

        ticker_map = {inst.ticker.upper(): inst for inst in instruments}

        found = []

        # 1. прямые тикеры
        for token in tokens:
            t = token.upper()
            if t in ticker_map and t not in found:
                found.append(t)

        # 2. алиасы
        aliases = db.query(InstrumentAlias).all()

        alias_pairs = [
            (self.normalize_text(a.alias), a.ticker.upper())
            for a in aliases
        ]

        alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)

        for alias_text, ticker in alias_pairs:
            if alias_text and alias_text in normalized_text:
                if ticker not in found:
                    found.append(ticker)

        # display names
        display_names = {}
        for ticker in found:
            inst = ticker_map.get(ticker)
            display_names[ticker] = (
                inst.name if inst and inst.name else ticker
            )

        return {
            "tickers": found,
            "primary_ticker": found[0] if found else None,
            "display_names": display_names
        }