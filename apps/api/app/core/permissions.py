"""CampusOS Permission Registry and System Role Definitions.

All permissions follow the atomic format: {domain}:{resource}:{action}
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    domain: str
    description: str


# --- Core Domain Permissions ---
CORE_INSTITUTION_READ: Final[str] = "core:institutions:read"
CORE_INSTITUTION_MANAGE: Final[str] = "core:institutions:manage"
CORE_CAMPUSES_READ: Final[str] = "core:campuses:read"
CORE_CAMPUSES_MANAGE: Final[str] = "core:campuses:manage"
CORE_DEPARTMENTS_READ: Final[str] = "core:departments:read"
CORE_DEPARTMENTS_MANAGE: Final[str] = "core:departments:manage"
CORE_PROGRAMS_READ: Final[str] = "core:programs:read"
CORE_PROGRAMS_MANAGE: Final[str] = "core:programs:manage"
CORE_REGULATIONS_MANAGE: Final[str] = "core:regulations:manage"
CORE_ACADEMIC_YEARS_READ: Final[str] = "core:academic_years:read"
CORE_ACADEMIC_YEARS_MANAGE: Final[str] = "core:academic_years:manage"
CORE_SECTIONS_READ: Final[str] = "core:sections:read"
CORE_SECTIONS_MANAGE: Final[str] = "core:sections:manage"

# --- People Domain Permissions ---
PEOPLE_USERS_READ: Final[str] = "people:users:read"
PEOPLE_USERS_MANAGE: Final[str] = "people:users:manage"
PEOPLE_STUDENTS_READ: Final[str] = "people:students:read"
PEOPLE_STUDENTS_CREATE: Final[str] = "people:students:create"
PEOPLE_STUDENTS_UPDATE: Final[str] = "people:students:update"
PEOPLE_FACULTY_READ: Final[str] = "people:faculty:read"
PEOPLE_FACULTY_MANAGE: Final[str] = "people:faculty:manage"
PEOPLE_STAFF_READ: Final[str] = "people:staff:read"
PEOPLE_STAFF_MANAGE: Final[str] = "people:staff:manage"
PEOPLE_ROLES_MANAGE: Final[str] = "people:roles:manage"

# --- Academics Domain Permissions ---
ACADEMICS_SUBJECTS_READ: Final[str] = "academics:subjects:read"
ACADEMICS_SUBJECTS_MANAGE: Final[str] = "academics:subjects:manage"
ACADEMICS_CURRICULUM_READ: Final[str] = "academics:curriculum:read"
ACADEMICS_CURRICULUM_MANAGE: Final[str] = "academics:curriculum:manage"
ACADEMICS_CURRICULUM_PUBLISH: Final[str] = "academics:curriculum:publish"
ACADEMICS_COURSES_READ: Final[str] = "academics:courses:read"
ACADEMICS_COURSES_MANAGE: Final[str] = "academics:courses:manage"
ACADEMICS_ENROLLMENTS_READ: Final[str] = "academics:enrollments:read"
ACADEMICS_ENROLLMENTS_MANAGE: Final[str] = "academics:enrollments:manage"
ACADEMICS_TIMETABLE_READ: Final[str] = "academics:timetable:read"
ACADEMICS_TIMETABLE_MANAGE: Final[str] = "academics:timetable:manage"
ACADEMICS_ROOMS_READ: Final[str] = "academics:rooms:read"
ACADEMICS_ROOMS_MANAGE: Final[str] = "academics:rooms:manage"
ACADEMICS_ENROLL_SELF: Final[str] = "academics:enroll:self"

# --- Attendance Domain Permissions ---
ATTENDANCE_SESSIONS_READ: Final[str] = "attendance:sessions:read"
ATTENDANCE_RECORDS_READ: Final[str] = "attendance:records:read"
ATTENDANCE_RECORDS_WRITE: Final[str] = "attendance:records:write"
ATTENDANCE_CORRECTIONS_APPROVE: Final[str] = "attendance:corrections:approve"
ATTENDANCE_LEAVE_APPLY: Final[str] = "attendance:leave:apply"
ATTENDANCE_LEAVE_APPROVE: Final[str] = "attendance:leave:approve"

# Granular Step 6 Attendance permissions
ATTENDANCE_READ: Final[str] = "attendance:read"
ATTENDANCE_MARK: Final[str] = "attendance:mark"
ATTENDANCE_UPDATE: Final[str] = "attendance:update"
ATTENDANCE_LOCK: Final[str] = "attendance:lock"
ATTENDANCE_CORRECT: Final[str] = "attendance:correct"
ATTENDANCE_APPROVE_CORRECTION: Final[str] = "attendance:approve_correction"

LEAVE_READ: Final[str] = "leave:read"
LEAVE_CREATE: Final[str] = "leave:create"
LEAVE_APPROVE: Final[str] = "leave:approve"
LEAVE_REJECT: Final[str] = "leave:reject"

ATTENDANCE_POLICY_READ: Final[str] = "attendance_policy:read"
ATTENDANCE_POLICY_CREATE: Final[str] = "attendance_policy:create"
ATTENDANCE_POLICY_UPDATE: Final[str] = "attendance_policy:update"

# --- Examination Domain Permissions ---
EXAMINATION_ASSESSMENTS_READ: Final[str] = "examination:assessments:read"
EXAMINATION_ASSESSMENTS_MANAGE: Final[str] = "examination:assessments:manage"
EXAMINATION_MARKS_WRITE: Final[str] = "examination:marks:write"
EXAMINATION_RESULTS_APPROVE: Final[str] = "examination:results:approve"
EXAMINATION_RESULTS_PUBLISH: Final[str] = "examination:results:publish"
EXAMINATION_RESULTS_READ_SELF: Final[str] = "examination:results:read_self"

# Step 7 Granular Examination permissions
EXAMINATIONS_READ: Final[str] = "examinations:read"
EXAMINATIONS_CREATE: Final[str] = "examinations:create"
EXAMINATIONS_UPDATE: Final[str] = "examinations:update"

ASSESSMENTS_READ: Final[str] = "assessments:read"
ASSESSMENTS_CREATE: Final[str] = "assessments:create"
ASSESSMENTS_UPDATE: Final[str] = "assessments:update"
ASSESSMENTS_FINALIZE: Final[str] = "assessments:finalize"

MARKS_READ: Final[str] = "marks:read"
MARKS_ENTER: Final[str] = "marks:enter"
MARKS_UPDATE: Final[str] = "marks:update"
MARKS_FINALIZE: Final[str] = "marks:finalize"
MARKS_CORRECT: Final[str] = "marks:correct"

RESULTS_READ: Final[str] = "results:read"
RESULTS_FINALIZE: Final[str] = "results:finalize"
RESULTS_PUBLISH: Final[str] = "results:publish"

GRADE_SCALES_READ: Final[str] = "grade_scales:read"
GRADE_SCALES_MANAGE: Final[str] = "grade_scales:manage"

ELIGIBILITY_READ: Final[str] = "eligibility:read"
ELIGIBILITY_EVALUATE: Final[str] = "eligibility:evaluate"
ELIGIBILITY_OVERRIDE: Final[str] = "eligibility:override"

# --- Finance Domain Permissions ---
FINANCE_STRUCTURES_MANAGE: Final[str] = "finance:structures:manage"
FINANCE_INVOICES_READ: Final[str] = "finance:invoices:read"
FINANCE_INVOICES_CREATE: Final[str] = "finance:invoices:create"
FINANCE_PAYMENTS_RECORD: Final[str] = "finance:payments:record"
FINANCE_PAYMENTS_PAY_SELF: Final[str] = "finance:payments:pay_self"
FINANCE_REFUNDS_APPROVE: Final[str] = "finance:refunds:approve"
FINANCE_REPORTS_READ: Final[str] = "finance:reports:read"

# Step 8 Granular Finance permissions
FINANCE_READ: Final[str] = "finance:read"
FINANCE_MANAGE_FEE_STRUCTURES: Final[str] = "finance:manage_fee_structures"

INVOICES_READ: Final[str] = "invoices:read"
INVOICES_CREATE: Final[str] = "invoices:create"
INVOICES_ISSUE: Final[str] = "invoices:issue"
INVOICES_CANCEL: Final[str] = "invoices:cancel"

PAYMENTS_READ: Final[str] = "payments:read"
PAYMENTS_CREATE: Final[str] = "payments:create"
PAYMENTS_CONFIRM: Final[str] = "payments:confirm"

RECEIPTS_READ: Final[str] = "receipts:read"
RECEIPTS_ISSUE: Final[str] = "receipts:issue"

SCHOLARSHIPS_READ: Final[str] = "scholarships:read"
SCHOLARSHIPS_CREATE: Final[str] = "scholarships:create"
SCHOLARSHIPS_APPROVE: Final[str] = "scholarships:approve"

ADJUSTMENTS_CREATE: Final[str] = "adjustments:create"
ADJUSTMENTS_APPROVE: Final[str] = "adjustments:approve"

REFUNDS_CREATE: Final[str] = "refunds:create"
REFUNDS_APPROVE: Final[str] = "refunds:approve"
REFUNDS_PROCESS: Final[str] = "refunds:process"

# --- Placement Domain Permissions ---
PLACEMENT_COMPANIES_READ: Final[str] = "placement:companies:read"
PLACEMENT_COMPANIES_MANAGE: Final[str] = "placement:companies:manage"
PLACEMENT_DRIVES_READ: Final[str] = "placement:drives:read"
PLACEMENT_DRIVES_MANAGE: Final[str] = "placement:drives:manage"
PLACEMENT_POSITIONS_MANAGE: Final[str] = "placement:positions:manage"
PLACEMENT_ELIGIBILITY_EVALUATE: Final[str] = "placement:eligibility:evaluate"
PLACEMENT_APPLY_SELF: Final[str] = "placement:apply:self"
PLACEMENT_APPLICATIONS_READ: Final[str] = "placement:applications:read"
PLACEMENT_APPLICATIONS_REVIEW: Final[str] = "placement:applications:review"
PLACEMENT_INTERVIEWS_MANAGE: Final[str] = "placement:interviews:manage"
PLACEMENT_INTERVIEWS_EVALUATE: Final[str] = "placement:interviews:evaluate"
PLACEMENT_OFFERS_READ: Final[str] = "placement:offers:read"
PLACEMENT_OFFERS_MANAGE: Final[str] = "placement:offers:manage"
PLACEMENT_OFFERS_RESPOND: Final[str] = "placement:offers:respond"
PLACEMENT_OUTCOMES_MANAGE: Final[str] = "placement:outcomes:manage"
PLACEMENT_ANALYTICS_READ: Final[str] = "placement:analytics:read"
PLACEMENT_PROFILE_READ: Final[str] = "placement:profile:read"
PLACEMENT_PROFILE_UPDATE: Final[str] = "placement:profile:update"

# --- Campus Events Domain Permissions ---
EVENTS_READ: Final[str] = "events:read"
EVENTS_CREATE: Final[str] = "events:create"
EVENTS_UPDATE: Final[str] = "events:update"
EVENTS_PUBLISH: Final[str] = "events:publish"
EVENTS_CANCEL: Final[str] = "events:cancel"
EVENTS_MANAGE_ATTENDANCE: Final[str] = "events:manage_attendance"
EVENTS_MANAGE_REGISTRATIONS: Final[str] = "events:manage_registrations"
EVENTS_SELF_REGISTER: Final[str] = "events:self_register"
EVENTS_SELF_MANAGE_REGISTRATION: Final[str] = "events:self_manage_registration"

# --- Campus Clubs Domain Permissions ---
CLUBS_READ: Final[str] = "clubs:read"
CLUBS_CREATE: Final[str] = "clubs:create"
CLUBS_UPDATE: Final[str] = "clubs:update"
CLUBS_APPROVE: Final[str] = "clubs:approve"
CLUBS_MANAGE_MEMBERSHIPS: Final[str] = "clubs:manage_memberships"
CLUBS_SELF_READ: Final[str] = "clubs:self_read"
CLUBS_SELF_REQUEST_MEMBERSHIP: Final[str] = "clubs:self_request_membership"
CLUBS_SELF_MANAGE_MEMBERSHIP: Final[str] = "clubs:self_manage_membership"

# --- Campus Announcements Domain Permissions ---
ANNOUNCEMENTS_READ: Final[str] = "announcements:read"
ANNOUNCEMENTS_CREATE: Final[str] = "announcements:create"
ANNOUNCEMENTS_UPDATE: Final[str] = "announcements:update"
ANNOUNCEMENTS_PUBLISH: Final[str] = "announcements:publish"
ANNOUNCEMENTS_ARCHIVE: Final[str] = "announcements:archive"

# --- Notifications Domain Permissions ---
NOTIFICATIONS_READ: Final[str] = "notifications:read"
NOTIFICATIONS_MANAGE: Final[str] = "notifications:manage"
NOTIFICATIONS_MANAGE_PREFERENCES: Final[str] = "notifications:manage_preferences"
NOTIFICATIONS_SELF_READ: Final[str] = "notifications:self_read"
NOTIFICATIONS_SELF_MANAGE_PREFERENCES: Final[str] = "notifications:self_manage_preferences"

# --- Legacy Campus & Logistics Permissions ---
CAMPUS_EVENTS_MANAGE: Final[str] = "campus:events:manage"
CAMPUS_ANNOUNCEMENTS_MANAGE: Final[str] = "campus:announcements:manage"
INFRASTRUCTURE_HOSTEL_MANAGE: Final[str] = "infrastructure:hostel:manage"
INFRASTRUCTURE_TRANSPORT_MANAGE: Final[str] = "infrastructure:transport:manage"
DOCUMENTS_MANAGE: Final[str] = "documents:manage"
AUDIT_LOGS_READ: Final[str] = "audit:logs:read"

# --- Documents & Digital Records Domain Permissions ---
DOCUMENTS_READ: Final[str] = "documents:read"
DOCUMENTS_CREATE: Final[str] = "documents:create"
DOCUMENTS_UPDATE: Final[str] = "documents:update"
DOCUMENTS_VERIFY: Final[str] = "documents:verify"
DOCUMENTS_REJECT: Final[str] = "documents:reject"
DOCUMENTS_ARCHIVE: Final[str] = "documents:archive"
DOCUMENTS_DELETE: Final[str] = "documents:delete"

DOCUMENT_CATEGORIES_READ: Final[str] = "document_categories:read"
DOCUMENT_CATEGORIES_MANAGE: Final[str] = "document_categories:manage"

DOCUMENT_REQUIREMENTS_READ: Final[str] = "document_requirements:read"
DOCUMENT_REQUIREMENTS_MANAGE: Final[str] = "document_requirements:manage"

CERTIFICATE_TEMPLATES_READ: Final[str] = "certificate_templates:read"
CERTIFICATE_TEMPLATES_MANAGE: Final[str] = "certificate_templates:manage"

CERTIFICATE_REQUESTS_CREATE: Final[str] = "certificate_requests:create"
CERTIFICATE_REQUESTS_READ: Final[str] = "certificate_requests:read"
CERTIFICATE_REQUESTS_REVIEW: Final[str] = "certificate_requests:review"
CERTIFICATE_REQUESTS_APPROVE: Final[str] = "certificate_requests:approve"
CERTIFICATE_REQUESTS_ISSUE: Final[str] = "certificate_requests:issue"
CERTIFICATE_REQUESTS_REVOKE: Final[str] = "certificate_requests:revoke"
CERTIFICATE_REQUESTS_CANCEL: Final[str] = "certificate_requests:cancel"

CERTIFICATES_READ: Final[str] = "certificates:read"
CERTIFICATES_VERIFY: Final[str] = "certificates:verify"
CERTIFICATES_REVOKE: Final[str] = "certificates:revoke"

INSTITUTIONAL_RECORDS_READ: Final[str] = "institutional_records:read"
INSTITUTIONAL_RECORDS_MANAGE: Final[str] = "institutional_records:manage"

# Dot notation aliases
DOCUMENTS_READ_DOT: Final[str] = "documents.read"
DOCUMENTS_CREATE_DOT: Final[str] = "documents.create"
DOCUMENTS_UPDATE_DOT: Final[str] = "documents.update"
DOCUMENTS_VERIFY_DOT: Final[str] = "documents.verify"
DOCUMENTS_REJECT_DOT: Final[str] = "documents.reject"
DOCUMENTS_ARCHIVE_DOT: Final[str] = "documents.archive"
DOCUMENT_CATEGORIES_MANAGE_DOT: Final[str] = "document_categories.manage"
DOCUMENT_REQUIREMENTS_MANAGE_DOT: Final[str] = "document_requirements.manage"
CERTIFICATE_TEMPLATES_READ_DOT: Final[str] = "certificate_templates.read"
CERTIFICATE_TEMPLATES_MANAGE_DOT: Final[str] = "certificate_templates.manage"
CERTIFICATE_REQUESTS_CREATE_DOT: Final[str] = "certificate_requests.create"
CERTIFICATE_REQUESTS_READ_DOT: Final[str] = "certificate_requests.read"
CERTIFICATE_REQUESTS_REVIEW_DOT: Final[str] = "certificate_requests.review"
CERTIFICATE_REQUESTS_APPROVE_DOT: Final[str] = "certificate_requests.approve"
CERTIFICATE_REQUESTS_ISSUE_DOT: Final[str] = "certificate_requests.issue"
CERTIFICATE_REQUESTS_REVOKE_DOT: Final[str] = "certificate_requests.revoke"
INSTITUTIONAL_RECORDS_READ_DOT: Final[str] = "institutional_records.read"
INSTITUTIONAL_RECORDS_MANAGE_DOT: Final[str] = "institutional_records.manage"

# Intelligence & AI Permissions
INTELLIGENCE_READ: Final[str] = "intelligence:read"
INTELLIGENCE_QUERY: Final[str] = "intelligence:query"
INTELLIGENCE_INSIGHTS_READ: Final[str] = "intelligence_insights:read"
INTELLIGENCE_ALERTS_READ: Final[str] = "intelligence_alerts:read"
INTELLIGENCE_ALERTS_MANAGE: Final[str] = "intelligence_alerts:manage"
INTELLIGENCE_ANALYTICS_READ: Final[str] = "intelligence_analytics:read"
INTELLIGENCE_SAVED_MANAGE: Final[str] = "intelligence_saved:manage"
INTELLIGENCE_ACTIVITY_READ: Final[str] = "intelligence_activity:read"
INTELLIGENCE_TOOLS_READ: Final[str] = "intelligence_tools:read"
INTELLIGENCE_GOVERNANCE_READ: Final[str] = "intelligence_governance:read"
INTELLIGENCE_GOVERNANCE_MANAGE: Final[str] = "intelligence_governance:manage"
INTELLIGENCE_PREDICT: Final[str] = "intelligence:predict"
INTELLIGENCE_RECOMMEND: Final[str] = "intelligence:recommend"
INTELLIGENCE_EVALUATE: Final[str] = "intelligence:evaluate"

# Intelligence dot aliases
INTELLIGENCE_READ_DOT: Final[str] = "intelligence.read"
INTELLIGENCE_QUERY_DOT: Final[str] = "intelligence.query"
INTELLIGENCE_INSIGHTS_READ_DOT: Final[str] = "intelligence.insights.read"
INTELLIGENCE_ALERTS_READ_DOT: Final[str] = "intelligence.alerts.read"
INTELLIGENCE_ALERTS_MANAGE_DOT: Final[str] = "intelligence.alerts.manage"
INTELLIGENCE_ANALYTICS_READ_DOT: Final[str] = "intelligence.analytics.read"
INTELLIGENCE_SAVED_MANAGE_DOT: Final[str] = "intelligence.saved.manage"
INTELLIGENCE_ACTIVITY_READ_DOT: Final[str] = "intelligence.activity.read"
INTELLIGENCE_TOOLS_READ_DOT: Final[str] = "intelligence.tools.read"
INTELLIGENCE_GOVERNANCE_READ_DOT: Final[str] = "intelligence.governance.read"
INTELLIGENCE_GOVERNANCE_MANAGE_DOT: Final[str] = "intelligence.governance.manage"
INTELLIGENCE_PREDICT_DOT: Final[str] = "intelligence.predict"
INTELLIGENCE_RECOMMEND_DOT: Final[str] = "intelligence.recommend"
INTELLIGENCE_EVALUATE_DOT: Final[str] = "intelligence.evaluate"


# --- Workflows & Automation Domain Permissions ---
WORKFLOWS_READ: Final[str] = "workflows:read"
WORKFLOWS_CREATE: Final[str] = "workflows:create"
WORKFLOWS_UPDATE: Final[str] = "workflows:update"
WORKFLOWS_ACTIVATE: Final[str] = "workflows:activate"
WORKFLOWS_PAUSE: Final[str] = "workflows:pause"
WORKFLOWS_ARCHIVE: Final[str] = "workflows:archive"
WORKFLOWS_EXECUTE: Final[str] = "workflows:execute"
WORKFLOWS_RETRY: Final[str] = "workflows:retry"
WORKFLOWS_CANCEL: Final[str] = "workflows:cancel"
WORKFLOW_EXECUTIONS_READ: Final[str] = "workflow_executions:read"
WORKFLOW_ACTIONS_MANAGE: Final[str] = "workflow_actions:manage"

# Workflow dot notation aliases
WORKFLOWS_READ_DOT: Final[str] = "workflows.read"
WORKFLOWS_CREATE_DOT: Final[str] = "workflows.create"
WORKFLOWS_UPDATE_DOT: Final[str] = "workflows.update"
WORKFLOWS_ACTIVATE_DOT: Final[str] = "workflows.activate"
WORKFLOWS_PAUSE_DOT: Final[str] = "workflows.pause"
WORKFLOWS_ARCHIVE_DOT: Final[str] = "workflows.archive"
WORKFLOWS_EXECUTE_DOT: Final[str] = "workflows.execute"
WORKFLOWS_RETRY_DOT: Final[str] = "workflows.retry"
WORKFLOWS_CANCEL_DOT: Final[str] = "workflows.cancel"
WORKFLOW_EXECUTIONS_READ_DOT: Final[str] = "workflow_executions.read"
WORKFLOW_ACTIONS_MANAGE_DOT: Final[str] = "workflow_actions.manage"

# --- Reporting & Analytics Domain Permissions ---
REPORTS_READ: Final[str] = "reports:read"
REPORTS_CREATE: Final[str] = "reports:create"
REPORTS_UPDATE: Final[str] = "reports:update"
REPORTS_EXECUTE: Final[str] = "reports:execute"
REPORTS_EXPORT: Final[str] = "reports:export"
REPORTS_SCHEDULE: Final[str] = "reports:schedule"
REPORTS_SHARE: Final[str] = "reports:share"
REPORTS_DELETE: Final[str] = "reports:delete"

ANALYTICS_READ: Final[str] = "analytics:read"
ANALYTICS_QUERY: Final[str] = "analytics:query"
ANALYTICS_EXPORT: Final[str] = "analytics:export"
ANALYTICS_MANAGE: Final[str] = "analytics:manage"
ANALYTICS_RECONCILE: Final[str] = "analytics:reconcile"
ANALYTICS_BACKFILL: Final[str] = "analytics:backfill"

# Reporting & Analytics dot notation aliases
REPORTS_READ_DOT: Final[str] = "reports.read"
REPORTS_CREATE_DOT: Final[str] = "reports.create"
REPORTS_UPDATE_DOT: Final[str] = "reports.update"
REPORTS_EXECUTE_DOT: Final[str] = "reports.execute"
REPORTS_EXPORT_DOT: Final[str] = "reports.export"
REPORTS_SCHEDULE_DOT: Final[str] = "reports.schedule"
REPORTS_SHARE_DOT: Final[str] = "reports.share"
REPORTS_DELETE_DOT: Final[str] = "reports.delete"

ANALYTICS_READ_DOT: Final[str] = "analytics.read"
ANALYTICS_QUERY_DOT: Final[str] = "analytics.query"
ANALYTICS_EXPORT_DOT: Final[str] = "analytics.export"
ANALYTICS_MANAGE_DOT: Final[str] = "analytics.manage"
ANALYTICS_RECONCILE_DOT: Final[str] = "analytics.reconcile"
ANALYTICS_BACKFILL_DOT: Final[str] = "analytics.backfill"

# --- Data Governance, Privacy & Compliance Domain Permissions ---
GOVERNANCE_READ: Final[str] = "governance:read"
GOVERNANCE_MANAGE: Final[str] = "governance:manage"
GOVERNANCE_POLICIES_READ: Final[str] = "governance:policies:read"
GOVERNANCE_POLICIES_MANAGE: Final[str] = "governance:policies:manage"
GOVERNANCE_RETENTION_READ: Final[str] = "governance:retention:read"
GOVERNANCE_RETENTION_MANAGE: Final[str] = "governance:retention:manage"
GOVERNANCE_RETENTION_EXECUTE: Final[str] = "governance:retention:execute"
GOVERNANCE_HOLDS_READ: Final[str] = "governance:holds:read"
GOVERNANCE_HOLDS_MANAGE: Final[str] = "governance:holds:manage"
GOVERNANCE_PRIVACY_READ: Final[str] = "governance:privacy:read"
GOVERNANCE_PRIVACY_CREATE: Final[str] = "governance:privacy:create"
GOVERNANCE_PRIVACY_REVIEW: Final[str] = "governance:privacy:review"
GOVERNANCE_PRIVACY_EXECUTE: Final[str] = "governance:privacy:execute"
GOVERNANCE_ACCESS_REVIEWS_READ: Final[str] = "governance:access_reviews:read"
GOVERNANCE_ACCESS_REVIEWS_MANAGE: Final[str] = "governance:access_reviews:manage"
GOVERNANCE_CLASSIFICATION_READ: Final[str] = "governance:classification:read"
GOVERNANCE_CLASSIFICATION_MANAGE: Final[str] = "governance:classification:manage"
GOVERNANCE_EXPORT_APPROVE: Final[str] = "governance:export:approve"
GOVERNANCE_EXPORT_MANAGE: Final[str] = "governance:export:manage"

# Dot notation aliases
GOVERNANCE_READ_DOT: Final[str] = "governance.read"
GOVERNANCE_MANAGE_DOT: Final[str] = "governance.manage"
GOVERNANCE_POLICIES_READ_DOT: Final[str] = "governance.policies.read"
GOVERNANCE_POLICIES_MANAGE_DOT: Final[str] = "governance.policies.manage"
GOVERNANCE_RETENTION_READ_DOT: Final[str] = "governance.retention.read"
GOVERNANCE_RETENTION_MANAGE_DOT: Final[str] = "governance.retention.manage"
GOVERNANCE_RETENTION_EXECUTE_DOT: Final[str] = "governance.retention.execute"
GOVERNANCE_HOLDS_READ_DOT: Final[str] = "governance.holds.read"
GOVERNANCE_HOLDS_MANAGE_DOT: Final[str] = "governance.holds.manage"
GOVERNANCE_PRIVACY_READ_DOT: Final[str] = "governance.privacy.read"
GOVERNANCE_PRIVACY_CREATE_DOT: Final[str] = "governance.privacy.create"
GOVERNANCE_PRIVACY_REVIEW_DOT: Final[str] = "governance.privacy.review"
GOVERNANCE_PRIVACY_EXECUTE_DOT: Final[str] = "governance.privacy.execute"
GOVERNANCE_ACCESS_REVIEWS_READ_DOT: Final[str] = "governance.access_reviews.read"
GOVERNANCE_ACCESS_REVIEWS_MANAGE_DOT: Final[str] = "governance.access_reviews.manage"
GOVERNANCE_CLASSIFICATION_READ_DOT: Final[str] = "governance.classification.read"
GOVERNANCE_CLASSIFICATION_MANAGE_DOT: Final[str] = "governance.classification.manage"
GOVERNANCE_EXPORT_APPROVE_DOT: Final[str] = "governance.export.approve"
# --- Enterprise Integration & Interoperability Domain Permissions ---
INTEGRATIONS_READ: Final[str] = "integrations:read"
INTEGRATIONS_MANAGE: Final[str] = "integrations:manage"
INTEGRATIONS_CONNECTORS_READ: Final[str] = "integrations:connectors:read"
INTEGRATIONS_CONNECTORS_MANAGE: Final[str] = "integrations:connectors:manage"
INTEGRATIONS_CONNECTORS_TEST: Final[str] = "integrations:connectors:test"
INTEGRATIONS_WEBHOOKS_READ: Final[str] = "integrations:webhooks:read"
INTEGRATIONS_WEBHOOKS_MANAGE: Final[str] = "integrations:webhooks:manage"
INTEGRATIONS_SYNC_READ: Final[str] = "integrations:sync:read"
INTEGRATIONS_SYNC_MANAGE: Final[str] = "integrations:sync:manage"
INTEGRATIONS_SYNC_EXECUTE: Final[str] = "integrations:sync:execute"
INTEGRATIONS_LOGS_READ: Final[str] = "integrations:logs:read"
INTEGRATIONS_HEALTH_READ: Final[str] = "integrations:health:read"
INTEGRATIONS_CREDENTIALS_MANAGE: Final[str] = "integrations:credentials:manage"
INTEGRATIONS_DELIVERIES_RETRY: Final[str] = "integrations:deliveries:retry"

# Dot notation aliases
INTEGRATIONS_READ_DOT: Final[str] = "integrations.read"
INTEGRATIONS_MANAGE_DOT: Final[str] = "integrations.manage"
INTEGRATIONS_CONNECTORS_READ_DOT: Final[str] = "integrations.connectors.read"
INTEGRATIONS_CONNECTORS_MANAGE_DOT: Final[str] = "integrations.connectors.manage"
INTEGRATIONS_CONNECTORS_TEST_DOT: Final[str] = "integrations.connectors.test"
INTEGRATIONS_WEBHOOKS_READ_DOT: Final[str] = "integrations.webhooks.read"
INTEGRATIONS_WEBHOOKS_MANAGE_DOT: Final[str] = "integrations.webhooks.manage"
INTEGRATIONS_SYNC_READ_DOT: Final[str] = "integrations.sync.read"
INTEGRATIONS_SYNC_MANAGE_DOT: Final[str] = "integrations.sync.manage"
INTEGRATIONS_SYNC_EXECUTE_DOT: Final[str] = "integrations.sync.execute"
INTEGRATIONS_LOGS_READ_DOT: Final[str] = "integrations.logs.read"
INTEGRATIONS_HEALTH_READ_DOT: Final[str] = "integrations.health.read"
INTEGRATIONS_CREDENTIALS_MANAGE_DOT: Final[str] = "integrations.credentials.manage"
INTEGRATIONS_DELIVERIES_RETRY_DOT: Final[str] = "integrations.deliveries.retry"

# --- Enterprise API Platform & Developer Portal Domain Permissions (Step 21) ---
API_PLATFORM_READ: Final[str] = "api:platform:read"
API_PLATFORM_MANAGE: Final[str] = "api:platform:manage"
API_APPLICATIONS_CREATE: Final[str] = "api:applications:create"
API_APPLICATIONS_READ: Final[str] = "api:applications:read"
API_APPLICATIONS_MANAGE: Final[str] = "api:applications:manage"
API_APPLICATIONS_APPROVE: Final[str] = "api:applications:approve"
API_CREDENTIALS_CREATE: Final[str] = "api:credentials:create"
API_CREDENTIALS_ROTATE: Final[str] = "api:credentials:rotate"
API_CREDENTIALS_REVOKE: Final[str] = "api:credentials:revoke"
API_SCOPES_MANAGE: Final[str] = "api:scopes:manage"
API_CATALOG_READ: Final[str] = "api:catalog:read"
API_CATALOG_MANAGE: Final[str] = "api:catalog:manage"
API_ANALYTICS_READ: Final[str] = "api:analytics:read"

# Dot notation aliases
API_PLATFORM_READ_DOT: Final[str] = "api.platform.read"
API_PLATFORM_MANAGE_DOT: Final[str] = "api.platform.manage"
API_APPLICATIONS_CREATE_DOT: Final[str] = "api.applications.create"
API_APPLICATIONS_READ_DOT: Final[str] = "api.applications.read"
API_APPLICATIONS_MANAGE_DOT: Final[str] = "api.applications.manage"
API_APPLICATIONS_APPROVE_DOT: Final[str] = "api.applications.approve"
API_CREDENTIALS_CREATE_DOT: Final[str] = "api.credentials.create"
API_CREDENTIALS_ROTATE_DOT: Final[str] = "api.credentials.rotate"
API_CREDENTIALS_REVOKE_DOT: Final[str] = "api.credentials.revoke"
API_SCOPES_MANAGE_DOT: Final[str] = "api.scopes.manage"
API_CATALOG_READ_DOT: Final[str] = "api.catalog.read"
API_CATALOG_MANAGE_DOT: Final[str] = "api.catalog.manage"
API_ANALYTICS_READ_DOT: Final[str] = "api.analytics.read"

# --- Enterprise Identity, SSO, Session & Access Federation (Step 22) ---
IDENTITY_READ: Final[str] = "identity:read"
IDENTITY_MANAGE: Final[str] = "identity:manage"
IDENTITY_PROVIDERS_READ: Final[str] = "identity:providers:read"
IDENTITY_PROVIDERS_MANAGE: Final[str] = "identity:providers:manage"
IDENTITY_PROVIDERS_TEST: Final[str] = "identity:providers:test"
IDENTITY_SESSIONS_READ: Final[str] = "identity:sessions:read"
IDENTITY_SESSIONS_REVOKE: Final[str] = "identity:sessions:revoke"
IDENTITY_EXTERNAL_LINKS_READ: Final[str] = "identity:external_links:read"
IDENTITY_EXTERNAL_LINKS_MANAGE: Final[str] = "identity:external_links:manage"
IDENTITY_MFA_MANAGE: Final[str] = "identity:mfa:manage"
IDENTITY_POLICIES_READ: Final[str] = "identity:policies:read"
IDENTITY_POLICIES_MANAGE: Final[str] = "identity:policies:manage"
IDENTITY_SECURITY_EVENTS_READ: Final[str] = "identity:security_events:read"

# Dot notation aliases
IDENTITY_READ_DOT: Final[str] = "identity.read"
IDENTITY_MANAGE_DOT: Final[str] = "identity.manage"
IDENTITY_PROVIDERS_READ_DOT: Final[str] = "identity.providers.read"
IDENTITY_PROVIDERS_MANAGE_DOT: Final[str] = "identity.providers.manage"
IDENTITY_PROVIDERS_TEST_DOT: Final[str] = "identity.providers.test"
IDENTITY_SESSIONS_READ_DOT: Final[str] = "identity.sessions.read"
IDENTITY_SESSIONS_REVOKE_DOT: Final[str] = "identity.sessions.revoke"
IDENTITY_EXTERNAL_LINKS_READ_DOT: Final[str] = "identity.external_links.read"
IDENTITY_EXTERNAL_LINKS_MANAGE_DOT: Final[str] = "identity.external_links.manage"
IDENTITY_MFA_MANAGE_DOT: Final[str] = "identity.mfa.manage"
IDENTITY_POLICIES_READ_DOT: Final[str] = "identity.policies.read"
IDENTITY_POLICIES_MANAGE_DOT: Final[str] = "identity.policies.manage"
IDENTITY_SECURITY_EVENTS_READ_DOT: Final[str] = "identity.security_events.read"

# --- Enterprise Administration, Configuration & Policy Management (Step 23) ---
CONFIGURATION_READ: Final[str] = "configuration:read"
CONFIGURATION_CREATE: Final[str] = "configuration:create"
CONFIGURATION_UPDATE: Final[str] = "configuration:update"
CONFIGURATION_DELETE: Final[str] = "configuration:delete"
CONFIGURATION_APPROVE: Final[str] = "configuration:approve"
CONFIGURATION_ROLLBACK: Final[str] = "configuration:rollback"
CONFIGURATION_PREVIEW: Final[str] = "configuration:preview"

POLICY_READ: Final[str] = "policy:read"
POLICY_MANAGE: Final[str] = "policy:manage"

FEATURE_FLAG_READ: Final[str] = "feature_flag:read"
FEATURE_FLAG_MANAGE: Final[str] = "feature_flag:manage"

MODULE_READ: Final[str] = "module:read"
MODULE_MANAGE: Final[str] = "module:manage"

SEQUENCE_READ: Final[str] = "sequence:read"
SEQUENCE_MANAGE: Final[str] = "sequence:manage"

# --- Enterprise Master Data Management & Data Quality (Step 24) ---
MASTER_DATA_READ: Final[str] = "master_data:read"
MASTER_DATA_VALIDATE: Final[str] = "master_data:validate"
MASTER_DATA_CORRECT: Final[str] = "master_data:correct"
MASTER_DATA_MERGE: Final[str] = "master_data:merge"
MASTER_DATA_APPROVE: Final[str] = "master_data:approve"
MASTER_DATA_REFERENCE_MANAGE: Final[str] = "master_data:reference_manage"
MASTER_DATA_QUALITY_MANAGE: Final[str] = "master_data:quality_manage"
MASTER_DATA_DEFINITION_MANAGE: Final[str] = "master_data:definition_manage"

# Dot notation aliases
CONFIGURATION_READ_DOT: Final[str] = "configuration.read"
CONFIGURATION_CREATE_DOT: Final[str] = "configuration.create"
CONFIGURATION_UPDATE_DOT: Final[str] = "configuration.update"
CONFIGURATION_DELETE_DOT: Final[str] = "configuration.delete"
CONFIGURATION_APPROVE_DOT: Final[str] = "configuration.approve"
CONFIGURATION_ROLLBACK_DOT: Final[str] = "configuration.rollback"
CONFIGURATION_PREVIEW_DOT: Final[str] = "configuration.preview"

POLICY_READ_DOT: Final[str] = "policy.read"
POLICY_MANAGE_DOT: Final[str] = "policy.manage"

FEATURE_FLAG_READ_DOT: Final[str] = "feature_flag.read"
FEATURE_FLAG_MANAGE_DOT: Final[str] = "feature_flag.manage"

MODULE_READ_DOT: Final[str] = "module.read"
MODULE_MANAGE_DOT: Final[str] = "module.manage"

SEQUENCE_READ_DOT: Final[str] = "sequence.read"
SEQUENCE_MANAGE_DOT: Final[str] = "sequence.manage"

MASTER_DATA_READ_DOT: Final[str] = "master_data.read"
MASTER_DATA_VALIDATE_DOT: Final[str] = "master_data.validate"
MASTER_DATA_CORRECT_DOT: Final[str] = "master_data.correct"
MASTER_DATA_MERGE_DOT: Final[str] = "master_data.merge"
MASTER_DATA_APPROVE_DOT: Final[str] = "master_data.approve"
MASTER_DATA_REFERENCE_MANAGE_DOT: Final[str] = "master_data.reference.manage"
MASTER_DATA_QUALITY_MANAGE_DOT: Final[str] = "master_data.quality.manage"
MASTER_DATA_DEFINITION_MANAGE_DOT: Final[str] = "master_data.definition.manage"

# --- Enterprise Case Management & HITL Operations (Step 25) ---
CASES_READ: Final[str] = "cases:read"
CASES_CREATE: Final[str] = "cases:create"
CASES_UPDATE: Final[str] = "cases:update"
CASES_RESOLVE: Final[str] = "cases:resolve"
CASES_CLOSE: Final[str] = "cases:close"
CASES_REOPEN: Final[str] = "cases:reopen"
CASES_ASSIGN: Final[str] = "cases:assign"
CASES_COMMENT: Final[str] = "cases:comment"

TASKS_READ: Final[str] = "tasks:read"
TASKS_CLAIM: Final[str] = "tasks:claim"
TASKS_RELEASE: Final[str] = "tasks:release"
TASKS_COMPLETE: Final[str] = "tasks:complete"
TASKS_REASSIGN: Final[str] = "tasks:reassign"
TASKS_DELEGATE: Final[str] = "tasks:delegate"
TASKS_ESCALATE: Final[str] = "tasks:escalate"

QUEUES_READ: Final[str] = "queues:read"
QUEUES_MANAGE: Final[str] = "queues:manage"

SLA_POLICIES_READ: Final[str] = "sla_policies:read"
SLA_POLICIES_MANAGE: Final[str] = "sla_policies:manage"

WORKFLOWS_TRANSITION: Final[str] = "workflows:transition"

# Dot notation aliases
CASES_READ_DOT: Final[str] = "cases.read"
CASES_CREATE_DOT: Final[str] = "cases.create"
CASES_UPDATE_DOT: Final[str] = "cases.update"
CASES_RESOLVE_DOT: Final[str] = "cases.resolve"
CASES_CLOSE_DOT: Final[str] = "cases.close"
CASES_REOPEN_DOT: Final[str] = "cases.reopen"
CASES_ASSIGN_DOT: Final[str] = "cases.assign"
CASES_COMMENT_DOT: Final[str] = "cases.comment"

TASKS_READ_DOT: Final[str] = "tasks.read"
TASKS_CLAIM_DOT: Final[str] = "tasks.claim"
TASKS_RELEASE_DOT: Final[str] = "tasks.release"
TASKS_COMPLETE_DOT: Final[str] = "tasks.complete"
TASKS_REASSIGN_DOT: Final[str] = "tasks.reassign"
TASKS_DELEGATE_DOT: Final[str] = "tasks.delegate"
TASKS_ESCALATE_DOT: Final[str] = "tasks.escalate"

QUEUES_READ_DOT: Final[str] = "queues.read"
QUEUES_MANAGE_DOT: Final[str] = "queues.manage"

SLA_POLICIES_READ_DOT: Final[str] = "sla_policies.read"
SLA_POLICIES_MANAGE_DOT: Final[str] = "sla_policies.manage"

WORKFLOWS_TRANSITION_DOT: Final[str] = "workflows.transition"

# --- Enterprise Notification, Communication & Delivery Orchestration (Step 26) ---
NOTIFICATIONS_READ: Final[str] = "notifications:read"
NOTIFICATIONS_MANAGE_PREFERENCES: Final[str] = "notifications:preferences:manage"
NOTIFICATION_TEMPLATES_READ: Final[str] = "notifications:templates:read"
NOTIFICATION_TEMPLATES_MANAGE: Final[str] = "notifications:templates:manage"
NOTIFICATION_RULES_MANAGE: Final[str] = "notifications:rules:manage"
NOTIFICATION_DELIVERIES_READ: Final[str] = "notifications:deliveries:read"
NOTIFICATION_DELIVERIES_RETRY: Final[str] = "notifications:deliveries:retry"
NOTIFICATION_DELIVERIES_CANCEL: Final[str] = "notifications:deliveries:cancel"
NOTIFICATION_ANALYTICS_READ: Final[str] = "notifications:analytics:read"
NOTIFICATION_PROVIDERS_MANAGE: Final[str] = "notifications:providers:manage"

# Dot notation aliases
NOTIFICATIONS_READ_DOT: Final[str] = "notification.read"
NOTIFICATIONS_MANAGE_PREFERENCES_DOT: Final[str] = "notification.manage_preferences"
NOTIFICATION_TEMPLATES_READ_DOT: Final[str] = "notification_template.read"
NOTIFICATION_TEMPLATES_MANAGE_DOT: Final[str] = "notification_template.manage"
NOTIFICATION_RULES_MANAGE_DOT: Final[str] = "notification_rule.manage"
NOTIFICATION_DELIVERIES_READ_DOT: Final[str] = "notification_delivery.read"
NOTIFICATION_DELIVERIES_RETRY_DOT: Final[str] = "notification_delivery.retry"
NOTIFICATION_DELIVERIES_CANCEL_DOT: Final[str] = "notification_delivery.cancel"
NOTIFICATION_ANALYTICS_READ_DOT: Final[str] = "notification_analytics.read"
NOTIFICATION_PROVIDERS_MANAGE_DOT: Final[str] = "notification_provider.manage"

# --- Enterprise Domain Events, Outbox & Reliability Backbone (Step 27) ---
DOMAIN_EVENTS_READ: Final[str] = "events:domain:read"
DOMAIN_EVENTS_RETRY: Final[str] = "events:domain:retry"
DOMAIN_EVENTS_REPLAY: Final[str] = "events:domain:replay"
DOMAIN_EVENTS_CONSUMERS_MANAGE: Final[str] = "events:domain:consumers:manage"
DOMAIN_EVENTS_METRICS_READ: Final[str] = "events:domain:metrics:read"

DOMAIN_EVENTS_READ_DOT: Final[str] = "events.domain.read"
DOMAIN_EVENTS_RETRY_DOT: Final[str] = "events.domain.retry"
DOMAIN_EVENTS_REPLAY_DOT: Final[str] = "events.domain.replay"
DOMAIN_EVENTS_CONSUMERS_MANAGE_DOT: Final[str] = "events.domain.consumers.manage"
DOMAIN_EVENTS_METRICS_READ_DOT: Final[str] = "events.domain.metrics.read"

# --- Enterprise Platform Administration & SaaS Operations (Step 30) ---
PLATFORM_TENANTS_READ: Final[str] = "platform:tenants:read"
PLATFORM_TENANTS_MANAGE: Final[str] = "platform:tenants:manage"
PLATFORM_LIFECYCLE_MANAGE: Final[str] = "platform:lifecycle:manage"
PLATFORM_PROVISION_MANAGE: Final[str] = "platform:provision:manage"
PLATFORM_ENTITLEMENTS_MANAGE: Final[str] = "platform:entitlements:manage"
PLATFORM_QUOTAS_MANAGE: Final[str] = "platform:quotas:manage"
PLATFORM_SUPPORT_ACCESS: Final[str] = "platform:support:access"
PLATFORM_DELETION_MANAGE: Final[str] = "platform:deletion:manage"
PLATFORM_OPS_HEALTH_READ: Final[str] = "platform:ops:health:read"

# --- Enterprise Reliability Engineering & Disaster Recovery (Step 31) ---
PLATFORM_RELIABILITY_READ: Final[str] = "platform:reliability:read"
PLATFORM_RELIABILITY_MANAGE: Final[str] = "platform:reliability:manage"
PLATFORM_BACKUP_TRIGGER: Final[str] = "platform:backup:trigger"
PLATFORM_RESTORE_VERIFY: Final[str] = "platform:restore:verify"

PLATFORM_TENANTS_READ_DOT: Final[str] = "platform.tenants.read"
PLATFORM_TENANTS_MANAGE_DOT: Final[str] = "platform.tenants.manage"
PLATFORM_LIFECYCLE_MANAGE_DOT: Final[str] = "platform.lifecycle.manage"
PLATFORM_PROVISION_MANAGE_DOT: Final[str] = "platform.provision.manage"
PLATFORM_ENTITLEMENTS_MANAGE_DOT: Final[str] = "platform.entitlements.manage"
PLATFORM_QUOTAS_MANAGE_DOT: Final[str] = "platform.quotas.manage"
PLATFORM_SUPPORT_ACCESS_DOT: Final[str] = "platform.support.access"
PLATFORM_DELETION_MANAGE_DOT: Final[str] = "platform.deletion.manage"
PLATFORM_OPS_HEALTH_READ_DOT: Final[str] = "platform.ops.health.read"

PLATFORM_RELIABILITY_READ_DOT: Final[str] = "platform.reliability.read"
PLATFORM_RELIABILITY_MANAGE_DOT: Final[str] = "platform.reliability.manage"
PLATFORM_BACKUP_TRIGGER_DOT: Final[str] = "platform.backup.trigger"
PLATFORM_RESTORE_VERIFY_DOT: Final[str] = "platform.restore.verify"

# --- Enterprise Security Operations, Threat Detection & Incident Response (Step 33) ---
SECURITY_INCIDENTS_READ: Final[str] = "security:incidents:read"
SECURITY_INCIDENTS_MANAGE: Final[str] = "security:incidents:manage"
SECURITY_ACTIONS_PROPOSE: Final[str] = "security:actions:propose"
SECURITY_ACTIONS_APPROVE: Final[str] = "security:actions:approve"
SECURITY_ACTIONS_EXECUTE: Final[str] = "security:actions:execute"
SECURITY_RULES_MANAGE: Final[str] = "security:rules:manage"
SECURITY_PLATFORM_READ: Final[str] = "security:platform:read"

SECURITY_INCIDENTS_READ_DOT: Final[str] = "security.incidents.read"
SECURITY_INCIDENTS_MANAGE_DOT: Final[str] = "security.incidents.manage"
SECURITY_ACTIONS_PROPOSE_DOT: Final[str] = "security.actions.propose"
SECURITY_ACTIONS_APPROVE_DOT: Final[str] = "security.actions.approve"
SECURITY_ACTIONS_EXECUTE_DOT: Final[str] = "security.actions.execute"
SECURITY_RULES_MANAGE_DOT: Final[str] = "security.rules.manage"
SECURITY_PLATFORM_READ_DOT: Final[str] = "security.platform.read"

# --- Enterprise Data Import, Migration, Reconciliation & Interoperability (Step 40) ---
DATA_IMPORT_READ: Final[str] = "data:import:read"
DATA_IMPORT_CREATE: Final[str] = "data:import:create"
DATA_IMPORT_MANAGE: Final[str] = "data:import:manage"
DATA_IMPORT_APPROVE: Final[str] = "data:import:approve"
DATA_IMPORT_EXECUTE: Final[str] = "data:import:execute"
DATA_IMPORT_CANCEL: Final[str] = "data:import:cancel"
DATA_IMPORT_RECONCILE: Final[str] = "data:import:reconcile"
DATA_IMPORT_DOWNLOAD: Final[str] = "data:import:download"

DATA_IMPORT_READ_DOT: Final[str] = "data.import.read"
DATA_IMPORT_CREATE_DOT: Final[str] = "data.import.create"
DATA_IMPORT_MANAGE_DOT: Final[str] = "data.import.manage"
DATA_IMPORT_APPROVE_DOT: Final[str] = "data.import.approve"
DATA_IMPORT_EXECUTE_DOT: Final[str] = "data.import.execute"
DATA_IMPORT_CANCEL_DOT: Final[str] = "data.import.cancel"
DATA_IMPORT_RECONCILE_DOT: Final[str] = "data.import.reconcile"
DATA_IMPORT_DOWNLOAD_DOT: Final[str] = "data.import.download"

# --- Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management (Step 41) ---
RECORDS_READ: Final[str] = "records:read"
RECORDS_CREATE: Final[str] = "records:create"
RECORDS_MANAGE: Final[str] = "records:manage"
RECORDS_POLICY_MANAGE: Final[str] = "records:policy:manage"
RECORDS_POLICY_PUBLISH: Final[str] = "records:policy:publish"
RECORDS_ARCHIVE_EXECUTE: Final[str] = "records:archive:execute"
RECORDS_ARCHIVE_RETRIEVE: Final[str] = "records:archive:retrieve"
RECORDS_HOLD_CREATE: Final[str] = "records:hold:create"
RECORDS_HOLD_MANAGE: Final[str] = "records:hold:manage"
RECORDS_HOLD_RELEASE: Final[str] = "records:hold:release"
RECORDS_DISPOSITION_REQUEST: Final[str] = "records:disposition:request"
RECORDS_DISPOSITION_APPROVE: Final[str] = "records:disposition:approve"
RECORDS_DISPOSITION_EXECUTE: Final[str] = "records:disposition:execute"

RECORDS_READ_DOT: Final[str] = "records.read"
RECORDS_CREATE_DOT: Final[str] = "records.create"
RECORDS_MANAGE_DOT: Final[str] = "records.manage"
RECORDS_POLICY_MANAGE_DOT: Final[str] = "records.policy.manage"
RECORDS_POLICY_PUBLISH_DOT: Final[str] = "records.policy.publish"
RECORDS_ARCHIVE_EXECUTE_DOT: Final[str] = "records.archive.execute"
RECORDS_ARCHIVE_RETRIEVE_DOT: Final[str] = "records.archive.retrieve"
RECORDS_HOLD_CREATE_DOT: Final[str] = "records.hold.create"
RECORDS_HOLD_MANAGE_DOT: Final[str] = "records.hold.manage"
RECORDS_HOLD_RELEASE_DOT: Final[str] = "records.hold.release"
RECORDS_DISPOSITION_REQUEST_DOT: Final[str] = "records.disposition.request"
RECORDS_DISPOSITION_APPROVE_DOT: Final[str] = "records.disposition.approve"
RECORDS_DISPOSITION_EXECUTE_DOT: Final[str] = "records.disposition.execute"

# --- Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge (Step 42) ---
KNOWLEDGE_READ: Final[str] = "knowledge:read"
KNOWLEDGE_CREATE: Final[str] = "knowledge:create"
KNOWLEDGE_MANAGE: Final[str] = "knowledge:manage"
KNOWLEDGE_REVIEW: Final[str] = "knowledge:review"
KNOWLEDGE_APPROVE: Final[str] = "knowledge:approve"
KNOWLEDGE_PUBLISH: Final[str] = "knowledge:publish"
KNOWLEDGE_RETIRE: Final[str] = "knowledge:retire"
KNOWLEDGE_ACKNOWLEDGE: Final[str] = "knowledge:acknowledge"
KNOWLEDGE_ATTESTATION_READ: Final[str] = "knowledge:attestation:read"

KNOWLEDGE_READ_DOT: Final[str] = "knowledge.read"
KNOWLEDGE_CREATE_DOT: Final[str] = "knowledge.create"
KNOWLEDGE_MANAGE_DOT: Final[str] = "knowledge.manage"
KNOWLEDGE_REVIEW_DOT: Final[str] = "knowledge.review"
KNOWLEDGE_APPROVE_DOT: Final[str] = "knowledge.approve"
KNOWLEDGE_PUBLISH_DOT: Final[str] = "knowledge.publish"
KNOWLEDGE_RETIRE_DOT: Final[str] = "knowledge.retire"
KNOWLEDGE_ACKNOWLEDGE_DOT: Final[str] = "knowledge.acknowledge"
KNOWLEDGE_ATTESTATION_READ_DOT: Final[str] = "knowledge.attestation.read"

# --- Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement (Step 43) ---
ACCREDITATION_READ: Final[str] = "accreditation:read"
ACCREDITATION_FRAMEWORK_MANAGE: Final[str] = "accreditation:framework:manage"
ACCREDITATION_CRITERIA_MANAGE: Final[str] = "accreditation:criteria:manage"
ACCREDITATION_ASSESS: Final[str] = "accreditation:assess"
ACCREDITATION_APPROVE: Final[str] = "accreditation:approve"
ACCREDITATION_EVIDENCE_MANAGE: Final[str] = "accreditation:evidence:manage"
ACCREDITATION_EVIDENCE_VERIFY: Final[str] = "accreditation:evidence:verify"
ACCREDITATION_INDICATOR_MANAGE: Final[str] = "accreditation:indicator:manage"
ACCREDITATION_AUDIT_MANAGE: Final[str] = "accreditation:audit:manage"
ACCREDITATION_CAPA_MANAGE: Final[str] = "accreditation:capa:manage"
ACCREDITATION_IMPROVEMENT_MANAGE: Final[str] = "accreditation:improvement:manage"
ACCREDITATION_REPORT_EXPORT: Final[str] = "accreditation:report:export"

ACCREDITATION_READ_DOT: Final[str] = "accreditation.read"
ACCREDITATION_FRAMEWORK_MANAGE_DOT: Final[str] = "accreditation.framework.manage"
ACCREDITATION_CRITERIA_MANAGE_DOT: Final[str] = "accreditation.criteria.manage"
ACCREDITATION_ASSESS_DOT: Final[str] = "accreditation.assess"
ACCREDITATION_APPROVE_DOT: Final[str] = "accreditation.approve"
ACCREDITATION_EVIDENCE_MANAGE_DOT: Final[str] = "accreditation.evidence.manage"
ACCREDITATION_EVIDENCE_VERIFY_DOT: Final[str] = "accreditation.evidence.verify"
ACCREDITATION_INDICATOR_MANAGE_DOT: Final[str] = "accreditation.indicator.manage"
ACCREDITATION_AUDIT_MANAGE_DOT: Final[str] = "accreditation.audit.manage"
ACCREDITATION_CAPA_MANAGE_DOT: Final[str] = "accreditation.capa.manage"
ACCREDITATION_IMPROVEMENT_MANAGE_DOT: Final[str] = "accreditation.improvement.manage"
ACCREDITATION_REPORT_EXPORT_DOT: Final[str] = "accreditation.report.export"

# --- Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management (Step 44) ---
RESEARCH_PROJECTS_READ: Final[str] = "research:projects:read"
RESEARCH_PROJECTS_MANAGE: Final[str] = "research:projects:manage"
RESEARCH_PROJECTS_TRANSITION: Final[str] = "research:projects:transition"
RESEARCH_GRANTS_APPLY: Final[str] = "research:grants:apply"
RESEARCH_GRANTS_APPROVE: Final[str] = "research:grants:approve"
RESEARCH_AWARDS_MANAGE: Final[str] = "research:awards:manage"
RESEARCH_BUDGETS_MANAGE: Final[str] = "research:budgets:manage"
RESEARCH_ETHICS_REVIEW: Final[str] = "research:ethics:review"
RESEARCH_OUTPUTS_MANAGE: Final[str] = "research:outputs:manage"
RESEARCH_OUTPUTS_VERIFY: Final[str] = "research:outputs:verify"
RESEARCH_IP_MANAGE: Final[str] = "research:ip:manage"
RESEARCH_IP_CONFIDENTIAL_READ: Final[str] = "research:ip:confidential:read"
RESEARCH_ANALYTICS_READ: Final[str] = "research:analytics:read"

RESEARCH_PROJECTS_READ_DOT: Final[str] = "research.projects.read"
RESEARCH_PROJECTS_MANAGE_DOT: Final[str] = "research.projects.manage"
RESEARCH_PROJECTS_TRANSITION_DOT: Final[str] = "research.projects.transition"
RESEARCH_GRANTS_APPLY_DOT: Final[str] = "research.grants.apply"
RESEARCH_GRANTS_APPROVE_DOT: Final[str] = "research.grants.approve"
RESEARCH_AWARDS_MANAGE_DOT: Final[str] = "research.awards.manage"
RESEARCH_BUDGETS_MANAGE_DOT: Final[str] = "research.budgets.manage"
RESEARCH_ETHICS_REVIEW_DOT: Final[str] = "research.ethics.review"
RESEARCH_OUTPUTS_MANAGE_DOT: Final[str] = "research.outputs.manage"
RESEARCH_OUTPUTS_VERIFY_DOT: Final[str] = "research.outputs.verify"
RESEARCH_IP_MANAGE_DOT: Final[str] = "research.ip.manage"
RESEARCH_IP_CONFIDENTIAL_READ_DOT: Final[str] = "research.ip.confidential.read"
RESEARCH_ANALYTICS_READ_DOT: Final[str] = "research.analytics.read"

# --- Enterprise Institutional Library, Learning Resources & Knowledge Access Management (Step 45) ---
LIBRARY_BRANCHES_READ: Final[str] = "library:branches:read"
LIBRARY_BRANCHES_MANAGE: Final[str] = "library:branches:manage"
LIBRARY_CATALOG_READ: Final[str] = "library:catalog:read"
LIBRARY_CATALOG_MANAGE: Final[str] = "library:catalog:manage"
LIBRARY_COPIES_MANAGE: Final[str] = "library:copies:manage"
LIBRARY_MEMBERS_READ: Final[str] = "library:members:read"
LIBRARY_MEMBERS_MANAGE: Final[str] = "library:members:manage"
LIBRARY_CIRCULATION_ISSUE: Final[str] = "library:circulation:issue"
LIBRARY_CIRCULATION_RETURN: Final[str] = "library:circulation:return"
LIBRARY_CIRCULATION_RENEW: Final[str] = "library:circulation:renew"
LIBRARY_RESERVATIONS_MANAGE: Final[str] = "library:reservations:manage"
LIBRARY_FINES_MANAGE: Final[str] = "library:fines:manage"
LIBRARY_FINES_WAIVE: Final[str] = "library:fines:waive"
LIBRARY_ACQUISITIONS_REQUEST: Final[str] = "library:acquisitions:request"
LIBRARY_ACQUISITIONS_MANAGE: Final[str] = "library:acquisitions:manage"
LIBRARY_SUBSCRIPTIONS_MANAGE: Final[str] = "library:subscriptions:manage"
LIBRARY_DIGITAL_ACCESS: Final[str] = "library:digital:access"
LIBRARY_AUDIT_MANAGE: Final[str] = "library:audit:manage"
LIBRARY_ANALYTICS_READ: Final[str] = "library:analytics:read"

LIBRARY_BRANCHES_READ_DOT: Final[str] = "library.branches.read"
LIBRARY_BRANCHES_MANAGE_DOT: Final[str] = "library.branches.manage"
LIBRARY_CATALOG_READ_DOT: Final[str] = "library.catalog.read"
LIBRARY_CATALOG_MANAGE_DOT: Final[str] = "library.catalog.manage"
LIBRARY_COPIES_MANAGE_DOT: Final[str] = "library.copies.manage"
LIBRARY_MEMBERS_READ_DOT: Final[str] = "library.members.read"
LIBRARY_MEMBERS_MANAGE_DOT: Final[str] = "library.members.manage"
LIBRARY_CIRCULATION_ISSUE_DOT: Final[str] = "library.circulation.issue"
LIBRARY_CIRCULATION_RETURN_DOT: Final[str] = "library.circulation.return"
LIBRARY_CIRCULATION_RENEW_DOT: Final[str] = "library.circulation.renew"
LIBRARY_RESERVATIONS_MANAGE_DOT: Final[str] = "library.reservations.manage"
LIBRARY_FINES_MANAGE_DOT: Final[str] = "library.fines.manage"
LIBRARY_FINES_WAIVE_DOT: Final[str] = "library.fines.waive"
LIBRARY_ACQUISITIONS_REQUEST_DOT: Final[str] = "library.acquisitions.request"
LIBRARY_ACQUISITIONS_MANAGE_DOT: Final[str] = "library.acquisitions.manage"
LIBRARY_SUBSCRIPTIONS_MANAGE_DOT: Final[str] = "library.subscriptions.manage"
LIBRARY_DIGITAL_ACCESS_DOT: Final[str] = "library.digital.access"
LIBRARY_AUDIT_MANAGE_DOT: Final[str] = "library.audit.manage"
LIBRARY_ANALYTICS_READ_DOT: Final[str] = "library.analytics.read"

# --- Step 47: Student Success, Academic Advising, Early-Warning & Intervention Management ---
STUDENT_SUCCESS_CASE_READ: Final[str] = "student_success:cases:read"
STUDENT_SUCCESS_CASE_MANAGE: Final[str] = "student_success:cases:manage"
STUDENT_SUCCESS_ADVISING_READ: Final[str] = "student_success:advising:read"
STUDENT_SUCCESS_ADVISING_MANAGE: Final[str] = "student_success:advising:manage"
STUDENT_SUCCESS_EARLY_WARNING_READ: Final[str] = "student_success:early_warning:read"
STUDENT_SUCCESS_EARLY_WARNING_MANAGE: Final[str] = "student_success:early_warning:manage"
STUDENT_SUCCESS_INTERVENTION_READ: Final[str] = "student_success:interventions:read"
STUDENT_SUCCESS_INTERVENTION_MANAGE: Final[str] = "student_success:interventions:manage"
STUDENT_SUCCESS_APPOINTMENT_MANAGE: Final[str] = "student_success:appointments:manage"
STUDENT_SUCCESS_REPORTS_READ: Final[str] = "student_success:reports:read"
STUDENT_SUCCESS_STUDENT_SELF_READ: Final[str] = "student_success:student_self:read"

STUDENT_SUCCESS_CASE_READ_DOT: Final[str] = "student_success.cases.read"
STUDENT_SUCCESS_CASE_MANAGE_DOT: Final[str] = "student_success.cases.manage"
STUDENT_SUCCESS_ADVISING_READ_DOT: Final[str] = "student_success.advising.read"
STUDENT_SUCCESS_ADVISING_MANAGE_DOT: Final[str] = "student_success.advising.manage"
STUDENT_SUCCESS_EARLY_WARNING_READ_DOT: Final[str] = "student_success.early_warning.read"
STUDENT_SUCCESS_EARLY_WARNING_MANAGE_DOT: Final[str] = "student_success.early_warning.manage"
STUDENT_SUCCESS_INTERVENTION_READ_DOT: Final[str] = "student_success.interventions.read"
STUDENT_SUCCESS_INTERVENTION_MANAGE_DOT: Final[str] = "student_success.interventions.manage"
STUDENT_SUCCESS_APPOINTMENT_MANAGE_DOT: Final[str] = "student_success.appointments.manage"
STUDENT_SUCCESS_REPORTS_READ_DOT: Final[str] = "student_success.reports.read"
STUDENT_SUCCESS_STUDENT_SELF_READ_DOT: Final[str] = "student_success.student_self.read"

# --- Step 48: Student Admissions, Enrollment & Onboarding Orchestration ---
ADMISSIONS_CYCLE_READ: Final[str] = "admissions:cycles:read"
ADMISSIONS_CYCLE_MANAGE: Final[str] = "admissions:cycles:manage"
ADMISSIONS_APPLICANT_READ: Final[str] = "admissions:applicants:read"
ADMISSIONS_APPLICANT_MANAGE: Final[str] = "admissions:applicants:manage"
ADMISSIONS_APPLICATION_READ: Final[str] = "admissions:applications:read"
ADMISSIONS_APPLICATION_MANAGE: Final[str] = "admissions:applications:manage"
ADMISSIONS_DOCUMENT_VERIFY: Final[str] = "admissions:documents:verify"
ADMISSIONS_ELIGIBILITY_EVALUATE: Final[str] = "admissions:eligibility:evaluate"
ADMISSIONS_REVIEW_MANAGE: Final[str] = "admissions:reviews:manage"
ADMISSIONS_SELECTION_MANAGE: Final[str] = "admissions:selection:manage"
ADMISSIONS_OFFERS_MANAGE: Final[str] = "admissions:offers:manage"
ADMISSIONS_ENROLLMENT_ORCHESTRATE: Final[str] = "admissions:enrollment:orchestrate"
ADMISSIONS_ONBOARDING_MANAGE: Final[str] = "admissions:onboarding:manage"
ADMISSIONS_REPORTS_READ: Final[str] = "admissions:reports:read"
ADMISSIONS_APPLICANT_SELF: Final[str] = "admissions:applicant_self:manage"

ADMISSIONS_CYCLE_READ_DOT: Final[str] = "admissions.cycles.read"
ADMISSIONS_CYCLE_MANAGE_DOT: Final[str] = "admissions.cycles.manage"
ADMISSIONS_APPLICANT_READ_DOT: Final[str] = "admissions.applicants.read"
ADMISSIONS_APPLICANT_MANAGE_DOT: Final[str] = "admissions.applicants.manage"
ADMISSIONS_APPLICATION_READ_DOT: Final[str] = "admissions.applications.read"
ADMISSIONS_APPLICATION_MANAGE_DOT: Final[str] = "admissions.applications.manage"
ADMISSIONS_DOCUMENT_VERIFY_DOT: Final[str] = "admissions.documents.verify"
ADMISSIONS_ELIGIBILITY_EVALUATE_DOT: Final[str] = "admissions.eligibility.evaluate"
ADMISSIONS_REVIEW_MANAGE_DOT: Final[str] = "admissions.reviews.manage"
ADMISSIONS_SELECTION_MANAGE_DOT: Final[str] = "admissions.selection.manage"
ADMISSIONS_OFFERS_MANAGE_DOT: Final[str] = "admissions.offers.manage"
ADMISSIONS_ENROLLMENT_ORCHESTRATE_DOT: Final[str] = "admissions.enrollment.orchestrate"
ADMISSIONS_ONBOARDING_MANAGE_DOT: Final[str] = "admissions.onboarding.manage"
ADMISSIONS_REPORTS_READ_DOT: Final[str] = "admissions.reports.read"
ADMISSIONS_APPLICANT_SELF_DOT: Final[str] = "admissions.applicant_self.manage"



# Comprehensive Registry
ALL_PERMISSIONS: Final[list[PermissionDefinition]] = [

    # Core
    PermissionDefinition(CORE_INSTITUTION_READ, "core", "Read institutional metadata"),
    PermissionDefinition(CORE_INSTITUTION_MANAGE, "core", "Configure institution settings"),
    PermissionDefinition(CORE_CAMPUSES_READ, "core", "View physical campuses"),
    PermissionDefinition(CORE_CAMPUSES_MANAGE, "core", "Manage physical campuses"),
    PermissionDefinition(CORE_DEPARTMENTS_READ, "core", "View academic & admin departments"),
    PermissionDefinition(CORE_DEPARTMENTS_MANAGE, "core", "Manage academic & admin departments"),
    PermissionDefinition(CORE_PROGRAMS_READ, "core", "View academic programs and degrees"),
    PermissionDefinition(CORE_PROGRAMS_MANAGE, "core", "Manage academic programs and degrees"),
    PermissionDefinition(CORE_REGULATIONS_MANAGE, "core", "Manage curriculum schemes/regulations"),
    PermissionDefinition(CORE_ACADEMIC_YEARS_READ, "core", "View academic years and terms"),
    PermissionDefinition(CORE_ACADEMIC_YEARS_MANAGE, "core", "Manage academic years and semesters"),
    PermissionDefinition(CORE_SECTIONS_READ, "core", "View class cohorts and sections"),
    PermissionDefinition(CORE_SECTIONS_MANAGE, "core", "Manage class cohorts and sections"),
    # People
    PermissionDefinition(PEOPLE_USERS_READ, "people", "View user accounts"),
    PermissionDefinition(PEOPLE_USERS_MANAGE, "people", "Manage user lifecycle and accounts"),
    PermissionDefinition(PEOPLE_STUDENTS_READ, "people", "View student institutional profiles"),
    PermissionDefinition(PEOPLE_STUDENTS_CREATE, "people", "Admit and onboard new students"),
    PermissionDefinition(PEOPLE_STUDENTS_UPDATE, "people", "Update student institutional profiles"),
    PermissionDefinition(PEOPLE_FACULTY_READ, "people", "View faculty profiles"),
    PermissionDefinition(PEOPLE_FACULTY_MANAGE, "people", "Manage faculty profiles"),
    PermissionDefinition(PEOPLE_STAFF_READ, "people", "View operational staff profiles"),
    PermissionDefinition(PEOPLE_STAFF_MANAGE, "people", "Manage operational staff profiles"),
    PermissionDefinition(PEOPLE_ROLES_MANAGE, "people", "Configure roles and permissions"),
    # Academics
    PermissionDefinition(ACADEMICS_SUBJECTS_READ, "academics", "View subject catalog"),
    PermissionDefinition(ACADEMICS_SUBJECTS_MANAGE, "academics", "Manage subject catalog"),
    PermissionDefinition(ACADEMICS_CURRICULUM_READ, "academics", "View curriculum versions"),
    PermissionDefinition(ACADEMICS_CURRICULUM_MANAGE, "academics", "Manage curriculum schemes"),
    PermissionDefinition(ACADEMICS_CURRICULUM_PUBLISH, "academics", "Publish curriculum versions"),
    PermissionDefinition(ACADEMICS_COURSES_READ, "academics", "View term course offerings"),
    PermissionDefinition(ACADEMICS_COURSES_MANAGE, "academics", "Manage courses & faculty"),
    PermissionDefinition(ACADEMICS_ENROLLMENTS_READ, "academics", "View course enrollments"),
    PermissionDefinition(ACADEMICS_ENROLLMENTS_MANAGE, "academics", "Manage course enrollments"),
    PermissionDefinition(ACADEMICS_TIMETABLE_READ, "academics", "View master timetable schedules"),
    PermissionDefinition(ACADEMICS_TIMETABLE_MANAGE, "academics", "Configure class timetables"),
    PermissionDefinition(ACADEMICS_ROOMS_READ, "academics", "View academic rooms"),
    PermissionDefinition(ACADEMICS_ROOMS_MANAGE, "academics", "Manage academic rooms"),
    PermissionDefinition(ACADEMICS_ENROLL_SELF, "academics", "Register for courses as a student"),
    # Attendance
    PermissionDefinition(ATTENDANCE_SESSIONS_READ, "attendance", "View attendance registers"),
    PermissionDefinition(ATTENDANCE_RECORDS_READ, "attendance", "View individual attendance marks"),
    PermissionDefinition(ATTENDANCE_RECORDS_WRITE, "attendance", "Record class attendance"),
    PermissionDefinition(
        ATTENDANCE_CORRECTIONS_APPROVE, "attendance", "Approve attendance dispute corrections"
    ),
    PermissionDefinition(ATTENDANCE_LEAVE_APPLY, "attendance", "Apply for formal leave"),
    PermissionDefinition(ATTENDANCE_LEAVE_APPROVE, "attendance", "Review and approve leave"),
    PermissionDefinition(ATTENDANCE_READ, "attendance", "Read attendance registers and summaries"),
    PermissionDefinition(ATTENDANCE_MARK, "attendance", "Mark session attendance"),
    PermissionDefinition(ATTENDANCE_UPDATE, "attendance", "Update marked attendance"),
    PermissionDefinition(ATTENDANCE_LOCK, "attendance", "Lock attendance session"),
    PermissionDefinition(ATTENDANCE_CORRECT, "attendance", "Request attendance correction"),
    PermissionDefinition(
        ATTENDANCE_APPROVE_CORRECTION, "attendance", "Approve attendance correction"
    ),
    PermissionDefinition(LEAVE_READ, "attendance", "View leave requests"),
    PermissionDefinition(LEAVE_CREATE, "attendance", "Submit leave request"),
    PermissionDefinition(LEAVE_APPROVE, "attendance", "Approve student leave"),
    PermissionDefinition(LEAVE_REJECT, "attendance", "Reject student leave"),
    PermissionDefinition(ATTENDANCE_POLICY_READ, "attendance", "Read attendance policies"),
    PermissionDefinition(ATTENDANCE_POLICY_CREATE, "attendance", "Create attendance policy"),
    PermissionDefinition(ATTENDANCE_POLICY_UPDATE, "attendance", "Update attendance policy"),
    # Examination
    PermissionDefinition(EXAMINATION_ASSESSMENTS_READ, "examination", "View assessment schemes"),
    PermissionDefinition(EXAMINATION_ASSESSMENTS_MANAGE, "examination", "Configure assessments"),
    PermissionDefinition(EXAMINATION_MARKS_WRITE, "examination", "Enter raw marks and grades"),
    PermissionDefinition(EXAMINATION_RESULTS_APPROVE, "examination", "Approve moderated grades"),
    PermissionDefinition(EXAMINATION_RESULTS_PUBLISH, "examination", "Publish official results"),
    PermissionDefinition(EXAMINATION_RESULTS_READ_SELF, "examination", "View personal grade cards"),
    PermissionDefinition(EXAMINATIONS_READ, "examination", "View examinations and cycles"),
    PermissionDefinition(
        EXAMINATIONS_CREATE, "examination", "Create examination cycle and schedules"
    ),
    PermissionDefinition(
        EXAMINATIONS_UPDATE, "examination", "Update examination schedule and terms"
    ),
    PermissionDefinition(ASSESSMENTS_READ, "examination", "View course assessments and components"),
    PermissionDefinition(ASSESSMENTS_CREATE, "examination", "Create course assessments"),
    PermissionDefinition(
        ASSESSMENTS_UPDATE, "examination", "Update course assessments and weightage"
    ),
    PermissionDefinition(ASSESSMENTS_FINALIZE, "examination", "Finalize assessment component"),
    PermissionDefinition(MARKS_READ, "examination", "View entered assessment marks"),
    PermissionDefinition(MARKS_ENTER, "examination", "Enter raw student assessment marks"),
    PermissionDefinition(MARKS_UPDATE, "examination", "Update draft student assessment marks"),
    PermissionDefinition(MARKS_FINALIZE, "examination", "Finalize assessment marks"),
    PermissionDefinition(MARKS_CORRECT, "examination", "Request or approve marks corrections"),
    PermissionDefinition(RESULTS_READ, "examination", "View course and semester exam results"),
    PermissionDefinition(RESULTS_FINALIZE, "examination", "Finalize and generate semester results"),
    PermissionDefinition(RESULTS_PUBLISH, "examination", "Publish official examination results"),
    PermissionDefinition(GRADE_SCALES_READ, "examination", "View institutional grading scales"),
    PermissionDefinition(GRADE_SCALES_MANAGE, "examination", "Configure grading scale bands"),
    PermissionDefinition(ELIGIBILITY_READ, "examination", "View student examination eligibility"),
    PermissionDefinition(
        ELIGIBILITY_EVALUATE, "examination", "Evaluate student examination eligibility"
    ),
    PermissionDefinition(
        ELIGIBILITY_OVERRIDE, "examination", "Override examination eligibility restrictions"
    ),
    PermissionDefinition(FINANCE_STRUCTURES_MANAGE, "finance", "Configure fee structures"),
    PermissionDefinition(FINANCE_INVOICES_READ, "finance", "View student invoices and ledgers"),
    PermissionDefinition(FINANCE_INVOICES_CREATE, "finance", "Generate student billing invoices"),
    PermissionDefinition(FINANCE_PAYMENTS_RECORD, "finance", "Record manual payment collections"),
    PermissionDefinition(FINANCE_PAYMENTS_PAY_SELF, "finance", "Pay personal fees via gateway"),
    PermissionDefinition(FINANCE_REFUNDS_APPROVE, "finance", "Authorize fee refunds & adjustments"),
    PermissionDefinition(FINANCE_REPORTS_READ, "finance", "Access financial billing analytics"),
    # Step 8 Granular Suite
    PermissionDefinition(FINANCE_READ, "finance", "View institutional billing and financial state"),
    PermissionDefinition(
        FINANCE_MANAGE_FEE_STRUCTURES, "finance", "Author, approve and activate fee structures"
    ),
    PermissionDefinition(INVOICES_READ, "finance", "View student fee invoices and billing lines"),
    PermissionDefinition(
        INVOICES_CREATE, "finance", "Generate student invoices from fee assignments"
    ),
    PermissionDefinition(INVOICES_ISSUE, "finance", "Issue draft invoices and commit balances"),
    PermissionDefinition(
        INVOICES_CANCEL, "finance", "Cancel issued invoices without balance corruption"
    ),
    PermissionDefinition(PAYMENTS_READ, "finance", "Inspect payment transaction records"),
    PermissionDefinition(PAYMENTS_CREATE, "finance", "Record inward student payments"),
    PermissionDefinition(PAYMENTS_CONFIRM, "finance", "Confirm and verify payment transactions"),
    PermissionDefinition(RECEIPTS_READ, "finance", "View and download payment receipts"),
    PermissionDefinition(RECEIPTS_ISSUE, "finance", "Generate and issue official payment receipts"),
    PermissionDefinition(
        SCHOLARSHIPS_READ, "finance", "View student scholarships, discounts and concessions"
    ),
    PermissionDefinition(
        SCHOLARSHIPS_CREATE, "finance", "Apply scholarship or fee waiver to student"
    ),
    PermissionDefinition(
        SCHOLARSHIPS_APPROVE, "finance", "Approve or reject student scholarship grants"
    ),
    PermissionDefinition(ADJUSTMENTS_CREATE, "finance", "Create debit/credit adjustment requests"),
    PermissionDefinition(
        ADJUSTMENTS_APPROVE, "finance", "Approve financial adjustments on invoices"
    ),
    PermissionDefinition(REFUNDS_CREATE, "finance", "Request fee refund for paid transactions"),
    PermissionDefinition(REFUNDS_APPROVE, "finance", "Authorize fee refund disbursements"),
    PermissionDefinition(REFUNDS_PROCESS, "finance", "Process and disburse approved refunds"),
    # Placement
    PermissionDefinition(
        PLACEMENT_COMPANIES_READ, "placement", "View recruiting companies directory"
    ),
    PermissionDefinition(
        PLACEMENT_COMPANIES_MANAGE, "placement", "Manage recruiting directory and contacts"
    ),
    PermissionDefinition(PLACEMENT_DRIVES_READ, "placement", "View campus placement drives"),
    PermissionDefinition(PLACEMENT_DRIVES_MANAGE, "placement", "Schedule and manage job drives"),
    PermissionDefinition(
        PLACEMENT_POSITIONS_MANAGE,
        "placement",
        "Create and manage job positions and eligibility rules",
    ),
    PermissionDefinition(
        PLACEMENT_ELIGIBILITY_EVALUATE,
        "placement",
        "Run automated eligibility evaluations for students",
    ),
    PermissionDefinition(PLACEMENT_APPLY_SELF, "placement", "Apply for placement positions"),
    PermissionDefinition(PLACEMENT_APPLICATIONS_READ, "placement", "View placement applications"),
    PermissionDefinition(
        PLACEMENT_APPLICATIONS_REVIEW, "placement", "Review and shortlist applicant applications"
    ),
    PermissionDefinition(
        PLACEMENT_INTERVIEWS_MANAGE, "placement", "Schedule interview rounds and slots"
    ),
    PermissionDefinition(
        PLACEMENT_INTERVIEWS_EVALUATE, "placement", "Submit interview evaluations and ratings"
    ),
    PermissionDefinition(PLACEMENT_OFFERS_READ, "placement", "View extended placement offers"),
    PermissionDefinition(PLACEMENT_OFFERS_MANAGE, "placement", "Log and issue job offers"),
    PermissionDefinition(
        PLACEMENT_OFFERS_RESPOND, "placement", "Accept or decline personal placement offers"
    ),
    PermissionDefinition(
        PLACEMENT_OUTCOMES_MANAGE, "placement", "Record institutional placement outcomes"
    ),
    PermissionDefinition(
        PLACEMENT_ANALYTICS_READ, "placement", "Access placement statistics and CTC analytics"
    ),
    PermissionDefinition(PLACEMENT_PROFILE_READ, "placement", "View student placement profile"),
    PermissionDefinition(
        PLACEMENT_PROFILE_UPDATE, "placement", "Update student placement profile and resume"
    ),
    # Logistics & Audit
    PermissionDefinition(CAMPUS_EVENTS_MANAGE, "campus", "Create and govern campus events"),
    PermissionDefinition(CAMPUS_ANNOUNCEMENTS_MANAGE, "campus", "Broadcast campus announcements"),
    PermissionDefinition(INFRASTRUCTURE_HOSTEL_MANAGE, "infra", "Manage hostel allocations"),
    PermissionDefinition(INFRASTRUCTURE_TRANSPORT_MANAGE, "infra", "Manage transport routes"),
    PermissionDefinition(DOCUMENTS_MANAGE, "documents", "Verify and issue official documents"),
    PermissionDefinition(AUDIT_LOGS_READ, "audit", "Inspect immutable system audit logs"),
    # Campus Events
    PermissionDefinition(EVENTS_READ, "events", "View campus events, categories, and venues"),
    PermissionDefinition(EVENTS_CREATE, "events", "Create and schedule campus events"),
    PermissionDefinition(EVENTS_UPDATE, "events", "Update event details and capacity"),
    PermissionDefinition(EVENTS_PUBLISH, "events", "Publish events and open registrations"),
    PermissionDefinition(EVENTS_CANCEL, "events", "Cancel or archive campus events"),
    PermissionDefinition(
        EVENTS_MANAGE_ATTENDANCE, "events", "Record and supervise event check-in and attendance"
    ),
    PermissionDefinition(
        EVENTS_MANAGE_REGISTRATIONS, "events", "Manage and review event participant registrations"
    ),
    PermissionDefinition(EVENTS_SELF_REGISTER, "events", "Register self for open campus events"),
    PermissionDefinition(
        EVENTS_SELF_MANAGE_REGISTRATION, "events", "View and cancel personal event registrations"
    ),
    # Campus Clubs
    PermissionDefinition(CLUBS_READ, "clubs", "View campus student clubs and organizations"),
    PermissionDefinition(CLUBS_CREATE, "clubs", "Found or propose new student clubs"),
    PermissionDefinition(CLUBS_UPDATE, "clubs", "Update club information and metadata"),
    PermissionDefinition(CLUBS_APPROVE, "clubs", "Approve proposed student clubs"),
    PermissionDefinition(
        CLUBS_MANAGE_MEMBERSHIPS, "clubs", "Review and manage club membership rosters and roles"
    ),
    PermissionDefinition(CLUBS_SELF_READ, "clubs", "View club directory and activities"),
    PermissionDefinition(
        CLUBS_SELF_REQUEST_MEMBERSHIP, "clubs", "Submit membership requests to student clubs"
    ),
    PermissionDefinition(
        CLUBS_SELF_MANAGE_MEMBERSHIP, "clubs", "Manage personal club membership and resignation"
    ),
    # Campus Announcements
    PermissionDefinition(
        ANNOUNCEMENTS_READ, "announcements", "Read institutional and targeted announcements"
    ),
    PermissionDefinition(
        ANNOUNCEMENTS_CREATE, "announcements", "Draft and author campus announcements"
    ),
    PermissionDefinition(
        ANNOUNCEMENTS_UPDATE, "announcements", "Update draft and scheduled announcements"
    ),
    PermissionDefinition(
        ANNOUNCEMENTS_PUBLISH, "announcements", "Broadcast announcements to target audiences"
    ),
    PermissionDefinition(
        ANNOUNCEMENTS_ARCHIVE, "announcements", "Archive or expire outdated announcements"
    ),
    # Notifications
    PermissionDefinition(
        NOTIFICATIONS_READ, "notifications", "Read system and institutional notifications"
    ),
    PermissionDefinition(
        NOTIFICATIONS_MANAGE,
        "notifications",
        "Administer notification delivery channels and dispatch",
    ),
    PermissionDefinition(
        NOTIFICATIONS_MANAGE_PREFERENCES,
        "notifications",
        "Manage user notification channel preferences",
    ),
    PermissionDefinition(
        NOTIFICATIONS_SELF_READ, "notifications", "Read personal notification inbox"
    ),
    PermissionDefinition(
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        "notifications",
        "Configure personal notification preferences",
    ),
    # Documents & Digital Records
    PermissionDefinition(DOCUMENTS_READ, "documents", "View and access permitted documents"),
    PermissionDefinition(DOCUMENTS_CREATE, "documents", "Upload and submit digital documents"),
    PermissionDefinition(DOCUMENTS_UPDATE, "documents", "Update document metadata and attributes"),
    PermissionDefinition(
        DOCUMENTS_VERIFY, "documents", "Verify and authenticate submitted documents"
    ),
    PermissionDefinition(
        DOCUMENTS_REJECT, "documents", "Reject non-compliant document submissions"
    ),
    PermissionDefinition(
        DOCUMENTS_ARCHIVE, "documents", "Archive historical or outdated documents"
    ),
    PermissionDefinition(
        DOCUMENTS_DELETE, "documents", "Delete or soft-delete permitted documents"
    ),
    PermissionDefinition(DOCUMENT_CATEGORIES_READ, "documents", "View document categories"),
    PermissionDefinition(
        DOCUMENT_CATEGORIES_MANAGE, "documents", "Configure institutional document categories"
    ),
    PermissionDefinition(DOCUMENT_REQUIREMENTS_READ, "documents", "View document requirements"),
    PermissionDefinition(
        DOCUMENT_REQUIREMENTS_MANAGE, "documents", "Configure program/dept document requirements"
    ),
    PermissionDefinition(
        CERTIFICATE_TEMPLATES_READ, "documents", "View certificate layout templates"
    ),
    PermissionDefinition(
        CERTIFICATE_TEMPLATES_MANAGE, "documents", "Author and manage certificate templates"
    ),
    PermissionDefinition(
        CERTIFICATE_REQUESTS_CREATE, "documents", "Apply for institutional certificates"
    ),
    PermissionDefinition(CERTIFICATE_REQUESTS_READ, "documents", "View certificate requests"),
    PermissionDefinition(
        CERTIFICATE_REQUESTS_REVIEW, "documents", "Review pending certificate applications"
    ),
    PermissionDefinition(
        CERTIFICATE_REQUESTS_APPROVE, "documents", "Approve validated certificate requests"
    ),
    PermissionDefinition(
        CERTIFICATE_REQUESTS_ISSUE, "documents", "Issue and digitally sign certificates"
    ),
    PermissionDefinition(CERTIFICATE_REQUESTS_REVOKE, "documents", "Revoke issued certificates"),
    PermissionDefinition(
        CERTIFICATE_REQUESTS_CANCEL, "documents", "Cancel pending certificate applications"
    ),
    PermissionDefinition(CERTIFICATES_READ, "documents", "View issued certificates"),
    PermissionDefinition(
        CERTIFICATES_VERIFY, "documents", "Verify cryptographic certificate authenticity"
    ),
    PermissionDefinition(CERTIFICATES_REVOKE, "documents", "Revoke valid credentials with cause"),
    PermissionDefinition(
        INSTITUTIONAL_RECORDS_READ, "documents", "Read institutional governance records"
    ),
    PermissionDefinition(
        INSTITUTIONAL_RECORDS_MANAGE,
        "documents",
        "Manage institutional policies, accreditations, circulars",
    ),
    # Intelligence & AI
    PermissionDefinition(
        INTELLIGENCE_READ, "intelligence", "Access institutional intelligence module"
    ),
    PermissionDefinition(
        INTELLIGENCE_QUERY, "intelligence", "Submit natural language queries to AI orchestrator"
    ),
    PermissionDefinition(
        INTELLIGENCE_INSIGHTS_READ, "intelligence", "View automated institutional insights"
    ),
    PermissionDefinition(INTELLIGENCE_ALERTS_READ, "intelligence", "View operational risk alerts"),
    PermissionDefinition(
        INTELLIGENCE_ALERTS_MANAGE, "intelligence", "Acknowledge and resolve operational alerts"
    ),
    PermissionDefinition(
        INTELLIGENCE_ANALYTICS_READ, "intelligence", "Run structured cross-domain analytics queries"
    ),
    PermissionDefinition(
        INTELLIGENCE_SAVED_MANAGE, "intelligence", "Pin and manage saved intelligence views"
    ),
    PermissionDefinition(
        INTELLIGENCE_ACTIVITY_READ, "intelligence", "Inspect AI audit telemetry and tool activity"
    ),
    PermissionDefinition(
        INTELLIGENCE_TOOLS_READ, "intelligence", "Inspect registered AI tool capabilities"
    ),
    PermissionDefinition(
        INTELLIGENCE_GOVERNANCE_READ, "intelligence", "View institutional AI governance policies"
    ),
    PermissionDefinition(
        INTELLIGENCE_GOVERNANCE_MANAGE, "intelligence", "Manage AI governance policies and budgets"
    ),
    PermissionDefinition(
        INTELLIGENCE_PREDICT, "intelligence", "Request predictive risk and support indicators"
    ),
    PermissionDefinition(
        INTELLIGENCE_RECOMMEND, "intelligence", "Access and action AI-assisted recommendations"
    ),
    PermissionDefinition(
        INTELLIGENCE_EVALUATE, "intelligence", "Run and inspect automated AI evaluation suites"
    ),

    # Workflows & Automation
    PermissionDefinition(WORKFLOWS_READ, "workflows", "View institutional workflows"),
    PermissionDefinition(WORKFLOWS_CREATE, "workflows", "Create new workflow definitions"),
    PermissionDefinition(WORKFLOWS_UPDATE, "workflows", "Modify workflow configurations"),
    PermissionDefinition(WORKFLOWS_ACTIVATE, "workflows", "Activate and publish workflows"),
    PermissionDefinition(WORKFLOWS_PAUSE, "workflows", "Pause active workflow runs"),
    PermissionDefinition(WORKFLOWS_ARCHIVE, "workflows", "Archive workflow definitions"),
    PermissionDefinition(WORKFLOWS_EXECUTE, "workflows", "Manually trigger workflow executions"),
    PermissionDefinition(WORKFLOWS_RETRY, "workflows", "Retry failed workflow executions"),
    PermissionDefinition(WORKFLOWS_CANCEL, "workflows", "Cancel active workflow executions"),
    PermissionDefinition(WORKFLOW_EXECUTIONS_READ, "workflows", "View execution history and logs"),
    PermissionDefinition(
        WORKFLOW_ACTIONS_MANAGE, "workflows", "Configure workflow actions and integrations"
    ),
    # Reporting & Analytics
    PermissionDefinition(REPORTS_READ, "reporting", "View institutional reports and definitions"),
    PermissionDefinition(REPORTS_CREATE, "reporting", "Create new report definitions"),
    PermissionDefinition(REPORTS_UPDATE, "reporting", "Modify report specifications"),
    PermissionDefinition(REPORTS_EXECUTE, "reporting", "Execute reports and generate datasets"),
    PermissionDefinition(REPORTS_EXPORT, "reporting", "Export reports to CSV/XLSX/PDF"),
    PermissionDefinition(REPORTS_SCHEDULE, "reporting", "Schedule recurring report delivery"),
    PermissionDefinition(REPORTS_SHARE, "reporting", "Share saved reports across roles"),
    PermissionDefinition(REPORTS_DELETE, "reporting", "Archive or delete reports"),
    PermissionDefinition(ANALYTICS_READ, "analytics", "Access institutional analytics metrics"),
    PermissionDefinition(ANALYTICS_QUERY, "analytics", "Run ad-hoc aggregated analytics queries"),
    PermissionDefinition(ANALYTICS_EXPORT, "analytics", "Export analytics chart and summary data"),
    PermissionDefinition(ANALYTICS_MANAGE, "analytics", "Configure and backfill analytics rollups"),
    PermissionDefinition(ANALYTICS_RECONCILE, "analytics", "Execute and inspect data quality reconciliation"),
    PermissionDefinition(ANALYTICS_BACKFILL, "analytics", "Trigger historical metric backfills"),
    # Data Governance, Privacy & Compliance
    PermissionDefinition(
        GOVERNANCE_READ, "governance", "View institutional governance policies and status"
    ),
    PermissionDefinition(
        GOVERNANCE_MANAGE, "governance", "Configure institutional governance and compliance"
    ),
    PermissionDefinition(
        GOVERNANCE_POLICIES_READ, "governance", "View governance and retention policies"
    ),
    PermissionDefinition(
        GOVERNANCE_POLICIES_MANAGE, "governance", "Create and update governance policies"
    ),
    PermissionDefinition(
        GOVERNANCE_RETENTION_READ, "governance", "Inspect retention schedules and evaluations"
    ),
    PermissionDefinition(
        GOVERNANCE_RETENTION_MANAGE, "governance", "Configure retention schedules and rules"
    ),
    PermissionDefinition(
        GOVERNANCE_RETENTION_EXECUTE, "governance", "Execute retention and archival actions"
    ),
    PermissionDefinition(
        GOVERNANCE_HOLDS_READ, "governance", "View legal and administrative holds"
    ),
    PermissionDefinition(
        GOVERNANCE_HOLDS_MANAGE, "governance", "Place and release legal/governance holds"
    ),
    PermissionDefinition(
        GOVERNANCE_PRIVACY_READ, "governance", "View privacy and data subject requests"
    ),
    PermissionDefinition(
        GOVERNANCE_PRIVACY_CREATE, "governance", "Submit privacy or data subject requests"
    ),
    PermissionDefinition(
        GOVERNANCE_PRIVACY_REVIEW, "governance", "Review and approve/reject privacy requests"
    ),
    PermissionDefinition(
        GOVERNANCE_PRIVACY_EXECUTE,
        "governance",
        "Execute privacy fulfillment, export, and deletion",
    ),
    PermissionDefinition(
        GOVERNANCE_ACCESS_REVIEWS_READ, "governance", "View access review campaigns"
    ),
    PermissionDefinition(
        GOVERNANCE_ACCESS_REVIEWS_MANAGE, "governance", "Manage and conduct access reviews"
    ),
    PermissionDefinition(
        GOVERNANCE_CLASSIFICATION_READ, "governance", "View data classification standards"
    ),
    PermissionDefinition(
        GOVERNANCE_CLASSIFICATION_MANAGE, "governance", "Configure data classification schemes"
    ),
    PermissionDefinition(GOVERNANCE_EXPORT_APPROVE, "governance", "Approve sensitive data exports"),
    PermissionDefinition(
        GOVERNANCE_EXPORT_MANAGE, "governance", "Manage data export governance controls"
    ),
    # Enterprise Integration & Interoperability
    PermissionDefinition(
        INTEGRATIONS_READ, "integrations", "View institutional integrations and connectors"
    ),
    PermissionDefinition(INTEGRATIONS_MANAGE, "integrations", "Manage institutional integrations"),
    PermissionDefinition(
        INTEGRATIONS_CONNECTORS_READ, "integrations", "View connector configurations"
    ),
    PermissionDefinition(
        INTEGRATIONS_CONNECTORS_MANAGE, "integrations", "Create and modify external connectors"
    ),
    PermissionDefinition(
        INTEGRATIONS_CONNECTORS_TEST, "integrations", "Execute test probes on external connectors"
    ),
    PermissionDefinition(
        INTEGRATIONS_WEBHOOKS_READ, "integrations", "View webhook subscriptions and deliveries"
    ),
    PermissionDefinition(
        INTEGRATIONS_WEBHOOKS_MANAGE, "integrations", "Create and modify webhook subscriptions"
    ),
    PermissionDefinition(
        INTEGRATIONS_SYNC_READ, "integrations", "View sync configurations and run history"
    ),
    PermissionDefinition(
        INTEGRATIONS_SYNC_MANAGE, "integrations", "Configure data synchronization specifications"
    ),
    PermissionDefinition(
        INTEGRATIONS_SYNC_EXECUTE, "integrations", "Trigger data synchronization runs"
    ),
    PermissionDefinition(
        INTEGRATIONS_LOGS_READ, "integrations", "Inspect integration telemetry logs"
    ),
    PermissionDefinition(
        INTEGRATIONS_HEALTH_READ, "integrations", "View integration health status"
    ),
    PermissionDefinition(
        INTEGRATIONS_CREDENTIALS_MANAGE, "integrations", "Manage encrypted integration credentials"
    ),
    PermissionDefinition(
        INTEGRATIONS_DELIVERIES_RETRY, "integrations", "Retry failed webhook deliveries"
    ),
    # Enterprise API Platform & Developer Portal
    PermissionDefinition(
        API_PLATFORM_READ, "api_platform", "Inspect platform API registry and gateway metrics"
    ),
    PermissionDefinition(
        API_PLATFORM_MANAGE, "api_platform", "Manage platform API gateways and configuration"
    ),
    PermissionDefinition(
        API_APPLICATIONS_CREATE, "api_platform", "Register new developer applications"
    ),
    PermissionDefinition(API_APPLICATIONS_READ, "api_platform", "View developer applications"),
    PermissionDefinition(
        API_APPLICATIONS_MANAGE, "api_platform", "Update or archive developer applications"
    ),
    PermissionDefinition(
        API_APPLICATIONS_APPROVE, "api_platform", "Review and approve developer applications"
    ),
    PermissionDefinition(API_CREDENTIALS_CREATE, "api_platform", "Issue API keys and credentials"),
    PermissionDefinition(API_CREDENTIALS_ROTATE, "api_platform", "Trigger credential rotation"),
    PermissionDefinition(API_CREDENTIALS_REVOKE, "api_platform", "Revoke API credentials"),
    PermissionDefinition(
        API_SCOPES_MANAGE, "api_platform", "Manage application capability scope grants"
    ),
    PermissionDefinition(
        API_CATALOG_READ, "api_platform", "View API product catalog and operations"
    ),
    PermissionDefinition(
        API_CATALOG_MANAGE, "api_platform", "Publish and deprecate API catalog items"
    ),
    PermissionDefinition(
        API_ANALYTICS_READ, "api_platform", "Access API usage telemetry and quota analytics"
    ),
    # Enterprise Identity, SSO, Session & Access Federation (Step 22)
    PermissionDefinition(
        IDENTITY_READ, "identity", "View institutional identity and federation settings"
    ),
    PermissionDefinition(IDENTITY_MANAGE, "identity", "Manage identity configuration and security"),
    PermissionDefinition(
        IDENTITY_PROVIDERS_READ, "identity", "View identity provider integrations"
    ),
    PermissionDefinition(
        IDENTITY_PROVIDERS_MANAGE, "identity", "Configure and update identity providers"
    ),
    PermissionDefinition(
        IDENTITY_PROVIDERS_TEST, "identity", "Test identity provider connectivity"
    ),
    PermissionDefinition(
        IDENTITY_SESSIONS_READ, "identity", "View user sessions and device activity"
    ),
    PermissionDefinition(IDENTITY_SESSIONS_REVOKE, "identity", "Revoke user sessions"),
    PermissionDefinition(IDENTITY_EXTERNAL_LINKS_READ, "identity", "View federated account links"),
    PermissionDefinition(
        IDENTITY_EXTERNAL_LINKS_MANAGE, "identity", "Manage federated account linking"
    ),
    PermissionDefinition(IDENTITY_MFA_MANAGE, "identity", "Configure multi-factor authentication"),
    PermissionDefinition(
        IDENTITY_POLICIES_READ, "identity", "View tenant identity and security policies"
    ),
    PermissionDefinition(
        IDENTITY_POLICIES_MANAGE, "identity", "Update tenant identity and security policies"
    ),
    PermissionDefinition(
        IDENTITY_SECURITY_EVENTS_READ, "identity", "Inspect authentication and security events"
    ),
    # Enterprise Administration, Configuration & Policy Management (Step 23)
    PermissionDefinition(
        CONFIGURATION_READ, "configuration", "View system and tenant configuration parameters"
    ),
    PermissionDefinition(
        CONFIGURATION_CREATE, "configuration", "Define new configuration parameters"
    ),
    PermissionDefinition(
        CONFIGURATION_UPDATE, "configuration", "Modify configuration values and overrides"
    ),
    PermissionDefinition(CONFIGURATION_DELETE, "configuration", "Remove configuration overrides"),
    PermissionDefinition(
        CONFIGURATION_APPROVE, "configuration", "Approve pending configuration changes"
    ),
    PermissionDefinition(
        CONFIGURATION_ROLLBACK, "configuration", "Rollback configuration to historical version"
    ),
    PermissionDefinition(
        CONFIGURATION_PREVIEW, "configuration", "Preview effective configuration and impact"
    ),
    PermissionDefinition(POLICY_READ, "configuration", "View business policies and rules"),
    PermissionDefinition(POLICY_MANAGE, "configuration", "Create and update business policies"),
    PermissionDefinition(FEATURE_FLAG_READ, "configuration", "Inspect tenant feature flags"),
    PermissionDefinition(FEATURE_FLAG_MANAGE, "configuration", "Toggle and manage feature flags"),
    PermissionDefinition(
        MODULE_READ, "configuration", "View module enablement and maintenance status"
    ),
    PermissionDefinition(
        MODULE_MANAGE, "configuration", "Enable, disable or set maintenance mode for modules"
    ),
    PermissionDefinition(SEQUENCE_READ, "configuration", "View numbering sequences and formats"),
    PermissionDefinition(
        SEQUENCE_MANAGE, "configuration", "Configure numbering sequences and reset rules"
    ),
    # Enterprise Master Data Management & Data Quality (Step 24)
    PermissionDefinition(
        MASTER_DATA_READ, "master_data", "View governed master data records and lineage"
    ),
    PermissionDefinition(
        MASTER_DATA_VALIDATE, "master_data", "Evaluate data quality rules against master records"
    ),
    PermissionDefinition(
        MASTER_DATA_CORRECT, "master_data", "Propose and review master data correction requests"
    ),
    PermissionDefinition(
        MASTER_DATA_MERGE, "master_data", "Execute controlled master data duplicate merges"
    ),
    PermissionDefinition(
        MASTER_DATA_APPROVE, "master_data", "Approve master data merges and critical corrections"
    ),
    PermissionDefinition(
        MASTER_DATA_REFERENCE_MANAGE, "master_data", "Manage controlled reference data values"
    ),
    PermissionDefinition(
        MASTER_DATA_QUALITY_MANAGE,
        "master_data",
        "Manage quality rules, weights and issue stewardship",
    ),
    PermissionDefinition(
        MASTER_DATA_DEFINITION_MANAGE,
        "master_data",
        "Configure master data entity governance definitions",
    ),
    # Enterprise Case Management & HITL Operations (Step 25)
    PermissionDefinition(CASES_READ, "cases", "View operational cases and timelines"),
    PermissionDefinition(CASES_CREATE, "cases", "Create new operational cases"),
    PermissionDefinition(CASES_UPDATE, "cases", "Update operational case details and priorities"),
    PermissionDefinition(CASES_RESOLVE, "cases", "Resolve operational cases"),
    PermissionDefinition(CASES_CLOSE, "cases", "Close operational cases"),
    PermissionDefinition(CASES_REOPEN, "cases", "Reopen resolved or closed cases"),
    PermissionDefinition(CASES_ASSIGN, "cases", "Assign and route cases to queues or owners"),
    PermissionDefinition(CASES_COMMENT, "cases", "Post operational notes and comments on cases"),
    PermissionDefinition(TASKS_READ, "tasks", "View human operational tasks and queues"),
    PermissionDefinition(TASKS_CLAIM, "tasks", "Claim available human tasks from work queues"),
    PermissionDefinition(TASKS_RELEASE, "tasks", "Release claimed human tasks back to queues"),
    PermissionDefinition(TASKS_COMPLETE, "tasks", "Complete human tasks and record explicit decisions"),
    PermissionDefinition(TASKS_REASSIGN, "tasks", "Reassign human tasks to other operators"),
    PermissionDefinition(TASKS_DELEGATE, "tasks", "Delegate human task authority temporarily"),
    PermissionDefinition(TASKS_ESCALATE, "tasks", "Escalate overdue or blocked human tasks"),
    PermissionDefinition(QUEUES_READ, "queues", "View operational work queues and memberships"),
    PermissionDefinition(QUEUES_MANAGE, "queues", "Configure operational work queues and routing"),
    PermissionDefinition(SLA_POLICIES_READ, "sla_policies", "View operational SLA policies and targets"),
    PermissionDefinition(SLA_POLICIES_MANAGE, "sla_policies", "Configure operational SLA policies and escalation"),
    PermissionDefinition(WORKFLOWS_TRANSITION, "workflows", "Execute manual or HITL workflow state transitions"),
    # Notifications (Step 26)
    PermissionDefinition(NOTIFICATION_TEMPLATES_READ, "notifications", "View notification templates and schemas"),
    PermissionDefinition(NOTIFICATION_TEMPLATES_MANAGE, "notifications", "Author and publish notification templates"),
    PermissionDefinition(NOTIFICATION_RULES_MANAGE, "notifications", "Configure notification dispatch rules and policies"),
    PermissionDefinition(NOTIFICATION_DELIVERIES_READ, "notifications", "View delivery logs, attempts, and status"),
    PermissionDefinition(NOTIFICATION_DELIVERIES_RETRY, "notifications", "Trigger manual retries of failed deliveries"),
    PermissionDefinition(NOTIFICATION_DELIVERIES_CANCEL, "notifications", "Cancel pending and scheduled deliveries"),
    PermissionDefinition(NOTIFICATION_ANALYTICS_READ, "notifications", "View delivery analytics, throughput, and success rates"),
    PermissionDefinition(NOTIFICATION_PROVIDERS_MANAGE, "notifications", "Manage notification providers and check channel health"),
    # Domain Events & Reliability Backbone (Step 27)
    PermissionDefinition(DOMAIN_EVENTS_READ, "events", "View transactional outbox events and payloads"),
    PermissionDefinition(DOMAIN_EVENTS_RETRY, "events", "Trigger manual retries of failed outbox events"),
    PermissionDefinition(DOMAIN_EVENTS_REPLAY, "events", "Execute audited replay of domain events to consumers"),
    PermissionDefinition(DOMAIN_EVENTS_CONSUMERS_MANAGE, "events", "Manage and inspect event consumers and checkpoints"),
    PermissionDefinition(DOMAIN_EVENTS_METRICS_READ, "events", "View event processing latency and throughput metrics"),
    # Enterprise Platform Administration & SaaS Operations (Step 30)
    PermissionDefinition(PLATFORM_TENANTS_READ, "platform", "View multi-tenant SaaS directory and tenant metadata"),
    PermissionDefinition(PLATFORM_TENANTS_MANAGE, "platform", "Provision, configure, and administer SaaS tenants"),
    PermissionDefinition(PLATFORM_LIFECYCLE_MANAGE, "platform", "Execute and govern tenant lifecycle state transitions"),
    PermissionDefinition(PLATFORM_PROVISION_MANAGE, "platform", "Coordinate and retry automated institution onboarding"),
    PermissionDefinition(PLATFORM_ENTITLEMENTS_MANAGE, "platform", "Manage subscription plans and feature entitlements"),
    PermissionDefinition(PLATFORM_QUOTAS_MANAGE, "platform", "Configure and govern tenant resource limits and quotas"),
    PermissionDefinition(PLATFORM_SUPPORT_ACCESS, "platform", "Request, access, and revoke scoped institution support sessions"),
    PermissionDefinition(PLATFORM_DELETION_MANAGE, "platform", "Evaluate deletion eligibility and schedule tenant decommissioning"),
    PermissionDefinition(PLATFORM_OPS_HEALTH_READ, "platform", "Access internal platform infrastructure health and operational telemetry"),
    # Enterprise Reliability Engineering & Disaster Recovery (Step 31)
    PermissionDefinition(PLATFORM_RELIABILITY_READ, "platform", "View disaster recovery posture, backups, and resilience telemetry"),
    PermissionDefinition(PLATFORM_RELIABILITY_MANAGE, "platform", "Administer platform resilience policies and circuit breakers"),
    PermissionDefinition(PLATFORM_BACKUP_TRIGGER, "platform", "Trigger and prune cryptographic database backups"),
    PermissionDefinition(PLATFORM_RESTORE_VERIFY, "platform", "Execute automated restore verification in isolated sandboxes"),
    # Enterprise Security Operations, Threat Detection & Incident Response (Step 33)
    PermissionDefinition(SECURITY_INCIDENTS_READ, "security", "View security incidents and detections"),
    PermissionDefinition(SECURITY_INCIDENTS_MANAGE, "security", "Triage, assign, and manage security incidents"),
    PermissionDefinition(SECURITY_ACTIONS_PROPOSE, "security", "Propose automated or manual containment actions"),
    PermissionDefinition(SECURITY_ACTIONS_APPROVE, "security", "Approve high-impact containment and response actions"),
    PermissionDefinition(SECURITY_ACTIONS_EXECUTE, "security", "Execute authorized containment and response actions"),
    PermissionDefinition(SECURITY_RULES_MANAGE, "security", "Configure threat detection rules, thresholds, and exclusions"),
    PermissionDefinition(SECURITY_PLATFORM_READ, "security", "View platform-wide and cross-tenant security operations telemetry"),
    # Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management (Step 41)
    PermissionDefinition(RECORDS_READ, "records", "View registered institutional records and retention state"),
    PermissionDefinition(RECORDS_CREATE, "records", "Index and register domain records into lifecycle engine"),
    PermissionDefinition(RECORDS_MANAGE, "records", "Manage record lifecycle states and transitions"),
    PermissionDefinition(RECORDS_POLICY_MANAGE, "records", "Author and configure institutional retention schedules"),
    PermissionDefinition(RECORDS_POLICY_PUBLISH, "records", "Publish and activate versioned retention policies"),
    PermissionDefinition(RECORDS_ARCHIVE_EXECUTE, "records", "Execute cold storage archival with cryptographic manifests"),
    PermissionDefinition(RECORDS_ARCHIVE_RETRIEVE, "records", "Retrieve and audit archived record content"),
    PermissionDefinition(RECORDS_HOLD_CREATE, "records", "Place administrative and legal holds on records"),
    PermissionDefinition(RECORDS_HOLD_MANAGE, "records", "Manage legal holds and custodian rosters"),
    PermissionDefinition(RECORDS_HOLD_RELEASE, "records", "Release active legal holds and trigger eligibility re-evaluation"),
    PermissionDefinition(RECORDS_DISPOSITION_REQUEST, "records", "Request and preview record disposition batches"),
    PermissionDefinition(RECORDS_DISPOSITION_APPROVE, "records", "Formally authorize record disposition execution"),
    PermissionDefinition(RECORDS_DISPOSITION_EXECUTE, "records", "Execute approved disposition and issue certificates"),
    # Institutional Knowledge Base (Step 42)
    PermissionDefinition(KNOWLEDGE_READ, "knowledge", "Search and view published institutional policies and knowledge"),
    PermissionDefinition(KNOWLEDGE_CREATE, "knowledge", "Author draft institutional knowledge items and SOPs"),
    PermissionDefinition(KNOWLEDGE_MANAGE, "knowledge", "Manage knowledge categories, scopes, and lifecycle settings"),
    PermissionDefinition(KNOWLEDGE_REVIEW, "knowledge", "Review knowledge drafts and provide editorial feedback"),
    PermissionDefinition(KNOWLEDGE_APPROVE, "knowledge", "Approve knowledge items for publication"),
    PermissionDefinition(KNOWLEDGE_PUBLISH, "knowledge", "Publish or schedule institutional policies and handbooks"),
    PermissionDefinition(KNOWLEDGE_RETIRE, "knowledge", "Retire or supersede obsolete knowledge items"),
    PermissionDefinition(KNOWLEDGE_ACKNOWLEDGE, "knowledge", "Acknowledge and submit policy attestations"),
    PermissionDefinition(KNOWLEDGE_ATTESTATION_READ, "knowledge", "View institutional policy attestation compliance reports"),
    # Institutional Accreditation & Quality Assurance (Step 43)
    PermissionDefinition(ACCREDITATION_READ, "accreditation", "View accreditation frameworks, criteria, assessments, and readiness reports"),
    PermissionDefinition(ACCREDITATION_FRAMEWORK_MANAGE, "accreditation", "Configure accreditation frameworks, cycles, and version snapshots"),
    PermissionDefinition(ACCREDITATION_CRITERIA_MANAGE, "accreditation", "Manage framework criteria, subcriteria, weights, and guidelines"),
    PermissionDefinition(ACCREDITATION_ASSESS, "accreditation", "Draft and submit criterion assessments and scores"),
    PermissionDefinition(ACCREDITATION_APPROVE, "accreditation", "Conduct independent review and approval of assessments"),
    PermissionDefinition(ACCREDITATION_EVIDENCE_MANAGE, "accreditation", "Attach, categorize, and manage supporting evidence links"),
    PermissionDefinition(ACCREDITATION_EVIDENCE_VERIFY, "accreditation", "Verify evidence validity, integrity, and compliance"),
    PermissionDefinition(ACCREDITATION_INDICATOR_MANAGE, "accreditation", "Configure quality indicators, benchmarks, and data sources"),
    PermissionDefinition(ACCREDITATION_AUDIT_MANAGE, "accreditation", "Plan, schedule, execute, and finalize internal quality audits"),
    PermissionDefinition(ACCREDITATION_CAPA_MANAGE, "accreditation", "Manage findings, corrective actions (CAPA), and verify closure"),
    PermissionDefinition(ACCREDITATION_IMPROVEMENT_MANAGE, "accreditation", "Define and monitor continuous quality improvement (CQI) plans"),
    PermissionDefinition(ACCREDITATION_REPORT_EXPORT, "accreditation", "Generate and export authorized accreditation compliance reports"),
    # Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management (Step 44)
    PermissionDefinition(RESEARCH_PROJECTS_READ, "research", "View research projects, teams, milestones, and registry"),
    PermissionDefinition(RESEARCH_PROJECTS_MANAGE, "research", "Create and manage research projects and memberships"),
    PermissionDefinition(RESEARCH_PROJECTS_TRANSITION, "research", "Authorize lifecycle status transitions for research projects"),
    PermissionDefinition(RESEARCH_GRANTS_APPLY, "research", "Draft and submit research grant applications"),
    PermissionDefinition(RESEARCH_GRANTS_APPROVE, "research", "Conduct internal institutional review and approve grant applications"),
    PermissionDefinition(RESEARCH_AWARDS_MANAGE, "research", "Register grant awards and disbursements"),
    PermissionDefinition(RESEARCH_BUDGETS_MANAGE, "research", "Manage project budget categories, revisions, and expenditure monitoring"),
    PermissionDefinition(RESEARCH_ETHICS_REVIEW, "research", "Review and decide on research ethics, biosafety, and compliance requests"),
    PermissionDefinition(RESEARCH_OUTPUTS_MANAGE, "research", "Register publications, datasets, and intellectual outputs"),
    PermissionDefinition(RESEARCH_OUTPUTS_VERIFY, "research", "Verify academic outputs and external citation metadata"),
    PermissionDefinition(RESEARCH_IP_MANAGE, "research", "Manage intellectual property, invention disclosures, and patent milestones"),
    PermissionDefinition(RESEARCH_IP_CONFIDENTIAL_READ, "research", "Access confidential IP disclosures and trade secret records"),
    PermissionDefinition(RESEARCH_ANALYTICS_READ, "research", "Access institutional research analytics, reports, and performance trends"),
    # Enterprise Institutional Library, Learning Resources & Knowledge Access Management (Step 45)
    PermissionDefinition(LIBRARY_BRANCHES_READ, "library", "View institutional library branches, hours, and policies"),
    PermissionDefinition(LIBRARY_BRANCHES_MANAGE, "library", "Manage library branches, locations, and schedules"),
    PermissionDefinition(LIBRARY_CATALOG_READ, "library", "Search and browse bibliographic catalog items"),
    PermissionDefinition(LIBRARY_CATALOG_MANAGE, "library", "Create, update, and withdraw catalog records"),
    PermissionDefinition(LIBRARY_COPIES_MANAGE, "library", "Manage physical inventory copies, barcodes, and shelf locations"),
    PermissionDefinition(LIBRARY_MEMBERS_READ, "library", "View library patron membership profiles and borrowing history"),
    PermissionDefinition(LIBRARY_MEMBERS_MANAGE, "library", "Manage library memberships, privileges, and suspensions"),
    PermissionDefinition(LIBRARY_CIRCULATION_ISSUE, "library", "Issue and checkout library materials to members"),
    PermissionDefinition(LIBRARY_CIRCULATION_RETURN, "library", "Process check-in and return of borrowed resources"),
    PermissionDefinition(LIBRARY_CIRCULATION_RENEW, "library", "Process loan renewals and due date extensions"),
    PermissionDefinition(LIBRARY_RESERVATIONS_MANAGE, "library", "Place, manage, and allocate resource hold reservations"),
    PermissionDefinition(LIBRARY_FINES_MANAGE, "library", "Assess, review, and post overdue and damage fines to finance"),
    PermissionDefinition(LIBRARY_FINES_WAIVE, "library", "Authorize waivers and adjustments for assessed library fines"),
    PermissionDefinition(LIBRARY_ACQUISITIONS_REQUEST, "library", "Submit resource recommendation and acquisition requests"),
    PermissionDefinition(LIBRARY_ACQUISITIONS_MANAGE, "library", "Approve purchase requests, track orders, and accession copies"),
    PermissionDefinition(LIBRARY_SUBSCRIPTIONS_MANAGE, "library", "Manage periodicals, serials, and database subscriptions"),
    PermissionDefinition(LIBRARY_DIGITAL_ACCESS, "library", "Access and download electronic resources and institutional documents"),
    PermissionDefinition(LIBRARY_AUDIT_MANAGE, "library", "Conduct physical inventory verification and reconcile stock discrepancies"),
    PermissionDefinition(LIBRARY_ANALYTICS_READ, "library", "View library circulation metrics, popular items, and collection reports"),
    # Student Success, Academic Advising, Early-Warning & Intervention Management (Step 47)
    PermissionDefinition(STUDENT_SUCCESS_CASE_READ, "student_success", "View student-success cases, history, and notes"),
    PermissionDefinition(STUDENT_SUCCESS_CASE_MANAGE, "student_success", "Create, update, assign, escalate, and close success cases"),
    PermissionDefinition(STUDENT_SUCCESS_ADVISING_READ, "student_success", "View advisor profiles, assignments, and advising plans"),
    PermissionDefinition(STUDENT_SUCCESS_ADVISING_MANAGE, "student_success", "Manage advisor assignments, plans, and caseload capacities"),
    PermissionDefinition(STUDENT_SUCCESS_EARLY_WARNING_READ, "student_success", "View early-warning rules, evaluations, and risk signals"),
    PermissionDefinition(STUDENT_SUCCESS_EARLY_WARNING_MANAGE, "student_success", "Configure rules, execute evaluations, and triage signals"),
    PermissionDefinition(STUDENT_SUCCESS_INTERVENTION_READ, "student_success", "View student intervention plans and progress milestones"),
    PermissionDefinition(STUDENT_SUCCESS_INTERVENTION_MANAGE, "student_success", "Create, track, update, and close intervention plans"),
    PermissionDefinition(STUDENT_SUCCESS_APPOINTMENT_MANAGE, "student_success", "Schedule, reschedule, complete, or cancel appointments"),
    PermissionDefinition(STUDENT_SUCCESS_REPORTS_READ, "student_success", "Access aggregate student-success analytics and caseload metrics"),
    PermissionDefinition(STUDENT_SUCCESS_STUDENT_SELF_READ, "student_success", "Student self-service access to permitted advising plans and appointments"),
    # Student Admissions, Enrollment & Onboarding Orchestration (Step 48)
    PermissionDefinition(ADMISSIONS_CYCLE_READ, "admissions", "View admission cycles, application deadlines, and seat capacities"),
    PermissionDefinition(ADMISSIONS_CYCLE_MANAGE, "admissions", "Configure, publish, suspend, or archive admission cycles"),
    PermissionDefinition(ADMISSIONS_APPLICANT_READ, "admissions", "View applicant profiles, contact information, and verification status"),
    PermissionDefinition(ADMISSIONS_APPLICANT_MANAGE, "admissions", "Manage applicant profiles, verification, and duplicate merging"),
    PermissionDefinition(ADMISSIONS_APPLICATION_READ, "admissions", "View admission applications, program preferences, and scores"),
    PermissionDefinition(ADMISSIONS_APPLICATION_MANAGE, "admissions", "Process applications, status transitions, withdrawals, and reopening"),
    PermissionDefinition(ADMISSIONS_DOCUMENT_VERIFY, "admissions", "Review and verify uploaded applicant evidence and certificates"),
    PermissionDefinition(ADMISSIONS_ELIGIBILITY_EVALUATE, "admissions", "Configure eligibility rules and execute evaluation checks"),
    PermissionDefinition(ADMISSIONS_REVIEW_MANAGE, "admissions", "Assign reviewers, record application review scores and decisions"),
    PermissionDefinition(ADMISSIONS_SELECTION_MANAGE, "admissions", "Generate merit lists, seat allocations, and publish selection rounds"),
    PermissionDefinition(ADMISSIONS_OFFERS_MANAGE, "admissions", "Issue, accept, decline, expire, or revoke admission offers"),
    PermissionDefinition(ADMISSIONS_ENROLLMENT_ORCHESTRATE, "admissions", "Execute idempotent enrollment and student record creation"),
    PermissionDefinition(ADMISSIONS_ONBOARDING_MANAGE, "admissions", "Coordinate post-enrollment student onboarding checklists and tasks"),
    PermissionDefinition(ADMISSIONS_REPORTS_READ, "admissions", "View admissions funnel analytics, conversion rates, and seat utilization"),
    PermissionDefinition(ADMISSIONS_APPLICANT_SELF, "admissions", "Applicant self-service portal to submit applications and view offers"),
]


# Default System Role Definitions
DEFAULT_ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "SUPER_ADMIN": [p.code for p in ALL_PERMISSIONS],
    "INSTITUTION_ADMIN": [
        ADMISSIONS_CYCLE_READ,
        ADMISSIONS_CYCLE_MANAGE,
        ADMISSIONS_APPLICANT_READ,
        ADMISSIONS_APPLICANT_MANAGE,
        ADMISSIONS_APPLICATION_READ,
        ADMISSIONS_APPLICATION_MANAGE,
        ADMISSIONS_DOCUMENT_VERIFY,
        ADMISSIONS_ELIGIBILITY_EVALUATE,
        ADMISSIONS_REVIEW_MANAGE,
        ADMISSIONS_SELECTION_MANAGE,
        ADMISSIONS_OFFERS_MANAGE,
        ADMISSIONS_ENROLLMENT_ORCHESTRATE,
        ADMISSIONS_ONBOARDING_MANAGE,
        ADMISSIONS_REPORTS_READ,

        STUDENT_SUCCESS_CASE_READ,
        STUDENT_SUCCESS_CASE_MANAGE,
        STUDENT_SUCCESS_ADVISING_READ,
        STUDENT_SUCCESS_ADVISING_MANAGE,
        STUDENT_SUCCESS_EARLY_WARNING_READ,
        STUDENT_SUCCESS_EARLY_WARNING_MANAGE,
        STUDENT_SUCCESS_INTERVENTION_READ,
        STUDENT_SUCCESS_INTERVENTION_MANAGE,
        STUDENT_SUCCESS_APPOINTMENT_MANAGE,
        STUDENT_SUCCESS_REPORTS_READ,

        LIBRARY_BRANCHES_READ,
        LIBRARY_BRANCHES_MANAGE,
        LIBRARY_CATALOG_READ,
        LIBRARY_CATALOG_MANAGE,
        LIBRARY_COPIES_MANAGE,
        LIBRARY_MEMBERS_READ,
        LIBRARY_MEMBERS_MANAGE,
        LIBRARY_CIRCULATION_ISSUE,
        LIBRARY_CIRCULATION_RETURN,
        LIBRARY_CIRCULATION_RENEW,
        LIBRARY_RESERVATIONS_MANAGE,
        LIBRARY_FINES_MANAGE,
        LIBRARY_FINES_WAIVE,
        LIBRARY_ACQUISITIONS_REQUEST,
        LIBRARY_ACQUISITIONS_MANAGE,
        LIBRARY_SUBSCRIPTIONS_MANAGE,
        LIBRARY_DIGITAL_ACCESS,
        LIBRARY_AUDIT_MANAGE,
        LIBRARY_ANALYTICS_READ,
        RESEARCH_PROJECTS_READ,
        RESEARCH_PROJECTS_MANAGE,
        RESEARCH_PROJECTS_TRANSITION,
        RESEARCH_GRANTS_APPLY,
        RESEARCH_GRANTS_APPROVE,
        RESEARCH_AWARDS_MANAGE,
        RESEARCH_BUDGETS_MANAGE,
        RESEARCH_ETHICS_REVIEW,
        RESEARCH_OUTPUTS_MANAGE,
        RESEARCH_OUTPUTS_VERIFY,
        RESEARCH_IP_MANAGE,
        RESEARCH_IP_CONFIDENTIAL_READ,
        RESEARCH_ANALYTICS_READ,
        ACCREDITATION_READ,
        ACCREDITATION_FRAMEWORK_MANAGE,
        ACCREDITATION_CRITERIA_MANAGE,
        ACCREDITATION_ASSESS,
        ACCREDITATION_APPROVE,
        ACCREDITATION_EVIDENCE_MANAGE,
        ACCREDITATION_EVIDENCE_VERIFY,
        ACCREDITATION_INDICATOR_MANAGE,
        ACCREDITATION_AUDIT_MANAGE,
        ACCREDITATION_CAPA_MANAGE,
        ACCREDITATION_IMPROVEMENT_MANAGE,
        ACCREDITATION_REPORT_EXPORT,
        KNOWLEDGE_READ,
        KNOWLEDGE_CREATE,
        KNOWLEDGE_MANAGE,
        KNOWLEDGE_REVIEW,
        KNOWLEDGE_APPROVE,
        KNOWLEDGE_PUBLISH,
        KNOWLEDGE_RETIRE,
        KNOWLEDGE_ACKNOWLEDGE,
        KNOWLEDGE_ATTESTATION_READ,
        RECORDS_READ,
        RECORDS_CREATE,
        RECORDS_MANAGE,
        RECORDS_POLICY_MANAGE,
        RECORDS_POLICY_PUBLISH,
        RECORDS_ARCHIVE_EXECUTE,
        RECORDS_ARCHIVE_RETRIEVE,
        RECORDS_HOLD_CREATE,
        RECORDS_HOLD_MANAGE,
        RECORDS_HOLD_RELEASE,
        RECORDS_DISPOSITION_REQUEST,
        RECORDS_DISPOSITION_APPROVE,
        RECORDS_DISPOSITION_EXECUTE,
        CORE_INSTITUTION_READ,
        CORE_INSTITUTION_MANAGE,
        CORE_CAMPUSES_READ,
        CORE_CAMPUSES_MANAGE,
        CORE_DEPARTMENTS_READ,
        CORE_DEPARTMENTS_MANAGE,
        CORE_PROGRAMS_READ,
        CORE_PROGRAMS_MANAGE,
        CORE_REGULATIONS_MANAGE,
        CORE_ACADEMIC_YEARS_READ,
        CORE_ACADEMIC_YEARS_MANAGE,
        CORE_SECTIONS_READ,
        CORE_SECTIONS_MANAGE,
        PEOPLE_USERS_READ,
        PEOPLE_USERS_MANAGE,
        PEOPLE_STUDENTS_READ,
        PEOPLE_STUDENTS_CREATE,
        PEOPLE_STUDENTS_UPDATE,
        PEOPLE_FACULTY_READ,
        PEOPLE_FACULTY_MANAGE,
        PEOPLE_STAFF_READ,
        PEOPLE_STAFF_MANAGE,
        PEOPLE_ROLES_MANAGE,
        ACADEMICS_SUBJECTS_READ,
        ACADEMICS_SUBJECTS_MANAGE,
        ACADEMICS_CURRICULUM_READ,
        ACADEMICS_CURRICULUM_MANAGE,
        ACADEMICS_CURRICULUM_PUBLISH,
        ACADEMICS_COURSES_READ,
        ACADEMICS_COURSES_MANAGE,
        ACADEMICS_ENROLLMENTS_READ,
        ACADEMICS_ENROLLMENTS_MANAGE,
        ACADEMICS_TIMETABLE_READ,
        ACADEMICS_TIMETABLE_MANAGE,
        ACADEMICS_ROOMS_READ,
        ACADEMICS_ROOMS_MANAGE,
        ATTENDANCE_SESSIONS_READ,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_RECORDS_WRITE,
        ATTENDANCE_CORRECTIONS_APPROVE,
        ATTENDANCE_LEAVE_APPLY,
        ATTENDANCE_LEAVE_APPROVE,
        ATTENDANCE_READ,
        ATTENDANCE_MARK,
        ATTENDANCE_UPDATE,
        ATTENDANCE_LOCK,
        ATTENDANCE_CORRECT,
        ATTENDANCE_APPROVE_CORRECTION,
        LEAVE_READ,
        LEAVE_CREATE,
        LEAVE_APPROVE,
        LEAVE_REJECT,
        ATTENDANCE_POLICY_READ,
        ATTENDANCE_POLICY_CREATE,
        ATTENDANCE_POLICY_UPDATE,
        EXAMINATIONS_READ,
        EXAMINATIONS_CREATE,
        EXAMINATIONS_UPDATE,
        ASSESSMENTS_READ,
        ASSESSMENTS_CREATE,
        ASSESSMENTS_UPDATE,
        ASSESSMENTS_FINALIZE,
        MARKS_READ,
        MARKS_ENTER,
        MARKS_UPDATE,
        MARKS_FINALIZE,
        MARKS_CORRECT,
        RESULTS_READ,
        RESULTS_FINALIZE,
        RESULTS_PUBLISH,
        GRADE_SCALES_READ,
        GRADE_SCALES_MANAGE,
        ELIGIBILITY_READ,
        ELIGIBILITY_EVALUATE,
        ELIGIBILITY_OVERRIDE,
        DOCUMENTS_MANAGE,
        CAMPUS_ANNOUNCEMENTS_MANAGE,
        AUDIT_LOGS_READ,
        FINANCE_READ,
        FINANCE_MANAGE_FEE_STRUCTURES,
        INVOICES_READ,
        INVOICES_CREATE,
        INVOICES_ISSUE,
        INVOICES_CANCEL,
        PAYMENTS_READ,
        PAYMENTS_CREATE,
        PAYMENTS_CONFIRM,
        RECEIPTS_READ,
        RECEIPTS_ISSUE,
        SCHOLARSHIPS_READ,
        SCHOLARSHIPS_CREATE,
        SCHOLARSHIPS_APPROVE,
        ADJUSTMENTS_CREATE,
        ADJUSTMENTS_APPROVE,
        REFUNDS_CREATE,
        REFUNDS_APPROVE,
        REFUNDS_PROCESS,
        EVENTS_READ,
        EVENTS_CREATE,
        EVENTS_UPDATE,
        EVENTS_PUBLISH,
        EVENTS_CANCEL,
        EVENTS_MANAGE_ATTENDANCE,
        EVENTS_MANAGE_REGISTRATIONS,
        CLUBS_READ,
        CLUBS_CREATE,
        CLUBS_UPDATE,
        CLUBS_APPROVE,
        CLUBS_MANAGE_MEMBERSHIPS,
        ANNOUNCEMENTS_READ,
        ANNOUNCEMENTS_CREATE,
        ANNOUNCEMENTS_UPDATE,
        ANNOUNCEMENTS_PUBLISH,
        ANNOUNCEMENTS_ARCHIVE,
        NOTIFICATIONS_READ,
        NOTIFICATIONS_MANAGE,
        NOTIFICATIONS_MANAGE_PREFERENCES,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        DOCUMENTS_READ,
        DOCUMENTS_CREATE,
        DOCUMENTS_UPDATE,
        DOCUMENTS_VERIFY,
        DOCUMENTS_REJECT,
        DOCUMENTS_ARCHIVE,
        DOCUMENTS_DELETE,
        DOCUMENT_CATEGORIES_READ,
        DOCUMENT_CATEGORIES_MANAGE,
        DOCUMENT_REQUIREMENTS_READ,
        DOCUMENT_REQUIREMENTS_MANAGE,
        CERTIFICATE_TEMPLATES_READ,
        CERTIFICATE_TEMPLATES_MANAGE,
        CERTIFICATE_REQUESTS_CREATE,
        CERTIFICATE_REQUESTS_READ,
        CERTIFICATE_REQUESTS_REVIEW,
        CERTIFICATE_REQUESTS_APPROVE,
        CERTIFICATE_REQUESTS_ISSUE,
        CERTIFICATE_REQUESTS_REVOKE,
        CERTIFICATE_REQUESTS_CANCEL,
        CERTIFICATES_READ,
        CERTIFICATES_VERIFY,
        CERTIFICATES_REVOKE,
        INSTITUTIONAL_RECORDS_READ,
        INSTITUTIONAL_RECORDS_MANAGE,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ALERTS_MANAGE,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        INTELLIGENCE_ACTIVITY_READ,
        INTELLIGENCE_TOOLS_READ,
        INTELLIGENCE_GOVERNANCE_READ,
        INTELLIGENCE_GOVERNANCE_MANAGE,
        INTELLIGENCE_PREDICT,
        INTELLIGENCE_RECOMMEND,
        INTELLIGENCE_EVALUATE,
        WORKFLOWS_READ,
        WORKFLOWS_CREATE,
        WORKFLOWS_UPDATE,
        WORKFLOWS_ACTIVATE,
        WORKFLOWS_PAUSE,
        WORKFLOWS_ARCHIVE,
        WORKFLOWS_EXECUTE,
        WORKFLOWS_RETRY,
        WORKFLOWS_CANCEL,
        WORKFLOW_EXECUTIONS_READ,
        WORKFLOW_ACTIONS_MANAGE,
        REPORTS_READ,
        REPORTS_CREATE,
        REPORTS_UPDATE,
        REPORTS_EXECUTE,
        REPORTS_EXPORT,
        REPORTS_SCHEDULE,
        REPORTS_SHARE,
        REPORTS_DELETE,
        ANALYTICS_READ,
        ANALYTICS_QUERY,
        ANALYTICS_EXPORT,
        ANALYTICS_MANAGE,
        ANALYTICS_RECONCILE,
        ANALYTICS_BACKFILL,
        GOVERNANCE_READ,
        GOVERNANCE_MANAGE,
        GOVERNANCE_POLICIES_READ,
        GOVERNANCE_POLICIES_MANAGE,
        GOVERNANCE_RETENTION_READ,
        GOVERNANCE_RETENTION_MANAGE,
        GOVERNANCE_RETENTION_EXECUTE,
        GOVERNANCE_HOLDS_READ,
        GOVERNANCE_HOLDS_MANAGE,
        GOVERNANCE_PRIVACY_READ,
        GOVERNANCE_PRIVACY_CREATE,
        GOVERNANCE_PRIVACY_REVIEW,
        GOVERNANCE_PRIVACY_EXECUTE,
        GOVERNANCE_ACCESS_REVIEWS_READ,
        GOVERNANCE_ACCESS_REVIEWS_MANAGE,
        GOVERNANCE_CLASSIFICATION_READ,
        GOVERNANCE_CLASSIFICATION_MANAGE,
        GOVERNANCE_EXPORT_APPROVE,
        GOVERNANCE_EXPORT_MANAGE,
        INTEGRATIONS_READ,
        INTEGRATIONS_MANAGE,
        INTEGRATIONS_CONNECTORS_READ,
        INTEGRATIONS_CONNECTORS_MANAGE,
        INTEGRATIONS_CONNECTORS_TEST,
        INTEGRATIONS_WEBHOOKS_READ,
        INTEGRATIONS_WEBHOOKS_MANAGE,
        INTEGRATIONS_SYNC_READ,
        INTEGRATIONS_SYNC_MANAGE,
        INTEGRATIONS_SYNC_EXECUTE,
        INTEGRATIONS_LOGS_READ,
        INTEGRATIONS_HEALTH_READ,
        INTEGRATIONS_CREDENTIALS_MANAGE,
        INTEGRATIONS_DELIVERIES_RETRY,
        API_PLATFORM_READ,
        API_PLATFORM_MANAGE,
        API_APPLICATIONS_CREATE,
        API_APPLICATIONS_READ,
        API_APPLICATIONS_MANAGE,
        API_APPLICATIONS_APPROVE,
        API_CREDENTIALS_CREATE,
        API_CREDENTIALS_ROTATE,
        API_CREDENTIALS_REVOKE,
        API_SCOPES_MANAGE,
        API_CATALOG_READ,
        API_CATALOG_MANAGE,
        API_ANALYTICS_READ,
        IDENTITY_READ,
        IDENTITY_MANAGE,
        IDENTITY_PROVIDERS_READ,
        IDENTITY_PROVIDERS_MANAGE,
        IDENTITY_PROVIDERS_TEST,
        IDENTITY_SESSIONS_READ,
        IDENTITY_SESSIONS_REVOKE,
        IDENTITY_EXTERNAL_LINKS_READ,
        IDENTITY_EXTERNAL_LINKS_MANAGE,
        IDENTITY_MFA_MANAGE,
        IDENTITY_POLICIES_READ,
        IDENTITY_POLICIES_MANAGE,
        IDENTITY_SECURITY_EVENTS_READ,
        CONFIGURATION_READ,
        CONFIGURATION_CREATE,
        CONFIGURATION_UPDATE,
        CONFIGURATION_DELETE,
        CONFIGURATION_APPROVE,
        CONFIGURATION_ROLLBACK,
        CONFIGURATION_PREVIEW,
        POLICY_READ,
        POLICY_MANAGE,
        FEATURE_FLAG_READ,
        FEATURE_FLAG_MANAGE,
        MODULE_READ,
        MODULE_MANAGE,
        SEQUENCE_READ,
        SEQUENCE_MANAGE,
        MASTER_DATA_READ,
        MASTER_DATA_VALIDATE,
        MASTER_DATA_CORRECT,
        MASTER_DATA_MERGE,
        MASTER_DATA_APPROVE,
        MASTER_DATA_REFERENCE_MANAGE,
        MASTER_DATA_QUALITY_MANAGE,
        MASTER_DATA_DEFINITION_MANAGE,
        CASES_READ,
        CASES_CREATE,
        CASES_UPDATE,
        CASES_RESOLVE,
        CASES_CLOSE,
        CASES_REOPEN,
        CASES_ASSIGN,
        CASES_COMMENT,
        TASKS_READ,
        TASKS_CLAIM,
        TASKS_RELEASE,
        TASKS_COMPLETE,
        TASKS_REASSIGN,
        TASKS_DELEGATE,
        TASKS_ESCALATE,
        QUEUES_READ,
        QUEUES_MANAGE,
        SLA_POLICIES_READ,
        SLA_POLICIES_MANAGE,
        WORKFLOWS_TRANSITION,
        NOTIFICATION_TEMPLATES_READ,
        NOTIFICATION_TEMPLATES_MANAGE,
        NOTIFICATION_RULES_MANAGE,
        NOTIFICATION_DELIVERIES_READ,
        NOTIFICATION_DELIVERIES_RETRY,
        NOTIFICATION_DELIVERIES_CANCEL,
        NOTIFICATION_ANALYTICS_READ,
        NOTIFICATION_PROVIDERS_MANAGE,
        DOMAIN_EVENTS_READ,
        DOMAIN_EVENTS_RETRY,
        DOMAIN_EVENTS_REPLAY,
        DOMAIN_EVENTS_CONSUMERS_MANAGE,
        DOMAIN_EVENTS_METRICS_READ,
        ANALYTICS_MANAGE,
        ANALYTICS_RECONCILE,
        ANALYTICS_BACKFILL,
        SECURITY_INCIDENTS_READ,
        SECURITY_INCIDENTS_MANAGE,
        SECURITY_ACTIONS_PROPOSE,
        SECURITY_ACTIONS_APPROVE,
        SECURITY_ACTIONS_EXECUTE,
        SECURITY_RULES_MANAGE,
    ],
    "DOCUMENT_OFFICER": [
        CORE_INSTITUTION_READ,
        CORE_DEPARTMENTS_READ,
        CORE_PROGRAMS_READ,
        PEOPLE_STUDENTS_READ,
        PEOPLE_FACULTY_READ,
        PEOPLE_STAFF_READ,
        DOCUMENTS_READ,
        DOCUMENTS_CREATE,
        DOCUMENTS_UPDATE,
        DOCUMENTS_VERIFY,
        DOCUMENTS_REJECT,
        DOCUMENTS_ARCHIVE,
        DOCUMENTS_DELETE,
        DOCUMENTS_MANAGE,
        DOCUMENT_CATEGORIES_READ,
        DOCUMENT_CATEGORIES_MANAGE,
        DOCUMENT_REQUIREMENTS_READ,
        DOCUMENT_REQUIREMENTS_MANAGE,
        CERTIFICATE_TEMPLATES_READ,
        CERTIFICATE_TEMPLATES_MANAGE,
        CERTIFICATE_REQUESTS_READ,
        CERTIFICATE_REQUESTS_REVIEW,
        CERTIFICATE_REQUESTS_APPROVE,
        CERTIFICATE_REQUESTS_ISSUE,
        CERTIFICATE_REQUESTS_REVOKE,
        CERTIFICATES_READ,
        CERTIFICATES_VERIFY,
        CERTIFICATES_REVOKE,
        INSTITUTIONAL_RECORDS_READ,
        INSTITUTIONAL_RECORDS_MANAGE,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        INTELLIGENCE_ACTIVITY_READ,
        INTELLIGENCE_TOOLS_READ,
        INTELLIGENCE_GOVERNANCE_READ,
        INTELLIGENCE_GOVERNANCE_MANAGE,
        INTELLIGENCE_PREDICT,
        INTELLIGENCE_RECOMMEND,
        INTELLIGENCE_EVALUATE,
    ],
    "PRINCIPAL": [
        CORE_INSTITUTION_READ,
        CORE_CAMPUSES_READ,
        CORE_DEPARTMENTS_READ,
        CORE_PROGRAMS_READ,
        CORE_ACADEMIC_YEARS_READ,
        CORE_SECTIONS_READ,
        PEOPLE_USERS_READ,
        PEOPLE_STUDENTS_READ,
        PEOPLE_FACULTY_READ,
        PEOPLE_STAFF_READ,
        ACADEMICS_SUBJECTS_READ,
        ACADEMICS_CURRICULUM_READ,
        ACADEMICS_COURSES_READ,
        ACADEMICS_ENROLLMENTS_READ,
        ACADEMICS_TIMETABLE_READ,
        ACADEMICS_ROOMS_READ,
        ATTENDANCE_SESSIONS_READ,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_CORRECTIONS_APPROVE,
        ATTENDANCE_READ,
        ATTENDANCE_CORRECT,
        ATTENDANCE_APPROVE_CORRECTION,
        LEAVE_READ,
        LEAVE_APPROVE,
        LEAVE_REJECT,
        ATTENDANCE_POLICY_READ,
        ATTENDANCE_POLICY_CREATE,
        ATTENDANCE_POLICY_UPDATE,
        EXAMINATIONS_READ,
        ASSESSMENTS_READ,
        MARKS_READ,
        RESULTS_READ,
        RESULTS_FINALIZE,
        RESULTS_PUBLISH,
        ELIGIBILITY_READ,
        ELIGIBILITY_OVERRIDE,
        EXAMINATION_RESULTS_APPROVE,
        EXAMINATION_RESULTS_PUBLISH,
        FINANCE_INVOICES_READ,
        FINANCE_REPORTS_READ,
        FINANCE_REFUNDS_APPROVE,
        FINANCE_READ,
        INVOICES_READ,
        RECEIPTS_READ,
        SCHOLARSHIPS_READ,
        PLACEMENT_DRIVES_READ,
        CAMPUS_ANNOUNCEMENTS_MANAGE,
        AUDIT_LOGS_READ,
        EVENTS_READ,
        EVENTS_CREATE,
        EVENTS_UPDATE,
        EVENTS_PUBLISH,
        EVENTS_CANCEL,
        EVENTS_MANAGE_ATTENDANCE,
        EVENTS_MANAGE_REGISTRATIONS,
        CLUBS_READ,
        CLUBS_CREATE,
        CLUBS_UPDATE,
        CLUBS_APPROVE,
        CLUBS_MANAGE_MEMBERSHIPS,
        ANNOUNCEMENTS_READ,
        ANNOUNCEMENTS_CREATE,
        ANNOUNCEMENTS_UPDATE,
        ANNOUNCEMENTS_PUBLISH,
        ANNOUNCEMENTS_ARCHIVE,
        NOTIFICATIONS_READ,
        NOTIFICATIONS_MANAGE,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        WORKFLOWS_READ,
        WORKFLOWS_EXECUTE,
        WORKFLOW_EXECUTIONS_READ,
        ANALYTICS_READ,
        ANALYTICS_QUERY,
        ANALYTICS_EXPORT,
        ANALYTICS_MANAGE,
        ANALYTICS_RECONCILE,
        ANALYTICS_BACKFILL,
        ANALYTICS_READ_DOT,
        ANALYTICS_QUERY_DOT,
        ANALYTICS_EXPORT_DOT,
        ANALYTICS_MANAGE_DOT,
        ANALYTICS_RECONCILE_DOT,
        ANALYTICS_BACKFILL_DOT,
    ],
    "HOD": [
        CORE_INSTITUTION_READ,
        CORE_DEPARTMENTS_READ,
        CORE_PROGRAMS_READ,
        CORE_ACADEMIC_YEARS_READ,
        CORE_SECTIONS_READ,
        PEOPLE_STUDENTS_READ,
        PEOPLE_FACULTY_READ,
        PEOPLE_STAFF_READ,
        ACADEMICS_SUBJECTS_READ,
        ACADEMICS_SUBJECTS_MANAGE,
        ACADEMICS_CURRICULUM_READ,
        ACADEMICS_CURRICULUM_MANAGE,
        ACADEMICS_COURSES_READ,
        ACADEMICS_COURSES_MANAGE,
        ACADEMICS_ENROLLMENTS_READ,
        ACADEMICS_ENROLLMENTS_MANAGE,
        ACADEMICS_TIMETABLE_READ,
        ACADEMICS_TIMETABLE_MANAGE,
        ACADEMICS_ROOMS_READ,
        ATTENDANCE_SESSIONS_READ,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_RECORDS_WRITE,
        ATTENDANCE_CORRECTIONS_APPROVE,
        ATTENDANCE_LEAVE_APPROVE,
        ATTENDANCE_READ,
        ATTENDANCE_MARK,
        ATTENDANCE_UPDATE,
        ATTENDANCE_LOCK,
        ATTENDANCE_CORRECT,
        ATTENDANCE_APPROVE_CORRECTION,
        LEAVE_READ,
        LEAVE_APPROVE,
        LEAVE_REJECT,
        ATTENDANCE_POLICY_READ,
        EXAMINATIONS_READ,
        EXAMINATIONS_CREATE,
        EXAMINATIONS_UPDATE,
        ASSESSMENTS_READ,
        ASSESSMENTS_CREATE,
        ASSESSMENTS_UPDATE,
        ASSESSMENTS_FINALIZE,
        MARKS_READ,
        MARKS_ENTER,
        MARKS_UPDATE,
        MARKS_FINALIZE,
        MARKS_CORRECT,
        RESULTS_READ,
        RESULTS_FINALIZE,
        RESULTS_PUBLISH,
        GRADE_SCALES_READ,
        ELIGIBILITY_READ,
        ELIGIBILITY_EVALUATE,
        EXAMINATION_ASSESSMENTS_READ,
        EXAMINATION_ASSESSMENTS_MANAGE,
        EXAMINATION_MARKS_WRITE,
        EXAMINATION_RESULTS_APPROVE,
        PLACEMENT_DRIVES_READ,
        CAMPUS_ANNOUNCEMENTS_MANAGE,
        EVENTS_READ,
        EVENTS_CREATE,
        EVENTS_UPDATE,
        EVENTS_PUBLISH,
        EVENTS_CANCEL,
        EVENTS_MANAGE_ATTENDANCE,
        EVENTS_MANAGE_REGISTRATIONS,
        CLUBS_READ,
        CLUBS_CREATE,
        CLUBS_UPDATE,
        CLUBS_APPROVE,
        CLUBS_MANAGE_MEMBERSHIPS,
        ANNOUNCEMENTS_READ,
        ANNOUNCEMENTS_CREATE,
        ANNOUNCEMENTS_UPDATE,
        ANNOUNCEMENTS_PUBLISH,
        ANNOUNCEMENTS_ARCHIVE,
        NOTIFICATIONS_READ,
        NOTIFICATIONS_MANAGE,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        DOCUMENTS_READ,
        DOCUMENTS_VERIFY,
        DOCUMENTS_REJECT,
        CERTIFICATE_TEMPLATES_READ,
        CERTIFICATE_REQUESTS_READ,
        CERTIFICATE_REQUESTS_APPROVE,
        CERTIFICATES_READ,
        INSTITUTIONAL_RECORDS_READ,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ALERTS_MANAGE,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        INTELLIGENCE_ACTIVITY_READ,
        WORKFLOWS_READ,
        WORKFLOW_EXECUTIONS_READ,
        ANALYTICS_READ,
        ANALYTICS_QUERY,
        ANALYTICS_EXPORT,
        ANALYTICS_MANAGE,
        ANALYTICS_RECONCILE,
        ANALYTICS_BACKFILL,
        ANALYTICS_READ_DOT,
        ANALYTICS_QUERY_DOT,
        ANALYTICS_EXPORT_DOT,
        ANALYTICS_MANAGE_DOT,
        ANALYTICS_RECONCILE_DOT,
        ANALYTICS_BACKFILL_DOT,
    ],
    "FACULTY": [
        LIBRARY_BRANCHES_READ,
        LIBRARY_CATALOG_READ,
        LIBRARY_CIRCULATION_RENEW,
        LIBRARY_RESERVATIONS_MANAGE,
        LIBRARY_ACQUISITIONS_REQUEST,
        LIBRARY_DIGITAL_ACCESS,
        RESEARCH_PROJECTS_READ,
        RESEARCH_PROJECTS_MANAGE,
        RESEARCH_GRANTS_APPLY,
        RESEARCH_OUTPUTS_MANAGE,
        CORE_INSTITUTION_READ,
        CORE_DEPARTMENTS_READ,
        CORE_PROGRAMS_READ,
        CORE_ACADEMIC_YEARS_READ,
        CORE_SECTIONS_READ,
        PEOPLE_STUDENTS_READ,
        ACADEMICS_SUBJECTS_READ,
        ACADEMICS_CURRICULUM_READ,
        ACADEMICS_COURSES_READ,
        ACADEMICS_ENROLLMENTS_READ,
        ACADEMICS_TIMETABLE_READ,
        ACADEMICS_ROOMS_READ,
        ATTENDANCE_SESSIONS_READ,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_RECORDS_WRITE,
        ATTENDANCE_READ,
        ATTENDANCE_MARK,
        ATTENDANCE_UPDATE,
        ATTENDANCE_LOCK,
        ATTENDANCE_CORRECT,
        LEAVE_READ,
        ATTENDANCE_POLICY_READ,
        EXAMINATIONS_READ,
        ASSESSMENTS_READ,
        ASSESSMENTS_CREATE,
        ASSESSMENTS_UPDATE,
        MARKS_READ,
        MARKS_ENTER,
        MARKS_UPDATE,
        RESULTS_READ,
        ELIGIBILITY_READ,
        EXAMINATION_ASSESSMENTS_READ,
        EXAMINATION_MARKS_WRITE,
        CAMPUS_EVENTS_MANAGE,
        EVENTS_READ,
        EVENTS_CREATE,
        EVENTS_UPDATE,
        EVENTS_MANAGE_ATTENDANCE,
        EVENTS_MANAGE_REGISTRATIONS,
        CLUBS_READ,
        CLUBS_MANAGE_MEMBERSHIPS,
        ANNOUNCEMENTS_READ,
        ANNOUNCEMENTS_CREATE,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        DOCUMENTS_READ,
        DOCUMENTS_CREATE,
        CERTIFICATES_READ,
        INSTITUTIONAL_RECORDS_READ,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        CASES_READ,
        CASES_CREATE,
        CASES_UPDATE,
        CASES_COMMENT,
        TASKS_READ,
        TASKS_CLAIM,
        TASKS_COMPLETE,
    ],
    "ACCOUNTS": [
        CORE_INSTITUTION_READ,
        PEOPLE_STUDENTS_READ,
        FINANCE_STRUCTURES_MANAGE,
        FINANCE_INVOICES_READ,
        FINANCE_INVOICES_CREATE,
        FINANCE_PAYMENTS_RECORD,
        FINANCE_REPORTS_READ,
        FINANCE_REFUNDS_APPROVE,
        FINANCE_READ,
        FINANCE_MANAGE_FEE_STRUCTURES,
        INVOICES_READ,
        INVOICES_CREATE,
        INVOICES_ISSUE,
        INVOICES_CANCEL,
        PAYMENTS_READ,
        PAYMENTS_CREATE,
        PAYMENTS_CONFIRM,
        RECEIPTS_READ,
        RECEIPTS_ISSUE,
        SCHOLARSHIPS_READ,
        SCHOLARSHIPS_CREATE,
        SCHOLARSHIPS_APPROVE,
        ADJUSTMENTS_CREATE,
        ADJUSTMENTS_APPROVE,
        REFUNDS_CREATE,
        REFUNDS_APPROVE,
        REFUNDS_PROCESS,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
    ],
    "PLACEMENT_OFFICER": [
        CORE_INSTITUTION_READ,
        PEOPLE_STUDENTS_READ,
        PLACEMENT_COMPANIES_READ,
        PLACEMENT_COMPANIES_MANAGE,
        PLACEMENT_DRIVES_READ,
        PLACEMENT_DRIVES_MANAGE,
        PLACEMENT_POSITIONS_MANAGE,
        PLACEMENT_ELIGIBILITY_EVALUATE,
        PLACEMENT_APPLICATIONS_READ,
        PLACEMENT_APPLICATIONS_REVIEW,
        PLACEMENT_INTERVIEWS_MANAGE,
        PLACEMENT_INTERVIEWS_EVALUATE,
        PLACEMENT_OFFERS_READ,
        PLACEMENT_OFFERS_MANAGE,
        PLACEMENT_OUTCOMES_MANAGE,
        PLACEMENT_ANALYTICS_READ,
        PLACEMENT_PROFILE_READ,
        PLACEMENT_PROFILE_UPDATE,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_ANALYTICS_READ,
        INTELLIGENCE_SAVED_MANAGE,
    ],
    "STUDENT": [
        STUDENT_SUCCESS_STUDENT_SELF_READ,
        LIBRARY_BRANCHES_READ,
        LIBRARY_CATALOG_READ,
        LIBRARY_CIRCULATION_RENEW,
        LIBRARY_RESERVATIONS_MANAGE,
        LIBRARY_DIGITAL_ACCESS,
        RESEARCH_PROJECTS_READ,
        CORE_INSTITUTION_READ,
        CORE_DEPARTMENTS_READ,
        CORE_PROGRAMS_READ,
        CORE_ACADEMIC_YEARS_READ,
        CORE_SECTIONS_READ,
        ACADEMICS_COURSES_READ,
        ACADEMICS_ENROLL_SELF,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_LEAVE_APPLY,
        ATTENDANCE_READ,
        ATTENDANCE_CORRECT,
        LEAVE_READ,
        LEAVE_CREATE,
        ATTENDANCE_POLICY_READ,
        EXAMINATIONS_READ,
        ASSESSMENTS_READ,
        RESULTS_READ,
        ELIGIBILITY_READ,
        EXAMINATION_RESULTS_READ_SELF,
        FINANCE_INVOICES_READ,
        FINANCE_PAYMENTS_PAY_SELF,
        FINANCE_READ,
        INVOICES_READ,
        PAYMENTS_READ,
        RECEIPTS_READ,
        SCHOLARSHIPS_READ,
        PLACEMENT_DRIVES_READ,
        PLACEMENT_APPLY_SELF,
        PLACEMENT_APPLICATIONS_READ,
        PLACEMENT_OFFERS_READ,
        PLACEMENT_OFFERS_RESPOND,
        PLACEMENT_PROFILE_READ,
        PLACEMENT_PROFILE_UPDATE,
        EVENTS_READ,
        EVENTS_SELF_REGISTER,
        EVENTS_SELF_MANAGE_REGISTRATION,
        CLUBS_READ,
        CLUBS_SELF_READ,
        CLUBS_SELF_REQUEST_MEMBERSHIP,
        CLUBS_SELF_MANAGE_MEMBERSHIP,
        ANNOUNCEMENTS_READ,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        DOCUMENTS_READ,
        DOCUMENTS_CREATE,
        CERTIFICATE_REQUESTS_CREATE,
        CERTIFICATE_REQUESTS_READ,
        CERTIFICATE_REQUESTS_CANCEL,
        CERTIFICATES_READ,
        INSTITUTIONAL_RECORDS_READ,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        GOVERNANCE_PRIVACY_CREATE,
        CASES_READ,
        CASES_CREATE,
        CASES_COMMENT,
    ],
    "PARENT": [
        CORE_INSTITUTION_READ,
        ATTENDANCE_RECORDS_READ,
        ATTENDANCE_READ,
        LEAVE_READ,
        ATTENDANCE_POLICY_READ,
        RESULTS_READ,
        EXAMINATION_RESULTS_READ_SELF,
        FINANCE_INVOICES_READ,
        FINANCE_PAYMENTS_PAY_SELF,
        ANNOUNCEMENTS_READ,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
    ],
    "STAFF": [
        CORE_INSTITUTION_READ,
        CORE_DEPARTMENTS_READ,
        PEOPLE_STAFF_READ,
        INFRASTRUCTURE_HOSTEL_MANAGE,
        INFRASTRUCTURE_TRANSPORT_MANAGE,
        DOCUMENTS_MANAGE,
        EVENTS_READ,
        EVENTS_MANAGE_ATTENDANCE,
        ANNOUNCEMENTS_READ,
        NOTIFICATIONS_SELF_READ,
        NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
        DOCUMENTS_READ,
        DOCUMENTS_CREATE,
        CERTIFICATES_READ,
        INSTITUTIONAL_RECORDS_READ,
        INTELLIGENCE_READ,
        INTELLIGENCE_QUERY,
        INTELLIGENCE_INSIGHTS_READ,
        INTELLIGENCE_ALERTS_READ,
        INTELLIGENCE_SAVED_MANAGE,
        CASES_READ,
        CASES_CREATE,
        CASES_UPDATE,
        CASES_COMMENT,
        TASKS_READ,
        TASKS_CLAIM,
        TASKS_COMPLETE,
    ],
    "PLATFORM_OPERATOR": [
        PLATFORM_TENANTS_READ,
        PLATFORM_TENANTS_MANAGE,
        PLATFORM_LIFECYCLE_MANAGE,
        PLATFORM_PROVISION_MANAGE,
        PLATFORM_ENTITLEMENTS_MANAGE,
        PLATFORM_QUOTAS_MANAGE,
        PLATFORM_SUPPORT_ACCESS,
        PLATFORM_DELETION_MANAGE,
        PLATFORM_OPS_HEALTH_READ,
        PLATFORM_RELIABILITY_READ,
        PLATFORM_RELIABILITY_MANAGE,
        PLATFORM_BACKUP_TRIGGER,
        PLATFORM_RESTORE_VERIFY,
        SECURITY_INCIDENTS_READ,
        SECURITY_INCIDENTS_MANAGE,
        SECURITY_ACTIONS_PROPOSE,
        SECURITY_ACTIONS_APPROVE,
        SECURITY_ACTIONS_EXECUTE,
        SECURITY_RULES_MANAGE,
        SECURITY_PLATFORM_READ,
    ],
    "PLATFORM_SUPPORT": [
        PLATFORM_TENANTS_READ,
        PLATFORM_SUPPORT_ACCESS,
        PLATFORM_OPS_HEALTH_READ,
        PLATFORM_RELIABILITY_READ,
        SECURITY_INCIDENTS_READ,
        SECURITY_PLATFORM_READ,
    ],
}
