import json
from sqlalchemy.orm import Session

from backend.models import AnalyticalReport, User


class AnalyticalReportService:
    def save_report(
        self,
        db: Session,
        user: User,
        message_id: int | None,
        intent_type: str,
        analytics_result: dict | None
    ) -> AnalyticalReport | None:
        if not analytics_result:
            return None

        report = AnalyticalReport(
            user_id=user.id,
            message_id=message_id,
            intent_type=intent_type,
            report_type=analytics_result.get("report_type", intent_type),
            trend_summary=analytics_result.get("trend_summary"),
            calculated_indicators=json.dumps(
                analytics_result.get("calculated_indicators", {}),
                ensure_ascii=False
            ),
            confidence_score=analytics_result.get("confidence_score")
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def get_user_reports(self, db: Session, user_id: int) -> list[AnalyticalReport]:
        return (
            db.query(AnalyticalReport)
            .filter(AnalyticalReport.user_id == user_id)
            .order_by(AnalyticalReport.created_at.desc())
            .all()
        )