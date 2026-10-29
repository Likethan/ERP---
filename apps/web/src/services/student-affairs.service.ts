/**
 * CampusOS Student Affairs & Disciplinary Client Service
 * "One Campus. One System. One Source of Truth."
 */

import {
  GrievanceCaseModel,
  DisciplinaryProceedingModel,
  CaseEvidenceModel,
  CaseMeetingModel,
  CaseCommunicationModel,
  ResolutionActionModel,
  AppealRecordModel,
  CaseEscalationModel,
  GrievanceCategoryModel,
  StudentAffairsOfficeModel,
  StudentAffairsPolicyConfigModel,
  StudentAffairsDashboardMetrics,
  GrievanceSubmissionForm,
  CaseFilterParams,
  CaseAssignmentForm,
  ConflictDeclarationForm,
  DisciplinaryProceedingForm,
  DisciplinaryFindingsForm,
  DisciplinarySanctionForm,
  EvidenceUploadForm,
  EvidenceRedactionForm,
  CaseMeetingForm,
  ResolutionActionForm,
  AppealFilingForm,
  AppealReviewForm,
  UrgentEscalationForm,
  ConfidentialMessageForm,
  SACaseStatus,
  SACasePriority,
  SAConfidentialityLevel,
  SASubmitterType,
  SAParticipantRole,
  SAFindingStatus,
  SADisciplinaryStage,
  SAMeetingStatus,
  SAActionStatus,
  SAAppealStatus,
  SAEscalationStatus,
} from "../types/student-affairs";
import {
  MOCK_CASES,
  MOCK_CATEGORIES,
  MOCK_SA_OFFICES,
  MOCK_POLICIES,
  MOCK_METRICS,
} from "../mocks/student-affairs.mock";

class StudentAffairsService {
  private cases: GrievanceCaseModel[] = [...MOCK_CASES];
  private categories: GrievanceCategoryModel[] = [...MOCK_CATEGORIES];
  private offices: StudentAffairsOfficeModel[] = [...MOCK_SA_OFFICES];
  private policies: StudentAffairsPolicyConfigModel[] = [...MOCK_POLICIES];

  async getDashboardMetrics(): Promise<StudentAffairsDashboardMetrics> {
    try {
      const res = await fetch("/api/v1/student-affairs/reports/dashboard");
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback to local calculation
    }
    return {
      ...MOCK_METRICS,
      total_cases: this.cases.length,
      active_grievances: this.cases.filter((c) => c.case_type === "GRIEVANCE" && c.status !== "RESOLVED" && c.status !== "CLOSED").length,
      active_disciplinary: this.cases.filter((c) => c.case_type === "DISCIPLINARY" && c.status !== "RESOLVED" && c.status !== "CLOSED").length,
    };
  }

  async getCases(filters?: CaseFilterParams): Promise<GrievanceCaseModel[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.caseType) params.append("case_type", filters.caseType);
      if (filters?.status) params.append("status", filters.status);
      if (filters?.priority) params.append("priority", filters.priority);
      if (filters?.confidentialityLevel) params.append("confidentiality_level", filters.confidentialityLevel);
      if (filters?.assignedOfficerId) params.append("assigned_officer_id", filters.assignedOfficerId);

      const res = await fetch(`/api/v1/student-affairs/cases?${params.toString()}`);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback to in-memory state
    }

    let results = [...this.cases];
    if (filters?.caseType) {
      results = results.filter((c) => c.case_type === filters.caseType);
    }
    if (filters?.status) {
      results = results.filter((c) => c.status === filters.status);
    }
    if (filters?.priority) {
      results = results.filter((c) => c.priority === filters.priority);
    }
    if (filters?.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      results = results.filter(
        (c) =>
          c.case_number.toLowerCase().includes(q) ||
          c.title.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q)
      );
    }
    if (filters?.isEscalated !== undefined) {
      results = results.filter((c) => c.is_escalated === filters.isEscalated);
    }
    return results;
  }

  async getCaseById(id: string): Promise<GrievanceCaseModel | null> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${id}`);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback
    }
    return this.cases.find((c) => c.id === id) || null;
  }

  async submitCase(data: GrievanceSubmissionForm): Promise<GrievanceCaseModel> {
    try {
      const res = await fetch("/api/v1/student-affairs/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category_id: data.categoryId,
          title: data.title,
          description: data.description,
          requested_resolution: data.requestedResolution,
          campus_id: data.campusId,
          is_anonymous: data.isAnonymous,
          submitter_type: data.submitterType,
          confidentiality_level: data.confidentialityLevel,
          supporting_documents: data.supportingDocuments || [],
        }),
      });
      if (res.ok) {
        const created = await res.json();
        this.cases.unshift(created);
        return created;
      }
    } catch {
      // Mock fallback
    }

    const seq = String(this.cases.length + 43).padStart(4, "0");
    const category = this.categories.find((cat) => cat.id === data.categoryId);
    const newCase: GrievanceCaseModel = {
      id: `case-${Date.now()}`,
      tenant_id: "ten-001",
      case_number: `GRV-2026-${seq}`,
      case_type: category?.case_type || "GRIEVANCE",
      category_id: data.categoryId,
      category: category || null,
      title: data.title,
      description: data.description,
      requested_resolution: data.requestedResolution,
      status: SACaseStatus.SUBMITTED,
      priority: category?.default_priority || SACasePriority.MEDIUM,
      confidentiality_level: data.confidentialityLevel || SAConfidentialityLevel.STANDARD,
      is_anonymous: data.isAnonymous,
      submitter_type: data.submitterType || SASubmitterType.STUDENT,
      submitter_user_id: data.isAnonymous ? null : "usr-current-user",
      submitter_name_redacted: data.isAnonymous ? "Anonymous Submitter (Identity Protected)" : "Student Submitter",
      campus_id: data.campusId,
      target_response_date: new Date(Date.now() + 48 * 3600 * 1000).toISOString(),
      target_resolution_date: new Date(Date.now() + 10 * 86400 * 1000).toISOString(),
      is_escalated: false,
      reopen_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      participants: [
        {
          id: `part-${Date.now()}`,
          tenant_id: "ten-001",
          case_id: `case-${Date.now()}`,
          role: SAParticipantRole.SUBMITTER,
          display_name: data.isAnonymous ? "Anonymous Submitter" : "Submitter",
          has_conflict_of_interest: false,
          assigned_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
      ],
      evidence_items: (data.supportingDocuments || []).map((doc, idx) => ({
        id: `ev-${Date.now()}-${idx}`,
        tenant_id: "ten-001",
        case_id: `case-${Date.now()}`,
        evidence_type: "DOCUMENT",
        title: doc.title,
        file_url: doc.fileUrl,
        file_size_bytes: doc.fileSizeBytes,
        uploaded_by_id: "usr-current-user",
        confidentiality_level: "PARTICIPANTS_ONLY",
        is_redacted: false,
        is_under_legal_hold: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })),
      meetings: [],
      communications: [],
      resolution_actions: [],
      appeals: [],
    };
    this.cases.unshift(newCase);
    return newCase;
  }

  async assignCase(data: CaseAssignmentForm): Promise<GrievanceCaseModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/assignments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          officer_id: data.officerId,
          reassignment_reason: data.reassignmentReason,
          priority: data.priority,
          target_response_hours: data.targetResponseHours,
        }),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback
    }

    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      c.assigned_officer_id = data.officerId;
      if (data.priority) c.priority = data.priority;
      if (c.status === SACaseStatus.SUBMITTED) {
        c.status = SACaseStatus.ACKNOWLEDGED;
      }
      c.updated_at = new Date().toISOString();
      return c;
    }
    throw new Error("Case not found");
  }

  async declareConflict(data: ConflictDeclarationForm): Promise<void> {
    try {
      await fetch(`/api/v1/student-affairs/cases/${data.caseId}/conflict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: data.reason,
          requested_reassignment_to_officer_id: data.requestedReassignmentToOfficerId,
        }),
      });
    } catch {
      // Mock update
    }

    const c = this.cases.find((item) => item.id === data.caseId);
    if (c && data.requestedReassignmentToOfficerId) {
      c.assigned_officer_id = data.requestedReassignmentToOfficerId;
      c.updated_at = new Date().toISOString();
    }
  }

  async createDisciplinaryProceeding(
    data: DisciplinaryProceedingForm
  ): Promise<DisciplinaryProceedingModel> {
    try {
      const res = await fetch(
        `/api/v1/student-affairs/cases/${data.caseId}/disciplinary-proceeding`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            respondent_student_id: data.respondentStudentId,
            allegation_summary: data.allegationSummary,
            policy_provisions_violated: data.policyProvisionsViolated,
            investigator_id: data.investigatorId,
          }),
        }
      );
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const proc: DisciplinaryProceedingModel = {
      id: `dp-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      respondent_student_id: data.respondentStudentId,
      allegation_summary: data.allegationSummary,
      policy_provisions_violated: data.policyProvisionsViolated,
      investigator_id: data.investigatorId,
      procedural_stage: SADisciplinaryStage.INTAKE_ASSESSMENT,
      finding_status: SAFindingStatus.PENDING,
      is_communicated: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      c.disciplinary_proceeding = proc;
      c.status = SACaseStatus.INVESTIGATION;
    }
    return proc;
  }

  async recordFindings(
    caseId: string,
    data: DisciplinaryFindingsForm
  ): Promise<DisciplinaryProceedingModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${caseId}/findings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          findings_summary: data.findingsSummary,
          finding_status: data.findingStatus,
          procedural_stage: data.proceduralStage,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const c = this.cases.find((item) => item.id === caseId);
    if (c?.disciplinary_proceeding) {
      c.disciplinary_proceeding.findings_summary = data.findingsSummary;
      c.disciplinary_proceeding.finding_status = data.findingStatus;
      c.disciplinary_proceeding.procedural_stage = data.proceduralStage;
      c.disciplinary_proceeding.updated_at = new Date().toISOString();
      return c.disciplinary_proceeding;
    }
    throw new Error("Disciplinary proceeding not found");
  }

  async approveSanction(
    caseId: string,
    data: DisciplinarySanctionForm
  ): Promise<DisciplinaryProceedingModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${caseId}/sanctions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sanction_type: data.sanctionType,
          sanction_details: data.sanctionDetails,
          decision_maker_id: data.decisionMakerId,
          appeal_deadline_days: data.appealDeadlineDays,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const c = this.cases.find((item) => item.id === caseId);
    if (c?.disciplinary_proceeding) {
      c.disciplinary_proceeding.sanction_type = data.sanctionType;
      c.disciplinary_proceeding.sanction_details = data.sanctionDetails;
      c.disciplinary_proceeding.decision_maker_id = data.decisionMakerId;
      c.disciplinary_proceeding.decision_date = new Date().toISOString();
      c.disciplinary_proceeding.appeal_deadline = new Date(
        Date.now() + data.appealDeadlineDays * 86400 * 1000
      ).toISOString();
      c.disciplinary_proceeding.procedural_stage = SADisciplinaryStage.SANCTION_APPROVED;
      c.disciplinary_proceeding.is_communicated = true;
      c.status = SACaseStatus.RESOLVED;
      c.resolution_summary = `Approved Sanction: ${data.sanctionType}. ${data.sanctionDetails}`;
      c.resolution_date = new Date().toISOString();
      return c.disciplinary_proceeding;
    }
    throw new Error("Proceeding not found");
  }

  async uploadEvidence(data: EvidenceUploadForm): Promise<CaseEvidenceModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/evidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          evidence_type: data.evidenceType,
          title: data.title,
          description: data.description,
          file_url: data.fileUrl,
          file_size_bytes: data.fileSizeBytes,
          confidentiality_level: data.confidentialityLevel,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const ev: CaseEvidenceModel = {
      id: `ev-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      evidence_type: data.evidenceType,
      title: data.title,
      description: data.description,
      file_url: data.fileUrl,
      file_size_bytes: data.fileSizeBytes,
      uploaded_by_id: "usr-current-user",
      confidentiality_level: data.confidentialityLevel,
      is_redacted: false,
      is_under_legal_hold: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      if (!c.evidence_items) c.evidence_items = [];
      c.evidence_items.push(ev);
    }
    return ev;
  }

  async redactEvidence(data: EvidenceRedactionForm): Promise<CaseEvidenceModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/evidence/${data.evidenceId}/redact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          redaction_summary: data.redactionSummary,
          redacted_file_url: data.redactedFileUrl,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    // Locate original evidence
    for (const c of this.cases) {
      const orig = c.evidence_items?.find((e) => e.id === data.evidenceId);
      if (orig) {
        const redacted: CaseEvidenceModel = {
          id: `ev-redacted-${Date.now()}`,
          tenant_id: "ten-001",
          case_id: orig.case_id,
          evidence_type: orig.evidence_type,
          title: `[REDACTED] ${orig.title}`,
          description: `Authorized Redaction: ${data.redactionSummary}`,
          file_url: data.redactedFileUrl,
          file_size_bytes: orig.file_size_bytes,
          uploaded_by_id: "usr-current-user",
          confidentiality_level: orig.confidentiality_level,
          is_redacted: true,
          redaction_summary: data.redactionSummary,
          original_evidence_id: orig.id,
          is_under_legal_hold: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        c.evidence_items?.push(redacted);
        return redacted;
      }
    }
    throw new Error("Original evidence not found");
  }

  async scheduleMeeting(data: CaseMeetingForm): Promise<CaseMeetingModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/meetings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: data.title,
          meeting_type: data.meetingType,
          scheduled_start: data.scheduledStart,
          scheduled_end: data.scheduledEnd,
          venue_or_url: data.venueOrUrl,
          facilitator_id: data.facilitatorId,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const meeting: CaseMeetingModel = {
      id: `meet-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      title: data.title,
      meeting_type: data.meetingType,
      scheduled_start: data.scheduledStart,
      scheduled_end: data.scheduledEnd,
      venue_or_url: data.venueOrUrl,
      facilitator_id: data.facilitatorId,
      status: SAMeetingStatus.SCHEDULED,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      if (!c.meetings) c.meetings = [];
      c.meetings.push(meeting);
      if (data.meetingType === "HEARING_PANEL") {
        c.status = SACaseStatus.HEARING;
      }
    }
    return meeting;
  }

  async addResolutionAction(data: ResolutionActionForm): Promise<ResolutionActionModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: data.description,
          action_type: data.actionType,
          assigned_owner_id: data.assignedOwnerId,
          due_date: data.dueDate,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const action: ResolutionActionModel = {
      id: `act-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      description: data.description,
      action_type: data.actionType,
      assigned_owner_id: data.assignedOwnerId,
      due_date: data.dueDate,
      status: SAActionStatus.PENDING,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      if (!c.resolution_actions) c.resolution_actions = [];
      c.resolution_actions.push(action);
    }
    return action;
  }

  async fileAppeal(data: AppealFilingForm): Promise<AppealRecordModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/appeals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appeal_grounds: data.appealGrounds,
          grounds_statement: data.groundsStatement,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const appeal: AppealRecordModel = {
      id: `app-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      appellant_id: "usr-current-user",
      appeal_date: new Date().toISOString(),
      appeal_grounds: data.appealGrounds,
      grounds_statement: data.groundsStatement,
      review_status: SAAppealStatus.FILED,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      if (!c.appeals) c.appeals = [];
      c.appeals.push(appeal);
      c.status = SACaseStatus.UNDER_REVIEW;
      if (c.disciplinary_proceeding) {
        c.disciplinary_proceeding.procedural_stage = SADisciplinaryStage.APPEAL_PENDING;
      }
    }
    return appeal;
  }

  async reviewAppeal(data: AppealReviewForm): Promise<AppealRecordModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/appeals/${data.appealId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assigned_reviewer_id: data.assignedReviewerId,
          review_status: data.reviewStatus,
          outcome_summary: data.outcomeSummary,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    for (const c of this.cases) {
      const appeal = c.appeals?.find((a) => a.id === data.appealId);
      if (appeal) {
        // Enforce separation of duties
        if (c.disciplinary_proceeding?.decision_maker_id === data.assignedReviewerId) {
          throw new Error("Separation of Duties Violation: Original decision maker cannot review appeal.");
        }
        appeal.assigned_reviewer_id = data.assignedReviewerId;
        appeal.review_status = data.reviewStatus;
        appeal.outcome_summary = data.outcomeSummary;
        appeal.outcome_date = new Date().toISOString();
        appeal.updated_at = new Date().toISOString();
        c.status = SACaseStatus.RESOLVED;
        c.resolution_summary = `Appellate Review: ${data.reviewStatus}. ${data.outcomeSummary}`;
        if (c.disciplinary_proceeding) {
          c.disciplinary_proceeding.procedural_stage = SADisciplinaryStage.CONCLUDED;
        }
        return appeal;
      }
    }
    throw new Error("Appeal record not found");
  }

  async triggerEscalation(data: UrgentEscalationForm): Promise<CaseEscalationModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/escalations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          escalation_level: data.escalationLevel,
          trigger_reason: data.triggerReason,
          safeguarding_lead_id: data.safeguardingLeadId,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const esc: CaseEscalationModel = {
      id: `esc-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      escalation_level: data.escalationLevel,
      status: SAEscalationStatus.ACTIVE,
      trigger_reason: data.triggerReason,
      escalated_by_id: "usr-current-user",
      safeguarding_lead_id: data.safeguardingLeadId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      c.is_escalated = true;
      c.escalation_reason = data.triggerReason;
      c.priority = SACasePriority.CRITICAL_URGENT;
    }
    return esc;
  }

  async sendConfidentialMessage(
    data: ConfidentialMessageForm
  ): Promise<CaseCommunicationModel> {
    try {
      const res = await fetch(`/api/v1/student-affairs/cases/${data.caseId}/communications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_body: data.messageBody,
          is_internal_only: data.isInternalOnly,
          attachment_url: data.attachmentUrl,
        }),
      });
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }

    const msg: CaseCommunicationModel = {
      id: `msg-${Date.now()}`,
      tenant_id: "ten-001",
      case_id: data.caseId,
      sender_user_id: "usr-current-user",
      sender_role: "CASE_OFFICER",
      message_body: data.messageBody,
      is_internal_only: data.isInternalOnly,
      attachment_url: data.attachmentUrl,
      is_acknowledged: false,
      created_at: new Date().toISOString(),
    };
    const c = this.cases.find((item) => item.id === data.caseId);
    if (c) {
      if (!c.communications) c.communications = [];
      c.communications.push(msg);
    }
    return msg;
  }

  async getCategories(): Promise<GrievanceCategoryModel[]> {
    try {
      const res = await fetch("/api/v1/student-affairs/case-categories");
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }
    return this.categories;
  }

  async getOffices(): Promise<StudentAffairsOfficeModel[]> {
    try {
      const res = await fetch("/api/v1/student-affairs/offices");
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }
    return this.offices;
  }

  async getPolicies(): Promise<StudentAffairsPolicyConfigModel[]> {
    try {
      const res = await fetch("/api/v1/student-affairs/policies");
      if (res.ok) return await res.json();
    } catch {
      // Mock
    }
    return this.policies;
  }
}

export const studentAffairsService = new StudentAffairsService();
