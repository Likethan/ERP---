/**
 * Client Service for International Relations, Student Exchange & Global Mobility (Step 60)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Provides typed REST API calls to `/api/v1/international-relations/...`
 * with resilient offline fallback to realistic mock data.
 */

import {
  AgreementAmendment,
  CourseEquivalencyMapping,
  CreditTransferRequest,
  FacultyMobilityRecord,
  InboundStudentProfile,
  InstitutionalAgreement,
  InternationalDashboardMetrics,
  InternationalPartner,
  InternationalPolicyConfig,
  MobilityApplication,
  MobilityDocument,
  MobilityFundingRequest,
  MobilityProgram,
  MobilityScholarship,
} from "@/types/international";
import {
  MOCK_AGREEMENTS,
  MOCK_APPLICATIONS,
  MOCK_CREDIT_TRANSFERS,
  MOCK_DASHBOARD_METRICS,
  MOCK_DOCUMENTS,
  MOCK_EQUIVALENCIES,
  MOCK_FACULTY_MOBILITIES,
  MOCK_FUNDING_REQUESTS,
  MOCK_INBOUND_STUDENTS,
  MOCK_PARTNERS,
  MOCK_POLICY_CONFIG,
  MOCK_PROGRAMS,
  MOCK_SCHOLARSHIPS,
} from "@/mocks/international.mock";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/international-relations";

async function fetchWithFallback<T>(url: string, options?: RequestInit, fallback?: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      credentials: "include",
    });

    if (!res.ok) {
      if (fallback !== undefined) return fallback;
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (fallback !== undefined) return fallback;
    throw err;
  }
}

export const internationalService = {
  // --------------------------------------------------------------------------
  // Dashboard & Policy
  // --------------------------------------------------------------------------
  async getDashboardMetrics(): Promise<InternationalDashboardMetrics> {
    return fetchWithFallback<InternationalDashboardMetrics>("/dashboard/metrics", {}, MOCK_DASHBOARD_METRICS);
  },

  async getPolicyConfig(): Promise<InternationalPolicyConfig> {
    return fetchWithFallback<InternationalPolicyConfig>("/config", {}, MOCK_POLICY_CONFIG);
  },

  async updatePolicyConfig(data: Partial<InternationalPolicyConfig>): Promise<InternationalPolicyConfig> {
    return fetchWithFallback<InternationalPolicyConfig>(
      "/config",
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      { ...MOCK_POLICY_CONFIG, ...data }
    );
  },

  // --------------------------------------------------------------------------
  // Partners
  // --------------------------------------------------------------------------
  async getPartners(params?: {
    country_code?: string;
    category?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<InternationalPartner[]> {
    const query = new URLSearchParams();
    if (params?.country_code) query.set("country_code", params.country_code);
    if (params?.category) query.set("category", params.category);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params?.search) query.set("search", params.search);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<InternationalPartner[]>("/partners" + qs, {}, MOCK_PARTNERS);
  },

  async getPartner(id: string): Promise<InternationalPartner> {
    const fallback = MOCK_PARTNERS.find((p) => p.id === id) || MOCK_PARTNERS[0];
    return fetchWithFallback<InternationalPartner>(`/partners/${id}`, {}, fallback);
  },

  async createPartner(data: Partial<InternationalPartner>): Promise<InternationalPartner> {
    const newId = `par-${Date.now().toString(36)}`;
    const created: InternationalPartner = {
      id: newId,
      partner_name: data.partner_name || data.partnerName || "New Partner",
      partnerName: data.partner_name || data.partnerName || "New Partner",
      country_name: data.country_name || data.countryName || "Unknown",
      countryName: data.country_name || data.countryName || "Unknown",
      country_code: data.country_code || data.countryCode || "XX",
      countryCode: data.country_code || data.countryCode || "XX",
      city: data.city || "",
      official_website: data.official_website || data.officialWebsite || "",
      category: data.category || "UNIVERSITY",
      is_active: data.is_active ?? true,
      primary_contact_name: data.primary_contact_name || data.primaryContactName || "",
      primary_contact_email: data.primary_contact_email || data.primaryContactEmail || "",
      ...data,
    } as InternationalPartner;

    return fetchWithFallback<InternationalPartner>(
      "/partners",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  // --------------------------------------------------------------------------
  // Agreements & MoUs
  // --------------------------------------------------------------------------
  async getAgreements(params?: {
    partner_id?: string;
    status?: string;
    expiring_soon?: boolean;
  }): Promise<InstitutionalAgreement[]> {
    const query = new URLSearchParams();
    if (params?.partner_id) query.set("partner_id", params.partner_id);
    if (params?.status) query.set("status", params.status);
    if (params?.expiring_soon) query.set("expiring_soon", "true");

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<InstitutionalAgreement[]>("/agreements" + qs, {}, MOCK_AGREEMENTS);
  },

  async getAgreement(id: string): Promise<InstitutionalAgreement> {
    const fallback = MOCK_AGREEMENTS.find((a) => a.id === id) || MOCK_AGREEMENTS[0];
    return fetchWithFallback<InstitutionalAgreement>(`/agreements/${id}`, {}, fallback);
  },

  async createAgreement(data: Partial<InstitutionalAgreement>): Promise<InstitutionalAgreement> {
    const created: InstitutionalAgreement = {
      id: `agr-${Date.now().toString(36)}`,
      partner_id: data.partner_id || data.partnerId || "",
      agreement_reference_number: data.agreement_reference_number || data.agreementReferenceNumber || `MOU-${Date.now().toString(36).toUpperCase()}`,
      agreement_title: data.agreement_title || data.agreementTitle || "New Agreement",
      agreement_type: data.agreement_type || "MOU",
      effective_start_date: data.effective_start_date || new Date().toISOString().split("T")[0],
      effective_end_date: data.effective_end_date || new Date(Date.now() + 365 * 86400000 * 3).toISOString().split("T")[0],
      renewal_warning_days: 90,
      status: "ACTIVE",
      ...data,
    } as InstitutionalAgreement;

    return fetchWithFallback<InstitutionalAgreement>(
      "/agreements",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async addAmendment(agreementId: string, data: Partial<AgreementAmendment>): Promise<AgreementAmendment> {
    const created: AgreementAmendment = {
      id: `amd-${Date.now().toString(36)}`,
      agreement_id: agreementId,
      title: data.title || "Scope Extension Amendment",
      description: data.description || "Updated terms",
      effective_date: new Date().toISOString().split("T")[0],
      ...data,
    };

    return fetchWithFallback<AgreementAmendment>(
      `/agreements/${agreementId}/amendments`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async getAmendments(agreementId: string): Promise<AgreementAmendment[]> {
    return fetchWithFallback<AgreementAmendment[]>(`/agreements/${agreementId}/amendments`, {}, []);
  },

  // --------------------------------------------------------------------------
  // Mobility Programs
  // --------------------------------------------------------------------------
  async getPrograms(params?: {
    partner_id?: string;
    open_only?: boolean;
    academic_year?: string;
  }): Promise<MobilityProgram[]> {
    const query = new URLSearchParams();
    if (params?.partner_id) query.set("partner_id", params.partner_id);
    if (params?.open_only) query.set("open_only", "true");
    if (params?.academic_year) query.set("academic_year", params.academic_year);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<MobilityProgram[]>("/programs" + qs, {}, MOCK_PROGRAMS);
  },

  async getProgram(id: string): Promise<MobilityProgram> {
    const fallback = MOCK_PROGRAMS.find((p) => p.id === id) || MOCK_PROGRAMS[0];
    return fetchWithFallback<MobilityProgram>(`/programs/${id}`, {}, fallback);
  },

  async createProgram(data: Partial<MobilityProgram>): Promise<MobilityProgram> {
    const created: MobilityProgram = {
      id: `prg-${Date.now().toString(36)}`,
      partner_id: data.partner_id || data.partnerId || "",
      program_title: data.program_title || data.programTitle || "Semester Exchange Program",
      program_code: data.program_code || data.programCode || `EXC-${Date.now().toString(36).toUpperCase()}`,
      program_type: data.program_type || "SEMESTER_EXCHANGE",
      term_type: data.term_type || "FALL_SEMESTER",
      academic_year: data.academic_year || "2026-2027",
      total_seats: data.total_seats || 5,
      application_start_date: data.application_start_date || new Date().toISOString().split("T")[0],
      application_deadline: data.application_deadline || new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0],
      expected_start_date: data.expected_start_date || new Date(Date.now() + 180 * 86400000).toISOString().split("T")[0],
      expected_end_date: data.expected_end_date || new Date(Date.now() + 360 * 86400000).toISOString().split("T")[0],
      is_published: data.is_published ?? true,
      ...data,
    } as MobilityProgram;

    return fetchWithFallback<MobilityProgram>(
      "/programs",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  // --------------------------------------------------------------------------
  // Applications & Multi-Stage Reviews
  // --------------------------------------------------------------------------
  async getApplications(params?: {
    student_id?: string;
    program_id?: string;
    status?: string;
    department_pending?: boolean;
    intl_office_pending?: boolean;
  }): Promise<MobilityApplication[]> {
    const query = new URLSearchParams();
    if (params?.student_id) query.set("student_id", params.student_id);
    if (params?.program_id) query.set("program_id", params.program_id);
    if (params?.status) query.set("status", params.status);
    if (params?.department_pending) query.set("department_pending", "true");
    if (params?.intl_office_pending) query.set("intl_office_pending", "true");

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<MobilityApplication[]>("/applications" + qs, {}, MOCK_APPLICATIONS);
  },

  async getApplication(id: string): Promise<MobilityApplication> {
    const fallback = MOCK_APPLICATIONS.find((a) => a.id === id) || MOCK_APPLICATIONS[0];
    return fetchWithFallback<MobilityApplication>(`/applications/${id}`, {}, fallback);
  },

  async createApplication(data: Partial<MobilityApplication>): Promise<MobilityApplication> {
    const created: MobilityApplication = {
      id: `app-${Date.now().toString(36)}`,
      application_reference_number: `MOB-${Date.now().toString(36).toUpperCase()}`,
      program_id: data.program_id || data.programId || "",
      student_id: data.student_id || data.studentId || "curr-student",
      status: "DEPARTMENT_REVIEW",
      statement_of_purpose: data.statement_of_purpose || data.statementOfPurpose || "",
      proposed_courses: data.proposed_courses || [],
      eligibility_check_passed: true,
      created_at: new Date().toISOString(),
      ...data,
    } as MobilityApplication;

    return fetchWithFallback<MobilityApplication>(
      "/applications",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async reviewApplication(
    id: string,
    action: "APPROVE" | "REJECT" | "RETURN" | "ESCALATE",
    comments: string,
    reasons?: string
  ): Promise<MobilityApplication> {
    const fallback = MOCK_APPLICATIONS.find((a) => a.id === id) || MOCK_APPLICATIONS[0];
    const updatedStatus = action === "APPROVE" ? "APPROVED" : action === "REJECT" ? "REJECTED" : fallback.status;

    return fetchWithFallback<MobilityApplication>(
      `/applications/${id}/review`,
      {
        method: "POST",
        body: JSON.stringify({ action, comments, conditions_or_reasons: reasons }),
      },
      { ...fallback, status: updatedStatus }
    );
  },

  async nominateStudent(id: string, notes?: string, partnerEmail?: string): Promise<MobilityApplication> {
    const fallback = MOCK_APPLICATIONS.find((a) => a.id === id) || MOCK_APPLICATIONS[0];
    return fetchWithFallback<MobilityApplication>(
      `/applications/${id}/nominate`,
      {
        method: "POST",
        body: JSON.stringify({ nomination_notes: notes, partner_contact_email: partnerEmail }),
      },
      { ...fallback, status: "PARTNER_NOMINATED", nominated_at: new Date().toISOString() }
    );
  },

  async recordPartnerDecision(id: string, decision: "ACCEPTED" | "REJECTED", notes?: string): Promise<MobilityApplication> {
    const fallback = MOCK_APPLICATIONS.find((a) => a.id === id) || MOCK_APPLICATIONS[0];
    const newStatus = decision === "ACCEPTED" ? "PARTNER_ACCEPTED" : "PARTNER_REJECTED";

    return fetchWithFallback<MobilityApplication>(
      `/applications/${id}/partner-decision`,
      {
        method: "POST",
        body: JSON.stringify({ decision, official_response_notes: notes }),
      },
      { ...fallback, status: newStatus, partner_decision: decision, partner_decision_notes: notes }
    );
  },

  async updatePreDeparture(
    id: string,
    checklist: Record<string, any>,
    visaRef?: string,
    insurancePolicy?: string
  ): Promise<MobilityApplication> {
    const fallback = MOCK_APPLICATIONS.find((a) => a.id === id) || MOCK_APPLICATIONS[0];
    return fetchWithFallback<MobilityApplication>(
      `/applications/${id}/pre-departure`,
      {
        method: "PUT",
        body: JSON.stringify({
          pre_departure_checklist: checklist,
          visa_reference_number: visaRef,
          insurance_policy_number: insurancePolicy,
        }),
      },
      { ...fallback, pre_departure_checklist: checklist, status: "ACTIVE_MOBILITY" }
    );
  },

  // --------------------------------------------------------------------------
  // Inbound Students
  // --------------------------------------------------------------------------
  async getInboundStudents(params?: {
    partner_id?: string;
    status?: string;
    orientation_pending?: boolean;
  }): Promise<InboundStudentProfile[]> {
    const query = new URLSearchParams();
    if (params?.partner_id) query.set("partner_id", params.partner_id);
    if (params?.status) query.set("status", params.status);
    if (params?.orientation_pending) query.set("orientation_pending", "true");

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<InboundStudentProfile[]>("/inbound" + qs, {}, MOCK_INBOUND_STUDENTS);
  },

  async createInboundStudent(data: Partial<InboundStudentProfile>): Promise<InboundStudentProfile> {
    const created: InboundStudentProfile = {
      id: `inb-${Date.now().toString(36)}`,
      partner_id: data.partner_id || data.partnerId || "",
      first_name: data.first_name || data.firstName || "Inbound",
      last_name: data.last_name || data.lastName || "Scholar",
      email: data.email || "exchange@partner.edu",
      home_institution_student_id: data.home_institution_student_id || data.homeInstitutionStudentId || "P-001",
      host_department_id: data.host_department_id || data.hostDepartmentId || "dept-cse",
      study_period_start: data.study_period_start || new Date().toISOString().split("T")[0],
      study_period_end: data.study_period_end || new Date(Date.now() + 120 * 86400000).toISOString().split("T")[0],
      check_in_status: "NOMINATED",
      orientation_completed: false,
      ...data,
    } as InboundStudentProfile;

    return fetchWithFallback<InboundStudentProfile>(
      "/inbound",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async checkinInboundStudent(id: string, notes?: string): Promise<InboundStudentProfile> {
    const fallback = MOCK_INBOUND_STUDENTS.find((s) => s.id === id) || MOCK_INBOUND_STUDENTS[0];
    return fetchWithFallback<InboundStudentProfile>(
      `/inbound/${id}/checkin`,
      {
        method: "POST",
        body: JSON.stringify({ orientation_checklist_completed: true, notes }),
      },
      { ...fallback, check_in_status: "ORIENTATION_COMPLETED", orientation_completed: true }
    );
  },

  // --------------------------------------------------------------------------
  // Faculty Mobility
  // --------------------------------------------------------------------------
  async getFacultyMobilities(params?: {
    direction?: string;
    partner_id?: string;
    status?: string;
  }): Promise<FacultyMobilityRecord[]> {
    const query = new URLSearchParams();
    if (params?.direction) query.set("direction", params.direction);
    if (params?.partner_id) query.set("partner_id", params.partner_id);
    if (params?.status) query.set("status", params.status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<FacultyMobilityRecord[]>("/faculty-mobility" + qs, {}, MOCK_FACULTY_MOBILITIES);
  },

  async createFacultyMobility(data: Partial<FacultyMobilityRecord>): Promise<FacultyMobilityRecord> {
    const created: FacultyMobilityRecord = {
      id: `fac-${Date.now().toString(36)}`,
      partner_id: data.partner_id || data.partnerId || "",
      staff_user_id: data.staff_user_id || data.staffUserId || "usr-current",
      mobility_type: data.mobility_type || "OUTBOUND",
      visit_start_date: data.visit_start_date || new Date().toISOString().split("T")[0],
      visit_end_date: data.visit_end_date || new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
      purpose_summary: data.purpose_summary || "Academic visiting fellowship and guest lecture series",
      status: "SUBMITTED",
      ...data,
    } as FacultyMobilityRecord;

    return fetchWithFallback<FacultyMobilityRecord>(
      "/faculty-mobility",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async approveFacultyMobility(
    id: string,
    level: "HOD" | "VP",
    status: "APPROVED" | "REJECTED",
    comments?: string
  ): Promise<FacultyMobilityRecord> {
    const fallback = MOCK_FACULTY_MOBILITIES.find((f) => f.id === id) || MOCK_FACULTY_MOBILITIES[0];
    return fetchWithFallback<FacultyMobilityRecord>(
      `/faculty-mobility/${id}/approval`,
      {
        method: "POST",
        body: JSON.stringify({ approval_level: level, status, comments }),
      },
      { ...fallback, status: status === "APPROVED" ? "APPROVED" : "REJECTED" }
    );
  },

  // --------------------------------------------------------------------------
  // Course Equivalencies & Credit Transfers
  // --------------------------------------------------------------------------
  async getCourseEquivalencies(params?: {
    partner_id?: string;
    department_id?: string;
    status?: string;
  }): Promise<CourseEquivalencyMapping[]> {
    const query = new URLSearchParams();
    if (params?.partner_id) query.set("partner_id", params.partner_id);
    if (params?.department_id) query.set("department_id", params.department_id);
    if (params?.status) query.set("status", params.status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<CourseEquivalencyMapping[]>("/course-equivalencies" + qs, {}, MOCK_EQUIVALENCIES);
  },

  async createCourseEquivalency(data: Partial<CourseEquivalencyMapping>): Promise<CourseEquivalencyMapping> {
    const created: CourseEquivalencyMapping = {
      id: `eq-${Date.now().toString(36)}`,
      partner_id: data.partner_id || data.partnerId || "",
      host_course_code: data.host_course_code || data.hostCourseCode || "EXT-101",
      host_course_title: data.host_course_title || data.hostCourseTitle || "External Course",
      host_credits: data.host_credits || data.hostCredits || 4,
      target_course_code: data.target_course_code || data.targetCourseCode || "CS301",
      target_course_title: data.target_course_title || data.targetCourseTitle || "Equivalent Internal Course",
      target_credits: data.target_credits || data.targetCredits || 4,
      department_id: data.department_id || data.departmentId || "dept-cse",
      status: "PROPOSED",
      ...data,
    } as CourseEquivalencyMapping;

    return fetchWithFallback<CourseEquivalencyMapping>(
      "/course-equivalencies",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async evaluateCourseEquivalency(
    id: string,
    decision: "APPROVED" | "REJECTED",
    notes: string
  ): Promise<CourseEquivalencyMapping> {
    const fallback = MOCK_EQUIVALENCIES.find((e) => e.id === id) || MOCK_EQUIVALENCIES[0];
    return fetchWithFallback<CourseEquivalencyMapping>(
      `/course-equivalencies/${id}/evaluate`,
      {
        method: "POST",
        body: JSON.stringify({ decision, evaluation_notes: notes }),
      },
      { ...fallback, status: decision === "APPROVED" ? "ACTIVE" : "DEPRECATED", evaluation_notes: notes }
    );
  },

  async getCreditTransfers(params?: {
    student_id?: string;
    application_id?: string;
    status?: string;
  }): Promise<CreditTransferRequest[]> {
    const query = new URLSearchParams();
    if (params?.student_id) query.set("student_id", params.student_id);
    if (params?.application_id) query.set("application_id", params.application_id);
    if (params?.status) query.set("status", params.status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<CreditTransferRequest[]>("/credit-transfers" + qs, {}, MOCK_CREDIT_TRANSFERS);
  },

  async createCreditTransfer(data: Partial<CreditTransferRequest>): Promise<CreditTransferRequest> {
    const created: CreditTransferRequest = {
      id: `ct-${Date.now().toString(36)}`,
      application_id: data.application_id || data.applicationId || "",
      student_id: data.student_id || data.studentId || "curr-student",
      host_institution_name: data.host_institution_name || "Partner University",
      host_credits_earned: data.host_credits_earned || 12,
      target_campus_credits: data.target_campus_credits || 12,
      status: "SUBMITTED",
      ...data,
    } as CreditTransferRequest;

    return fetchWithFallback<CreditTransferRequest>(
      "/credit-transfers",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async approveCreditTransfer(
    id: string,
    decision: "APPROVED" | "REJECTED",
    notes: string,
    councilRef?: string
  ): Promise<CreditTransferRequest> {
    const fallback = MOCK_CREDIT_TRANSFERS.find((c) => c.id === id) || MOCK_CREDIT_TRANSFERS[0];
    return fetchWithFallback<CreditTransferRequest>(
      `/credit-transfers/${id}/committee-approval`,
      {
        method: "POST",
        body: JSON.stringify({
          decision,
          committee_notes: notes,
          academic_council_approval_reference: councilRef,
        }),
      },
      {
        ...fallback,
        status: decision === "APPROVED" ? "APPROVED" : "REJECTED",
        committee_review_notes: notes,
        academic_council_approval_ref: councilRef,
      }
    );
  },

  // --------------------------------------------------------------------------
  // Documents & Checklists
  // --------------------------------------------------------------------------
  async getDocuments(params?: {
    application_id?: string;
    inbound_student_id?: string;
    faculty_mobility_id?: string;
    verification_status?: string;
  }): Promise<MobilityDocument[]> {
    const query = new URLSearchParams();
    if (params?.application_id) query.set("application_id", params.application_id);
    if (params?.inbound_student_id) query.set("inbound_student_id", params.inbound_student_id);
    if (params?.faculty_mobility_id) query.set("faculty_mobility_id", params.faculty_mobility_id);
    if (params?.verification_status) query.set("verification_status", params.verification_status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<MobilityDocument[]>("/documents" + qs, {}, MOCK_DOCUMENTS);
  },

  async uploadDocument(data: Partial<MobilityDocument>): Promise<MobilityDocument> {
    const created: MobilityDocument = {
      id: `doc-${Date.now().toString(36)}`,
      document_type: data.document_type || "PASSPORT_BIO",
      document_name: data.document_name || "document.pdf",
      file_storage_url: data.file_storage_url || "https://campus-storage.edu/docs/sample.pdf",
      verification_status: "PENDING",
      created_at: new Date().toISOString(),
      ...data,
    } as MobilityDocument;

    return fetchWithFallback<MobilityDocument>(
      "/documents",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async verifyDocument(id: string, status: "VERIFIED" | "REJECTED", reason?: string): Promise<MobilityDocument> {
    const fallback = MOCK_DOCUMENTS.find((d) => d.id === id) || MOCK_DOCUMENTS[0];
    return fetchWithFallback<MobilityDocument>(
      `/documents/${id}/verify`,
      {
        method: "POST",
        body: JSON.stringify({ status, rejection_reason: reason }),
      },
      { ...fallback, verification_status: status, rejection_reason: reason }
    );
  },

  // --------------------------------------------------------------------------
  // Scholarships & Grants
  // --------------------------------------------------------------------------
  async getScholarships(params?: { is_active?: boolean }): Promise<MobilityScholarship[]> {
    const qs = params?.is_active !== undefined ? `?is_active=${params.is_active}` : "";
    return fetchWithFallback<MobilityScholarship[]>("/scholarships" + qs, {}, MOCK_SCHOLARSHIPS);
  },

  async createScholarship(data: Partial<MobilityScholarship>): Promise<MobilityScholarship> {
    const created: MobilityScholarship = {
      id: `sch-${Date.now().toString(36)}`,
      scholarship_code: data.scholarship_code || `SCH-${Date.now().toString(36).toUpperCase()}`,
      scholarship_name: data.scholarship_name || "Mobility Scholarship",
      funding_source: data.funding_source || "Institutional Trust",
      award_amount_per_student: data.award_amount_per_student || 2000,
      total_available_slots: data.total_available_slots || 5,
      application_deadline: data.application_deadline || new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0],
      is_active: true,
      ...data,
    } as MobilityScholarship;

    return fetchWithFallback<MobilityScholarship>(
      "/scholarships",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async getFundingRequests(params?: {
    application_id?: string;
    status?: string;
  }): Promise<MobilityFundingRequest[]> {
    const query = new URLSearchParams();
    if (params?.application_id) query.set("application_id", params.application_id);
    if (params?.status) query.set("status", params.status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchWithFallback<MobilityFundingRequest[]>("/funding-requests" + qs, {}, MOCK_FUNDING_REQUESTS);
  },

  async createFundingRequest(data: Partial<MobilityFundingRequest>): Promise<MobilityFundingRequest> {
    const created: MobilityFundingRequest = {
      id: `fnd-${Date.now().toString(36)}`,
      application_id: data.application_id || data.applicationId || "",
      student_id: data.student_id || data.studentId || "curr-student",
      requested_amount: data.requested_amount || 1500,
      currency: "USD",
      status: "REQUESTED",
      justification: data.justification || "Travel grant assistance",
      ...data,
    } as MobilityFundingRequest;

    return fetchWithFallback<MobilityFundingRequest>(
      "/funding-requests",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      created
    );
  },

  async approveFundingRequest(
    id: string,
    status: "APPROVED" | "REJECTED",
    amount?: number,
    refId?: string
  ): Promise<MobilityFundingRequest> {
    const fallback = MOCK_FUNDING_REQUESTS.find((f) => f.id === id) || MOCK_FUNDING_REQUESTS[0];
    return fetchWithFallback<MobilityFundingRequest>(
      `/funding-requests/${id}/approval`,
      {
        method: "POST",
        body: JSON.stringify({ status, approved_amount: amount, finance_reference_id: refId }),
      },
      { ...fallback, status, approved_amount: amount || fallback.requested_amount, finance_disbursement_ref: refId }
    );
  },
};
