import re


class IntentService:
    def detect_intent(
        self,
        text: str,
        resolved_tickers: list[str] | None = None
    ) -> str:
        text_lower = (text or "").lower().replace("ё", "е").strip()
        resolved_tickers = resolved_tickers or []

        if self._looks_like_fx_price_query(text_lower):
            return "fx_price_query"

        if self._looks_like_dividend_calendar_query(text_lower):
            return "expected_dividend_query"

        if self._looks_like_bond_ranking_query(text_lower):
            return "bond_ranking"

        if self._looks_like_dividend_aristocrats_query(text_lower):
            return "dividend_aristocrats"

        if self._looks_like_dividend_ranking_query(text_lower):
            return "dividend_ranking_query"

        if self._looks_like_bond_coupon_query(text_lower):
            return "bond_coupon_query"

        if self._looks_like_historical_dividend_query(text_lower):
            return "historical_dividend_query"

        if self._looks_like_expected_dividend_query(text_lower):
            return "expected_dividend_query"

        if self._looks_like_dividend_record_date_query(text_lower):
            return "dividend_record_date_query"

        if any(marker in text_lower for marker in [
            "дивиденд",
            "дивиденды",
            "дивидендная доходность",
            "выплата дивидендов",
        ]):
            return "dividend_info"

        if self._looks_like_price_extremes_query(text_lower):
            return "historical_price_extremes_query"

        if self._looks_like_max_turnover_query(text_lower):
            return "max_turnover_query"

        if any(marker in text_lower for marker in [
            "стоит ли покупать",
            "покупать или подождать",
            "покупать сейчас или подождать",
            "стоит ли входить",
            "есть ли смысл покупать",
            "входить сейчас",
            "хороший ли сейчас вход",
            "когда лучше купить",
            "лучше купить сейчас",
            "пора ли покупать",
            "покупать эту бумагу",
            "стоит ли его сейчас покупать",
            "стоит ли ее сейчас покупать",
        ]):
            return "buy_or_wait"

        if any(marker in text_lower for marker in [
            "точка входа",
            "вход по бумаге",
            "где лучше входить",
            "какой уровень входа",
            "на каком уровне покупать",
            "где вход",
        ]):
            return "entry_point_analysis"

        if any(marker in text_lower for marker in [
            "теханализ",
            "технический анализ",
            "сделай теханализ",
            "покажи теханализ",
            "какой сейчас тренд",
            "какой тренд",
            "есть ли тренд",
            "сигнал",
            "есть ли сигнал",
            "торговый сигнал",
            "скользящ",
            "sma",
            "macd",
            "rsi",
            "график",
            "динамика",
            "движение цены",
        ]):
            return "technical_analysis"

        compare_markers = [
            "сравни",
            "сравнение",
            "что лучше",
            "чем отличается",
            "лучше чем",
            "vs",
        ]

        if len(resolved_tickers) >= 2 or any(marker in text_lower for marker in compare_markers):
            if any(marker in text_lower for marker in [
                "цена",
                "котировка",
                "сколько стоит",
            ]):
                return "multi_price_compare"

            if any(marker in text_lower for marker in [
                "новости",
                "новостной фон",
            ]):
                return "multi_news_compare"

            if any(marker in text_lower for marker in [
                "позиции",
                "мои позиции",
                "мой результат",
                "мой портфель",
                "в плюсе",
                "в минусе",
            ]):
                return "multi_position_compare"

            return "multi_instrument_compare"

        if any(marker in text_lower for marker in [
            "мой портфель",
            "портфель",
            "мои позиции",
            "проанализируй портфель",
            "что с моим портфелем",
            "что с моими позициями",
            "как дела у портфеля",
        ]):
            return "portfolio_analysis"

        if any(marker in text_lower for marker in [
            "риск",
            "доходность",
            "риск и доходность",
            "насколько рискован",
            "какая доходность",
        ]):
            return "risk_return"

        if any(marker in text_lower for marker in [
            "сравни с индексом",
            "сравни с бенчмарком",
            "бенчмарк",
            "индекс мосбиржи",
            "imoex",
        ]):
            return "benchmark_compare"

        if any(marker in text_lower for marker in [
            "новости",
            "объясни новости",
            "что по новостям",
            "новостной фон",
            "какие новости",
        ]):
            return "news_explain"

        if any(marker in text_lower for marker in [
            "что будет если",
            "сценарий",
            "прогноз",
            "что может быть",
            "что дальше",
        ]):
            return "scenario_forecast"

        if any(marker in text_lower for marker in [
            "цена",
            "сколько стоит",
            "котировка",
            "какая стоимость",
            "какая цена",
            "а сколько он стоит",
            "а сколько она стоит",
        ]):
            return "price_check"

        if resolved_tickers:
            return "simple_analysis"

        return "general_question"

    def _looks_like_dividend_calendar_query(self, text: str) -> bool:

        has_year_2026 = "2026" in text

        has_dividend_word = any(marker in text for marker in [
            "дивиденд",
            "дивиденды",
            "дивидендов",
            "дивидендам",
            "дивдоходность",
        ])

        has_calendar_date_marker = any(marker in text for marker in [
            "дата покупки под дивиденды",
            "купить под дивиденды",
            "до какой даты купить",
            "когда купить под дивиденды",
            "t+1",
            "дата отсечки",
            "дата закрытия реестра",
            "отсечка по дивидендам",
            "закрытие реестра",
        ])

        has_future_dividend_marker = any(marker in text for marker in [
            "какой будет дивиденд",
            "какой ожидается дивиденд",
            "ожидаемый дивиденд",
            "прогноз дивиденда",
            "дивиденд в 2026",
            "дивиденды в 2026",
            "дивиденды по",
            "дивиденды",
            "последний дивиденд",
            "дивиденд в этом году",
            "огда дивиденд"
        ])

        return has_year_2026 and (
            has_calendar_date_marker
            or (has_dividend_word and has_future_dividend_marker)
        )

    def _looks_like_fx_price_query(self, text: str) -> bool:
        has_currency = any(marker in text for marker in [
            "доллар",
            "евро",
            "юань",
            "рубль",
            "usd",
            "eur",
            "cny",
            "rub",
            "валюта",
            "курс валют",
            "usd/rub",
            "eur/rub",
            "cny/rub",
        ])
        has_price = any(marker in text for marker in [
            "сколько стоит",
            "какой курс",
            "курс",
            "цена",
            "котировка",
            "стоит",
            "покажи курс",
        ])
        return (has_currency and has_price) or text in {"usd rub", "eur rub", "cny rub"}

    def _looks_like_dividend_ranking_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "топ дивиденд",
            "дивидендные акции",
            "акции с наибольшими дивидендами",
            "самые дивидендные акции",
            "самая высокая дивидендная доходность",
            "компании платят наибольшие дивиденды",
            "лучшие дивидендные бумаги",
            "топ дивидендных акций",
        ])

    def _looks_like_dividend_aristocrats_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "дивидендные аристократы",
            "аристократы",
            "стабильно платят дивиденды",
            "платят дивиденды каждый год",
            "каждый год платят дивиденды",
            "кто платит дивиденды каждый год",
            "устойчивые дивиденды",
            "надежные дивидендные акции",
            "надежные дивидендные компании",
        ])

    def _looks_like_bond_ranking_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "дай мне список облигаций с наибольшим купоном",
            "список облигаций с наибольшим купоном",
            "облигации с наибольшим купоном",
            "облигации с высоким купоном",
            "самые доходные облигации",
            "топ облигаций",
            "рейтинг облигаций",
            "облигации с самым высоким купоном",
        ])

    def _looks_like_bond_coupon_query(self, text: str) -> bool:
        has_bond = any(marker in text for marker in [
            "облигац",
            "облигации",
            "бонды",
            "выпуск",
            "isin",
            "ru000",
        ])
        has_coupon = any(marker in text for marker in [
            "купон",
            "размер купона",
            "последний купон",
            "следующий купон",
            "купон платился",
            "расписание купонов",
            "когда следующий купон",
            "покажи расписание купонов",
        ])
        return has_bond and has_coupon

    def _looks_like_historical_dividend_query(self, text: str) -> bool:
        has_dividend = any(marker in text for marker in [
            "дивиденд",
            "дивиденды",
            "прошлый дивиденд",
            "последний дивиденд",
            "выплачивался",
            "когда выплачивался",
        ])

        has_year = bool(re.search(r"\b20\d{2}\b", text))

        has_past_marker = any(marker in text for marker in [
            "прошлый",
            "последний",
            "выплачивался",
            "был",
            "когда был",
            "когда выплачивался",
        ])

        return has_dividend and has_year and has_past_marker

    def _looks_like_expected_dividend_query(self, text: str) -> bool:
        has_dividend = "дивид" in text
        has_expected_marker = any(marker in text for marker in [
            "ожидается",
            "ожидаемый",
            "прогнозируется",
            "ожидается дивиденд",
            "какой ожидается дивиденд",
            "какой будет дивиденд",
            "будет дивиденд",
            "за 2025",
            "за 2026",
        ])
        return has_dividend and has_expected_marker

    def _looks_like_dividend_record_date_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "дата отсечки",
            "когда отсечка",
            "закрытие реестра",
            "дата закрытия реестра",
            "реестр по дивидендам",
        ])

    def _looks_like_price_extremes_query(self, text: str) -> bool:
        has_price = any(marker in text for marker in [
            "минимальная цена",
            "максимальная цена",
            "минимум",
            "максимум",
            "самая низкая цена",
            "самая высокая цена",
            "low",
            "high",
        ])
        has_period = any(marker in text for marker in [
            "год назад",
            "за год",
            "за месяц",
            "за 3 месяца",
            "за 6 месяцев",
            "за период",
            "год",
            "месяц",
            "полгода",
        ]) or bool(re.search(r"\b20\d{2}\b", text))
        return has_price and has_period

    def _looks_like_max_turnover_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "максимальный торговый оборот",
            "максимальный оборот",
            "самый большой оборот",
            "наибольший оборот",
            "максимальный объем торгов",
            "максимальный обьем торгов",
        ])

