from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import RequestHistoryResponse
from backend.services.request_history_service import RequestHistoryService

router = APIRouter(prefix="/history", tags=["request_history"])
request_history_service = RequestHistoryService()


@router.get("/me", response_model=list[RequestHistoryResponse])
def get_my_request_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return request_history_service.get_user_history(db, current_user.id)