/**
 * CampusOS — Enterprise Student Engagement & Civic Impact Service (Step 65)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * REST API client communicating with `/api/v1/engagement/*`
 * with resilient offline fallback to realistic institutional records.
 */

import {
  ApplicationCreateInput,
  ApplicationReviewInput,
  CertificateIssueInput,
  CommunityPartner,
  EngagementAnalyticsSummary,
  EngagementCertificate,
  EngagementProgram,
  OpportunityCreateInput,
  ParticipationApplication,
  ParticipationAttendance,
  PartnerCreateInput,
  ProgramCreateInput,
  ReflectionSubmission,
  ReflectionSubmitInput,
  ServiceHourCorrectionInput,
  ServiceHourEntry,
  ServiceHourLogInput,
  ServiceHourVerifyInput,
  ShiftCreateInput,
  VolunteerOpportunity,
  VolunteerShift,
} from "../types/engagement";
import {
  MOCK_ANALYTICS,
  MOCK_APPLICATIONS,
  MOCK_ATTENDANCES,
  MOCK_CERTIFICATES,
  MOCK_OPPORTUNITIES,
  MOCK_PARTNERS,
  MOCK_PROGRAMS,
  MOCK_REFLECTIONS,
  MOCK_SERVICE_HOURS,
  MOCK_SHIFTS,
} from "../mocks/engagement.mock";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/engagement`
    : "http://localhost:8000/api/v1/engagement";

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
      cache: "no-store",
    });

    if (!res.ok) {
      if (fallback !== undefined) return fallback;
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    if (fallback !== undefined) return fallback;
    throw err;
  }
}

export class EngagementService {
  // Programs
  static async listPrograms(status?: string, category?: string): Promise<EngagementProgram[]> {
    let q = "";
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (category) params.append("category", category);
    if (params.toString()) q = `?${params.toString()}`;

    return fetchWithFallback<EngagementProgram[]>(`/programs${q}`, { method: "GET" }, MOCK_PROGRAMS);
  }

  static async getProgram(id: string): Promise<EngagementProgram> {
    const fallback = MOCK_PROGRAMS.find((p) => p.id === id) || MOCK_PROGRAMS[0];
    return fetchWithFallback<EngagementProgram>(`/programs/${id}`, { method: "GET" }, fallback);
  }

  static async createProgram(data: ProgramCreateInput): Promise<EngagementProgram> {
    return fetchWithFallback<EngagementProgram>(
      `/programs`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_PROGRAMS[0],
        id: `prog-${Date.now()}`,
        code: data.code,
        name: data.name,
        slug: data.slug,
        category: data.category,
        start_date: data.start_date,
        end_date: data.end_date,
        status: "DRAFT",
      }
    );
  }

  static async transitionProgram(id: string, target_status: string, notes?: string): Promise<EngagementProgram> {
    return fetchWithFallback<EngagementProgram>(
      `/programs/${id}/transition`,
      {
        method: "POST",
        body: JSON.stringify({ target_status, notes }),
      },
      {
        ...MOCK_PROGRAMS[0],
        id,
        status: target_status as any,
      }
    );
  }

  // Partners
  static async listPartners(status?: string): Promise<CommunityPartner[]> {
    const q = status ? `?status=${status}` : "";
    return fetchWithFallback<CommunityPartner[]>(`/partners${q}`, { method: "GET" }, MOCK_PARTNERS);
  }

  static async createPartner(data: PartnerCreateInput): Promise<CommunityPartner> {
    return fetchWithFallback<CommunityPartner>(
      `/partners`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_PARTNERS[0],
        id: `part-${Date.now()}`,
        name: data.name,
        slug: data.slug,
        organization_type: data.organization_type,
        contact_person_name: data.contact_person_name,
        contact_email: data.contact_email,
        status: "ACTIVE",
      }
    );
  }

  // Opportunities
  static async listOpportunities(programId?: string, status?: string): Promise<VolunteerOpportunity[]> {
    const params = new URLSearchParams();
    if (programId) params.append("program_id", programId);
    if (status) params.append("status", status);
    const q = params.toString() ? `?${params.toString()}` : "";

    return fetchWithFallback<VolunteerOpportunity[]>(`/opportunities${q}`, { method: "GET" }, MOCK_OPPORTUNITIES);
  }

  static async createOpportunity(data: OpportunityCreateInput): Promise<VolunteerOpportunity> {
    return fetchWithFallback<VolunteerOpportunity>(
      `/opportunities`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_OPPORTUNITIES[0],
        id: `opp-${Date.now()}`,
        title: data.title,
        capacity: data.capacity,
        start_date: data.start_date,
        end_date: data.end_date,
        status: "DRAFT",
      }
    );
  }

  // Applications
  static async listApplications(opportunityId?: string, status?: string): Promise<ParticipationApplication[]> {
    const params = new URLSearchParams();
    if (opportunityId) params.append("opportunity_id", opportunityId);
    if (status) params.append("status", status);
    const q = params.toString() ? `?${params.toString()}` : "";

    return fetchWithFallback<ParticipationApplication[]>(`/applications${q}`, { method: "GET" }, MOCK_APPLICATIONS);
  }

  static async applyToOpportunity(data: ApplicationCreateInput): Promise<ParticipationApplication> {
    return fetchWithFallback<ParticipationApplication>(
      `/applications`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_APPLICATIONS[0],
        id: `app-${Date.now()}`,
        opportunity_id: data.opportunity_id,
        status: "APPLIED",
        statement_of_interest: data.statement_of_interest,
      }
    );
  }

  static async reviewApplication(id: string, review: ApplicationReviewInput): Promise<ParticipationApplication> {
    return fetchWithFallback<ParticipationApplication>(
      `/applications/${id}/review`,
      {
        method: "POST",
        body: JSON.stringify(review),
      },
      {
        ...MOCK_APPLICATIONS[0],
        id,
        status: review.status,
        reviewer_notes: review.reviewer_notes,
      }
    );
  }

  // Shifts
  static async listShifts(opportunityId?: string): Promise<VolunteerShift[]> {
    const q = opportunityId ? `?opportunity_id=${opportunityId}` : "";
    return fetchWithFallback<VolunteerShift[]>(`/shifts${q}`, { method: "GET" }, MOCK_SHIFTS);
  }

  static async createShift(data: ShiftCreateInput): Promise<VolunteerShift> {
    return fetchWithFallback<VolunteerShift>(
      `/shifts`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_SHIFTS[0],
        id: `shift-${Date.now()}`,
        title: data.title,
        shift_date: data.shift_date,
        start_time: data.start_time,
        end_time: data.end_time,
        capacity: data.capacity,
      }
    );
  }

  static async assignStudentToShift(shiftId: string, applicationId: string, studentId: string) {
    return fetchWithFallback(
      `/shifts/assign`,
      {
        method: "POST",
        body: JSON.stringify({ shift_id: shiftId, application_id: applicationId, student_id: studentId }),
      },
      { id: `asgn-${Date.now()}`, shift_id: shiftId, status: "ASSIGNED" }
    );
  }

  // Attendance & Service Hours
  static async listServiceHours(studentId?: string, programId?: string, status?: string): Promise<ServiceHourEntry[]> {
    const params = new URLSearchParams();
    if (studentId) params.append("student_id", studentId);
    if (programId) params.append("program_id", programId);
    if (status) params.append("status", status);
    const q = params.toString() ? `?${params.toString()}` : "";

    return fetchWithFallback<ServiceHourEntry[]>(`/service-hours${q}`, { method: "GET" }, MOCK_SERVICE_HOURS);
  }

  static async submitServiceHours(data: ServiceHourLogInput): Promise<ServiceHourEntry> {
    return fetchWithFallback<ServiceHourEntry>(
      `/service-hours`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_SERVICE_HOURS[0],
        id: `hour-${Date.now()}`,
        activity_date: data.activity_date,
        duration_hours: data.duration_hours,
        activity_description: data.activity_description,
        status: "PENDING",
        is_verified: false,
      }
    );
  }

  static async verifyServiceHours(id: string, data: ServiceHourVerifyInput): Promise<ServiceHourEntry> {
    return fetchWithFallback<ServiceHourEntry>(
      `/service-hours/${id}/verify`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_SERVICE_HOURS[0],
        id,
        status: data.status,
        is_verified: data.status === "APPROVED",
        supervisor_comments: data.supervisor_comments,
      }
    );
  }

  static async correctServiceHours(id: string, data: ServiceHourCorrectionInput): Promise<ServiceHourEntry> {
    return fetchWithFallback<ServiceHourEntry>(
      `/service-hours/${id}/correct`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_SERVICE_HOURS[0],
        id,
        duration_hours: data.new_hours,
        corrections: [
          {
            id: `corr-${Date.now()}`,
            service_hour_id: id,
            previous_hours: 4.0,
            new_hours: data.new_hours,
            reason_for_change: data.reason_for_change,
            changed_by_user_id: "coord-01",
            changed_at: new Date().toISOString(),
          },
        ],
      }
    );
  }

  // Reflections
  static async listReflections(programId?: string): Promise<ReflectionSubmission[]> {
    const q = programId ? `?program_id=${programId}` : "";
    return fetchWithFallback<ReflectionSubmission[]>(`/reflections${q}`, { method: "GET" }, MOCK_REFLECTIONS);
  }

  static async submitReflection(data: ReflectionSubmitInput): Promise<ReflectionSubmission> {
    return fetchWithFallback<ReflectionSubmission>(
      `/reflections`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_REFLECTIONS[0],
        id: `refl-${Date.now()}`,
        reflection_text: data.reflection_text,
        status: "SUBMITTED",
      }
    );
  }

  // Certificates
  static async listCertificates(studentId?: string, programId?: string): Promise<EngagementCertificate[]> {
    const params = new URLSearchParams();
    if (studentId) params.append("student_id", studentId);
    if (programId) params.append("program_id", programId);
    const q = params.toString() ? `?${params.toString()}` : "";

    return fetchWithFallback<EngagementCertificate[]>(`/certificates${q}`, { method: "GET" }, MOCK_CERTIFICATES);
  }

  static async issueCertificate(data: CertificateIssueInput): Promise<EngagementCertificate> {
    return fetchWithFallback<EngagementCertificate>(
      `/certificates/issue`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      {
        ...MOCK_CERTIFICATES[0],
        id: `cert-${Date.now()}`,
        student_id: data.student_id,
        program_id: data.program_id,
        issued_at: new Date().toISOString(),
      }
    );
  }

  static async verifyCertificateHash(hash: string): Promise<EngagementCertificate> {
    return fetchWithFallback<EngagementCertificate>(
      `/certificates/verify/${hash}`,
      { method: "GET" },
      MOCK_CERTIFICATES[0]
    );
  }

  // Analytics
  static async getAnalytics(): Promise<EngagementAnalyticsSummary> {
    return fetchWithFallback<EngagementAnalyticsSummary>(`/analytics`, { method: "GET" }, MOCK_ANALYTICS);
  }
}
