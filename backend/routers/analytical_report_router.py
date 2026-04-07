from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import AnalyticalReportResponse
from backend.services.analytical_report_service import AnalyticalReportService

router = APIRouter(prefix="/reports", tags=["analytical_reports"])
report_service = AnalyticalReportService()


@router.get("/me", response_model=list[AnalyticalReportResponse])
def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return report_service.get_user_reports(db, current_user.id)