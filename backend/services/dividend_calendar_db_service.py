import re
from sqlalchemy.orm import Session

from backend.models import DividendCalendarItem


class DividendCalendarDBService:
    def get_by_ticker(self, db: Session, ticker: str, year: int = 2026):
        ticker = (ticker or "").upper().strip()
        if not ticker:
            return None

        return (
            db.query(DividendCalendarItem)
            .filter(DividendCalendarItem.ticker == ticker)
            .order_by(DividendCalendarItem.t1_buy_date.desc())
            .first()
        )

    def search_by_name(self, db: Session, name: str, year: int = 2026):
        normalized = self._normalize_name(name)
        if not normalized:
            return None

        candidates = self._build_name_candidates(normalized)

        for candidate in candidates:
            item = (
                db.query(DividendCalendarItem)
                .filter(DividendCalendarItem.security_name.ilike(f"%{candidate}%"))
                .order_by(DividendCalendarItem.t1_buy_date.desc())
                .first()
            )
            if item:
                return item

        return None

    def find_best_match(
            self,
            db: Session,
            *,
            ticker: str | None = None,
            display_name: str | None = None,
            user_text: str | None = None,
            year: int = 2026,
    ):
        text = (user_text or "").lower()

        if ticker:
            item = self.get_by_ticker(db, ticker, year)
            if item:
                return item

        alias_map = {
            "татнефть": ["TATN", "TATNP"],
            "татнефти": ["TATN", "TATNP"],
            "tatneft": ["TATN", "TATNP"],

            "озон": ["OZON", "OZPH"],
            "ozon": ["OZON", "OZPH"],

            "черкизово": ["GCHE"],
            "cherkizovo": ["GCHE"],

            "лукойл": ["LKOH"],
            "lukoil": ["LKOH"],
        }

        for key, tickers in alias_map.items():
            if key in text:
                for t in tickers:
                    item = self.get_by_ticker(db, t, year)
                    if item:
                        return item

        if display_name:
            item = (
                db.query(DividendCalendarItem)
                .filter(DividendCalendarItem.security_name.ilike(f"%{display_name}%"))
                .order_by(DividendCalendarItem.t1_buy_date.desc())
                .first()
            )
            if item:
                return item

        all_items = db.query(DividendCalendarItem).all()

        normalized_text = self._normalize_name(text)

        for item in all_items:
            name = self._normalize_name(item.security_name)

            if name and name in normalized_text:
                return item

            if normalized_text and normalized_text in name:
                return item

        tokens = normalized_text.split()

        for token in tokens:
            if len(token) < 4:
                continue

            for item in all_items:
                name = self._normalize_name(item.security_name)
                if token in name:
                    return item

        return None

    def to_context_dict(self, item) -> dict | None:
        if not item:
            return None

        return {
            "ticker": item.ticker,
            "name": item.security_name,
            "year": 2026,
            "dividend_per_share": item.dividend_rub,
            "currency": "RUB",
            "t1_buy_date": item.t1_buy_date.isoformat() if item.t1_buy_date else None,
            "record_date": item.record_date.isoformat() if item.record_date else None,
            "planned_payment_date": item.planned_payment_date.isoformat() if item.planned_payment_date else None,
            "declared_date": None,
            "status": item.status,
            "price": item.share_price,
            "dividend_yield_percent": item.dividend_yield_percent,
            "source": "dividend_calendar_2026_db",
            "dividend_found": True,
        }

    def _normalize_name(self, value: str | None) -> str:
        if not value:
            return ""
        value = value.lower().replace("ё", "е").strip()
        value = re.sub(r"[\"'«»()]", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _build_name_candidates(self, value: str) -> list[str]:
        if not value:
            return []

        stop_words = {
            "по", "дивидендам", "дивиденды", "дата", "отсечки", "когда",
            "какой", "будет", "ожидается", "до", "даты", "купить",
            "под", "в", "году", "год", "плановая", "выплата", "выплаты",
        }

        tokens = [t for t in value.split() if t not in stop_words and len(t) >= 3]

        candidates = []
        if value:
            candidates.append(value)

        if tokens:
            candidates.append(" ".join(tokens))

        for token in sorted(set(tokens), key=len, reverse=True):
            candidates.append(token)

        extra = []
        joined = " ".join(tokens)

        if "татнефт" in joined:
            extra.extend(["татнефть", "татнефть ао", "татнефть ап"])
        if "озон" in joined:
            extra.extend(["озон", "мкпао озон", "озонфарм"])
        if "черкиз" in joined:
            extra.append("черкизово")
        if "лукойл" in joined or "лукоил" in joined:
            extra.append("лукойл")

        for item in extra:
            if item not in candidates:
                candidates.append(item)

        return candidates