"""Enterprise Data Quality & Analytics Reconciliation Framework (Step 28).

Executes automated reconciliation between operational source-of-truth records and
derived analytical metrics, detecting discrepancies, invalid ranges, and data anomalies.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import (
    AnalyticsDailyMetric,
    AnalyticsReconciliationFinding,
    ReconciliationSeverity,
    ReconciliationStatus,
)
from app.models.attendance import AttendanceRecord
from app.models.examination import StudentAssessmentMark
from app.models.finance import PaymentTransaction
from app.models.people import StudentProfile

logger = logging.getLogger("campusos.analytics.reconciliation")


class DataQualityReconciliationService:
    """Detects discrepancies between operational domain tables and analytical rollups."""

    @classmethod
    async def run_tenant_reconciliation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[AnalyticsReconciliationFinding]:
        """Execute all data-quality and reconciliation rules for a tenant."""
        now = datetime.now(UTC)
        findings: list[AnalyticsReconciliationFinding] = []

        # ---------------------------------------------------------------------
        # Rule 1: Finance Collections Reconciliation
        # Operational: Confirmed gateway payments (status == 'SUCCESS')
        # Analytical: Sum of 'confirmed_collections' in analytics_daily_metrics
        # ---------------------------------------------------------------------
        op_payments_stmt = select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            and_(
                PaymentTransaction.tenant_id == tenant_id,
                PaymentTransaction.status == "SUCCESS",
            )
        )
        op_payments_val = Decimal(str((await db.execute(op_payments_stmt)).scalar() or 0))

        an_payments_stmt = select(
            func.coalesce(func.sum(AnalyticsDailyMetric.value_numeric), 0)
        ).where(
            and_(
                AnalyticsDailyMetric.tenant_id == tenant_id,
                AnalyticsDailyMetric.metric_id == "confirmed_collections",
                AnalyticsDailyMetric.dimension_type == "GLOBAL",
            )
        )
        an_payments_val = Decimal(str((await db.execute(an_payments_stmt)).scalar() or 0))

        diff_payments = abs(op_payments_val - an_payments_val)
        if diff_payments > Decimal("0.01") and op_payments_val > 0:
            finding = AnalyticsReconciliationFinding(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_code="FIN_PAYMENTS_RECONCILIATION",
                severity=(
                    ReconciliationSeverity.ERROR
                    if diff_payments > Decimal("1000")
                    else ReconciliationSeverity.WARNING
                ),
                metric_id="confirmed_collections",
                source_table="finance_payments",
                operational_value=op_payments_val,
                analytics_value=an_payments_val,
                discrepancy_delta=diff_payments,
                details_json={
                    "message": (
                        "Operational confirmed payments sum does not match analytical rollup total."
                    ),
                    "operational_sum": str(op_payments_val),
                    "analytical_sum": str(an_payments_val),
                },
                resolution_status=ReconciliationStatus.OPEN,
                detected_at=now,
            )
            db.add(finding)
            findings.append(finding)

        # ---------------------------------------------------------------------
        # Rule 2: Active Student Count Consistency
        # Operational: Headcount in people_students WHERE status == 'ACTIVE'
        # ---------------------------------------------------------------------
        op_students_stmt = select(func.count(StudentProfile.id)).where(
            and_(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.status == "ACTIVE",
            )
        )
        op_students_count = int((await db.execute(op_students_stmt)).scalar() or 0)

        an_students_stmt = select(
            func.coalesce(func.max(AnalyticsDailyMetric.value_numeric), 0)
        ).where(
            and_(
                AnalyticsDailyMetric.tenant_id == tenant_id,
                AnalyticsDailyMetric.metric_id == "total_active_students",
            )
        )
        an_students_val = int((await db.execute(an_students_stmt)).scalar() or 0)

        if an_students_val > 0 and op_students_count != an_students_val:
            finding = AnalyticsReconciliationFinding(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_code="ACAD_STUDENT_STATUS_CONSISTENCY",
                severity=ReconciliationSeverity.WARNING,
                metric_id="total_active_students",
                source_table="people_students",
                operational_value=Decimal(op_students_count),
                analytics_value=Decimal(an_students_val),
                discrepancy_delta=Decimal(abs(op_students_count - an_students_val)),
                details_json={
                    "message": (
                        "Operational active student headcount differs from latest daily rollup."
                    ),
                    "operational_count": op_students_count,
                    "analytics_count": an_students_val,
                },
                resolution_status=ReconciliationStatus.OPEN,
                detected_at=now,
            )
            db.add(finding)
            findings.append(finding)

        # ---------------------------------------------------------------------
        # Rule 3: Attendance Boundary Invariant [0, 100]
        # Invariant: No attendance percentage should ever be negative or > 100%
        # ---------------------------------------------------------------------
        invalid_att_stmt = select(AnalyticsDailyMetric).where(
            and_(
                AnalyticsDailyMetric.tenant_id == tenant_id,
                AnalyticsDailyMetric.metric_id == "attendance_percentage",
                (AnalyticsDailyMetric.value_numeric < Decimal("0"))
                | (AnalyticsDailyMetric.value_numeric > Decimal("100")),
            )
        )
        invalid_att_rollups = (await db.execute(invalid_att_stmt)).scalars().all()
        for inv in invalid_att_rollups:
            finding = AnalyticsReconciliationFinding(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_code="ATT_PERCENTAGE_BOUNDARY",
                severity=ReconciliationSeverity.CRITICAL,
                metric_id="attendance_percentage",
                source_table="attendance_records",
                operational_value=None,
                analytics_value=inv.value_numeric,
                discrepancy_delta=inv.value_numeric,
                details_json={
                    "message": f"Impossible attendance percentage detected: {inv.value_numeric}%",
                    "date": inv.metric_date.isoformat(),
                },
                resolution_status=ReconciliationStatus.OPEN,
                detected_at=now,
            )
            db.add(finding)
            findings.append(finding)

        # ---------------------------------------------------------------------
        # Rule 4: Examination Marks Integrity
        # Invariant: Marks obtained cannot be negative
        # ---------------------------------------------------------------------
        invalid_marks_stmt = select(func.count(StudentAssessmentMark.id)).where(
            and_(
                StudentAssessmentMark.tenant_id == tenant_id,
                StudentAssessmentMark.marks_obtained < Decimal("0"),
            )
        )
        invalid_marks_count = int((await db.execute(invalid_marks_stmt)).scalar() or 0)
        if invalid_marks_count > 0:
            finding = AnalyticsReconciliationFinding(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_code="EXAM_MARKS_INTEGRITY",
                severity=ReconciliationSeverity.CRITICAL,
                metric_id="average_examination_score",
                source_table="examination_student_marks",
                operational_value=Decimal(invalid_marks_count),
                analytics_value=None,
                discrepancy_delta=Decimal(invalid_marks_count),
                details_json={"negative_marks_row_count": invalid_marks_count},
                resolution_status=ReconciliationStatus.OPEN,
                detected_at=now,
            )
            db.add(finding)
            findings.append(finding)

        # ---------------------------------------------------------------------
        # Rule 5: Orphan Attendance Records Check
        # ---------------------------------------------------------------------
        orphan_att_stmt = select(func.count(AttendanceRecord.id)).where(
            and_(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.session_id.is_(None),
            )
        )
        orphan_count = int((await db.execute(orphan_att_stmt)).scalar() or 0)
        if orphan_count > 0:
            finding = AnalyticsReconciliationFinding(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_code="ORPHAN_ATTENDANCE_RECORDS",
                severity=ReconciliationSeverity.ERROR,
                metric_id="attendance_percentage",
                source_table="attendance_records",
                operational_value=Decimal(orphan_count),
                analytics_value=None,
                discrepancy_delta=Decimal(orphan_count),
                details_json={"orphan_attendance_records": orphan_count},
                resolution_status=ReconciliationStatus.OPEN,
                detected_at=now,
            )
            db.add(finding)
            findings.append(finding)

        await db.commit()
        return findings

    @classmethod
    async def list_findings(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[AnalyticsReconciliationFinding]:
        """List reconciliation findings for a tenant with optional filtering."""
        conditions = [AnalyticsReconciliationFinding.tenant_id == tenant_id]
        if status:
            conditions.append(AnalyticsReconciliationFinding.resolution_status == status.upper())
        if severity:
            conditions.append(AnalyticsReconciliationFinding.severity == severity.upper())

        stmt = (
            select(AnalyticsReconciliationFinding)
            .where(and_(*conditions))
            .order_by(AnalyticsReconciliationFinding.detected_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
