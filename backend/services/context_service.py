from sqlalchemy.orm import Session

from backend.models import Chat, User
from backend.services.portfolio_service import PortfolioService
from backend.services.market_service import MarketService
from backend.services.news_service import NewsService
from backend.services.corporate_actions_service import CorporateActionsService
from backend.services.price_history_service import PriceHistoryService
from backend.services.technical_analysis_service import TechnicalAnalysisService
from backend.services.recommendation_service import RecommendationService
from backend.services.instrument_comparison_service import InstrumentComparisonService


class ContextService:
    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.market_service = MarketService()
        self.news_service = NewsService()
        self.corporate_actions_service = CorporateActionsService()
        self.price_history_service = PriceHistoryService()
        self.technical_analysis_service = TechnicalAnalysisService()
        self.recommendation_service = RecommendationService()
        self.instrument_comparison_service = InstrumentComparisonService()

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
            if message.role in {"user", "assistant"}:
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

        technical_analysis_context = None
        dividend_context = None
        dividend_text_summary = None
        buy_or_wait_context = None
        entry_point_context = None
        dividend_comment_context = None

        multi_technical_analysis_contexts = []
        multi_dividend_contexts = []
        multi_entry_point_contexts = []
        multi_buy_or_wait_contexts = []
        multi_comparison_items = []
        comparison_context = None

        # Одиночный контекст
        if market_context and market_context.get("ticker") and market_context.get("price_found"):
            ticker = market_context["ticker"]
            current_price = market_context.get("price")

            try:
                candles = self.price_history_service.get_candles(
                    ticker=ticker,
                    interval="24",
                    limit=60
                )
                if candles:
                    technical_analysis_context = self.technical_analysis_service.analyze(candles)
            except Exception:
                technical_analysis_context = None

            dividend_context = self.corporate_actions_service.get_dividend_context(
                ticker=ticker,
                current_price=current_price
            )
            dividend_text_summary = self.corporate_actions_service.build_dividend_text_summary(
                dividend_context
            )

            buy_or_wait_context = self.recommendation_service.build_buy_or_wait_context(
                market_context=market_context,
                technical_analysis=technical_analysis_context,
                dividend_context=dividend_context,
                position_market_metrics=position_market_metrics
            )

            entry_point_context = self.recommendation_service.build_entry_point_context(
                market_context=market_context,
                technical_analysis=technical_analysis_context
            )

            dividend_comment_context = self.recommendation_service.build_dividend_comment(
                dividend_context=dividend_context
            )

        # Множественный контекст для сравнений
        for idx, market_item in enumerate(multi_market_context):
            if not market_item.get("price_found"):
                continue

            ticker = market_item.get("ticker")
            current_price = market_item.get("price")

            ta_ctx = None
            try:
                candles = self.price_history_service.get_candles(
                    ticker=ticker,
                    interval="24",
                    limit=60
                )
                if candles:
                    ta_ctx = self.technical_analysis_service.analyze(candles)
            except Exception:
                ta_ctx = None

            dividend_ctx = self.corporate_actions_service.get_dividend_context(
                ticker=ticker,
                current_price=current_price
            )

            related_position_metrics = None
            for pos_metrics in multi_position_market_metrics:
                if pos_metrics.get("ticker") == ticker:
                    related_position_metrics = pos_metrics
                    break

            entry_ctx = self.recommendation_service.build_entry_point_context(
                market_context=market_item,
                technical_analysis=ta_ctx
            )

            buy_wait_ctx = self.recommendation_service.build_buy_or_wait_context(
                market_context=market_item,
                technical_analysis=ta_ctx,
                dividend_context=dividend_ctx,
                position_market_metrics=related_position_metrics
            )

            multi_technical_analysis_contexts.append({
                "ticker": ticker,
                "display_name": market_item.get("display_name"),
                "analysis": ta_ctx
            })

            multi_dividend_contexts.append({
                "ticker": ticker,
                "display_name": market_item.get("display_name"),
                "dividend": dividend_ctx
            })

            multi_entry_point_contexts.append({
                "ticker": ticker,
                "display_name": market_item.get("display_name"),
                "entry_point": entry_ctx
            })

            multi_buy_or_wait_contexts.append({
                "ticker": ticker,
                "display_name": market_item.get("display_name"),
                "buy_or_wait": buy_wait_ctx
            })

            multi_comparison_items.append({
                "ticker": ticker,
                "display_name": market_item.get("display_name"),
                "market_context": market_item,
                "technical_analysis_context": ta_ctx,
                "dividend_context": dividend_ctx,
                "position_market_metrics": related_position_metrics,
                "entry_point_context": entry_ctx,
                "buy_or_wait_context": buy_wait_ctx,
            })

        if len(multi_comparison_items) >= 2:
            comparison_context = self.instrument_comparison_service.build_comparison(
                multi_comparison_items
            )

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
            "multi_position_market_metrics": multi_position_market_metrics,
            "technical_analysis_context": technical_analysis_context,
            "dividend_context": dividend_context,
            "dividend_text_summary": dividend_text_summary,
            "buy_or_wait_context": buy_or_wait_context,
            "entry_point_context": entry_point_context,
            "dividend_comment_context": dividend_comment_context,
            "multi_technical_analysis_contexts": multi_technical_analysis_contexts,
            "multi_dividend_contexts": multi_dividend_contexts,
            "multi_entry_point_contexts": multi_entry_point_contexts,
            "multi_buy_or_wait_contexts": multi_buy_or_wait_contexts,
            "comparison_context": comparison_context
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
            "стоит ли покупать",
            "покупать или подождать",
            "точка входа",
            "дивиденд",
            "что лучше",
        ]

        return any(marker in text for marker in refresh_markers)