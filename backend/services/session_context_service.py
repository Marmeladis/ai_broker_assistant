import json
from sqlalchemy.orm import Session

from backend.models import ChatSessionState


class SessionContextService:
    def get_or_create_state(self, db: Session, chat_id: int) -> ChatSessionState:
        state = (
            db.query(ChatSessionState)
            .filter(ChatSessionState.chat_id == chat_id)
            .first()
        )
        if state:
            return state

        state = ChatSessionState(
            chat_id=chat_id,
            last_ticker=None,
            recent_tickers_json=json.dumps([]),
            last_intent=None,
            last_resolved_instrument_json=None,
        )
        db.add(state)
        db.commit()
        db.refresh(state)
        return state

    def get_context(self, db: Session, chat_id: int) -> dict:
        state = self.get_or_create_state(db, chat_id)

        recent_tickers = []
        if state.recent_tickers_json:
            try:
                recent_tickers = json.loads(state.recent_tickers_json)
            except Exception:
                recent_tickers = []

        last_resolved_instrument = None
        if state.last_resolved_instrument_json:
            try:
                last_resolved_instrument = json.loads(state.last_resolved_instrument_json)
            except Exception:
                last_resolved_instrument = None

        return {
            "last_ticker": state.last_ticker,
            "recent_tickers": recent_tickers,
            "last_intent": state.last_intent,
            "last_resolved_instrument": last_resolved_instrument,
        }

    def update_context(
        self,
        db: Session,
        chat_id: int,
        resolved_instrument: dict | None,
        intent: str | None
    ) -> dict:
        state = self.get_or_create_state(db, chat_id)
        current = self.get_context(db, chat_id)

        last_ticker = current.get("last_ticker")
        recent_tickers = current.get("recent_tickers", [])
        last_resolved_instrument = current.get("last_resolved_instrument")

        if resolved_instrument and resolved_instrument.get("ticker"):
            ticker = resolved_instrument["ticker"].upper()

            last_ticker = ticker
            last_resolved_instrument = resolved_instrument

            if ticker in recent_tickers:
                recent_tickers.remove(ticker)

            recent_tickers.insert(0, ticker)
            recent_tickers = recent_tickers[:5]

        state.last_ticker = last_ticker
        state.recent_tickers_json = json.dumps(recent_tickers, ensure_ascii=False)
        state.last_intent = intent or state.last_intent
        state.last_resolved_instrument_json = (
            json.dumps(last_resolved_instrument, ensure_ascii=False)
            if last_resolved_instrument
            else state.last_resolved_instrument_json
        )

        db.commit()
        db.refresh(state)

        return self.get_context(db, chat_id)

    def clear_context(self, db: Session, chat_id: int):
        state = (
            db.query(ChatSessionState)
            .filter(ChatSessionState.chat_id == chat_id)
            .first()
        )
        if not state:
            return

        state.last_ticker = None
        state.recent_tickers_json = json.dumps([])
        state.last_intent = None
        state.last_resolved_instrument_json = None

        db.commit()

    def enrich_user_text(
        self,
        db: Session,
        chat_id: int,
        user_text: str
    ) -> dict:

        user_text = (user_text or "").strip()
        session_context = self.get_context(db, chat_id)

        last_ticker = session_context.get("last_ticker")
        last_resolved_instrument = session_context.get("last_resolved_instrument")

        if not user_text:
            return {
                "original_text": user_text,
                "enriched_text": user_text,
                "used_session_context": False,
                "session_context": session_context
            }

        if not last_ticker:
            return {
                "original_text": user_text,
                "enriched_text": user_text,
                "used_session_context": False,
                "session_context": session_context
            }

        if not self._looks_like_followup(user_text):
            return {
                "original_text": user_text,
                "enriched_text": user_text,
                "used_session_context": False,
                "session_context": session_context
            }

        instrument_name = last_ticker
        if last_resolved_instrument:
            instrument_name = last_resolved_instrument.get("name") or last_ticker

        enriched_text = (
            f"{user_text} "
            f"[session_instrument: {instrument_name}, ticker: {last_ticker}]"
        )

        return {
            "original_text": user_text,
            "enriched_text": enriched_text,
            "used_session_context": True,
            "session_context": session_context
        }

    def _looks_like_followup(self, text: str) -> bool:
        text_lower = text.lower().replace("ё", "е").strip()

        followup_markers = [
            "а по нему",
            "а по ней",
            "по нему",
            "по ней",
            "по этой бумаге",
            "по этой акции",
            "по бумаге",
            "по акции",
            "а когда по нему",
            "а когда по ней",
            "а дивиденды",
            "а цена",
            "а если сравнить",
            "сравни с",
            "а сейчас",
            "а вход",
            "а стоит ли",
            "а покупать",
            "а подождать",
            "а какая точка входа",
            "а что с позицией",
            "моя позиция по нему",
            "моя позиция по ней",
            "что с ним",
            "что с ней",
            "а новости",
            "а тренд",
            "а сигнал",
        ]

        short_followups = {
            "а по нему?",
            "а по ней?",
            "по нему?",
            "по ней?",
            "а сейчас?",
            "а дивиденды?",
            "а цена?",
            "а вход?",
            "а сигнал?",
            "а тренд?",
        }

        if text_lower in short_followups:
            return True

        return any(marker in text_lower for marker in followup_markers)