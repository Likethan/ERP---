"""CampusOS Enterprise Domain Events and Transactional Outbox Engine (Step 27).

Enforces:
- Central registry of validated, versioned domain events with schema versioning
- Strict payload sanitization (minimal metadata and identifiers only, no PII/secrets)
- Transactional Outbox pattern: events are recorded atomically in the active DB transaction
- Safe concurrency locking with FOR UPDATE SKIP LOCKED on supported engines
- Bounded jittered exponential backoff and dead-letter routing
- Durable per-consumer idempotency and replay capabilities
"""

import logging
import random
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.event import (
    ConsumerCheckpointStatus,
    EventConsumerCheckpoint,
    EventDeadLetter,
)
from app.models.workflow import OutboxEvent, OutboxEventStatus

logger = logging.getLogger("campusos.events")

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|secret|token|api_key|card|cvv|credit|credential|auth_token|refresh_token|private_key|salt|pin)",
    re.IGNORECASE,
)


class DomainEventType(StrEnum):
    """Central Allowlist of Trusted CampusOS Domain Events."""

    STUDENT_CREATED = "STUDENT_CREATED"
    STUDENT_ENROLLED = "STUDENT_ENROLLED"
    ATTENDANCE_THRESHOLD_REACHED = "ATTENDANCE_THRESHOLD_REACHED"
    ATTENDANCE_MARKED = "ATTENDANCE_MARKED"
    EXAM_RESULT_PUBLISHED = "EXAM_RESULT_PUBLISHED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    INVOICE_OVERDUE = "INVOICE_OVERDUE"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    DOCUMENT_EXPIRY_APPROACHING = "DOCUMENT_EXPIRY_APPROACHING"
    DOCUMENT_EXPIRED = "DOCUMENT_EXPIRED"
    PLACEMENT_DRIVE_OPENED = "PLACEMENT_DRIVE_OPENED"
    PLACEMENT_OFFER_ACCEPTED = "PLACEMENT_OFFER_ACCEPTED"
    EVENT_REGISTERED = "EVENT_REGISTERED"
    HOSTEL_ALLOCATION_CREATED = "HOSTEL_ALLOCATION_CREATED"
    HOSTEL_APPLICATION_SUBMITTED = "HOSTEL_APPLICATION_SUBMITTED"
    HOSTEL_APPLICATION_APPROVED = "HOSTEL_APPLICATION_APPROVED"
    HOSTEL_RESIDENT_CHECKED_IN = "HOSTEL_RESIDENT_CHECKED_IN"
    HOSTEL_RESIDENT_CHECKED_OUT = "HOSTEL_RESIDENT_CHECKED_OUT"
    HOSTEL_OUTING_OVERDUE = "HOSTEL_OUTING_OVERDUE"
    HOSTEL_INCIDENT_REPORTED = "HOSTEL_INCIDENT_REPORTED"
    HOSTEL_SERVICE_REQUEST_CREATED = "HOSTEL_SERVICE_REQUEST_CREATED"
    # Step 55: Enterprise Transport, Fleet, Routes & Student Mobility Management
    TRANSPORT_APPLICATION_SUBMITTED = "TRANSPORT_APPLICATION_SUBMITTED"
    TRANSPORT_APPLICATION_APPROVED = "TRANSPORT_APPLICATION_APPROVED"
    TRANSPORT_ALLOCATION_CONFIRMED = "TRANSPORT_ALLOCATION_CONFIRMED"
    TRANSPORT_ALLOCATION_CANCELLED = "TRANSPORT_ALLOCATION_CANCELLED"
    TRANSPORT_TRIP_DISPATCHED = "TRANSPORT_TRIP_DISPATCHED"
    TRANSPORT_TRIP_COMPLETED = "TRANSPORT_TRIP_COMPLETED"
    TRANSPORT_TRIP_CANCELLED = "TRANSPORT_TRIP_CANCELLED"
    TRANSPORT_TRIP_DELAYED = "TRANSPORT_TRIP_DELAYED"
    TRANSPORT_BOARDING_RECORDED = "TRANSPORT_BOARDING_RECORDED"
    TRANSPORT_INCIDENT_REPORTED = "TRANSPORT_INCIDENT_REPORTED"
    TRANSPORT_COMPLIANCE_EXPIRING = "TRANSPORT_COMPLIANCE_EXPIRING"
    TRANSPORT_VEHICLE_MAINTENANCE_REQUIRED = "TRANSPORT_VEHICLE_MAINTENANCE_REQUIRED"
    # Step 57: Enterprise Sports, Athletics, Recreation & Student Fitness Management
    SPORTS_FACILITY_BOOKED = "SPORTS_FACILITY_BOOKED"
    SPORTS_FACILITY_MAINTENANCE_CLOSED = "SPORTS_FACILITY_MAINTENANCE_CLOSED"
    SPORTS_PARTICIPANT_REGISTERED = "SPORTS_PARTICIPANT_REGISTERED"
    SPORTS_TEAM_CREATED = "SPORTS_TEAM_CREATED"
    SPORTS_TEAM_ROSTER_UPDATED = "SPORTS_TEAM_ROSTER_UPDATED"
    SPORTS_TRAINING_SCHEDULED = "SPORTS_TRAINING_SCHEDULED"
    SPORTS_COMPETITION_ANNOUNCED = "SPORTS_COMPETITION_ANNOUNCED"
    SPORTS_COMPETITION_REGISTERED = "SPORTS_COMPETITION_REGISTERED"
    SPORTS_FIXTURE_SCHEDULED = "SPORTS_FIXTURE_SCHEDULED"
    SPORTS_MATCH_RESULT_RECORDED = "SPORTS_MATCH_RESULT_RECORDED"
    SPORTS_MATCH_RESULT_VERIFIED = "SPORTS_MATCH_RESULT_VERIFIED"
    SPORTS_EQUIPMENT_CHECKED_OUT = "SPORTS_EQUIPMENT_CHECKED_OUT"
    SPORTS_EQUIPMENT_RETURNED = "SPORTS_EQUIPMENT_RETURNED"
    FINANCE_PAYMENT_FAILED = "FINANCE_PAYMENT_FAILED"
    PLACEMENT_INTERVIEW_SCHEDULED = "PLACEMENT_INTERVIEW_SCHEDULED"
    DOCUMENTS_VERIFICATION_COMPLETED = "DOCUMENTS_VERIFICATION_COMPLETED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    CAMPUS_EVENT_UPDATED = "CAMPUS_EVENT_UPDATED"
    WORKFLOW_TASK_ASSIGNED = "WORKFLOW_TASK_ASSIGNED"
    WORKFLOW_SLA_BREACHED = "WORKFLOW_SLA_BREACHED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_COMPLETED = "CASE_COMPLETED"
    NOTIFICATION_DELIVERY_FAILED = "NOTIFICATION_DELIVERY_FAILED"
    # Step 30: Enterprise Platform Operations
    TENANT_LIFECYCLE_TRANSITIONED = "TENANT_LIFECYCLE_TRANSITIONED"
    TENANT_PROVISIONING_COMPLETED = "TENANT_PROVISIONING_COMPLETED"
    TENANT_QUOTA_THRESHOLD_WARNING = "TENANT_QUOTA_THRESHOLD_WARNING"
    # Step 59: Enterprise Student Counselling, Mentoring & Personal Development
    STUDENT_MENTOR_ASSIGNED = "STUDENT_MENTOR_ASSIGNED"
    STUDENT_MENTOR_REASSIGNED = "STUDENT_MENTOR_REASSIGNED"
    MENTORING_SESSION_SCHEDULED = "MENTORING_SESSION_SCHEDULED"
    MENTORING_SESSION_COMPLETED = "MENTORING_SESSION_COMPLETED"
    COUNSELLING_APPOINTMENT_REQUESTED = "COUNSELLING_APPOINTMENT_REQUESTED"
    COUNSELLING_APPOINTMENT_CONFIRMED = "COUNSELLING_APPOINTMENT_CONFIRMED"
    COUNSELLING_APPOINTMENT_RESCHEDULED = "COUNSELLING_APPOINTMENT_RESCHEDULED"
    COUNSELLING_APPOINTMENT_CANCELLED = "COUNSELLING_APPOINTMENT_CANCELLED"
    DEVELOPMENT_PLAN_CREATED = "DEVELOPMENT_PLAN_CREATED"
    DEVELOPMENT_GOAL_COMPLETED = "DEVELOPMENT_GOAL_COMPLETED"
    SUPPORT_REFERRAL_DISPATCHED = "SUPPORT_REFERRAL_DISPATCHED"
    SUPPORT_REFERRAL_STATUS_UPDATED = "SUPPORT_REFERRAL_STATUS_UPDATED"
    SUPPORT_FOLLOWUP_REMINDER = "SUPPORT_FOLLOWUP_REMINDER"
    # Step 60: Enterprise International Relations, Student Exchange & Global Mobility
    INTERNATIONAL_PARTNER_REGISTERED = "INTERNATIONAL_PARTNER_REGISTERED"
    AGREEMENT_STATUS_CHANGED = "AGREEMENT_STATUS_CHANGED"
    AGREEMENT_EXPIRY_WARNING = "AGREEMENT_EXPIRY_WARNING"
    MOBILITY_PROGRAM_PUBLISHED = "MOBILITY_PROGRAM_PUBLISHED"
    MOBILITY_APPLICATION_SUBMITTED = "MOBILITY_APPLICATION_SUBMITTED"
    MOBILITY_APPLICATION_REVIEWED = "MOBILITY_APPLICATION_REVIEWED"
    MOBILITY_APPLICATION_NOMINATED = "MOBILITY_APPLICATION_NOMINATED"
    MOBILITY_PARTNER_DECISION_RECORDED = "MOBILITY_PARTNER_DECISION_RECORDED"
    INBOUND_STUDENT_CHECKED_IN = "INBOUND_STUDENT_CHECKED_IN"
    FACULTY_MOBILITY_APPROVED = "FACULTY_MOBILITY_APPROVED"
    CREDIT_TRANSFER_APPROVED = "CREDIT_TRANSFER_APPROVED"
    MOBILITY_DOCUMENT_VERIFIED = "MOBILITY_DOCUMENT_VERIFIED"
    MOBILITY_FUNDING_APPROVED = "MOBILITY_FUNDING_APPROVED"


@dataclass(frozen=True)
class EventDefinition:
    event_type: DomainEventType
    aggregate_type: str
    description: str
    source_module: str
    allowed_payload_keys: frozenset[str]
    schema_version: str = "1.0"
    retention_days: int = 90
    is_external_publishable: bool = False
    registered_consumers: list[str] = field(default_factory=list)


# Central Event Registry mapping each event type to metadata definition
EVENT_REGISTRY: dict[DomainEventType, EventDefinition] = {
    DomainEventType.STUDENT_CREATED: EventDefinition(
        event_type=DomainEventType.STUDENT_CREATED,
        aggregate_type="Student",
        description="Emitted when a new student profile is registered.",
        source_module="people",
        allowed_payload_keys=frozenset(
            {"student_id", "enrollment_number", "department_id", "program_id", "batch_year"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.STUDENT_ENROLLED: EventDefinition(
        event_type=DomainEventType.STUDENT_ENROLLED,
        aggregate_type="Enrollment",
        description="Emitted when a student is formally enrolled in an academic program/course.",
        source_module="academics",
        allowed_payload_keys=frozenset(
            {"student_id", "course_id", "section_id", "semester", "academic_year_id"}
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.ATTENDANCE_THRESHOLD_REACHED: EventDefinition(
        event_type=DomainEventType.ATTENDANCE_THRESHOLD_REACHED,
        aggregate_type="AttendanceSummary",
        description="Emitted when attendance drops below configured policy thresholds.",
        source_module="attendance",
        allowed_payload_keys=frozenset(
            {
                "student_id",
                "course_id",
                "percentage",
                "threshold",
                "classes_attended",
                "total_classes",
            }
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.ATTENDANCE_MARKED: EventDefinition(
        event_type=DomainEventType.ATTENDANCE_MARKED,
        aggregate_type="AttendanceSession",
        description="Emitted when faculty marks an attendance session.",
        source_module="attendance",
        allowed_payload_keys=frozenset(
            {"session_id", "course_id", "section_id", "date", "total_present", "total_absent"}
        ),
        registered_consumers=["AuditTrailConsumer", "NotificationEventConsumer"],
    ),
    DomainEventType.EXAM_RESULT_PUBLISHED: EventDefinition(
        event_type=DomainEventType.EXAM_RESULT_PUBLISHED,
        aggregate_type="Assessment",
        description="Emitted when authorized examination results are finalized and published.",
        source_module="examinations",
        allowed_payload_keys=frozenset(
            {"assessment_id", "course_id", "academic_year_id", "published_by", "student_count"}
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.INVOICE_GENERATED: EventDefinition(
        event_type=DomainEventType.INVOICE_GENERATED,
        aggregate_type="Invoice",
        description="Emitted when a fee invoice is issued to a student.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "total_amount", "due_date", "fee_structure_id"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.INVOICE_OVERDUE: EventDefinition(
        event_type=DomainEventType.INVOICE_OVERDUE,
        aggregate_type="Invoice",
        description="Emitted when an outstanding invoice passes its due date without full payment.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "outstanding_amount", "due_date", "days_overdue"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.PAYMENT_RECEIVED: EventDefinition(
        event_type=DomainEventType.PAYMENT_RECEIVED,
        aggregate_type="Payment",
        description="Emitted when a fee payment is successfully confirmed.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {
                "payment_id",
                "invoice_id",
                "student_id",
                "amount",
                "payment_method",
                "transaction_ref",
            }
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.DOCUMENT_EXPIRY_APPROACHING: EventDefinition(
        event_type=DomainEventType.DOCUMENT_EXPIRY_APPROACHING,
        aggregate_type="Document",
        description="Emitted when a student or staff document is nearing its expiry date.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"document_id", "user_id", "document_type", "expiry_date", "days_until_expiry"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DOCUMENT_EXPIRED: EventDefinition(
        event_type=DomainEventType.DOCUMENT_EXPIRED,
        aggregate_type="Document",
        description="Emitted when a mandatory document has expired.",
        source_module="documents",
        allowed_payload_keys=frozenset({"document_id", "user_id", "document_type", "expiry_date"}),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.PLACEMENT_DRIVE_OPENED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_DRIVE_OPENED,
        aggregate_type="PlacementDrive",
        description="Emitted when a recruitment drive opens for applicant registrations.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"drive_id", "company_name", "role_title", "deadline", "eligible_departments"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.PLACEMENT_OFFER_ACCEPTED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_OFFER_ACCEPTED,
        aggregate_type="PlacementOffer",
        description="Emitted when a student accepts an authorized job offer.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"offer_id", "drive_id", "student_id", "company_name", "ctc"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.EVENT_REGISTERED: EventDefinition(
        event_type=DomainEventType.EVENT_REGISTERED,
        aggregate_type="CampusEventRegistration",
        description="Emitted when a member registers for a campus or club event.",
        source_module="campus",
        allowed_payload_keys=frozenset({"event_id", "user_id", "registration_id", "ticket_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_ALLOCATION_CREATED: EventDefinition(
        event_type=DomainEventType.HOSTEL_ALLOCATION_CREATED,
        aggregate_type="HostelAllocation",
        description="Emitted when a student is allocated a room or bed in a hostel.",
        source_module="residential",
        allowed_payload_keys=frozenset(
            {"allocation_id", "student_id", "hostel_id", "room_id", "bed_number"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_APPLICATION_SUBMITTED: EventDefinition(
        event_type=DomainEventType.HOSTEL_APPLICATION_SUBMITTED,
        aggregate_type="HostelApplication",
        description="Emitted when a student submits an accommodation application.",
        source_module="residential",
        allowed_payload_keys=frozenset({"application_id", "student_id", "cycle_id", "application_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_APPLICATION_APPROVED: EventDefinition(
        event_type=DomainEventType.HOSTEL_APPLICATION_APPROVED,
        aggregate_type="HostelApplication",
        description="Emitted when an accommodation application is approved.",
        source_module="residential",
        allowed_payload_keys=frozenset({"application_id", "student_id", "cycle_id", "reviewer_user_id"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_RESIDENT_CHECKED_IN: EventDefinition(
        event_type=DomainEventType.HOSTEL_RESIDENT_CHECKED_IN,
        aggregate_type="HostelResident",
        description="Emitted when a resident physically completes check-in and inventory handover.",
        source_module="residential",
        allowed_payload_keys=frozenset({"resident_id", "student_id", "hostel_id", "bed_id", "check_in_time"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_RESIDENT_CHECKED_OUT: EventDefinition(
        event_type=DomainEventType.HOSTEL_RESIDENT_CHECKED_OUT,
        aggregate_type="HostelResident",
        description="Emitted when a resident checks out and releases their room/bed.",
        source_module="residential",
        allowed_payload_keys=frozenset({"resident_id", "student_id", "hostel_id", "bed_id", "check_out_time", "checkout_reason"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_OUTING_OVERDUE: EventDefinition(
        event_type=DomainEventType.HOSTEL_OUTING_OVERDUE,
        aggregate_type="HostelLeavePass",
        description="Emitted when a residential student fails to return from an outing by curfew/expected time.",
        source_module="residential",
        allowed_payload_keys=frozenset({"pass_id", "student_id", "hostel_id", "expected_return_time"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_INCIDENT_REPORTED: EventDefinition(
        event_type=DomainEventType.HOSTEL_INCIDENT_REPORTED,
        aggregate_type="HostelIncident",
        description="Emitted when a residential disciplinary or safety incident is recorded.",
        source_module="residential",
        allowed_payload_keys=frozenset({"incident_id", "hostel_id", "severity", "incident_type"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_SERVICE_REQUEST_CREATED: EventDefinition(
        event_type=DomainEventType.HOSTEL_SERVICE_REQUEST_CREATED,
        aggregate_type="HostelComplaint",
        description="Emitted when a student submits a hostel repair or service request ticket.",
        source_module="residential",
        allowed_payload_keys=frozenset({"complaint_id", "student_id", "hostel_id", "room_id", "category", "priority"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    # Step 55 Transport Domain Events
    DomainEventType.TRANSPORT_APPLICATION_SUBMITTED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_APPLICATION_SUBMITTED,
        aggregate_type="TransportApplication",
        description="Emitted when a student submits a transport service subscription application.",
        source_module="transport",
        allowed_payload_keys=frozenset({"application_id", "student_id", "preferred_route_id", "preferred_stop_id", "service_type"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_APPLICATION_APPROVED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_APPLICATION_APPROVED,
        aggregate_type="TransportApplication",
        description="Emitted when an authorized officer approves a student transport application.",
        source_module="transport",
        allowed_payload_keys=frozenset({"application_id", "student_id", "reviewer_user_id"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_ALLOCATION_CONFIRMED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_ALLOCATION_CONFIRMED,
        aggregate_type="TransportAllocation",
        description="Emitted when a seat allocation or transport pass is issued to a passenger.",
        source_module="transport",
        allowed_payload_keys=frozenset({"allocation_id", "student_id", "route_id", "stop_id", "vehicle_id", "pass_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_ALLOCATION_CANCELLED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_ALLOCATION_CANCELLED,
        aggregate_type="TransportAllocation",
        description="Emitted when a transport pass is cancelled or revoked.",
        source_module="transport",
        allowed_payload_keys=frozenset({"allocation_id", "student_id", "route_id", "cancellation_reason"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_TRIP_DISPATCHED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_TRIP_DISPATCHED,
        aggregate_type="TransportTrip",
        description="Emitted when a scheduled transport trip passes pre-trip check and departs depot.",
        source_module="transport",
        allowed_payload_keys=frozenset({"trip_id", "route_id", "vehicle_id", "driver_id", "trip_date", "service_window"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_TRIP_COMPLETED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_TRIP_COMPLETED,
        aggregate_type="TransportTrip",
        description="Emitted when a transit trip successfully completes its itinerary.",
        source_module="transport",
        allowed_payload_keys=frozenset({"trip_id", "route_id", "actual_end_time", "end_odometer_km"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_TRIP_CANCELLED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_TRIP_CANCELLED,
        aggregate_type="TransportTrip",
        description="Emitted when a scheduled transit trip is cancelled.",
        source_module="transport",
        allowed_payload_keys=frozenset({"trip_id", "route_id", "cancellation_reason"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_TRIP_DELAYED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_TRIP_DELAYED,
        aggregate_type="TransportTrip",
        description="Emitted when a transit trip experiences delay or service disruption.",
        source_module="transport",
        allowed_payload_keys=frozenset({"trip_id", "route_id", "delay_minutes", "disruption_notes"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_BOARDING_RECORDED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_BOARDING_RECORDED,
        aggregate_type="TransportBoardingRecord",
        description="Emitted when student boarding or drop-off is scanned and verified.",
        source_module="transport",
        allowed_payload_keys=frozenset({"record_id", "trip_id", "student_id", "stop_id", "boarding_status", "verification_method"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_INCIDENT_REPORTED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_INCIDENT_REPORTED,
        aggregate_type="TransportIncident",
        description="Emitted when an in-transit breakdown, collision, or passenger incident is logged.",
        source_module="transport",
        allowed_payload_keys=frozenset({"incident_id", "incident_number", "trip_id", "severity", "incident_type"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_COMPLIANCE_EXPIRING: EventDefinition(
        event_type=DomainEventType.TRANSPORT_COMPLIANCE_EXPIRING,
        aggregate_type="TransportVehicle",
        description="Emitted when a vehicle's fitness, insurance, or permit is approaching expiration.",
        source_module="transport",
        allowed_payload_keys=frozenset({"vehicle_id", "registration_number", "document_type", "expiry_date"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.TRANSPORT_VEHICLE_MAINTENANCE_REQUIRED: EventDefinition(
        event_type=DomainEventType.TRANSPORT_VEHICLE_MAINTENANCE_REQUIRED,
        aggregate_type="TransportVehicle",
        description="Emitted when a vehicle fails pre-trip safety checks or reports defects.",
        source_module="transport",
        allowed_payload_keys=frozenset({"vehicle_id", "registration_number", "defect_notes", "work_order_id"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    # Step 57 Sports & Athletics Domain Events
    DomainEventType.SPORTS_FACILITY_BOOKED: EventDefinition(
        event_type=DomainEventType.SPORTS_FACILITY_BOOKED,
        aggregate_type="FacilityBooking",
        description="Emitted when a campus sports facility, ground, or court is reserved.",
        source_module="sports",
        allowed_payload_keys=frozenset({"booking_id", "facility_id", "booking_date", "start_time", "end_time", "booking_type"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_FACILITY_MAINTENANCE_CLOSED: EventDefinition(
        event_type=DomainEventType.SPORTS_FACILITY_MAINTENANCE_CLOSED,
        aggregate_type="SportsFacility",
        description="Emitted when a facility or court is placed under maintenance closure.",
        source_module="sports",
        allowed_payload_keys=frozenset({"facility_id", "facility_code", "maintenance_notes"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_PARTICIPANT_REGISTERED: EventDefinition(
        event_type=DomainEventType.SPORTS_PARTICIPANT_REGISTERED,
        aggregate_type="SportsParticipant",
        description="Emitted when a student or staff member registers as a sports participant.",
        source_module="sports",
        allowed_payload_keys=frozenset({"participant_id", "student_id", "primary_sport", "clearance_status"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_TEAM_CREATED: EventDefinition(
        event_type=DomainEventType.SPORTS_TEAM_CREATED,
        aggregate_type="SportsTeam",
        description="Emitted when a new institutional sports team is created.",
        source_module="sports",
        allowed_payload_keys=frozenset({"team_id", "team_name", "sport", "division"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_TEAM_ROSTER_UPDATED: EventDefinition(
        event_type=DomainEventType.SPORTS_TEAM_ROSTER_UPDATED,
        aggregate_type="TeamMembership",
        description="Emitted when an athlete is added, transferred, or updated on a team roster.",
        source_module="sports",
        allowed_payload_keys=frozenset({"membership_id", "team_id", "participant_id", "role", "jersey_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_TRAINING_SCHEDULED: EventDefinition(
        event_type=DomainEventType.SPORTS_TRAINING_SCHEDULED,
        aggregate_type="TrainingSession",
        description="Emitted when a training session or fitness clinic is scheduled.",
        source_module="sports",
        allowed_payload_keys=frozenset({"session_id", "program_id", "facility_id", "session_date"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_COMPETITION_ANNOUNCED: EventDefinition(
        event_type=DomainEventType.SPORTS_COMPETITION_ANNOUNCED,
        aggregate_type="Competition",
        description="Emitted when a tournament or sports meet opens for participant registrations.",
        source_module="sports",
        allowed_payload_keys=frozenset({"competition_id", "competition_name", "sport", "format", "registration_deadline"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_COMPETITION_REGISTERED: EventDefinition(
        event_type=DomainEventType.SPORTS_COMPETITION_REGISTERED,
        aggregate_type="CompetitionRegistration",
        description="Emitted when a team or individual registers for a tournament.",
        source_module="sports",
        allowed_payload_keys=frozenset({"registration_id", "competition_id", "team_id", "registration_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_FIXTURE_SCHEDULED: EventDefinition(
        event_type=DomainEventType.SPORTS_FIXTURE_SCHEDULED,
        aggregate_type="MatchFixture",
        description="Emitted when tournament match fixtures are generated and scheduled.",
        source_module="sports",
        allowed_payload_keys=frozenset({"match_id", "competition_id", "match_number", "facility_id", "match_date"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_MATCH_RESULT_RECORDED: EventDefinition(
        event_type=DomainEventType.SPORTS_MATCH_RESULT_RECORDED,
        aggregate_type="MatchResult",
        description="Emitted when match scores are entered and saved.",
        source_module="sports",
        allowed_payload_keys=frozenset({"result_id", "match_id", "home_score", "away_score", "outcome"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_MATCH_RESULT_VERIFIED: EventDefinition(
        event_type=DomainEventType.SPORTS_MATCH_RESULT_VERIFIED,
        aggregate_type="MatchResult",
        description="Emitted when match results are verified and standings are updated.",
        source_module="sports",
        allowed_payload_keys=frozenset({"result_id", "match_id", "verified_by_user_id", "outcome"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_EQUIPMENT_CHECKED_OUT: EventDefinition(
        event_type=DomainEventType.SPORTS_EQUIPMENT_CHECKED_OUT,
        aggregate_type="EquipmentAssignment",
        description="Emitted when sports equipment or gear is checked out.",
        source_module="sports",
        allowed_payload_keys=frozenset({"assignment_id", "item_name", "quantity", "due_date"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SPORTS_EQUIPMENT_RETURNED: EventDefinition(
        event_type=DomainEventType.SPORTS_EQUIPMENT_RETURNED,
        aggregate_type="EquipmentAssignment",
        description="Emitted when sports equipment is returned and condition inspected.",
        source_module="sports",
        allowed_payload_keys=frozenset({"assignment_id", "item_name", "condition_on_return", "status"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.FINANCE_PAYMENT_FAILED: EventDefinition(
        event_type=DomainEventType.FINANCE_PAYMENT_FAILED,
        aggregate_type="Payment",
        description="Emitted when a payment transaction fails or is rejected.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "amount", "failure_reason", "transaction_ref"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED,
        aggregate_type="InterviewSchedule",
        description="Emitted when an interview slot is confirmed for a candidate.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"drive_id", "student_id", "company_name", "interview_time", "venue"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED: EventDefinition(
        event_type=DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED,
        aggregate_type="DocumentVerification",
        description="Emitted when document verification review completes.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"document_id", "user_id", "document_type", "verified_by", "status"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.CERTIFICATE_ISSUED: EventDefinition(
        event_type=DomainEventType.CERTIFICATE_ISSUED,
        aggregate_type="IssuedCertificate",
        description="Emitted when an official student certificate is issued.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"certificate_id", "student_id", "certificate_type", "certificate_number", "issued_at"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.CAMPUS_EVENT_UPDATED: EventDefinition(
        event_type=DomainEventType.CAMPUS_EVENT_UPDATED,
        aggregate_type="CampusEvent",
        description="Emitted when campus event schedule, status, or details change.",
        source_module="campus",
        allowed_payload_keys=frozenset({"event_id", "title", "start_at", "venue_name", "status"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.WORKFLOW_TASK_ASSIGNED: EventDefinition(
        event_type=DomainEventType.WORKFLOW_TASK_ASSIGNED,
        aggregate_type="HumanTask",
        description="Emitted when an operational workflow or case task is assigned to an actor.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"task_id", "case_id", "assigned_user_id", "task_title", "due_at"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.WORKFLOW_SLA_BREACHED: EventDefinition(
        event_type=DomainEventType.WORKFLOW_SLA_BREACHED,
        aggregate_type="SlaInstance",
        description="Emitted when an operational task or case breaches its SLA deadline.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"sla_instance_id", "case_id", "task_id", "policy_id", "due_at"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.CASE_ESCALATED: EventDefinition(
        event_type=DomainEventType.CASE_ESCALATED,
        aggregate_type="Case",
        description="Emitted when a case is escalated to higher authority or supervisory queue.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"case_id", "case_number", "assigned_queue_id", "reason", "escalated_by"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.CASE_COMPLETED: EventDefinition(
        event_type=DomainEventType.CASE_COMPLETED,
        aggregate_type="Case",
        description="Emitted when a case or human task workflow is formally completed.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"case_id", "case_number", "resolution", "closed_by", "case_type"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.NOTIFICATION_DELIVERY_FAILED: EventDefinition(
        event_type=DomainEventType.NOTIFICATION_DELIVERY_FAILED,
        aggregate_type="NotificationDelivery",
        description="Emitted when an external notification delivery fails after max attempts.",
        source_module="notifications",
        allowed_payload_keys=frozenset(
            {"delivery_id", "channel", "recipient_id", "failure_reason", "attempt_count"}
        ),
        registered_consumers=["WorkflowEventConsumer", "AuditTrailConsumer"],
    ),
    # Step 30: Enterprise Platform Operations
    DomainEventType.TENANT_LIFECYCLE_TRANSITIONED: EventDefinition(
        event_type=DomainEventType.TENANT_LIFECYCLE_TRANSITIONED,
        aggregate_type="Institution",
        description="Emitted when a tenant lifecycle status transitions.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "tenant_code", "old_status", "new_status", "reason", "actor_id"}
        ),
        registered_consumers=["AuditTrailConsumer"],
    ),
    DomainEventType.TENANT_PROVISIONING_COMPLETED: EventDefinition(
        event_type=DomainEventType.TENANT_PROVISIONING_COMPLETED,
        aggregate_type="Institution",
        description="Emitted when multi-stage tenant provisioning is completed.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "code", "plan", "status"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING: EventDefinition(
        event_type=DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING,
        aggregate_type="TenantResourceQuotaUsage",
        description="Emitted when a tenant resource usage reaches warning threshold.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "resource_type", "current_usage", "soft_limit", "hard_limit", "unit"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    # Step 59: Student Counselling, Mentoring & Personal Development
    DomainEventType.STUDENT_MENTOR_ASSIGNED: EventDefinition(
        event_type=DomainEventType.STUDENT_MENTOR_ASSIGNED,
        aggregate_type="MentorAssignment",
        description="Emitted when a faculty mentor is assigned to a student.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"assignment_id", "student_id", "mentor_user_id", "academic_year"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.STUDENT_MENTOR_REASSIGNED: EventDefinition(
        event_type=DomainEventType.STUDENT_MENTOR_REASSIGNED,
        aggregate_type="MentorAssignment",
        description="Emitted when a student's faculty mentor is reassigned.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"assignment_id", "student_id", "old_mentor_id", "new_mentor_id", "reason"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MENTORING_SESSION_SCHEDULED: EventDefinition(
        event_type=DomainEventType.MENTORING_SESSION_SCHEDULED,
        aggregate_type="MentoringSession",
        description="Emitted when a mentoring session is scheduled.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"session_id", "mentor_user_id", "session_date", "start_time", "session_type"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.MENTORING_SESSION_COMPLETED: EventDefinition(
        event_type=DomainEventType.MENTORING_SESSION_COMPLETED,
        aggregate_type="MentoringSession",
        description="Emitted when a mentoring session is completed.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"session_id", "mentor_user_id", "session_date", "follow_up_date"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.COUNSELLING_APPOINTMENT_REQUESTED: EventDefinition(
        event_type=DomainEventType.COUNSELLING_APPOINTMENT_REQUESTED,
        aggregate_type="CounsellingAppointment",
        description="Emitted when a counselling appointment is requested.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"appointment_id", "student_id", "appointment_date", "category"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.COUNSELLING_APPOINTMENT_CONFIRMED: EventDefinition(
        event_type=DomainEventType.COUNSELLING_APPOINTMENT_CONFIRMED,
        aggregate_type="CounsellingAppointment",
        description="Emitted when a counselling appointment is confirmed.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"appointment_id", "student_id", "counsellor_user_id", "appointment_date", "start_time"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.COUNSELLING_APPOINTMENT_RESCHEDULED: EventDefinition(
        event_type=DomainEventType.COUNSELLING_APPOINTMENT_RESCHEDULED,
        aggregate_type="CounsellingAppointment",
        description="Emitted when a counselling appointment is rescheduled.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"appointment_id", "student_id", "appointment_date", "start_time"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.COUNSELLING_APPOINTMENT_CANCELLED: EventDefinition(
        event_type=DomainEventType.COUNSELLING_APPOINTMENT_CANCELLED,
        aggregate_type="CounsellingAppointment",
        description="Emitted when a counselling appointment is cancelled.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"appointment_id", "student_id", "cancellation_reason"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DEVELOPMENT_PLAN_CREATED: EventDefinition(
        event_type=DomainEventType.DEVELOPMENT_PLAN_CREATED,
        aggregate_type="StudentDevelopmentPlan",
        description="Emitted when an individual student development plan is initiated.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"plan_id", "student_id", "academic_year"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DEVELOPMENT_GOAL_COMPLETED: EventDefinition(
        event_type=DomainEventType.DEVELOPMENT_GOAL_COMPLETED,
        aggregate_type="DevelopmentGoal",
        description="Emitted when a development milestone or goal is completed.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"goal_id", "plan_id", "category", "title"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SUPPORT_REFERRAL_DISPATCHED: EventDefinition(
        event_type=DomainEventType.SUPPORT_REFERRAL_DISPATCHED,
        aggregate_type="SupportReferral",
        description="Emitted when a referral is dispatched to an institutional support service.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"referral_id", "referral_code", "student_id", "target_service", "priority"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.SUPPORT_REFERRAL_STATUS_UPDATED: EventDefinition(
        event_type=DomainEventType.SUPPORT_REFERRAL_STATUS_UPDATED,
        aggregate_type="SupportReferral",
        description="Emitted when a support referral status changes.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"referral_id", "status", "assigned_staff_user_id"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.SUPPORT_FOLLOWUP_REMINDER: EventDefinition(
        event_type=DomainEventType.SUPPORT_FOLLOWUP_REMINDER,
        aggregate_type="SupportFollowUp",
        description="Emitted when a support follow-up check is due.",
        source_module="student_support",
        allowed_payload_keys=frozenset({"followup_id", "assigned_user_id", "due_date", "title"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    # Step 60: Enterprise International Relations, Student Exchange & Global Mobility
    DomainEventType.INTERNATIONAL_PARTNER_REGISTERED: EventDefinition(
        event_type=DomainEventType.INTERNATIONAL_PARTNER_REGISTERED,
        aggregate_type="InternationalPartner",
        description="Emitted when a new international partner institution or university is registered.",
        source_module="international",
        allowed_payload_keys=frozenset({"partner_id", "institution_name", "country", "category"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.AGREEMENT_STATUS_CHANGED: EventDefinition(
        event_type=DomainEventType.AGREEMENT_STATUS_CHANGED,
        aggregate_type="InstitutionalAgreement",
        description="Emitted when an MoU or international agreement status transitions.",
        source_module="international",
        allowed_payload_keys=frozenset({"agreement_id", "agreement_number", "partner_id", "old_status", "new_status"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.AGREEMENT_EXPIRY_WARNING: EventDefinition(
        event_type=DomainEventType.AGREEMENT_EXPIRY_WARNING,
        aggregate_type="InstitutionalAgreement",
        description="Emitted when an agreement is nearing its expiration date.",
        source_module="international",
        allowed_payload_keys=frozenset({"agreement_id", "agreement_number", "partner_name", "expiry_date", "days_remaining"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.MOBILITY_PROGRAM_PUBLISHED: EventDefinition(
        event_type=DomainEventType.MOBILITY_PROGRAM_PUBLISHED,
        aggregate_type="MobilityProgram",
        description="Emitted when an exchange or study-abroad program opens for student applications.",
        source_module="international",
        allowed_payload_keys=frozenset({"program_id", "program_code", "title", "partner_id", "deadline"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.MOBILITY_APPLICATION_SUBMITTED: EventDefinition(
        event_type=DomainEventType.MOBILITY_APPLICATION_SUBMITTED,
        aggregate_type="MobilityApplication",
        description="Emitted when a student submits an international exchange application.",
        source_module="international",
        allowed_payload_keys=frozenset({"application_id", "application_number", "student_id", "program_id"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MOBILITY_APPLICATION_REVIEWED: EventDefinition(
        event_type=DomainEventType.MOBILITY_APPLICATION_REVIEWED,
        aggregate_type="MobilityApplication",
        description="Emitted when a mobility application completes a review stage.",
        source_module="international",
        allowed_payload_keys=frozenset({"application_id", "reviewer_id", "stage", "action", "status"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MOBILITY_APPLICATION_NOMINATED: EventDefinition(
        event_type=DomainEventType.MOBILITY_APPLICATION_NOMINATED,
        aggregate_type="MobilityApplication",
        description="Emitted when an approved student is nominated to a partner institution.",
        source_module="international",
        allowed_payload_keys=frozenset({"application_id", "partner_id", "nomination_date", "student_id"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MOBILITY_PARTNER_DECISION_RECORDED: EventDefinition(
        event_type=DomainEventType.MOBILITY_PARTNER_DECISION_RECORDED,
        aggregate_type="MobilityApplication",
        description="Emitted when a partner institution's admission decision is recorded.",
        source_module="international",
        allowed_payload_keys=frozenset({"application_id", "decision", "partner_id"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.INBOUND_STUDENT_CHECKED_IN: EventDefinition(
        event_type=DomainEventType.INBOUND_STUDENT_CHECKED_IN,
        aggregate_type="InboundStudentProfile",
        description="Emitted when an inbound international exchange student completes arrival check-in.",
        source_module="international",
        allowed_payload_keys=frozenset({"inbound_id", "student_name", "partner_id", "host_department_id"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.FACULTY_MOBILITY_APPROVED: EventDefinition(
        event_type=DomainEventType.FACULTY_MOBILITY_APPROVED,
        aggregate_type="FacultyMobilityRecord",
        description="Emitted when faculty mobility or visiting scholar request is approved.",
        source_module="international",
        allowed_payload_keys=frozenset({"mobility_id", "staff_user_id", "mobility_type", "partner_id"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.CREDIT_TRANSFER_APPROVED: EventDefinition(
        event_type=DomainEventType.CREDIT_TRANSFER_APPROVED,
        aggregate_type="StudentCreditTransferRequest",
        description="Emitted when academic credit transfer is officially authorized by the committee.",
        source_module="international",
        allowed_payload_keys=frozenset({"transfer_id", "student_id", "approved_credits", "committee_ref"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MOBILITY_DOCUMENT_VERIFIED: EventDefinition(
        event_type=DomainEventType.MOBILITY_DOCUMENT_VERIFIED,
        aggregate_type="MobilityDocument",
        description="Emitted when a mandatory mobility document or passport reference is verified.",
        source_module="international",
        allowed_payload_keys=frozenset({"document_id", "document_type", "status", "verified_by"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.MOBILITY_FUNDING_APPROVED: EventDefinition(
        event_type=DomainEventType.MOBILITY_FUNDING_APPROVED,
        aggregate_type="MobilityFundingRequest",
        description="Emitted when a student travel grant or mobility scholarship allocation is approved.",
        source_module="international",
        allowed_payload_keys=frozenset({"request_id", "student_id", "approved_amount", "scholarship_id"}),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
}

# Standard dot-notation aliases mapping to canonical DomainEventType
EVENT_ALIAS_MAP: dict[str, DomainEventType] = {
    # Step 27 Canonical Event Names
    "student.enrollment.created": DomainEventType.STUDENT_ENROLLED,
    "attendance.session.finalized": DomainEventType.ATTENDANCE_MARKED,
    "examination.results.published": DomainEventType.EXAM_RESULT_PUBLISHED,
    "finance.payment.confirmed": DomainEventType.PAYMENT_RECEIVED,
    "placement.offer.created": DomainEventType.PLACEMENT_OFFER_ACCEPTED,
    "document.certificate.issued": DomainEventType.CERTIFICATE_ISSUED,
    "workflow.case.completed": DomainEventType.CASE_COMPLETED,
    "notification.delivery.failed": DomainEventType.NOTIFICATION_DELIVERY_FAILED,
    # Step 30 Platform Operations
    "tenant.lifecycle.transitioned": DomainEventType.TENANT_LIFECYCLE_TRANSITIONED,
    "tenant.provisioning.completed": DomainEventType.TENANT_PROVISIONING_COMPLETED,
    "tenant.quota.threshold_warning": DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING,
    # Backwards-compatible aliases
    "attendance.low_threshold": DomainEventType.ATTENDANCE_THRESHOLD_REACHED,
    "examination.result.published": DomainEventType.EXAM_RESULT_PUBLISHED,
    "finance.invoice.issued": DomainEventType.INVOICE_GENERATED,
    "finance.payment.received": DomainEventType.PAYMENT_RECEIVED,
    "finance.payment.failed": DomainEventType.FINANCE_PAYMENT_FAILED,
    "placement.interview.scheduled": DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED,
    "placement.offer.received": DomainEventType.PLACEMENT_OFFER_ACCEPTED,
    "documents.verification.completed": DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED,
    "documents.expiry.warning": DomainEventType.DOCUMENT_EXPIRY_APPROACHING,
    "campus.event.updated": DomainEventType.CAMPUS_EVENT_UPDATED,
    "workflow.task.assigned": DomainEventType.WORKFLOW_TASK_ASSIGNED,
    "workflow.sla.breached": DomainEventType.WORKFLOW_SLA_BREACHED,
    "case.escalated": DomainEventType.CASE_ESCALATED,
}


@dataclass
class DomainEventEnvelope:
    """Standard, versioned domain event envelope contract."""

    event_id: UUID
    event_type: str
    schema_version: str = "1.0"
    tenant_id: UUID | None = None
    aggregate_type: str = ""
    aggregate_id: UUID | str = ""
    event_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    actor_id: UUID | None = None
    actor_context: dict[str, Any] | None = None
    producer: str = "CAMPUSOS_CORE"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": str(self.aggregate_id) if self.aggregate_id else None,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_context": self.actor_context or {},
            "producer": self.producer,
            "payload": self.payload,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_outbox_event(cls, event: OutboxEvent) -> "DomainEventEnvelope":
        return cls(
            event_id=event.id,
            event_type=event.event_type,
            schema_version=getattr(event, "schema_version", "1.0") or "1.0",
            tenant_id=event.tenant_id,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            event_timestamp=event.created_at,
            correlation_id=event.correlation_id,
            causation_id=getattr(event, "causation_id", None),
            actor_id=getattr(event, "actor_id", None),
            actor_context=getattr(event, "actor_context", None) or {},
            producer=getattr(event, "producer", "CAMPUSOS_CORE") or "CAMPUSOS_CORE",
            payload=event.payload or {},
            metadata=getattr(event, "metadata_json", None) or {},
        )

    @classmethod
    def create(
        cls,
        event_type: str,
        tenant_id: UUID | None = None,
        aggregate_type: str = "",
        aggregate_id: UUID | str = "",
        payload: dict[str, Any] | None = None,
        schema_version: str = "1.0",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: UUID | None = None,
        actor_context: dict[str, Any] | None = None,
        producer: str = "CAMPUSOS_PLATFORM_OPS",
        metadata: dict[str, Any] | None = None,
    ) -> "DomainEventEnvelope":
        return cls(
            event_id=uuid4(),
            event_type=event_type,
            schema_version=schema_version,
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            correlation_id=correlation_id or str(uuid4()),
            causation_id=causation_id,
            actor_id=actor_id,
            actor_context=actor_context or {},
            producer=producer,
            metadata=metadata or {},
        )


def validate_schema_version(schema_version: str) -> None:
    """Validate that the schema version is currently supported by the engine."""
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationException(
            f"Unsupported domain event schema version: '{schema_version}'. "
            f"Supported versions: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )


def normalize_event_type(event_type: str) -> DomainEventType:
    """Normalize event type string or dot alias to canonical DomainEventType."""
    if event_type in EVENT_ALIAS_MAP:
        return EVENT_ALIAS_MAP[event_type]
    return DomainEventType(event_type)


def is_valid_event_type(event_type: str) -> bool:
    """Validate that an event type belongs to the explicit allowlist or registered aliases."""
    if event_type in EVENT_ALIAS_MAP:
        return True
    try:
        DomainEventType(event_type)
        return True
    except ValueError:
        return False


def sanitize_event_payload(event_type: str, raw_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize payload to strictly contain only allowlisted non-sensitive fields.

    Discards any credentials, passwords, tokens, or unlisted parameters.
    """
    if not is_valid_event_type(event_type):
        raise ValidationException(f"Unsupported or unregistered domain event type: '{event_type}'")

    canonical_type = normalize_event_type(event_type)
    definition = EVENT_REGISTRY[canonical_type]
    if not raw_payload:
        return {}

    sanitized = {}
    for key, value in raw_payload.items():
        # Reject and omit any key matching sensitive regex
        if SENSITIVE_KEY_PATTERNS.search(key):
            continue
        if key in definition.allowed_payload_keys:
            if isinstance(value, UUID):
                sanitized[key] = str(value)
            elif isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            else:
                sanitized[key] = value

    return sanitized


SENSITIVE_TEXT_PATTERN = re.compile(
    r"(?i)(password|secret|token|api_key|card|cvv|credit|credential|auth_token|refresh_token|private_key|salt|pin)\s*[:=]\s*([^\s,;]+)"
)


def sanitize_error_text(error_text: str | None) -> str:
    """Sanitize error messages to eliminate sensitive credentials or stack details."""
    if not error_text:
        return ""
    cleaned = SENSITIVE_TEXT_PATTERN.sub(r"\1=[REDACTED]", error_text)
    return cleaned[:1000]


class OutboxService:
    """Service for transactional outbox persistence, fetching, and status updates."""

    @classmethod
    async def publish_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: DomainEventType | str,
        aggregate_type: str,
        aggregate_id: str | UUID,
        payload: dict[str, Any] | None = None,
        schema_version: str = "1.0",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: UUID | None = None,
        actor_context: dict[str, Any] | None = None,
        producer: str = "CAMPUSOS_CORE",
        metadata_json: dict[str, Any] | None = None,
        available_at: datetime | None = None,
    ) -> OutboxEvent:
        """Publish an event to the outbox table within the caller's active DB transaction.

        Guarantees atomicity: the outbox record is added to the active session without committing,
        ensuring business mutations and the event record commit or rollback together.
        """
        validate_schema_version(schema_version)
        ev_str = str(event_type)
        if not is_valid_event_type(ev_str):
            raise ValidationException(f"Cannot emit unregistered event type: '{ev_str}'")

        sanitized_payload = sanitize_event_payload(ev_str, payload)
        now = datetime.now(UTC)

        agg_uuid = (
            aggregate_id
            if isinstance(aggregate_id, UUID)
            else (
                UUID(str(aggregate_id))
                if isinstance(aggregate_id, str) and len(str(aggregate_id)) == 36
                else uuid4()
            )
        )

        outbox_event = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            schema_version=schema_version,
            event_type=ev_str,
            aggregate_type=aggregate_type,
            aggregate_id=agg_uuid,
            payload=sanitized_payload,
            status=OutboxEventStatus.PENDING,
            attempt_count=0,
            max_attempts=5,
            correlation_id=str(correlation_id) if correlation_id else str(uuid4()),
            causation_id=str(causation_id) if causation_id else None,
            actor_id=actor_id,
            actor_context=actor_context or {},
            producer=producer,
            metadata_json=metadata_json or {},
            available_at=available_at or now,
            created_at=now,
        )
        db.add(outbox_event)
        # We deliberately do NOT call db.commit() here so this event
        # commits atomically with the business transaction.
        return outbox_event

    @classmethod
    async def create_event(cls, db: AsyncSession, envelope: "DomainEventEnvelope") -> OutboxEvent:
        """Publish an envelope directly into the transactional outbox."""
        return await cls.publish_event(
            db=db,
            tenant_id=envelope.tenant_id or uuid4(),
            event_type=envelope.event_type,
            aggregate_type=envelope.aggregate_type,
            aggregate_id=envelope.aggregate_id,
            payload=envelope.payload,
            schema_version=envelope.schema_version,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
            actor_id=envelope.actor_id,
            actor_context=envelope.actor_context,
            producer=envelope.producer,
            metadata_json=envelope.metadata,
        )

    @classmethod
    async def fetch_pending_events(
        cls,
        db: AsyncSession,
        batch_size: int = 50,
        now: datetime | None = None,
        tenant_id: UUID | None = None,
        lock_for_update: bool = False,
    ) -> list[OutboxEvent]:
        """Fetch pending outbox events ready for processing with concurrency locking."""
        current_time = now or datetime.now(UTC)
        conditions = [
            OutboxEvent.status == OutboxEventStatus.PENDING,
            OutboxEvent.available_at <= current_time,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = (
            select(OutboxEvent)
            .where(and_(*conditions))
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
        )

        if lock_for_update:
            bind = db.get_bind()
            dialect_name = getattr(bind.dialect, "name", "") if bind is not None else ""
            if dialect_name == "postgresql":
                stmt = stmt.with_for_update(skip_locked=True)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def mark_processing(cls, db: AsyncSession, event_id: UUID) -> bool:
        """Mark an outbox event as currently processing."""
        stmt = (
            update(OutboxEvent)
            .where(
                and_(
                    OutboxEvent.id == event_id,
                    OutboxEvent.status == OutboxEventStatus.PENDING,
                )
            )
            .values(
                status=OutboxEventStatus.PROCESSING,
                attempt_count=OutboxEvent.attempt_count + 1,
            )
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @classmethod
    async def mark_processed(cls, db: AsyncSession, event_id: UUID) -> None:
        """Mark an outbox event as successfully processed."""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxEventStatus.PROCESSED,
                processed_at=datetime.now(UTC),
            )
        )
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def mark_failed(
        cls,
        db: AsyncSession,
        event_id: UUID,
        error_message: str,
        max_retries: int = 5,
        consumer_name: str | None = None,
    ) -> None:
        """Mark an event as failed with bounded jittered exponential backoff
        or dead-letter state.
        """
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if not event:
            return

        now = datetime.now(UTC)
        sanitized_err = sanitize_error_text(error_message)
        event.last_error = sanitized_err

        if event.attempt_count >= max_retries:
            event.status = OutboxEventStatus.DEAD_LETTER
            logger.error(
                "Outbox event %s reached max retries (%d). Routed to DEAD_LETTER. Error: %s",
                event_id,
                max_retries,
                sanitized_err,
            )
            # Create EventDeadLetter entry
            dlq_entry = EventDeadLetter(
                id=uuid4(),
                tenant_id=event.tenant_id,
                event_id=event.id,
                event_type=event.event_type,
                consumer_name=consumer_name,
                failure_reason=sanitized_err[:255] or "Max attempts exceeded",
                error_details_json={
                    "last_error": sanitized_err,
                    "attempt_count": event.attempt_count,
                },
                attempt_count=event.attempt_count,
                first_failed_at=now,
                last_failed_at=now,
                is_resolved=False,
            )
            db.add(dlq_entry)
        else:
            event.status = OutboxEventStatus.PENDING
            # Bounded exponential backoff with jitter: min(3600, 2^attempt * 10 + jitter)
            jitter = random.uniform(0.5, 3.0)
            delay_sec = min(3600, int((2**event.attempt_count) * 10 + jitter))
            event.available_at = now + timedelta(seconds=delay_sec)
            logger.warning(
                "Outbox event %s failed (attempt %d/%d). Scheduled retry in %ds: %s",
                event_id,
                event.attempt_count,
                max_retries,
                delay_sec,
                sanitized_err,
            )

        await db.commit()

    @classmethod
    async def retry_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        user_id: UUID | None = None,
    ) -> OutboxEvent:
        """Manually reset a failed or dead-letter outbox event for immediate retry."""
        stmt = select(OutboxEvent).where(
            and_(OutboxEvent.id == event_id, OutboxEvent.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise NotFoundException(
                f"Outbox event '{event_id}' not found for tenant '{tenant_id}'."
            )

        now = datetime.now(UTC)
        event.status = OutboxEventStatus.PENDING
        event.attempt_count = 0
        event.available_at = now
        event.last_error = None

        # Resolve any associated dead letter record
        dlq_stmt = select(EventDeadLetter).where(
            and_(EventDeadLetter.event_id == event_id, EventDeadLetter.tenant_id == tenant_id)
        )
        dlq_res = await db.execute(dlq_stmt)
        dlq_records = dlq_res.scalars().all()
        for dlq in dlq_records:
            dlq.is_resolved = True
            dlq.resolved_at = now
            dlq.resolved_by_id = user_id
            dlq.resolution_notes = "Manual operator retry initiated"

        await db.commit()
        return event

    @classmethod
    async def replay_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        user_id: UUID | None = None,
        consumer_names: list[str] | None = None,
    ) -> OutboxEvent:
        """Audited replay of a domain event, selectively resetting consumer checkpoints."""
        stmt = select(OutboxEvent).where(
            and_(OutboxEvent.id == event_id, OutboxEvent.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise NotFoundException(
                f"Outbox event '{event_id}' not found for tenant '{tenant_id}'."
            )

        now = datetime.now(UTC)

        # Reset checkpoints
        cp_query = select(EventConsumerCheckpoint).where(
            and_(
                EventConsumerCheckpoint.tenant_id == tenant_id,
                EventConsumerCheckpoint.event_id == event_id,
            )
        )
        if consumer_names:
            cp_query = cp_query.where(EventConsumerCheckpoint.consumer_name.in_(consumer_names))

        cp_res = await db.execute(cp_query)
        checkpoints = cp_res.scalars().all()
        for cp in checkpoints:
            cp.status = ConsumerCheckpointStatus.PENDING
            cp.attempt_count = 0
            cp.error_message = None

        event.status = OutboxEventStatus.PENDING
        event.available_at = now

        # Update dead letter if present
        dlq_stmt = select(EventDeadLetter).where(
            and_(EventDeadLetter.event_id == event_id, EventDeadLetter.tenant_id == tenant_id)
        )
        dlq_res = await db.execute(dlq_stmt)
        for dlq in dlq_res.scalars().all():
            dlq.is_resolved = True
            dlq.resolved_at = now
            dlq.resolved_by_id = user_id
            dlq.resolution_notes = (
                f"Operator replay executed (consumers: {consumer_names or 'ALL'})"
            )

        await db.commit()
        return event

    @classmethod
    async def cleanup_published_events(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
        retention_days: int = 90,
    ) -> int:
        """Safely prune published outbox events older than the retention window.

        Guarantees that pending, processing, or dead-letter events are NEVER removed.
        """
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        conditions = [
            OutboxEvent.status == OutboxEventStatus.PROCESSED,
            OutboxEvent.processed_at <= cutoff,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = delete(OutboxEvent).where(and_(*conditions))
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount or 0

    @classmethod
    async def recover_abandoned_events(
        cls,
        db: AsyncSession,
        stuck_threshold_seconds: int = 300,
        tenant_id: UUID | None = None,
    ) -> dict[str, int]:
        """Recover events stuck in PROCESSING due to worker termination or crashes (Step 31).

        Resets events to PENDING if stuck longer than threshold, or dead-letters if attempt_count
        exceeds max_attempts.
        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=stuck_threshold_seconds)

        conditions = [
            OutboxEvent.status == OutboxEventStatus.PROCESSING,
            OutboxEvent.updated_at <= cutoff,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = select(OutboxEvent).where(and_(*conditions))
        res = await db.execute(stmt)
        stuck_events = list(res.scalars().all())

        recovered_count = 0
        dead_lettered_count = 0

        for ev in stuck_events:
            if ev.attempt_count >= ev.max_attempts:
                ev.status = OutboxEventStatus.DEAD_LETTER
                ev.last_error = f"Abandoned in PROCESSING after worker crash. Max attempts ({ev.max_attempts}) reached."
                dead_lettered_count += 1
                dlq_entry = EventDeadLetter(
                    id=uuid4(),
                    tenant_id=ev.tenant_id,
                    event_id=ev.id,
                    event_type=ev.event_type,
                    consumer_name="WorkerRecoverySubsystem",
                    failure_reason="Abandoned processing event exceeded max attempts",
                    error_details_json={
                        "stuck_threshold_seconds": stuck_threshold_seconds,
                        "attempt_count": ev.attempt_count,
                    },
                    attempt_count=ev.attempt_count,
                    first_failed_at=now,
                    last_failed_at=now,
                    is_resolved=False,
                )
                db.add(dlq_entry)
            else:
                ev.status = OutboxEventStatus.PENDING
                ev.available_at = now
                recovered_count += 1

        if stuck_events:
            await db.commit()
            logger.info(
                "Recovered %d abandoned outbox events (stuck > %ds), %d dead-lettered.",
                recovered_count,
                stuck_threshold_seconds,
                dead_lettered_count,
            )

        return {
            "recovered_count": recovered_count,
            "dead_lettered_count": dead_lettered_count,
        }

    @classmethod
    async def get_backlog_metrics(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Inspect queue processing delay, backlog size, and health against reliability objectives (Step 31)."""
        now = datetime.now(UTC)

        pending_cond = [OutboxEvent.status == OutboxEventStatus.PENDING]
        if tenant_id:
            pending_cond.append(OutboxEvent.tenant_id == tenant_id)
        pending_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*pending_cond)))).scalar() or 0

        proc_cond = [OutboxEvent.status == OutboxEventStatus.PROCESSING]
        if tenant_id:
            proc_cond.append(OutboxEvent.tenant_id == tenant_id)
        proc_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*proc_cond)))).scalar() or 0

        dl_cond = [OutboxEvent.status == OutboxEventStatus.DEAD_LETTER]
        if tenant_id:
            dl_cond.append(OutboxEvent.tenant_id == tenant_id)
        dl_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*dl_cond)))).scalar() or 0

        oldest_stmt = select(OutboxEvent.created_at).where(and_(*pending_cond)).order_by(OutboxEvent.created_at.asc()).limit(1)
        oldest_created_at = (await db.execute(oldest_stmt)).scalar()

        oldest_age_seconds = 0.0
        if oldest_created_at:
            if oldest_created_at.tzinfo is None:
                oldest_created_at = oldest_created_at.replace(tzinfo=UTC)
            oldest_age_seconds = max(0.0, (now - oldest_created_at).total_seconds())

        is_healthy = oldest_age_seconds <= 300.0 and proc_count < 1000

        return {
            "pending_count": pending_count,
            "processing_count": proc_count,
            "dead_letter_count": dl_count,
            "oldest_event_age_seconds": round(oldest_age_seconds, 2),
            "is_healthy": is_healthy,
        }


class EventPublisher:
    """Convenience helper to record domain events into the transactional outbox."""

    @staticmethod
    async def publish(
        db: AsyncSession,
        tenant_id: UUID,
        event_type: DomainEventType | str,
        aggregate_type: str,
        aggregate_id: str | UUID,
        payload: dict[str, Any] | None = None,
        schema_version: str = "1.0",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: UUID | None = None,
        actor_context: dict[str, Any] | None = None,
        producer: str = "CAMPUSOS_CORE",
    ) -> OutboxEvent:
        return await OutboxService.publish_event(
            db=db,
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            schema_version=schema_version,
            correlation_id=correlation_id,
            causation_id=causation_id,
            actor_id=actor_id,
            actor_context=actor_context,
            producer=producer,
        )


event_publisher = EventPublisher()


