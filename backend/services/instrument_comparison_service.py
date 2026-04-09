class InstrumentComparisonService:
    """
    Сравнение нескольких инструментов по:
    - цене
    - тренду / сигналу
    - RSI
    - точке входа
    - дивидендам
    - позиции пользователя
    """

    def build_comparison(self, items: list[dict]) -> dict:
        """
        items = [
            {
                "ticker": ...,
                "display_name": ...,
                "market_context": ...,
                "technical_analysis_context": ...,
                "dividend_context": ...,
                "position_market_metrics": ...,
                "entry_point_context": ...,
                "buy_or_wait_context": ...,
            }
        ]
        """
        if not items:
            return {
                "comparison_found": False,
                "items": [],
                "summary": "Недостаточно данных для сравнения инструментов."
            }

        scored_items = []
        for item in items:
            score = 0
            reasons = []

            ta = item.get("technical_analysis_context") or {}
            dividend = item.get("dividend_context") or {}
            entry_ctx = item.get("entry_point_context") or {}
            buy_wait = item.get("buy_or_wait_context") or {}

            trend = ta.get("trend")
            signal = ta.get("signal")
            rsi = ta.get("rsi_14")
            dividend_yield = dividend.get("dividend_yield_percent")
            entry_bias = entry_ctx.get("entry_bias")
            decision = buy_wait.get("decision")

            if trend == "uptrend":
                score += 2
                reasons.append("uptrend")
            elif trend == "downtrend":
                score -= 2
                reasons.append("downtrend")

            if signal == "bullish":
                score += 2
                reasons.append("bullish_signal")
            elif signal == "bearish":
                score -= 2
                reasons.append("bearish_signal")

            if rsi is not None:
                if 40 <= rsi <= 65:
                    score += 1
                    reasons.append("rsi_balanced")
                elif rsi > 70:
                    score -= 1
                    reasons.append("rsi_overbought")
                elif rsi < 30:
                    score += 0
                    reasons.append("rsi_oversold")

            if entry_bias == "near_support":
                score += 2
                reasons.append("near_support")
            elif entry_bias == "near_resistance":
                score -= 1
                reasons.append("near_resistance")

            if decision == "buy_zone":
                score += 2
                reasons.append("buy_zone")
            elif decision == "wait_for_better_entry":
                score -= 1
                reasons.append("wait_for_better_entry")

            if dividend_yield is not None:
                if dividend_yield >= 10:
                    score += 2
                    reasons.append("high_dividend_yield")
                elif dividend_yield >= 6:
                    score += 1
                    reasons.append("solid_dividend_yield")

            scored_item = {
                **item,
                "comparison_score": score,
                "comparison_reasons": reasons
            }
            scored_items.append(scored_item)

        scored_items.sort(key=lambda x: x.get("comparison_score", 0), reverse=True)

        best_item = scored_items[0] if scored_items else None

        if best_item:
            best_name = best_item.get("display_name") or best_item.get("ticker")
            summary = f"На текущем наборе сигналов сильнее выглядит {best_name}."
        else:
            summary = "Не удалось определить лидирующий инструмент."

        return {
            "comparison_found": True,
            "items": scored_items,
            "summary": summary,
            "best_item": best_item
        }