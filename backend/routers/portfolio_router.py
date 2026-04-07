from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import PortfolioPositionCreate, PortfolioPositionResponse
from backend.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
portfolio_service = PortfolioService()


@router.get("/me", response_model=list[PortfolioPositionResponse])
def get_my_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return portfolio_service.get_user_positions(db, current_user)


@router.post("/me/positions", response_model=PortfolioPositionResponse)
def add_position(
    payload: PortfolioPositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return portfolio_service.add_position(
            db=db,
            user=current_user,
            ticker=payload.ticker,
            quantity=payload.quantity,
            avg_price=payload.avg_price
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))