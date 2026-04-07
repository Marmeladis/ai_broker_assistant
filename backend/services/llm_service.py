import time
import uuid
import requests

from backend.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.temperature = settings.LLM_TEMPERATURE

        self.gigachat_auth_key = settings.GIGACHAT_AUTH_KEY
        self.gigachat_scope = settings.GIGACHAT_SCOPE
        self.gigachat_auth_url = settings.GIGACHAT_AUTH_URL
        self.gigachat_base_url = settings.GIGACHAT_BASE_URL
        self.gigachat_model = settings.GIGACHAT_MODEL
        self.gigachat_timeout = settings.GIGACHAT_TIMEOUT_SECONDS
        self.gigachat_verify_ssl = settings.GIGACHAT_VERIFY_SSL

        self._access_token: str | None = None
        self._access_token_expires_at: int = 0

    def is_configured(self) -> bool:
        if self.provider != "gigachat":
            return False

        return bool(
            self.gigachat_auth_key
            and self.gigachat_scope
            and self.gigachat_auth_url
            and self.gigachat_base_url
            and self.gigachat_model
        )

    def healthcheck(self) -> dict:
        if not self.is_configured():
            return {
                "configured": False,
                "available": False,
                "provider": self.provider,
                "message": "GigaChat не настроен"
            }

        try:
            token = self._get_access_token()

            response = requests.get(
                f"{self.gigachat_base_url}/models",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout=20,
                verify=self.gigachat_verify_ssl
            )
            response.raise_for_status()

            data = response.json()
            models = []
            for item in data.get("data", []):
                model_id = item.get("id")
                if model_id:
                    models.append(model_id)

            return {
                "configured": True,
                "available": True,
                "provider": "gigachat",
                "message": "GigaChat доступен",
                "models": models
            }
        except Exception as e:
            return {
                "configured": True,
                "available": False,
                "provider": "gigachat",
                "message": f"Ошибка подключения к GigaChat: {str(e)}"
            }

    def build_messages(
        self,
        user_text: str,
        context: dict,
        intent: str,
        analytics_result: dict | None = None,
        fact_summary: dict | None = None
    ) -> list[dict]:
        system_prompt = """
Ты — интеллектуальный ассистент для работников брокерской сферы.

Пользователь общается с тобой через единый чат.
Ты должен учитывать:
- историю диалога,
- портфель клиента,
- агрегированные метрики портфеля,
- рыночные данные,
- новости,
- результаты аналитики,
- агрегированные факты по инструменту и позиции.

Правила:
1. Отвечай строго на русском языке.
2. Не выдумывай факты, цены, новости и показатели.
3. Если данных недостаточно — прямо скажи об этом.
4. Не давай индивидуальных инвестиционных рекомендаций.
5. Если пользователь спрашивает про портфель — используй агрегированные метрики портфеля.
6. Если пользователь спрашивает про конкретную бумагу — используй цену, новости и данные позиции.
7. Если есть текущий P&L по позиции или портфелю — можешь его описать.
8. Если пользователь просит технический анализ — используй только доступные индикаторы и не обещай рост или падение как факт.
9. Отвечай кратко, профессионально, содержательно.
"""

        messages = [{"role": "system", "content": system_prompt.strip()}]

        portfolio = context.get("portfolio", [])
        if portfolio:
            messages.append({
                "role": "system",
                "content": f"Портфель клиента: {portfolio}"
            })

        portfolio_metrics = context.get("portfolio_metrics")
        if portfolio_metrics:
            messages.append({
                "role": "system",
                "content": f"Метрики портфеля: {portfolio_metrics}"
            })

        portfolio_text_summary = context.get("portfolio_text_summary")
        if portfolio_text_summary:
            messages.append({
                "role": "system",
                "content": f"Краткое summary портфеля: {portfolio_text_summary}"
            })

        market_context = context.get("market_context")
        if market_context:
            messages.append({
                "role": "system",
                "content": f"Рыночный контекст: {market_context}"
            })

        multi_market_context = context.get("multi_market_context")
        if multi_market_context:
            messages.append({
                "role": "system",
                "content": f"Множественный рыночный контекст: {multi_market_context}"
            })

        news_context = context.get("news_context")
        if news_context:
            messages.append({
                "role": "system",
                "content": f"Новостной контекст: {news_context}"
            })

        multi_news_context = context.get("multi_news_context")
        if multi_news_context:
            messages.append({
                "role": "system",
                "content": f"Множественный новостной контекст: {multi_news_context}"
            })

        position_context = context.get("position_context")
        if position_context:
            messages.append({
                "role": "system",
                "content": f"Контекст позиции пользователя: {position_context}"
            })

        position_market_metrics = context.get("position_market_metrics")
        if position_market_metrics:
            messages.append({
                "role": "system",
                "content": f"Метрики позиции: {position_market_metrics}"
            })

        multi_position_contexts = context.get("multi_position_contexts")
        if multi_position_contexts:
            messages.append({
                "role": "system",
                "content": f"Контексты нескольких позиций: {multi_position_contexts}"
            })

        multi_position_market_metrics = context.get("multi_position_market_metrics")
        if multi_position_market_metrics:
            messages.append({
                "role": "system",
                "content": f"Метрики нескольких позиций: {multi_position_market_metrics}"
            })

        resolved_instrument = context.get("resolved_instrument")
        if resolved_instrument:
            messages.append({
                "role": "system",
                "content": f"Распознанный инструмент: {resolved_instrument}"
            })

        if fact_summary:
            messages.append({
                "role": "system",
                "content": f"Агрегированные факты: {fact_summary}"
            })

        messages.extend(context.get("chat_history", []))

        messages.append({
            "role": "system",
            "content": f"Определённый intent: {intent}"
        })

        if analytics_result:
            messages.append({
                "role": "system",
                "content": f"Результат аналитики: {analytics_result}"
            })

        messages.append({
            "role": "user",
            "content": user_text
        })

        return messages

    def generate(
        self,
        messages: list[dict],
        intent: str,
        analytics_result: dict | None = None
    ) -> str:
        if not self.is_configured():
            return self._fallback_response(messages, intent, analytics_result)

        try:
            if self.provider == "gigachat":
                return self._generate_gigachat(messages)

            return self._fallback_response(messages, intent, analytics_result)
        except Exception as e:
            return f"Ошибка обращения к LLM: {str(e)}"

    def _generate_gigachat(self, messages: list[dict]) -> str:
        token = self._get_access_token()

        payload = {
            "model": self.gigachat_model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
            "n": 1,
            "max_tokens": 1024,
            "repetition_penalty": 1
        }

        response = requests.post(
            f"{self.gigachat_base_url}/chat/completions",
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=self.gigachat_timeout,
            verify=self.gigachat_verify_ssl
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "GigaChat вернул пустой ответ."

        content = choices[0].get("message", {}).get("content")
        if not content:
            return "GigaChat не вернул текст ответа."

        return content.strip()

    def _get_access_token(self) -> str:
        now = int(time.time())

        if self._access_token and now < self._access_token_expires_at - 60:
            return self._access_token

        response = requests.post(
            self.gigachat_auth_url,
            data={"scope": self.gigachat_scope},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Bearer {self.gigachat_auth_key}",
            },
            timeout=20,
            verify=self.gigachat_verify_ssl
        )
        response.raise_for_status()

        data = response.json()

        access_token = data.get("access_token")
        expires_at = data.get("expires_at")

        if not access_token:
            raise RuntimeError(f"GigaChat не вернул access_token: {data}")

        if not expires_at:
            expires_at = int(time.time()) + 1800

        self._access_token = access_token
        self._access_token_expires_at = int(expires_at)

        return self._access_token

    def _fallback_response(
        self,
        messages: list[dict],
        intent: str,
        analytics_result: dict | None = None
    ) -> str:
        if intent == "technical_analysis":
            return self._technical_analysis_fallback(analytics_result)

        if intent == "portfolio_analysis":
            return self._portfolio_analysis_fallback(analytics_result)

        if intent == "risk_return":
            return self._risk_return_fallback(analytics_result)

        if intent == "benchmark_compare":
            return self._benchmark_compare_fallback(analytics_result)

        if intent == "price_check":
            return self._price_check_fallback(analytics_result)

        if intent == "multi_price_compare":
            return self._multi_price_compare_fallback(analytics_result)

        if intent == "news_explain":
            return self._news_explain_fallback(analytics_result)

        if intent == "multi_news_compare":
            return self._multi_news_compare_fallback(analytics_result)

        if intent == "multi_position_compare":
            return self._multi_position_compare_fallback(analytics_result)

        if intent == "multi_instrument_compare":
            return self._multi_instrument_compare_fallback(analytics_result)

        if intent == "scenario_forecast":
            return self._scenario_fallback(analytics_result)

        if intent == "simple_analysis":
            return self._simple_analysis_fallback(analytics_result)

        user_text = messages[-1]["content"] if messages else ""
        return f"Я получил ваш запрос: {user_text}. Пока не хватает данных для более точного ответа."

    def _technical_analysis_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось выполнить технический анализ."

        data = analytics_result.get("calculated_indicators", {})
        trend = data.get("trend")
        signal = data.get("signal")
        sma_5 = data.get("sma_5")
        sma_10 = data.get("sma_10")
        rsi_14 = data.get("rsi_14")
        macd = data.get("macd")
        macd_signal = data.get("macd_signal")
        support = data.get("support")
        resistance = data.get("resistance")
        pattern = data.get("pattern")
        last_price = data.get("last_price")

        parts = []
        if last_price is not None:
            parts.append(f"Последняя цена: {last_price}.")
        if trend:
            parts.append(f"Текущий тренд: {trend}.")
        if signal:
            parts.append(f"Сигнал: {signal}.")
        if sma_5 is not None:
            parts.append(f"SMA(5): {round(sma_5, 4)}.")
        if sma_10 is not None:
            parts.append(f"SMA(10): {round(sma_10, 4)}.")
        if rsi_14 is not None:
            parts.append(f"RSI(14): {round(rsi_14, 4)}.")
        if macd is not None and macd_signal is not None:
            parts.append(f"MACD: {round(macd, 4)}, signal: {round(macd_signal, 4)}.")
        if support is not None:
            parts.append(f"Поддержка: {round(support, 4)}.")
        if resistance is not None:
            parts.append(f"Сопротивление: {round(resistance, 4)}.")
        if pattern:
            parts.append(f"Обнаруженный паттерн: {pattern}.")
        parts.append("Это технический сигнал, а не инвестиционная рекомендация.")

        return " ".join(parts)

    def _portfolio_analysis_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось собрать аналитику по портфелю."

        data = analytics_result.get("calculated_indicators", {})
        positions_count = data.get("positions_count", 0)
        invested = data.get("total_invested_value")
        market_value = data.get("total_market_value")
        pnl = data.get("total_absolute_pnl")
        pnl_percent = data.get("total_pnl_percent")
        profitable = data.get("profitable_positions", 0)
        losing = data.get("losing_positions", 0)

        parts = [f"По портфелю найдено {positions_count} позиций."]

        if invested is not None:
            parts.append(f"Суммарно вложено: {invested}.")
        if market_value is not None:
            parts.append(f"Текущая рыночная стоимость: {market_value}.")
        if pnl is not None:
            pnl_text = f"{pnl}"
            if pnl_percent is not None:
                pnl_text += f" ({pnl_percent}%)"
            parts.append(f"Совокупный результат: {pnl_text}.")
        parts.append(f"Позиции в плюсе: {profitable}, в минусе: {losing}.")
        parts.append("Ответ носит информационный характер и не является инвестиционной рекомендацией.")

        return " ".join(parts)

    def _risk_return_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось оценить риск и доходность."

        data = analytics_result.get("calculated_indicators", {})
        positions_count = data.get("positions_count", 0)
        profitable = data.get("profitable_positions", 0)
        losing = data.get("losing_positions", 0)
        pnl_percent = data.get("total_pnl_percent")

        parts = [
            f"Предварительная оценка портфеля: позиций {positions_count}, "
            f"в плюсе {profitable}, в минусе {losing}."
        ]

        if pnl_percent is not None:
            parts.append(f"Текущий совокупный результат составляет {pnl_percent}%.")

        parts.append("Для точной оценки риска нужны более подробные исторические данные.")
        return " ".join(parts)

    def _benchmark_compare_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить сравнение с бенчмарком."

        data = analytics_result.get("calculated_indicators", {})
        positions_count = data.get("positions_count")
        pnl_percent = data.get("total_pnl_percent")

        parts = []
        if positions_count is not None:
            parts.append(f"В портфеле {positions_count} позиций.")
        if pnl_percent is not None:
            parts.append(f"Текущий совокупный результат портфеля: {pnl_percent}%.")
        parts.append("Полноценное сравнение с бенчмарком требует подключения эталонного индекса или стратегии сравнения.")

        return " ".join(parts)

    def _price_check_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Цена инструмента не найдена."

        data = analytics_result.get("calculated_indicators", {})
        ticker = data.get("ticker")
        display_name = data.get("display_name")
        price = data.get("price")
        source_name = data.get("source_name")
        recorded_at = data.get("recorded_at")
        position_metrics = data.get("position_metrics")

        if not ticker or price is None:
            return "Цена инструмента в текущем контексте не найдена."

        instrument_name = display_name or ticker
        parts = [f"По инструменту {instrument_name} найдена текущая цена {price}."]

        if source_name:
            parts.append(f"Источник данных: {source_name}.")
        if recorded_at:
            parts.append(f"Время записи: {recorded_at}.")

        if position_metrics:
            pnl = position_metrics.get("absolute_pnl")
            pnl_percent = position_metrics.get("pnl_percent")
            market_value = position_metrics.get("market_value")

            if market_value is not None:
                parts.append(f"Текущая стоимость вашей позиции: {market_value}.")
            if pnl is not None:
                pnl_text = f"{pnl}"
                if pnl_percent is not None:
                    pnl_text += f" ({pnl_percent}%)"
                parts.append(f"Текущий результат по позиции: {pnl_text}.")

        return " ".join(parts)

    def _multi_price_compare_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить сравнение цен."

        data = analytics_result.get("calculated_indicators", {})
        items = data.get("items", [])
        position_metrics = data.get("position_metrics", [])

        if not items:
            return "Данных для сравнения цен не найдено."

        parts = ["Сравнение цен по инструментам:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            if item.get("price_found"):
                parts.append(f"{name}: {item.get('price')}.")
            else:
                parts.append(f"{name}: цена не найдена.")

        if position_metrics:
            parts.append("Также найдены данные по позициям пользователя для части инструментов.")

        return " ".join(parts)

    def _news_explain_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось найти новостной контекст."

        data = analytics_result.get("calculated_indicators", {})
        ticker = data.get("ticker")
        display_name = data.get("display_name")
        news_count = data.get("news_count", 0)
        has_position = data.get("has_position", False)

        if not ticker or news_count == 0:
            return "Новости по инструменту не найдены."

        instrument_name = display_name or ticker
        parts = [f"По инструменту {instrument_name} найдено новостей: {news_count}."]

        if has_position:
            parts.append("У пользователя есть позиция по этому инструменту, поэтому новостной фон особенно важен для оценки текущей ситуации.")

        parts.append("Для подробного объяснения новости лучше использовать подключённую LLM.")
        return " ".join(parts)

    def _multi_news_compare_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить сравнение новостей."

        items = analytics_result.get("calculated_indicators", {}).get("items", [])
        if not items:
            return "Новостной контекст для сравнения не найден."

        parts = ["Сравнение новостного фона:"]
        for item in items:
            name = item.get("display_name", item.get("ticker"))
            count = len(item.get("items", [])) if item.get("news_found") else 0
            parts.append(f"{name}: новостей {count}.")
        return " ".join(parts)

    def _multi_position_compare_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить сравнение позиций."

        items = analytics_result.get("calculated_indicators", {}).get("items", [])
        if not items:
            return "Нет данных для сравнения позиций."

        parts = ["Сравнение позиций пользователя:"]
        for item in items:
            ticker = item.get("ticker")
            market_value = item.get("market_value")
            pnl = item.get("absolute_pnl")
            pnl_percent = item.get("pnl_percent")

            text = f"{ticker}:"
            if market_value is not None:
                text += f" стоимость {market_value},"
            if pnl is not None:
                text += f" P&L {pnl}"
                if pnl_percent is not None:
                    text += f" ({pnl_percent}%)"
            text += "."
            parts.append(text)

        return " ".join(parts)

    def _multi_instrument_compare_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить сравнение инструментов."

        data = analytics_result.get("calculated_indicators", {})
        market_items = data.get("market_items", [])
        news_items = data.get("news_items", [])
        position_items = data.get("position_items", [])

        parts = ["Подготовлено сравнение нескольких инструментов."]

        if market_items:
            parts.append(f"По рынку найдено инструментов: {len(market_items)}.")
        if news_items:
            parts.append(f"По новостям найдено инструментов: {len(news_items)}.")
        if position_items:
            parts.append(f"По позициям пользователя найдено инструментов: {len(position_items)}.")

        return " ".join(parts)

    def _scenario_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось сформировать сценарный комментарий."

        data = analytics_result.get("calculated_indicators", {})
        parts = ["Можно построить базовый сценарный комментарий по текущему контексту."]
        if data.get("has_market_context"):
            parts.append("Рыночные данные доступны.")
        if data.get("has_news_context"):
            parts.append("Новостной контекст доступен.")
        if data.get("has_portfolio"):
            parts.append("Портфель клиента учтён.")
        return " ".join(parts)

    def _simple_analysis_fallback(self, analytics_result: dict | None) -> str:
        if not analytics_result:
            return "Не удалось подготовить аналитический комментарий."

        trend = analytics_result.get("trend_summary")
        if trend:
            return f"Предварительный аналитический вывод: {trend}"
        return "Подготовлен общий аналитический комментарий."