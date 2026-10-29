/**
 * CampusOS Residential Life, Hostel Administration, Room Allocation & Student Accommodation Service
 *
 * Product Principle: "One Campus. One System. One Source of Truth."
 * Connects directly to backend API routes at `/api/v1/residential/...`
 */

import { apiFetch, apiFetchPaginated } from "@/lib/api-client";
import { ApiResponse } from "@campusos/types";

export interface HostelFacility {
  id: string;
  tenant_id: string;
  campus_id: string;
  code: string;
  name: string;
  gender: "MALE" | "FEMALE" | "CO_ED";
  hostel_type: "BOYS" | "GIRLS" | "CO_ED" | "INTERNATIONAL" | "POSTGRADUATE" | "STAFF" | "SPECIAL";
  status: "ACTIVE" | "INACTIVE" | "MAINTENANCE" | "DECOMMISSIONED";
  description?: string;
  address?: string;
  curfew_time?: string;
  contact_phone?: string;
  contact_email?: string;
  rules_summary?: string;
  amenities?: string[];
  visitor_policy?: Record<string, any>;
  emergency_contacts?: any[];
  warden_user_id?: string;
  assistant_warden_user_id?: string;
  created_at: string;
  updated_at: string;
}

export interface HostelBlock {
  id: string;
  hostel_id: string;
  name: string;
  code?: string;
  description?: string;
}

export interface HostelFloor {
  id: string;
  block_id: string;
  floor_number: number;
  name?: string;
  is_accessible: boolean;
}

export interface HostelRoom {
  id: string;
  floor_id: string;
  room_number: string;
  room_type: "SINGLE" | "DOUBLE" | "TRIPLE" | "FOUR_SHARING" | "DORMITORY" | "ACCESSIBLE" | "STUDY_SUITE";
  capacity: number;
  current_occupancy: number;
  is_accessible: boolean;
  is_air_conditioned: boolean;
  has_attached_bathroom: boolean;
  status: string;
  amenities?: string[];
  restrictions?: Record<string, any>;
  beds?: HostelBed[];
}

export interface HostelBed {
  id: string;
  room_id: string;
  bed_code: string;
  is_available: boolean;
  status: "AVAILABLE" | "RESERVED" | "OCCUPIED" | "BLOCKED" | "UNDER_MAINTENANCE" | "RETIRED";
  blocked_reason?: string;
  blocked_until?: string;
  reserved_until?: string;
}

export interface HostelOccupancyStat {
  hostel_id: string;
  hostel_name: string;
  hostel_code: string;
  total_beds: number;
  occupied_beds: number;
  reserved_beds: number;
  available_beds: number;
  blocked_beds: number;
  occupancy_percentage: number;
}

export interface OccupancyDashboardResponse {
  overall_total_beds: number;
  overall_occupied_beds: number;
  overall_reserved_beds: number;
  overall_available_beds: number;
  overall_blocked_beds: number;
  overall_occupancy_percentage: number;
  hostel_stats: HostelOccupancyStat[];
}

export interface AccommodationApplication {
  id: string;
  tenant_id: string;
  cycle_id: string;
  student_id: string;
  application_number: string;
  preferred_hostel_id?: string;
  preferred_room_type?: string;
  requires_accessibility: boolean;
  accessibility_notes?: string;
  dietary_preference?: string;
  medical_conditions?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  priority_score: number;
  status: "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "WAITLISTED" | "REJECTED" | "WITHDRAWN" | "ALLOCATED";
  reviewer_user_id?: string;
  review_notes?: string;
  reviewed_at?: string;
  allocated_bed_id?: string;
  created_at: string;
}

export interface HostelAllocation {
  id: string;
  tenant_id: string;
  bed_id: string;
  student_id: string;
  academic_year_id: string;
  application_id?: string;
  status: "RESERVED" | "ALLOCATED" | "CHECKED_IN" | "CHECKED_OUT" | "TRANSFERRED" | "CANCELLED";
  check_in_date: string;
  expected_check_out_date?: string;
  allocated_by_user_id?: string;
  special_considerations?: string;
  bed?: HostelBed;
  created_at: string;
}

export interface HostelResident {
  id: string;
  tenant_id: string;
  allocation_id: string;
  student_id: string;
  bed_id: string;
  hostel_id: string;
  academic_year_id: string;
  status: "PENDING_CHECKIN" | "CHECKED_IN" | "ACTIVE" | "TEMPORARILY_ABSENT" | "CHECKED_OUT" | "TRANSFERRED" | "EVICTED";
  check_in_time: string;
  checked_in_by_user_id?: string;
  key_card_issued: boolean;
  key_number?: string;
  facilities_condition_note?: string;
  inventory_handover?: Record<string, boolean>;
  expected_departure_date?: string;
  check_out_time?: string;
  checked_out_by_user_id?: string;
  checkout_reason?: string;
  room_condition_on_checkout?: string;
  key_returned: boolean;
  damage_assessment_notes?: string;
  damage_charges_amount: number;
  damage_invoice_id?: string;
  cleared_by_finance: boolean;
}

export interface HostelFeePlan {
  id: string;
  code: string;
  name: string;
  hostel_id?: string;
  room_type: string;
  billing_cycle: string;
  rent_amount: number;
  mess_amount: number;
  deposit_amount: number;
  utility_amount: number;
  amenities_amount: number;
  total_amount: number;
  is_active: boolean;
}

export interface HostelMealPlan {
  id: string;
  code: string;
  name: string;
  hostel_id?: string;
  meal_type: string;
  monthly_rate: number;
  daily_rate: number;
  serves_breakfast: boolean;
  serves_lunch: boolean;
  serves_snacks: boolean;
  serves_dinner: boolean;
  is_active: boolean;
}

export interface HostelLeavePass {
  id: string;
  student_id: string;
  hostel_id?: string;
  outing_type: string;
  pass_code?: string;
  departure_time: string;
  expected_return_time: string;
  actual_departure_time?: string;
  actual_return_time?: string;
  destination?: string;
  reason: string;
  parent_consent_verified: boolean;
  status: string;
}

export interface HostelGatePass {
  id: string;
  resident_id: string;
  student_id: string;
  hostel_id: string;
  pass_code: string;
  purpose: string;
  destination?: string;
  valid_from: string;
  valid_until: string;
  status: string;
  actual_exit_time?: string;
  actual_entry_time?: string;
}

export interface HostelVisitor {
  id: string;
  hostel_id: string;
  host_student_id: string;
  visitor_name: string;
  visitor_phone: string;
  visitor_relation: string;
  purpose: string;
  pass_code: string;
  expected_check_in: string;
  expected_check_out: string;
  actual_check_in?: string;
  actual_check_out?: string;
  status: string;
}

export interface HostelComplaint {
  id: string;
  ticket_number: string;
  student_id: string;
  hostel_id?: string;
  room_id: string;
  work_order_id?: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  status: string;
  sla_deadline?: string;
  resolved_at?: string;
}

export interface HostelIncident {
  id: string;
  incident_number: string;
  hostel_id: string;
  incident_type: string;
  severity: string;
  incident_time: string;
  location_description: string;
  description: string;
  action_taken?: string;
  status: string;
}

class ResidentialService {
  // 1. Hostels & Hierarchy
  async listHostels(params?: { campus_id?: string; status?: string; search?: string }): Promise<ApiResponse<HostelFacility[]>> {
    const query = new URLSearchParams();
    if (params?.campus_id && params.campus_id !== "ALL") query.append("campus_id", params.campus_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelFacility[]>(`/api/v1/residential/hostels${qs}`);
  }

  async getHostelById(id: string): Promise<ApiResponse<HostelFacility>> {
    return apiFetch<HostelFacility>(`/api/v1/residential/hostels/${id}`);
  }

  async createHostel(payload: Partial<HostelFacility>): Promise<ApiResponse<HostelFacility>> {
    return apiFetch<HostelFacility>("/api/v1/residential/hostels", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async updateHostel(id: string, payload: Partial<HostelFacility>): Promise<ApiResponse<HostelFacility>> {
    return apiFetch<HostelFacility>(`/api/v1/residential/hostels/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  // 2. Rooms & Bed Inventory
  async listRooms(params?: { hostel_id?: string; floor_id?: string; room_type?: string }): Promise<ApiResponse<HostelRoom[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.floor_id) query.append("floor_id", params.floor_id);
    if (params?.room_type && params.room_type !== "ALL") query.append("room_type", params.room_type);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelRoom[]>(`/api/v1/residential/rooms${qs}`);
  }

  async listBeds(params?: { hostel_id?: string; room_id?: string; status?: string; is_available?: boolean }): Promise<ApiResponse<HostelBed[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.room_id) query.append("room_id", params.room_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    if (params?.is_available !== undefined) query.append("is_available", String(params.is_available));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelBed[]>(`/api/v1/residential/beds${qs}`);
  }

  async blockBed(bedId: string, blockedReason: string, blockedUntil?: string): Promise<ApiResponse<HostelBed>> {
    return apiFetch<HostelBed>(`/api/v1/residential/beds/${bedId}/block`, {
      method: "POST",
      body: JSON.stringify({ blocked_reason: blockedReason, blocked_until: blockedUntil }),
    });
  }

  async unblockBed(bedId: string): Promise<ApiResponse<HostelBed>> {
    return apiFetch<HostelBed>(`/api/v1/residential/beds/${bedId}/unblock`, {
      method: "POST",
    });
  }

  // 3. Occupancy Dashboard
  async getOccupancyDashboard(campusId?: string): Promise<ApiResponse<OccupancyDashboardResponse>> {
    const qs = campusId && campusId !== "ALL" ? `?campus_id=${campusId}` : "";
    return apiFetch<OccupancyDashboardResponse>(`/api/v1/residential/occupancy/dashboard${qs}`);
  }

  async getOccupancyReport(hostelId?: string, campusId?: string): Promise<ApiResponse<OccupancyDashboardResponse>> {
    const query = new URLSearchParams();
    if (hostelId && hostelId !== "ALL") query.append("hostel_id", hostelId);
    if (campusId && campusId !== "ALL") query.append("campus_id", campusId);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<OccupancyDashboardResponse>(`/api/v1/residential/reports/occupancy${qs}`);
  }

  // 4. Applications & Allocations
  async listApplications(params?: { cycle_id?: string; status?: string }): Promise<ApiResponse<AccommodationApplication[]>> {
    const query = new URLSearchParams();
    if (params?.cycle_id) query.append("cycle_id", params.cycle_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<AccommodationApplication[]>(`/api/v1/residential/applications${qs}`);
  }

  async reviewApplication(applicationId: string, payload: { status: string; review_notes?: string }): Promise<ApiResponse<AccommodationApplication>> {
    return apiFetch<AccommodationApplication>(`/api/v1/residential/applications/${applicationId}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listAllocations(params?: { hostel_id?: string; student_id?: string; status?: string }): Promise<ApiResponse<HostelAllocation[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.student_id) query.append("student_id", params.student_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelAllocation[]>(`/api/v1/residential/allocations${qs}`);
  }

  async allocateBed(payload: { bed_id: string; student_id: string; academic_year_id: string; check_in_date: string; special_considerations?: string }): Promise<ApiResponse<HostelAllocation>> {
    return apiFetch<HostelAllocation>("/api/v1/residential/allocations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async transferAllocation(allocationId: string, payload: { new_bed_id: string; reason: string }): Promise<ApiResponse<HostelAllocation>> {
    return apiFetch<HostelAllocation>(`/api/v1/residential/allocations/${allocationId}/transfer`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // 5. Resident Lifecycle (Check-In & Check-Out)
  async checkInResident(allocationId: string, payload: { key_number?: string; facilities_condition_note?: string; inventory_handover?: Record<string, boolean>; expected_departure_date?: string }): Promise<ApiResponse<HostelResident>> {
    return apiFetch<HostelResident>(`/api/v1/residential/residents/${allocationId}/check-in`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async checkOutResident(residentId: string, payload: { checkout_reason: string; room_condition_on_checkout?: string; key_returned?: boolean; damage_assessment_notes?: string; damage_charges_amount?: number }): Promise<ApiResponse<HostelResident>> {
    return apiFetch<HostelResident>(`/api/v1/residential/residents/${residentId}/check-out`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // 6. Fees & Meal Plans
  async listFeePlans(params?: { hostel_id?: string; is_active?: boolean }): Promise<ApiResponse<HostelFeePlan[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.is_active !== undefined) query.append("is_active", String(params.is_active));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelFeePlan[]>(`/api/v1/residential/fee-plans${qs}`);
  }

  async listMealPlans(params?: { hostel_id?: string; is_active?: boolean }): Promise<ApiResponse<HostelMealPlan[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.is_active !== undefined) query.append("is_active", String(params.is_active));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelMealPlan[]>(`/api/v1/residential/meal-plans${qs}`);
  }

  // 7. Movement, Visitors & Gate Passes
  async listOutings(params?: { student_id?: string; hostel_id?: string; status?: string }): Promise<ApiResponse<HostelLeavePass[]>> {
    const query = new URLSearchParams();
    if (params?.student_id) query.append("student_id", params.student_id);
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelLeavePass[]>(`/api/v1/residential/outings${qs}`);
  }

  async requestOuting(payload: Partial<HostelLeavePass>): Promise<ApiResponse<HostelLeavePass>> {
    return apiFetch<HostelLeavePass>("/api/v1/residential/outings", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listGatePasses(params?: { resident_id?: string; status?: string }): Promise<ApiResponse<HostelGatePass[]>> {
    const query = new URLSearchParams();
    if (params?.resident_id) query.append("resident_id", params.resident_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelGatePass[]>(`/api/v1/residential/gate-passes${qs}`);
  }

  async verifyGatePass(passId: string, payload: { pass_code: string; action: "EXIT" | "ENTRY" }): Promise<ApiResponse<HostelGatePass>> {
    return apiFetch<HostelGatePass>(`/api/v1/residential/gate-passes/${passId}/verify`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listVisitors(params?: { hostel_id?: string; status?: string }): Promise<ApiResponse<HostelVisitor[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelVisitor[]>(`/api/v1/residential/visitors${qs}`);
  }

  async registerVisitor(payload: Partial<HostelVisitor>): Promise<ApiResponse<HostelVisitor>> {
    return apiFetch<HostelVisitor>("/api/v1/residential/visitors", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // 8. Service Requests & Complaints
  async listServiceRequests(params?: { hostel_id?: string; category?: string; status?: string }): Promise<ApiResponse<HostelComplaint[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.category && params.category !== "ALL") query.append("category", params.category);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelComplaint[]>(`/api/v1/residential/service-requests${qs}`);
  }

  async createServiceRequest(payload: Partial<HostelComplaint>): Promise<ApiResponse<HostelComplaint>> {
    return apiFetch<HostelComplaint>("/api/v1/residential/service-requests", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // 9. Safety & Incidents
  async listIncidents(params?: { hostel_id?: string; severity?: string; status?: string }): Promise<ApiResponse<HostelIncident[]>> {
    const query = new URLSearchParams();
    if (params?.hostel_id) query.append("hostel_id", params.hostel_id);
    if (params?.severity && params.severity !== "ALL") query.append("severity", params.severity);
    if (params?.status && params.status !== "ALL") query.append("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<HostelIncident[]>(`/api/v1/residential/incidents${qs}`);
  }

  async reportIncident(payload: Partial<HostelIncident>): Promise<ApiResponse<HostelIncident>> {
    return apiFetch<HostelIncident>("/api/v1/residential/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}

export const residentialService = new ResidentialService();
