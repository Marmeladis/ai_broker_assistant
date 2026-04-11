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
        normalized = self.normalize_text(text)
        return normalized.split()

    def resolve_ticker_from_text(self, db: Session, text: str) -> str | None:
        tickers = self.resolve_tickers_from_text(db, text)
        return tickers[0] if tickers else None

    def resolve_tickers_from_text(self, db: Session, text: str) -> list[str]:
        if not text:
            return []

        normalized_text = self.normalize_text(text)
        tokens = self.tokenize(text)

        instruments = db.query(FinancialInstrument).all()
        known_tickers = {inst.ticker.upper(): inst.ticker.upper() for inst in instruments}

        found = []

        #Прямые тикеры
        for token in tokens:
            token_upper = token.upper()
            if token_upper in known_tickers and token_upper not in found:
                found.append(token_upper)

        #Названия
        aliases = db.query(InstrumentAlias).all()
        alias_pairs = []
        for item in aliases:
            alias_pairs.append((self.normalize_text(item.alias), item.ticker.upper()))

        alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)

        for alias_text, ticker in alias_pairs:
            if alias_text and alias_text in normalized_text and ticker not in found:
                found.append(ticker)

        return found

    def get_instrument_display_name(self, db: Session, ticker: str) -> str:
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker.upper()
        ).first()

        if instrument and instrument.name:
            return instrument.name

        return ticker.upper()