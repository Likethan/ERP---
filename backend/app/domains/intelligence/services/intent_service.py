"""Intent classification and tool planning service."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentPlan:
    intent: str
    domain: str
    target_tools: list[str] = field(default_factory=list)
    confidence: float = 0.95
    suggested_params: dict[str, dict[str, Any]] = field(default_factory=dict)


class IntentService:
    """Classifies natural language query into approved domain tool executions."""

    @classmethod
    def classify(cls, query: str, context: dict[str, Any] | None = None) -> IntentPlan:
        q = query.lower().strip()
        ctx = context or {}

        # 1. Multi-domain comparison (attendance vs exam)
        if (
            ("compare" in q or "correlation" in q)
            and "attendance" in q
            and ("exam" in q or "performance" in q)
        ):
            return IntentPlan(
                intent="CROSS_DOMAIN_ATTENDANCE_EXAM",
                domain="ALL",
                target_tools=["attendance.get_summary", "examinations.get_pass_percentage"],
            )

        # 2. Attendance below threshold / shortage
        if "attendance" in q and ("below" in q or "shortage" in q or "75" in q or "less than" in q):
            return IntentPlan(
                intent="ATTENDANCE_SHORTAGE",
                domain="ATTENDANCE",
                target_tools=["attendance.get_students_below_threshold"],
                suggested_params={
                    "attendance.get_students_below_threshold": {"threshold": 75.0, "limit": 20}
                },
            )

        # 3. Overall attendance summary
        if "attendance" in q:
            if ctx.get("student_id") or "my attendance" in q:
                return IntentPlan(
                    intent="STUDENT_ATTENDANCE",
                    domain="ATTENDANCE",
                    target_tools=["attendance.get_student_attendance"],
                    suggested_params={
                        "attendance.get_student_attendance": {"identifier": ctx.get("student_id")}
                    },
                )
            return IntentPlan(
                intent="ATTENDANCE_SUMMARY",
                domain="ATTENDANCE",
                target_tools=["attendance.get_summary"],
            )

        # 4. Fee & finance queries
        if any(
            w in q
            for w in [
                "fee",
                "fees",
                "finance",
                "outstanding",
                "tuition",
                "dues",
                "invoiced",
                "collected",
            ]
        ):
            if "my fee" in q or ctx.get("student_id"):
                return IntentPlan(
                    intent="STUDENT_FEE_INVOICE",
                    domain="FINANCE",
                    target_tools=["finance.get_student_invoice_summary"],
                    suggested_params={
                        "finance.get_student_invoice_summary": {"identifier": ctx.get("student_id")}
                    },
                )
            return IntentPlan(
                intent="FEE_OUTSTANDING",
                domain="FINANCE",
                target_tools=["finance.get_fee_summary", "finance.get_outstanding_summary"],
            )

        # 5. Examinations & results
        if any(
            w in q
            for w in ["exam", "examination", "results", "marks", "grades", "gpa", "pass percentage"]
        ):
            return IntentPlan(
                intent="EXAM_RESULT_SUMMARY",
                domain="EXAMINATIONS",
                target_tools=[
                    "examinations.get_pass_percentage",
                    "examinations.get_grade_distribution",
                ],
            )

        # 6. Placement & drives
        if any(
            w in q
            for w in [
                "placement",
                "recruitment",
                "drive",
                "offers",
                "salary",
                "ctc",
                "company",
                "companies",
            ]
        ):
            return IntentPlan(
                intent="PLACEMENT_SUMMARY",
                domain="PLACEMENT",
                target_tools=["placement.get_drive_summary", "placement.get_placement_outcomes"],
            )

        # 7. Hostel & infrastructure
        if any(w in q for w in ["hostel", "room", "bed", "occupancy", "transport", "bus"]):
            return IntentPlan(
                intent="INFRASTRUCTURE_OCCUPANCY",
                domain="INFRASTRUCTURE",
                target_tools=[
                    "infrastructure.get_hostel_occupancy",
                    "infrastructure.get_transport_summary",
                ],
            )

        # 8. Events & campus activities
        if any(
            w in q
            for w in ["event", "events", "hackathon", "symposium", "club", "clubs", "circular"]
        ):
            return IntentPlan(
                intent="CAMPUS_EVENTS",
                domain="CAMPUS",
                target_tools=["campus.get_event_summary", "campus.get_club_summary"],
            )

        # 9. Documents & verification
        if any(
            w in q
            for w in ["document", "documents", "verification", "certificate", "expiring", "records"]
        ):
            return IntentPlan(
                intent="DOCUMENT_VERIFICATION",
                domain="DOCUMENTS",
                target_tools=[
                    "documents.get_verification_summary",
                    "documents.get_expiring_documents",
                ],
            )

        # 10. Student lookup
        if any(w in q for w in ["student", "students", "roll number", "admission"]):
            return IntentPlan(
                intent="STUDENT_LOOKUP",
                domain="PEOPLE",
                target_tools=["people.search_students"],
                suggested_params={"people.search_students": {"query": q, "limit": 20}},
            )

        # Fallback / General
        return IntentPlan(
            intent="GENERAL_CAMPUS_INFORMATION",
            domain="ALL",
            target_tools=["academics.get_program_summary"],
        )
