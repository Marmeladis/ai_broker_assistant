from datetime import datetime
from sqlalchemy.orm import Session

from ..auth import create_access_token
from ..models import User, UserSession


class SessionService:
    def start_session(self, db: Session, user: User):
        access_token, expires_at = create_access_token(data={"sub": str(user.id)})

        session = UserSession(
            user_id=user.id,
            access_token=access_token,
            is_active=True,
            expires_at=expires_at
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return access_token, session

    def get_active_session(self, db: Session, user_id: int) -> UserSession | None:
        return (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
            .order_by(UserSession.created_at.desc())
            .first()
        )

    def deactivate_session(self, db: Session, access_token: str) -> None:
        session = (
            db.query(UserSession)
            .filter(UserSession.access_token == access_token)
            .first()
        )
        if session:
            session.is_active = False
            db.commit()