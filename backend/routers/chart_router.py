from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.services.price_history_service import PriceHistoryService
from backend.services.technical_analysis_service import TechnicalAnalysisService
from backend.services.instrument_service import InstrumentService

router = APIRouter(prefix="/charts", tags=["charts"])

price_history_service = PriceHistoryService()
ta_service = TechnicalAnalysisService()
instrument_service = InstrumentService()


@router.get("/candles/{query}")
def get_candles(
    query: str,
    interval: str = Query(default="24"),
    limit: int = Query(default=30, ge=5, le=300),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        instrument = instrument_service.resolve_or_create_instrument(db, query)
        if not instrument:
            raise HTTPException(status_code=404, detail="Инструмент не найден")

        ticker = instrument.ticker.upper().strip()

        candles = price_history_service.get_candles(
            ticker=ticker,
            interval=interval,
            limit=limit
        )

        if not candles:
            raise HTTPException(status_code=404, detail="Свечи не найдены")

        analysis = ta_service.analyze(candles)

        return {
            "ticker": ticker,
            "name": instrument.name,
            "interval": interval,
            "limit": limit,
            "candles": candles,
            "analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки свечей: {str(e)}"
        )