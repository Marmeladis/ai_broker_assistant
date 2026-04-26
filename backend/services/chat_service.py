import re
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models import Chat, Message, User
from backend.services.intent_service import IntentService
from backend.services.context_service import ContextService
from backend.services.llm_service import LLMService
from backend.services.analytics_service import AnalyticsService
from backend.services.request_history_service import RequestHistoryService
from backend.services.analytical_report_service import AnalyticalReportService
from backend.services.response_builder_service import ResponseBuilderService
from backend.services.comparative_response_service import ComparativeResponseService
from backend.services.smart_answer_service import SmartAnswerService
from backend.services.query_preprocessor_service import QueryPreprocessorService
from backend.services.session_context_service import SessionContextService


class ChatService:
    _RU_MONTHS = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    }
    _ISO_DATE_RE = re.compile(
        r"\b(\d{4})-(\d{2})-(\d{2})(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?\b"
    )
    _TECHNICAL_META_RE = re.compile(
        r"(?:^|(?<=[.!?])\s+)[^.!?]*(?:"
        r"Источник|источник|Источник данных|source_name|"
        r"Объ[её]м|объ[её]м|volume|"
        r"Время обновления|время обновления|recorded_at|last_update_time"
        r")[^.!?]*[.!?]?",
        re.IGNORECASE,
    )

    @classmethod
    def _format_date(cls, value: Any) -> str | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            parsed = value.date()
        elif isinstance(value, date):
            parsed = value
        else:
            text = str(value).strip()
            if not text:
                return None

            match = cls._ISO_DATE_RE.search(text)
            if not match:
                return text

            year, month, day = map(int, match.groups())
            try:
                parsed = date(year, month, day)
            except ValueError:
                return text

        return f"{parsed.day} {cls._RU_MONTHS[parsed.month]} {parsed.year} года"

    @classmethod
    def _clean_user_answer(cls, text: str | None) -> str:
        if not text:
            return ""

        cleaned = cls._TECHNICAL_META_RE.sub("", text)
        cleaned = cls._ISO_DATE_RE.sub(
            lambda match: cls._format_date(match.group(0)) or match.group(0),
            cleaned,
        )
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([.!?,:;])", r"\1", cleaned)
        return cleaned.strip()

    def __init__(self):
        self.intent_service = IntentService()
        self.context_service = ContextService()
        self.llm_service = LLMService()
        self.analytics_service = AnalyticsService()
        self.request_history_service = RequestHistoryService()
        self.analytical_report_service = AnalyticalReportService()
        self.response_builder_service = ResponseBuilderService()
        self.comparative_response_service = ComparativeResponseService()
        self.smart_answer_service = SmartAnswerService()
        self.query_preprocessor_service = QueryPreprocessorService()
        self.session_context_service = SessionContextService()

    def get_user_chat(self, db: Session, user_id: int) -> Chat | None:
        return db.query(Chat).filter(Chat.user_id == user_id).first()

    def get_chat_with_messages(self, db: Session, user_id: int) -> Chat | None:
        return db.query(Chat).filter(Chat.user_id == user_id).first()

    def save_message(self, db: Session, chat_id: int, role: str, content: str) -> Message:
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def process_user_message(self, db: Session, user: User, user_text: str) -> dict:
        chat = self.get_user_chat(db, user.id)
        if not chat:
            raise ValueError("Чат пользователя не найден")

        user_message = self.save_message(
            db=db,
            chat_id=chat.id,
            role="user",
            content=user_text
        )

        db.refresh(chat)

        session_enrichment = self.session_context_service.enrich_user_text(
            db=db,
            chat_id=chat.id,
            user_text=user_text
        )
        enriched_text = session_enrichment["enriched_text"]

        preprocess_result = self.query_preprocessor_service.preprocess(
            db=db,
            user=user,
            user_text=enriched_text
        )

        normalized_text = preprocess_result["normalized_text"]
        resolved_instrument = preprocess_result["resolved_instrument"]

        if not resolved_instrument:
            session_context = session_enrichment.get("session_context", {})
            session_instrument = session_context.get("last_resolved_instrument")
            if session_enrichment.get("used_session_context") and session_instrument:
                resolved_instrument = session_instrument

        # ВАЖНО: здесь нужен именно список тикеров
        resolved_tickers = self.context_service.market_service.extract_tickers_from_text(
            db=db,
            text=normalized_text,
            resolved_instrument=resolved_instrument
        )

        session_context = self.session_context_service.get_context(db, chat.id)
        last_ticker = session_context.get("last_ticker")

        if "сравни" in normalized_text.lower() and last_ticker:
            if last_ticker not in resolved_tickers:
                resolved_tickers = [last_ticker] + resolved_tickers

        intent = self.intent_service.detect_intent(
            text=normalized_text,
            resolved_tickers=resolved_tickers
        )

        context = self.context_service.build_context(
            db=db,
            user=user,
            chat=chat,
            user_text=normalized_text,
            resolved_instrument=resolved_instrument
        )

        context["session_context"] = session_context
        context["used_session_context"] = session_enrichment.get("used_session_context", False)

        analytics_result = self.analytics_service.run(
            intent=intent,
            context=context
        )

        comparative_summary = self.comparative_response_service.build_comparative_summary(
            intent=intent,
            analytics_result=analytics_result
        )

        fact_summary = self.response_builder_service.build_fact_summary(
            intent=intent,
            context=context,
            analytics_result=analytics_result,
            comparative_summary=comparative_summary
        )

        smart_answer = self.smart_answer_service.build_answer(
            user_text=normalized_text,
            intent=intent,
            context=context,
            analytics_result=analytics_result,
            comparative_summary=comparative_summary
        )

        if smart_answer:
            assistant_text = smart_answer
        else:
            llm_messages = self.llm_service.build_messages(
                user_text=normalized_text,
                context=context,
                intent=intent,
                analytics_result=analytics_result,
                fact_summary=fact_summary
            )

            assistant_text = self.llm_service.generate(
                messages=llm_messages,
                intent=intent,
                analytics_result=analytics_result
            )

        assistant_text = self._clean_user_answer(assistant_text)

        assistant_message = self.save_message(
            db=db,
            chat_id=chat.id,
            role="assistant",
            content=assistant_text
        )

        history_entry = self.request_history_service.log_request(
            db=db,
            user=user,
            message_id=user_message.id,
            user_query=user_text,
            system_response=assistant_text,
            intent_type=intent
        )

        analytical_report = self.analytical_report_service.save_report(
            db=db,
            user=user,
            message_id=user_message.id,
            intent_type=intent,
            analytics_result=analytics_result
        )

        updated_session_context = self.session_context_service.update_context(
            db=db,
            chat_id=chat.id,
            resolved_instrument=resolved_instrument,
            intent=intent
        )

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "intent": intent,
            "resolved_instrument": resolved_instrument,
            "analytics": analytics_result,
            "comparative_summary": comparative_summary,
            "fact_summary": fact_summary,
            "history_id": history_entry.id if history_entry else None,
            "analytical_report_id": analytical_report.id if analytical_report else None,
            "session_context": updated_session_context,
            "used_session_context": session_enrichment.get("used_session_context", False)
        }