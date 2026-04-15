from __future__ import annotations

from sqlalchemy.orm import Session
import requests

from backend.services.instrument_service import InstrumentService
from backend.services.market_service import MarketService


class QueryPreprocessorService:
    """
    Предобработка пользовательского запроса.

    Цели:
    1. Нормализовать текст.
    2. Попробовать распознать инструмент локально и безопасно.
    3. Не ронять чат, если внешний MOEX-поиск временно недоступен.
    """

    def __init__(self):
        self.instrument_service = InstrumentService()
        self.market_service = MarketService()

    def preprocess(
        self,
        db: Session,
        user,
        user_text: str
    ) -> dict:
        original_text = user_text or ""
        normalized_text = self._normalize_text(original_text)

        resolved_instrument = self._safe_resolve_instrument(
            db=db,
            text=normalized_text
        )

        return {
            "original_text": original_text,
            "normalized_text": normalized_text,
            "resolved_instrument": resolved_instrument
        }

    def _safe_resolve_instrument(
        self,
        db: Session,
        text: str
    ) -> dict | None:
        """
        Порядок:
        1. Сначала пробуем локально через текущую БД/резолвер market_service.
        2. Если не нашли — пробуем resolve_or_create_instrument.
        3. Любые сетевые ошибки MOEX гасим и возвращаем None, а не 500.
        """
        if not text:
            return None

        # 1. Локальное/мягкое распознавание
        try:
            local = self.market_service.instrument_resolver.resolve_instrument_from_text(db, text)
            if local:
                return self._normalize_resolved_instrument(local)
        except AttributeError:
            # Если у instrument_resolver нет такого метода, пробуем тикер+display name
            try:
                ticker = self.market_service.extract_ticker_from_text(db, text)
                if ticker:
                    display_name = self.market_service.instrument_resolver.get_instrument_display_name(db, ticker)
                    return {
                        "ticker": ticker.upper(),
                        "name": display_name or ticker.upper()
                    }
            except Exception:
                pass
        except Exception:
            pass

        # 2. Попытка через instrument_service, но безопасно
        try:
            instrument = self.instrument_service.resolve_or_create_instrument(db, text)
            if instrument:
                return {
                    "ticker": instrument.ticker,
                    "name": instrument.name,
                    "instrument_id": getattr(instrument, "id", None)
                }
        except requests.RequestException:
            return None
        except Exception:
            return None

        return None

    def _normalize_resolved_instrument(self, instrument) -> dict:
        """
        Приводим разные варианты результата к единому формату dict.
        """
        if isinstance(instrument, dict):
            ticker = instrument.get("ticker")
            name = instrument.get("name") or instrument.get("display_name")
            instrument_id = instrument.get("instrument_id") or instrument.get("id")

            return {
                "ticker": ticker.upper() if ticker else ticker,
                "name": name,
                "instrument_id": instrument_id
            }

        ticker = getattr(instrument, "ticker", None)
        name = getattr(instrument, "name", None)
        instrument_id = getattr(instrument, "id", None)

        return {
            "ticker": ticker.upper() if ticker else ticker,
            "name": name,
            "instrument_id": instrument_id
        }

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip()
        text = text.replace("ё", "е")
        text = " ".join(text.split())

        return text