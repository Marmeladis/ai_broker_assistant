from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from backend.config import settings


class BondService:

    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS

    def resolve_bond_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Очень простой MVP-resolver:
        - ищет ISIN/RU-код вида RU000...
        - ищет явный secid в тексте, если пользователь сам его указал

        Позже можно расширить через поиск по MOEX issuer/name.
        """
        text = (text or "").strip()

        # Поиск ISIN российского формата
        import re
        isin_match = re.search(r"\bRU[0-9A-Z]{10}\b", text.upper())
        if isin_match:
            code = isin_match.group(0)
            return {
                "bond_code": code,
                "bond_kind": "isin",
                "display_name": code,
            }

        # Очень грубый поиск secid как токена без пробелов
        token_match = re.search(r"\b[A-Z0-9]{6,20}\b", text.upper())
        if token_match and "ОБЛИГ" in text.upper():
            code = token_match.group(0)
            return {
                "bond_code": code,
                "bond_kind": "secid_or_isin",
                "display_name": code,
            }

        # Специальный MVP-хак под Сбербанк
        lowered = text.lower().replace("ё", "е")
        if "сбер" in lowered and "облига" in lowered:
            # Можно заменить на более конкретную бумагу, если в проекте есть предпочитаемый secid
            return {
                "bond_code": "RU000A103YM3",
                "bond_kind": "isin",
                "display_name": "Сбербанк RU000A103YM3",
            }

        return None

    def get_coupon_schedule(self, bond_code: str) -> list[dict[str, Any]]:
        bond_code = (bond_code or "").strip().upper()
        if not bond_code:
            return []

        url = f"{self.base_url}/securities/{bond_code}/bondization.json"

        response = requests.get(
            url,
            params={
                "iss.meta": "off",
                "iss.only": "coupons"
            },
            timeout=self.timeout
        )
        response.raise_for_status()

        payload = response.json()
        coupons = payload.get("coupons", {})
        columns = coupons.get("columns", [])
        rows = coupons.get("data", [])

        if not columns or not rows:
            return []

        result = []
        for row in rows:
            item = dict(zip(columns, row))

            coupon_date = item.get("coupondate")
            coupon_value = item.get("value")

            if not coupon_date or coupon_value is None:
                continue

            result.append({
                "bond_code": item.get("secid") or bond_code,
                "isin": item.get("isin"),
                "name": item.get("name"),
                "coupon_date": coupon_date,
                "record_date": item.get("recorddate"),
                "start_date": item.get("startdate"),
                "coupon_value": self._to_float(item.get("value")),
                "coupon_percent": self._to_float(item.get("valueprc")),
                "face_value": self._to_float(item.get("facevalue")),
                "face_unit": item.get("faceunit"),
                "source_name": "moex_bondization",
            })

        result.sort(key=lambda x: x.get("coupon_date") or "")
        return result

    def get_last_coupon(self, bond_code: str) -> dict[str, Any] | None:
        schedule = self.get_coupon_schedule(bond_code)
        if not schedule:
            return None

        today = datetime.utcnow().date()

        past_items = []
        for item in schedule:
            try:
                coupon_date = datetime.fromisoformat(item["coupon_date"]).date()
                if coupon_date <= today:
                    past_items.append(item)
            except Exception:
                continue

        if not past_items:
            return None

        past_items.sort(key=lambda x: x["coupon_date"], reverse=True)
        return past_items[0]

    def get_next_coupon(self, bond_code: str) -> dict[str, Any] | None:
        schedule = self.get_coupon_schedule(bond_code)
        if not schedule:
            return None

        today = datetime.utcnow().date()

        future_items = []
        for item in schedule:
            try:
                coupon_date = datetime.fromisoformat(item["coupon_date"]).date()
                if coupon_date > today:
                    future_items.append(item)
            except Exception:
                continue

        if not future_items:
            return None

        future_items.sort(key=lambda x: x["coupon_date"])
        return future_items[0]

    def build_last_coupon_summary(self, coupon: dict[str, Any] | None) -> str:
        if not coupon:
            return "Данные по последнему купону не найдены."

        parts = [
            f"Последний известный купон по облигации {coupon.get('bond_code')} составил {coupon.get('coupon_value')} {coupon.get('face_unit') or ''}."
        ]

        if coupon.get("coupon_percent") is not None:
            parts.append(f"Купонная ставка в этом периоде: {coupon.get('coupon_percent')}%.")

        if coupon.get("coupon_date"):
            parts.append(f"Дата выплаты купона: {coupon.get('coupon_date')}.")

        if coupon.get("record_date"):
            parts.append(f"Дата фиксации владельцев: {coupon.get('record_date')}.")

        return " ".join(parts)

    def build_next_coupon_summary(self, coupon: dict[str, Any] | None) -> str:
        if not coupon:
            return "Данные по следующему купону не найдены."

        parts = [
            f"Следующий купон по облигации {coupon.get('bond_code')} ожидается {coupon.get('coupon_date')}."
        ]

        if coupon.get("coupon_value") is not None:
            parts.append(f"Размер купона: {coupon.get('coupon_value')} {coupon.get('face_unit') or ''}.")

        if coupon.get("coupon_percent") is not None:
            parts.append(f"Купонная ставка: {coupon.get('coupon_percent')}%.")

        if coupon.get("record_date"):
            parts.append(f"Дата фиксации владельцев: {coupon.get('record_date')}.")

        return " ".join(parts)

    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except Exception:
            return None

    def get_top_bonds_by_coupon(self, limit: int = 10) -> list[dict]:

        url = f"{self.base_url}/engines/stock/markets/bonds/securities.json"

        response = requests.get(
            url,
            params={
                "iss.meta": "off",
                "iss.only": "securities",
                "securities.columns": "SECID,SHORTNAME,COUPONVALUE,COUPONPERCENT,FACEVALUE",
            },
            timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json().get("securities", {})
        columns = data.get("columns", [])
        rows = data.get("data", [])

        result = []

        for row in rows:
            item = dict(zip(columns, row))

            coupon_percent = self._to_float(item.get("COUPONPERCENT"))
            coupon_value = self._to_float(item.get("COUPONVALUE"))

            if coupon_percent is None and coupon_value is None:
                continue

            result.append({
                "ticker": item.get("SECID"),
                "name": item.get("SHORTNAME"),
                "coupon_percent": coupon_percent,
                "coupon_value": coupon_value,
                "face_value": self._to_float(item.get("FACEVALUE")),
            })

        # сортировка по проценту
        result.sort(
            key=lambda x: x.get("coupon_percent") or 0,
            reverse=True
        )

        return result[:limit]