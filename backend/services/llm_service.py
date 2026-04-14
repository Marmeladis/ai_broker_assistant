import time
import uuid
from typing import Any

import requests

from backend.config import settings


class LLMService:
    def __init__(self):
        self.provider = getattr(settings, "LLM_PROVIDER", "gigachat")
        self.temperature = getattr(settings, "LLM_TEMPERATURE", 0.2)

        # Generic / legacy settings
        self.base_url = getattr(settings, "LLM_BASE_URL", "")
        self.api_key = getattr(settings, "LLM_API_KEY", "")
        self.model_name = getattr(settings, "LLM_MODEL_NAME", "")
        self.timeout = getattr(settings, "LLM_TIMEOUT_SECONDS", 60)

        # GigaChat settings
        self.gigachat_auth_key = getattr(settings, "GIGACHAT_AUTH_KEY", "")
        self.gigachat_scope = getattr(settings, "GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.gigachat_auth_url = getattr(settings, "GIGACHAT_AUTH_URL", "")
        self.gigachat_base_url = getattr(settings, "GIGACHAT_BASE_URL", "")
        self.gigachat_model = getattr(settings, "GIGACHAT_MODEL", "GigaChat")
        self.gigachat_timeout = getattr(settings, "GIGACHAT_TIMEOUT_SECONDS", 60)
        self.gigachat_verify_ssl = self._to_bool(
            getattr(settings, "GIGACHAT_VERIFY_SSL", False)
        )

        self._access_token: str | None = None
        self._access_token_expires_at: float = 0.0

    def build_messages(
        self,
        user_text: str,
        context: dict[str, Any],
        intent: str,
        analytics_result: dict[str, Any] | None = None,
        fact_summary: str | None = None,
    ) -> list[dict[str, str]]:
        system_prompt = self._build_system_prompt(
            intent=intent,
            context=context,
            analytics_result=analytics_result,
            fact_summary=fact_summary,
        )

        return [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_text,
            },
        ]

    def generate(
        self,
        messages: list[dict[str, str]],
        intent: str,
        analytics_result: dict[str, Any] | None = None,
    ) -> str:
        provider = (self.provider or "gigachat").lower().strip()

        if provider == "gigachat":
            return self._generate_gigachat(messages)

        return self._generate_openai_compatible(messages)


    def health(self) -> dict[str, Any]:
        provider = (self.provider or "gigachat").lower().strip()

        if provider == "gigachat":
            if not self.gigachat_auth_key or not self.gigachat_auth_url or not self.gigachat_base_url:
                return {
                    "configured": False,
                    "available": False,
                    "provider": "gigachat",
                    "message": "GigaChat не настроен",
                }

            try:
                token = self._get_access_token()
                models = self._list_gigachat_models(token)
                return {
                    "configured": True,
                    "available": True,
                    "provider": "gigachat",
                    "message": "GigaChat доступен",
                    "models": models,
                }
            except Exception as e:
                return {
                    "configured": True,
                    "available": False,
                    "provider": "gigachat",
                    "message": f"Ошибка подключения к GigaChat: {str(e)}",
                }

        if not self.base_url or not self.model_name:
            return {
                "configured": False,
                "available": False,
                "provider": provider,
                "message": "LLM не настроена",
            }

        return {
            "configured": True,
            "available": True,
            "provider": provider,
            "message": "LLM настроена",
        }


    def _generate_gigachat(self, messages: list[dict[str, str]]) -> str:
        token = self._get_access_token()
        payload = {
            "model": self.gigachat_model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
            "n": 1,
            "max_tokens": 1024,
            "repetition_penalty": 1,
        }

        response = requests.post(
            f"{self.gigachat_base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=self.gigachat_timeout,
            verify=self.gigachat_verify_ssl,
        )

        # Ключевой фикс: refresh + retry один раз при expired token
        if response.status_code == 401:
            self._access_token = None
            self._access_token_expires_at = 0.0
            token = self._get_access_token()

            response = requests.post(
                f"{self.gigachat_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.gigachat_timeout,
                verify=self.gigachat_verify_ssl,
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
        now = time.time()

        if self._access_token and now < self._access_token_expires_at - 60:
            return self._access_token

        if not self.gigachat_auth_key:
            raise RuntimeError("GigaChat auth key не задан")

        headers = {
            "Authorization": f"Basic {self.gigachat_auth_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        response = requests.post(
            self.gigachat_auth_url,
            headers=headers,
            data={"scope": self.gigachat_scope},
            timeout=self.gigachat_timeout,
            verify=self.gigachat_verify_ssl,
        )
        response.raise_for_status()

        data = response.json()
        access_token = data.get("access_token")
        expires_at = data.get("expires_at")

        if not access_token:
            raise RuntimeError("GigaChat не вернул access_token")

        self._access_token = access_token

        if expires_at:
            try:
                self._access_token_expires_at = float(expires_at) / 1000.0
            except Exception:
                self._access_token_expires_at = now + 1800
        else:
            self._access_token_expires_at = now + 1800

        return self._access_token

    def _list_gigachat_models(self, token: str) -> list[str]:
        response = requests.get(
            f"{self.gigachat_base_url.rstrip('/')}/models",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=self.gigachat_timeout,
            verify=self.gigachat_verify_ssl,
        )

        if response.status_code == 401:
            self._access_token = None
            self._access_token_expires_at = 0.0
            token = self._get_access_token()

            response = requests.get(
                f"{self.gigachat_base_url.rstrip('/')}/models",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.gigachat_timeout,
                verify=self.gigachat_verify_ssl,
            )

        response.raise_for_status()
        data = response.json()

        items = data.get("data", [])
        result = []
        for item in items:
            model_id = item.get("id")
            if model_id:
                result.append(model_id)

        return result


    def _generate_openai_compatible(self, messages: list[dict[str, str]]) -> str:
        if not self.base_url:
            raise RuntimeError("LLM_BASE_URL не задан")
        if not self.model_name:
            raise RuntimeError("LLM_MODEL_NAME не задан")

        response = requests.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            json={
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
            },
            headers=self._build_openai_compatible_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "LLM вернула пустой ответ."

        content = choices[0].get("message", {}).get("content")
        if not content:
            return "LLM не вернула текст ответа."

        return content.strip()

    def _build_openai_compatible_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


    def _build_system_prompt(
        self,
        intent: str,
        context: dict[str, Any],
        analytics_result: dict[str, Any] | None = None,
        fact_summary: str | None = None,
    ) -> str:
        lines: list[str] = []

        lines.append(
            "Ты — инвестиционный ассистент. Отвечай кратко, по делу, на русском языке."
        )
        lines.append(
            "Используй только подтверждённые данные из переданного контекста. Не выдумывай цифры, даты и источники."
        )
        lines.append(
            "Если данных недостаточно, честно скажи об этом."
        )
        lines.append(
            "Не давай гарантий доходности и не обещай будущий рост."
        )

        if intent:
            lines.append(f"Текущий intent: {intent}.")

        if fact_summary:
            lines.append(f"Факты: {fact_summary}")

        if analytics_result:
            trend_summary = analytics_result.get("trend_summary")
            calculated = analytics_result.get("calculated_indicators", {})
            if trend_summary:
                lines.append(f"Аналитический вывод: {trend_summary}")
            if calculated:
                lines.append(f"Структурированные данные: {calculated}")

        market_context = context.get("market_context")
        if market_context:
            lines.append(f"Рыночный контекст: {market_context}")

        technical_analysis_context = context.get("technical_analysis_context")
        if technical_analysis_context:
            lines.append(f"Технический анализ: {technical_analysis_context}")

        dividend_context = context.get("dividend_context")
        if dividend_context:
            lines.append(f"Дивиденды: {dividend_context}")

        expected_dividend_context = context.get("expected_dividend_context")
        if expected_dividend_context:
            lines.append(f"Ожидаемые дивиденды: {expected_dividend_context}")

        fx_context = context.get("fx_context")
        if fx_context:
            lines.append(f"Валютный контекст: {fx_context}")

        bond_context = context.get("bond_context")
        if bond_context:
            lines.append(f"Контекст облигации: {bond_context}")

        dividend_ranking_context = context.get("dividend_ranking_context")
        if dividend_ranking_context:
            lines.append(f"Рейтинг дивидендных акций: {dividend_ranking_context}")

        dividend_aristocrats_context = context.get("dividend_aristocrats_context")
        if dividend_aristocrats_context:
            lines.append(f"Устойчивые дивидендные компании: {dividend_aristocrats_context}")

        bond_ranking_context = context.get("bond_ranking_context")
        if bond_ranking_context:
            lines.append(f"Рейтинг облигаций: {bond_ranking_context}")

        return "\n".join(lines)


    def _to_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}