from backend.services.price_history_service import PriceHistoryService
from backend.services.technical_analysis_service import TechnicalAnalysisService


class AnalyticsService:
    def __init__(self):
        self.price_history_service = PriceHistoryService()
        self.ta_service = TechnicalAnalysisService()

    def run(self, user_text: str, intent: str, context: dict) -> dict | None:
        portfolio = context.get("portfolio", [])
        portfolio_metrics = context.get("portfolio_metrics", {})
        market_context = context.get("market_context")
        multi_market_context = context.get("multi_market_context", [])
        news_context = context.get("news_context")
        multi_news_context = context.get("multi_news_context", [])
        position_market_metrics = context.get("position_market_metrics")
        multi_position_market_metrics = context.get("multi_position_market_metrics", [])

        if intent == "technical_analysis":
            ticker = (
                context.get("market_context", {}).get("ticker")
                or (context.get("multi_market_context") or [{}])[0].get("ticker")
            )

            if not ticker:
                return {
                    "report_type": "technical_analysis",
                    "trend_summary": "тикер не определён",
                    "calculated_indicators": {},
                    "confidence_score": 0.2
                }

            try:
                candles = self.price_history_service.get_candles(
                    ticker=ticker,
                    interval="24",
                    limit=60
                )
                analysis = self.ta_service.analyze(candles)

                signal = analysis.get("signal")
                trend = analysis.get("trend")

                return {
                    "report_type": "technical_analysis",
                    "trend_summary": f"обнаружен тренд: {trend}, сигнал: {signal}",
                    "calculated_indicators": analysis,
                    "confidence_score": 0.78
                }
            except Exception as e:
                return {
                    "report_type": "technical_analysis",
                    "trend_summary": f"не удалось выполнить технический анализ: {str(e)}",
                    "calculated_indicators": {},
                    "confidence_score": 0.2
                }

        if intent == "portfolio_analysis":
            if not portfolio:
                return {
                    "report_type": "portfolio_analysis",
                    "trend_summary": "портфель пользователя пуст",
                    "calculated_indicators": {
                        "positions_count": 0,
                        "tickers": []
                    },
                    "confidence_score": 0.95
                }

            return {
                "report_type": "portfolio_analysis",
                "trend_summary": "сформирован агрегированный обзор портфеля",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "total_invested_value": portfolio_metrics.get("total_invested_value"),
                    "total_market_value": portfolio_metrics.get("total_market_value"),
                    "total_absolute_pnl": portfolio_metrics.get("total_absolute_pnl"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent"),
                    "profitable_positions": portfolio_metrics.get("profitable_positions"),
                    "losing_positions": portfolio_metrics.get("losing_positions")
                },
                "confidence_score": 0.9
            }

        if intent == "price_check":
            if market_context and market_context.get("price_found"):
                result = {
                    "ticker": market_context.get("ticker"),
                    "display_name": market_context.get("display_name"),
                    "price": market_context.get("price"),
                    "source_name": market_context.get("source_name"),
                    "recorded_at": market_context.get("recorded_at")
                }

                if position_market_metrics:
                    result["position_metrics"] = position_market_metrics

                return {
                    "report_type": "price_check",
                    "trend_summary": "в рыночном контексте найдена актуальная цена инструмента",
                    "calculated_indicators": result,
                    "confidence_score": 0.98
                }

            return {
                "report_type": "price_check",
                "trend_summary": "цена инструмента не найдена",
                "calculated_indicators": {},
                "confidence_score": 0.25
            }

        if intent == "multi_price_compare":
            return {
                "report_type": "multi_price_compare",
                "trend_summary": "подготовлено сравнение цен по нескольким инструментам",
                "calculated_indicators": {
                    "items": multi_market_context,
                    "position_metrics": multi_position_market_metrics
                },
                "confidence_score": 0.97
            }

        if intent == "news_explain":
            if news_context and news_context.get("news_found"):
                return {
                    "report_type": "news_explain",
                    "trend_summary": "найден новостной контекст для объяснения",
                    "calculated_indicators": {
                        "ticker": news_context.get("ticker"),
                        "display_name": news_context.get("display_name"),
                        "news_count": len(news_context.get("items", [])),
                        "has_position": position_market_metrics is not None
                    },
                    "confidence_score": 0.91
                }

            return {
                "report_type": "news_explain",
                "trend_summary": "новостной контекст не найден",
                "calculated_indicators": {},
                "confidence_score": 0.20
            }

        if intent == "multi_news_compare":
            return {
                "report_type": "multi_news_compare",
                "trend_summary": "подготовлен обзор новостного фона по нескольким инструментам",
                "calculated_indicators": {
                    "items": multi_news_context
                },
                "confidence_score": 0.89
            }

        if intent == "multi_position_compare":
            return {
                "report_type": "multi_position_compare",
                "trend_summary": "подготовлено сравнение результата по нескольким позициям пользователя",
                "calculated_indicators": {
                    "items": multi_position_market_metrics
                },
                "confidence_score": 0.86
            }

        if intent == "multi_instrument_compare":
            return {
                "report_type": "multi_instrument_compare",
                "trend_summary": "подготовлено общее сравнение нескольких инструментов по доступному контексту",
                "calculated_indicators": {
                    "market_items": multi_market_context,
                    "news_items": multi_news_context,
                    "position_items": multi_position_market_metrics
                },
                "confidence_score": 0.83
            }

        if intent == "benchmark_compare":
            return {
                "report_type": "benchmark_compare",
                "trend_summary": "доступно базовое сравнение портфеля с бенчмарком на уровне агрегатов",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent")
                },
                "confidence_score": 0.63
            }

        if intent == "risk_return":
            return {
                "report_type": "risk_return",
                "trend_summary": "доступна предварительная оценка результата портфеля и структуры позиций",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "profitable_positions": portfolio_metrics.get("profitable_positions"),
                    "losing_positions": portfolio_metrics.get("losing_positions"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent")
                },
                "confidence_score": 0.72
            }

        if intent == "scenario_forecast":
            return {
                "report_type": "scenario_forecast",
                "trend_summary": "можно сформировать базовый сценарный комментарий на основе рынка, новостей и портфеля",
                "calculated_indicators": {
                    "has_market_context": bool(market_context or multi_market_context),
                    "has_news_context": bool(news_context or multi_news_context),
                    "has_portfolio": bool(portfolio),
                    "has_position_metrics": bool(position_market_metrics or multi_position_market_metrics)
                },
                "confidence_score": 0.56
            }

        if intent == "simple_analysis":
            return {
                "report_type": "simple_analysis",
                "trend_summary": "доступен общий аналитический комментарий по инструменту или портфелю",
                "calculated_indicators": {
                    "has_portfolio": bool(portfolio),
                    "has_market_context": bool(market_context or multi_market_context),
                    "has_news_context": bool(news_context or multi_news_context),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent")
                },
                "confidence_score": 0.73
            }

        return None