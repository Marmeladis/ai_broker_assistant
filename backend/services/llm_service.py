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
        system_parts = [
            """
Ты — интеллектуальный ассистент для работников брокерской сферы.

Тебе уже передаются готовые данные от системы:
- рыночные цены,
- теханализ,
- дивиденды,
- портфель,
- позиция пользователя,
- исторические экстремумы,
- валютные котировки,
- купоны облигаций,
- рейтинги бумаг.

ОСНОВНОЕ ПРАВИЛО:
Ты не ищешь факты сам и не выдумываешь их.
Ты обязан опираться только на переданные системой данные.

Обязательные правила ответа:
1. Отвечай строго на русском языке.
2. Не выдумывай факты, даты, дивиденды, цены, сигналы и показатели.
3. Если данных недостаточно — прямо скажи это.
4. Не говори, что у тебя нет доступа к рынку, если данные уже переданы системой.
5. Не отправляй пользователя на внешние сайты.
6. Не давай персональную инвестиционную рекомендацию в приказной форме.
7. Используй аналитические, осторожные формулировки:
   - "по текущим данным выглядит..."
   - "более осторожный сценарий..."
   - "в текущем контексте..."
   - "если цель — дивидендная идея..."
8. Если вопрос про покупку:
   - дай краткий вывод,
   - объясни почему,
   - укажи уровни / сигналы / риски, если они есть.
9. Если вопрос про дивиденды:
   - назови размер дивиденда,
   - дату отсечки,
   - дату покупки под дивиденды, если она есть,
   - дивидендную доходность, если она есть.
   Не выводи дату выплаты, кроме случая, когда пользователь прямо спрашивает именно про выплату.
10. Если вопрос про облигации:
   - используй только переданные купоны / ставки / даты.
11. Если вопрос про рейтинги:
   - объясни, что это выборка по текущим доступным данным, а не гарантия качества.
12. Ответ должен быть профессиональным, понятным и без воды.
13. Предпочтительная длина ответа: 4–8 предложений.
14. Если уже есть готовый аналитический вывод от системы, опирайся на него в первую очередь.
15. Все даты в ответе пиши в формате "11 февраля 2026 года". Не используй ISO-формат дат.
16. Не выводи технические поля: источник данных, source_name, объём, volume, время обновления, recorded_at, last_update_time.
""".strip()
        ]

        portfolio = context.get("portfolio", [])
        if portfolio:
            system_parts.append(f"Портфель клиента: {portfolio}")

        portfolio_metrics = context.get("portfolio_metrics")
        if portfolio_metrics:
            system_parts.append(f"Метрики портфеля: {portfolio_metrics}")

        portfolio_text_summary = context.get("portfolio_text_summary")
        if portfolio_text_summary:
            system_parts.append(f"Краткое summary портфеля: {portfolio_text_summary}")

        market_context = context.get("market_context")
        if market_context:
            system_parts.append(f"Рыночный контекст: {market_context}")

        multi_market_context = context.get("multi_market_context")
        if multi_market_context:
            system_parts.append(f"Множественный рыночный контекст: {multi_market_context}")

        news_context = context.get("news_context")
        if news_context:
            system_parts.append(f"Новостной контекст: {news_context}")

        multi_news_context = context.get("multi_news_context")
        if multi_news_context:
            system_parts.append(f"Множественный новостной контекст: {multi_news_context}")

        position_context = context.get("position_context")
        if position_context:
            system_parts.append(f"Контекст позиции пользователя: {position_context}")

        position_market_metrics = context.get("position_market_metrics")
        if position_market_metrics:
            system_parts.append(f"Метрики позиции: {position_market_metrics}")

        multi_position_contexts = context.get("multi_position_contexts")
        if multi_position_contexts:
            system_parts.append(f"Контексты нескольких позиций: {multi_position_contexts}")

        multi_position_market_metrics = context.get("multi_position_market_metrics")
        if multi_position_market_metrics:
            system_parts.append(f"Метрики нескольких позиций: {multi_position_market_metrics}")

        resolved_instrument = context.get("resolved_instrument")
        if resolved_instrument:
            system_parts.append(f"Распознанный инструмент: {resolved_instrument}")

        technical_analysis_context = context.get("technical_analysis_context")
        if technical_analysis_context:
            system_parts.append(f"Технический анализ: {technical_analysis_context}")

        dividend_context = context.get("dividend_context")
        if dividend_context:
            system_parts.append(f"Дивидендный контекст: {dividend_context}")

        dividend_text_summary = context.get("dividend_text_summary")
        if dividend_text_summary:
            system_parts.append(f"Краткий комментарий по дивидендам: {dividend_text_summary}")

        buy_or_wait_context = context.get("buy_or_wait_context")
        if buy_or_wait_context:
            system_parts.append(f"Контекст buy_or_wait: {buy_or_wait_context}")

        entry_point_context = context.get("entry_point_context")
        if entry_point_context:
            system_parts.append(f"Контекст точки входа: {entry_point_context}")

        dividend_comment_context = context.get("dividend_comment_context")
        if dividend_comment_context:
            system_parts.append(f"Комментарий по дивидендам: {dividend_comment_context}")

        last_dividend_context = context.get("last_dividend_context")
        if last_dividend_context:
            system_parts.append(f"Последний дивидендный контекст: {last_dividend_context}")

        year_dividend_context = context.get("year_dividend_context")
        if year_dividend_context:
            system_parts.append(f"Дивидендный контекст по году: {year_dividend_context}")

        expected_dividend_context = context.get("expected_dividend_context")
        if expected_dividend_context:
            system_parts.append(f"Ожидаемый дивидендный контекст: {expected_dividend_context}")

        historical_price_extremes_context = context.get("historical_price_extremes_context")
        if historical_price_extremes_context:
            system_parts.append(f"Исторические экстремумы цены: {historical_price_extremes_context}")

        max_turnover_context = context.get("max_turnover_context")
        if max_turnover_context:
            system_parts.append(f"Максимальный торговый оборот: {max_turnover_context}")

        fx_context = context.get("fx_context")
        if fx_context:
            system_parts.append(f"Распознанный валютный запрос: {fx_context}")

        fx_price_context = context.get("fx_price_context")
        if fx_price_context:
            system_parts.append(f"Валютный контекст: {fx_price_context}")

        bond_context = context.get("bond_context")
        if bond_context:
            system_parts.append(f"Распознанная облигация: {bond_context}")

        bond_last_coupon_context = context.get("bond_last_coupon_context")
        if bond_last_coupon_context:
            system_parts.append(f"Последний купон по облигации: {bond_last_coupon_context}")

        bond_next_coupon_context = context.get("bond_next_coupon_context")
        if bond_next_coupon_context:
            system_parts.append(f"Следующий купон по облигации: {bond_next_coupon_context}")

        bond_coupon_schedule_context = context.get("bond_coupon_schedule_context")
        if bond_coupon_schedule_context:
            system_parts.append(f"Расписание купонов по облигации: {bond_coupon_schedule_context[:10]}")

        bond_ranking_context = context.get("bond_ranking_context")
        if bond_ranking_context:
            system_parts.append(f"Рейтинг облигаций по купону: {bond_ranking_context}")

        dividend_ranking_context = context.get("dividend_ranking_context")
        if dividend_ranking_context:
            system_parts.append(f"Рейтинг акций по дивидендной доходности: {dividend_ranking_context}")

        dividend_aristocrats_context = context.get("dividend_aristocrats_context")
        if dividend_aristocrats_context:
            system_parts.append(f"Компании с устойчивыми дивидендами: {dividend_aristocrats_context}")

        session_context = context.get("session_context")
        if session_context:
            system_parts.append(f"Сессионный контекст диалога: {session_context}")

        used_session_context = context.get("used_session_context")
        if used_session_context is not None:
            system_parts.append(f"Использован сессионный контекст: {used_session_context}")

        if fact_summary:
            system_parts.append(f"Агрегированные факты: {fact_summary}")

        system_parts.append(f"Определённый intent: {intent}")

        if analytics_result:
            system_parts.append(f"Результат аналитики: {analytics_result}")

        messages = [
            {
                "role": "system",
                "content": "\n\n".join(system_parts)
            }
        ]

        chat_history = context.get("chat_history", [])
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({
                    "role": role,
                    "content": content
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

        if response.status_code >= 400:
            raise RuntimeError(f"GigaChat error {response.status_code}: {response.text}")

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
        data = (analytics_result or {}).get("calculated_indicators", {})

        if intent == "price_check":
            if data.get("price_found"):
                return f"По инструменту {data.get('display_name') or data.get('ticker')} найдена текущая цена {data.get('price')}."
            return "Цена инструмента в текущем контексте не найдена."

        if intent == "technical_analysis":
            parts = []
            bullish = []
            bearish = []
            neutral = []

            trend = data.get("trend")
            signal = data.get("signal")
            rsi = data.get("rsi_14")
            macd = data.get("macd")
            macd_signal = data.get("macd_signal")
            support = data.get("support")
            resistance = data.get("resistance")
            last_price = data.get("last_price")

            if last_price is not None:
                parts.append(f"Последняя цена: {round(last_price, 4)}.")

            if trend:
                if trend == "uptrend":
                    parts.append("Тренд: восходящий — краткосрочно это поддерживает бумагу.")
                    bullish.append("восходящий тренд")
                elif trend == "downtrend":
                    parts.append("Тренд: нисходящий — бумага остаётся под давлением.")
                    bearish.append("нисходящий тренд")
                else:
                    parts.append("Тренд: боковой — выраженного направления сейчас нет.")
                    neutral.append("боковой тренд")

            if rsi is not None:
                rsi_value = round(rsi, 4)
                if rsi > 70:
                    parts.append(f"RSI(14): {rsi_value} — зона перекупленности, возможна коррекция или пауза.")
                    bearish.append("перекупленность по RSI")
                elif rsi < 30:
                    parts.append(f"RSI(14): {rsi_value} — зона перепроданности, возможен технический отскок.")
                    bullish.append("перепроданность по RSI")
                else:
                    parts.append(f"RSI(14): {rsi_value} — нейтральная зона без сильного самостоятельного сигнала.")
                    neutral.append("нейтральный RSI")

            if macd is not None:
                macd_text = f"MACD: {round(macd, 4)}"
                if macd_signal is not None:
                    macd_text += f", сигнальная линия: {round(macd_signal, 4)}"
                    if macd > macd_signal:
                        parts.append(f"{macd_text}. MACD выше сигнальной линии — импульс скорее бычий.")
                        bullish.append("MACD выше сигнальной линии")
                    elif macd < macd_signal:
                        parts.append(f"{macd_text}. MACD ниже сигнальной линии — импульс скорее медвежий.")
                        bearish.append("MACD ниже сигнальной линии")
                else:
                    parts.append(f"{macd_text}.")

            if support is not None:
                parts.append(f"Поддержка: {round(support, 4)}.")
            if resistance is not None:
                parts.append(f"Сопротивление: {round(resistance, 4)}.")
            if signal:
                parts.append(f"Краткосрочный сигнал: {signal}.")

            if bullish or bearish or neutral:
                summary = []
                if bullish:
                    summary.append("бычьи факторы: " + ", ".join(dict.fromkeys(bullish)))
                if bearish:
                    summary.append("медвежьи факторы: " + ", ".join(dict.fromkeys(bearish)))
                if neutral:
                    summary.append("нейтральные факторы: " + ", ".join(dict.fromkeys(neutral)))
                parts.append("Совокупно: " + "; ".join(summary) + ".")

            parts.append("Это технический комментарий, а не торговая рекомендация.")
            return " ".join(parts) if parts else "Не удалось выполнить технический анализ."

        if intent in {"dividend_info", "historical_dividend_query", "expected_dividend_query", "dividend_record_date_query"}:
            if not data.get("dividend_found") and not data.get("record_date"):
                return "Данные по дивидендам по этой бумаге сейчас не найдены."

            parts = []
            if data.get("dividend_per_share") is not None:
                parts.append(f"Размер дивиденда: {data.get('dividend_per_share')}.")
            if data.get("record_date"):
                parts.append(f"Дата отсечки: {data.get('record_date')}.")
            if data.get("declared_date"):
                parts.append(f"Дата решения: {data.get('declared_date')}.")
            if data.get("payment_timing_note"):
                parts.append("Дивиденды обычно поступают в срок до 25 рабочих дней после даты закрытия реестра.")
            return " ".join(parts) if parts else "Данные по дивидендам по этой бумаге сейчас не найдены."

        if intent == "historical_price_extremes_query":
            if not data.get("found"):
                return "Исторические экстремумы цены по выбранному периоду не найдены."
            parts = []
            if data.get("min_price") is not None:
                parts.append(f"Минимальная цена была {data.get('min_price')} на дату {data.get('min_price_date')}.")
            if data.get("max_price") is not None:
                parts.append(f"Максимальная цена была {data.get('max_price')} на дату {data.get('max_price_date')}.")
            return " ".join(parts)

        if intent == "max_turnover_query":
            if not data.get("found"):
                return "Данные по максимальному торговому обороту за выбранный период не найдены."
            return (
                f"По бумаге {data.get('ticker')} максимальный торговый оборот за день "
                f"составил {data.get('max_turnover')} на дату {data.get('turnover_date')}."
            )

        if intent == "fx_price_query":
            if data.get("price") is None:
                return "Не удалось найти актуальную цену по этой валюте."
            return f"По валютной паре {data.get('display_name')} текущая цена составляет {data.get('price')}."

        if intent == "bond_coupon_query":
            last_coupon = data.get("last_coupon") or {}
            next_coupon = data.get("next_coupon") or {}
            parts = []
            if last_coupon:
                parts.append(
                    f"Последний известный купон по облигации {last_coupon.get('bond_code')} "
                    f"составил {last_coupon.get('coupon_value')} {last_coupon.get('face_unit') or ''}."
                )
            if next_coupon:
                parts.append(
                    f"Следующий купон ожидается {next_coupon.get('coupon_date')} "
                    f"в размере {next_coupon.get('coupon_value')} {next_coupon.get('face_unit') or ''}."
                )
            return " ".join(parts) if parts else "Данные по купонам облигации не найдены."

        if intent == "bond_ranking":
            items = data.get("items", [])
            if not items:
                return "Не удалось получить список облигаций с высоким купоном."
            return "Сформирован рейтинг облигаций по купону."

        if intent == "dividend_ranking_query":
            items = data.get("items", [])
            if not items:
                return "Не удалось получить список акций с высокой дивидендной доходностью."
            return "Сформирован рейтинг акций по дивидендной доходности."

        if intent == "dividend_aristocrats":
            items = data.get("items", [])
            if not items:
                return "Не удалось найти устойчивые дивидендные компании."
            return "Сформирован список компаний с устойчивой дивидендной историей."

        if intent == "buy_or_wait":
            if data.get("summary"):
                return data.get("summary")
            decision = data.get("decision")
            if decision == "buy_zone":
                return "По текущим данным бумага выглядит относительно интересной для входа."
            if decision == "wait_for_better_entry":
                return "По текущим данным более осторожный сценарий — дождаться более комфортной точки входа."
            return "Сигналы смешанные, поэтому спешить с входом не обязательно."

        if intent == "entry_point_analysis":
            if data.get("summary"):
                return data.get("summary")
            return "Подготовлен анализ точки входа."

        if intent == "portfolio_analysis":
            positions_count = data.get("positions_count", 0)
            return f"По портфелю найдено {positions_count} позиций."

        user_text = messages[-1]["content"] if messages else ""
        return f"Я получил ваш запрос: {user_text}. Пока не хватает данных для более точного ответа."