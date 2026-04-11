from sqlalchemy.orm import Session

from backend.models import User
from backend.services.instrument_service import InstrumentService


class QueryPreprocessorService:
    def __init__(self):
        self.instrument_service = InstrumentService()

    def preprocess(self, db: Session, user: User, user_text: str) -> dict:
        original_text = (user_text or "").strip()
        if not original_text:
            return {
                "original_text": user_text,
                "normalized_text": user_text,
                "resolved_instrument": None
            }

        instrument = self.instrument_service.resolve_or_create_instrument(db, original_text)

        if not instrument:
            return {
                "original_text": original_text,
                "normalized_text": original_text,
                "resolved_instrument": None
            }

        ticker = instrument.ticker.upper()
        name = instrument.name or ticker

        normalized_text = self._inject_instrument_hint(
            text=original_text,
            ticker=ticker,
            name=name
        )

        return {
            "original_text": original_text,
            "normalized_text": normalized_text,
            "resolved_instrument": {
                "ticker": ticker,
                "name": name,
                "type": instrument.type,
                "currency": instrument.currency
            }
        }

    def _inject_instrument_hint(self, text: str, ticker: str, name: str) -> str:

        text = text.strip()

        upper_text = text.upper()
        if ticker in upper_text:
            return text

        return f"{text} [instrument: {name}, ticker: {ticker}]"