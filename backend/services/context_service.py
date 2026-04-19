import re
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
from backend.services.dividend_service import DividendService
from backend.services.historical_market_service import HistoricalMarketService
from backend.services.fx_service import FXService
from backend.services.bond_service import BondService
from backend.services.dividend_calendar_db_service import DividendCalendarDBService


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
        self.dividend_service = DividendService()
        self.historical_market_service = HistoricalMarketService()
        self.fx_service = FXService()
        self.bond_service = BondService()
        self.dividend_calendar_db_service = DividendCalendarDBService()

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
            try:
                portfolio_refresh_result = self.portfolio_service.refresh_portfolio_market_data(db, user)
            except Exception:
                portfolio_refresh_result = None

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
                try:
                    pos_ctx = self.portfolio_service.build_position_context(db, user, ticker)
                except Exception:
                    pos_ctx = None

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

        requested_year = self._extract_year_from_text(user_text)
        requested_limit = self._extract_period_limit_from_text(user_text)

        last_dividend_context = None
        year_dividend_context = None
        expected_dividend_context = None
        expected_dividend_calendar_context = None
        historical_price_extremes_context = None
        max_turnover_context = None

        fx_context = None
        fx_price_context = None
        try:
            fx_context = self.fx_service.resolve_fx_from_text(user_text)
            if fx_context:
                fx_price_context = self.fx_service.get_fx_price(fx_context["code"])
        except Exception:
            fx_context = None
            fx_price_context = None

        bond_context = None
        bond_last_coupon_context = None
        bond_next_coupon_context = None
        bond_coupon_schedule_context = None

        try:
            bond_context = self.bond_service.resolve_bond_from_text(user_text)
            if bond_context:
                bond_code = bond_context["bond_code"]
                bond_last_coupon_context = self.bond_service.get_last_coupon(bond_code)
                bond_next_coupon_context = self.bond_service.get_next_coupon(bond_code)
                bond_coupon_schedule_context = self.bond_service.get_coupon_schedule(bond_code)
        except Exception:
            bond_context = None
            bond_last_coupon_context = None
            bond_next_coupon_context = None
            bond_coupon_schedule_context = None

        # Ключевые идентификаторы бумаги
        ticker_for_calendar = None
        display_name_for_calendar = None

        if market_context and market_context.get("ticker"):
            ticker_for_calendar = market_context.get("ticker")

        if market_context and market_context.get("display_name"):
            display_name_for_calendar = market_context.get("display_name")

        if not ticker_for_calendar and tickers:
            ticker_for_calendar = tickers[0]

        if not display_name_for_calendar and resolved_instrument and resolved_instrument.get("name"):
            display_name_for_calendar = resolved_instrument.get("name")

        # Рыночная / тех / обычная дивидендная аналитика — только если есть цена
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

            try:
                dividend_context = self.corporate_actions_service.get_dividend_context(
                    ticker=ticker,
                    current_price=current_price
                )
                dividend_text_summary = self.corporate_actions_service.build_dividend_text_summary(
                    dividend_context
                )
            except Exception:
                dividend_context = None
                dividend_text_summary = None

            try:
                buy_or_wait_context = self.recommendation_service.build_buy_or_wait_context(
                    market_context=market_context,
                    technical_analysis=technical_analysis_context,
                    dividend_context=dividend_context,
                    position_market_metrics=position_market_metrics
                )
            except Exception:
                buy_or_wait_context = None

            try:
                entry_point_context = self.recommendation_service.build_entry_point_context(
                    market_context=market_context,
                    technical_analysis=technical_analysis_context
                )
            except Exception:
                entry_point_context = None

            try:
                dividend_comment_context = self.recommendation_service.build_dividend_comment(
                    dividend_context=dividend_context
                )
            except Exception:
                dividend_comment_context = None

            try:
                last_dividend_context = self.dividend_service.get_last_dividend(ticker)
            except Exception:
                last_dividend_context = None

            try:
                if requested_year:
                    year_dividend_context = self.dividend_service.get_dividend_by_year(
                        ticker=ticker,
                        year=requested_year
                    )
                    expected_dividend_context = self.dividend_service.get_expected_dividend(
                        ticker=ticker,
                        year=requested_year
                    )
                else:
                    expected_dividend_context = self.dividend_service.get_expected_dividend(
                        ticker=ticker,
                        year=None
                    )
            except Exception:
                year_dividend_context = None
                expected_dividend_context = None

            try:
                historical_price_extremes_context = self.historical_market_service.get_price_extremes(
                    ticker=ticker,
                    interval="24",
                    limit=requested_limit
                )
            except Exception:
                historical_price_extremes_context = None

            try:
                max_turnover_context = self.historical_market_service.get_max_turnover_day(
                    ticker=ticker,
                    interval="24",
                    limit=requested_limit
                )
            except Exception:
                max_turnover_context = None

        # Критичный фикс: календарь 2026 ищем отдельно от price_found
        try:
            if requested_year == 2026:
                item = self.dividend_calendar_db_service.find_best_match(
                    db,
                    ticker=ticker_for_calendar,
                    display_name=display_name_for_calendar,
                    user_text=user_text,
                    year=2026,
                )
                expected_dividend_calendar_context = self.dividend_calendar_db_service.to_context_dict(item)
        except Exception:
            expected_dividend_calendar_context = None

        for market_item in multi_market_context:
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

            try:
                dividend_ctx = self.corporate_actions_service.get_dividend_context(
                    ticker=ticker,
                    current_price=current_price
                )
            except Exception:
                dividend_ctx = None

            related_position_metrics = None
            for pos_metrics in multi_position_market_metrics:
                if pos_metrics.get("ticker") == ticker:
                    related_position_metrics = pos_metrics
                    break

            try:
                entry_ctx = self.recommendation_service.build_entry_point_context(
                    market_context=market_item,
                    technical_analysis=ta_ctx
                )
            except Exception:
                entry_ctx = None

            try:
                buy_wait_ctx = self.recommendation_service.build_buy_or_wait_context(
                    market_context=market_item,
                    technical_analysis=ta_ctx,
                    dividend_context=dividend_ctx,
                    position_market_metrics=related_position_metrics
                )
            except Exception:
                buy_wait_ctx = None

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
            try:
                comparison_context = self.instrument_comparison_service.build_comparison(
                    multi_comparison_items
                )
            except Exception:
                comparison_context = None

        bond_ranking_context = None
        if "облигац" in user_text.lower():
            try:
                bond_ranking_context = self.bond_service.get_top_bonds_by_coupon(limit=10)
            except Exception:
                bond_ranking_context = None

        dividend_ranking_context = None
        lowered_text = user_text.lower().replace("ё", "е")
        if any(marker in lowered_text for marker in [
            "топ дивиденд",
            "дивидендные акции",
            "акции с наибольшими дивидендами",
            "самые дивидендные акции",
            "самая высокая дивидендная доходность",
            "компании платят наибольшие дивиденды",
            "лучшие дивидендные бумаги",
        ]):
            try:
                dividend_ranking_context = self.dividend_service.get_top_dividend_stocks(limit=10)
            except Exception:
                dividend_ranking_context = None

        dividend_aristocrats_context = None
        if any(marker in lowered_text for marker in [
            "дивидендные аристократы",
            "аристократ",
            "стабильно",
            "каждый год",
        ]):
            try:
                dividend_aristocrats_context = self.dividend_service.get_dividend_aristocrats()
            except Exception:
                dividend_aristocrats_context = None

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
            "comparison_context": comparison_context,
            "last_dividend_context": last_dividend_context,
            "year_dividend_context": year_dividend_context,
            "expected_dividend_context": expected_dividend_context,
            "expected_dividend_calendar_context": expected_dividend_calendar_context,
            "historical_price_extremes_context": historical_price_extremes_context,
            "max_turnover_context": max_turnover_context,
            "requested_year": requested_year,
            "requested_limit": requested_limit,
            "fx_context": fx_context,
            "fx_price_context": fx_price_context,
            "bond_context": bond_context,
            "bond_last_coupon_context": bond_last_coupon_context,
            "bond_next_coupon_context": bond_next_coupon_context,
            "bond_coupon_schedule_context": bond_coupon_schedule_context,
            "bond_ranking_context": bond_ranking_context,
            "dividend_ranking_context": dividend_ranking_context,
            "dividend_aristocrats_context": dividend_aristocrats_context,
        }

    def _extract_year_from_text(self, text: str) -> int | None:
        match = re.search(r"\b(20\d{2})\b", text)
        if not match:
            return None

        try:
            return int(match.group(1))
        except Exception:
            return None

    def _extract_period_limit_from_text(self, text: str) -> int:
        text = text.lower().replace("ё", "е")

        if "год назад" in text or "за год" in text:
            return 365
        if "за 6 месяцев" in text or "полгода" in text:
            return 180
        if "за 3 месяца" in text:
            return 90
        if "за месяц" in text:
            return 30

        return 365

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
            "минимальная цена",
            "максимальная цена",
            "оборот",
            "доллар",
            "евро",
            "юань",
            "валюта",
            "курс",
            "облигац",
            "купон",
        ]

        return any(marker in text for marker in refresh_markers)