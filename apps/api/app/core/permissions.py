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
    PermissionDefinition(ATTENDANCE_APPROVE_CORRECTION, "attendance", "Approve attendance correction"),
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
    PermissionDefinition(EXAMINATIONS_CREATE, "examination", "Create examination cycle and schedules"),
    PermissionDefinition(EXAMINATIONS_UPDATE, "examination", "Update examination schedule and terms"),
    PermissionDefinition(ASSESSMENTS_READ, "examination", "View course assessments and components"),
    PermissionDefinition(ASSESSMENTS_CREATE, "examination", "Create course assessments"),
    PermissionDefinition(ASSESSMENTS_UPDATE, "examination", "Update course assessments and weightage"),
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
    PermissionDefinition(ELIGIBILITY_EVALUATE, "examination", "Evaluate student examination eligibility"),
    PermissionDefinition(ELIGIBILITY_OVERRIDE, "examination", "Override examination eligibility restrictions"),
    PermissionDefinition(FINANCE_STRUCTURES_MANAGE, "finance", "Configure fee structures"),
    PermissionDefinition(FINANCE_INVOICES_READ, "finance", "View student invoices and ledgers"),
    PermissionDefinition(FINANCE_INVOICES_CREATE, "finance", "Generate student billing invoices"),
    PermissionDefinition(FINANCE_PAYMENTS_RECORD, "finance", "Record manual payment collections"),
    PermissionDefinition(FINANCE_PAYMENTS_PAY_SELF, "finance", "Pay personal fees via gateway"),
    PermissionDefinition(FINANCE_REFUNDS_APPROVE, "finance", "Authorize fee refunds & adjustments"),
    PermissionDefinition(FINANCE_REPORTS_READ, "finance", "Access financial billing analytics"),
    # Step 8 Granular Suite
    PermissionDefinition(FINANCE_READ, "finance", "View institutional billing and financial state"),
    PermissionDefinition(FINANCE_MANAGE_FEE_STRUCTURES, "finance", "Author, approve and activate fee structures"),
    PermissionDefinition(INVOICES_READ, "finance", "View student fee invoices and billing lines"),
    PermissionDefinition(INVOICES_CREATE, "finance", "Generate student invoices from fee assignments"),
    PermissionDefinition(INVOICES_ISSUE, "finance", "Issue draft invoices and commit balances"),
    PermissionDefinition(INVOICES_CANCEL, "finance", "Cancel issued invoices without balance corruption"),
    PermissionDefinition(PAYMENTS_READ, "finance", "Inspect payment transaction records"),
    PermissionDefinition(PAYMENTS_CREATE, "finance", "Record inward student payments"),
    PermissionDefinition(PAYMENTS_CONFIRM, "finance", "Confirm and verify payment transactions"),
    PermissionDefinition(RECEIPTS_READ, "finance", "View and download payment receipts"),
    PermissionDefinition(RECEIPTS_ISSUE, "finance", "Generate and issue official payment receipts"),
    PermissionDefinition(SCHOLARSHIPS_READ, "finance", "View student scholarships, discounts and concessions"),
    PermissionDefinition(SCHOLARSHIPS_CREATE, "finance", "Apply scholarship or fee waiver to student"),
    PermissionDefinition(SCHOLARSHIPS_APPROVE, "finance", "Approve or reject student scholarship grants"),
    PermissionDefinition(ADJUSTMENTS_CREATE, "finance", "Create debit/credit adjustment requests"),
    PermissionDefinition(ADJUSTMENTS_APPROVE, "finance", "Approve financial adjustments on invoices"),
    PermissionDefinition(REFUNDS_CREATE, "finance", "Request fee refund for paid transactions"),
    PermissionDefinition(REFUNDS_APPROVE, "finance", "Authorize fee refund disbursements"),
    PermissionDefinition(REFUNDS_PROCESS, "finance", "Process and disburse approved refunds"),
    # Placement
    PermissionDefinition(PLACEMENT_COMPANIES_READ, "placement", "View recruiting companies directory"),
    PermissionDefinition(PLACEMENT_COMPANIES_MANAGE, "placement", "Manage recruiting directory and contacts"),
    PermissionDefinition(PLACEMENT_DRIVES_READ, "placement", "View campus placement drives"),
    PermissionDefinition(PLACEMENT_DRIVES_MANAGE, "placement", "Schedule and manage job drives"),
    PermissionDefinition(PLACEMENT_POSITIONS_MANAGE, "placement", "Create and manage job positions and eligibility rules"),
    PermissionDefinition(PLACEMENT_ELIGIBILITY_EVALUATE, "placement", "Run automated eligibility evaluations for students"),
    PermissionDefinition(PLACEMENT_APPLY_SELF, "placement", "Apply for placement positions"),
    PermissionDefinition(PLACEMENT_APPLICATIONS_READ, "placement", "View placement applications"),
    PermissionDefinition(PLACEMENT_APPLICATIONS_REVIEW, "placement", "Review and shortlist applicant applications"),
    PermissionDefinition(PLACEMENT_INTERVIEWS_MANAGE, "placement", "Schedule interview rounds and slots"),
    PermissionDefinition(PLACEMENT_INTERVIEWS_EVALUATE, "placement", "Submit interview evaluations and ratings"),
    PermissionDefinition(PLACEMENT_OFFERS_READ, "placement", "View extended placement offers"),
    PermissionDefinition(PLACEMENT_OFFERS_MANAGE, "placement", "Log and issue job offers"),
    PermissionDefinition(PLACEMENT_OFFERS_RESPOND, "placement", "Accept or decline personal placement offers"),
    PermissionDefinition(PLACEMENT_OUTCOMES_MANAGE, "placement", "Record institutional placement outcomes"),
    PermissionDefinition(PLACEMENT_ANALYTICS_READ, "placement", "Access placement statistics and CTC analytics"),
    PermissionDefinition(PLACEMENT_PROFILE_READ, "placement", "View student placement profile"),
    PermissionDefinition(PLACEMENT_PROFILE_UPDATE, "placement", "Update student placement profile and resume"),
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
    PermissionDefinition(EVENTS_MANAGE_ATTENDANCE, "events", "Record and supervise event check-in and attendance"),
    PermissionDefinition(EVENTS_MANAGE_REGISTRATIONS, "events", "Manage and review event participant registrations"),
    PermissionDefinition(EVENTS_SELF_REGISTER, "events", "Register self for open campus events"),
    PermissionDefinition(EVENTS_SELF_MANAGE_REGISTRATION, "events", "View and cancel personal event registrations"),
    # Campus Clubs
    PermissionDefinition(CLUBS_READ, "clubs", "View campus student clubs and organizations"),
    PermissionDefinition(CLUBS_CREATE, "clubs", "Found or propose new student clubs"),
    PermissionDefinition(CLUBS_UPDATE, "clubs", "Update club information and metadata"),
    PermissionDefinition(CLUBS_APPROVE, "clubs", "Approve proposed student clubs"),
    PermissionDefinition(CLUBS_MANAGE_MEMBERSHIPS, "clubs", "Review and manage club membership rosters and roles"),
    PermissionDefinition(CLUBS_SELF_READ, "clubs", "View club directory and activities"),
    PermissionDefinition(CLUBS_SELF_REQUEST_MEMBERSHIP, "clubs", "Submit membership requests to student clubs"),
    PermissionDefinition(CLUBS_SELF_MANAGE_MEMBERSHIP, "clubs", "Manage personal club membership and resignation"),
    # Campus Announcements
    PermissionDefinition(ANNOUNCEMENTS_READ, "announcements", "Read institutional and targeted announcements"),
    PermissionDefinition(ANNOUNCEMENTS_CREATE, "announcements", "Draft and author campus announcements"),
    PermissionDefinition(ANNOUNCEMENTS_UPDATE, "announcements", "Update draft and scheduled announcements"),
    PermissionDefinition(ANNOUNCEMENTS_PUBLISH, "announcements", "Broadcast announcements to target audiences"),
    PermissionDefinition(ANNOUNCEMENTS_ARCHIVE, "announcements", "Archive or expire outdated announcements"),
    # Notifications
    PermissionDefinition(NOTIFICATIONS_READ, "notifications", "Read system and institutional notifications"),
    PermissionDefinition(NOTIFICATIONS_MANAGE, "notifications", "Administer notification delivery channels and dispatch"),
    PermissionDefinition(NOTIFICATIONS_MANAGE_PREFERENCES, "notifications", "Manage user notification channel preferences"),
    PermissionDefinition(NOTIFICATIONS_SELF_READ, "notifications", "Read personal notification inbox"),
    PermissionDefinition(NOTIFICATIONS_SELF_MANAGE_PREFERENCES, "notifications", "Configure personal notification preferences"),
]


# Default System Role Definitions
DEFAULT_ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "SUPER_ADMIN": [p.code for p in ALL_PERMISSIONS],
    "INSTITUTION_ADMIN": [
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
    ],
    "FACULTY": [
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
    ],
    "STUDENT": [
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
    ],
}
