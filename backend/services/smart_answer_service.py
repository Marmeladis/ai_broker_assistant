from __future__ import annotations

from typing import Any


class SmartAnswerService:
    def build_answer(
        self,
        user_text: str,
        intent: str,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None = None,
        comparative_summary: dict[str, Any] | None = None,
    ) -> str | None:
        if intent == "dividend_ranking_query":
            return self._dividend_ranking_answer(analytics_result)

        if intent == "dividend_aristocrats":
            return self._dividend_aristocrats_answer(analytics_result)

        if intent == "bond_ranking_query":
            return self._bond_ranking_answer(analytics_result)

        if intent == "bond_coupon_query":
            return self._bond_coupon_answer(analytics_result)

        if intent == "fx_price_query":
            return self._fx_price_answer(analytics_result)

        if intent == "price_check":
            return self._price_answer(analytics_result)

        if intent == "technical_analysis":
            return self._technical_analysis_answer(analytics_result)

        if intent == "historical_dividend_query":
            return self._historical_dividend_answer(context, analytics_result)

        if intent == "expected_dividend_query":
            return self._expected_dividend_answer(context, analytics_result)

        if intent == "dividend_record_date_query":
            return self._dividend_record_date_answer(context, analytics_result)

        if intent == "expected_dividend_record_date_query":
            return self._expected_dividend_record_date_answer(context, analytics_result)

        if intent == "dividend_info":
            return self._dividend_info_answer(analytics_result)

        if intent == "historical_price_extremes_query":
            return self._historical_price_extremes_answer(analytics_result)

        if intent == "max_turnover_query":
            return self._max_turnover_answer(analytics_result)

        if intent == "buy_or_wait":
            return self._buy_or_wait_answer(analytics_result)

        if intent == "entry_point_analysis":
            return self._entry_point_answer(analytics_result)

        return None


    def _dividend_ranking_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось получить список акций с высокой дивидендной доходностью."

        parts = ["Топ акций по дивидендной доходности:"]

        for i, item in enumerate(items, 1):
            name = item.get("name") or item.get("ticker")
            ticker = item.get("ticker")
            dy = item.get("dividend_yield_percent")
            dividend_per_share = item.get("dividend_per_share")
            year = item.get("year")

            text = f"{i}. {name} ({ticker}) — дивдоходность {dy}%"
            if dividend_per_share is not None:
                text += f", дивиденд {dividend_per_share}"
            if year:
                text += f", последний подтверждённый контекст {year} года"
            parts.append(text)

        parts.append(
            "Важно: высокая дивидендная доходность не всегда означает низкий риск или устойчивость будущих выплат."
        )
        return "\n".join(parts)

    def _dividend_aristocrats_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось найти устойчивые дивидендные компании."

        parts = ["Компании с устойчивыми дивидендными выплатами:"]

        for i, item in enumerate(items, 1):
            name = item.get("name") or item.get("ticker")
            ticker = item.get("ticker")
            years = item.get("years")
            dividend_yield = item.get("dividend_yield")
            last_dividend_year = item.get("last_dividend_year")

            text = f"{i}. {name} ({ticker}) — {years} лет подряд"
            if dividend_yield is not None:
                text += f", текущая ориентировочная дивдоходность {dividend_yield}%"
            if last_dividend_year:
                text += f", последний подтверждённый дивидендный год {last_dividend_year}"
            parts.append(text)

        parts.append(
            "Такие компании обычно считаются более устойчивыми по дивидендной истории, но это не исключает рыночных и корпоративных рисков."
        )
        return "\n".join(parts)

    def _bond_ranking_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        items = data.get("items", [])

        if not items:
            return "Не удалось получить список облигаций с высоким купоном."

        parts = ["Топ облигаций по купонной ставке:"]

        for i, item in enumerate(items, 1):
            name = item.get("name") or item.get("ticker")
            ticker = item.get("ticker")
            coupon_percent = item.get("coupon_percent")
            coupon_value = item.get("coupon_value")

            text = f"{i}. {name} ({ticker})"
            if coupon_percent is not None:
                text += f" — {coupon_percent}%"
            if coupon_value is not None:
                text += f", купон {coupon_value}"
            parts.append(text)

        parts.append(
            "Обрати внимание: высокий купон часто связан с повышенным риском эмитента и ликвидности."
        )
        return "\n".join(parts)


    def _bond_coupon_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Данные по купонам облигации не найдены."

        bond_code = data.get("ticker") or data.get("bond_code") or data.get("secid")
        coupon_percent = data.get("coupon_percent")
        coupon_value = data.get("coupon_value")
        next_coupon_date = data.get("next_coupon_date")
        maturity_date = data.get("maturity_date")
        name = data.get("name")

        if not any([bond_code, coupon_percent, coupon_value, next_coupon_date, maturity_date, name]):
            return "Данные по купонам облигации не найдены."

        parts = []
        display_name = name or bond_code or "облигации"

        if coupon_value is not None or coupon_percent is not None:
            text = f"По облигации {display_name}"
            if coupon_value is not None:
                text += f" размер купона составляет {coupon_value}"
            if coupon_percent is not None:
                text += f", купонная ставка {coupon_percent}%"
            text += "."
            parts.append(text)

        if next_coupon_date:
            parts.append(f"Ближайшая дата выплаты купона: {next_coupon_date}.")
        if maturity_date:
            parts.append(f"Дата погашения: {maturity_date}.")

        if not parts:
            return "Данные по купонам облигации не найдены."

        return " ".join(parts)


    def _fx_price_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or data.get("price") is None:
            return "Не удалось найти актуальную цену по этой валюте."

        parts = [
            f"По валютной паре {data.get('display_name')} текущая цена составляет {data.get('price')}."
        ]

        if data.get("last_update_time"):
            parts.append(f"Время обновления: {data.get('last_update_time')}.")

        parts.append("Источник: MOEX.")
        return " ".join(parts)


    def _price_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or data.get("price") is None:
            return "Не удалось найти актуальную цену по этому инструменту."

        name = data.get("display_name") or data.get("ticker")
        price = data.get("price")
        source_name = data.get("source_name")
        recorded_at = data.get("recorded_at")

        parts = [f"По инструменту {name} текущая цена составляет {price}."]

        if source_name:
            parts.append(f"Источник: {source_name}.")
        if recorded_at:
            parts.append(f"Время обновления: {recorded_at}.")

        return " ".join(parts)

    def _technical_analysis_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data:
            return "Не удалось выполнить технический анализ по инструменту."

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
            parts.append(f"RSI(14): {round(float(rsi_14), 4)}.")
            if float(rsi_14) > 70:
                parts.append("Индикатор находится в зоне перекупленности.")
            elif float(rsi_14) < 30:
                parts.append("Индикатор находится в зоне перепроданности.")
        if support is not None:
            parts.append(f"Поддержка: {round(float(support), 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(float(resistance), 4)}.")
        if pattern:
            parts.append(f"Паттерн: {pattern}.")

        parts.append("Технический комментарий носит информационный характер.")
        return " ".join(parts)


    def _historical_dividend_answer(
        self,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None,
    ) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        requested_year = self._extract_requested_year(context, analytics_result)

        if not data or not data.get("dividend_found"):
            if requested_year:
                return f"По этой бумаге у меня сейчас нет подтверждённых данных по дивиденду за {requested_year} год."
            return "По этой бумаге у меня сейчас нет подтверждённых данных по последнему дивиденду."

        ticker = data.get("ticker")
        year = data.get("year")
        dividend_per_share = data.get("dividend_per_share")
        record_date = data.get("record_date")
        declared_date = data.get("declared_date")
        currency = data.get("currency")

        parts = []

        if requested_year:
            parts.append(
                f"По бумаге {ticker} за {requested_year} год найден дивиденд {dividend_per_share} {currency or ''}."
            )
        else:
            if year:
                parts.append(
                    f"Последний известный дивиденд по бумаге {ticker} составил {dividend_per_share} {currency or ''} за {year} год."
                )
            else:
                parts.append(
                    f"Последний известный дивиденд по бумаге {ticker} составил {dividend_per_share} {currency or ''}."
                )

        if record_date:
            parts.append(f"Дата отсечки: {record_date}.")
        if declared_date:
            parts.append(f"Дата решения: {declared_date}.")

        return " ".join(parts)

    def _expected_dividend_answer(
        self,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None,
    ) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        requested_year = self._extract_requested_year(context, analytics_result)

        if not data or not data.get("dividend_found"):
            if requested_year:
                return (
                    f"По текущим данным у меня нет подтверждённого дивидендного ориентира "
                    f"по этой бумаге за {requested_year} год."
                )
            return "По текущим данным у меня нет подтверждённого дивидендного ориентира по этой бумаге."

        ticker = data.get("ticker")
        year = data.get("year")
        dividend_per_share = data.get("dividend_per_share")
        record_date = data.get("record_date")
        declared_date = data.get("declared_date")
        currency = data.get("currency")
        is_expected_proxy = data.get("is_expected_proxy", False)

        parts = []

        if requested_year:
            parts.append(
                f"По текущим данным ориентир по дивиденду для бумаги {ticker} за {requested_year} год составляет {dividend_per_share} {currency or ''}."
            )
        else:
            if year:
                parts.append(
                    f"По текущим данным наиболее релевантный дивидендный ориентир по бумаге {ticker} составляет {dividend_per_share} {currency or ''} за {year} год."
                )
            else:
                parts.append(
                    f"По текущим данным наиболее релевантный дивидендный ориентир по бумаге {ticker} составляет {dividend_per_share} {currency or ''}."
                )

        if record_date:
            parts.append(f"Дата отсечки: {record_date}.")
        if declared_date:
            parts.append(f"Дата решения: {declared_date}.")
        if is_expected_proxy:
            parts.append("Это ориентир по доступным данным, а не гарантированное будущее решение по дивидендам.")

        return " ".join(parts)

    def _dividend_record_date_answer(
        self,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None,
    ) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        requested_year = self._extract_requested_year(context, analytics_result)

        if not data or not data.get("dividend_found") or not data.get("record_date"):
            if requested_year:
                return f"По этой бумаге у меня сейчас нет подтверждённой даты отсечки за {requested_year} год."
            return "По этой бумаге у меня сейчас нет подтверждённой даты отсечки."

        ticker = data.get("ticker")
        record_date = data.get("record_date")
        dividend_per_share = data.get("dividend_per_share")
        currency = data.get("currency")
        year = data.get("year")

        parts = []

        if requested_year:
            parts.append(f"По бумаге {ticker} дата отсечки за {requested_year} год: {record_date}.")
        else:
            if year:
                parts.append(f"Последняя известная дата отсечки по бумаге {ticker}: {record_date} (контекст {year} года).")
            else:
                parts.append(f"Последняя известная дата отсечки по бумаге {ticker}: {record_date}.")

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда в этом контексте: {dividend_per_share} {currency or ''}.")

        parts.append("Поступление дивидендов обычно ожидается в срок до 25 рабочих дней после даты закрытия реестра.")
        return " ".join(parts)

    def _expected_dividend_record_date_answer(
        self,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None,
    ) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        requested_year = self._extract_requested_year(context, analytics_result)

        if not data or not data.get("dividend_found") or not data.get("record_date"):
            if requested_year:
                return f"Подтверждённой даты отсечки по этой бумаге за {requested_year} год пока нет."
            return "Подтверждённой будущей даты отсечки по этой бумаге пока нет."

        ticker = data.get("ticker")
        record_date = data.get("record_date")
        dividend_per_share = data.get("dividend_per_share")
        currency = data.get("currency")
        is_expected_proxy = data.get("is_expected_proxy", False)

        parts = []
        if requested_year:
            parts.append(f"По текущим данным ориентир по дате отсечки для бумаги {ticker} за {requested_year} год: {record_date}.")
        else:
            parts.append(f"По текущим данным ориентир по ближайшей дате отсечки для бумаги {ticker}: {record_date}.")

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда в этом контексте: {dividend_per_share} {currency or ''}.")
        if is_expected_proxy:
            parts.append("Это ориентир по доступным данным, а не гарантированно утверждённая будущая отсечка.")

        return " ".join(parts)

    def _dividend_info_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("dividend_found"):
            return "По этой бумаге у меня сейчас нет подтверждённых данных по дивидендам."

        parts = ["По бумаге найдены дивидендные данные."]

        dividend_per_share = data.get("dividend_per_share")
        record_date = data.get("record_date")
        year = data.get("year")

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда: {dividend_per_share}.")
        if record_date:
            parts.append(f"Дата закрытия реестра: {record_date}.")
        if year:
            parts.append(f"Контекст выплаты: {year} год.")

        parts.append("Поступление дивидендов обычно ожидается в срок до 25 рабочих дней после даты закрытия реестра.")
        return " ".join(parts)


    def _historical_price_extremes_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("found"):
            return "Исторические экстремумы цены по выбранному периоду не найдены."

        ticker = data.get("ticker")
        min_price = data.get("min_price")
        min_price_date = data.get("min_price_date")
        max_price = data.get("max_price")
        max_price_date = data.get("max_price_date")

        parts = [f"По бумаге {ticker} за выбранный период найдены ценовые экстремумы."]

        if min_price is not None:
            parts.append(f"Минимальная цена была {min_price} на дату {min_price_date}.")
        if max_price is not None:
            parts.append(f"Максимальная цена была {max_price} на дату {max_price_date}.")

        return " ".join(parts)

    def _max_turnover_answer(self, analytics_result: dict[str, Any] | None) -> str:
        data = (analytics_result or {}).get("calculated_indicators", {})
        if not data or not data.get("found"):
            return "Данные по максимальному торговому обороту за выбранный период не найдены."

        ticker = data.get("ticker")
        max_turnover = data.get("max_turnover")
        turnover_date = data.get("turnover_date")

        return (
            f"По бумаге {ticker} максимальный торговый оборот за день "
            f"составил {max_turnover} на дату {turnover_date}."
        )


    def _buy_or_wait_answer(self, analytics_result: dict[str, Any] | None) -> str:
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
        dividend_context = data.get("dividend_context") or {}

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
            parts.append(f"RSI(14): {round(float(rsi_14), 4)}.")
        if support is not None:
            parts.append(f"Поддержка: {round(float(support), 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(float(resistance), 4)}.")

        if dividend_context.get("dividend_per_share") is not None:
            if dividend_context.get("record_date"):
                parts.append(f"Ближайшая известная дивидендная дата в контексте: {dividend_context.get('record_date')}.")
            if dividend_context.get("dividend_per_share") is not None:
                parts.append(f"Размер дивиденда в известном контексте: {dividend_context.get('dividend_per_share')}.")

        if decision == "buy_zone":
            parts.append("По текущим данным бумага выглядит относительно интересной для входа, но решение стоит принимать с учётом горизонта и риска.")
        elif decision == "wait_for_better_entry":
            parts.append("Более осторожный сценарий — дождаться более комфортной точки входа или отката.")
        elif decision == "neutral_wait":
            parts.append("Сигналы смешанные, поэтому без дополнительного подтверждения спешить с входом не обязательно.")

        parts.append("Это аналитический комментарий, а не персональная инвестиционная рекомендация.")
        return " ".join(parts)

    def _entry_point_answer(self, analytics_result: dict[str, Any] | None) -> str:
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
            parts.append(f"Поддержка: {round(float(support), 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(float(resistance), 4)}.")
        if trend:
            parts.append(f"Тренд: {trend}.")
        if signal:
            parts.append(f"Сигнал: {signal}.")
        if rsi_14 is not None:
            parts.append(f"RSI(14): {round(float(rsi_14), 4)}.")

        if entry_bias == "near_support":
            parts.append("Цена ближе к поддержке, поэтому точка входа выглядит более комфортной, чем у сопротивления.")
        elif entry_bias == "near_resistance":
            parts.append("Цена ближе к сопротивлению, поэтому вход на текущих уровнях выглядит более осторожным.")
        elif entry_bias == "mid_range":
            parts.append("Цена находится примерно в середине диапазона между поддержкой и сопротивлением.")

        return " ".join(parts)

    def _extract_requested_year(
        self,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None,
    ) -> int | None:
        data = (analytics_result or {}).get("calculated_indicators", {})
        year = data.get("year")
        try:
            return int(year) if year is not None else None
        except Exception:
            return None