from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import ChatMessageCreate, ChatProcessResponse, ChatResponse
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.get("/me", response_model=ChatResponse)
def get_my_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = chat_service.get_chat_with_messages(db, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


@router.post("/me/messages", response_model=ChatProcessResponse)
def send_message(
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = chat_service.process_user_message(
            db=db,
            user=current_user,
            user_text=payload.content
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))