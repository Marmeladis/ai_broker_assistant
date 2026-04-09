class IntentService:
    def detect_intent(
        self,
        text: str,
        resolved_tickers: list[str] | None = None
    ) -> str:
        text_lower = (text or "").lower().replace("ё", "е").strip()
        resolved_tickers = resolved_tickers or []

        # ---- dividends ----
        if any(marker in text_lower for marker in [
            "дивиденд",
            "дивиденды",
            "дивидендная доходность",
            "когда отсечка",
            "дата отсечки",
            "реестр",
            "закрытие реестра",
            "когда будут дивиденды",
            "какие дивиденды",
            "выплата дивидендов",
        ]):
            return "dividend_info"

        # ---- buy / wait / entry point ----
        if any(marker in text_lower for marker in [
            "стоит ли покупать",
            "покупать или подождать",
            "покупать сейчас или подождать",
            "стоит ли входить",
            "есть ли смысл покупать",
            "входить сейчас",
            "хороший ли сейчас вход",
            "точка входа",
            "когда лучше купить",
            "лучше купить сейчас",
            "пора ли покупать",
            "покупать эту бумагу",
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

        # ---- technical analysis ----
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

        # ---- multi compare intents ----
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

        # ---- portfolio analysis ----
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

        # ---- risk / return ----
        if any(marker in text_lower for marker in [
            "риск",
            "доходность",
            "риск и доходность",
            "насколько рискован",
            "какая доходность",
        ]):
            return "risk_return"

        # ---- benchmark compare ----
        if any(marker in text_lower for marker in [
            "сравни с индексом",
            "сравни с бенчмарком",
            "бенчмарк",
            "индекс мосбиржи",
            "imoex",
        ]):
            return "benchmark_compare"

        # ---- news ----
        if any(marker in text_lower for marker in [
            "новости",
            "объясни новости",
            "что по новостям",
            "новостной фон",
            "какие новости",
        ]):
            return "news_explain"

        # ---- scenario ----
        if any(marker in text_lower for marker in [
            "что будет если",
            "сценарий",
            "прогноз",
            "что может быть",
            "что дальше",
        ]):
            return "scenario_forecast"

        # ---- price ----
        if any(marker in text_lower for marker in [
            "цена",
            "сколько стоит",
            "котировка",
            "какая стоимость",
            "какая цена",
        ]):
            return "price_check"

        # ---- fallback ----
        if resolved_tickers:
            return "simple_analysis"

        return "general_question"