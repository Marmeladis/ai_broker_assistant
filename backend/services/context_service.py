from sqlalchemy.orm import Session

from backend.models import Chat, User
from backend.services.portfolio_service import PortfolioService
from backend.services.market_service import MarketService
from backend.services.news_service import NewsService


class ContextService:
    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.market_service = MarketService()
        self.news_service = NewsService()

    def build_context(
        self,
        db: Session,
        user: User,
        chat: Chat,
        user_text: str,
        history_limit: int = 10,
        resolved_instrument: dict | None = None
    ) -> dict:
        messages = chat.messages[-history_limit:] if chat.messages else []

        chat_history = []
        for message in messages:
            chat_history.append({
                "role": message.role,
                "content": message.content
            })

        should_refresh_portfolio = self._should_refresh_portfolio_prices(user_text)

        portfolio_refresh_result = None
        if should_refresh_portfolio:
            portfolio_refresh_result = self.portfolio_service.refresh_portfolio_market_data(db, user)

        portfolio_summary = self.portfolio_service.build_portfolio_summary(db, user)
        portfolio_metrics = self.portfolio_service.build_portfolio_metrics(db, user)
        portfolio_text_summary = self.portfolio_service.build_portfolio_text_summary(portfolio_metrics)

        market_context = self.market_service.build_market_context(
            db=db,
            user_text=user_text,
            resolved_instrument=resolved_instrument
        )
        multi_market_context = self.market_service.build_multi_market_context(
            db=db,
            user_text=user_text,
            resolved_instrument=resolved_instrument
        )

        news_context = self.news_service.build_news_context(
            db=db,
            user_text=user_text,
            resolved_instrument=resolved_instrument
        )
        multi_news_context = self.news_service.build_multi_news_context(
            db=db,
            user_text=user_text,
            resolved_instrument=resolved_instrument
        )

        tickers = self.market_service.extract_tickers_from_text(
            db=db,
            text=user_text,
            resolved_instrument=resolved_instrument
        )

        position_context = None
        position_market_metrics = None
        multi_position_contexts = []
        multi_position_market_metrics = []

        if tickers:
            for idx, ticker in enumerate(tickers):
                pos_ctx = self.portfolio_service.build_position_context(db, user, ticker)
                if pos_ctx:
                    multi_position_contexts.append(pos_ctx)

                    related_market = None
                    if idx < len(multi_market_context):
                        related_market = multi_market_context[idx]

                    metrics = self.market_service.build_position_market_metrics(
                        position_context=pos_ctx,
                        market_context=related_market
                    )
                    if metrics:
                        multi_position_market_metrics.append(metrics)

            if multi_position_contexts:
                position_context = multi_position_contexts[0]

            if multi_position_market_metrics:
                position_market_metrics = multi_position_market_metrics[0]

        return {
            "chat": {
                "id": chat.id,
                "title": chat.title
            },
            "chat_history": chat_history,
            "resolved_instrument": resolved_instrument,
            "portfolio": portfolio_summary,
            "portfolio_metrics": portfolio_metrics,
            "portfolio_text_summary": portfolio_text_summary,
            "portfolio_refresh_result": portfolio_refresh_result,
            "market_context": market_context,
            "multi_market_context": multi_market_context,
            "news_context": news_context,
            "multi_news_context": multi_news_context,
            "position_context": position_context,
            "position_market_metrics": position_market_metrics,
            "multi_position_contexts": multi_position_contexts,
            "multi_position_market_metrics": multi_position_market_metrics
        }

    def _should_refresh_portfolio_prices(self, user_text: str) -> bool:
        text = user_text.lower().replace("ё", "е")

        refresh_markers = [
            "портфел",
            "позиц",
            "мой результат",
            "общий результат",
            "в плюсе",
            "в минусе",
            "риск",
            "доходност",
            "сравни",
            "анализ",
            "проанализиру",
        ]

        return any(marker in text for marker in refresh_markers)