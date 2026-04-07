class SmartAnswerService:
    def build_answer(
        self,
        user_text: str,
        intent: str,
        context: dict,
        analytics_result: dict | None = None,
        comparative_summary: dict | None = None
    ) -> str | None:
        if intent == "portfolio_analysis":
            return self._portfolio_answer(context, analytics_result)

        if intent == "risk_return":
            return self._risk_return_answer(context, analytics_result)

        if intent == "price_check":
            return self._price_answer(context, analytics_result)

        if intent == "news_explain":
            return self._news_answer(context, analytics_result)

        if intent == "multi_price_compare":
            return self._multi_price_compare_answer(context, analytics_result, comparative_summary)

        if intent == "multi_news_compare":
            return self._multi_news_compare_answer(context, analytics_result, comparative_summary)

        if intent == "multi_position_compare":
            return self._multi_position_compare_answer(context, analytics_result, comparative_summary)

        if intent == "multi_instrument_compare":
            return self._multi_instrument_compare_answer(context, analytics_result, comparative_summary)

        if intent == "benchmark_compare":
            return self._benchmark_compare_answer(context, analytics_result)

        return None

    def _portfolio_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        metrics = context.get("portfolio_metrics", {})
        if not metrics or metrics.get("positions_count", 0) == 0:
            return "Портфель сейчас пуст. Чтобы я мог сделать обзор, сначала добавь позиции и рыночные данные."

        positions_count = metrics.get("positions_count")
        invested = metrics.get("total_invested_value")
        market_value = metrics.get("total_market_value")
        total_pnl = metrics.get("total_absolute_pnl")
        total_pnl_percent = metrics.get("total_pnl_percent")
        profitable = metrics.get("profitable_positions")
        losing = metrics.get("losing_positions")
        unknown = metrics.get("unknown_positions")

        parts = [
            f"Сейчас в портфеле {positions_count} позиций."
        ]

        if invested is not None:
            parts.append(f"Суммарно вложено: {invested}.")
        if market_value is not None:
            parts.append(f"Текущая рыночная стоимость: {market_value}.")
        if total_pnl is not None:
            pnl_text = f"{total_pnl}"
            if total_pnl_percent is not None:
                pnl_text += f" ({total_pnl_percent}%)"
            parts.append(f"Общий результат по портфелю: {pnl_text}.")
        parts.append(
            f"Позиции в плюсе: {profitable}, в минусе: {losing}, без актуальной цены: {unknown}."
        )
        parts.append("Это информационный обзор, не инвестиционная рекомендация.")

        return " ".join(parts)

    def _risk_return_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        if not analytics_result:
            return None

        data = analytics_result.get("calculated_indicators", {})
        positions_count = data.get("positions_count")
        profitable = data.get("profitable_positions")
        losing = data.get("losing_positions")
        total_pnl_percent = data.get("total_pnl_percent")

        parts = []
        if positions_count is not None:
            parts.append(f"Предварительная оценка по портфелю: позиций {positions_count}.")
        if profitable is not None and losing is not None:
            parts.append(f"В плюсе {profitable} позиций, в минусе {losing}.")
        if total_pnl_percent is not None:
            parts.append(f"Текущий совокупный результат составляет {total_pnl_percent}%.")
        parts.append("Для более точной оценки риска нужна историческая динамика цен и волатильности.")

        return " ".join(parts)

    def _price_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        market = context.get("market_context")
        if not market:
            return "Я не смог определить инструмент в запросе. Напиши тикер или название бумаги."

        if not market.get("price_found"):
            return f"По инструменту {market.get('display_name', market.get('ticker'))} цена в базе не найдена."

        name = market.get("display_name", market.get("ticker"))
        price = market.get("price")
        source = market.get("source_name")
        recorded_at = market.get("recorded_at")

        parts = [
            f"По инструменту {name} текущая цена: {price}."
        ]

        if source:
            parts.append(f"Источник: {source}.")
        if recorded_at:
            parts.append(f"Время записи: {recorded_at}.")

        pos_metrics = context.get("position_market_metrics")
        if pos_metrics:
            market_value = pos_metrics.get("market_value")
            pnl = pos_metrics.get("absolute_pnl")
            pnl_percent = pos_metrics.get("pnl_percent")

            if market_value is not None:
                parts.append(f"Текущая стоимость твоей позиции: {market_value}.")
            if pnl is not None:
                pnl_text = f"{pnl}"
                if pnl_percent is not None:
                    pnl_text += f" ({pnl_percent}%)"
                parts.append(f"Текущий результат по позиции: {pnl_text}.")

        return " ".join(parts)

    def _news_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        news = context.get("news_context")
        if not news:
            return "Я не смог определить инструмент для поиска новостей."

        name = news.get("display_name", news.get("ticker"))

        if not news.get("news_found"):
            return f"По инструменту {name} новости в текущей базе не найдены."

        items = news.get("items", [])
        count = len(items)
        latest_title = items[0]["title"] if items else None

        parts = [f"По инструменту {name} найдено новостей: {count}."]
        if latest_title:
            parts.append(f"Последняя новость: «{latest_title}».")

        if context.get("position_context"):
            parts.append("У тебя есть позиция по этому инструменту, поэтому новостной фон напрямую важен для оценки ситуации.")

        parts.append("Если хочешь, я могу отдельно разобрать смысл этой новости и возможное влияние на бумагу.")

        return " ".join(parts)

    def _multi_price_compare_answer(self, context: dict, analytics_result: dict | None, comparative_summary: dict | None) -> str | None:
        items = context.get("multi_market_context", [])
        if not items:
            return None

        parts = ["Сравнение цен по инструментам:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            if item.get("price_found"):
                parts.append(f"{name}: {item.get('price')}.")
            else:
                parts.append(f"{name}: цена не найдена.")

        if comparative_summary and comparative_summary.get("summary_text"):
            parts.append(comparative_summary["summary_text"])

        return " ".join(parts)

    def _multi_news_compare_answer(self, context: dict, analytics_result: dict | None, comparative_summary: dict | None) -> str | None:
        items = context.get("multi_news_context", [])
        if not items:
            return None

        parts = ["Сравнение новостного фона:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            count = len(item.get("items", [])) if item.get("news_found") else 0
            parts.append(f"{name}: новостей {count}.")

        if comparative_summary and comparative_summary.get("summary_text"):
            parts.append(comparative_summary["summary_text"])

        return " ".join(parts)

    def _multi_position_compare_answer(self, context: dict, analytics_result: dict | None, comparative_summary: dict | None) -> str | None:
        items = context.get("multi_position_market_metrics", [])
        if not items:
            return "Я нашёл несколько инструментов, но не нашёл достаточных данных по позициям для сравнения."

        parts = ["Сравнение твоих позиций:"]
        for item in items:
            ticker = item.get("ticker")
            market_value = item.get("market_value")
            pnl = item.get("absolute_pnl")
            pnl_percent = item.get("pnl_percent")

            text = f"{ticker}:"
            if market_value is not None:
                text += f" стоимость {market_value},"
            if pnl is not None:
                text += f" результат {pnl}"
                if pnl_percent is not None:
                    text += f" ({pnl_percent}%)"
            text += "."
            parts.append(text)

        if comparative_summary and comparative_summary.get("summary_text"):
            parts.append(comparative_summary["summary_text"])

        return " ".join(parts)

    def _multi_instrument_compare_answer(self, context: dict, analytics_result: dict | None, comparative_summary: dict | None) -> str | None:
        parts = ["Я подготовил сравнение инструментов по доступному контексту."]

        if comparative_summary and comparative_summary.get("summary_text"):
            parts.append(comparative_summary["summary_text"])

        return " ".join(parts)

    def _benchmark_compare_answer(self, context: dict, analytics_result: dict | None) -> str | None:
        if not analytics_result:
            return None

        data = analytics_result.get("calculated_indicators", {})
        positions_count = data.get("positions_count")
        total_pnl_percent = data.get("total_pnl_percent")

        parts = []
        if positions_count is not None:
            parts.append(f"В портфеле {positions_count} позиций.")
        if total_pnl_percent is not None:
            parts.append(f"Текущий совокупный результат портфеля: {total_pnl_percent}%.")
        parts.append("Для полноценного сравнения с бенчмарком нужно подключить эталонный индекс или набор целевых метрик.")

        return " ".join(parts)