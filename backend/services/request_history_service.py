from sqlalchemy.orm import Session

from backend.models import RequestHistory, User


class RequestHistoryService:
    def log_request(
        self,
        db: Session,
        user: User,
        message_id: int | None,
        user_query: str,
        system_response: str | None,
        intent_type: str
    ) -> RequestHistory:
        entry = RequestHistory(
            user_id=user.id,
            message_id=message_id,
            user_query=user_query,
            system_response=system_response,
            intent_type=intent_type
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def get_user_history(self, db: Session, user_id: int) -> list[RequestHistory]:
        return (
            db.query(RequestHistory)
            .filter(RequestHistory.user_id == user_id)
            .order_by(RequestHistory.timestamp.desc())
            .all()
        )