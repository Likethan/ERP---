# ruff: noqa: F403, F405
"""CampusOS Permission Catalog (ALL_PERMISSIONS)."""

from typing import Final

from app.core.permissions.constants import *  # noqa: F403
from app.core.permissions.constants import PermissionDefinition

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
    # Timetable & Scheduling
    PermissionDefinition(TIMETABLE_READ, "timetable", "View master timetables, schedule grids, and sessions"),
    PermissionDefinition(TIMETABLE_MANAGE, "timetable", "Create, edit, clone, and configure timetable schedules"),
    PermissionDefinition(TIMETABLE_GENERATE, "timetable", "Run constraint-based automated timetable generation jobs"),
    PermissionDefinition(TIMETABLE_APPROVE, "timetable", "Review and approve timetable draft versions"),
    PermissionDefinition(TIMETABLE_PUBLISH, "timetable", "Publish approved timetables and synchronize canonical slots"),
    PermissionDefinition(TIMETABLE_CHANGES_REQUEST, "timetable", "Submit schedule change, reschedule, or room swap requests"),
    PermissionDefinition(TIMETABLE_CHANGES_APPROVE, "timetable", "Review and approve schedule change requests and emergency updates"),
    PermissionDefinition(TIMETABLE_RESOURCES_MANAGE, "timetable", "Manage room reservations, maintenance windows, and equipment suitability"),
    PermissionDefinition(TIMETABLE_FACULTY_AVAILABILITY, "timetable", "Configure faculty availability windows and workload preferences"),
    PermissionDefinition(TIMETABLE_REPORTS_READ, "timetable", "View timetable coverage, room utilization, and faculty workload analytics"),
    PermissionDefinition(TIMETABLE_STUDENT_SELF_READ, "timetable", "Student view of published cohort class timetable"),
    # Step 50: Enterprise Procurement, Vendor Management & Inventory Control
    PermissionDefinition(PROCUREMENT_READ, "procurement", "View procurement vendors, requisitions, purchase orders, and stock"),
    PermissionDefinition(PROCUREMENT_MANAGE, "procurement", "Manage vendor onboarding, purchase orders, and procurement configuration"),
    PermissionDefinition(PROCUREMENT_VENDORS_MANAGE, "procurement", "Register, verify, and evaluate supplier/vendor organizations"),
    PermissionDefinition(PROCUREMENT_REQUISITIONS_CREATE, "procurement", "Create and submit departmental purchase requisitions"),
    PermissionDefinition(PROCUREMENT_REQUISITIONS_APPROVE, "procurement", "Review, return, or approve purchase requisitions"),
    PermissionDefinition(PROCUREMENT_QUOTATIONS_MANAGE, "procurement", "Manage RFQs, quotation submissions, and vendor evaluation scores"),
    PermissionDefinition(PROCUREMENT_ORDERS_CREATE, "procurement", "Draft and amend institutional purchase orders"),
    PermissionDefinition(PROCUREMENT_ORDERS_APPROVE, "procurement", "Approve and issue binding purchase orders"),
    PermissionDefinition(PROCUREMENT_RECEIVING_MANAGE, "procurement", "Record goods receipts, quality inspection, and returns (RTV)"),
    PermissionDefinition(PROCUREMENT_INVENTORY_MANAGE, "procurement", "Manage inventory locations, items, stock adjustments, and transfers"),
    PermissionDefinition(PROCUREMENT_INVENTORY_READ, "procurement", "View inventory item catalogue, availability, and movement history"),
    PermissionDefinition(PROCUREMENT_INVOICE_MATCH, "procurement", "Perform three-way invoice matching and resolve variance overrides"),
    PermissionDefinition(PROCUREMENT_REPORTS_READ, "procurement", "View procurement spend, order fulfillment, and inventory analytics"),
    # Step 51: Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration
    PermissionDefinition(WORKFORCE_READ, "workforce", "View workforce directory, leave, and workload"),
    PermissionDefinition(WORKFORCE_MANAGE, "workforce", "Manage workforce configuration and administration"),
    PermissionDefinition(WORKFORCE_EMPLOYEE_READ, "workforce", "View workforce employee profiles and employment history"),
    PermissionDefinition(WORKFORCE_EMPLOYEE_MANAGE, "workforce", "Create, update, and transfer employee records"),
    PermissionDefinition(WORKFORCE_LIFECYCLE_MANAGE, "workforce", "Manage staff onboarding, offboarding, and clearance tasks"),
    PermissionDefinition(WORKFORCE_LEAVE_POLICY_MANAGE, "workforce", "Configure leave types, policies, and accrual rules"),
    PermissionDefinition(WORKFORCE_LEAVE_READ, "workforce", "View leave requests, balances, and calendar"),
    PermissionDefinition(WORKFORCE_LEAVE_SUBMIT, "workforce", "Submit employee leave requests"),
    PermissionDefinition(WORKFORCE_LEAVE_APPROVE, "workforce", "Review, approve, or reject leave applications"),
    PermissionDefinition(WORKFORCE_LEAVE_BALANCE_MANAGE, "workforce", "Adjust, grant, and reconcile employee leave balances"),
    PermissionDefinition(WORKFORCE_AVAILABILITY_READ, "workforce", "Check staff availability and timetable scheduling conflicts"),
    PermissionDefinition(WORKFORCE_WORKLOAD_READ, "workforce", "View staff workload targets, allocations, and summaries"),
    PermissionDefinition(WORKFORCE_WORKLOAD_MANAGE, "workforce", "Define workload targets, adjust hours, and manage assignments"),
    PermissionDefinition(WORKFORCE_HR_CASE_READ, "workforce", "View employee self-service requests and HR service cases"),
    PermissionDefinition(WORKFORCE_HR_CASE_MANAGE, "workforce", "Assign, update, and resolve HR service cases"),
    PermissionDefinition(WORKFORCE_REPORTS_READ, "workforce", "View workforce headcount, leave utilization, and capacity reports"),
    # Step 52: Enterprise Payroll, Compensation, Benefits & Statutory Compliance
    PermissionDefinition(PAYROLL_COMPENSATION_READ, "payroll", "View salary structures, compensation grades, and employee assignments"),
    PermissionDefinition(PAYROLL_COMPENSATION_MANAGE, "payroll", "Configure salary structures, pay grades, and employee compensation packages"),
    PermissionDefinition(PAYROLL_CALENDAR_MANAGE, "payroll", "Manage payroll calendars, pay cycles, and cutoff schedules"),
    PermissionDefinition(PAYROLL_RUN_CREATE, "payroll", "Create and initiate payroll processing batches"),
    PermissionDefinition(PAYROLL_RUN_CALCULATE, "payroll", "Trigger payroll calculation engine and view computation breakdown"),
    PermissionDefinition(PAYROLL_RUN_REVIEW, "payroll", "Review pre-payroll summaries, exceptions, and reconciliation items"),
    PermissionDefinition(PAYROLL_RUN_APPROVE, "payroll", "Approve or reject calculated payroll runs"),
    PermissionDefinition(PAYROLL_RUN_POST, "payroll", "Post finalized payroll runs to financial general ledger journals"),
    PermissionDefinition(PAYROLL_PAYMENT_MANAGE, "payroll", "Prepare and export payment disbursement files and bank instructions"),
    PermissionDefinition(PAYROLL_RECONCILIATION_MANAGE, "payroll", "Reconcile payment transactions with bank statements and clear anomalies"),
    PermissionDefinition(PAYROLL_COMPLIANCE_MANAGE, "payroll", "Configure and maintain versioned statutory compliance rules and contributions"),
    PermissionDefinition(PAYROLL_PAYSLIP_READ_OWN, "payroll", "Access personal finalized payslips and annual compensation summaries"),
    PermissionDefinition(PAYROLL_PAYSLIP_READ_AUTH, "payroll", "Access employee payslips for institutional audits and administration"),
    PermissionDefinition(PAYROLL_REPORTS_READ, "payroll", "Generate and export payroll registers, statutory reports, and tax audits"),
    # Step 53: Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management
    PermissionDefinition(ASSETS_READ, "assets", "View registered institutional assets, custody, and lifecycle status"),
    PermissionDefinition(ASSETS_CREATE, "assets", "Register new institutional assets, equipment, and facilities"),
    PermissionDefinition(ASSETS_MANAGE, "assets", "Configure asset categories, policies, and edit asset records"),
    PermissionDefinition(ASSETS_ASSIGN, "assets", "Assign asset custody, temporary loans, and process handovers"),
    PermissionDefinition(ASSETS_TRANSFER, "assets", "Initiate and approve inter-campus or departmental asset transfers"),
    PermissionDefinition(ASSETS_LIFECYCLE_MANAGE, "assets", "Execute lifecycle transitions, state changes, and decommissioning"),
    PermissionDefinition(ASSETS_MAINTENANCE_READ, "assets", "View maintenance plans, schedules, and work orders"),
    PermissionDefinition(ASSETS_MAINTENANCE_MANAGE, "assets", "Create, dispatch, update, and close maintenance work orders and consume parts"),
    PermissionDefinition(ASSETS_INSPECTION_MANAGE, "assets", "Execute periodic inspections, record safety findings, and apply restrictions"),
    PermissionDefinition(ASSETS_AUDIT_MANAGE, "assets", "Create audit campaigns, conduct tag verification scans, and reconcile discrepancies"),
    PermissionDefinition(ASSETS_RETIREMENT_REQUEST, "assets", "Submit formal asset retirement and disposal requests"),
    PermissionDefinition(ASSETS_RETIREMENT_APPROVE, "assets", "Approve asset retirement, condemnation, and certified disposal"),
    PermissionDefinition(ASSETS_FINANCIAL_READ, "assets", "Access fixed-asset depreciation schedules, book values, and finance references"),
    PermissionDefinition(ASSETS_REPORT_READ, "assets", "Generate enterprise asset, maintenance, and compliance analytics reports"),
    # Step 54: Enterprise Hostel, Residential Life, Room Allocation & Student Accommodation Management
    PermissionDefinition(RESIDENTIAL_HOSTEL_READ, "residential", "View hostels, buildings, floors, rooms, and bed inventory"),
    PermissionDefinition(RESIDENTIAL_HOSTEL_MANAGE, "residential", "Configure hostels, blocks, floors, rooms, amenities, and policies"),
    PermissionDefinition(RESIDENTIAL_ROOM_MANAGE, "residential", "Manage room inventory, temporary bed blocks, and capacity"),
    PermissionDefinition(RESIDENTIAL_APPLICATION_SUBMIT_OWN, "residential", "Submit own accommodation application and preferences"),
    PermissionDefinition(RESIDENTIAL_APPLICATION_REVIEW, "residential", "Review, score, approve, waitlist, or reject accommodation applications"),
    PermissionDefinition(RESIDENTIAL_ALLOCATION_MANAGE, "residential", "Manage bed allocations, reservations, transfers, and waitlists"),
    PermissionDefinition(RESIDENTIAL_CHECKIN_MANAGE, "residential", "Process resident check-in, key handover, and facility condition acknowledgement"),
    PermissionDefinition(RESIDENTIAL_CHECKOUT_MANAGE, "residential", "Execute resident check-out, room handover inspection, and damage charge assessment"),
    PermissionDefinition(RESIDENTIAL_FEES_READ, "residential", "View residential fee plans, meal plan charges, and payment summaries"),
    PermissionDefinition(RESIDENTIAL_FEES_MANAGE, "residential", "Configure hostel fee plans, meal plan rates, and generate residential invoices"),
    PermissionDefinition(RESIDENTIAL_MOVEMENT_MANAGE, "residential", "Authorize, track, and verify student outings, leave passes, and roll-calls"),
    PermissionDefinition(RESIDENTIAL_VISITOR_MANAGE, "residential", "Register, approve, and verify hostel visitors and security gate passes"),
    PermissionDefinition(RESIDENTIAL_MAINTENANCE_SUBMIT, "residential", "Submit hostel service requests, room repair tickets, and feedback"),
    PermissionDefinition(RESIDENTIAL_INCIDENT_READ_AUTHORIZED, "residential", "Access restricted residential safety and disciplinary incident reports"),
    PermissionDefinition(RESIDENTIAL_INCIDENT_MANAGE, "residential", "Log, investigate, escalate, and resolve residential safety incidents and inspections"),
    PermissionDefinition(RESIDENTIAL_REPORT_READ, "residential", "Generate residential occupancy dashboards, vacancy summaries, and compliance reports"),
    # Step 55: Enterprise Transport, Fleet, Routes & Student Mobility Management
    PermissionDefinition(TRANSPORT_SERVICE_READ, "transport", "View transport service configurations, zones, and schedules"),
    PermissionDefinition(TRANSPORT_SERVICE_MANAGE, "transport", "Configure transport service policies, operating calendars, and capacity limits"),
    PermissionDefinition(TRANSPORT_VEHICLE_READ, "transport", "View institutional vehicle fleet, specs, and status"),
    PermissionDefinition(TRANSPORT_VEHICLE_MANAGE, "transport", "Manage institutional fleet vehicles, compliance certificates, and safety checks"),
    PermissionDefinition(TRANSPORT_DRIVER_MANAGE, "transport", "Manage driver assignments, driving license compliance, and shifts"),
    PermissionDefinition(TRANSPORT_ROUTE_READ, "transport", "View transit routes, itineraries, stops, and schedules"),
    PermissionDefinition(TRANSPORT_ROUTE_MANAGE, "transport", "Create, edit, suspend, or retire transport routes and ordered stops"),
    PermissionDefinition(TRANSPORT_APPLICATION_SUBMIT_OWN, "transport", "Submit own transport pass application and route preferences"),
    PermissionDefinition(TRANSPORT_APPLICATION_REVIEW, "transport", "Review, score, approve, waitlist, or reject student transport applications"),
    PermissionDefinition(TRANSPORT_SUBSCRIPTION_MANAGE, "transport", "Manage transport subscriptions, renewals, suspensions, and passes"),
    PermissionDefinition(TRANSPORT_ALLOCATION_MANAGE, "transport", "Execute seat allocations, route transfers, and waitlist allocations"),
    PermissionDefinition(TRANSPORT_TRIP_READ, "transport", "View scheduled and operational transport trips and manifests"),
    PermissionDefinition(TRANSPORT_TRIP_DISPATCH, "transport", "Dispatch trips, assign substitute drivers/vehicles, and log operational deviations"),
    PermissionDefinition(TRANSPORT_BOARDING_RECORD, "transport", "Record and verify student boarding and drop-off attendance on trips"),
    PermissionDefinition(TRANSPORT_TRACKING_READ_AUTHORIZED, "transport", "Access live or telemetry vehicle tracking with privacy controls"),
    PermissionDefinition(TRANSPORT_INCIDENT_MANAGE, "transport", "Log, investigate, and resolve transport safety incidents and breakdowns"),
    PermissionDefinition(TRANSPORT_FINANCE_READ_AUTHORIZED, "transport", "Access transport pricing plans, fee structures, and invoice reconciliations"),
    PermissionDefinition(TRANSPORT_REPORT_READ, "transport", "Generate transport route utilization, passenger manifest, and compliance analytics reports"),
    # Step 57: Enterprise Sports, Athletics, Recreation & Student Fitness Management
    PermissionDefinition(SPORTS_DEPARTMENT_READ, "sports", "View sports departments, recreation centers, and policies"),
    PermissionDefinition(SPORTS_DEPARTMENT_MANAGE, "sports", "Configure sports departments, staff assignments, and operating schedules"),
    PermissionDefinition(SPORTS_FACILITY_READ, "sports", "View campus sports grounds, courts, and bookable facilities"),
    PermissionDefinition(SPORTS_FACILITY_MANAGE, "sports", "Register and configure sports facilities, operating hours, and maintenance closures"),
    PermissionDefinition(SPORTS_BOOKING_CREATE, "sports", "Reserve sports facilities and courts for training, recreation, or events"),
    PermissionDefinition(SPORTS_BOOKING_MANAGE, "sports", "Manage, approve, or cancel facility reservations and conflict overrides"),
    PermissionDefinition(SPORTS_PARTICIPANT_READ, "sports", "View student athlete and participant sports profiles and clearance status"),
    PermissionDefinition(SPORTS_PARTICIPANT_REGISTER_SELF, "sports", "Self-service registration for sports activities, teams, and fitness camps"),
    PermissionDefinition(SPORTS_PARTICIPANT_MANAGE, "sports", "Manage participant eligibility, clearance verification, and consent records"),
    PermissionDefinition(SPORTS_TEAM_READ, "sports", "View institutional sports teams, divisions, and rosters"),
    PermissionDefinition(SPORTS_TEAM_MANAGE, "sports", "Create and govern sports teams, roster capacity, and membership approvals"),
    PermissionDefinition(SPORTS_COACH_MANAGE, "sports", "Assign and manage coaches, trainers, and coordinators for teams and programs"),
    PermissionDefinition(SPORTS_TRAINING_READ, "sports", "View training programs, fitness camps, and session schedules"),
    PermissionDefinition(SPORTS_TRAINING_MANAGE, "sports", "Create training programs, schedule sessions, and manage camp enrollment"),
    PermissionDefinition(SPORTS_ATTENDANCE_RECORD, "sports", "Record and verify student athlete attendance at training sessions"),
    PermissionDefinition(SPORTS_COMPETITION_READ, "sports", "View tournaments, leagues, sports meets, and fixtures"),
    PermissionDefinition(SPORTS_COMPETITION_MANAGE, "sports", "Organize tournaments, generate fixtures, and configure competition rules"),
    PermissionDefinition(SPORTS_MATCH_SCHEDULE, "sports", "Schedule, reschedule, and assign venues and officials to matches"),
    PermissionDefinition(SPORTS_RESULT_RECORD, "sports", "Input match scores, results, and game events"),
    PermissionDefinition(SPORTS_RESULT_VERIFY, "sports", "Verify and publish official match outcomes, standings, and rankings"),
    PermissionDefinition(SPORTS_EQUIPMENT_MANAGE, "sports", "Manage sports gear checkout, returns, and inventory damage tracking"),
    PermissionDefinition(SPORTS_FINANCE_MANAGE, "sports", "Configure tournament entry fees, program pricing, and invoice generation"),
    PermissionDefinition(SPORTS_REPORT_READ, "sports", "Access sports participation, facility utilization, and competition reports"),
    # Step 58: Enterprise Student Affairs, Grievance Redressal & Disciplinary Case Management
    PermissionDefinition(SA_OFFICE_READ, "student_affairs", "View student affairs offices, policies, and grievance categories"),
    PermissionDefinition(SA_OFFICE_MANAGE, "student_affairs", "Configure student affairs offices, staff assignments, and campus settings"),
    PermissionDefinition(SA_CATEGORY_READ, "student_affairs", "View institutional grievance categories and SLA rules"),
    PermissionDefinition(SA_CATEGORY_MANAGE, "student_affairs", "Manage grievance categories, SLA hours, and confidentiality requirements"),
    PermissionDefinition(SA_CASE_SUBMIT_OWN, "student_affairs", "Submit student grievances, complaints, and requests for resolution"),
    PermissionDefinition(SA_CASE_READ_OWN, "student_affairs", "View status, receipts, and communication history for own submitted cases"),
    PermissionDefinition(SA_CASE_READ_ASSIGNED, "student_affairs", "View and process cases specifically assigned to case officer or investigator"),
    PermissionDefinition(SA_CASE_READ_ALL, "student_affairs", "Access all student affairs cases across campus with role-based restrictions"),
    PermissionDefinition(SA_CASE_ASSIGN, "student_affairs", "Assign and reassign case officers and investigators with conflict tracking"),
    PermissionDefinition(SA_CASE_UPDATE, "student_affairs", "Update case classification, status transitions, and procedural milestones"),
    PermissionDefinition(SA_CASE_CONFIDENTIAL_READ, "student_affairs", "Access confidential and restricted safeguarding case records"),
    PermissionDefinition(SA_DISCIPLINARY_MANAGE, "student_affairs", "Manage formal disciplinary proceedings, notices, findings, and sanctions"),
    PermissionDefinition(SA_EVIDENCE_READ, "student_affairs", "Review evidence attachments, witness statements, and procedural documents"),
    PermissionDefinition(SA_EVIDENCE_UPLOAD, "student_affairs", "Upload evidence files, incident reports, and case documentation"),
    PermissionDefinition(SA_EVIDENCE_REDACT, "student_affairs", "Redact sensitive personal data from evidence files while preserving originals"),
    PermissionDefinition(SA_MEETING_MANAGE, "student_affairs", "Schedule and manage hearings, mediation sessions, and case conferences"),
    PermissionDefinition(SA_RESOLUTION_PROPOSE, "student_affairs", "Propose resolutions, corrective actions, and restitution terms"),
    PermissionDefinition(SA_RESOLUTION_APPROVE, "student_affairs", "Authorize formal case resolutions, agreed remedies, and closures"),
    PermissionDefinition(SA_APPEAL_FILE, "student_affairs", "File formal appeals against disciplinary decisions within policy windows"),
    PermissionDefinition(SA_APPEAL_REVIEW, "student_affairs", "Review appeals under separation-of-duties governance and issue final determinations"),
    PermissionDefinition(SA_ESCALATION_MANAGE, "student_affairs", "Manage urgent safeguarding escalations, threat evaluations, and safety referrals"),
    PermissionDefinition(SA_COMMUNICATION_SEND, "student_affairs", "Send confidential messages and information requests within authorized case threads"),
    PermissionDefinition(SA_REPORT_READ, "student_affairs", "Access student affairs analytics, grievance SLA tracking, and resolution reports"),
    PermissionDefinition(SA_POLICY_MANAGE, "student_affairs", "Configure institutional student affairs policies, SLA targets, and appeal rules"),
    # Student Counselling, Mentoring & Personal Development (Step 59)
    PermissionDefinition(MENTOR_ASSIGNMENT_READ, "student_support", "View student-mentor assignments and coverage"),
    PermissionDefinition(MENTOR_ASSIGNMENT_MANAGE, "student_support", "Create, update, and reassign faculty mentors"),
    PermissionDefinition(MENTORING_SESSION_READ, "student_support", "View scheduled and completed mentoring sessions"),
    PermissionDefinition(MENTORING_SESSION_MANAGE, "student_support", "Schedule, update, and record mentoring session summaries"),
    PermissionDefinition(MENTORING_SESSION_PARTICIPATE, "student_support", "Participate in mentoring sessions and record reflections"),
    PermissionDefinition(COUNSELLING_APPOINTMENT_REQUEST, "student_support", "Request or book counselling appointments"),
    PermissionDefinition(COUNSELLING_APPOINTMENT_READ, "student_support", "View counselling appointment schedule and status"),
    PermissionDefinition(COUNSELLING_APPOINTMENT_MANAGE, "student_support", "Confirm, reschedule, or cancel counselling appointments"),
    PermissionDefinition(COUNSELLING_CONFIDENTIAL_READ, "student_support", "Access restricted confidential clinical counselling records"),
    PermissionDefinition(COUNSELLING_CONFIDENTIAL_WRITE, "student_support", "Record and update restricted clinical counselling notes"),
    PermissionDefinition(DEVELOPMENT_PLAN_READ, "student_support", "View student individual development plans"),
    PermissionDefinition(DEVELOPMENT_PLAN_MANAGE, "student_support", "Create and manage student development plans and goals"),
    PermissionDefinition(DEVELOPMENT_PLAN_UPDATE_OWN, "student_support", "Update self-development progress and reflections"),
    PermissionDefinition(SUPPORT_REFERRAL_CREATE, "student_support", "Create referrals across student support services"),
    PermissionDefinition(SUPPORT_REFERRAL_READ, "student_support", "View student support referrals and statuses"),
    PermissionDefinition(SUPPORT_REFERRAL_MANAGE, "student_support", "Process, accept, or close student support referrals"),
    PermissionDefinition(SUPPORT_FOLLOWUP_MANAGE, "student_support", "Coordinate and complete support follow-up deadlines"),
    PermissionDefinition(SUPPORT_REPORT_READ, "student_support", "Access aggregate mentoring and non-confidential support analytics"),
    PermissionDefinition(SUPPORT_CONFIG_MANAGE, "student_support", "Configure mentoring limits, booking windows, and support policies"),
    # International Relations, Student Exchange & Global Mobility (Step 60)
    PermissionDefinition(INTL_PARTNER_READ, "international", "View international partners and universities"),
    PermissionDefinition(INTL_PARTNER_MANAGE, "international", "Register, update, and manage international partner institutions"),
    PermissionDefinition(INTL_AGREEMENT_READ, "international", "View institutional MoUs, bilateral agreements, and renewal terms"),
    PermissionDefinition(INTL_AGREEMENT_MANAGE, "international", "Draft, approve, and manage international partnership agreements"),
    PermissionDefinition(INTL_PROGRAM_READ, "international", "Browse published exchange and study-abroad programs"),
    PermissionDefinition(INTL_PROGRAM_MANAGE, "international", "Configure and publish international mobility programs"),
    PermissionDefinition(MOBILITY_APPLICATION_APPLY, "international", "Apply for study abroad and exchange programs"),
    PermissionDefinition(MOBILITY_APPLICATION_READ, "international", "View student mobility applications and status"),
    PermissionDefinition(MOBILITY_APPLICATION_REVIEW, "international", "Review and evaluate student exchange applications"),
    PermissionDefinition(MOBILITY_APPLICATION_NOMINATE, "international", "Nominate approved students to partner institutions"),
    PermissionDefinition(MOBILITY_INBOUND_MANAGE, "international", "Manage inbound exchange students, arrival, and orientation"),
    PermissionDefinition(FACULTY_MOBILITY_READ, "international", "View faculty mobility and visiting scholar records"),
    PermissionDefinition(FACULTY_MOBILITY_MANAGE, "international", "Coordinate outbound faculty exchange and visiting scholar visits"),
    PermissionDefinition(CREDIT_EQUIVALENCY_READ, "international", "View course equivalency mappings"),
    PermissionDefinition(CREDIT_EQUIVALENCY_EVALUATE, "international", "Evaluate international course syllabi and proposed equivalencies"),
    PermissionDefinition(CREDIT_TRANSFER_APPROVE, "international", "Approve formal academic credit transfer determinations"),
    PermissionDefinition(MOBILITY_DOCUMENT_VERIFY, "international", "Verify international mobility checklists and uploaded documents"),
    PermissionDefinition(MOBILITY_FUNDING_MANAGE, "international", "Coordinate mobility scholarships, grants, and funding requests"),
    PermissionDefinition(INTL_REPORT_READ, "international", "Access global mobility and partnership health analytics"),
    PermissionDefinition(INTL_CONFIG_MANAGE, "international", "Configure international mobility policies and workflows"),
    # Legal Affairs, Contract Lifecycle & Risk (Step 62)
    PermissionDefinition(LEGAL_OPERATIONS_READ, "legal", "Access unified institutional legal operations dashboard"),
    PermissionDefinition(LEGAL_CONTRACTS_READ, "legal", "View institutional contract registry and status"),
    PermissionDefinition(LEGAL_CONTRACTS_MANAGE, "legal", "Create, edit, and transition institutional contracts"),
    PermissionDefinition(LEGAL_CONTRACTS_APPROVE, "legal", "Approve institutional contracts through workflow"),
    PermissionDefinition(LEGAL_CONTRACTS_EXECUTE, "legal", "Record execution and external signature of contracts"),
    PermissionDefinition(LEGAL_OBLIGATIONS_READ, "legal", "View contractual commitments and obligations"),
    PermissionDefinition(LEGAL_OBLIGATIONS_MANAGE, "legal", "Manage, fulfill, verify, or waive contract obligations"),
    PermissionDefinition(LEGAL_MATTERS_READ, "legal", "View authorized institutional legal matters and cases"),
    PermissionDefinition(LEGAL_MATTERS_MANAGE, "legal", "Create and manage institutional legal matters"),
    PermissionDefinition(LEGAL_MATTERS_CONFIDENTIAL, "legal", "Access restricted attorney-client privileged legal notes"),
    PermissionDefinition(LEGAL_POLICIES_MANAGE, "legal", "Draft, update, and manage institutional policies"),
    PermissionDefinition(LEGAL_POLICIES_APPROVE, "legal", "Approve and publish institutional policies"),
    PermissionDefinition(LEGAL_COMPLIANCE_READ, "legal", "View compliance obligations and assessments"),
    PermissionDefinition(LEGAL_COMPLIANCE_MANAGE, "legal", "Manage compliance obligations, evidence, and corrective actions"),
    PermissionDefinition(LEGAL_RISKS_READ, "legal", "View enterprise risk register and 5x5 scoring matrix"),
    PermissionDefinition(LEGAL_RISKS_MANAGE, "legal", "Assess, mitigate, and record accepted institutional risks"),
    # Student Engagement, Community Service, Volunteering & Civic Impact (Step 65)
    PermissionDefinition(ENGAGEMENT_PROGRAMS_READ, "engagement", "View community service and engagement programs"),
    PermissionDefinition(ENGAGEMENT_PROGRAMS_MANAGE, "engagement", "Create, edit, and coordinate community engagement programs"),
    PermissionDefinition(ENGAGEMENT_PROGRAMS_APPROVE, "engagement", "Approve community engagement programs"),
    PermissionDefinition(ENGAGEMENT_PROGRAMS_PUBLISH, "engagement", "Publish approved community engagement programs"),
    PermissionDefinition(ENGAGEMENT_PARTNERS_READ, "engagement", "View community partners and collaborative organizations"),
    PermissionDefinition(ENGAGEMENT_PARTNERS_MANAGE, "engagement", "Manage partner organizations and partnership agreements"),
    PermissionDefinition(ENGAGEMENT_OPPORTUNITIES_READ, "engagement", "Discover and view volunteering opportunities"),
    PermissionDefinition(ENGAGEMENT_OPPORTUNITIES_MANAGE, "engagement", "Create and manage volunteering opportunities and shifts"),
    PermissionDefinition(ENGAGEMENT_APPLICATIONS_APPLY, "engagement", "Apply for volunteering opportunities"),
    PermissionDefinition(ENGAGEMENT_APPLICATIONS_READ, "engagement", "View volunteer participation applications"),
    PermissionDefinition(ENGAGEMENT_APPLICATIONS_MANAGE, "engagement", "Review, approve, waitlist, or reject participation applications"),
    PermissionDefinition(ENGAGEMENT_SHIFTS_MANAGE, "engagement", "Create shifts and manage participant rosters"),
    PermissionDefinition(ENGAGEMENT_ATTENDANCE_RECORD, "engagement", "Record check-in, check-out and participation attendance"),
    PermissionDefinition(ENGAGEMENT_HOURS_SUBMIT, "engagement", "Submit service hours for verification"),
    PermissionDefinition(ENGAGEMENT_HOURS_VERIFY, "engagement", "Verify, adjust, and approve student service hours"),
    PermissionDefinition(ENGAGEMENT_REFLECTIONS_SUBMIT, "engagement", "Submit reflections, learning outcomes and evidence"),
    PermissionDefinition(ENGAGEMENT_REFLECTIONS_REVIEW, "engagement", "Review and grade student reflection submissions"),
    PermissionDefinition(ENGAGEMENT_CERTIFICATES_ISSUE, "engagement", "Issue verifiable engagement and civic service certificates"),
    PermissionDefinition(ENGAGEMENT_CERTIFICATES_REVOKE, "engagement", "Revoke or reissue engagement certificates"),
    PermissionDefinition(ENGAGEMENT_SAFETY_MANAGE, "engagement", "Manage safety briefings, consent records, and risk clearance"),
    PermissionDefinition(ENGAGEMENT_ANALYTICS_READ, "engagement", "Access civic engagement and impact analytics"),
    PermissionDefinition(ENGAGEMENT_POLICIES_MANAGE, "engagement", "Configure community engagement guidelines and policies"),
    # Step 66: Enterprise Student Housing, Off-Campus Accommodation & Landlord Partnerships
    PermissionDefinition(HOUSING_PROPERTY_READ, "housing", "View approved accommodation properties and housing options"),
    PermissionDefinition(HOUSING_PROPERTY_MANAGE, "housing", "Create, update, and manage student housing properties"),
    PermissionDefinition(HOUSING_PROPERTY_APPROVE, "housing", "Review and approve/suspend accommodation properties"),
    PermissionDefinition(HOUSING_PROVIDER_READ, "housing", "View registered accommodation providers and landlords"),
    PermissionDefinition(HOUSING_PROVIDER_MANAGE, "housing", "Manage landlord partnerships, MoUs, and provider records"),
    PermissionDefinition(HOUSING_PROVIDER_PORTAL, "housing", "Access provider and landlord self-service portal"),
    PermissionDefinition(HOUSING_REQUEST_SUBMIT_OWN, "housing", "Submit own student housing and accommodation request"),
    PermissionDefinition(HOUSING_REQUEST_READ, "housing", "View student housing requests across institution/campus"),
    PermissionDefinition(HOUSING_REQUEST_REVIEW, "housing", "Review, evaluate, and approve/reject housing requests"),
    PermissionDefinition(HOUSING_OFFER_MANAGE, "housing", "Issue, modify, or revoke accommodation offers"),
    PermissionDefinition(HOUSING_ASSIGNMENT_MANAGE, "housing", "Allocate, transfer, and manage student room assignments"),
    PermissionDefinition(HOUSING_AGREEMENT_READ, "housing", "View housing agreements, leases, and deposit terms"),
    PermissionDefinition(HOUSING_AGREEMENT_MANAGE, "housing", "Create and execute accommodation agreements and leases"),
    PermissionDefinition(HOUSING_CHECKIN_MANAGE, "housing", "Process check-in/out, inventory checklists, and damage assessments"),
    PermissionDefinition(HOUSING_INSPECTION_READ, "housing", "View property safety, fire, and hygiene inspection reports"),
    PermissionDefinition(HOUSING_INSPECTION_MANAGE, "housing", "Schedule and conduct residential compliance inspections"),
    PermissionDefinition(HOUSING_MAINTENANCE_SUBMIT, "housing", "Submit accommodation maintenance and repair requests"),
    PermissionDefinition(HOUSING_MAINTENANCE_MANAGE, "housing", "Coordinate, assign, and resolve housing maintenance work orders"),
    PermissionDefinition(HOUSING_ANALYTICS_READ, "housing", "Access housing occupancy, capacity, and compliance analytics"),
    # Step 67: Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Platform
    PermissionDefinition(SUSTAINABILITY_TARGET_READ, "sustainability", "View sustainability targets, baselines, and KPI configurations"),
    PermissionDefinition(SUSTAINABILITY_TARGET_MANAGE, "sustainability", "Configure and update campus sustainability targets"),
    PermissionDefinition(SUSTAINABILITY_ENERGY_READ, "sustainability", "View energy consumption and renewable generation data"),
    PermissionDefinition(SUSTAINABILITY_ENERGY_MANAGE, "sustainability", "Record energy readings, fuels, and investigate peak anomalies"),
    PermissionDefinition(SUSTAINABILITY_WATER_READ, "sustainability", "View water consumption, borewell, rainwater, and recycling logs"),
    PermissionDefinition(SUSTAINABILITY_WATER_MANAGE, "sustainability", "Record water utility logs, detect leak anomalies, and coordinate fixes"),
    PermissionDefinition(SUSTAINABILITY_WASTE_READ, "sustainability", "View solid, organic, and recyclable waste audit records"),
    PermissionDefinition(SUSTAINABILITY_WASTE_MANAGE, "sustainability", "Record and manage waste manifests and vendor recycling certificates"),
    PermissionDefinition(SUSTAINABILITY_WASTE_HAZARDOUS, "sustainability", "Authorize, manifest, and verify hazardous and e-waste disposals"),
    PermissionDefinition(SUSTAINABILITY_EMISSIONS_READ, "sustainability", "View Scope 1, 2, and 3 carbon accounting balances"),
    PermissionDefinition(SUSTAINABILITY_EMISSIONS_CALCULATE, "sustainability", "Execute carbon calculation runs and emission recalculations"),
    PermissionDefinition(SUSTAINABILITY_EMISSIONS_FACTOR_MANAGE, "sustainability", "Maintain emission factor registries, versions, and warming potentials"),
    PermissionDefinition(SUSTAINABILITY_INITIATIVE_READ, "sustainability", "View campus green initiatives, programs, and milestones"),
    PermissionDefinition(SUSTAINABILITY_INITIATIVE_MANAGE, "sustainability", "Create and track sustainability programs, investments, and budgets"),
    PermissionDefinition(SUSTAINABILITY_COMPLIANCE_READ, "sustainability", "View environmental compliance obligations, permits, and inspection audits"),
    PermissionDefinition(SUSTAINABILITY_COMPLIANCE_MANAGE, "sustainability", "Manage environmental licenses, NOC renewals, and corrective actions"),
    PermissionDefinition(SUSTAINABILITY_IOT_INGEST, "sustainability", "Ingest and process smart meter and IoT environmental sensor telemetry"),
    PermissionDefinition(SUSTAINABILITY_DATA_IMPORT, "sustainability", "Bulk import utility invoices, meter spreadsheets, and historical datasets"),
    PermissionDefinition(SUSTAINABILITY_ANALYTICS_READ, "sustainability", "Access campus sustainability dashboards, ESG metrics, and net-zero projections"),
    PermissionDefinition(CAMPUS_SECURITY_CONFIG_READ, "campus_security", "View campus security gates, zones, and operating policies"),
    PermissionDefinition(CAMPUS_SECURITY_CONFIG_MANAGE, "campus_security", "Configure campus checkpoints, security zones, and visit policies"),
    PermissionDefinition(CAMPUS_SECURITY_VISITOR_READ, "campus_security", "View visitor pre-registrations and visit logs"),
    PermissionDefinition(CAMPUS_SECURITY_VISITOR_REQUEST, "campus_security", "Submit visitor pre-registration and host requests"),
    PermissionDefinition(CAMPUS_SECURITY_VISITOR_APPROVE, "campus_security", "Approve or reject visitor requests"),
    PermissionDefinition(CAMPUS_SECURITY_GATE_CHECKIN, "campus_security", "Process visitor gate check-in and issue visitor passes"),
    PermissionDefinition(CAMPUS_SECURITY_GATE_CHECKOUT, "campus_security", "Process visitor gate check-out"),
    PermissionDefinition(CAMPUS_SECURITY_PASS_REVOKE, "campus_security", "Revoke active visitor pass or access token"),
    PermissionDefinition(CAMPUS_SECURITY_CONTRACTOR_READ, "campus_security", "View contractor organization profiles and work permits"),
    PermissionDefinition(CAMPUS_SECURITY_CONTRACTOR_MANAGE, "campus_security", "Manage contractor profiles, safety training, and badges"),
    PermissionDefinition(CAMPUS_SECURITY_ACCESS_ZONE_READ, "campus_security", "View security access zones and clearance levels"),
    PermissionDefinition(CAMPUS_SECURITY_ACCESS_ZONE_MANAGE, "campus_security", "Configure security access zones and restrictions"),
    PermissionDefinition(CAMPUS_SECURITY_ACCESS_GRANT_MANAGE, "campus_security", "Grant, extend, or revoke time-limited zone access"),
    PermissionDefinition(CAMPUS_SECURITY_INCIDENT_READ, "campus_security", "View campus physical security incident reports"),
    PermissionDefinition(CAMPUS_SECURITY_INCIDENT_REPORT, "campus_security", "Report physical security incidents or safety hazards"),
    PermissionDefinition(CAMPUS_SECURITY_INCIDENT_MANAGE, "campus_security", "Assign, investigate, escalate, and resolve security incidents"),
    PermissionDefinition(CAMPUS_SECURITY_EMERGENCY_READ, "campus_security", "View active emergency events and coordination workspaces"),
    PermissionDefinition(CAMPUS_SECURITY_EMERGENCY_MANAGE, "campus_security", "Initiate emergency events, dispatch tasks, and post after-action reports"),
    PermissionDefinition(CAMPUS_SECURITY_PATROL_READ, "campus_security", "View security patrol plans and checkpoint logs"),
    PermissionDefinition(CAMPUS_SECURITY_PATROL_MANAGE, "campus_security", "Create patrol routes, record rounds, and review completion"),
    PermissionDefinition(CAMPUS_SECURITY_ANALYTICS_READ, "campus_security", "Access campus security analytics and gate operations dashboards"),

]


# Default System Role Definitions
