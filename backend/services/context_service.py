from __future__ import annotations

from typing import Any

from backend.services.market_service import MarketService
from backend.services.price_history_service import PriceHistoryService
from backend.services.technical_analysis_service import TechnicalAnalysisService
from backend.services.dividend_service import DividendService
from backend.services.fx_service import FXService
from backend.services.bond_service import BondService


class ContextService:

    def __init__(
        self,
        market_service: MarketService,
        price_history_service: PriceHistoryService,
        technical_analysis_service: TechnicalAnalysisService,
        dividend_service: DividendService,
        fx_service: FXService,
        bond_service: BondService,
    ):
        self.market_service = market_service
        self.price_history_service = price_history_service
        self.technical_analysis_service = technical_analysis_service
        self.dividend_service = dividend_service
        self.fx_service = fx_service
        self.bond_service = bond_service

    def build_context(
        self,
        user_text: str,
        resolved_instrument: dict | None,
    ) -> dict[str, Any]:

        context: dict[str, Any] = {
            "market_context": None,
            "price_history_context": None,
            "technical_analysis_context": None,
            "dividend_context": None,
            "expected_dividend_context": None,
            "fx_context": None,
            "bond_context": None,
            "bond_ranking_context": None,
            "dividend_ranking_context": None,
            "dividend_aristocrats_context": None,
        }


        if resolved_instrument and resolved_instrument.get("ticker"):
            ticker = resolved_instrument["ticker"]

            try:
                market_data = self.market_service.get_market_data(ticker)
                context["market_context"] = market_data
            except Exception:
                context["market_context"] = None


            try:
                candles = self.price_history_service.get_candles(ticker)
                context["price_history_context"] = candles
            except Exception:
                candles = None
                context["price_history_context"] = None


            if candles:
                try:
                    ta = self.technical_analysis_service.analyze(candles)
                    context["technical_analysis_context"] = ta
                except Exception:
                    context["technical_analysis_context"] = None


            try:
                last_div = self.dividend_service.get_last_dividend(ticker)
                context["dividend_context"] = last_div
            except Exception:
                context["dividend_context"] = None

            try:
                expected_div = self.dividend_service.get_expected_dividend(ticker)
                context["expected_dividend_context"] = expected_div
            except Exception:
                context["expected_dividend_context"] = None

        try:
            fx_resolved = self.fx_service.resolve_fx_from_text(user_text)
            if fx_resolved:
                fx_data = self.fx_service.get_fx_price(fx_resolved["code"])
                context["fx_context"] = fx_data
        except Exception:
            context["fx_context"] = None


        if self._needs_dividend_ranking(user_text):
            try:
                ranking = self.dividend_service.get_top_dividend_stocks()
                context["dividend_ranking_context"] = ranking
            except Exception:
                context["dividend_ranking_context"] = None


        if self._needs_dividend_aristocrats(user_text):
            try:
                aristocrats = self.dividend_service.get_dividend_aristocrats()
                context["dividend_aristocrats_context"] = aristocrats
            except Exception:
                context["dividend_aristocrats_context"] = None


        if self._needs_bond_ranking(user_text):
            try:
                bonds = self.bond_service.get_top_bonds_by_coupon()
                context["bond_ranking_context"] = bonds
            except Exception:
                context["bond_ranking_context"] = None

        if resolved_instrument and resolved_instrument.get("is_bond"):
            try:
                bond_data = self.bond_service.get_bond_info(
                    resolved_instrument["ticker"]
                )
                context["bond_context"] = bond_data
            except Exception:
                context["bond_context"] = None

        return context

    def _needs_dividend_ranking(self, text: str) -> bool:
        text = text.lower()
        return any(marker in text for marker in [
            "топ дивиденд",
            "дивидендные акции",
            "самые дивидендные",
            "высокая дивдоходность",
            "наибольшие дивиденды",
            "у каких компаний",
        ])

    def _needs_dividend_aristocrats(self, text: str) -> bool:
        text = text.lower()
        return any(marker in text for marker in [
            "дивидендные аристократы",
            "стабильно платят дивиденды",
            "каждый год дивиденды",
            "устойчивые дивиденды",
        ])

    def _needs_bond_ranking(self, text: str) -> bool:
        text = text.lower()
        return any(marker in text for marker in [
            "облигации с высоким купоном",
            "топ облигаций",
            "самые доходные облигации",
            "рейтинг облигаций",
        ])