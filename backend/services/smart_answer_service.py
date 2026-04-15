class SmartAnswerService:
    def build_answer(
        self,
        user_text: str,
        intent: str,
        context: dict,
        analytics_result: dict | None = None,
        comparative_summary: dict | None = None
    ) -> str | None:
        if intent == "price_check":
            return self._price_answer(context, analytics_result)

        if intent == "portfolio_analysis":
            return self._portfolio_answer(context, analytics_result)

        if intent == "technical_analysis":
            return self._technical_analysis_answer(context, analytics_result)

        if intent == "dividend_info":
            return self._dividend_info_answer(context, analytics_result)

        if intent == "buy_or_wait":
            return self._buy_or_wait_answer(context, analytics_result)

        if intent == "entry_point_analysis":
            return self._entry_point_answer(context, analytics_result)

        if intent == "multi_price_compare":
            return self._multi_price_compare_answer(context)

        if intent == "multi_position_compare":
            return self._multi_position_compare_answer(context)

        if intent == "multi_news_compare":
            return self._multi_news_compare_answer(context)

        if intent == "multi_instrument_compare":
            return self._multi_instrument_compare_answer(context)

        return None

    def _price_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        market_context = context.get("market_context")
        position_metrics = context.get("position_market_metrics")

        if not market_context or not market_context.get("price_found"):
            return "Не удалось найти актуальную цену по этому инструменту."

        name = market_context.get("display_name") or market_context.get("ticker")
        price = market_context.get("price")
        source_name = market_context.get("source_name")
        recorded_at = market_context.get("recorded_at")

        parts = [f"По инструменту {name} текущая цена составляет {price}."]

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

    def _portfolio_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        positions_count = data.get("positions_count", 0)
        invested = data.get("total_invested_value")
        market_value = data.get("total_market_value")
        pnl = data.get("total_absolute_pnl")
        pnl_percent = data.get("total_pnl_percent")
        profitable = data.get("profitable_positions")
        losing = data.get("losing_positions")

        if positions_count == 0:
            return "Портфель пока пуст."

        parts = [f"В портфеле сейчас {positions_count} позиций."]

        if invested is not None:
            parts.append(f"Суммарно вложено: {invested}.")
        if market_value is not None:
            parts.append(f"Текущая рыночная стоимость: {market_value}.")
        if pnl is not None:
            pnl_text = f"{pnl}"
            if pnl_percent is not None:
                pnl_text += f" ({pnl_percent}%)"
            parts.append(f"Совокупный результат: {pnl_text}.")
        if profitable is not None and losing is not None:
            parts.append(f"В плюсе {profitable} позиций, в минусе {losing}.")

        parts.append("Это информационный обзор, а не инвестиционная рекомендация.")
        return " ".join(parts)

    def _technical_analysis_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return None

        trend = data.get("trend")
        signal = data.get("signal")
        rsi_14 = data.get("rsi_14")
        support = data.get("support")
        resistance = data.get("resistance")
        last_price = data.get("last_price")
        pattern = data.get("pattern")

        parts = []

        if last_price is not None:
            parts.append(f"Последняя цена: {last_price}.")
        if trend:
            parts.append(f"Текущий тренд: {trend}.")
        if signal:
            parts.append(f"Сигнал: {signal}.")
        if rsi_14 is not None:
            parts.append(f"RSI(14): {round(rsi_14, 4)}.")
            if rsi_14 > 70:
                parts.append("Индикатор находится в зоне перекупленности.")
            elif rsi_14 < 30:
                parts.append("Индикатор находится в зоне перепроданности.")
        if support is not None:
            parts.append(f"Поддержка: {round(support, 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(resistance, 4)}.")
        if pattern:
            parts.append(f"Паттерн: {pattern}.")

        parts.append("Технический комментарий носит информационный характер.")
        return " ".join(parts)

    def _dividend_info_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("dividend_found"):
            return "По этой бумаге у меня сейчас нет подтверждённых данных по дивидендам."

        parts = ["По бумаге найдены дивидендные данные."]

        dividend_per_share = data.get("dividend_per_share")
        record_date = data.get("record_date")
        payment_timing_note = data.get("payment_timing_note")
        dividend_yield_percent = data.get("dividend_yield_percent")

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда: {dividend_per_share}.")
        if record_date:
            parts.append(f"Дата закрытия реестра: {record_date}.")
        if payment_timing_note:
            parts.append("Дивиденды обычно поступают в срок до месяца после даты закрытия реестра.")
        if dividend_yield_percent is not None:
            parts.append(f"Оценочная дивидендная доходность: {dividend_yield_percent}%.")

        parts.append("Если цель — дивидендная идея, важно учитывать дату закрытия реестра заранее.")
        return " ".join(parts)

    def _buy_or_wait_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Недостаточно данных, чтобы оценить, покупать сейчас или подождать."

        decision = data.get("decision")
        summary = data.get("summary")
        current_price = data.get("current_price")
        trend = data.get("trend")
        signal = data.get("signal")
        rsi_14 = data.get("rsi_14")
        support = data.get("support")
        resistance = data.get("resistance")
        dividend_context = data.get("dividend_context")
        position_metrics = data.get("position_market_metrics")

        parts = []

        if summary:
            parts.append(summary)

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

        if dividend_context and dividend_context.get("dividend_found"):
            record_date = dividend_context.get("record_date")
            dividend_yield_percent = dividend_context.get("dividend_yield_percent")
            if record_date:
                parts.append(f"Ближайшая дивидендная дата в контексте: {record_date}.")
            if dividend_yield_percent is not None:
                parts.append(f"Оценочная дивидендная доходность: {dividend_yield_percent}%.")

        if position_metrics:
            pnl = position_metrics.get("absolute_pnl")
            pnl_percent = position_metrics.get("pnl_percent")
            if pnl is not None:
                pnl_text = f"{pnl}"
                if pnl_percent is not None:
                    pnl_text += f" ({pnl_percent}%)"
                parts.append(f"По текущей позиции результат: {pnl_text}.")

        if decision == "buy_zone":
            parts.append("По текущим данным бумага выглядит относительно интересной для входа, но решение стоит принимать с учётом горизонта и риска.")
        elif decision == "wait_for_better_entry":
            parts.append("Более осторожный сценарий — дождаться более комфортной точки входа или отката.")
        elif decision == "neutral_wait":
            parts.append("Сигналы смешанные, поэтому без дополнительного подтверждения спешить с входом не обязательно.")

        parts.append("Это аналитический комментарий, а не персональная инвестиционная рекомендация.")
        return " ".join(parts)

    def _entry_point_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Недостаточно данных для анализа точки входа."

        summary = data.get("summary")
        entry_bias = data.get("entry_bias")
        current_price = data.get("current_price")
        support = data.get("support")
        resistance = data.get("resistance")
        trend = data.get("trend")
        signal = data.get("signal")
        rsi_14 = data.get("rsi_14")

        parts = []
        if summary:
            parts.append(summary)
        if current_price is not None:
            parts.append(f"Текущая цена: {current_price}.")
        if support is not None:
            parts.append(f"Поддержка: {round(support, 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(resistance, 4)}.")
        if trend:
            parts.append(f"Тренд: {trend}.")
        if signal:
            parts.append(f"Сигнал: {signal}.")
        if rsi_14 is not None:
            parts.append(f"RSI(14): {round(rsi_14, 4)}.")

        if entry_bias == "near_support":
            parts.append("Цена ближе к поддержке, поэтому точка входа выглядит более комфортной, чем у сопротивления.")
        elif entry_bias == "near_resistance":
            parts.append("Цена ближе к сопротивлению, поэтому вход на текущих уровнях выглядит более осторожным.")
        elif entry_bias == "mid_range":
            parts.append("Цена находится примерно в середине диапазона между поддержкой и сопротивлением.")

        return " ".join(parts)

    def _multi_price_compare_answer(self, context: dict) -> str | None:
        items = context.get("multi_market_context", [])
        if len(items) < 2:
            return None

        parts = ["Сравнение цен по инструментам:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            if item.get("price_found"):
                parts.append(f"{name}: {item.get('price')}.")
            else:
                parts.append(f"{name}: цена не найдена.")
        return " ".join(parts)

    def _multi_position_compare_answer(self, context: dict) -> str | None:
        items = context.get("multi_position_market_metrics", [])
        if len(items) < 2:
            return None

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

    def _multi_news_compare_answer(self, context: dict) -> str | None:
        items = context.get("multi_news_context", [])
        if len(items) < 2:
            return None

        parts = ["Сравнение новостного фона:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            count = len(item.get("items", [])) if item.get("news_found") else 0
            parts.append(f"{name}: новостей {count}.")
        return " ".join(parts)

    def _multi_instrument_compare_answer(self, context: dict) -> str | None:
        comparison_context = context.get("comparison_context")
        if not comparison_context or not comparison_context.get("comparison_found"):
            return None

        items = comparison_context.get("items", [])
        best_item = comparison_context.get("best_item")
        summary = comparison_context.get("summary")

        if len(items) < 2:
            return None

        parts = [summary]

        for item in items:
            name = item.get("display_name") or item.get("ticker")
            score = item.get("comparison_score")
            ta = item.get("technical_analysis_context") or {}
            dividend = item.get("dividend_context") or {}
            entry_ctx = item.get("entry_point_context") or {}
            buy_wait = item.get("buy_or_wait_context") or {}

            text = f"{name}: score {score}"

            trend = ta.get("trend")
            signal = ta.get("signal")
            if trend:
                text += f", тренд {trend}"
            if signal:
                text += f", сигнал {signal}"

            dividend_yield = dividend.get("dividend_yield_percent")
            if dividend_yield is not None:
                text += f", дивдоходность {dividend_yield}%"

            entry_bias = entry_ctx.get("entry_bias")
            if entry_bias == "near_support":
                text += ", цена ближе к поддержке"
            elif entry_bias == "near_resistance":
                text += ", цена ближе к сопротивлению"

            decision = buy_wait.get("decision")
            if decision == "buy_zone":
                text += ", сценарий входа выглядит относительно комфортным"
            elif decision == "wait_for_better_entry":
                text += ", по входу разумнее дождаться лучшей точки"

            text += "."
            parts.append(text)

        if best_item:
            best_name = best_item.get("display_name") or best_item.get("ticker")
            parts.append(f"На текущем наборе сигналов сильнее выглядит {best_name}.")

        parts.append("Это сравнительный аналитический комментарий, а не инвестиционная рекомендация.")
        return " ".join(parts)