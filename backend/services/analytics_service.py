class AnalyticsService:

    def run(self, intent: str, context: dict) -> dict:
        market_context = context.get("market_context") or {}
        multi_market_context = context.get("multi_market_context") or []

        news_context = context.get("news_context") or {}
        multi_news_context = context.get("multi_news_context") or []

        portfolio_metrics = context.get("portfolio_metrics") or {}
        position_market_metrics = context.get("position_market_metrics") or {}
        multi_position_market_metrics = context.get("multi_position_market_metrics") or []

        technical_analysis_context = context.get("technical_analysis_context") or {}
        dividend_context = context.get("dividend_context") or {}
        buy_or_wait_context = context.get("buy_or_wait_context") or {}
        entry_point_context = context.get("entry_point_context") or {}
        dividend_comment_context = context.get("dividend_comment_context") or {}

        last_dividend_context = context.get("last_dividend_context") or {}
        year_dividend_context = context.get("year_dividend_context") or {}
        expected_dividend_context = context.get("expected_dividend_context") or {}
        expected_dividend_calendar_context = context.get("expected_dividend_calendar_context") or {}

        historical_price_extremes_context = context.get("historical_price_extremes_context") or {}
        max_turnover_context = context.get("max_turnover_context") or {}

        fx_price_context = context.get("fx_price_context") or {}

        bond_context = context.get("bond_context") or {}
        bond_last_coupon_context = context.get("bond_last_coupon_context") or {}
        bond_next_coupon_context = context.get("bond_next_coupon_context") or {}
        bond_coupon_schedule_context = context.get("bond_coupon_schedule_context") or []
        bond_ranking_context = context.get("bond_ranking_context") or []

        dividend_ranking_context = context.get("dividend_ranking_context") or []
        dividend_aristocrats_context = context.get("dividend_aristocrats_context") or []

        comparison_context = context.get("comparison_context") or {}

        requested_year = context.get("requested_year")
        requested_limit = context.get("requested_limit")

        if intent == "price_check":
            return {
                "report_type": "price_check",
                "trend_summary": "Текущая цена инструмента",
                "calculated_indicators": {
                    "ticker": market_context.get("ticker"),
                    "display_name": market_context.get("display_name"),
                    "price_found": market_context.get("price_found", False),
                    "price": market_context.get("price"),
                    "volume": market_context.get("volume"),
                    "recorded_at": market_context.get("recorded_at"),
                    "source_name": market_context.get("source_name"),
                    "position_metrics": position_market_metrics if position_market_metrics else None,
                },
                "confidence_score": 0.98 if market_context.get("price_found") else 0.2,
            }

        if intent == "technical_analysis":
            return {
                "report_type": "technical_analysis",
                "trend_summary": "Технический анализ по инструменту",
                "calculated_indicators": {
                    "ticker": market_context.get("ticker"),
                    "display_name": market_context.get("display_name"),
                    "trend": technical_analysis_context.get("trend"),
                    "signal": technical_analysis_context.get("signal"),
                    "rsi_14": technical_analysis_context.get("rsi_14"),
                    "sma_5": technical_analysis_context.get("sma_5"),
                    "sma_10": technical_analysis_context.get("sma_10"),
                    "support": technical_analysis_context.get("support"),
                    "resistance": technical_analysis_context.get("resistance"),
                    "last_price": technical_analysis_context.get("last_price"),
                    "pattern": technical_analysis_context.get("pattern"),
                    "macd": technical_analysis_context.get("macd"),
                    "macd_signal": technical_analysis_context.get("macd_signal"),
                },
                "confidence_score": 0.9 if technical_analysis_context else 0.25,
            }

        if intent == "buy_or_wait":
            return {
                "report_type": "buy_or_wait",
                "trend_summary": buy_or_wait_context.get("summary") or "Оценка сценария покупки",
                "calculated_indicators": {
                    "ticker": market_context.get("ticker"),
                    "display_name": market_context.get("display_name"),
                    "decision": buy_or_wait_context.get("decision"),
                    "summary": buy_or_wait_context.get("summary"),
                    "reasons": buy_or_wait_context.get("reasons", []),
                    "trend": buy_or_wait_context.get("trend"),
                    "signal": buy_or_wait_context.get("signal"),
                    "rsi_14": buy_or_wait_context.get("rsi_14"),
                    "support": buy_or_wait_context.get("support"),
                    "resistance": buy_or_wait_context.get("resistance"),
                    "current_price": buy_or_wait_context.get("current_price"),
                    "dividend_context": dividend_context if dividend_context else None,
                    "position_market_metrics": position_market_metrics if position_market_metrics else None,
                },
                "confidence_score": 0.86 if buy_or_wait_context else 0.3,
            }

        if intent == "entry_point_analysis":
            return {
                "report_type": "entry_point_analysis",
                "trend_summary": entry_point_context.get("summary") or "Оценка точки входа",
                "calculated_indicators": {
                    "ticker": market_context.get("ticker"),
                    "display_name": market_context.get("display_name"),
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
                "confidence_score": 0.84 if entry_point_context else 0.28,
            }

        if intent == "dividend_info":
            base = dividend_comment_context if dividend_comment_context else dividend_context
            found = bool(base and base.get("dividend_found"))
            return {
                "report_type": "dividend_info",
                "trend_summary": base.get("summary") or "Дивидендная информация по бумаге",
                "calculated_indicators": {
                    "ticker": dividend_context.get("ticker") or market_context.get("ticker"),
                    "dividend_found": found,
                    "dividend_per_share": base.get("dividend_per_share"),
                    "record_date": base.get("record_date"),
                    "payment_date": base.get("payment_date"),
                    "payment_timing_note": dividend_context.get("payment_timing_note"),
                    "dividend_yield_percent": base.get("dividend_yield_percent"),
                    "currency": dividend_context.get("currency"),
                    "source_name": dividend_context.get("source_name"),
                },
                "confidence_score": 0.9 if found else 0.25,
            }

        if intent == "historical_dividend_query":
            target = year_dividend_context if (requested_year and year_dividend_context) else last_dividend_context
            found = bool(target)
            return {
                "report_type": "historical_dividend_query",
                "trend_summary": "Исторический дивиденд по бумаге",
                "calculated_indicators": {
                    "ticker": (target or {}).get("ticker") or market_context.get("ticker"),
                    "year": (target or {}).get("year") or requested_year,
                    "dividend_found": found,
                    "dividend_per_share": (target or {}).get("dividend_per_share"),
                    "record_date": (target or {}).get("record_date"),
                    "declared_date": (target or {}).get("declared_date"),
                    "currency": (target or {}).get("currency"),
                    "source_name": (target or {}).get("source_name"),
                },
                "confidence_score": 0.92 if found else 0.22,
            }

        if intent == "expected_dividend_query":
            if requested_year is not None:
                if requested_year == 2026:
                    if not expected_dividend_calendar_context:
                        return {
                            "report_type": "expected_dividend_query",
                            "requested_year": requested_year,
                            "success": False,
                            "message": f"По календарю дивидендов за {requested_year} год подтверждённых данных по этой бумаге нет.",
                            "calculated_indicators": {
                                "ticker": market_context.get("ticker"),
                                "year": requested_year,
                                "dividend_found": False,
                                "dividend_per_share": None,
                                "record_date": None,
                                "declared_date": None,
                                "planned_payment_date": None,
                                "currency": None,
                                "source_name": None,
                                "is_expected_proxy": False,
                                "t1_buy_date": None,
                                "status": None,
                                "dividend_yield_percent": None,
                                "price": None,
                            },
                            "confidence_score": 0.2,
                        }

                    return {
                        "report_type": "expected_dividend_query",
                        "requested_year": requested_year,
                        "success": True,
                        "message": None,
                        "calculated_indicators": {
                            "ticker": expected_dividend_calendar_context.get("ticker") or market_context.get("ticker"),
                            "year": requested_year,
                            "dividend_found": True,
                            "dividend_per_share": expected_dividend_calendar_context.get("dividend_per_share"),
                            "record_date": expected_dividend_calendar_context.get("record_date"),
                            "declared_date": expected_dividend_calendar_context.get("declared_date"),
                            "planned_payment_date": expected_dividend_calendar_context.get("planned_payment_date"),
                            "currency": expected_dividend_calendar_context.get("currency") or "RUB",
                            "source_name": expected_dividend_calendar_context.get("source") or "dividend_calendar_db",
                            "is_expected_proxy": False,
                            "t1_buy_date": expected_dividend_calendar_context.get("t1_buy_date"),
                            "status": expected_dividend_calendar_context.get("status"),
                            "dividend_yield_percent": expected_dividend_calendar_context.get("dividend_yield_percent"),
                            "price": expected_dividend_calendar_context.get("price"),
                            "sector": expected_dividend_calendar_context.get("sector"),
                        },
                        "confidence_score": 0.98,
                    }

                if not expected_dividend_context or expected_dividend_context.get("year") != requested_year:
                    return {
                        "report_type": "expected_dividend_query",
                        "requested_year": requested_year,
                        "success": False,
                        "message": f"По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге за {requested_year} год.",
                        "calculated_indicators": {
                            "ticker": market_context.get("ticker"),
                            "year": requested_year,
                            "dividend_found": False,
                            "dividend_per_share": None,
                            "record_date": None,
                            "declared_date": None,
                            "planned_payment_date": None,
                            "currency": None,
                            "source_name": None,
                            "is_expected_proxy": False,
                        },
                        "confidence_score": 0.2,
                    }

                return {
                    "report_type": "expected_dividend_query",
                    "requested_year": requested_year,
                    "success": True,
                    "message": None,
                    "calculated_indicators": {
                        "ticker": expected_dividend_context.get("ticker") or market_context.get("ticker"),
                        "year": expected_dividend_context.get("year"),
                        "dividend_found": True,
                        "dividend_per_share": expected_dividend_context.get("dividend_per_share"),
                        "record_date": expected_dividend_context.get("record_date"),
                        "declared_date": expected_dividend_context.get("declared_date"),
                        "planned_payment_date": expected_dividend_context.get("planned_payment_date"),
                        "currency": expected_dividend_context.get("currency"),
                        "source_name": expected_dividend_context.get("source_name"),
                        "is_expected_proxy": False,
                    },
                    "confidence_score": 0.85,
                }

            if expected_dividend_context:
                return {
                    "report_type": "expected_dividend_query",
                    "requested_year": None,
                    "success": True,
                    "message": None,
                    "calculated_indicators": {
                        "ticker": expected_dividend_context.get("ticker") or market_context.get("ticker"),
                        "year": expected_dividend_context.get("year"),
                        "dividend_found": True,
                        "dividend_per_share": expected_dividend_context.get("dividend_per_share"),
                        "record_date": expected_dividend_context.get("record_date"),
                        "declared_date": expected_dividend_context.get("declared_date"),
                        "planned_payment_date": expected_dividend_context.get("planned_payment_date"),
                        "currency": expected_dividend_context.get("currency"),
                        "source_name": expected_dividend_context.get("source_name"),
                        "is_expected_proxy": True,
                    },
                    "confidence_score": 0.75,
                }

            return {
                "report_type": "expected_dividend_query",
                "requested_year": None,
                "success": False,
                "message": "Нет данных по ожидаемым дивидендам.",
                "calculated_indicators": {
                    "ticker": market_context.get("ticker"),
                    "year": None,
                    "dividend_found": False,
                    "dividend_per_share": None,
                    "record_date": None,
                    "declared_date": None,
                    "planned_payment_date": None,
                    "currency": None,
                    "source_name": None,
                    "is_expected_proxy": False,
                },
                "confidence_score": 0.2,
            }

        if intent == "dividend_record_date_query":
            if requested_year == 2026:
                if not expected_dividend_calendar_context:
                    return {
                        "report_type": "dividend_record_date_query",
                        "requested_year": requested_year,
                        "success": False,
                        "message": f"По календарю дивидендов за {requested_year} год подтверждённых данных по этой бумаге нет.",
                        "calculated_indicators": {
                            "ticker": market_context.get("ticker"),
                            "year": requested_year,
                            "dividend_found": False,
                            "record_date": None,
                            "t1_buy_date": None,
                            "planned_payment_date": None,
                            "dividend_per_share": None,
                            "currency": None,
                        },
                        "confidence_score": 0.2,
                    }

                return {
                    "report_type": "dividend_record_date_query",
                    "requested_year": requested_year,
                    "success": True,
                    "message": None,
                    "calculated_indicators": {
                        "ticker": expected_dividend_calendar_context.get("ticker") or market_context.get("ticker"),
                        "year": requested_year,
                        "dividend_found": True,
                        "record_date": expected_dividend_calendar_context.get("record_date"),
                        "t1_buy_date": expected_dividend_calendar_context.get("t1_buy_date"),
                        "planned_payment_date": expected_dividend_calendar_context.get("planned_payment_date"),
                        "dividend_per_share": expected_dividend_calendar_context.get("dividend_per_share"),
                        "currency": expected_dividend_calendar_context.get("currency") or "RUB",
                        "status": expected_dividend_calendar_context.get("status"),
                    },
                    "confidence_score": 0.95,
                }

            target = year_dividend_context if (requested_year and year_dividend_context) else last_dividend_context
            found = bool(target and target.get("record_date"))
            return {
                "report_type": "dividend_record_date_query",
                "trend_summary": "Дата отсечки по дивидендам",
                "calculated_indicators": {
                    "ticker": (target or {}).get("ticker") or market_context.get("ticker"),
                    "year": (target or {}).get("year") or requested_year,
                    "dividend_found": bool(target),
                    "record_date": (target or {}).get("record_date"),
                    "dividend_per_share": (target or {}).get("dividend_per_share"),
                    "currency": (target or {}).get("currency"),
                },
                "confidence_score": 0.93 if found else 0.2,
            }

        if intent == "historical_price_extremes_query":
            found = bool(historical_price_extremes_context and historical_price_extremes_context.get("found"))
            return {
                "report_type": "historical_price_extremes_query",
                "trend_summary": "Исторические экстремумы цены",
                "calculated_indicators": {
                    "ticker": historical_price_extremes_context.get("ticker") or market_context.get("ticker"),
                    "found": found,
                    "min_price": historical_price_extremes_context.get("min_price"),
                    "min_price_date": historical_price_extremes_context.get("min_price_date"),
                    "max_price": historical_price_extremes_context.get("max_price"),
                    "max_price_date": historical_price_extremes_context.get("max_price_date"),
                    "period_candles": historical_price_extremes_context.get("period_candles"),
                    "requested_limit": requested_limit,
                },
                "confidence_score": 0.94 if found else 0.2,
            }

        if intent == "max_turnover_query":
            found = bool(max_turnover_context and max_turnover_context.get("found"))
            return {
                "report_type": "max_turnover_query",
                "trend_summary": "Максимальный торговый оборот",
                "calculated_indicators": {
                    "ticker": max_turnover_context.get("ticker") or market_context.get("ticker"),
                    "found": found,
                    "max_turnover": max_turnover_context.get("max_turnover"),
                    "turnover_date": max_turnover_context.get("turnover_date"),
                    "period_candles": max_turnover_context.get("period_candles"),
                    "requested_limit": requested_limit,
                },
                "confidence_score": 0.94 if found else 0.2,
            }

        if intent == "fx_price_query":
            found = bool(fx_price_context and fx_price_context.get("price") is not None)
            return {
                "report_type": "fx_price_query",
                "trend_summary": "Курс валютной пары",
                "calculated_indicators": {
                    "currency_code": fx_price_context.get("currency_code"),
                    "secid": fx_price_context.get("secid"),
                    "display_name": fx_price_context.get("display_name"),
                    "shortname": fx_price_context.get("shortname"),
                    "price": fx_price_context.get("price"),
                    "boardid": fx_price_context.get("boardid"),
                    "trading_status": fx_price_context.get("trading_status"),
                    "last_update_time": fx_price_context.get("last_update_time"),
                    "source_name": fx_price_context.get("source_name"),
                },
                "confidence_score": 0.97 if found else 0.2,
            }

        if intent == "bond_coupon_query":
            found = bool(bond_last_coupon_context or bond_next_coupon_context or bond_coupon_schedule_context)
            return {
                "report_type": "bond_coupon_query",
                "trend_summary": "Купоны по облигации",
                "calculated_indicators": {
                    "bond_context": bond_context if bond_context else None,
                    "last_coupon": bond_last_coupon_context if bond_last_coupon_context else None,
                    "next_coupon": bond_next_coupon_context if bond_next_coupon_context else None,
                    "coupon_schedule": bond_coupon_schedule_context[:10] if bond_coupon_schedule_context else [],
                },
                "confidence_score": 0.92 if found else 0.2,
            }

        if intent == "bond_ranking":
            found = bool(bond_ranking_context)
            return {
                "report_type": "bond_ranking",
                "trend_summary": "Рейтинг облигаций по купону",
                "calculated_indicators": {
                    "items": bond_ranking_context,
                },
                "confidence_score": 0.9 if found else 0.2,
            }

        if intent == "dividend_ranking_query":
            found = bool(dividend_ranking_context)
            return {
                "report_type": "dividend_ranking_query",
                "trend_summary": "Рейтинг акций по дивидендной доходности",
                "calculated_indicators": {
                    "items": dividend_ranking_context,
                },
                "confidence_score": 0.9 if found else 0.2,
            }

        if intent == "dividend_aristocrats":
            found = bool(dividend_aristocrats_context)
            return {
                "report_type": "dividend_aristocrats",
                "trend_summary": "Компании с устойчивыми дивидендными выплатами",
                "calculated_indicators": {
                    "items": dividend_aristocrats_context,
                },
                "confidence_score": 0.9 if found else 0.2,
            }

        if intent == "multi_price_compare":
            return {
                "report_type": "multi_price_compare",
                "trend_summary": "Сравнение цен нескольких инструментов",
                "calculated_indicators": {
                    "items": multi_market_context,
                    "position_metrics": multi_position_market_metrics,
                },
                "confidence_score": 0.9 if multi_market_context else 0.2,
            }

        if intent == "multi_news_compare":
            return {
                "report_type": "multi_news_compare",
                "trend_summary": "Сравнение новостного фона нескольких инструментов",
                "calculated_indicators": {
                    "items": multi_news_context,
                },
                "confidence_score": 0.88 if multi_news_context else 0.2,
            }

        if intent == "multi_position_compare":
            return {
                "report_type": "multi_position_compare",
                "trend_summary": "Сравнение позиций пользователя",
                "calculated_indicators": {
                    "items": multi_position_market_metrics,
                },
                "confidence_score": 0.88 if multi_position_market_metrics else 0.2,
            }

        if intent == "multi_instrument_compare":
            return {
                "report_type": "multi_instrument_compare",
                "trend_summary": "Сравнение инструментов",
                "calculated_indicators": {
                    "market_items": multi_market_context,
                    "news_items": multi_news_context,
                    "position_items": multi_position_market_metrics,
                    "comparison_context": comparison_context,
                },
                "confidence_score": 0.86 if comparison_context or multi_market_context else 0.2,
            }

        if intent == "portfolio_analysis":
            return {
                "report_type": "portfolio_analysis",
                "trend_summary": "Сводка по портфелю",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "total_invested_value": portfolio_metrics.get("total_invested_value"),
                    "total_market_value": portfolio_metrics.get("total_market_value"),
                    "total_absolute_pnl": portfolio_metrics.get("total_absolute_pnl"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent"),
                    "profitable_positions": portfolio_metrics.get("profitable_positions"),
                    "losing_positions": portfolio_metrics.get("losing_positions"),
                },
                "confidence_score": 0.9,
            }

        if intent == "news_explain":
            found = bool(news_context and news_context.get("news_found"))
            return {
                "report_type": "news_explain",
                "trend_summary": "Новостной фон по инструменту",
                "calculated_indicators": {
                    "ticker": news_context.get("ticker"),
                    "display_name": news_context.get("display_name"),
                    "news_found": news_context.get("news_found"),
                    "items": news_context.get("items", []),
                },
                "confidence_score": 0.86 if found else 0.2,
            }

        if intent == "risk_return":
            return {
                "report_type": "risk_return",
                "trend_summary": "Предварительная оценка риска и доходности",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "profitable_positions": portfolio_metrics.get("profitable_positions"),
                    "losing_positions": portfolio_metrics.get("losing_positions"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent"),
                },
                "confidence_score": 0.75,
            }

        if intent == "benchmark_compare":
            return {
                "report_type": "benchmark_compare",
                "trend_summary": "Базовое сравнение с бенчмарком",
                "calculated_indicators": {
                    "positions_count": portfolio_metrics.get("positions_count"),
                    "total_pnl_percent": portfolio_metrics.get("total_pnl_percent"),
                },
                "confidence_score": 0.65,
            }

        if intent == "scenario_forecast":
            return {
                "report_type": "scenario_forecast",
                "trend_summary": "Сценарный комментарий на основе текущих данных",
                "calculated_indicators": {
                    "has_market_context": bool(market_context or multi_market_context),
                    "has_news_context": bool(news_context or multi_news_context),
                    "has_dividend_context": bool(dividend_context),
                    "has_technical_analysis": bool(technical_analysis_context),
                },
                "confidence_score": 0.58,
            }

        if intent == "simple_analysis":
            return {
                "report_type": "simple_analysis",
                "trend_summary": "Общий аналитический комментарий",
                "calculated_indicators": {
                    "has_market_context": bool(market_context or multi_market_context),
                    "has_news_context": bool(news_context or multi_news_context),
                    "has_dividend_context": bool(dividend_context),
                    "has_technical_analysis": bool(technical_analysis_context),
                    "has_fx_price": bool(fx_price_context),
                    "has_bond_coupon": bool(bond_last_coupon_context or bond_next_coupon_context),
                },
                "confidence_score": 0.7,
            }

        return {
            "report_type": "general_question",
            "trend_summary": "Общий ответ",
            "calculated_indicators": {},
            "confidence_score": 0.5,
        }