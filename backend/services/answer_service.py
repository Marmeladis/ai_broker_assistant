class AnswerService:
    def build_prompt(self, user, text, dialog_context, intent, market_context, analytics_result):
        system_prompt = """
Ты — интеллектуальный ассистент для брокерской сферы.
Отвечай строго на русском языке.
Учитывай историю диалога, контекст клиента, рыночные данные и результаты аналитики.
Не выдумывай факты.
Не давай индивидуальных инвестиционных рекомендаций.
Если данных недостаточно — сообщи об этом прямо.
"""

        messages = [{"role": "system", "content": system_prompt}]

        if dialog_context.get("portfolio"):
            messages.append({
                "role": "system",
                "content": f"Портфель клиента: {dialog_context['portfolio']}"
            })

        if dialog_context.get("chat_history"):
            messages.extend(dialog_context["chat_history"])

        messages.append({
            "role": "system",
            "content": f"Определённый intent: {intent}"
        })

        if market_context:
            messages.append({
                "role": "system",
                "content": f"Рыночный контекст: {market_context}"
            })

        if analytics_result:
            messages.append({
                "role": "system",
                "content": f"Аналитический результат: {analytics_result}"
            })

        messages.append({"role": "user", "content": text})
        return messages