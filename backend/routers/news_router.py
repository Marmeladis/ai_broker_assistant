from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.services.news_service import NewsService
from backend.services.instrument_service import InstrumentService

router = APIRouter(prefix="/news", tags=["news"])

news_service = NewsService()
instrument_service = InstrumentService()


@router.post("/refresh/{query}")
def refresh_news(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    instrument = instrument_service.resolve_or_create_instrument(db, query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    items = news_service.refresh_news_from_provider(
        db=db,
        ticker=instrument.ticker,
        limit=10
    )

    return {
        "ticker": instrument.ticker,
        "name": instrument.name,
        "loaded_count": len(items)
    }


@router.get("/{query}")
def get_news(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    instrument = instrument_service.resolve_or_create_instrument(db, query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    news_service.refresh_news_from_provider(db=db, ticker=instrument.ticker, limit=10)
    items = news_service.get_latest_news_by_ticker(db, instrument.ticker, limit=5)

    return {
        "ticker": instrument.ticker,
        "name": instrument.name,
        "items": [
            {
                "title": x.title,
                "content": x.content,
                "published_at": x.published_at.isoformat(),
                "source_name": x.source_name
            }
            for x in items
        ]
    }