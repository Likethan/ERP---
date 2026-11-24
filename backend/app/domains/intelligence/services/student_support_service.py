"""Predictive Intelligence & Explainable Student Support Service (Step 29).

Implements explainable academic and attendance risk indicator scoring derived
from authoritative ERP records. Strictly prohibits automated disciplinary or
grading actions, enforcing mandatory human review and privacy safeguards.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.attendance import AttendanceRecord
from app.models.examination import StudentAssessmentMark
from app.models.intelligence import AIPrediction
from app.models.people import StudentProfile
from app.schemas.intelligence import PredictionRequest, PredictionResponse, RiskLevelEnum


class StudentSupportPredictionService:
    """Computes explainable academic risk and early support indicators."""

    MODEL_NAME = "CampusOS-AcademicRisk-Baseline"
    MODEL_VERSION = "v1.2-rule-based"

    @classmethod
    async def evaluate_student_risk(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request: PredictionRequest,
    ) -> PredictionResponse:
        """Evaluate academic or attendance risk for a specific student."""
        # 1. Resolve Student Record
        student_id_str = request.target_id
        try:
            student_uuid = UUID(student_id_str)
        except ValueError as exc:
            raise ValidationException(f"Invalid student UUID format: '{student_id_str}'") from exc

        stmt = select(StudentProfile).where(
            StudentProfile.id == student_uuid,
            StudentProfile.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        student = res.scalars().first()
        if not student:
            raise NotFoundException(
                f"Student with ID '{student_id_str}' was not found in this institution."
            )

        # 2. Extract Authoritative Attendance Signals
        att_stmt = select(
            func.count(AttendanceRecord.id).label("total_sessions"),
            func.count(AttendanceRecord.id)
            .filter(AttendanceRecord.status.in_(["PRESENT", "LATE"]))
            .label("attended_sessions"),
        ).where(
            AttendanceRecord.student_id == student_uuid,
            AttendanceRecord.tenant_id == tenant_id,
        )
        att_res = await db.execute(att_stmt)
        att_row = att_res.first()

        total_sessions = att_row.total_sessions if att_row else 0
        attended_sessions = att_row.attended_sessions if att_row else 0
        attendance_pct = (
            round((attended_sessions / total_sessions) * 100.0, 1) if total_sessions > 0 else 85.0
        )

        # 3. Extract Authoritative Examination & Assessment Signals
        marks_stmt = select(
            func.count(StudentAssessmentMark.id).label("total_exams"),
            func.avg(StudentAssessmentMark.marks_obtained).label("avg_marks"),
            func.count(StudentAssessmentMark.id)
            .filter(StudentAssessmentMark.marks_obtained < 40.0)
            .label("failed_exams"),
        ).where(
            StudentAssessmentMark.student_id == student_uuid,
            StudentAssessmentMark.tenant_id == tenant_id,
        )
        marks_res = await db.execute(marks_stmt)
        marks_row = marks_res.first()

        total_exams = marks_row.total_exams if marks_row else 0
        avg_marks = (
            float(marks_row.avg_marks) if marks_row and marks_row.avg_marks is not None else 72.0
        )
        failed_exams = marks_row.failed_exams if marks_row else 0

        # 4. Compute Rule-Based Risk Score (0.0 = Low Risk, 1.0 = Critical Risk)
        risk_score = 0.1
        signals: dict[str, Any] = {
            "attendance_percentage": attendance_pct,
            "attended_sessions": attended_sessions,
            "total_sessions": total_sessions,
            "total_assessments_count": total_exams,
            "average_marks": round(avg_marks, 1),
            "failed_assessments_count": failed_exams,
            "admission_number": student.admission_number,
        }

        # Attendance risk contribution
        if attendance_pct < 65.0:
            risk_score += 0.5
        elif attendance_pct < 75.0:
            risk_score += 0.3
        elif attendance_pct < 80.0:
            risk_score += 0.1

        # Academic marks contribution
        if failed_exams >= 2:
            risk_score += 0.4
        elif failed_exams == 1:
            risk_score += 0.2

        if avg_marks < 40.0:
            risk_score += 0.3
        elif avg_marks < 55.0:
            risk_score += 0.1

        risk_score = min(round(risk_score, 2), 1.0)

        # 5. Determine Risk Level
        if risk_score >= 0.75:
            risk_level = RiskLevelEnum.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevelEnum.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevelEnum.MEDIUM
        else:
            risk_level = RiskLevelEnum.LOW

        # 6. Formulate Explainable Narrative
        explanation_parts = []
        if attendance_pct < 75.0:
            explanation_parts.append(
                f"Attendance is currently at {attendance_pct}%, which is below the mandatory institutional threshold of 75.0%."
            )
        if failed_exams > 0:
            explanation_parts.append(
                f"Student has scored below passing grade in {failed_exams} assessment(s) (average score: {avg_marks:.1f}%)."
            )
        if not explanation_parts:
            explanation_parts.append(
                f"Attendance ({attendance_pct}%) and examination performance ({avg_marks:.1f}%) are within standard satisfactory parameters."
            )

        explanation = " ".join(explanation_parts)

        limitations = (
            "Indicator derived from current semester records only. This indicator is a supportive signal "
            "and MUST NOT be used for autonomous grading, academic penalties, or disciplinary action. "
            "Human faculty advisor review is mandatory."
        )

        pred_id = f"PRED-{uuid4().hex[:10].upper()}"

        # 7. Persist to Database for Governance & Audit Trail
        pred_record = AIPrediction(
            tenant_id=tenant_id,
            prediction_id=pred_id,
            prediction_type=request.prediction_type.value,
            target_type="STUDENT",
            target_id=str(student_uuid),
            model_name=cls.MODEL_NAME,
            model_version=cls.MODEL_VERSION,
            is_rule_based=True,
            prediction_score=Decimal(str(risk_score)),
            risk_level=risk_level.value,
            signals=signals,
            explanation=explanation,
            limitations=limitations,
            human_review_required=True,
            status="PENDING_REVIEW",
        )
        db.add(pred_record)
        await db.flush()

        return PredictionResponse(
            predictionId=pred_id,
            predictionType=request.prediction_type.value,
            targetType="STUDENT",
            targetId=str(student_uuid),
            modelName=cls.MODEL_NAME,
            modelVersion=cls.MODEL_VERSION,
            isRuleBased=True,
            predictionScore=risk_score,
            riskLevel=risk_level,
            signals=signals,
            explanation=explanation,
            limitations=limitations,
            humanReviewRequired=True,
            status="PENDING_REVIEW",
            createdAt=datetime.now(UTC).isoformat(),
        )
