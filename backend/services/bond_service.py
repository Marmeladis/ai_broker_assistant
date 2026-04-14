from __future__ import annotations

from typing import Any

import requests

from backend.config import settings


class BondService:


    def __init__(self):
        self.base_url = settings.MOEX_ISS_BASE_URL.rstrip("/")
        self.timeout = settings.MARKET_HTTP_TIMEOUT_SECONDS


    def resolve_bond_from_text(self, text: str) -> dict[str, Any] | None:

        import re

        text = (text or "").strip()
        upper = text.upper()

        isin_match = re.search(r"\bRU[0-9A-Z]{10}\b", upper)
        if isin_match:
            code = isin_match.group(0)
            return {
                "ticker": code,
                "name": code,
                "is_bond": True,
            }

        su_match = re.search(r"\bSU[0-9A-Z]{9,15}\b", upper)
        if su_match:
            code = su_match.group(0)
            return {
                "ticker": code,
                "name": code,
                "is_bond": True,
            }

        token_match = re.search(r"\b[A-Z0-9]{6,20}\b", upper)
        lowered = text.lower().replace("ё", "е")
        if token_match and "облига" in lowered:
            code = token_match.group(0)
            return {
                "ticker": code,
                "name": code,
                "is_bond": True,
            }

        return None

    def get_bond_info(self, bond_code: str) -> dict[str, Any] | None:

        bond_code = (bond_code or "").strip().upper()
        if not bond_code:
            return None

        url = f"{self.base_url}/securities/{bond_code}/bondization.json"

        response = requests.get(
            url,
            params={
                "iss.meta": "off",
                "iss.only": "coupons",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        coupons = payload.get("coupons", {})
        columns = coupons.get("columns", [])
        rows = coupons.get("data", [])

        if not columns or not rows:
            return None

        schedule: list[dict[str, Any]] = []
        for row in rows:
            item = dict(zip(columns, row))

            coupon_date = item.get("coupondate")
            coupon_value = self._to_float(item.get("value"))
            coupon_percent = self._to_float(item.get("valueprc"))

            schedule.append(
                {
                    "ticker": item.get("secid") or bond_code,
                    "isin": item.get("isin"),
                    "name": item.get("name"),
                    "coupon_date": coupon_date,
                    "record_date": item.get("recorddate"),
                    "start_date": item.get("startdate"),
                    "coupon_value": coupon_value,
                    "coupon_percent": coupon_percent,
                    "face_value": self._to_float(item.get("facevalue")),
                    "face_unit": item.get("faceunit"),
                    "source_name": "moex_bondization",
                }
            )

        schedule.sort(key=lambda x: x.get("coupon_date") or "")

        last_known = None
        next_known = None
        today = self._today_str()

        for item in schedule:
            coupon_date = item.get("coupon_date")
            if not coupon_date:
                continue

            if coupon_date <= today:
                last_known = item
            elif coupon_date > today and next_known is None:
                next_known = item

        base_item = next_known or last_known or schedule[-1]

        return {
            "ticker": base_item.get("ticker") or bond_code,
            "name": base_item.get("name") or bond_code,
            "coupon_percent": base_item.get("coupon_percent"),
            "coupon_value": base_item.get("coupon_value"),
            "face_value": base_item.get("face_value"),
            "face_unit": base_item.get("face_unit"),
            "next_coupon_date": next_known.get("coupon_date") if next_known else None,
            "last_coupon_date": last_known.get("coupon_date") if last_known else None,
            "record_date": next_known.get("record_date") if next_known else (last_known.get("record_date") if last_known else None),
            "source_name": "moex_bondization",
        }

    def get_top_bonds_by_coupon(self, limit: int = 10) -> list[dict[str, Any]]:

        url = f"{self.base_url}/engines/stock/markets/bonds/securities.json"

        response = requests.get(
            url,
            params={
                "iss.meta": "off",
                "iss.only": "securities",
                "securities.columns": "SECID,SHORTNAME,COUPONVALUE,COUPONPERCENT,FACEVALUE,PRIMARY_BOARDID",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        securities = payload.get("securities", {})
        columns = securities.get("columns", [])
        rows = securities.get("data", [])

        if not columns or not rows:
            return []

        result: list[dict[str, Any]] = []

        for row in rows:
            item = dict(zip(columns, row))

            coupon_percent = self._to_float(item.get("COUPONPERCENT"))
            coupon_value = self._to_float(item.get("COUPONVALUE"))
            face_value = self._to_float(item.get("FACEVALUE"))

            if coupon_percent is None and coupon_value is None:
                continue

            if coupon_percent is not None and coupon_percent <= 0:
                continue
            if coupon_value is not None and coupon_value <= 0:
                continue

            result.append(
                {
                    "ticker": item.get("SECID"),
                    "name": item.get("SHORTNAME"),
                    "coupon_percent": coupon_percent,
                    "coupon_value": coupon_value,
                    "face_value": face_value,
                    "boardid": item.get("PRIMARY_BOARDID"),
                    "source_name": "moex_bonds_market",
                }
            )

        result.sort(
            key=lambda x: (
                x.get("coupon_percent") if x.get("coupon_percent") is not None else -1,
                x.get("coupon_value") if x.get("coupon_value") is not None else -1,
            ),
            reverse=True,
        )

        return result[:limit]


    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except Exception:
            return None

    def _today_str(self) -> str:
        from datetime import datetime
        return str(datetime.utcnow().date())