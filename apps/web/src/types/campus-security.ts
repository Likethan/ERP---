/**
 * TypeScript Type Definitions for Campus Physical Security, Visitor Management & Emergency Response (Step 68).
 * CampusOS — "One Campus. One System. One Source of Truth."
 */

export type CheckpointType =
  | "MAIN_GATE"
  | "VEHICLE_BARRIER"
  | "PEDESTRIAN_TURNSTILE"
  | "SERVICE_GATE"
  | "EMERGENCY_EXIT";

export type ClearanceLevel =
  | "PUBLIC"
  | "CAMPUS_GENERAL"
  | "FACULTY_STAFF_ONLY"
  | "RESTRICTED"
  | "HIGH_SECURITY";

export type VisitorCategory =
  | "GUEST"
  | "PARENT"
  | "VENDOR"
  | "CONTRACTOR"
  | "INTERVIEW_CANDIDATE"
  | "EVENT_ATTENDEE"
  | "OFFICIAL"
  | "VIP";

export type VisitorPassStatus =
  | "ISSUED"
  | "CHECKED_IN"
  | "CHECKED_OUT"
  | "OVERDUE"
  | "REVOKED"
  | "EXPIRED";

export type IncidentCategory =
  | "UNAUTHORIZED_ACCESS"
  | "PROPERTY_LOSS_DAMAGE"
  | "SAFETY_HAZARD"
  | "SUSPICIOUS_ACTIVITY"
  | "VEHICLE_GATE_INCIDENT"
  | "POLICY_VIOLATION"
  | "EMERGENCY_ASSISTANCE";

export type IncidentSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type IncidentStatus =
  | "REPORTED"
  | "ACKNOWLEDGED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "ESCALATED"
  | "RESOLVED"
  | "CLOSED";

export type EmergencyEventType =
  | "FIRE_ALARM"
  | "SEVERE_WEATHER"
  | "MEDICAL_EMERGENCY"
  | "ACTIVE_THREAT"
  | "INFRASTRUCTURE_FAILURE"
  | "HAZMAT_LEAK"
  | "NATURAL_DISASTER";

export type EmergencySeverity = "ADVISORY" | "WARNING" | "EMERGENCY" | "CATASTROPHIC";

export type EmergencyStatus = "ACTIVE" | "CONTAINED" | "ALL_CLEAR" | "CLOSED";

export type EmergencyTaskPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type EmergencyTaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "BLOCKED";

export type PatrolShift =
  | "MORNING_SHIFT"
  | "AFTERNOON_SHIFT"
  | "NIGHT_SHIFT"
  | "WEEKEND_SHIFT";

export type PatrolRecordStatus = "COMPLETED" | "MISSED" | "DELAYED" | "EXCEPTION_NOTED";


export interface SecurityCheckpoint {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  checkpoint_type: CheckpointType;
  location_description: string;
  is_manned: boolean;
  operating_hours: string;
  guard_post_phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SecurityZone {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  clearance_level: ClearanceLevel;
  building_name?: string;
  floor_number?: number;
  requires_escort: boolean;
  max_occupancy?: number;
  emergency_assembly_point?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VisitorProfile {
  id: string;
  tenant_id: string;
  full_name: string;
  email: string;
  phone: string;
  organization?: string;
  id_document_type: string;
  id_document_number_masked?: string;
  is_vip: boolean;
  is_blacklisted: boolean;
  blacklist_reason?: string;
  total_visits: number;
  created_at: string;
  updated_at: string;
}

export interface VisitorRequest {
  id: string;
  tenant_id: string;
  request_number: string;
  visitor_id: string;
  visitor_name: string;
  visitor_phone: string;
  visitor_email: string;
  visitor_category: VisitorCategory;
  host_user_id?: string;
  host_name: string;
  host_department?: string;
  visit_purpose: string;
  destination_zone_id?: string;
  destination_description: string;
  expected_arrival_at: string;
  expected_departure_at: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
  approval_required: boolean;
  approved_by_user_id?: string;
  approved_at?: string;
  rejection_reason?: string;
  vehicle_number?: string;
  has_vehicle: boolean;
  accompanying_count: number;
  created_at: string;
  updated_at: string;
}

export interface VisitorPass {
  id: string;
  tenant_id: string;
  pass_number: string;
  request_id?: string;
  visitor_id: string;
  visitor_name: string;
  visitor_category: VisitorCategory;
  host_name: string;
  destination: string;
  signed_token: string;
  valid_from: string;
  valid_until: string;
  status: VisitorPassStatus;
  check_in_at?: string;
  check_in_checkpoint_id?: string;
  check_in_officer_id?: string;
  check_out_at?: string;
  check_out_checkpoint_id?: string;
  check_out_officer_id?: string;
  is_overdue: boolean;
  revoked_at?: string;
  revocation_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface ContractorAccessProfile {
  id: string;
  tenant_id: string;
  contractor_code: string;
  organization_name: string;
  contractor_name: string;
  contractor_phone: string;
  service_type: string;
  work_order_reference?: string;
  valid_from: string;
  valid_until: string;
  is_safety_induction_completed: boolean;
  safety_induction_date?: string;
  status: "ACTIVE" | "PENDING_VERIFICATION" | "SUSPENDED" | "EXPIRED";
  authorized_zone_ids: string[];
  emergency_contact_phone?: string;
  badge_reference?: string;
  created_at: string;
  updated_at: string;
}

export interface AccessGrant {
  id: string;
  tenant_id: string;
  grant_number: string;
  zone_id: string;
  grantee_type: "STUDENT" | "STAFF" | "CONTRACTOR" | "VISITOR";
  grantee_id: string;
  grantee_name: string;
  valid_from: string;
  valid_until: string;
  is_temporary: boolean;
  granted_by_user_id?: string;
  grant_reason: string;
  status: "ACTIVE" | "EXPIRED" | "REVOKED";
  revoked_at?: string;
  revoked_by_user_id?: string;
  revocation_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface CampusSecurityIncident {
  id: string;
  tenant_id: string;
  incident_number: string;
  title: string;
  category: IncidentCategory;
  severity: IncidentSeverity;
  status: IncidentStatus;
  reported_at: string;
  reported_by_user_id?: string;
  reported_by_name?: string;
  reported_location: string;
  zone_id?: string;
  checkpoint_id?: string;
  description: string;
  assigned_team?: string;
  assigned_to_user_id?: string;
  assigned_at?: string;
  is_escalated: boolean;
  escalated_at?: string;
  escalation_reason?: string;
  resolution_summary?: string;
  resolved_at?: string;
  resolved_by_user_id?: string;
  corrective_action_notes?: string;
  evidence_urls?: string[];
  created_at: string;
  updated_at: string;
}

export interface EmergencyResponseTask {
  id: string;
  tenant_id: string;
  event_id: string;
  task_title: string;
  priority: EmergencyTaskPriority;
  assigned_to_role?: string;
  assigned_to_user_id?: string;
  status: EmergencyTaskStatus;
  action_checklist?: Array<{ step: string; done: boolean }>;
  completed_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface EmergencyEvent {
  id: string;
  tenant_id: string;
  event_code: string;
  title: string;
  event_type: EmergencyEventType;
  severity: EmergencySeverity;
  status: EmergencyStatus;
  affected_campus_areas: string;
  affected_zone_ids: string[];
  coordinator_user_id?: string;
  coordinator_name: string;
  emergency_broadcast_message?: string;
  initiated_at: string;
  all_clear_at?: string;
  closed_at?: string;
  after_action_report?: string;
  external_services_contacted?: string[];
  tasks?: EmergencyResponseTask[];
  created_at: string;
  updated_at: string;
}

export interface SecurityPatrolPlan {
  id: string;
  tenant_id: string;
  plan_code: string;
  title: string;
  shift_name: PatrolShift;
  frequency_hours: number;
  assigned_team_name: string;
  checkpoints_sequence: string[];
  is_active: boolean;
  supervisor_user_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PatrolCheckpointRecord {
  id: string;
  tenant_id: string;
  plan_id: string;
  checkpoint_id: string;
  officer_user_id?: string;
  officer_name: string;
  scheduled_round_time: string;
  scanned_at?: string;
  status: PatrolRecordStatus;
  verification_token?: string;
  observations?: string;
  incident_created_id?: string;
  supervisor_reviewed: boolean;
  supervisor_review_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SecurityOperationsOverview {
  visitors_currently_on_campus: number;
  expected_arrivals_today: number;
  pending_visitor_approvals: number;
  overdue_visitor_departures: number;
  active_contractors_on_site: number;
  active_access_grants: number;
  open_security_incidents: number;
  critical_incidents_count: number;
  active_emergency_events: number;
  patrol_completion_rate_pct: number;
  manned_checkpoints_count: number;
  security_readiness_score: number;
}
