from sqlalchemy.orm import Session

from backend.models import MarketData, FinancialInstrument, ExternalSource
from backend.services.instrument_resolver_service import InstrumentResolverService
from backend.services.instrument_service import InstrumentService
from backend.services.market_provider_service import MarketProviderService


class MarketService:
    PROVIDER_SOURCE_NAME = "moex_iss"

    def __init__(self):
        self.instrument_resolver = InstrumentResolverService()
        self.instrument_service = InstrumentService()
        self.market_provider = MarketProviderService()

    def ensure_source(self, db: Session, source_name: str, endpoint_url: str | None = None) -> ExternalSource:
        source = db.query(ExternalSource).filter(ExternalSource.name == source_name).first()
        if source:
            return source

        source = ExternalSource(
            name=source_name,
            endpoint_url=endpoint_url,
            is_active=True
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def ensure_instrument(
        self,
        db: Session,
        ticker: str,
        name: str = "",
        instrument_type: str = "stock",
        currency: str = "RUB"
    ) -> FinancialInstrument:
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker.upper()
        ).first()
        if instrument:
            return instrument

        instrument = FinancialInstrument(
            ticker=ticker.upper(),
            name=name or ticker.upper(),
            type=instrument_type,
            currency=currency
        )
        db.add(instrument)
        db.commit()
        db.refresh(instrument)
        return instrument

    def ensure_instrument_from_query(self, db: Session, query: str) -> FinancialInstrument | None:
        return self.instrument_service.resolve_or_create_instrument(db, query)

    def save_market_data(
        self,
        db: Session,
        ticker: str,
        source_name: str,
        price,
        volume,
        recorded_at
    ) -> MarketData:
        ticker = ticker.upper()

        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker
        ).first()
        if not instrument:
            raise ValueError(f"Инструмент {ticker} не найден")

        source = db.query(ExternalSource).filter(
            ExternalSource.name == source_name
        ).first()
        if not source:
            raise ValueError(f"Источник {source_name} не найден")

        market_entry = MarketData(
            ticker=ticker,
            source_name=source_name,
            price=price,
            volume=volume,
            recorded_at=recorded_at
        )
        db.add(market_entry)
        db.commit()
        db.refresh(market_entry)
        return market_entry

    def get_latest_price_any_source(self, db: Session, ticker: str) -> MarketData | None:
        return (
            db.query(MarketData)
            .filter(MarketData.ticker == ticker.upper())
            .order_by(MarketData.recorded_at.desc(), MarketData.id.desc())
            .first()
        )

    def get_latest_price_by_source(self, db: Session, ticker: str, source_name: str) -> MarketData | None:
        return (
            db.query(MarketData)
            .filter(
                MarketData.ticker == ticker.upper(),
                MarketData.source_name == source_name
            )
            .order_by(MarketData.recorded_at.desc(), MarketData.id.desc())
            .first()
        )

    def get_latest_price_prefer_provider(self, db: Session, ticker: str) -> MarketData | None:
        provider_entry = self.get_latest_price_by_source(db, ticker, self.PROVIDER_SOURCE_NAME)
        if provider_entry:
            return provider_entry

        return self.get_latest_price_any_source(db, ticker)

    def get_latest_price(self, db: Session, ticker: str) -> MarketData | None:
        return self.get_latest_price_prefer_provider(db, ticker)

    def extract_ticker_from_text(self, db: Session, text: str, resolved_instrument: dict | None = None) -> str | None:
        if resolved_instrument and resolved_instrument.get("ticker"):
            return resolved_instrument["ticker"].upper()
        return self.instrument_resolver.resolve_ticker_from_text(db, text)

    def extract_tickers_from_text(self, db: Session, text: str, resolved_instrument: dict | None = None) -> list[str]:
        if resolved_instrument and resolved_instrument.get("ticker"):
            return [resolved_instrument["ticker"].upper()]
        return self.instrument_resolver.resolve_tickers_from_text(db, text)

    def refresh_latest_price_from_provider(self, db: Session, ticker: str) -> MarketData | None:
        ticker = ticker.upper().strip()

        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker
        ).first()
        if not instrument:
            instrument = self.ensure_instrument_from_query(db, ticker)
            if not instrument:
                instrument = self.ensure_instrument(
                    db=db,
                    ticker=ticker,
                    name=ticker,
                    instrument_type="stock",
                    currency="RUB"
                )

        self.ensure_source(
            db=db,
            source_name=self.PROVIDER_SOURCE_NAME,
            endpoint_url=self.market_provider.base_url
        )

        quote = self.market_provider.fetch_latest_share_quote(ticker=ticker)

        if quote.get("price") is None:
            return None

        return self.save_market_data(
            db=db,
            ticker=ticker,
            source_name=self.PROVIDER_SOURCE_NAME,
            price=quote["price"],
            volume=quote["volume"],
            recorded_at=quote["recorded_at"]
        )

    def build_market_context(self, db: Session, user_text: str, resolved_instrument: dict | None = None) -> dict | None:
        ticker = self.extract_ticker_from_text(db, user_text, resolved_instrument=resolved_instrument)
        if not ticker:
            return None

        display_name = self.instrument_resolver.get_instrument_display_name(db, ticker)

        refreshed = self.refresh_latest_price_from_provider(db, ticker)
        latest = refreshed or self.get_latest_price_prefer_provider(db, ticker)

        if not latest:
            return {
                "ticker": ticker,
                "display_name": display_name,
                "price_found": False
            }

        return {
            "ticker": latest.ticker,
            "display_name": display_name,
            "price_found": True,
            "price": float(latest.price),
            "volume": float(latest.volume) if latest.volume is not None else None,
            "recorded_at": latest.recorded_at.isoformat(),
            "source_name": latest.source_name
        }

    def build_multi_market_context(self, db: Session, user_text: str, resolved_instrument: dict | None = None) -> list[dict]:
        tickers = self.extract_tickers_from_text(db, user_text, resolved_instrument=resolved_instrument)
        results = []

        for ticker in tickers:
            display_name = self.instrument_resolver.get_instrument_display_name(db, ticker)

            refreshed = self.refresh_latest_price_from_provider(db, ticker)
            latest = refreshed or self.get_latest_price_prefer_provider(db, ticker)

            if not latest:
                results.append({
                    "ticker": ticker,
                    "display_name": display_name,
                    "price_found": False
                })
            else:
                results.append({
                    "ticker": latest.ticker,
                    "display_name": display_name,
                    "price_found": True,
                    "price": float(latest.price),
                    "volume": float(latest.volume) if latest.volume is not None else None,
                    "recorded_at": latest.recorded_at.isoformat(),
                    "source_name": latest.source_name
                })

        return results

    def build_position_market_metrics(self, position_context: dict | None, market_context: dict | None) -> dict | None:
        if not position_context or not market_context:
            return None

        if not market_context.get("price_found"):
            return None

        avg_price = position_context["avg_price"]
        quantity = position_context["quantity"]
        current_price = market_context["price"]

        absolute_pnl_per_share = current_price - avg_price
        total_pnl = absolute_pnl_per_share * quantity

        pnl_percent = None
        if avg_price != 0:
            pnl_percent = (absolute_pnl_per_share / avg_price) * 100

        market_value = current_price * quantity
        invested_value = avg_price * quantity

        return {
            "ticker": position_context["ticker"],
            "quantity": quantity,
            "avg_price": avg_price,
            "current_price": current_price,
            "invested_value": round(invested_value, 4),
            "market_value": round(market_value, 4),
            "absolute_pnl": round(total_pnl, 4),
            "pnl_percent": round(pnl_percent, 4) if pnl_percent is not None else None
        }