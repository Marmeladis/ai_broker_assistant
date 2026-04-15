from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import NewsItem, FinancialInstrument, ExternalSource, InstrumentAlias
from backend.services.instrument_resolver_service import InstrumentResolverService
from backend.services.news_provider_service import NewsProviderService


class NewsService:
    PROVIDER_SOURCE_NAME = "news_provider"

    def __init__(self):
        self.instrument_resolver = InstrumentResolverService()
        self.news_provider = NewsProviderService()

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

    def add_news(
        self,
        db: Session,
        ticker: str,
        source_name: str,
        title: str,
        content: str,
        published_at
    ) -> NewsItem:
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

        news_item = NewsItem(
            ticker=ticker,
            source_name=source_name,
            title=title,
            content=content,
            published_at=published_at
        )
        db.add(news_item)
        db.commit()
        db.refresh(news_item)
        return news_item

    def get_latest_news_by_ticker(self, db: Session, ticker: str, limit: int = 5) -> list[NewsItem]:
        return (
            db.query(NewsItem)
            .filter(NewsItem.ticker == ticker.upper())
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(limit)
            .all()
        )

    def refresh_news_from_provider(self, db: Session, ticker: str, limit: int = 10) -> list[NewsItem]:
        ticker = ticker.upper().strip()

        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker
        ).first()
        if not instrument:
            return []

        self.ensure_source(
            db=db,
            source_name=self.PROVIDER_SOURCE_NAME,
            endpoint_url="rss"
        )

        alias_rows = (
            db.query(InstrumentAlias)
            .filter(InstrumentAlias.ticker == ticker)
            .all()
        )
        aliases = [x.alias for x in alias_rows]

        provider_items = self.news_provider.fetch_news(
            ticker=ticker,
            instrument_name=instrument.name,
            aliases=aliases,
            max_items=limit
        )

        saved: list[NewsItem] = []

        for item in provider_items:
            title = item.get("title") or ""
            content = item.get("content") or ""
            published_at_raw = item.get("published_at")

            published_at = None
            if published_at_raw:
                try:
                    published_at = datetime.fromisoformat(published_at_raw)
                except Exception:
                    published_at = None

            if not published_at:
                published_at = datetime.utcnow()

            existing = (
                db.query(NewsItem)
                .filter(
                    NewsItem.ticker == ticker,
                    NewsItem.title == title,
                    NewsItem.published_at == published_at
                )
                .first()
            )
            if existing:
                saved.append(existing)
                continue

            news = NewsItem(
                ticker=ticker,
                source_name=item.get("source_name") or self.PROVIDER_SOURCE_NAME,
                title=title,
                content=content,
                published_at=published_at
            )
            db.add(news)
            db.commit()
            db.refresh(news)
            saved.append(news)

        return saved

    def extract_ticker_from_text(self, db: Session, text: str, resolved_instrument: dict | None = None) -> str | None:
        if resolved_instrument and resolved_instrument.get("ticker"):
            return resolved_instrument["ticker"].upper()
        return self.instrument_resolver.resolve_ticker_from_text(db, text)

    def extract_tickers_from_text(self, db: Session, text: str, resolved_instrument: dict | None = None) -> list[str]:
        if resolved_instrument and resolved_instrument.get("ticker"):
            return [resolved_instrument["ticker"].upper()]
        return self.instrument_resolver.resolve_tickers_from_text(db, text)

    def build_news_context(self, db: Session, user_text: str, resolved_instrument: dict | None = None) -> dict | None:
        ticker = self.extract_ticker_from_text(db, user_text, resolved_instrument=resolved_instrument)
        if not ticker:
            return None

        display_name = self.instrument_resolver.get_instrument_display_name(db, ticker)

        self.refresh_news_from_provider(db, ticker=ticker, limit=10)
        news_list = self.get_latest_news_by_ticker(db, ticker=ticker, limit=3)

        if not news_list:
            return {
                "ticker": ticker,
                "display_name": display_name,
                "news_found": False,
                "items": []
            }

        items = []
        for item in news_list:
            items.append({
                "title": item.title,
                "content": item.content,
                "published_at": item.published_at.isoformat(),
                "source_name": item.source_name
            })

        return {
            "ticker": ticker,
            "display_name": display_name,
            "news_found": True,
            "items": items
        }

    def build_multi_news_context(self, db: Session, user_text: str, resolved_instrument: dict | None = None) -> list[dict]:
        tickers = self.extract_tickers_from_text(db, user_text, resolved_instrument=resolved_instrument)
        results = []

        for ticker in tickers:
            display_name = self.instrument_resolver.get_instrument_display_name(db, ticker)

            self.refresh_news_from_provider(db, ticker=ticker, limit=10)
            news_list = self.get_latest_news_by_ticker(db, ticker=ticker, limit=3)

            if not news_list:
                results.append({
                    "ticker": ticker,
                    "display_name": display_name,
                    "news_found": False,
                    "items": []
                })
            else:
                items = []
                for item in news_list:
                    items.append({
                        "title": item.title,
                        "content": item.content,
                        "published_at": item.published_at.isoformat(),
                        "source_name": item.source_name
                    })

                results.append({
                    "ticker": ticker,
                    "display_name": display_name,
                    "news_found": True,
                    "items": items
                })

        return results