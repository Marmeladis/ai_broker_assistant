class RecommendationService:
    def build_buy_or_wait_context(
        self,
        market_context: dict | None,
        technical_analysis: dict | None,
        dividend_context: dict | None,
        position_market_metrics: dict | None = None
    ) -> dict:
        if not market_context:
            return {
                "recommendation_type": "buy_or_wait",
                "decision": "insufficient_data",
                "summary": "Недостаточно рыночных данных для оценки точки входа.",
                "reasons": ["no_market_context"]
            }

        price = market_context.get("price")
        technical_analysis = technical_analysis or {}

        trend = technical_analysis.get("trend")
        signal = technical_analysis.get("signal")
        rsi = technical_analysis.get("rsi_14")
        support = technical_analysis.get("support")
        resistance = technical_analysis.get("resistance")

        reasons = []
        score_buy = 0
        score_wait = 0

        if trend == "uptrend":
            score_buy += 1
            reasons.append("uptrend")
        elif trend == "downtrend":
            score_wait += 2
            reasons.append("downtrend")
        elif trend == "sideways":
            reasons.append("sideways")

        if signal == "bullish":
            score_buy += 2
            reasons.append("bullish_signal")
        elif signal == "bearish":
            score_wait += 2
            reasons.append("bearish_signal")

        if rsi is not None:
            if rsi > 70:
                score_wait += 2
                reasons.append("rsi_overbought")
            elif rsi < 30:
                score_buy += 1
                reasons.append("rsi_oversold")
            else:
                reasons.append("rsi_neutral")

        if price is not None and support is not None and resistance is not None:
            try:
                distance_to_support = abs(price - support)
                distance_to_resistance = abs(resistance - price)

                if distance_to_support < distance_to_resistance:
                    score_buy += 1
                    reasons.append("price_near_support")
                elif distance_to_resistance < distance_to_support:
                    score_wait += 1
                    reasons.append("price_near_resistance")
            except Exception:
                pass

        if dividend_context and dividend_context.get("dividend_found"):
            reasons.append("dividend_known")

            dividend_yield = dividend_context.get("dividend_yield_percent")
            if dividend_yield is not None and dividend_yield >= 8:
                score_buy += 1
                reasons.append("attractive_dividend_yield")

        if position_market_metrics:
            reasons.append("position_exists")

        if score_buy > score_wait:
            decision = "buy_zone"
            summary = "По текущим данным бумага выглядит относительно интересной для входа, но решение стоит принимать с учётом твоего горизонта и риска."
        elif score_wait > score_buy:
            decision = "wait_for_better_entry"
            summary = "По текущим данным более осторожный сценарий — подождать более комфортную точку входа."
        else:
            decision = "neutral_wait"
            summary = "Сигналы смешанные: выраженного преимущества для немедленного входа сейчас нет."

        return {
            "recommendation_type": "buy_or_wait",
            "decision": decision,
            "summary": summary,
            "reasons": reasons,
            "trend": trend,
            "signal": signal,
            "rsi_14": rsi,
            "support": support,
            "resistance": resistance,
            "current_price": price,
            "has_dividend_context": bool(dividend_context and dividend_context.get("dividend_found")),
            "has_position": position_market_metrics is not None
        }

    def build_entry_point_context(
        self,
        market_context: dict | None,
        technical_analysis: dict | None
    ) -> dict:
        if not market_context:
            return {
                "recommendation_type": "entry_point_analysis",
                "entry_bias": "unknown",
                "summary": "Недостаточно рыночных данных для анализа точки входа."
            }

        technical_analysis = technical_analysis or {}

        price = market_context.get("price")
        support = technical_analysis.get("support")
        resistance = technical_analysis.get("resistance")
        signal = technical_analysis.get("signal")
        trend = technical_analysis.get("trend")
        rsi = technical_analysis.get("rsi_14")

        entry_bias = "neutral"
        reasons = []

        if signal == "bullish":
            reasons.append("bullish_signal")
        elif signal == "bearish":
            reasons.append("bearish_signal")

        if trend == "uptrend":
            reasons.append("uptrend")
        elif trend == "downtrend":
            reasons.append("downtrend")

        if rsi is not None:
            if rsi > 70:
                reasons.append("rsi_overbought")
            elif rsi < 30:
                reasons.append("rsi_oversold")

        if price is not None and support is not None and resistance is not None:
            try:
                distance_to_support = abs(price - support)
                distance_to_resistance = abs(resistance - price)

                if distance_to_support < distance_to_resistance:
                    entry_bias = "near_support"
                elif distance_to_resistance < distance_to_support:
                    entry_bias = "near_resistance"
                else:
                    entry_bias = "mid_range"
            except Exception:
                entry_bias = "neutral"

        summary_map = {
            "near_support": "Текущая цена ближе к поддержке, поэтому точка входа выглядит более комфортной, чем при входе у сопротивления.",
            "near_resistance": "Текущая цена ближе к сопротивлению, поэтому вход на этих уровнях выглядит более осторожным.",
            "mid_range": "Цена находится примерно в середине диапазона между поддержкой и сопротивлением.",
            "neutral": "По текущим данным явной точки входа не выделяется.",
            "unknown": "Недостаточно данных для оценки точки входа."
        }

        return {
            "recommendation_type": "entry_point_analysis",
            "entry_bias": entry_bias,
            "summary": summary_map.get(entry_bias, summary_map["neutral"]),
            "reasons": reasons,
            "current_price": price,
            "support": support,
            "resistance": resistance,
            "signal": signal,
            "trend": trend,
            "rsi_14": rsi
        }

    def build_dividend_comment(
        self,
        dividend_context: dict | None
    ) -> dict:
        if not dividend_context or not dividend_context.get("dividend_found"):
            return {
                "recommendation_type": "dividend_info",
                "summary": "Данные по дивидендам по этой бумаге сейчас не найдены.",
                "dividend_found": False
            }

        dividend_per_share = dividend_context.get("dividend_per_share")
        record_date = dividend_context.get("record_date")
        payment_date = dividend_context.get("payment_date")
        dividend_yield = dividend_context.get("dividend_yield_percent")

        parts = ["По бумаге найдены дивидендные данные."]

        if dividend_per_share is not None:
            parts.append(f"Размер дивиденда: {dividend_per_share}.")

        if record_date:
            parts.append(f"Дата закрытия реестра: {record_date}.")

        if payment_date:
            parts.append(f"Ожидаемая дата выплаты: {payment_date}.")

        if dividend_yield is not None:
            parts.append(f"Оценочная дивидендная доходность: {dividend_yield}%.")

        return {
            "recommendation_type": "dividend_info",
            "summary": " ".join(parts),
            "dividend_found": True,
            "dividend_per_share": dividend_per_share,
            "record_date": record_date,
            "payment_date": payment_date,
            "dividend_yield_percent": dividend_yield
        }