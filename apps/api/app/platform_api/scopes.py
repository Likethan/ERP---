"""Capability-Oriented API Scopes Registry & Centralized Scope Resolver (Step 21).

Provides:
- Capability-oriented API scope taxonomy (domain.action)
- Risk level tiers (LOW, MEDIUM, HIGH, CRITICAL)
- High-risk governance gating requiring administrative approval
- Explicit hierarchical relationships (no automatic write -> read assumption unless declared)
- Mapping from API scopes to required underlying principal PBAC permissions
"""

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class ApiScopeDefinition:
    """Definition of an externally consumable capability scope."""

    code: str
    domain: str
    description: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: bool
    implied_scopes: tuple[str, ...] = field(default_factory=tuple)
    required_pbac_permissions: tuple[str, ...] = field(default_factory=tuple)


# -----------------------------------------------------------------------------
# Standard Capability Scopes
# -----------------------------------------------------------------------------

SCOPE_STUDENTS_READ: Final[str] = "students.read"
SCOPE_STUDENTS_WRITE: Final[str] = "students.write"

SCOPE_FACULTY_READ: Final[str] = "faculty.read"
SCOPE_STAFF_READ: Final[str] = "staff.read"

SCOPE_ACADEMICS_READ: Final[str] = "academics.read"
SCOPE_ATTENDANCE_READ: Final[str] = "attendance.read"

SCOPE_EXAMINATIONS_READ: Final[str] = "examinations.read"
SCOPE_EXAMINATIONS_WRITE: Final[str] = "examinations.write"

SCOPE_FINANCE_READ: Final[str] = "finance.read"
SCOPE_FINANCE_WRITE: Final[str] = "finance.write"

SCOPE_PLACEMENT_READ: Final[str] = "placement.read"

SCOPE_EVENTS_READ: Final[str] = "events.read"
SCOPE_EVENTS_WRITE: Final[str] = "events.write"

SCOPE_DOCUMENTS_READ: Final[str] = "documents.read"
SCOPE_DOCUMENTS_WRITE: Final[str] = "documents.write"
SCOPE_CERTIFICATES_ISSUE: Final[str] = "certificates.issue"

SCOPE_REPORTS_READ: Final[str] = "reports.read"
SCOPE_ANALYTICS_READ: Final[str] = "analytics.read"
SCOPE_NOTIFICATIONS_SEND: Final[str] = "notifications.send"


# -----------------------------------------------------------------------------
# Scope Registry
# -----------------------------------------------------------------------------

API_SCOPE_REGISTRY: Final[dict[str, ApiScopeDefinition]] = {
    SCOPE_STUDENTS_READ: ApiScopeDefinition(
        code=SCOPE_STUDENTS_READ,
        domain="students",
        description="Read student directory, profiles, and basic institutional records",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("people:students:read",),
    ),
    SCOPE_STUDENTS_WRITE: ApiScopeDefinition(
        code=SCOPE_STUDENTS_WRITE,
        domain="students",
        description="Admit, onboard, or update student profile records",
        risk_level="HIGH",
        requires_approval=True,
        implied_scopes=(),  # Note: writing does NOT imply reading unless granted
        required_pbac_permissions=("people:students:create", "people:students:update"),
    ),
    SCOPE_FACULTY_READ: ApiScopeDefinition(
        code=SCOPE_FACULTY_READ,
        domain="faculty",
        description="View faculty directory and department assignments",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("people:faculty:read",),
    ),
    SCOPE_STAFF_READ: ApiScopeDefinition(
        code=SCOPE_STAFF_READ,
        domain="staff",
        description="View operational staff directories",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("people:staff:read",),
    ),
    SCOPE_ACADEMICS_READ: ApiScopeDefinition(
        code=SCOPE_ACADEMICS_READ,
        domain="academics",
        description="Read curriculum, courses, programs, and syllabus structures",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("academics:courses:read", "academics:curriculum:read"),
    ),
    SCOPE_ATTENDANCE_READ: ApiScopeDefinition(
        code=SCOPE_ATTENDANCE_READ,
        domain="attendance",
        description="Query student attendance sessions and percentage metrics",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("attendance:records:read", "attendance:read"),
    ),
    SCOPE_EXAMINATIONS_READ: ApiScopeDefinition(
        code=SCOPE_EXAMINATIONS_READ,
        domain="examinations",
        description="Read published assessment marks, grade reports, and GPA results",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("examinations:results:read",),
    ),
    SCOPE_EXAMINATIONS_WRITE: ApiScopeDefinition(
        code=SCOPE_EXAMINATIONS_WRITE,
        domain="examinations",
        description="Enter marks, submit exam evaluations, or modify grade entries",
        risk_level="CRITICAL",
        requires_approval=True,
        implied_scopes=(),
        required_pbac_permissions=("examinations:marks:entry",),
    ),
    SCOPE_FINANCE_READ: ApiScopeDefinition(
        code=SCOPE_FINANCE_READ,
        domain="finance",
        description="Inspect student fee invoices, dues, and payment receipts",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("finance:invoices:read", "finance:read"),
    ),
    SCOPE_FINANCE_WRITE: ApiScopeDefinition(
        code=SCOPE_FINANCE_WRITE,
        domain="finance",
        description="Process payment transactions, record collections, or initiate refunds",
        risk_level="CRITICAL",
        requires_approval=True,
        implied_scopes=(),
        required_pbac_permissions=("finance:payments:create",),
    ),
    SCOPE_PLACEMENT_READ: ApiScopeDefinition(
        code=SCOPE_PLACEMENT_READ,
        domain="placement",
        description="View corporate placement drives and campus hiring schedules",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("placement:drives:read",),
    ),
    SCOPE_EVENTS_READ: ApiScopeDefinition(
        code=SCOPE_EVENTS_READ,
        domain="events",
        description="View campus calendar, student club activities, and public events",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("events:read",),
    ),
    SCOPE_EVENTS_WRITE: ApiScopeDefinition(
        code=SCOPE_EVENTS_WRITE,
        domain="events",
        description="Create, schedule, and publish campus events and announcements",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("events:create", "events:publish"),
    ),
    SCOPE_DOCUMENTS_READ: ApiScopeDefinition(
        code=SCOPE_DOCUMENTS_READ,
        domain="documents",
        description="Access and download verified institutional documents",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("documents:read",),
    ),
    SCOPE_DOCUMENTS_WRITE: ApiScopeDefinition(
        code=SCOPE_DOCUMENTS_WRITE,
        domain="documents",
        description="Upload digital documents and submit verification requests",
        risk_level="HIGH",
        requires_approval=True,
        implied_scopes=(),
        required_pbac_permissions=("documents:create", "documents:manage"),
    ),
    SCOPE_CERTIFICATES_ISSUE: ApiScopeDefinition(
        code=SCOPE_CERTIFICATES_ISSUE,
        domain="documents",
        description="Generate and issue cryptographically verifiable certificates",
        risk_level="CRITICAL",
        requires_approval=True,
        implied_scopes=(),
        required_pbac_permissions=("certificates:requests:issue",),
    ),
    SCOPE_REPORTS_READ: ApiScopeDefinition(
        code=SCOPE_REPORTS_READ,
        domain="reports",
        description="Retrieve pre-calculated institutional reports and metric digests",
        risk_level="MEDIUM",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("reports:read",),
    ),
    SCOPE_ANALYTICS_READ: ApiScopeDefinition(
        code=SCOPE_ANALYTICS_READ,
        domain="analytics",
        description="Access API performance metrics and institutional telemetry",
        risk_level="LOW",
        requires_approval=False,
        implied_scopes=(),
        required_pbac_permissions=("analytics:read",),
    ),
    SCOPE_NOTIFICATIONS_SEND: ApiScopeDefinition(
        code=SCOPE_NOTIFICATIONS_SEND,
        domain="notifications",
        description="Dispatch SMS, Email, and Push alerts to students and staff",
        risk_level="HIGH",
        requires_approval=True,
        implied_scopes=(),
        required_pbac_permissions=("notifications:manage",),
    ),
}


# -----------------------------------------------------------------------------
# Centralized Scope Resolver
# -----------------------------------------------------------------------------


class ScopeResolver:
    """Evaluates scope fulfillment with explicit hierarchy resolution."""

    @classmethod
    def is_scope_granted(cls, granted_scopes: set[str], required_scope: str) -> bool:
        """Determines if the granted scopes satisfy the required capability scope.

        Rules:
        1. Wildcard '*' satisfies any scope.
        2. Exact match satisfies the scope.
        3. Declared implied parent scopes satisfy the scope.
        4. No undeclared write -> read assumptions are made.
        """
        if "*" in granted_scopes or required_scope in granted_scopes:
            return True

        # Check if any granted scope explicitly implies required_scope
        for granted in granted_scopes:
            defn = API_SCOPE_REGISTRY.get(granted)
            if defn and required_scope in defn.implied_scopes:
                return True

        return False

    @classmethod
    def get_high_risk_scopes(cls) -> set[str]:
        """Returns all capability scopes classified as HIGH or CRITICAL risk."""
        return {
            code
            for code, defn in API_SCOPE_REGISTRY.items()
            if defn.risk_level in ("HIGH", "CRITICAL") or defn.requires_approval
        }

    @classmethod
    def get_required_pbac_permissions(cls, scope_code: str) -> tuple[str, ...]:
        """Resolves required underlying PBAC permissions for an API scope."""
        defn = API_SCOPE_REGISTRY.get(scope_code)
        return defn.required_pbac_permissions if defn else ()


scope_resolver = ScopeResolver()
