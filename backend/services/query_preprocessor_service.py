from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.models import User
from backend.services.instrument_resolver_service import InstrumentResolverService
from backend.services.fx_service import FXService
from backend.services.bond_service import BondService


class QueryPreprocessorService:

    def __init__(
        self,
        instrument_resolver_service: InstrumentResolverService,
        fx_service: FXService,
        bond_service: BondService,
    ):
        self.instrument_resolver_service = instrument_resolver_service
        self.fx_service = fx_service
        self.bond_service = bond_service

    def preprocess(
        self,
        db: Session,
        user: User,
        user_text: str,
    ) -> dict[str, Any]:
        normalized_text = self._normalize_text(user_text)


        if self._looks_like_broad_market_query(normalized_text):
            return {
                "original_text": user_text,
                "normalized_text": normalized_text,
                "resolved_instrument": None,
                "query_kind": "broad_market_query",
            }


        fx_resolved = self.fx_service.resolve_fx_from_text(normalized_text)
        if fx_resolved:
            return {
                "original_text": user_text,
                "normalized_text": normalized_text,
                "resolved_instrument": None,
                "query_kind": "fx_query",
                "resolved_fx": fx_resolved,
            }

        if self._looks_like_single_bond_query(normalized_text):
            bond_resolved = self.bond_service.resolve_bond_from_text(normalized_text)
            if bond_resolved:
                return {
                    "original_text": user_text,
                    "normalized_text": normalized_text,
                    "resolved_instrument": bond_resolved,
                    "query_kind": "single_bond_query",
                }

        resolved_instrument = self.instrument_resolver_service.resolve(
            db=db,
            query=normalized_text,
        )

        return {
            "original_text": user_text,
            "normalized_text": normalized_text,
            "resolved_instrument": resolved_instrument,
            "query_kind": "instrument_query" if resolved_instrument else "generic_query",
        }


    def _normalize_text(self, text: str) -> str:
        return (text or "").strip()

    def _looks_like_broad_market_query(self, text: str) -> bool:
        text_lower = text.lower().replace("ё", "е").strip()

        broad_markers = [
            "топ дивиденд",
            "дивидендные акции",
            "акции с наибольшими дивидендами",
            "самые дивидендные акции",
            "самая высокая дивидендная доходность",
            "компании платят наибольшие дивиденды",
            "лучшие дивидендные бумаги",
            "какие акции платят наибольшие дивиденды",
            "за какие акции платят наибольшие дивиденды",
            "покажи топ дивидендных акций",
            "у каких компаний самая высокая дивдоходность",

            "дивидендные аристократы",
            "стабильно платят дивиденды",
            "платят дивиденды каждый год",
            "устойчивые дивиденды",
            "надежные дивидендные акции",
            "надежные дивидендные бумаги",
            "какие компании сейчас являются дивидендными аристократами",

            "какие облигации самые доходные",
            "топ облигаций по купону",
            "облигации с высоким купоном",
            "облигации с наибольшим купоном",
            "самые доходные облигации",
            "рейтинг облигаций",
            "покажи облигации с высоким купоном",

            "если я хочу дивиденды, что лучше купить",
            "что лучше купить под дивиденды",
            "какие бумаги лучше купить",
        ]

        return any(marker in text_lower for marker in broad_markers)

    def _looks_like_single_bond_query(self, text: str) -> bool:
        text_lower = text.lower().replace("ё", "е").strip()

        if self._looks_like_broad_market_query(text_lower):
            return False

        bond_markers = [
            "облигац",
            "облигации",
            "бонды",
            "выпуск",
            "isin",
            "ru000",
            "su0",
        ]

        coupon_markers = [
            "купон",
            "размер купона",
            "последний купон",
            "следующий купон",
            "купон платился",
            "расписание купонов",
            "дата выплаты купона",
        ]

        has_bond = any(marker in text_lower for marker in bond_markers)
        has_coupon_or_specificity = any(marker in text_lower for marker in coupon_markers)

        explicitly_identified = ("ru000" in text_lower) or ("isin" in text_lower)

        return (has_bond and has_coupon_or_specificity) or explicitly_identified