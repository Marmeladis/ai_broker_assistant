from fastapi import APIRouter, Depends

from backend.services.news_service import NewsService
from backend.auth import get_current_user

router = APIRouter(prefix="/news", tags=["news"])

news_service = NewsService()


@router.get("/{ticker}")
def get_news(ticker: str, user=Depends(get_current_user)):
    items = news_service.get_news_by_ticker(ticker)

    return {
        "ticker": ticker,
        "items": items
    }