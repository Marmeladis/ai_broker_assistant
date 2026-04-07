class ComparativeResponseService:
    def build_comparative_summary(
        self,
        intent: str,
        analytics_result: dict | None
    ) -> dict | None:
        if not analytics_result:
            return None

        data = analytics_result.get("calculated_indicators", {})

        if intent == "multi_price_compare":
            return self._build_price_compare_summary(data)

        if intent == "multi_news_compare":
            return self._build_news_compare_summary(data)

        if intent == "multi_position_compare":
            return self._build_position_compare_summary(data)

        if intent == "multi_instrument_compare":
            return self._build_instrument_compare_summary(data)

        return None

    def _build_price_compare_summary(self, data: dict) -> dict | None:
        items = data.get("items", [])
        found_items = [x for x in items if x.get("price_found") and x.get("price") is not None]

        if len(found_items) < 2:
            return {
                "comparison_type": "multi_price_compare",
                "summary_text": "Недостаточно данных для полноценного сравнения цен.",
                "leader": None
            }

        leader = max(found_items, key=lambda x: x.get("price", 0))
        loser = min(found_items, key=lambda x: x.get("price", 0))

        return {
            "comparison_type": "multi_price_compare",
            "leader": {
                "ticker": leader.get("ticker"),
                "display_name": leader.get("display_name"),
                "price": leader.get("price")
            },
            "lagger": {
                "ticker": loser.get("ticker"),
                "display_name": loser.get("display_name"),
                "price": loser.get("price")
            },
            "summary_text": (
                f"По доступным рыночным данным более высокая цена у "
                f"{leader.get('display_name', leader.get('ticker'))}: {leader.get('price')}. "
                f"Более низкая цена у {loser.get('display_name', loser.get('ticker'))}: {loser.get('price')}."
            )
        }

    def _build_news_compare_summary(self, data: dict) -> dict | None:
        items = data.get("items", [])
        if len(items) < 2:
            return {
                "comparison_type": "multi_news_compare",
                "summary_text": "Недостаточно данных для сравнения новостного фона.",
                "leader": None
            }

        counts = []
        for item in items:
            counts.append({
                "ticker": item.get("ticker"),
                "display_name": item.get("display_name"),
                "news_count": len(item.get("items", [])) if item.get("news_found") else 0
            })

        leader = max(counts, key=lambda x: x.get("news_count", 0))
        loser = min(counts, key=lambda x: x.get("news_count", 0))

        return {
            "comparison_type": "multi_news_compare",
            "leader": leader,
            "lagger": loser,
            "summary_text": (
                f"Наиболее насыщенный новостной фон у "
                f"{leader.get('display_name', leader.get('ticker'))}: {leader.get('news_count')} новостей. "
                f"Менее насыщенный — у {loser.get('display_name', loser.get('ticker'))}: {loser.get('news_count')}."
            )
        }

    def _build_position_compare_summary(self, data: dict) -> dict | None:
        items = data.get("items", [])
        valid_items = [x for x in items if x.get("absolute_pnl") is not None]

        if len(valid_items) < 2:
            return {
                "comparison_type": "multi_position_compare",
                "summary_text": "Недостаточно данных для сравнения позиций.",
                "leader": None
            }

        leader = max(valid_items, key=lambda x: x.get("absolute_pnl", 0))
        loser = min(valid_items, key=lambda x: x.get("absolute_pnl", 0))

        return {
            "comparison_type": "multi_position_compare",
            "leader": {
                "ticker": leader.get("ticker"),
                "absolute_pnl": leader.get("absolute_pnl"),
                "pnl_percent": leader.get("pnl_percent")
            },
            "lagger": {
                "ticker": loser.get("ticker"),
                "absolute_pnl": loser.get("absolute_pnl"),
                "pnl_percent": loser.get("pnl_percent")
            },
            "summary_text": (
                f"Лучшая позиция по текущему результату — {leader.get('ticker')}: "
                f"P&L {leader.get('absolute_pnl')} ({leader.get('pnl_percent')}%). "
                f"Хуже выглядит {loser.get('ticker')}: "
                f"P&L {loser.get('absolute_pnl')} ({loser.get('pnl_percent')}%)."
            )
        }

    def _build_instrument_compare_summary(self, data: dict) -> dict | None:
        market_items = data.get("market_items", [])
        news_items = data.get("news_items", [])
        position_items = data.get("position_items", [])

        summary_parts = []

        if market_items:
            valid_market = [x for x in market_items if x.get("price_found") and x.get("price") is not None]
            if len(valid_market) >= 2:
                leader_price = max(valid_market, key=lambda x: x.get("price", 0))
                summary_parts.append(
                    f"По цене лидирует {leader_price.get('display_name', leader_price.get('ticker'))}."
                )

        if news_items:
            counts = []
            for item in news_items:
                counts.append({
                    "display_name": item.get("display_name"),
                    "ticker": item.get("ticker"),
                    "news_count": len(item.get("items", [])) if item.get("news_found") else 0
                })
            if len(counts) >= 2:
                leader_news = max(counts, key=lambda x: x.get("news_count", 0))
                summary_parts.append(
                    f"По насыщенности новостного фона выделяется "
                    f"{leader_news.get('display_name', leader_news.get('ticker'))}."
                )

        if position_items:
            valid_positions = [x for x in position_items if x.get("absolute_pnl") is not None]
            if len(valid_positions) >= 2:
                leader_pos = max(valid_positions, key=lambda x: x.get("absolute_pnl", 0))
                summary_parts.append(
                    f"По позиции пользователя лучше выглядит {leader_pos.get('ticker')}."
                )

        if not summary_parts:
            summary_parts.append("Недостаточно данных для осмысленного общего сравнения инструментов.")

        return {
            "comparison_type": "multi_instrument_compare",
            "summary_text": " ".join(summary_parts)
        }