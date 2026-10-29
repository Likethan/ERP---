/**
 * CampusOS — Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Service (Step 66)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * REST API client communicating with `/api/v1/housing/*`
 * with resilient offline fallback to realistic institutional records.
 */

import {
  AccommodationBed,
  AccommodationProperty,
  AccommodationProvider,
  AccommodationUnit,
  HousingAgreementCreateInput,
  HousingAgreementReference,
  HousingAnalyticsSummary,
  HousingAssignment,
  HousingAssignmentCreateInput,
  HousingCheckInOutInput,
  HousingCheckInOutRecord,
  HousingInspectionCreateInput,
  HousingMaintenanceCreateInput,
  HousingMaintenanceRequest,
  HousingMaintenanceUpdateInput,
  HousingOffer,
  HousingOfferCreateInput,
  HousingOfferRespondInput,
  HousingPropertyInspection,
  HousingRequestCreateInput,
  HousingRequestReviewInput,
  HousingTransferInput,
  PropertyCreateInput,
  PropertyTransitionInput,
  ProviderCreateInput,
  StudentHousingRequest,
  UnitCreateInput,
} from "../types/housing";
import {
  MOCK_AGREEMENTS,
  MOCK_ANALYTICS,
  MOCK_ASSIGNMENTS,
  MOCK_CHECKINS,
  MOCK_INSPECTIONS,
  MOCK_MAINTENANCE,
  MOCK_PROPERTIES,
  MOCK_PROVIDERS,
  MOCK_REQUESTS,
  MOCK_UNITS,
} from "../mocks/housing.mock";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/housing`
    : "http://localhost:8000/api/v1/housing";

async function fetchWithFallback<T>(
  url: string,
  options?: RequestInit,
  fallback?: T
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });
    if (!res.ok) {
      if (fallback !== undefined) return fallback;
      throw new Error(`Housing API error: ${res.status} ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    if (fallback !== undefined) return fallback;
    throw err;
  }
}

// In-memory state containers for dynamic updates when backend is offline
const propertiesState = [...MOCK_PROPERTIES];
const providersState = [...MOCK_PROVIDERS];
const unitsState = [...MOCK_UNITS];
const requestsState = [...MOCK_REQUESTS];
const assignmentsState = [...MOCK_ASSIGNMENTS];
const agreementsState = [...MOCK_AGREEMENTS];
const checkinsState = [...MOCK_CHECKINS];
const inspectionsState = [...MOCK_INSPECTIONS];
const maintenanceState = [...MOCK_MAINTENANCE];
const analyticsState = { ...MOCK_ANALYTICS };
const offersState: HousingOffer[] = [
  {
    id: "offer-001",
    tenant_id: "tenant-default",
    request_id: "req-001",
    student_id: "st-001",
    property_id: "prop-001",
    unit_id: "unit-001",
    bed_id: "bed-001",
    offered_rent_monthly: 9500,
    offered_deposit: 19000,
    occupancy_start_date: "2025-07-01",
    occupancy_end_date: "2026-06-30",
    offer_valid_until: "2025-06-15T00:00:00Z",
    status: "OFFERED",
    created_at: new Date().toISOString(),
  },
];

export const HousingService = {
  // =========================================================================
  // 1. DASHBOARD & ANALYTICS
  // =========================================================================

  async getAnalytics(): Promise<HousingAnalyticsSummary> {
    return fetchWithFallback<HousingAnalyticsSummary>(
      "/analytics",
      { method: "GET" },
      analyticsState
    );
  },

  // =========================================================================
  // 2. ACCOMMODATION PROVIDERS & LANDLORDS
  // =========================================================================

  async listProviders(status?: string): Promise<AccommodationProvider[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithFallback<AccommodationProvider[]>(
      `/providers${query}`,
      { method: "GET" },
      status ? providersState.filter((p) => p.verification_status === status) : providersState
    );
  },

  async getProvider(id: string): Promise<AccommodationProvider> {
    const fallback = providersState.find((p) => p.id === id);
    return fetchWithFallback<AccommodationProvider>(
      `/providers/${id}`,
      { method: "GET" },
      fallback || providersState[0]
    );
  },

  async createProvider(data: ProviderCreateInput): Promise<AccommodationProvider> {
    const fallback: AccommodationProvider = {
      id: `prov-${Date.now()}`,
      tenant_id: "tenant-default",
      name: data.name,
      slug: data.slug,
      provider_type: data.provider_type,
      registration_number: data.registration_number,
      contact_name: data.contact_name,
      contact_email: data.contact_email,
      contact_phone: data.contact_phone,
      emergency_phone: data.emergency_phone,
      tax_id: data.tax_id,
      address: data.address,
      city: data.city || "Bengaluru",
      state: data.state || "Karnataka",
      mou_reference: data.mou_reference,
      mou_valid_from: data.mou_valid_from,
      mou_valid_to: data.mou_valid_to,
      verification_status: "PENDING",
      rating: 4.5,
      total_properties_managed: 0,
      total_beds_provided: 0,
      is_active: data.is_active ?? true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    providersState.unshift(fallback);
    return fetchWithFallback<AccommodationProvider>(
      "/providers",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  // =========================================================================
  // 3. ACCOMMODATION PROPERTIES
  // =========================================================================

  async listProperties(publishedOnly = false): Promise<AccommodationProperty[]> {
    const query = publishedOnly ? "?published_only=true" : "";
    return fetchWithFallback<AccommodationProperty[]>(
      `/properties${query}`,
      { method: "GET" },
      publishedOnly
        ? propertiesState.filter((p) => p.lifecycle_status === "PUBLISHED")
        : propertiesState
    );
  },

  async getProperty(id: string): Promise<AccommodationProperty> {
    const fallback = propertiesState.find((p) => p.id === id);
    return fetchWithFallback<AccommodationProperty>(
      `/properties/${id}`,
      { method: "GET" },
      fallback || propertiesState[0]
    );
  },

  async createProperty(data: PropertyCreateInput): Promise<AccommodationProperty> {
    const fallback: AccommodationProperty = {
      id: `prop-${Date.now()}`,
      tenant_id: "tenant-default",
      code: data.code,
      name: data.name,
      slug: data.slug,
      provider_id: data.provider_id,
      hostel_id: data.hostel_id,
      campus_id: data.campus_id,
      property_type: data.property_type,
      lifecycle_status: "DRAFT",
      description: data.description,
      address: data.address,
      city: data.city || "Bengaluru",
      state: data.state || "Karnataka",
      postal_code: data.postal_code,
      distance_to_campus_km: data.distance_to_campus_km ?? 1.5,
      total_rooms: 0,
      total_bed_capacity: 0,
      occupied_beds: 0,
      available_beds: 0,
      monthly_rent_min: data.monthly_rent_min ?? 6000,
      monthly_rent_max: data.monthly_rent_max ?? 12000,
      security_deposit_amount: data.security_deposit_amount ?? 15000,
      currency: data.currency || "INR",
      amenities: data.amenities || ["WIFI", "CCTV"],
      utilities_included: data.utilities_included || ["WATER", "WIFI"],
      accessibility_features: data.accessibility_features || [],
      safety_features: data.safety_features || ["FIRE_EXTINGUISHERS", "CCTV"],
      house_rules: data.house_rules,
      manager_name: data.manager_name,
      manager_phone: data.manager_phone,
      manager_email: data.manager_email,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    propertiesState.unshift(fallback);
    return fetchWithFallback<AccommodationProperty>(
      "/properties",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async transitionProperty(
    id: string,
    transition: PropertyTransitionInput
  ): Promise<AccommodationProperty> {
    const prop = propertiesState.find((p) => p.id === id);
    if (prop) {
      prop.lifecycle_status = transition.target_status;
      if (transition.approval_valid_until) {
        prop.approval_valid_until = transition.approval_valid_until;
      }
      prop.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<AccommodationProperty>(
      `/properties/${id}/transition`,
      { method: "POST", body: JSON.stringify(transition) },
      prop || propertiesState[0]
    );
  },

  // =========================================================================
  // 4. UNITS & BEDS INVENTORY
  // =========================================================================

  async listUnits(propertyId: string): Promise<AccommodationUnit[]> {
    return fetchWithFallback<AccommodationUnit[]>(
      `/units?property_id=${propertyId}`,
      { method: "GET" },
      unitsState.filter((u) => u.property_id === propertyId)
    );
  },

  async createUnit(data: UnitCreateInput): Promise<AccommodationUnit> {
    const fallback: AccommodationUnit = {
      id: `unit-${Date.now()}`,
      tenant_id: "tenant-default",
      property_id: data.property_id,
      unit_number: data.unit_number,
      unit_type: data.unit_type,
      floor_number: data.floor_number ?? 1,
      bed_capacity: data.bed_capacity,
      occupied_beds: 0,
      rent_per_bed: data.rent_per_bed,
      security_deposit_per_bed: data.security_deposit_per_bed,
      is_furnished: data.is_furnished ?? true,
      has_attached_bath: data.has_attached_bath ?? true,
      is_accessible: data.is_accessible ?? false,
      is_available: true,
      status: "AVAILABLE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    unitsState.unshift(fallback);
    return fetchWithFallback<AccommodationUnit>(
      "/units",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async blockBed(bedId: string, reason: string): Promise<AccommodationBed> {
    const fallback: AccommodationBed = {
      id: bedId,
      tenant_id: "tenant-default",
      unit_id: "unit-001",
      bed_code: "BED-BLOCKED",
      is_available: false,
      status: "BLOCKED_MAINTENANCE",
      blocked_reason: reason,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return fetchWithFallback<AccommodationBed>(
      `/beds/${bedId}/block?reason=${encodeURIComponent(reason)}`,
      { method: "POST" },
      fallback
    );
  },

  // =========================================================================
  // 5. HOUSING REQUESTS & OFFERS
  // =========================================================================

  async listRequests(status?: string): Promise<StudentHousingRequest[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithFallback<StudentHousingRequest[]>(
      `/requests${query}`,
      { method: "GET" },
      status ? requestsState.filter((r) => r.status === status) : requestsState
    );
  },

  async submitRequest(data: HousingRequestCreateInput): Promise<StudentHousingRequest> {
    const fallback: StudentHousingRequest = {
      id: `req-${Date.now()}`,
      tenant_id: "tenant-default",
      request_number: `REQ-HOU-2026-${String(requestsState.length + 1).padStart(4, "0")}`,
      student_id: "st-current-user",
      student_name: "Rahul Sharma",
      student_roll_number: "CS2026-901",
      preferred_property_id: data.preferred_property_id,
      preferred_unit_type: data.preferred_unit_type,
      academic_term: data.academic_term || "AY 2026-27 Autumn",
      requested_move_in_date: data.requested_move_in_date,
      requested_move_out_date: data.requested_move_out_date,
      budget_min: data.budget_min,
      budget_max: data.budget_max,
      accessibility_required: data.accessibility_required ?? false,
      disability_accommodation_notes: data.disability_accommodation_notes,
      dietary_preference: data.dietary_preference,
      lifestyle_preferences: {},
      special_requests: data.special_requests,
      supporting_document_ids: [],
      status: "SUBMITTED",
      priority_score: data.accessibility_required ? 85.0 : 60.0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    requestsState.unshift(fallback);
    return fetchWithFallback<StudentHousingRequest>(
      "/requests",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async reviewRequest(
    id: string,
    review: HousingRequestReviewInput
  ): Promise<StudentHousingRequest> {
    const req = requestsState.find((r) => r.id === id);
    if (req) {
      req.status = review.status;
      req.review_notes = review.review_notes;
      req.rejection_reason = review.rejection_reason;
      if (review.priority_score !== undefined) req.priority_score = review.priority_score;
      if (review.status === 'WAITLISTED' && !req.waitlist_position) {
        req.waitlist_position = 1;
      }
      req.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<StudentHousingRequest>(
      `/requests/${id}/review`,
      { method: "POST", body: JSON.stringify(review) },
      req || requestsState[0]
    );
  },

  async createOffer(data: HousingOfferCreateInput): Promise<HousingOffer> {
    const fallback: HousingOffer = {
      id: `offer-${Date.now()}`,
      tenant_id: "tenant-default",
      request_id: data.request_id,
      student_id: "st-offer-recipient",
      property_id: data.property_id,
      unit_id: data.unit_id,
      bed_id: data.bed_id,
      offered_rent_monthly: data.offered_rent_monthly,
      offered_deposit: data.offered_deposit,
      occupancy_start_date: data.occupancy_start_date,
      occupancy_end_date: data.occupancy_end_date,
      offer_valid_until: new Date(Date.now() + (data.offer_valid_days || 7) * 86400000).toISOString(),
      status: "OFFERED",
      created_at: new Date().toISOString(),
    };
    return fetchWithFallback<HousingOffer>(
      "/offers",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async respondToOffer(
    offerId: string,
    response: HousingOfferRespondInput
  ): Promise<HousingOffer> {
    const fallback: HousingOffer = {
      id: offerId,
      tenant_id: "tenant-default",
      request_id: "req-002",
      student_id: "st-002",
      property_id: "prop-002",
      unit_id: "unit-004",
      bed_id: "bed-004",
      offered_rent_monthly: 9500,
      offered_deposit: 18000,
      occupancy_start_date: "2026-08-01",
      occupancy_end_date: "2027-05-31",
      offer_valid_until: new Date().toISOString(),
      status: response.decision,
      decline_reason: response.decline_reason,
      response_notes: response.response_notes,
      responded_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    return fetchWithFallback<HousingOffer>(
      `/offers/${offerId}/respond`,
      { method: "POST", body: JSON.stringify(response) },
      fallback
    );
  },

  // =========================================================================
  // 6. ALLOCATIONS & ROOM TRANSFERS
  // =========================================================================

  async listAssignments(): Promise<HousingAssignment[]> {
    return fetchWithFallback<HousingAssignment[]>(
      "/assignments",
      { method: "GET" },
      assignmentsState
    );
  },

  async allocateStudent(data: HousingAssignmentCreateInput): Promise<HousingAssignment> {
    const fallback: HousingAssignment = {
      id: `asgn-${Date.now()}`,
      tenant_id: "tenant-default",
      assignment_number: `ASGN-HOU-2026-${String(assignmentsState.length + 1).padStart(4, "0")}`,
      student_id: data.student_id,
      property_id: data.property_id,
      unit_id: data.unit_id,
      bed_id: data.bed_id,
      start_date: data.start_date,
      end_date: data.end_date,
      monthly_rent: data.monthly_rent,
      security_deposit: data.security_deposit,
      status: "ACTIVE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    assignmentsState.unshift(fallback);
    return fetchWithFallback<HousingAssignment>(
      "/assignments",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async transferAssignment(
    assignmentId: string,
    transfer: HousingTransferInput
  ): Promise<HousingAssignment> {
    const asgn = assignmentsState.find((a) => a.id === assignmentId);
    if (asgn) {
      asgn.unit_id = transfer.target_unit_id;
      asgn.bed_id = transfer.target_bed_id;
      asgn.status = "TRANSFERRED";
      asgn.transfer_to_unit_id = transfer.target_unit_id;
      asgn.transfer_reason = transfer.transfer_reason;
      asgn.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<HousingAssignment>(
      `/assignments/${assignmentId}/transfer`,
      { method: "POST", body: JSON.stringify(transfer) },
      asgn || assignmentsState[0]
    );
  },

  // =========================================================================
  // 7. AGREEMENTS & LEASES
  // =========================================================================

  async listAgreements(): Promise<HousingAgreementReference[]> {
    return fetchWithFallback<HousingAgreementReference[]>(
      "/agreements",
      { method: "GET" },
      agreementsState
    );
  },

  async createAgreement(data: HousingAgreementCreateInput): Promise<HousingAgreementReference> {
    const fallback: HousingAgreementReference = {
      id: `agmt-${Date.now()}`,
      tenant_id: "tenant-default",
      assignment_id: data.assignment_id,
      property_id: "prop-001",
      student_id: "st-004",
      agreement_number: `AGR-HOU-2026-${String(agreementsState.length + 1).padStart(4, "0")}`,
      agreement_title: data.agreement_title,
      valid_from: data.valid_from,
      valid_to: data.valid_to,
      rent_amount: data.rent_amount,
      deposit_amount: data.deposit_amount,
      payment_frequency: data.payment_frequency || "MONTHLY",
      finance_invoice_reference: data.finance_invoice_reference,
      deposit_invoice_reference: data.deposit_invoice_reference,
      deposit_refund_status: "HELD",
      terms_and_conditions_acknowledged: true,
      status: "PENDING_SIGNATURE",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    agreementsState.unshift(fallback);
    return fetchWithFallback<HousingAgreementReference>(
      "/agreements",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  // =========================================================================
  // 8. CHECK-IN / CHECK-OUT AUDITS
  // =========================================================================

  async listCheckIns(): Promise<HousingCheckInOutRecord[]> {
    return fetchWithFallback<HousingCheckInOutRecord[]>(
      "/check-in-out",
      { method: "GET" },
      checkinsState
    );
  },

  async recordCheckInOut(data: HousingCheckInOutInput): Promise<HousingCheckInOutRecord> {
    const fallback: HousingCheckInOutRecord = {
      id: `check-${Date.now()}`,
      tenant_id: "tenant-default",
      assignment_id: data.assignment_id,
      student_id: "st-004",
      record_type: data.record_type,
      scheduled_date: data.scheduled_date,
      actual_timestamp: new Date().toISOString(),
      key_card_issued_or_returned: data.key_card_issued_or_returned ?? true,
      key_identifier: data.key_identifier,
      room_condition_rating: data.room_condition_rating || "GOOD",
      checklist_items: data.checklist_items || { room: "GOOD" },
      damage_assessed_amount: data.damage_assessed_amount || 0,
      damage_description: data.damage_description,
      photos_evidence_ids: data.photos_evidence_ids || [],
      student_signature_confirmed: data.student_signature_confirmed ?? true,
      notes: data.notes,
      status: "COMPLETED",
      created_at: new Date().toISOString(),
    };
    checkinsState.unshift(fallback);
    return fetchWithFallback<HousingCheckInOutRecord>(
      "/check-in-out",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  // =========================================================================
  // 9. INSPECTIONS & COMPLIANCE
  // =========================================================================

  async listInspections(propertyId?: string): Promise<HousingPropertyInspection[]> {
    const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
    return fetchWithFallback<HousingPropertyInspection[]>(
      `/inspections${query}`,
      { method: "GET" },
      propertyId ? inspectionsState.filter((i) => i.property_id === propertyId) : inspectionsState
    );
  },

  async recordInspection(data: HousingInspectionCreateInput): Promise<HousingPropertyInspection> {
    const isFailed =
      data.overall_outcome === "FAILED_CRITICAL" || data.critical_issues_found;
    const fallback: HousingPropertyInspection = {
      id: `insp-${Date.now()}`,
      tenant_id: "tenant-default",
      property_id: data.property_id,
      inspection_code: `INSP-HOU-2026-${String(inspectionsState.length + 1).padStart(4, "0")}`,
      inspector_user_id: "user-admin-01",
      inspector_name: "Chief Safety Officer",
      inspection_date: data.inspection_date,
      inspection_type: data.inspection_type || "SAFETY_FIRE",
      overall_outcome: data.overall_outcome || "PASSED",
      safety_score: data.safety_score ?? (isFailed ? 45.0 : 96.0),
      checklist_results: data.checklist_results || { fire_safety: isFailed ? "FAILED" : "PASSED" },
      critical_issues_found: Boolean(isFailed),
      availability_suspended: Boolean(isFailed),
      corrective_actions_required: data.corrective_actions_required,
      corrective_action_deadline: data.corrective_action_deadline,
      reinspection_due_date: data.reinspection_due_date,
      compliance_status: isFailed ? "NON_COMPLIANT_SUSPENDED" : "COMPLIANT",
      created_at: new Date().toISOString(),
    };
    inspectionsState.unshift(fallback);

    // If critical failure, auto-suspend property
    if (isFailed) {
      const prop = propertiesState.find((p) => p.id === data.property_id);
      if (prop) {
        prop.lifecycle_status = "SUSPENDED";
      }
    }

    return fetchWithFallback<HousingPropertyInspection>(
      "/inspections",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  // =========================================================================
  // 10. MAINTENANCE & SERVICE REQUESTS
  // =========================================================================

  async listMaintenance(propertyId?: string): Promise<HousingMaintenanceRequest[]> {
    const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
    return fetchWithFallback<HousingMaintenanceRequest[]>(
      `/maintenance${query}`,
      { method: "GET" },
      propertyId ? maintenanceState.filter((m) => m.property_id === propertyId) : maintenanceState
    );
  },

  async submitMaintenance(data: HousingMaintenanceCreateInput): Promise<HousingMaintenanceRequest> {
    const fallback: HousingMaintenanceRequest = {
      id: `maint-${Date.now()}`,
      tenant_id: "tenant-default",
      property_id: data.property_id,
      unit_id: data.unit_id,
      reported_by_user_id: "user-current",
      reporter_name: "Resident Student",
      category: data.category || "PLUMBING",
      priority: data.priority || "MEDIUM",
      title: data.title,
      description: data.description,
      photo_urls: data.photo_urls || [],
      status: "REPORTED",
      cost_charged_to: "INSTITUTION_MAINTENANCE_BUDGET",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    maintenanceState.unshift(fallback);
    return fetchWithFallback<HousingMaintenanceRequest>(
      "/maintenance",
      { method: "POST", body: JSON.stringify(data) },
      fallback
    );
  },

  async updateMaintenance(
    id: string,
    update: HousingMaintenanceUpdateInput
  ): Promise<HousingMaintenanceRequest> {
    const ticket = maintenanceState.find((m) => m.id === id);
    if (ticket) {
      ticket.status = update.status;
      if (update.assigned_technician_name) ticket.assigned_technician_name = update.assigned_technician_name;
      if (update.assigned_vendor_name) ticket.assigned_vendor_name = update.assigned_vendor_name;
      if (update.scheduled_visit_date) ticket.scheduled_visit_date = update.scheduled_visit_date;
      if (update.completion_notes) ticket.completion_notes = update.completion_notes;
      if (update.tenant_satisfaction_rating) ticket.tenant_satisfaction_rating = update.tenant_satisfaction_rating;
      if (update.tenant_feedback) ticket.tenant_feedback = update.tenant_feedback;
      if (update.status === "COMPLETED" && !ticket.completed_at) {
        ticket.completed_at = new Date().toISOString();
      }
      ticket.updated_at = new Date().toISOString();
    }
    return fetchWithFallback<HousingMaintenanceRequest>(
      `/maintenance/${id}`,
      { method: "PUT", body: JSON.stringify(update) },
      ticket || maintenanceState[0]
    );
  },

  async verifyProvider(id: string, isVerified: boolean, notes?: string): Promise<AccommodationProvider> {
    const prov = providersState.find((p) => p.id === id);
    if (prov) {
      prov.verification_status = isVerified ? "VERIFIED" : "SUSPENDED";
      prov.verification_notes = notes;
      prov.verified_at = new Date().toISOString();
      return prov;
    }
    return providersState[0];
  },

  async toggleBedBlock(bedId: string, isBlocked: boolean, reason?: string): Promise<AccommodationBed> {
    for (const unit of unitsState) {
      const bed = unit.beds?.find((b) => b.id === bedId);
      if (bed) {
        bed.status = isBlocked ? "BLOCKED_MAINTENANCE" : "AVAILABLE";
        bed.is_available = !isBlocked;
        bed.blocked_reason = isBlocked ? reason : undefined;
        return bed;
      }
    }
    return {
      id: bedId,
      tenant_id: "tenant-default",
      unit_id: "unit-001",
      bed_code: "BED-01",
      status: isBlocked ? "BLOCKED_MAINTENANCE" : "AVAILABLE",
      is_available: !isBlocked,
      blocked_reason: isBlocked ? reason : undefined,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  },

  async listOffers(requestId?: string): Promise<HousingOffer[]> {
    return requestId ? offersState.filter((o) => o.request_id === requestId) : offersState;
  },

  async transferRoom(assignmentId: string, data: HousingTransferInput): Promise<HousingAssignment> {
    return this.transferAssignment(assignmentId, data);
  },

  async respondOffer(offerId: string, data: HousingOfferRespondInput): Promise<HousingOffer> {
    return this.respondToOffer(offerId, data);
  },
};
