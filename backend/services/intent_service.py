class IntentService:
    def detect_intent(self, text: str, resolved_tickers: list[str] | None = None) -> str:
        text_lower = text.lower().strip().replace("ё", "е")
        resolved_tickers = resolved_tickers or []
        is_multi = len(resolved_tickers) >= 2

        # technical analysis
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
        ]):
            return "technical_analysis"

        # multi-comparison intents
        if is_multi:
            if any(marker in text_lower for marker in [
                "новост",
                "объясни новост",
                "какие новости",
                "сравни новости",
            ]):
                return "multi_news_compare"

            if any(marker in text_lower for marker in [
                "цен",
                "котиров",
                "курс",
                "сколько стоит",
                "сравни цену",
                "сравни котировки",
            ]):
                return "multi_price_compare"

            if any(marker in text_lower for marker in [
                "позиц",
                "что с моими пози",
                "что с моей пози",
                "мой результат",
                "мои бумаги",
                "по моим бумагам",
                "в плюсе",
                "в минусе",
                "результат",
                "pnl",
            ]):
                return "multi_position_compare"

            if any(marker in text_lower for marker in [
                "сравни",
                "сравнение",
                "что лучше",
                "лучше выглядит",
                "какой лучше",
                "какая бумага лучше",
            ]):
                return "multi_instrument_compare"

        # generic comparison
        if any(marker in text_lower for marker in [
            "сравни",
            "сравнение",
            "бенчмарк",
            "индекс",
            "что лучше",
            "лучше выглядит",
        ]):
            return "benchmark_compare"

        # price
        if any(marker in text_lower for marker in [
            "цена",
            "котиров",
            "сколько стоит",
            "курс",
            "текущая цена",
        ]):
            return "price_check"

        # news
        if any(marker in text_lower for marker in [
            "новост",
            "объясни новост",
            "что значит новост",
            "влияние новост",
        ]):
            return "news_explain"

        # portfolio / positions
        if any(marker in text_lower for marker in [
            "портфел",
            "позиц",
            "актив",
            "мой результат",
            "общий результат",
            "результат по портфел",
            "что с моими пози",
            "что с моей пози",
        ]):
            return "portfolio_analysis"

        # risk / return
        if any(marker in text_lower for marker in [
            "риск",
            "доходност",
            "волатиль",
            "просадк",
            "в плюсе",
            "в минусе",
            "прибыл",
            "убыт",
            "pnl",
            "сколько я заработал",
            "сколько заработал",
        ]):
            return "risk_return"

        # scenario
        if any(marker in text_lower for marker in [
            "сценари",
            "прогноз",
            "что будет",
            "если рынок",
        ]):
            return "scenario_forecast"

        # generic analysis
        if any(marker in text_lower for marker in [
            "аналитик",
            "проанализиру",
            "анализ",
        ]):
            return "simple_analysis"

        return "general_question"