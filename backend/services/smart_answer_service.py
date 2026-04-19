class SmartAnswerService:
    """
    Детерминированный слой ответов.
    Если можем уверенно ответить по готовым данным — отвечаем без LLM.
    Если нет — возвращаем None, и дальше отвечает LLM.
    """

    def build_answer(
        self,
        user_text: str,
        intent: str,
        context: dict,
        analytics_result: dict | None = None,
        comparative_summary: dict | None = None
    ) -> str | None:
        if intent == "price_check":
            return self._price_answer(analytics_result)

        if intent == "technical_analysis":
            return self._technical_analysis_answer(analytics_result)

        if intent == "buy_or_wait":
            return self._buy_or_wait_answer(analytics_result)

        if intent == "entry_point_analysis":
            return self._entry_point_answer(analytics_result)

        if intent == "dividend_info":
            return self._dividend_info_answer(analytics_result)

        if intent == "historical_dividend_query":
            return self._historical_dividend_answer(analytics_result)

        if intent == "expected_dividend_query":
            return self._expected_dividend_answer(user_text, analytics_result)

        if intent == "dividend_record_date_query":
            return self._dividend_record_date_answer(user_text, analytics_result)

        if intent == "historical_price_extremes_query":
            return self._historical_price_extremes_answer(analytics_result)

        if intent == "max_turnover_query":
            return self._max_turnover_answer(analytics_result)

        if intent == "fx_price_query":
            return self._fx_price_answer(analytics_result)

        if intent == "bond_coupon_query":
            return self._bond_coupon_answer(analytics_result)

        if intent == "bond_ranking":
            return self._bond_ranking_answer(analytics_result)

        if intent == "dividend_ranking_query":
            return self._dividend_ranking_answer(analytics_result)

        if intent == "dividend_aristocrats":
            return self._dividend_aristocrats_answer(analytics_result)

        if intent == "multi_price_compare":
            return self._multi_price_compare_answer(analytics_result)

        if intent == "multi_news_compare":
            return self._multi_news_compare_answer(analytics_result)

        if intent == "multi_position_compare":
            return self._multi_position_compare_answer(analytics_result)

        if intent == "multi_instrument_compare":
            return self._multi_instrument_compare_answer(analytics_result, comparative_summary)

        if intent == "portfolio_analysis":
            return self._portfolio_answer(analytics_result)

        if intent == "news_explain":
            return self._news_explain_answer(analytics_result)

        if intent == "risk_return":
            return self._risk_return_answer(analytics_result)

        if intent == "benchmark_compare":
            return self._benchmark_compare_answer(analytics_result)

        return None

    def _price_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("price_found"):
            return "Не удалось найти актуальную цену по этому инструменту."

        name = data.get("display_name") or data.get("ticker")
        price = data.get("price")
        volume = data.get("volume")
        source_name = data.get("source_name")
        recorded_at = data.get("recorded_at")
        position_metrics = data.get("position_metrics")

        parts = [f"По инструменту {name} текущая цена составляет {price}."]

        if volume is not None:
            parts.append(f"Объём в последней записи: {volume}.")
        if source_name:
            parts.append(f"Источник: {source_name}.")
        if recorded_at:
            parts.append(f"Время обновления: {recorded_at}.")

        if position_metrics:
            market_value = position_metrics.get("market_value")
            pnl = position_metrics.get("absolute_pnl")
            pnl_percent = position_metrics.get("pnl_percent")

            if market_value is not None:
                parts.append(f"Текущая стоимость твоей позиции: {market_value}.")
            if pnl is not None:
                pnl_text = f"{pnl}"
                if pnl_percent is not None:
                    pnl_text += f" ({pnl_percent}%)"
                parts.append(f"Текущий результат по позиции: {pnl_text}.")

        return " ".join(parts)

    def _technical_analysis_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Недостаточно данных для технического анализа."

        parts = []

        if data.get("last_price") is not None:
            parts.append(f"Последняя цена: {data.get('last_price')}.")
        if data.get("trend"):
            parts.append(f"Текущий тренд: {data.get('trend')}.")
        if data.get("signal"):
            parts.append(f"Сигнал: {data.get('signal')}.")
        if data.get("rsi_14") is not None:
            rsi = round(data.get("rsi_14"), 4)
            parts.append(f"RSI(14): {rsi}.")
            if rsi > 70:
                parts.append("Индикатор находится в зоне перекупленности.")
            elif rsi < 30:
                parts.append("Индикатор находится в зоне перепроданности.")
        if data.get("support") is not None:
            parts.append(f"Поддержка: {round(data.get('support'), 4)}.")
        if data.get("resistance") is not None:
            parts.append(f"Сопротивление: {round(data.get('resistance'), 4)}.")
        if data.get("pattern"):
            parts.append(f"Паттерн: {data.get('pattern')}.")
        if data.get("macd") is not None:
            parts.append(f"MACD: {round(data.get('macd'), 4)}.")
        if data.get("macd_signal") is not None:
            parts.append(f"Сигнальная линия MACD: {round(data.get('macd_signal'), 4)}.")

        parts.append("Технический комментарий носит информационный характер.")
        return " ".join(parts)

    def _buy_or_wait_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Недостаточно данных, чтобы оценить, покупать сейчас или подождать."

        parts = []

        summary = data.get("summary")
        decision = data.get("decision")
        trend = data.get("trend")
        signal = data.get("signal")
        rsi_14 = data.get("rsi_14")
        current_price = data.get("current_price")
        support = data.get("support")
        resistance = data.get("resistance")
        dividend_context = data.get("dividend_context") or {}
        position_market_metrics = data.get("position_market_metrics") or {}

        if summary:
            parts.append(summary)
        else:
            if decision == "buy_zone":
                parts.append("По текущим данным бумага выглядит относительно интересной для входа.")
            elif decision == "wait_for_better_entry":
                parts.append("По текущим данным более осторожный сценарий — дождаться более комфортной точки входа.")
            else:
                parts.append("Сигналы смешанные, поэтому спешить с входом не обязательно.")

        if current_price is not None:
            parts.append(f"Текущая цена: {current_price}.")
        if trend:
            parts.append(f"Тренд: {trend}.")
        if signal:
            parts.append(f"Сигнал: {signal}.")
        if rsi_14 is not None:
            parts.append(f"RSI(14): {round(rsi_14, 4)}.")
        if support is not None:
            parts.append(f"Поддержка: {round(support, 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(resistance, 4)}.")

        if dividend_context.get("dividend_found"):
            if dividend_context.get("record_date"):
                parts.append(f"Дата закрытия реестра в текущем контексте: {dividend_context.get('record_date')}.")
            if dividend_context.get("dividend_yield_percent") is not None:
                parts.append(f"Оценочная дивидендная доходность: {dividend_context.get('dividend_yield_percent')}%.")

        if position_market_metrics:
            pnl = position_market_metrics.get("absolute_pnl")
            pnl_percent = position_market_metrics.get("pnl_percent")
            if pnl is not None:
                pnl_text = f"{pnl}"
                if pnl_percent is not None:
                    pnl_text += f" ({pnl_percent}%)"
                parts.append(f"По текущей позиции результат: {pnl_text}.")

        parts.append("Это аналитический комментарий, а не персональная инвестиционная рекомендация.")
        return " ".join(parts)

    def _entry_point_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Недостаточно данных для анализа точки входа."

        parts = []

        if data.get("summary"):
            parts.append(data.get("summary"))
        else:
            parts.append("Анализ точки входа по текущим рыночным данным.")

        if data.get("current_price") is not None:
            parts.append(f"Текущая цена: {data.get('current_price')}.")
        if data.get("support") is not None:
            parts.append(f"Поддержка: {round(data.get('support'), 4)}.")
        if data.get("resistance") is not None:
            parts.append(f"Сопротивление: {round(data.get('resistance'), 4)}.")
        if data.get("trend"):
            parts.append(f"Тренд: {data.get('trend')}.")
        if data.get("signal"):
            parts.append(f"Сигнал: {data.get('signal')}.")
        if data.get("rsi_14") is not None:
            parts.append(f"RSI(14): {round(data.get('rsi_14'), 4)}.")

        entry_bias = data.get("entry_bias")
        if entry_bias == "near_support":
            parts.append("Цена ближе к поддержке, поэтому точка входа выглядит более комфортной.")
        elif entry_bias == "near_resistance":
            parts.append("Цена ближе к сопротивлению, поэтому вход на текущих уровнях выглядит более осторожным.")
        elif entry_bias == "mid_range":
            parts.append("Цена находится примерно в середине диапазона между поддержкой и сопротивлением.")

        return " ".join(parts)

    def _dividend_info_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("dividend_found"):
            return "По этой бумаге у меня сейчас нет подтверждённых данных по дивидендам."

        parts = ["По бумаге найдены дивидендные данные."]

        if data.get("dividend_per_share") is not None:
            parts.append(f"Размер дивиденда: {data.get('dividend_per_share')}.")
        if data.get("record_date"):
            parts.append(f"Дата закрытия реестра: {data.get('record_date')}.")
        if data.get("payment_date"):
            parts.append(f"Дата выплаты: {data.get('payment_date')}.")
        elif data.get("payment_timing_note"):
            parts.append("Дивиденды обычно поступают в срок до 25 рабочих дней после даты закрытия реестра.")
        if data.get("dividend_yield_percent") is not None:
            parts.append(f"Оценочная дивидендная доходность: {data.get('dividend_yield_percent')}%.")
        if data.get("source_name"):
            parts.append(f"Источник данных: {data.get('source_name')}.")

        return " ".join(parts)

    def _historical_dividend_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("dividend_found"):
            year = data.get("year")
            if year:
                return f"По этой бумаге у меня сейчас нет подтверждённых данных по дивиденду за {year} год."
            return "По этой бумаге у меня сейчас нет подтверждённых данных по историческому дивиденду."

        ticker = data.get("ticker")
        year = data.get("year")
        dividend_per_share = data.get("dividend_per_share")
        currency = data.get("currency")
        record_date = data.get("record_date")
        declared_date = data.get("declared_date")

        parts = []
        if year:
            parts.append(f"По бумаге {ticker} за {year} год найден дивиденд {dividend_per_share} {currency or ''}.")
        else:
            parts.append(f"По бумаге {ticker} найден исторический дивиденд {dividend_per_share} {currency or ''}.")
        if record_date:
            parts.append(f"Дата отсечки: {record_date}.")
        if declared_date:
            parts.append(f"Дата решения: {declared_date}.")

        return " ".join(parts)

    def _expected_dividend_answer(self, user_text: str, analytics_result: dict | None) -> str | None:
        analytics_result = analytics_result or {}
        success = analytics_result.get("success")
        message = analytics_result.get("message")
        requested_year = analytics_result.get("requested_year")
        data = analytics_result.get("calculated_indicators", {}) or {}

        if success is False:
            return message or (
                f"По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге за {requested_year} год."
                if requested_year else
                "По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге."
            )

        if not data or not data.get("dividend_found"):
            if requested_year:
                return f"По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге за {requested_year} год."
            return "По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге."

        ticker = data.get("ticker")
        year = data.get("year")
        dividend_per_share = data.get("dividend_per_share")
        currency = data.get("currency")
        record_date = data.get("record_date")
        declared_date = data.get("declared_date")
        t1_buy_date = data.get("t1_buy_date")
        planned_payment_date = data.get("planned_payment_date")
        source_name = data.get("source_name")
        status = data.get("status")
        price = data.get("price")
        dividend_yield_percent = data.get("dividend_yield_percent")

        text_lower = (user_text or "").lower().replace("ё", "е")

        asks_buy_date = any(marker in text_lower for marker in [
            "до какой даты купить",
            "когда купить под дивиденды",
            "дата покупки под дивиденды",
            "купить под дивиденды",
            "t+1",
        ])

        asks_record_date = any(marker in text_lower for marker in [
            "дата отсечки",
            "когда дата отсечки",
            "отсечка",
            "дата закрытия реестра",
            "закрытие реестра",
        ])

        asks_payment_date = any(marker in text_lower for marker in [
            "плановая дата выплаты",
            "когда выплата",
            "когда плановая выплата",
            "дата выплаты",
            "когда выплатят",
        ])

        asks_only_dividend = (
            "дивиденд" in text_lower or "дивиденды" in text_lower
        ) and not asks_buy_date and not asks_record_date and not asks_payment_date

        parts = []

        # 1. Точечный ответ на "до какой даты купить"
        if asks_buy_date and t1_buy_date:
            parts.append(f"Купить под дивиденды по бумаге {ticker} нужно до {t1_buy_date}.")
            if record_date:
                parts.append(f"Дата отсечки: {record_date}.")
            if planned_payment_date:
                parts.append(f"Плановая дата выплаты: {planned_payment_date}.")
            if dividend_per_share is not None:
                parts.append(f"Дивиденд: {dividend_per_share} {currency or ''}.")
            if status:
                parts.append(f"Статус: {status}.")
            if source_name:
                parts.append(f"Источник: {source_name}.")
            return " ".join(parts)

        # 2. Точечный ответ на "когда дата отсечки"
        if asks_record_date and record_date:
            parts.append(f"Дата отсечки по бумаге {ticker}: {record_date}.")
            if t1_buy_date:
                parts.append(f"Купить под дивиденды (T+1) нужно до {t1_buy_date}.")
            if planned_payment_date:
                parts.append(f"Плановая дата выплаты: {planned_payment_date}.")
            if dividend_per_share is not None:
                parts.append(f"Дивиденд: {dividend_per_share} {currency or ''}.")
            if status:
                parts.append(f"Статус: {status}.")
            if source_name:
                parts.append(f"Источник: {source_name}.")
            return " ".join(parts)

        # 3. Точечный ответ на "когда выплата"
        if asks_payment_date and planned_payment_date:
            parts.append(f"Плановая дата выплаты по бумаге {ticker}: {planned_payment_date}.")
            if record_date:
                parts.append(f"Дата отсечки: {record_date}.")
            if t1_buy_date:
                parts.append(f"Купить под дивиденды (T+1) нужно до {t1_buy_date}.")
            if dividend_per_share is not None:
                parts.append(f"Дивиденд: {dividend_per_share} {currency or ''}.")
            if status:
                parts.append(f"Статус: {status}.")
            if source_name:
                parts.append(f"Источник: {source_name}.")
            return " ".join(parts)

        # 4. Общий ответ про дивиденд
        if requested_year:
            if status == "Подтверждено":
                parts.append(
                    f"По календарю дивидендов для бумаги {ticker} за {requested_year} год подтверждён дивиденд {dividend_per_share} {currency or ''}."
                )
            elif status == "Рекомендовано":
                parts.append(
                    f"По календарю дивидендов для бумаги {ticker} за {requested_year} год рекомендован дивиденд {dividend_per_share} {currency or ''}."
                )
            else:
                parts.append(
                    f"По текущим данным ориентир по дивиденду для бумаги {ticker} за {requested_year} год составляет {dividend_per_share} {currency or ''}."
                )
        elif year:
            parts.append(
                f"По текущим данным ориентир по дивиденду для бумаги {ticker} за {year} год составляет {dividend_per_share} {currency or ''}."
            )
        else:
            parts.append(
                f"По текущим данным наиболее релевантный дивидендный ориентир по бумаге {ticker} составляет {dividend_per_share} {currency or ''}."
            )

        if record_date:
            parts.append(f"Дата отсечки: {record_date}.")
        if t1_buy_date:
            parts.append(f"Купить под дивиденды (T+1) нужно до {t1_buy_date}.")
            parts.append("Это последний день покупки на бирже, чтобы попасть в реестр на дивиденды.")
        if planned_payment_date:
            parts.append(f"Плановая дата выплаты: {planned_payment_date}.")
        if declared_date:
            parts.append(f"Дата решения: {declared_date}.")
        if status:
            parts.append(f"Статус: {status}.")
        if price is not None:
            parts.append(f"Цена бумаги в календаре: {price}.")
        if dividend_yield_percent is not None:
            parts.append(f"Дивидендная доходность: {dividend_yield_percent}%.")
        if source_name:
            parts.append(f"Источник: {source_name}.")
        if data.get("is_expected_proxy"):
            parts.append("Это ориентир по доступным данным, а не гарантированное будущее решение по дивидендам.")

        return " ".join(parts)

    def _dividend_record_date_answer(self, user_text: str, analytics_result: dict | None) -> str | None:
        analytics_result = analytics_result or {}
        success = analytics_result.get("success")
        message = analytics_result.get("message")
        data = analytics_result.get("calculated_indicators", {}) or {}

        if success is False and message:
            return message

        if not data:
            return "По этой бумаге у меня сейчас нет подтверждённой даты отсечки."

        record_date = data.get("record_date")
        t1_buy_date = data.get("t1_buy_date")
        planned_payment_date = data.get("planned_payment_date")
        ticker = data.get("ticker")
        dividend_per_share = data.get("dividend_per_share")
        currency = data.get("currency")
        status = data.get("status")

        text_lower = (user_text or "").lower().replace("ё", "е")
        asks_buy_date = any(marker in text_lower for marker in [
            "до какой даты купить",
            "когда купить под дивиденды",
            "дата покупки под дивиденды",
            "купить под дивиденды",
            "t+1",
        ])

        if asks_buy_date:
            if not t1_buy_date:
                year = data.get("year")
                if year:
                    return f"По этой бумаге у меня сейчас нет подтверждённой даты покупки под дивиденды за {year} год."
                return "По этой бумаге у меня сейчас нет подтверждённой даты покупки под дивиденды."

            parts = [f"Купить под дивиденды по бумаге {ticker} нужно до {t1_buy_date}."]
            if record_date:
                parts.append(f"Дата отсечки: {record_date}.")
            if planned_payment_date:
                parts.append(f"Плановая дата выплаты: {planned_payment_date}.")
            if dividend_per_share is not None:
                parts.append(f"Дивиденд: {dividend_per_share} {currency or ''}.")
            if status:
                parts.append(f"Статус: {status}.")
            return " ".join(parts)

        if not record_date:
            year = data.get("year")
            if year:
                return f"По этой бумаге у меня сейчас нет подтверждённой даты отсечки за {year} год."
            return "По этой бумаге у меня сейчас нет подтверждённой даты отсечки."

        parts = [f"Дата отсечки по бумаге {ticker}: {record_date}."]
        if t1_buy_date:
            parts.append(f"Купить под дивиденды (T+1) нужно до {t1_buy_date}.")
            parts.append("Это последний день покупки на бирже, чтобы попасть в реестр на дивиденды.")
        if planned_payment_date:
            parts.append(f"Плановая дата выплаты: {planned_payment_date}.")
        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда в этом контексте: {dividend_per_share} {currency or ''}.")
        if status:
            parts.append(f"Статус: {status}.")
        parts.append("Поступление дивидендов обычно ожидается в срок до 25 рабочих дней после даты закрытия реестра.")
        return " ".join(parts)

    def _historical_price_extremes_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("found"):
            return "Исторические экстремумы цены по выбранному периоду не найдены."

        parts = [f"По бумаге {data.get('ticker')} за выбранный период найдены ценовые экстремумы."]
        if data.get("min_price") is not None:
            parts.append(f"Минимальная цена была {data.get('min_price')} на дату {data.get('min_price_date')}.")
        if data.get("max_price") is not None:
            parts.append(f"Максимальная цена была {data.get('max_price')} на дату {data.get('max_price_date')}.")
        return " ".join(parts)

    def _max_turnover_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("found"):
            return "Данные по максимальному торговому обороту за выбранный период не найдены."

        return (
            f"По бумаге {data.get('ticker')} максимальный торговый оборот за день "
            f"составил {data.get('max_turnover')} на дату {data.get('turnover_date')}."
        )

    def _fx_price_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or data.get("price") is None:
            return "Не удалось найти актуальную цену по этой валюте."

        parts = [f"По валютной паре {data.get('display_name')} текущая цена составляет {data.get('price')}."]
        if data.get("last_update_time"):
            parts.append(f"Время обновления: {data.get('last_update_time')}.")
        if data.get("source_name"):
            parts.append(f"Источник: {data.get('source_name')}.")
        return " ".join(parts)

    def _bond_coupon_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Данные по купонам облигации не найдены."

        last_coupon = data.get("last_coupon") or {}
        next_coupon = data.get("next_coupon") or {}
        schedule = data.get("coupon_schedule") or []

        if not last_coupon and not next_coupon and not schedule:
            return "Данные по купонам облигации не найдены."

        parts = []

        if last_coupon:
            parts.append(
                f"Последний известный купон по облигации {last_coupon.get('bond_code')} "
                f"составил {last_coupon.get('coupon_value')} {last_coupon.get('face_unit') or ''}."
            )
            if last_coupon.get("coupon_percent") is not None:
                parts.append(f"Купонная ставка в этом периоде: {last_coupon.get('coupon_percent')}%.")
            if last_coupon.get("coupon_date"):
                parts.append(f"Дата последней выплаты купона: {last_coupon.get('coupon_date')}.")

        if next_coupon:
            parts.append(
                f"Следующий купон ожидается {next_coupon.get('coupon_date')} "
                f"в размере {next_coupon.get('coupon_value')} {next_coupon.get('face_unit') or ''}."
            )
            if next_coupon.get("coupon_percent") is not None:
                parts.append(f"Купонная ставка следующего периода: {next_coupon.get('coupon_percent')}%.")

        if schedule:
            parts.append(f"В расписании доступно купонов: {len(schedule)}.")

        return " ".join(parts)

    def _bond_ranking_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось получить список облигаций с высоким купоном."

        parts = ["Топ облигаций по купонной доходности:"]
        for i, item in enumerate(items, 1):
            text = f"{i}. {item.get('name')} ({item.get('ticker')})"
            if item.get("coupon_percent") is not None:
                text += f" — {item.get('coupon_percent')}%"
            if item.get("coupon_value") is not None:
                text += f", купон {item.get('coupon_value')}"
            parts.append(text)

        parts.append("Обрати внимание: высокая доходность по облигациям часто связана с повышенным риском эмитента.")
        return "\n".join(parts)

    def _dividend_ranking_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось получить список акций с высокой дивидендной доходностью."

        parts = ["Топ акций по дивидендной доходности:"]
        for i, item in enumerate(items, 1):
            text = f"{i}. {item.get('name') or item.get('ticker')} ({item.get('ticker')}) — дивдоходность {item.get('dividend_yield_percent')}%"
            if item.get("dividend_per_share") is not None:
                text += f", дивиденд {item.get('dividend_per_share')}"
            if item.get("year"):
                text += f", последний контекст {item.get('year')} года"
            parts.append(text)

        parts.append("Важно: высокая дивидендная доходность не всегда означает низкий риск или устойчивость будущих выплат.")
        return "\n".join(parts)

    def _dividend_aristocrats_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось найти устойчивые дивидендные компании."

        parts = ["Компании с устойчивыми дивидендными выплатами:"]
        for i, item in enumerate(items, 1):
            parts.append(
                f"{i}. {item.get('name') or item.get('ticker')} ({item.get('ticker')}) — "
                f"{item.get('years')} лет подряд, доходность {item.get('dividend_yield')}%"
            )

        parts.append("Такие компании обычно выглядят устойчивее по дивидендной истории, но это не исключает рыночных рисков.")
        return "\n".join(parts)

    def _multi_price_compare_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось подготовить сравнение цен."

        parts = ["Сравнение цен по инструментам:"]
        for item in items:
            name = item.get("display_name") or item.get("ticker")
            if item.get("price_found"):
                parts.append(f"{name}: {item.get('price')}.")
            else:
                parts.append(f"{name}: цена не найдена.")
        return " ".join(parts)

    def _multi_news_compare_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось подготовить сравнение новостей."

        parts = ["Сравнение новостного фона:"]
        for item in items:
            name = item.get("display_name") or item.get("ticker")
            count = len(item.get("items", [])) if item.get("news_found") else 0
            parts.append(f"{name}: новостей {count}.")
        return " ".join(parts)

    def _multi_position_compare_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось подготовить сравнение позиций."

        parts = ["Сравнение позиций пользователя:"]
        for item in items:
            ticker = item.get("ticker")
            pnl = item.get("absolute_pnl")
            pnl_percent = item.get("pnl_percent")

            text = f"{ticker}:"
            if pnl is not None:
                text += f" P&L {pnl}"
                if pnl_percent is not None:
                    text += f" ({pnl_percent}%)"
            text += "."
            parts.append(text)

        return " ".join(parts)

    def _multi_instrument_compare_answer(
        self,
        analytics_result: dict | None,
        comparative_summary: dict | None = None
    ) -> str | None:
        if comparative_summary and comparative_summary.get("summary"):
            return comparative_summary.get("summary")

        data = (analytics_result or {}).get("calculated_indicators", {})
        comparison_context = data.get("comparison_context") or {}

        if comparison_context.get("summary"):
            return comparison_context.get("summary")

        market_items = data.get("market_items", [])
        if not market_items:
            return "Не удалось подготовить сравнение инструментов."

        parts = ["Сравнение инструментов:"]
        for item in market_items:
            name = item.get("display_name") or item.get("ticker")
            if item.get("price_found"):
                parts.append(f"{name}: цена {item.get('price')}.")
            else:
                parts.append(f"{name}: цена не найдена.")
        return " ".join(parts)

    def _portfolio_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        positions_count = data.get("positions_count", 0)

        if positions_count == 0:
            return "Портфель пока пуст."

        parts = [f"В портфеле сейчас {positions_count} позиций."]

        if data.get("total_invested_value") is not None:
            parts.append(f"Суммарно вложено: {data.get('total_invested_value')}.")
        if data.get("total_market_value") is not None:
            parts.append(f"Текущая рыночная стоимость: {data.get('total_market_value')}.")
        if data.get("total_absolute_pnl") is not None:
            pnl_text = f"{data.get('total_absolute_pnl')}"
            if data.get("total_pnl_percent") is not None:
                pnl_text += f" ({data.get('total_pnl_percent')}%)"
            parts.append(f"Совокупный результат: {pnl_text}.")
        if data.get("profitable_positions") is not None and data.get("losing_positions") is not None:
            parts.append(f"В плюсе {data.get('profitable_positions')} позиций, в минусе {data.get('losing_positions')}.")

        parts.append("Это информационный обзор, а не инвестиционная рекомендация.")
        return " ".join(parts)

    def _news_explain_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("news_found"):
            return "Новости по инструменту не найдены."

        ticker = data.get("ticker")
        items = data.get("items", [])
        parts = [f"По инструменту {ticker} найден новостной контекст."]
        if items:
            parts.append(f"Количество найденных материалов: {len(items)}.")
        return " ".join(parts)

    def _risk_return_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        parts = [
            f"Предварительная оценка портфеля: позиций {data.get('positions_count', 0)}, "
            f"в плюсе {data.get('profitable_positions', 0)}, в минусе {data.get('losing_positions', 0)}."
        ]
        if data.get("total_pnl_percent") is not None:
            parts.append(f"Текущий совокупный результат составляет {data.get('total_pnl_percent')}%.")
        parts.append("Для точной оценки риска нужна более детальная модель риска и исторических колебаний.")
        return " ".join(parts)

    def _benchmark_compare_answer(self, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        parts = []
        if data.get("positions_count") is not None:
            parts.append(f"В портфеле {data.get('positions_count')} позиций.")
        if data.get("total_pnl_percent") is not None:
            parts.append(f"Текущий совокупный результат портфеля: {data.get('total_pnl_percent')}%.")
        parts.append("Полноценное сравнение с бенчмарком требует отдельного индекса или эталонного портфеля.")
        return " ".join(parts)