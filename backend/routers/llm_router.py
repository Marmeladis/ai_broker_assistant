from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.services.llm_service import LLMService

router = APIRouter(prefix="/llm", tags=["llm"])
llm_service = LLMService()


@router.get("/health")
def llm_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return llm_service.healthcheck()