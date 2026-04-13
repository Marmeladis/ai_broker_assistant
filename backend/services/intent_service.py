import re


class IntentService:
    def detect_intent(
        self,
        text: str,
        resolved_tickers: list[str] | None = None
    ) -> str:
        text_lower = (text or "").lower().replace("ё", "е").strip()
        resolved_tickers = resolved_tickers or []

        if self._looks_like_dividend_aristocrats_query(text_lower):
            return "dividend_aristocrats"

        if self._looks_like_dividend_ranking_query(text_lower):
            return "dividend_ranking_query"

        if self._looks_like_bond_ranking_query(text_lower):
            return "bond_ranking_query"

        if self._looks_like_bond_coupon_query(text_lower):
            return "bond_coupon_query"

        if self._looks_like_fx_price_query(text_lower):
            return "fx_price_query"

        if self._looks_like_expected_dividend_record_date_query(text_lower):
            return "expected_dividend_record_date_query"

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
            "есть ли сейчас смысл входить",
            "есть ли сейчас хороший вход",
        ]):
            return "buy_or_wait"

        if any(marker in text_lower for marker in [
            "точка входа",
            "вход по бумаге",
            "где лучше входить",
            "какой уровень входа",
            "на каком уровне покупать",
            "где вход",
            "хороший вход",
        ]):
            return "entry_point_analysis"

        if any(marker in text_lower for marker in [
            "теханализ",
            "технический анализ",
            "сделай теханализ",
            "покажи теханализ",
            "график",
            "динамика",
            "покажи динамику",
            "движение цены",
            "тренд",
            "какой тренд",
            "есть ли тренд",
            "сигнал",
            "есть ли сигнал",
            "торговый сигнал",
            "скользящ",
            "sma",
            "macd",
            "rsi",
        ]):
            return "technical_analysis"

        compare_markers = [
            "сравни",
            "сравнение",
            "что лучше",
            "чем отличается",
            "лучше чем",
            "или",
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
            "какой у меня сейчас результат",
            "я в плюсе или в минусе",
            "мой результат",
            "общий результат",
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
        ]):
            return "price_check"

        if resolved_tickers:
            return "simple_analysis"

        return "general_question"

    def _looks_like_dividend_aristocrats_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "дивидендные аристократы",
            "стабильно платят дивиденды",
            "платят дивиденды каждый год",
            "устойчивые дивиденды",
            "надежные дивидендные акции",
            "надежные дивидендные бумаги",
            "какие компании сейчас являются дивидендными аристократами",
        ])

    def _looks_like_dividend_ranking_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "топ дивиденд",
            "дивидендные акции",
            "акции с наибольшими дивидендами",
            "самые дивидендные акции",
            "самая высокая дивидендная доходность",
            "компании платят наибольшие дивиденды",
            "лучшие дивидендные бумаги",
            "какие акции платят наибольшие дивиденды",
            "за какие акции платят наибольшие дивиденды",
            "покажи топ дивидендных акций",
            "у каких компаний самая высокая дивдоходность",
        ])

    def _looks_like_bond_ranking_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "какие облигации самые доходные",
            "топ облигаций по купону",
            "облигации с высоким купоном",
            "облигации с наибольшим купоном",
            "самые доходные облигации",
            "рейтинг облигаций",
            "покажи облигации с высоким купоном",
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
        ])
        if self._looks_like_bond_ranking_query(text):
            return False
        return has_bond and has_coupon

    def _looks_like_fx_price_query(self, text: str) -> bool:
        has_currency = any(marker in text for marker in [
            "доллар",
            "евро",
            "юань",
            "usd",
            "eur",
            "cny",
            "usd/rub",
            "eur/rub",
            "cny/rub",
            "usdrub",
            "eurrub",
            "cnyrub",
            "валюта",
        ])
        has_price = any(marker in text for marker in [
            "сколько стоит",
            "какой курс",
            "курс",
            "цена",
            "котировка",
            "стоит",
        ])
        return has_currency and has_price

    def _looks_like_expected_dividend_record_date_query(self, text: str) -> bool:
        return any(marker in text for marker in [
            "когда будет дата отсечки",
            "когда будет отсечка",
            "отсечка в этом году",
            "дата отсечки в этом году",
            "когда ожидается отсечка",
            "когда будет дата закрытия реестра",
            "будет ли отсечка в этом году",
        ])

    def _looks_like_historical_dividend_query(self, text: str) -> bool:
        has_dividend = any(marker in text for marker in [
            "дивиденд",
            "дивиденды",
            "выплачивался последний дивиденд",
            "прошлый дивиденд",
            "последний дивиденд",
            "какой был дивиденд",
        ])
        has_year = bool(re.search(r"\b20\d{2}\b", text))
        has_history_marker = any(marker in text for marker in [
            "прошлый",
            "последний",
            "в 20",
            "за 20",
            "был",
            "выплачивался",
        ])
        return has_dividend and (has_year or has_history_marker)

    def _looks_like_expected_dividend_query(self, text: str) -> bool:
        has_dividend = "дивид" in text
        has_expected_marker = any(marker in text for marker in [
            "ожидается",
            "ожидаемый",
            "прогнозируется",
            "в этом году",
            "за 2025",
            "за 2026",
            "за 2027",
            "ожидается дивиденд",
            "будут ли дивиденды",
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