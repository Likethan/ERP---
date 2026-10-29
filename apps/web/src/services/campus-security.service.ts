/**
 * Enterprise Campus Physical Security, Visitor Management & Emergency Response Service (Step 68).
 * CampusOS — "One Campus. One System. One Source of Truth."
 */

import {
  MOCK_ACCESS_GRANTS,
  MOCK_CHECKPOINTS,
  MOCK_CONTRACTORS,
  MOCK_EMERGENCY_EVENTS,
  MOCK_INCIDENTS,
  MOCK_PATROL_PLANS,
  MOCK_PATROL_RECORDS,
  MOCK_SECURITY_OVERVIEW,
  MOCK_SECURITY_ZONES,
  MOCK_VISITOR_PASSES,
  MOCK_VISITOR_PROFILES,
  MOCK_VISITOR_REQUESTS,
} from "../mocks/campus-security.mock";
import {
  AccessGrant,
  CampusSecurityIncident,
  ContractorAccessProfile,
  EmergencyEvent,
  EmergencyResponseTask,
  PatrolCheckpointRecord,
  SecurityCheckpoint,
  SecurityOperationsOverview,
  SecurityPatrolPlan,
  SecurityZone,
  VisitorPass,
  VisitorProfile,
  VisitorRequest,
} from "../types/campus-security";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// In-memory state for offline/mock mode
const overviewState: SecurityOperationsOverview = { ...MOCK_SECURITY_OVERVIEW };
const checkpointsState: SecurityCheckpoint[] = [...MOCK_CHECKPOINTS];
const zonesState: SecurityZone[] = [...MOCK_SECURITY_ZONES];
const visitorsState: VisitorProfile[] = [...MOCK_VISITOR_PROFILES];
const requestsState: VisitorRequest[] = [...MOCK_VISITOR_REQUESTS];
const passesState: VisitorPass[] = [...MOCK_VISITOR_PASSES];
const contractorsState: ContractorAccessProfile[] = [...MOCK_CONTRACTORS];
const grantsState: AccessGrant[] = [...MOCK_ACCESS_GRANTS];
const incidentsState: CampusSecurityIncident[] = [...MOCK_INCIDENTS];
const emergencyEventsState: EmergencyEvent[] = [...MOCK_EMERGENCY_EVENTS];
const patrolPlansState: SecurityPatrolPlan[] = [...MOCK_PATROL_PLANS];
const patrolRecordsState: PatrolCheckpointRecord[] = [...MOCK_PATROL_RECORDS];

async function fetchWithFallback<T>(
  endpoint: string,
  options: RequestInit = {},
  fallbackData: T
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}/campus-security${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include",
    });
    if (!res.ok) {
      return fallbackData;
    }
    return await res.json();
  } catch {
    return fallbackData;
  }
}

export const CampusSecurityService = {
  // =========================================================================
  // 1. EXECUTIVE COMMAND SCORECARD & ANALYTICS
  // =========================================================================

  async getOverview(): Promise<SecurityOperationsOverview> {
    return fetchWithFallback<SecurityOperationsOverview>(
      "/overview",
      { method: "GET" },
      overviewState
    );
  },

  // =========================================================================
  // 2. CHECKPOINTS & SECURITY ZONES
  // =========================================================================

  async listCheckpoints(isManned?: boolean): Promise<SecurityCheckpoint[]> {
    const query = isManned !== undefined ? `?is_manned=${isManned}` : "";
    return fetchWithFallback<SecurityCheckpoint[]>(
      `/checkpoints${query}`,
      { method: "GET" },
      isManned !== undefined
        ? checkpointsState.filter((c) => c.is_manned === isManned)
        : checkpointsState
    );
  },

  async createCheckpoint(data: {
    code: string;
    name: string;
    checkpoint_type?: any;
    location_description: string;
    is_manned?: boolean;
    operating_hours?: string;
    guard_post_phone?: string;
  }): Promise<SecurityCheckpoint> {
    const fallback: SecurityCheckpoint = {
      id: `chkpt-${Date.now()}`,
      tenant_id: "tenant-default",
      code: data.code.toUpperCase(),
      name: data.name,
      checkpoint_type: data.checkpoint_type || "MAIN_GATE",
      location_description: data.location_description,
      is_manned: data.is_manned ?? true,
      operating_hours: data.operating_hours || "24x7",
      guard_post_phone: data.guard_post_phone,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    checkpointsState.unshift(fallback);
    return fetchWithFallback<SecurityCheckpoint>(
      "/checkpoints",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async listZones(clearanceLevel?: string): Promise<SecurityZone[]> {
    const query = clearanceLevel ? `?clearance_level=${clearanceLevel}` : "";
    return fetchWithFallback<SecurityZone[]>(
      `/zones${query}`,
      { method: "GET" },
      clearanceLevel
        ? zonesState.filter((z) => z.clearance_level === clearanceLevel)
        : zonesState
    );
  },

  async createZone(data: {
    code: string;
    name: string;
    clearance_level?: any;
    building_name?: string;
    floor_number?: number;
    requires_escort?: boolean;
    max_occupancy?: number;
    emergency_assembly_point?: string;
  }): Promise<SecurityZone> {
    const fallback: SecurityZone = {
      id: `zone-${Date.now()}`,
      tenant_id: "tenant-default",
      code: data.code.toUpperCase(),
      name: data.name,
      clearance_level: data.clearance_level || "CAMPUS_GENERAL",
      building_name: data.building_name,
      floor_number: data.floor_number,
      requires_escort: data.requires_escort ?? false,
      max_occupancy: data.max_occupancy,
      emergency_assembly_point: data.emergency_assembly_point,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    zonesState.unshift(fallback);
    return fetchWithFallback<SecurityZone>(
      "/zones",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  // =========================================================================
  // 3. VISITOR DIRECTORY & PRE-REGISTRATION
  // =========================================================================

  async createVisitorProfile(data: {
    full_name: string;
    email: string;
    phone: string;
    organization?: string;
    id_document_type: string;
    id_document_number_masked?: string;
    is_vip?: boolean;
  }): Promise<VisitorProfile> {
    const fallback: VisitorProfile = {
      id: `vis-${Date.now()}`,
      tenant_id: "tenant-default",
      full_name: data.full_name,
      email: data.email,
      phone: data.phone,
      organization: data.organization,
      id_document_type: data.id_document_type,
      id_document_number_masked: data.id_document_number_masked,
      is_vip: data.is_vip ?? false,
      is_blacklisted: false,
      total_visits: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    visitorsState.unshift(fallback);
    return fetchWithFallback<VisitorProfile>(
      "/visitors",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async listVisitors(search?: string): Promise<VisitorProfile[]> {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    return fetchWithFallback<VisitorProfile[]>(
      `/visitors${query}`,
      { method: "GET" },
      search
        ? visitorsState.filter(
            (v) =>
              v.full_name.toLowerCase().includes(search.toLowerCase()) ||
              v.email.toLowerCase().includes(search.toLowerCase()) ||
              v.phone.includes(search)
          )
        : visitorsState
    );
  },

  async listRequests(status?: string): Promise<VisitorRequest[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithFallback<VisitorRequest[]>(
      `/requests${query}`,
      { method: "GET" },
      status ? requestsState.filter((r) => r.status === status) : requestsState
    );
  },

  async submitRequest(data: {
    visitor_name: string;
    visitor_phone: string;
    visitor_email: string;
    visitor_category?: any;
    organization?: string;
    id_document_type?: string;
    id_document_number_masked?: string;
    host_name: string;
    host_department?: string;
    visit_purpose: string;
    destination_description: string;
    expected_arrival_at: string;
    expected_departure_at: string;
    has_vehicle?: boolean;
    vehicle_number?: string;
    accompanying_count?: number;
  }): Promise<VisitorRequest> {
    const reqNumber = `VR-2026-${String(requestsState.length + 1).padStart(4, "0")}`;
    const fallback: VisitorRequest = {
      id: `vreq-${Date.now()}`,
      tenant_id: "tenant-default",
      request_number: reqNumber,
      visitor_id: `vis-${Date.now()}`,
      visitor_name: data.visitor_name,
      visitor_phone: data.visitor_phone,
      visitor_email: data.visitor_email,
      visitor_category: data.visitor_category || "GUEST",
      host_name: data.host_name,
      host_department: data.host_department,
      visit_purpose: data.visit_purpose,
      destination_description: data.destination_description,
      expected_arrival_at: data.expected_arrival_at,
      expected_departure_at: data.expected_departure_at,
      status: "PENDING",
      approval_required: true,
      has_vehicle: data.has_vehicle ?? false,
      vehicle_number: data.vehicle_number,
      accompanying_count: data.accompanying_count || 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    requestsState.unshift(fallback);
    return fetchWithFallback<VisitorRequest>(
      "/requests",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async reviewRequest(
    requestId: string,
    decision: "APPROVED" | "REJECTED",
    rejectionReason?: string
  ): Promise<VisitorRequest> {
    const req = requestsState.find((r) => r.id === requestId);
    if (req) {
      req.status = decision;
      req.rejection_reason = rejectionReason;
      req.approved_at = new Date().toISOString();
      req.updated_at = new Date().toISOString();

      if (decision === "APPROVED") {
        const passNumber = `VP-2026-${String(passesState.length + 1).padStart(4, "0")}`;
        const newPass: VisitorPass = {
          id: `pass-${Date.now()}`,
          tenant_id: "tenant-default",
          pass_number: passNumber,
          request_id: req.id,
          visitor_id: req.visitor_id,
          visitor_name: req.visitor_name,
          visitor_category: req.visitor_category,
          host_name: req.host_name,
          destination: req.destination_description,
          signed_token: `VT-tenant-default:${passNumber}:${Date.now() + 86400000}:mock_sig`,
          valid_from: req.expected_arrival_at,
          valid_until: req.expected_departure_at,
          status: "ISSUED",
          is_overdue: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        passesState.unshift(newPass);
      }
    }
    return fetchWithFallback<VisitorRequest>(
      `/requests/${requestId}/review`,
      { method: "POST", body: JSON.stringify({ decision, rejection_reason: rejectionReason }) },
      req || requestsState[0]
    );
  },

  async createVisitorRequest(data: any): Promise<VisitorRequest> {
    return this.submitRequest(data);
  },

  async approveVisitorRequest(requestId: string, approvedByUserId?: string): Promise<VisitorRequest> {
    const res = await this.reviewRequest(requestId, "APPROVED");
    if (approvedByUserId && res) {
      res.approved_by_user_id = approvedByUserId;
    }
    return res;
  },

  async rejectVisitorRequest(requestId: string, reason?: string): Promise<VisitorRequest> {
    return this.reviewRequest(requestId, "REJECTED", reason);
  },

  async generateVisitorPass(requestId: string, hoursValid: number = 8): Promise<VisitorPass> {
    const req = requestsState.find((r) => r.id === requestId);
    const passNumber = `VPASS-2026-${String(passesState.length + 1).padStart(4, "0")}`;
    const now = new Date();
    const until = new Date(now.getTime() + hoursValid * 3600 * 1000);
    const fallback: VisitorPass = {
      id: `pass-${Date.now()}`,
      tenant_id: "tenant-default",
      pass_number: passNumber,
      request_id: requestId,
      visitor_id: req ? req.visitor_id : `vis-${Date.now()}`,
      visitor_name: req ? req.visitor_name : "Authorized Visitor",
      visitor_category: req ? req.visitor_category : "GUEST",
      host_name: req ? req.host_name : "Campus Host",
      destination: req ? req.destination_description : "Campus General",
      signed_token: `VT-tenant-default:${passNumber}:${until.getTime()}:mock_sig_${Date.now()}`,
      valid_from: now.toISOString(),
      valid_until: until.toISOString(),
      status: "ISSUED",
      is_overdue: false,
      created_at: now.toISOString(),
      updated_at: now.toISOString(),
    };
    passesState.unshift(fallback);
    return fetchWithFallback<VisitorPass>(
      `/requests/${requestId}/generate-pass`,
      { method: "POST", body: JSON.stringify({ hours_valid: hoursValid }) },
      fallback
    );
  },

  // =========================================================================
  // 4. GATE OPERATIONS (PASSES, CHECK-IN, CHECK-OUT)
  // =========================================================================

  async listPasses(status?: string): Promise<VisitorPass[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithFallback<VisitorPass[]>(
      `/passes${query}`,
      { method: "GET" },
      status ? passesState.filter((p) => p.status === status) : passesState
    );
  },

  async verifyPassToken(signedToken: string): Promise<VisitorPass> {
    const fallback = passesState.find((p) => p.signed_token === signedToken);
    if (!fallback) {
      throw new Error("Invalid or untrusted visitor QR token");
    }
    return fetchWithFallback<VisitorPass>(
      "/passes/verify",
      { method: "POST", body: JSON.stringify({ signed_token: signedToken }) },
      fallback
    );
  },

  async verifyVisitorPassToken(signedToken: string): Promise<{ valid: boolean; message: string; pass?: VisitorPass }> {
    const pass = passesState.find((p) => p.signed_token === signedToken);
    if (!pass) {
      return { valid: false, message: "Invalid or untrusted visitor QR token" };
    }
    return { valid: true, message: "Pass token verified valid", pass };
  },

  async checkInVisitor(
    signedToken: string,
    checkpointId: string,
    officerId?: string
  ): Promise<{ success: boolean; message: string; pass?: VisitorPass }> {
    const pass = passesState.find((p) => p.signed_token === signedToken);
    if (!pass) {
      return { success: false, message: "Pass not found for token" };
    }
    if (pass.status === "CHECKED_IN") {
      return { success: false, message: "Duplicate check-in rejected: Already checked in" };
    }
    pass.status = "CHECKED_IN";
    pass.check_in_at = new Date().toISOString();
    pass.check_in_checkpoint_id = checkpointId;
    pass.check_in_officer_id = officerId;
    pass.updated_at = new Date().toISOString();
    overviewState.visitors_currently_on_campus += 1;
    return { success: true, message: "Visitor checked in successfully", pass };
  },

  async checkOutVisitor(
    signedToken: string,
    checkpointId: string,
    officerId?: string
  ): Promise<{ success: boolean; message: string; pass?: VisitorPass }> {
    const pass = passesState.find((p) => p.signed_token === signedToken);
    if (!pass) {
      return { success: false, message: "Pass not found for token" };
    }
    pass.status = "CHECKED_OUT";
    pass.check_out_at = new Date().toISOString();
    pass.check_out_checkpoint_id = checkpointId;
    pass.check_out_officer_id = officerId;
    pass.is_overdue = false;
    pass.updated_at = new Date().toISOString();
    overviewState.visitors_currently_on_campus = Math.max(0, overviewState.visitors_currently_on_campus - 1);
    return { success: true, message: "Visitor checked out successfully", pass };
  },

  async revokeVisitorPass(passId: string, reason: string): Promise<VisitorPass> {
    return this.revokePass(passId, reason);
  },

  async gateCheckIn(
    passId: string,
    checkpointId: string,
    vehicleNumber?: string
  ): Promise<VisitorPass> {
    const pass = passesState.find((p) => p.id === passId);
    if (pass) {
      if (pass.status === "CHECKED_IN") {
        throw new Error("Duplicate check-in rejected: visitor is already checked in");
      }
      pass.status = "CHECKED_IN";
      pass.check_in_at = new Date().toISOString();
      pass.check_in_checkpoint_id = checkpointId;
      pass.updated_at = new Date().toISOString();
      overviewState.visitors_currently_on_campus += 1;
    }
    return fetchWithFallback<VisitorPass>(
      `/passes/${passId}/check-in`,
      { method: "POST", body: JSON.stringify({ checkpoint_id: checkpointId, vehicle_number: vehicleNumber }) },
      pass || passesState[0]
    );
  },

  async gateCheckOut(passId: string, checkpointId: string): Promise<VisitorPass> {
    const pass = passesState.find((p) => p.id === passId);
    if (pass) {
      pass.status = "CHECKED_OUT";
      pass.check_out_at = new Date().toISOString();
      pass.check_out_checkpoint_id = checkpointId;
      pass.is_overdue = false;
      pass.updated_at = new Date().toISOString();
      overviewState.visitors_currently_on_campus = Math.max(0, overviewState.visitors_currently_on_campus - 1);
    }
    return fetchWithFallback<VisitorPass>(
      `/passes/${passId}/check-out`,
      { method: "POST", body: JSON.stringify({ checkpoint_id: checkpointId }) },
      pass || passesState[0]
    );
  },

  async revokePass(passId: string, reason: string): Promise<VisitorPass> {
    const pass = passesState.find((p) => p.id === passId);
    if (pass) {
      pass.status = "REVOKED";
      pass.revoked_at = new Date().toISOString();
      pass.revocation_reason = reason;
      pass.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<VisitorPass>(
      `/passes/${passId}/revoke`,
      { method: "POST", body: JSON.stringify({ revocation_reason: reason }) },
      pass || passesState[0]
    );
  },

  // =========================================================================
  // 5. CONTRACTORS & ACCESS GRANTS
  // =========================================================================

  async listContractors(status?: string): Promise<ContractorAccessProfile[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithFallback<ContractorAccessProfile[]>(
      `/contractors${query}`,
      { method: "GET" },
      status ? contractorsState.filter((c) => c.status === status) : contractorsState
    );
  },

  async createContractor(data: {
    organization_name: string;
    contractor_name: string;
    contractor_phone: string;
    service_type: string;
    work_order_reference?: string;
    valid_from: string;
    valid_until: string;
    is_safety_induction_completed?: boolean;
    authorized_zone_ids?: string[];
  }): Promise<ContractorAccessProfile> {
    const code = `CONT-2026-${String(contractorsState.length + 1).padStart(3, "0")}`;
    const fallback: ContractorAccessProfile = {
      id: `cont-${Date.now()}`,
      tenant_id: "tenant-default",
      contractor_code: code,
      organization_name: data.organization_name,
      contractor_name: data.contractor_name,
      contractor_phone: data.contractor_phone,
      service_type: data.service_type,
      work_order_reference: data.work_order_reference,
      valid_from: data.valid_from,
      valid_until: data.valid_until,
      is_safety_induction_completed: data.is_safety_induction_completed ?? false,
      status: "ACTIVE",
      authorized_zone_ids: data.authorized_zone_ids || [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    contractorsState.unshift(fallback);
    return fetchWithFallback<ContractorAccessProfile>(
      "/contractors",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async registerContractor(data: any): Promise<ContractorAccessProfile> {
    return this.createContractor(data);
  },

  async verifyContractorSafetyInduction(contractorId: string): Promise<ContractorAccessProfile> {
    const contractor = contractorsState.find((c) => c.id === contractorId);
    if (contractor) {
      contractor.is_safety_induction_completed = true;
      contractor.safety_induction_date = new Date().toISOString();
      contractor.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<ContractorAccessProfile>(
      `/contractors/${contractorId}/safety-induction`,
      { method: "POST" },
      contractor || contractorsState[0]
    );
  },

  async listAccessGrants(zoneId?: string, status?: string): Promise<AccessGrant[]> {
    let list = [...grantsState];
    if (zoneId) list = list.filter((g) => g.zone_id === zoneId);
    if (status) list = list.filter((g) => g.status === status);
    return fetchWithFallback<AccessGrant[]>(
      `/access-grants${status ? `?status=${status}` : ""}`,
      { method: "GET" },
      list
    );
  },

  async createAccessGrant(data: {
    zone_id: string;
    grantee_type: any;
    grantee_id: string;
    grantee_name: string;
    valid_from: string;
    valid_until: string;
    is_temporary?: boolean;
    grant_reason: string;
  }): Promise<AccessGrant> {
    const grantNumber = `AG-2026-${String(grantsState.length + 1).padStart(4, "0")}`;
    const fallback: AccessGrant = {
      id: `grant-${Date.now()}`,
      tenant_id: "tenant-default",
      grant_number: grantNumber,
      zone_id: data.zone_id,
      grantee_type: data.grantee_type,
      grantee_id: data.grantee_id,
      grantee_name: data.grantee_name,
      valid_from: data.valid_from,
      valid_until: data.valid_until,
      is_temporary: data.is_temporary ?? true,
      grant_reason: data.grant_reason,
      status: "ACTIVE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    grantsState.unshift(fallback);
    return fetchWithFallback<AccessGrant>(
      "/access-grants",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async revokeAccessGrant(grantId: string, reason: string): Promise<AccessGrant> {
    const grant = grantsState.find((g) => g.id === grantId);
    if (grant) {
      grant.status = "REVOKED";
      grant.revoked_at = new Date().toISOString();
      grant.revocation_reason = reason;
      grant.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<AccessGrant>(
      `/access-grants/${grantId}/revoke`,
      { method: "POST", body: JSON.stringify({ revocation_reason: reason }) },
      grant || grantsState[0]
    );
  },

  // =========================================================================
  // 6. PHYSICAL SECURITY INCIDENTS
  // =========================================================================

  async listIncidents(status?: string, severity?: string): Promise<CampusSecurityIncident[]> {
    let list = [...incidentsState];
    if (status) list = list.filter((i) => i.status === status);
    if (severity) list = list.filter((i) => i.severity === severity);
    return fetchWithFallback<CampusSecurityIncident[]>(
      "/incidents",
      { method: "GET" },
      list
    );
  },

  async reportIncident(data: {
    title: string;
    category: any;
    severity?: any;
    reported_location: string;
    zone_id?: string;
    checkpoint_id?: string;
    description: string;
    assigned_team?: string;
  }): Promise<CampusSecurityIncident> {
    const incNumber = `SEC-INC-2026-${String(incidentsState.length + 1).padStart(4, "0")}`;
    const fallback: CampusSecurityIncident = {
      id: `inc-${Date.now()}`,
      tenant_id: "tenant-default",
      incident_number: incNumber,
      title: data.title,
      category: data.category,
      severity: data.severity || "MEDIUM",
      status: "REPORTED",
      reported_at: new Date().toISOString(),
      reported_location: data.reported_location,
      zone_id: data.zone_id,
      checkpoint_id: data.checkpoint_id,
      description: data.description,
      assigned_team: data.assigned_team || "Security Response Team",
      is_escalated: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    incidentsState.unshift(fallback);
    return fetchWithFallback<CampusSecurityIncident>(
      "/incidents",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async escalateIncident(incidentId: string, reason: string, targetTeam?: string): Promise<CampusSecurityIncident> {
    const inc = incidentsState.find((i) => i.id === incidentId);
    if (inc) {
      inc.is_escalated = true;
      inc.escalated_at = new Date().toISOString();
      inc.escalation_reason = reason;
      inc.status = "ESCALATED";
      if (targetTeam) inc.assigned_team = targetTeam;
      inc.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<CampusSecurityIncident>(
      `/incidents/${incidentId}/escalate`,
      { method: "POST", body: JSON.stringify({ escalation_reason: reason, target_team: targetTeam }) },
      inc || incidentsState[0]
    );
  },

  async resolveIncident(incidentId: string, summary: string, correctiveNotes?: string): Promise<CampusSecurityIncident> {
    const inc = incidentsState.find((i) => i.id === incidentId);
    if (inc) {
      inc.status = "RESOLVED";
      inc.resolution_summary = summary;
      inc.corrective_action_notes = correctiveNotes;
      inc.resolved_at = new Date().toISOString();
      inc.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<CampusSecurityIncident>(
      `/incidents/${incidentId}`,
      {
        method: "PUT",
        body: JSON.stringify({
          status: "RESOLVED",
          resolution_summary: summary,
          corrective_action_notes: correctiveNotes,
        }),
      },
      inc || incidentsState[0]
    );
  },

  // =========================================================================
  // 7. EMERGENCY RESPONSE COORDINATION
  // =========================================================================

  async listEmergencyEvents(status?: string): Promise<EmergencyEvent[]> {
    return fetchWithFallback<EmergencyEvent[]>(
      "/emergency/events",
      { method: "GET" },
      status ? emergencyEventsState.filter((e) => e.status === status) : emergencyEventsState
    );
  },

  async createEmergencyEvent(data: {
    title: string;
    event_type: any;
    severity?: any;
    affected_campus_areas: string;
    coordinator_name: string;
    emergency_broadcast_message?: string;
  }): Promise<EmergencyEvent> {
    const code = `EMG-2026-${String(emergencyEventsState.length + 1).padStart(4, "0")}`;
    const fallback: EmergencyEvent = {
      id: `emg-${Date.now()}`,
      tenant_id: "tenant-default",
      event_code: code,
      title: data.title,
      event_type: data.event_type,
      severity: data.severity || "EMERGENCY",
      status: "ACTIVE",
      affected_campus_areas: data.affected_campus_areas,
      affected_zone_ids: [],
      coordinator_name: data.coordinator_name,
      emergency_broadcast_message: data.emergency_broadcast_message,
      initiated_at: new Date().toISOString(),
      tasks: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    emergencyEventsState.unshift(fallback);
    return fetchWithFallback<EmergencyEvent>(
      "/emergency/events",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async updateEmergencyEvent(
    eventId: string,
    data: { status?: any; after_action_report?: string }
  ): Promise<EmergencyEvent> {
    const ev = emergencyEventsState.find((e) => e.id === eventId);
    if (ev) {
      if (data.status) {
        ev.status = data.status;
        if (data.status === "ALL_CLEAR") ev.all_clear_at = new Date().toISOString();
        if (data.status === "CLOSED") ev.closed_at = new Date().toISOString();
      }
      if (data.after_action_report) ev.after_action_report = data.after_action_report;
      ev.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<EmergencyEvent>(
      `/emergency/events/${eventId}`,
      { method: "PUT", body: JSON.stringify(data) },
      ev || emergencyEventsState[0]
    );
  },

  async initiateEmergencyEvent(data: any): Promise<EmergencyEvent> {
    const ev = await this.createEmergencyEvent(data);
    ev.tasks = [
      {
        id: `task-${Date.now()}-1`,
        tenant_id: ev.tenant_id,
        event_id: ev.id,
        task_title: `Notify emergency responders and campus dispatch for ${ev.event_type}`,
        priority: "URGENT",
        assigned_to_role: "First Response Lead",
        status: "PENDING",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: `task-${Date.now()}-2`,
        tenant_id: ev.tenant_id,
        event_id: ev.id,
        task_title: `Secure perimeter around ${ev.affected_campus_areas}`,
        priority: "HIGH",
        assigned_to_role: "Patrol Guard Unit",
        status: "PENDING",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    return ev;
  },

  async completeEmergencyTask(taskId: string, notes?: string): Promise<EmergencyResponseTask> {
    let task: EmergencyResponseTask | undefined;
    for (const ev of emergencyEventsState) {
      if (ev.tasks) {
        task = ev.tasks.find((t) => t.id === taskId);
        if (task) {
          task.status = "COMPLETED";
          task.completed_at = new Date().toISOString();
          task.notes = notes;
          task.updated_at = new Date().toISOString();
          break;
        }
      }
    }
    const fallback: EmergencyResponseTask = task || {
      id: taskId,
      tenant_id: "tenant-default",
      event_id: "emg-default",
      task_title: "Emergency Response Task",
      priority: "HIGH",
      status: "COMPLETED",
      completed_at: new Date().toISOString(),
      notes,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return fetchWithFallback<EmergencyResponseTask>(
      `/emergency/tasks/${taskId}`,
      { method: "PUT", body: JSON.stringify({ status: "COMPLETED", notes }) },
      fallback
    );
  },

  async submitAfterActionReport(eventId: string, afterActionReport: string): Promise<EmergencyEvent> {
    return this.updateEmergencyEvent(eventId, { after_action_report: afterActionReport });
  },

  async closeEmergencyEvent(eventId: string): Promise<EmergencyEvent> {
    return this.updateEmergencyEvent(eventId, { status: "CLOSED" });
  },

  // =========================================================================
  // 8. SECURITY PATROLS & CHECKPOINT ROUNDS
  // =========================================================================

  async listPatrolPlans(): Promise<SecurityPatrolPlan[]> {
    return fetchWithFallback<SecurityPatrolPlan[]>(
      "/patrols/plans",
      { method: "GET" },
      patrolPlansState
    );
  },

  async listPatrolRecords(planId?: string): Promise<PatrolCheckpointRecord[]> {
    return fetchWithFallback<PatrolCheckpointRecord[]>(
      `/patrols/records${planId ? `?plan_id=${planId}` : ""}`,
      { method: "GET" },
      planId ? patrolRecordsState.filter((r) => r.plan_id === planId) : patrolRecordsState
    );
  },

  async createPatrolPlan(data: {
    title: string;
    shift_name?: any;
    frequency_hours?: number;
    assigned_team_name: string;
    checkpoints_sequence?: string[];
  }): Promise<SecurityPatrolPlan> {
    const code = `PATROL-2026-${String(patrolPlansState.length + 1).padStart(3, "0")}`;
    const fallback: SecurityPatrolPlan = {
      id: `plan-${Date.now()}`,
      tenant_id: "tenant-default",
      plan_code: code,
      title: data.title,
      shift_name: data.shift_name || "MORNING_SHIFT",
      frequency_hours: data.frequency_hours || 2,
      assigned_team_name: data.assigned_team_name,
      checkpoints_sequence: data.checkpoints_sequence || [],
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    patrolPlansState.unshift(fallback);
    return fetchWithFallback<SecurityPatrolPlan>(
      "/patrols/plans",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async scanPatrolCheckpoint(data: {
    plan_id: string;
    checkpoint_id: string;
    officer_name: string;
    scheduled_round_time: string;
    status?: any;
    verification_token?: string;
    observations?: string;
  }): Promise<PatrolCheckpointRecord> {
    const rec = await this.recordPatrolCheckpoint(data);
    if (data.status) rec.status = data.status;
    return rec;
  },

  async recordPatrolCheckpoint(data: {
    plan_id: string;
    checkpoint_id: string;
    officer_name: string;
    scheduled_round_time: string;
    verification_token?: string;
    observations?: string;
  }): Promise<PatrolCheckpointRecord> {
    const fallback: PatrolCheckpointRecord = {
      id: `prec-${Date.now()}`,
      tenant_id: "tenant-default",
      plan_id: data.plan_id,
      checkpoint_id: data.checkpoint_id,
      officer_name: data.officer_name,
      scheduled_round_time: data.scheduled_round_time,
      scanned_at: new Date().toISOString(),
      status: "COMPLETED",
      verification_token: data.verification_token,
      observations: data.observations,
      supervisor_reviewed: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    patrolRecordsState.unshift(fallback);
    return fetchWithFallback<PatrolCheckpointRecord>(
      "/patrols/records",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async reviewPatrolRecord(recordId: string, notes: string): Promise<PatrolCheckpointRecord> {
    const rec = patrolRecordsState.find((r) => r.id === recordId);
    if (rec) {
      rec.supervisor_reviewed = true;
      rec.supervisor_review_notes = notes;
      rec.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<PatrolCheckpointRecord>(
      `/patrols/records/${recordId}/review`,
      { method: "POST", body: JSON.stringify({ supervisor_review_notes: notes }) },
      rec || patrolRecordsState[0]
    );
  },
};

