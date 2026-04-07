from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import hash_password, verify_password, get_current_user
from backend.database import get_db
from backend.models import User, Chat
from backend.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
)
from backend.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["auth"])
session_service = SessionService()


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.login == payload.login).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )

    try:
        user = User(
            login=payload.login,
            password_hash=hash_password(payload.password),
            role="client"
        )
        db.add(user)
        db.flush()

        personal_chat = Chat(
            user_id=user.id,
            title="Личный чат с ассистентом"
        )
        db.add(personal_chat)

        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка регистрации: {str(e)}"
        )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.login == payload.login).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )

        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )

        access_token, session = session_service.start_session(db=db, user=user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "login": user.login,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "session": {
                "id": session.id,
                "user_id": session.user_id,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка входа: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user