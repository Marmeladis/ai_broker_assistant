class ResponseBuilderService:
    def build_fact_summary(
        self,
        intent: str,
        context: dict,
        analytics_result: dict | None = None,
        comparative_summary: dict | None = None
    ) -> dict:
        portfolio = context.get("portfolio", [])
        portfolio_text_summary = context.get("portfolio_text_summary")

        market_context = context.get("market_context")
        multi_market_context = context.get("multi_market_context", [])

        news_context = context.get("news_context")
        multi_news_context = context.get("multi_news_context", [])

        position_context = context.get("position_context")
        position_market_metrics = context.get("position_market_metrics")

        multi_position_contexts = context.get("multi_position_contexts", [])
        multi_position_market_metrics = context.get("multi_position_market_metrics", [])

        summary = {
            "intent": intent,
            "facts": []
        }

        if portfolio_text_summary:
            summary["facts"].append(portfolio_text_summary)

        if len(multi_market_context) > 1:
            for item in multi_market_context:
                if item.get("price_found"):
                    summary["facts"].append(
                        f"{item.get('display_name', item.get('ticker'))}: цена {item.get('price')} "
                        f"(источник {item.get('source_name')})."
                    )
                else:
                    summary["facts"].append(
                        f"{item.get('display_name', item.get('ticker'))}: цена не найдена."
                    )
        elif market_context:
            if market_context.get("price_found"):
                summary["facts"].append(
                    f"По инструменту {market_context.get('display_name', market_context.get('ticker'))} "
                    f"найдена цена {market_context.get('price')} из источника {market_context.get('source_name')}."
                )
            else:
                summary["facts"].append(
                    f"По инструменту {market_context.get('display_name', market_context.get('ticker'))} цена не найдена."
                )

        if len(multi_position_contexts) > 1:
            for pos in multi_position_contexts:
                summary["facts"].append(
                    f"У пользователя есть позиция по {pos['ticker']}: "
                    f"{pos['quantity']} шт. по средней цене {pos['avg_price']}."
                )
        elif position_context:
            summary["facts"].append(
                f"У пользователя есть позиция по {position_context['ticker']}: "
                f"{position_context['quantity']} шт. по средней цене {position_context['avg_price']}."
            )

        if len(multi_position_market_metrics) > 1:
            for metrics in multi_position_market_metrics:
                pnl_percent = metrics.get("pnl_percent")
                pnl_text = f"{pnl_percent}%" if pnl_percent is not None else "н/д"

                summary["facts"].append(
                    f"По позиции {metrics['ticker']}: рыночная стоимость {metrics['market_value']}, "
                    f"P&L {metrics['absolute_pnl']}, P&L% {pnl_text}."
                )
        elif position_market_metrics:
            pnl_percent = position_market_metrics.get("pnl_percent")
            pnl_text = f"{pnl_percent}%" if pnl_percent is not None else "н/д"

            summary["facts"].append(
                f"По позиции {position_market_metrics['ticker']} текущая оценка: "
                f"рыночная стоимость {position_market_metrics['market_value']}, "
                f"P&L {position_market_metrics['absolute_pnl']}, P&L% {pnl_text}."
            )

        if len(multi_news_context) > 1:
            for news_item in multi_news_context:
                if news_item.get("news_found"):
                    summary["facts"].append(
                        f"По {news_item.get('display_name', news_item.get('ticker'))} найдено новостей: "
                        f"{len(news_item.get('items', []))}."
                    )
                else:
                    summary["facts"].append(
                        f"По {news_item.get('display_name', news_item.get('ticker'))} новости не найдены."
                    )
        elif news_context:
            if news_context.get("news_found"):
                summary["facts"].append(
                    f"По инструменту {news_context.get('display_name', news_context.get('ticker'))} "
                    f"найдено новостей: {len(news_context.get('items', []))}."
                )
            else:
                summary["facts"].append(
                    f"По инструменту {news_context.get('display_name', news_context.get('ticker'))} новости не найдены."
                )

        if portfolio:
            summary["facts"].append(
                f"В портфеле пользователя позиций: {len(portfolio)}."
            )

        if analytics_result:
            summary["facts"].append(
                f"Аналитический вывод: {analytics_result.get('trend_summary')}."
            )

        if comparative_summary and comparative_summary.get("summary_text"):
            summary["facts"].append(
                f"Сравнительный вывод: {comparative_summary.get('summary_text')}"
            )

        return summary