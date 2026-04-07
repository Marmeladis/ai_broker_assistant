from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import InstrumentCreate, MarketDataCreate, MarketDataResponse
from backend.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])
market_service = MarketService()


@router.post("/instruments")
def create_instrument(
    payload: InstrumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    instrument = market_service.ensure_instrument(
        db=db,
        ticker=payload.ticker,
        name=payload.name,
        instrument_type=payload.type,
        currency=payload.currency
    )
    return {
        "ticker": instrument.ticker,
        "name": instrument.name,
        "type": instrument.type,
        "currency": instrument.currency
    }


@router.post("/data", response_model=MarketDataResponse)
def add_market_data(
    payload: MarketDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return market_service.save_market_data(
            db=db,
            ticker=payload.ticker,
            source_name=payload.source_name,
            price=payload.price,
            volume=payload.volume,
            recorded_at=payload.recorded_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh/{ticker}", response_model=MarketDataResponse)
def refresh_market_data(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        instrument = market_service.ensure_instrument_from_query(db, ticker)
        resolved_ticker = instrument.ticker if instrument else ticker.upper()

        refreshed = market_service.refresh_latest_price_from_provider(db, resolved_ticker)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Не удалось получить цену у провайдера")
        return refreshed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления цены: {str(e)}")


@router.get("/price/{query}")
def get_latest_price(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        instrument = market_service.ensure_instrument_from_query(db, query)
        if not instrument:
            raise HTTPException(status_code=404, detail="Инструмент не найден")

        refreshed = market_service.refresh_latest_price_from_provider(db, instrument.ticker)
        latest = refreshed or market_service.get_latest_price_prefer_provider(db, instrument.ticker)

        if not latest:
            raise HTTPException(status_code=404, detail="Цена не найдена")

        return {
            "ticker": latest.ticker,
            "name": instrument.name,
            "price": float(latest.price),
            "volume": float(latest.volume) if latest.volume is not None else None,
            "recorded_at": latest.recorded_at,
            "source_name": latest.source_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения цены: {str(e)}")


@router.get("/resolve")
def resolve_instrument(
    query: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    instrument = market_service.ensure_instrument_from_query(db, query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    return {
        "ticker": instrument.ticker,
        "name": instrument.name,
        "type": instrument.type,
        "currency": instrument.currency
    }