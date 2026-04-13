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

        technical_analysis_context = context.get("technical_analysis_context")
        dividend_context = context.get("dividend_context")
        buy_or_wait_context = context.get("buy_or_wait_context")
        entry_point_context = context.get("entry_point_context")
        dividend_comment_context = context.get("dividend_comment_context")

        last_dividend_context = context.get("last_dividend_context")
        year_dividend_context = context.get("year_dividend_context")
        expected_dividend_context = context.get("expected_dividend_context")
        historical_price_extremes_context = context.get("historical_price_extremes_context")
        max_turnover_context = context.get("max_turnover_context")
        requested_year = context.get("requested_year")
        requested_limit = context.get("requested_limit")

        fx_price_context = context.get("fx_price_context")
        bond_last_coupon_context = context.get("bond_last_coupon_context")
        bond_next_coupon_context = context.get("bond_next_coupon_context")
        bond_coupon_schedule_context = context.get("bond_coupon_schedule_context")
        dividend_ranking_context = context.get("dividend_ranking_context")

        if intent == "dividend_ranking_query":
            if dividend_ranking_context:
                return {
                    "report_type": "dividend_ranking_query",
                    "trend_summary": "сформирован рейтинг акций по дивидендной доходности",
                    "calculated_indicators": {
                        "items": dividend_ranking_context
                    },
                    "confidence_score": 0.9
                }

            return {
                "report_type": "dividend_ranking_query",
                "trend_summary": "не удалось получить рейтинг дивидендных акций",
                "calculated_indicators": {},
                "confidence_score": 0.25
            }

        if intent == "bond_coupon_query":
            if bond_last_coupon_context or bond_next_coupon_context or bond_coupon_schedule_context:
                return {
                    "report_type": "bond_coupon_query",
                    "trend_summary": "найдены данные по купонам облигации",
                    "calculated_indicators": {
                        "last_coupon": bond_last_coupon_context,
                        "next_coupon": bond_next_coupon_context,
                        "coupon_schedule": bond_coupon_schedule_context[:10] if bond_coupon_schedule_context else [],
                    },
                    "confidence_score": 0.93
                }

            return {
                "report_type": "bond_coupon_query",
                "trend_summary": "данные по купонам облигации не найдены",
                "calculated_indicators": {},
                "confidence_score": 0.24
            }

        if intent == "fx_price_query":
            if fx_price_context and fx_price_context.get("price") is not None:
                return {
                    "report_type": "fx_price_query",
                    "trend_summary": "найдена актуальная цена валютной пары",
                    "calculated_indicators": fx_price_context,
                    "confidence_score": 0.97
                }

            return {
                "report_type": "fx_price_query",
                "trend_summary": "цена валютной пары не найдена",
                "calculated_indicators": {},
                "confidence_score": 0.22
            }

        if intent == "technical_analysis":
            ticker = (
                (market_context or {}).get("ticker")
                or (context.get("multi_market_context") or [{}])[0].get("ticker")
            )

            if not ticker:
                return {
                    "report_type": "technical_analysis",
                    "trend_summary": "тикер не определён",
                    "calculated_indicators": {},
                    "confidence_score": 0.2
                }

            if technical_analysis_context:
                trend = technical_analysis_context.get("trend")
                signal = technical_analysis_context.get("signal")

                return {
                    "report_type": "technical_analysis",
                    "trend_summary": f"обнаружен тренд: {trend}, сигнал: {signal}",
                    "calculated_indicators": technical_analysis_context,
                    "confidence_score": 0.82
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

        if intent == "historical_dividend_query":
            if requested_year and year_dividend_context:
                return {
                    "report_type": "historical_dividend_query",
                    "trend_summary": f"найден дивиденд по бумаге за {requested_year} год",
                    "calculated_indicators": {
                        "ticker": year_dividend_context.get("ticker"),
                        "year": requested_year,
                        "dividend_found": True,
                        "dividend_per_share": year_dividend_context.get("dividend_per_share"),
                        "record_date": year_dividend_context.get("record_date"),
                        "declared_date": year_dividend_context.get("declared_date"),
                        "currency": year_dividend_context.get("currency"),
                        "source_name": year_dividend_context.get("source_name"),
                    },
                    "confidence_score": 0.9
                }

            if last_dividend_context:
                return {
                    "report_type": "historical_dividend_query",
                    "trend_summary": "найден последний известный дивиденд по бумаге",
                    "calculated_indicators": {
                        "ticker": last_dividend_context.get("ticker"),
                        "year": last_dividend_context.get("year"),
                        "dividend_found": True,
                        "dividend_per_share": last_dividend_context.get("dividend_per_share"),
                        "record_date": last_dividend_context.get("record_date"),
                        "declared_date": last_dividend_context.get("declared_date"),
                        "currency": last_dividend_context.get("currency"),
                        "source_name": last_dividend_context.get("source_name"),
                    },
                    "confidence_score": 0.86
                }

            return {
                "report_type": "historical_dividend_query",
                "trend_summary": "исторические дивиденды по бумаге не найдены",
                "calculated_indicators": {
                    "ticker": (market_context or {}).get("ticker"),
                    "year": requested_year,
                    "dividend_found": False
                },
                "confidence_score": 0.25
            }

        if intent == "expected_dividend_query":
            if expected_dividend_context:
                return {
                    "report_type": "expected_dividend_query",
                    "trend_summary": "найден наиболее релевантный дивидендный ориентир по бумаге",
                    "calculated_indicators": {
                        "ticker": expected_dividend_context.get("ticker"),
                        "year": expected_dividend_context.get("year"),
                        "dividend_found": True,
                        "dividend_per_share": expected_dividend_context.get("dividend_per_share"),
                        "record_date": expected_dividend_context.get("record_date"),
                        "declared_date": expected_dividend_context.get("declared_date"),
                        "currency": expected_dividend_context.get("currency"),
                        "source_name": expected_dividend_context.get("source_name"),
                        "is_expected_proxy": True,
                    },
                    "confidence_score": 0.74
                }

            return {
                "report_type": "expected_dividend_query",
                "trend_summary": "ожидаемый дивиденд по бумаге не найден",
                "calculated_indicators": {
                    "ticker": (market_context or {}).get("ticker"),
                    "year": requested_year,
                    "dividend_found": False,
                    "is_expected_proxy": True,
                },
                "confidence_score": 0.22
            }

        if intent == "dividend_record_date_query":
            if year_dividend_context and year_dividend_context.get("record_date"):
                return {
                    "report_type": "dividend_record_date_query",
                    "trend_summary": "найдена дата отсечки по дивидендам за указанный год",
                    "calculated_indicators": {
                        "ticker": year_dividend_context.get("ticker"),
                        "year": requested_year,
                        "dividend_found": True,
                        "record_date": year_dividend_context.get("record_date"),
                        "dividend_per_share": year_dividend_context.get("dividend_per_share"),
                        "currency": year_dividend_context.get("currency"),
                    },
                    "confidence_score": 0.92
                }

            if last_dividend_context and last_dividend_context.get("record_date"):
                return {
                    "report_type": "dividend_record_date_query",
                    "trend_summary": "найдена последняя известная дата отсечки по дивидендам",
                    "calculated_indicators": {
                        "ticker": last_dividend_context.get("ticker"),
                        "year": last_dividend_context.get("year"),
                        "dividend_found": True,
                        "record_date": last_dividend_context.get("record_date"),
                        "dividend_per_share": last_dividend_context.get("dividend_per_share"),
                        "currency": last_dividend_context.get("currency"),
                    },
                    "confidence_score": 0.9
                }

            return {
                "report_type": "dividend_record_date_query",
                "trend_summary": "дата отсечки по дивидендам не найдена",
                "calculated_indicators": {
                    "ticker": (market_context or {}).get("ticker"),
                    "year": requested_year,
                    "dividend_found": False
                },
                "confidence_score": 0.25
            }

        if intent == "dividend_info":
            if dividend_comment_context and dividend_comment_context.get("dividend_found"):
                return {
                    "report_type": "dividend_info",
                    "trend_summary": dividend_comment_context.get("summary"),
                    "calculated_indicators": {
                        "ticker": (dividend_context or {}).get("ticker"),
                        "dividend_found": dividend_comment_context.get("dividend_found"),
                        "dividend_per_share": dividend_comment_context.get("dividend_per_share"),
                        "record_date": dividend_comment_context.get("record_date"),
                        "payment_date": dividend_comment_context.get("payment_date"),
                        "payment_timing_note": (dividend_context or {}).get("payment_timing_note"),
                        "dividend_yield_percent": dividend_comment_context.get("dividend_yield_percent"),
                    },
                    "confidence_score": 0.87
                }

            return {
                "report_type": "dividend_info",
                "trend_summary": "данные по дивидендам не найдены",
                "calculated_indicators": dividend_context or {},
                "confidence_score": 0.35
            }

        if intent == "historical_price_extremes_query":
            if historical_price_extremes_context and historical_price_extremes_context.get("found"):
                return {
                    "report_type": "historical_price_extremes_query",
                    "trend_summary": "найдены исторические экстремумы цены за выбранный период",
                    "calculated_indicators": {
                        "ticker": historical_price_extremes_context.get("ticker"),
                        "found": True,
                        "min_price": historical_price_extremes_context.get("min_price"),
                        "min_price_date": historical_price_extremes_context.get("min_price_date"),
                        "max_price": historical_price_extremes_context.get("max_price"),
                        "max_price_date": historical_price_extremes_context.get("max_price_date"),
                        "period_candles": historical_price_extremes_context.get("period_candles"),
                        "requested_limit": requested_limit,
                    },
                    "confidence_score": 0.93
                }

            return {
                "report_type": "historical_price_extremes_query",
                "trend_summary": "исторические экстремумы цены не найдены",
                "calculated_indicators": {
                    "ticker": (market_context or {}).get("ticker"),
                    "found": False,
                    "requested_limit": requested_limit,
                },
                "confidence_score": 0.26
            }

        if intent == "max_turnover_query":
            if max_turnover_context and max_turnover_context.get("found"):
                return {
                    "report_type": "max_turnover_query",
                    "trend_summary": "найден день с максимальным торговым оборотом за выбранный период",
                    "calculated_indicators": {
                        "ticker": max_turnover_context.get("ticker"),
                        "found": True,
                        "max_turnover": max_turnover_context.get("max_turnover"),
                        "turnover_date": max_turnover_context.get("turnover_date"),
                        "period_candles": max_turnover_context.get("period_candles"),
                        "requested_limit": requested_limit,
                    },
                    "confidence_score": 0.91
                }

            return {
                "report_type": "max_turnover_query",
                "trend_summary": "данные по максимальному торговому обороту не найдены",
                "calculated_indicators": {
                    "ticker": (market_context or {}).get("ticker"),
                    "found": False,
                    "requested_limit": requested_limit,
                },
                "confidence_score": 0.24
            }

        if intent == "buy_or_wait":
            if buy_or_wait_context:
                decision = buy_or_wait_context.get("decision")
                summary = buy_or_wait_context.get("summary")

                return {
                    "report_type": "buy_or_wait",
                    "trend_summary": summary,
                    "calculated_indicators": {
                        "decision": decision,
                        "summary": summary,
                        "reasons": buy_or_wait_context.get("reasons", []),
                        "trend": buy_or_wait_context.get("trend"),
                        "signal": buy_or_wait_context.get("signal"),
                        "rsi_14": buy_or_wait_context.get("rsi_14"),
                        "support": buy_or_wait_context.get("support"),
                        "resistance": buy_or_wait_context.get("resistance"),
                        "current_price": buy_or_wait_context.get("current_price"),
                        "has_dividend_context": buy_or_wait_context.get("has_dividend_context"),
                        "has_position": buy_or_wait_context.get("has_position"),
                        "dividend_context": dividend_context,
                        "position_market_metrics": position_market_metrics,
                    },
                    "confidence_score": 0.81
                }

            return {
                "report_type": "buy_or_wait",
                "trend_summary": "недостаточно данных для оценки точки входа",
                "calculated_indicators": {},
                "confidence_score": 0.3
            }

        if intent == "entry_point_analysis":
            if entry_point_context:
                return {
                    "report_type": "entry_point_analysis",
                    "trend_summary": entry_point_context.get("summary"),
                    "calculated_indicators": {
                        "entry_bias": entry_point_context.get("entry_bias"),
                        "summary": entry_point_context.get("summary"),
                        "reasons": entry_point_context.get("reasons", []),
                        "current_price": entry_point_context.get("current_price"),
                        "support": entry_point_context.get("support"),
                        "resistance": entry_point_context.get("resistance"),
                        "signal": entry_point_context.get("signal"),
                        "trend": entry_point_context.get("trend"),
                        "rsi_14": entry_point_context.get("rsi_14"),
                    },
                    "confidence_score": 0.79
                }

            return {
                "report_type": "entry_point_analysis",
                "trend_summary": "точка входа не определена из-за нехватки данных",
                "calculated_indicators": {},
                "confidence_score": 0.28
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
                        "has_position": position_market_metrics is not None,
                        "items": news_context.get("items", [])
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
                    "position_items": multi_position_market_metrics,
                    "comparison_context": context.get("comparison_context")
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
                    "has_position_metrics": bool(position_market_metrics or multi_position_market_metrics),
                    "has_dividend_context": bool(dividend_context and dividend_context.get("dividend_found"))
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
                    "has_dividend_context": bool(dividend_context and dividend_context.get("dividend_found")),
                    "has_technical_analysis": bool(technical_analysis_context),
                    "has_historical_dividend": bool(last_dividend_context),
                    "has_price_extremes": bool(historical_price_extremes_context and historical_price_extremes_context.get("found")),
                    "has_max_turnover": bool(max_turnover_context and max_turnover_context.get("found")),
                    "has_fx_price": bool(fx_price_context and fx_price_context.get("price") is not None),
                    "has_bond_coupon": bool(bond_last_coupon_context or bond_next_coupon_context),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent")
                },
                "confidence_score": 0.73
            }
        if intent == "bond_ranking":
            ranking = context.get("bond_ranking_context")

            if ranking:
                return {
                    "report_type": "bond_ranking",
                    "trend_summary": "сформирован рейтинг облигаций по купону",
                    "calculated_indicators": {
                        "items": ranking
                    },
                    "confidence_score": 0.95
                }

            return {
                "report_type": "bond_ranking",
                "trend_summary": "не удалось получить рейтинг облигаций",
                "calculated_indicators": {},
                "confidence_score": 0.3
            }

        if intent == "dividend_aristocrats":
            items = context.get("dividend_aristocrats_context")

            if items:
                return {
                    "report_type": "dividend_aristocrats",
                    "trend_summary": "найдены устойчивые дивидендные компании",
                    "calculated_indicators": {
                        "items": items
                    },
                    "confidence_score": 0.92
                }

            return {
                "report_type": "dividend_aristocrats",
                "trend_summary": "не удалось найти устойчивые дивидендные компании",
                "calculated_indicators": {},
                "confidence_score": 0.3
            }

        return None