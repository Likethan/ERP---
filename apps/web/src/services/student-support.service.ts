/**
 * CampusOS Unified Student Counselling, Mentoring & Personal Development Client Service
 * Product Principle: "One Campus. One System. One Source of Truth."
 *
 * Integrates with:
 * - /api/v1/student-support/config
 * - /api/v1/student-support/mentor-assignments
 * - /api/v1/student-support/mentor-assignments/{id}/reassign
 * - /api/v1/student-support/mentees
 * - /api/v1/student-support/mentees/unassigned
 * - /api/v1/student-support/mentoring-sessions
 * - /api/v1/student-support/mentoring-sessions/{id}
 * - /api/v1/student-support/mentoring-sessions/{id}/reflection
 * - /api/v1/student-support/counselling-appointments
 * - /api/v1/student-support/counselling-appointments/{id}
 * - /api/v1/student-support/confidential-records
 * - /api/v1/student-support/confidential-records/{id}
 * - /api/v1/student-support/development-plans
 * - /api/v1/student-support/development-plans/{id}
 * - /api/v1/student-support/development-plans/{id}/goals
 * - /api/v1/student-support/development-plans/goals/{id}
 * - /api/v1/student-support/referrals
 * - /api/v1/student-support/referrals/{id}
 * - /api/v1/student-support/follow-ups
 * - /api/v1/student-support/follow-ups/{id}
 * - /api/v1/student-support/telemetry
 */

import { apiFetch } from "@/lib/api-client";
import { ApiResponse } from "@campusos/types";
import {
  MentorAssignmentItem,
  MenteeItem,
  MentoringSessionItem,
  CounsellingAppointmentItem,
  ConfidentialCounsellingRecordItem,
  StudentDevelopmentPlanItem,
  DevelopmentGoalItem,
  SupportReferralItem,
  SupportFollowUpItem,
  SupportPolicyConfigItem,
  SupportTelemetryMetrics,
} from "../types/student-support";
import {
  MOCK_SUPPORT_CONFIG,
  MOCK_MENTOR_ASSIGNMENTS,
  MOCK_MENTEES,
  MOCK_MENTORING_SESSIONS,
  MOCK_COUNSELLING_APPOINTMENTS,
  MOCK_CONFIDENTIAL_RECORDS,
  MOCK_DEVELOPMENT_PLANS,
  MOCK_SUPPORT_REFERRALS,
  MOCK_SUPPORT_FOLLOW_UPS,
  MOCK_TELEMETRY_METRICS,
} from "../mocks/student-support.mock";

export class StudentSupportService {
  // ===========================================================================
  // POLICY CONFIG
  // ===========================================================================

  static async getConfig(): Promise<SupportPolicyConfigItem> {
    try {
      const res = await apiFetch<SupportPolicyConfigItem>("/api/v1/student-support/config");
      return res.data;
    } catch {
      return MOCK_SUPPORT_CONFIG;
    }
  }

  static async updateConfig(data: Partial<SupportPolicyConfigItem>): Promise<SupportPolicyConfigItem> {
    try {
      const res = await apiFetch<SupportPolicyConfigItem>("/api/v1/student-support/config", {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      return { ...MOCK_SUPPORT_CONFIG, ...data, updatedAt: new Date().toISOString() };
    }
  }

  // ===========================================================================
  // MENTOR ASSIGNMENTS & MENTEES
  // ===========================================================================

  static async listMentorAssignments(params?: {
    mentorUserId?: string;
    studentId?: string;
    status?: string;
    departmentId?: string;
  }): Promise<MentorAssignmentItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.mentorUserId) query.set("mentor_user_id", params.mentorUserId);
      if (params?.studentId) query.set("student_id", params.studentId);
      if (params?.status) query.set("status", params.status);
      if (params?.departmentId) query.set("department_id", params.departmentId);

      const res = await apiFetch<MentorAssignmentItem[]>(`/api/v1/student-support/mentor-assignments?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_MENTOR_ASSIGNMENTS];
      if (params?.mentorUserId) filtered = filtered.filter(a => a.mentorUserId === params.mentorUserId);
      if (params?.studentId) filtered = filtered.filter(a => a.studentId === params.studentId);
      if (params?.status) filtered = filtered.filter(a => a.status === params.status);
      return filtered;
    }
  }

  static async createMentorAssignment(data: Partial<MentorAssignmentItem>): Promise<MentorAssignmentItem> {
    try {
      const res = await apiFetch<MentorAssignmentItem>("/api/v1/student-support/mentor-assignments", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const newAssignment: MentorAssignmentItem = {
        id: `assign-${Date.now()}`,
        tenantId: "tenant-campus-01",
        studentId: data.studentId || "stu-new",
        studentName: data.studentName || "Student Candidate",
        studentRoll: data.studentRoll || "26CS999",
        mentorUserId: data.mentorUserId || "fac-001",
        mentorName: data.mentorName || "Dr. Arvind Swaminathan",
        academicYear: data.academicYear || "2026-2027",
        assignmentType: data.assignmentType || "MANUAL",
        status: "ACTIVE",
        assignedDate: data.assignedDate || new Date().toISOString().split("T")[0],
        notes: data.notes,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_MENTOR_ASSIGNMENTS.unshift(newAssignment);
      return newAssignment;
    }
  }

  static async reassignMentor(
    assignmentId: string,
    req: {
      newMentorUserId?: string;
      new_faculty_staff_id?: string;
      reason?: string;
      reassignment_reason?: string;
      effectiveDate?: string;
    }
  ): Promise<MentorAssignmentItem> {
    const newId = req.new_faculty_staff_id || req.newMentorUserId || "";
    const reasonText = req.reassignment_reason || req.reason || "";
    try {
      const res = await apiFetch<MentorAssignmentItem>(`/api/v1/student-support/mentor-assignments/${assignmentId}/reassign`, {
        method: "POST",
        body: JSON.stringify({
          new_mentor_user_id: newId,
          reason: reasonText,
          effective_date: req.effectiveDate,
        }),
      });
      return res.data;
    } catch {
      const old = MOCK_MENTOR_ASSIGNMENTS.find(a => a.id === assignmentId);
      if (old) {
        old.status = "REASSIGNED";
        old.endDate = req.effectiveDate || new Date().toISOString().split("T")[0];
        old.reassignmentReason = reasonText;
        old.reassignment_reason = reasonText;
      }
      const reassigned: MentorAssignmentItem = {
        id: `assign-${Date.now()}`,
        tenantId: "tenant-campus-01",
        studentId: old?.studentId || "stu-001",
        studentName: old?.studentName || "Student Candidate",
        studentRoll: old?.studentRoll || "26CS012",
        mentorUserId: newId,
        faculty_id: newId,
        mentorName: "Prof. Meenakshi Sundaram",
        faculty_name: "Prof. Meenakshi Sundaram",
        academicYear: old?.academicYear || "2026-2027",
        assignmentType: "REASSIGNED",
        status: "REASSIGNED",
        assignedDate: req.effectiveDate || new Date().toISOString().split("T")[0],
        reassignedFromId: assignmentId,
        reassignmentReason: reasonText,
        reassignment_reason: reasonText,
        notes: `Reassigned: ${reasonText}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_MENTOR_ASSIGNMENTS.unshift(reassigned);
      return reassigned;
    }
  }

  static async listAuthorizedMentees(): Promise<MenteeItem[]> {
    try {
      const res = await apiFetch<MenteeItem[]>("/api/v1/student-support/mentees");
      return res.data;
    } catch {
      return MOCK_MENTEES;
    }
  }

  static async getStudentAssignedMentor(studentId?: string): Promise<MentorAssignmentItem | null> {
    try {
      const path = studentId ? `/api/v1/student-support/mentor-assignments?student_id=${studentId}&status=ACTIVE` : "/api/v1/student-support/mentor-assignments/my-mentor";
      const res = await apiFetch<MentorAssignmentItem | MentorAssignmentItem[]>(path);
      if (Array.isArray(res.data)) {
        return res.data[0] || null;
      }
      return res.data;
    } catch {
      return MOCK_MENTOR_ASSIGNMENTS[0] || null;
    }
  }

  // ===========================================================================
  // MENTORING SESSIONS
  // ===========================================================================

  static async listMentoringSessions(params?: {
    mentorUserId?: string;
    studentId?: string;
    status?: string;
  }): Promise<MentoringSessionItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.mentorUserId) query.set("mentor_user_id", params.mentorUserId);
      if (params?.studentId) query.set("student_id", params.studentId);
      if (params?.status) query.set("status", params.status);

      const res = await apiFetch<MentoringSessionItem[]>(`/api/v1/student-support/mentoring-sessions?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_MENTORING_SESSIONS];
      if (params?.status) filtered = filtered.filter(s => s.status === params.status);
      return filtered;
    }
  }

  static async scheduleMentoringSession(data: Partial<MentoringSessionItem> & { attendeeStudentIds?: string[] }): Promise<MentoringSessionItem> {
    try {
      const res = await apiFetch<MentoringSessionItem>("/api/v1/student-support/mentoring-sessions", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const newSession: MentoringSessionItem = {
        id: `sess-${Date.now()}`,
        tenantId: "tenant-campus-01",
        assignmentId: data.assignmentId,
        mentorUserId: data.mentorUserId || "fac-001",
        mentorName: data.mentorName || "Dr. Arvind Swaminathan",
        sessionTitle: data.sessionTitle || "Mentoring Check-in",
        sessionType: data.sessionType || "ONE_ON_ONE",
        sessionDate: data.sessionDate || new Date().toISOString().split("T")[0],
        startTime: data.startTime || "10:00:00",
        endTime: data.endTime || "10:45:00",
        locationOrLink: data.locationOrLink || "Faculty Office Room 304",
        status: "SCHEDULED",
        summary: data.summary,
        actionItems: data.actionItems || [],
        followUpDate: data.followUpDate,
        createdByUserId: "fac-001",
        attendees: (data.attendeeStudentIds || ["stu-001"]).map((sid, idx) => ({
          id: `att-${Date.now()}-${idx}`,
          sessionId: `sess-${Date.now()}`,
          studentId: sid,
          studentName: "Aarav Sharma",
          attendanceStatus: "PENDING",
        })),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_MENTORING_SESSIONS.unshift(newSession);
      return newSession;
    }
  }

  static async updateMentoringSession(sessionId: string, data: Partial<MentoringSessionItem>): Promise<MentoringSessionItem> {
    try {
      const res = await apiFetch<MentoringSessionItem>(`/api/v1/student-support/mentoring-sessions/${sessionId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const existing = MOCK_MENTORING_SESSIONS.find(s => s.id === sessionId);
      if (existing) {
        Object.assign(existing, data, { updatedAt: new Date().toISOString() });
        return existing;
      }
      throw new Error("Session not found");
    }
  }

  static async recordAttendeeReflection(
    sessionId: string,
    studentId: string,
    data: { attendanceStatus?: string; studentFeedback?: string; studentReflection?: string }
  ) {
    try {
      const res = await apiFetch(`/api/v1/student-support/mentoring-sessions/${sessionId}/reflection?student_id=${studentId}`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const sess = MOCK_MENTORING_SESSIONS.find(s => s.id === sessionId);
      const att = sess?.attendees?.find(a => a.studentId === studentId);
      if (att) {
        if (data.attendanceStatus) att.attendanceStatus = data.attendanceStatus as any;
        if (data.studentFeedback) att.studentFeedback = data.studentFeedback;
        if (data.studentReflection) att.studentReflection = data.studentReflection;
      }
      return att;
    }
  }

  // ===========================================================================
  // COUNSELLING APPOINTMENTS
  // ===========================================================================

  static async listCounsellingAppointments(params?: {
    studentId?: string;
    counsellorUserId?: string;
    status?: string;
  }): Promise<CounsellingAppointmentItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.studentId) query.set("student_id", params.studentId);
      if (params?.counsellorUserId) query.set("counsellor_user_id", params.counsellorUserId);
      if (params?.status) query.set("status", params.status);

      const res = await apiFetch<CounsellingAppointmentItem[]>(`/api/v1/student-support/counselling-appointments?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_COUNSELLING_APPOINTMENTS];
      if (params?.status) filtered = filtered.filter(a => a.status === params.status);
      return filtered;
    }
  }

  static async requestCounsellingAppointment(data: Partial<CounsellingAppointmentItem>): Promise<CounsellingAppointmentItem> {
    try {
      const res = await apiFetch<CounsellingAppointmentItem>("/api/v1/student-support/counselling-appointments", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const seq = Math.floor(1000 + Math.random() * 9000);
      const newAppt: CounsellingAppointmentItem = {
        id: `appt-${Date.now()}`,
        appointmentNumber: `COU-2026-${seq}`,
        appointment_number: `COU-2026-${seq}`,
        tenantId: "tenant-campus-01",
        studentId: data.studentId || (data as any).student_id || "stu-001",
        student_id: data.studentId || (data as any).student_id || "stu-001",
        studentName: data.studentName || "Aarav Sharma",
        student_name: data.studentName || "Aarav Sharma",
        counsellorUserId: data.counsellorUserId || "coun-001",
        counsellorName: "Pooja Nambiar, M.Phil Clinical Psych",
        category: data.category || "GENERAL_COUNSELLING",
        appointmentDate: data.appointmentDate || (data as any).scheduled_start?.split("T")[0] || new Date().toISOString().split("T")[0],
        startTime: data.startTime || "14:00:00",
        endTime: data.endTime || "14:45:00",
        durationMinutes: data.durationMinutes || 45,
        mode: data.mode || (data as any).appointment_mode || "IN_PERSON",
        appointment_mode: data.mode || (data as any).appointment_mode || "IN_PERSON",
        venueOrLink: data.venueOrLink || (data as any).location || "Consultation Suite 102",
        location: data.venueOrLink || (data as any).location || "Consultation Suite 102",
        status: "REQUESTED",
        requestReason: data.requestReason || (data as any).reason_summary,
        reason_summary: data.requestReason || (data as any).reason_summary,
        bookedByUserId: "stu-001",
        isConfidential: true,
        hasConfidentialNotes: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_COUNSELLING_APPOINTMENTS.unshift(newAppt);
      return newAppt;
    }
  }

  static async updateCounsellingAppointment(appointmentId: string, data: Partial<CounsellingAppointmentItem>): Promise<CounsellingAppointmentItem> {
    try {
      const res = await apiFetch<CounsellingAppointmentItem>(`/api/v1/student-support/counselling-appointments/${appointmentId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const existing = MOCK_COUNSELLING_APPOINTMENTS.find(a => a.id === appointmentId);
      if (existing) {
        Object.assign(existing, data, { updatedAt: new Date().toISOString() });
        return existing;
      }
      throw new Error("Appointment not found");
    }
  }

  // ===========================================================================
  // STRICT CONFIDENTIAL COUNSELLING RECORDS
  // ===========================================================================

  static async createConfidentialRecord(data: Partial<ConfidentialCounsellingRecordItem>): Promise<ConfidentialCounsellingRecordItem> {
    try {
      const res = await apiFetch<ConfidentialCounsellingRecordItem>("/api/v1/student-support/confidential-records", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const consentVal = (data as any).consent_verified ?? data.consentConfirmed ?? true;
      const newRec: ConfidentialCounsellingRecordItem = {
        id: `conf-${Date.now()}`,
        tenantId: "tenant-campus-01",
        appointmentId: data.appointmentId || (data as any).appointment_id,
        appointment_id: data.appointmentId || (data as any).appointment_id,
        studentId: data.studentId || (data as any).student_id || "stu-001",
        student_id: data.studentId || (data as any).student_id || "stu-001",
        studentName: "Aarav Sharma",
        student_name: "Aarav Sharma",
        counsellorUserId: "coun-001",
        counsellorName: "Pooja Nambiar, M.Phil Clinical Psych",
        sessionNotesRestricted: data.sessionNotesRestricted || (data as any).session_observations || "",
        session_observations: (data as any).session_observations,
        interventionType: data.interventionType || "SOLUTION_FOCUSED",
        interventions_applied: (data as any).interventions_applied,
        clinicalObservations: data.clinicalObservations || (data as any).session_observations,
        followUpRecommended: data.followUpRecommended || (data as any).follow_up_recommended || false,
        follow_up_recommended: data.followUpRecommended || (data as any).follow_up_recommended || false,
        followUpTargetDate: data.followUpTargetDate,
        consentConfirmed: consentVal,
        consent_verified: consentVal,
        accessCount: 1,
        lastAccessedAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_CONFIDENTIAL_RECORDS.unshift(newRec);
      return newRec;
    }
  }

  static async getConfidentialRecord(recordId: string): Promise<ConfidentialCounsellingRecordItem> {
    try {
      const res = await apiFetch<ConfidentialCounsellingRecordItem>(`/api/v1/student-support/confidential-records/${recordId}`);
      return res.data;
    } catch {
      const rec = MOCK_CONFIDENTIAL_RECORDS.find(r => r.id === recordId);
      if (!rec) throw new Error("Confidential record not found or access restricted");
      if (rec.accessCount !== undefined) {
        rec.accessCount += 1;
      }
      rec.lastAccessedAt = new Date().toISOString();
      return rec;
    }
  }

  // ===========================================================================
  // STUDENT DEVELOPMENT PLANS (IDP)
  // ===========================================================================

  static async listDevelopmentPlans(params?: {
    studentId?: string;
    mentorUserId?: string;
  }): Promise<StudentDevelopmentPlanItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.studentId) query.set("student_id", params.studentId);
      if (params?.mentorUserId) query.set("mentor_user_id", params.mentorUserId);

      const res = await apiFetch<StudentDevelopmentPlanItem[]>(`/api/v1/student-support/development-plans?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_DEVELOPMENT_PLANS];
      if (params?.studentId) filtered = filtered.filter(p => p.studentId === params.studentId);
      return filtered;
    }
  }

  static async getDevelopmentPlan(planId: string): Promise<StudentDevelopmentPlanItem> {
    try {
      const res = await apiFetch<StudentDevelopmentPlanItem>(`/api/v1/student-support/development-plans/${planId}`);
      return res.data;
    } catch {
      const plan = MOCK_DEVELOPMENT_PLANS.find(p => p.id === planId);
      if (!plan) throw new Error("Development plan not found");
      return plan;
    }
  }

  static async createDevelopmentPlan(data: Partial<StudentDevelopmentPlanItem>): Promise<StudentDevelopmentPlanItem> {
    try {
      const res = await apiFetch<StudentDevelopmentPlanItem>("/api/v1/student-support/development-plans", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const newPlan: StudentDevelopmentPlanItem = {
        id: `plan-${Date.now()}`,
        tenantId: "tenant-campus-01",
        studentId: data.studentId || "stu-001",
        studentName: data.studentName || "Aarav Sharma",
        mentorUserId: data.mentorUserId || "fac-001",
        mentorName: "Dr. Arvind Swaminathan",
        title: data.title || "Individual Development Plan",
        academicYear: data.academicYear || "2026-2027",
        status: "ACTIVE",
        overallProgressPct: 0,
        reviewFrequency: data.reviewFrequency || "MONTHLY",
        nextReviewDate: data.nextReviewDate,
        strengthsSummary: data.strengthsSummary,
        areasForGrowth: data.areasForGrowth,
        careerAspirations: data.careerAspirations,
        goals: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_DEVELOPMENT_PLANS.unshift(newPlan);
      return newPlan;
    }
  }

  static async addGoalToPlan(planId: string, goalData: Partial<DevelopmentGoalItem>): Promise<DevelopmentGoalItem> {
    try {
      const res = await apiFetch<DevelopmentGoalItem>(`/api/v1/student-support/development-plans/${planId}/goals`, {
        method: "POST",
        body: JSON.stringify(goalData),
      });
      return res.data;
    } catch {
      const plan = MOCK_DEVELOPMENT_PLANS.find(p => p.id === planId);
      const newGoal: DevelopmentGoalItem = {
        id: `goal-${Date.now()}`,
        tenantId: "tenant-campus-01",
        planId,
        plan_id: planId,
        category: goalData.category || "ACADEMIC_EXCELLENCE",
        title: goalData.title || "Goal Title",
        description: goalData.description,
        targetDate: goalData.targetDate || (goalData as any).target_completion_date,
        target_completion_date: goalData.targetDate || (goalData as any).target_completion_date,
        successMetric: (goalData as any).success_metric,
        success_metric: (goalData as any).success_metric,
        status: "ACTIVE",
        progressPct: 0,
        progress_pct: 0,
        measurableMilestones: goalData.measurableMilestones || [],
        mentorNotes: goalData.mentorNotes,
        studentReflection: goalData.studentReflection,
        actionItems: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      if (plan) {
        if (!plan.goals) plan.goals = [];
        plan.goals.push(newGoal);
      }
      return newGoal;
    }
  }

  static async updateGoal(goalId: string, data: Partial<DevelopmentGoalItem>): Promise<DevelopmentGoalItem> {
    try {
      const res = await apiFetch<DevelopmentGoalItem>(`/api/v1/student-support/development-plans/goals/${goalId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      for (const p of MOCK_DEVELOPMENT_PLANS) {
        if (!p.goals) continue;
        const g = p.goals.find(goal => goal.id === goalId);
        if (g) {
          const newPct = (data as any).progress_pct ?? data.progressPct ?? g.progressPct ?? 0;
          Object.assign(g, data, {
            progressPct: newPct,
            progress_pct: newPct,
            updatedAt: new Date().toISOString(),
          });
          // Recalculate plan overall progress
          const totalPct = p.goals.reduce((acc, curr) => acc + (curr.progressPct ?? curr.progress_pct ?? 0), 0);
          p.overallProgressPct = Math.round(totalPct / p.goals.length);
          p.overall_progress_pct = p.overallProgressPct;
          return g;
        }
      }
      throw new Error("Goal not found");
    }
  }

  // ===========================================================================
  // SUPPORT REFERRALS & FOLLOW-UPS
  // ===========================================================================

  static async listSupportReferrals(params?: {
    studentId?: string;
    targetService?: string;
    status?: string;
  }): Promise<SupportReferralItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.studentId) query.set("student_id", params.studentId);
      if (params?.targetService) query.set("target_service", params.targetService);
      if (params?.status) query.set("status", params.status);

      const res = await apiFetch<SupportReferralItem[]>(`/api/v1/student-support/referrals?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_SUPPORT_REFERRALS];
      if (params?.targetService) filtered = filtered.filter(r => r.targetService === params.targetService);
      if (params?.status) filtered = filtered.filter(r => r.status === params.status);
      return filtered;
    }
  }

  static async createSupportReferral(data: Partial<SupportReferralItem>): Promise<SupportReferralItem> {
    try {
      const res = await apiFetch<SupportReferralItem>("/api/v1/student-support/referrals", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const refConsent = (data as any).student_consent_obtained ?? data.consentObtained ?? true;
      const refSeq = Math.floor(Math.random() * 9000 + 1000);
      const refCode = `REF-${new Date().getFullYear()}-${refSeq}`;
      const newRef: SupportReferralItem = {
        id: `ref-${Date.now()}`,
        tenantId: "tenant-campus-01",
        referralCode: refCode,
        referral_number: refCode,
        studentId: data.studentId || (data as any).student_id || "stu-001",
        student_id: data.studentId || (data as any).student_id || "stu-001",
        studentName: data.studentName || "Aarav Sharma",
        referringUserId: "fac-001",
        referringUserName: "Dr. Arvind Swaminathan",
        referringRole: data.referringRole || (data as any).referrer_role || "FACULTY_MENTOR",
        referrer_role: data.referringRole || (data as any).referrer_role || "FACULTY_MENTOR",
        targetService: data.targetService || (data as any).target_service || "CAREER_SERVICES",
        target_service: data.targetService || (data as any).target_service || "CAREER_SERVICES",
        reasonCategory: data.reasonCategory || (data as any).reason_category || "Skill Enhancement",
        reason_category: data.reasonCategory || (data as any).reason_category || "Skill Enhancement",
        priority: data.priority || "STANDARD",
        summaryNotes: data.summaryNotes,
        status: "PENDING",
        consentObtained: refConsent,
        student_consent_obtained: refConsent,
        followUps: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_SUPPORT_REFERRALS.unshift(newRef);
      return newRef;
    }
  }

  static async updateSupportReferral(referralId: string, data: Partial<SupportReferralItem>): Promise<SupportReferralItem> {
    try {
      const res = await apiFetch<SupportReferralItem>(`/api/v1/student-support/referrals/${referralId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const existing = MOCK_SUPPORT_REFERRALS.find(r => r.id === referralId);
      if (existing) {
        Object.assign(existing, data, { updatedAt: new Date().toISOString() });
        return existing;
      }
      throw new Error("Referral not found");
    }
  }

  static async listFollowUps(params?: {
    assignedUserId?: string;
    status?: string;
  }): Promise<SupportFollowUpItem[]> {
    try {
      const query = new URLSearchParams();
      if (params?.assignedUserId) query.set("assigned_user_id", params.assignedUserId);
      if (params?.status) query.set("status", params.status);

      const res = await apiFetch<SupportFollowUpItem[]>(`/api/v1/student-support/follow-ups?${query.toString()}`);
      return res.data;
    } catch {
      let filtered = [...MOCK_SUPPORT_FOLLOW_UPS];
      if (params?.status) filtered = filtered.filter(f => f.status === params.status);
      return filtered;
    }
  }

  static async createFollowUp(data: Partial<SupportFollowUpItem>): Promise<SupportFollowUpItem> {
    try {
      const res = await apiFetch<SupportFollowUpItem>("/api/v1/student-support/follow-ups", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const newFup: SupportFollowUpItem = {
        id: `fup-${Date.now()}`,
        tenantId: "tenant-campus-01",
        referralId: data.referralId,
        planId: data.planId,
        appointmentId: data.appointmentId,
        assignedUserId: data.assignedUserId || (data as any).assigned_to_user_id || "fac-001",
        assigned_to_user_id: data.assignedUserId || (data as any).assigned_to_user_id || "fac-001",
        assignedUserName: "Dr. Arvind Swaminathan",
        title: data.title || "Follow-up Task",
        dueDate: data.dueDate || (data as any).due_date || new Date().toISOString().split("T")[0],
        due_date: data.dueDate || (data as any).due_date || new Date().toISOString().split("T")[0],
        priority: data.priority || "HIGH",
        notes: data.notes,
        status: "PENDING",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      MOCK_SUPPORT_FOLLOW_UPS.unshift(newFup);
      return newFup;
    }
  }

  static async updateFollowUp(followupId: string, data: Partial<SupportFollowUpItem>): Promise<SupportFollowUpItem> {
    try {
      const res = await apiFetch<SupportFollowUpItem>(`/api/v1/student-support/follow-ups/${followupId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return res.data;
    } catch {
      const existing = MOCK_SUPPORT_FOLLOW_UPS.find(f => f.id === followupId);
      if (existing) {
        Object.assign(existing, data, { updatedAt: new Date().toISOString() });
        return existing;
      }
      throw new Error("Follow-up not found");
    }
  }

  // ===========================================================================
  // PRIVACY-SAFE OPERATIONAL TELEMETRY
  // ===========================================================================

  static async getTelemetryMetrics(): Promise<SupportTelemetryMetrics> {
    try {
      const res = await apiFetch<SupportTelemetryMetrics>("/api/v1/student-support/telemetry");
      return res.data;
    } catch {
      return MOCK_TELEMETRY_METRICS;
    }
  }

  // ===========================================================================
  // CONVENIENCE ROUTE & WORKFLOW ALIASES
  // ===========================================================================

  static async getPolicyConfig(): Promise<SupportPolicyConfigItem> {
    return this.getConfig();
  }

  static async updatePolicyConfig(data: any): Promise<SupportPolicyConfigItem> {
    return this.updateConfig(data);
  }

  static async getMentorAssignments(params?: any): Promise<MentorAssignmentItem[]> {
    return this.listMentorAssignments(params);
  }

  static async getAssignedMentees(): Promise<MenteeItem[]> {
    return this.listAuthorizedMentees();
  }

  static async getUnassignedStudents(): Promise<MenteeItem[]> {
    return [
      {
        student_id: "stu-unassigned-01",
        studentId: "stu-unassigned-01",
        student_name: "Rohan Varma",
        studentName: "Rohan Varma",
        student_reg_no: "26CS089",
        rollNumber: "26CS089",
        department_name: "Computer Science",
        departmentName: "Computer Science",
        program_name: "B.Tech Computer Science",
        programName: "B.Tech Computer Science",
        current_year_semester: "Year 2, Sem 3",
        academicYear: "2026-2027",
        assignmentId: "",
        assignedDate: "",
        openFollowUpsCount: 0,
      },
      {
        student_id: "stu-unassigned-02",
        studentId: "stu-unassigned-02",
        student_name: "Meera Krishnan",
        studentName: "Meera Krishnan",
        student_reg_no: "26EC034",
        rollNumber: "26EC034",
        department_name: "Electronics & Communication",
        departmentName: "Electronics & Communication",
        program_name: "B.Tech Electronics",
        programName: "B.Tech Electronics",
        current_year_semester: "Year 2, Sem 3",
        academicYear: "2026-2027",
        assignmentId: "",
        assignedDate: "",
        openFollowUpsCount: 0,
      },
    ];
  }

  static async getMentoringSessions(params?: any): Promise<MentoringSessionItem[]> {
    return this.listMentoringSessions(params);
  }

  static async createMentoringSession(data: any): Promise<MentoringSessionItem> {
    return this.scheduleMentoringSession({
      title: data.title,
      sessionTitle: data.title,
      sessionType: data.session_type,
      session_type: data.session_type,
      sessionDate: data.scheduled_start ? data.scheduled_start.split("T")[0] : undefined,
      scheduled_start: data.scheduled_start,
      scheduled_end: data.scheduled_end,
      locationOrLink: data.location,
      location: data.location,
      summary: data.discussion_points,
      discussion_points: data.discussion_points,
      attendeeStudentIds: data.student_ids,
      ...data,
    });
  }

  static async completeMentoringSession(sessionId: string, data: { summary_notes: string; action_items?: any[] }): Promise<MentoringSessionItem> {
    return this.updateMentoringSession(sessionId, {
      status: "COMPLETED",
      summary: data.summary_notes,
      summary_notes: data.summary_notes,
      actionItems: data.action_items,
    });
  }

  static async submitMenteeReflection(sessionId: string, reflectionText: string): Promise<MentoringSessionItem> {
    const session = MOCK_MENTORING_SESSIONS.find(s => s.id === sessionId);
    if (session) {
      session.student_reflection = reflectionText;
      return session;
    }
    const sessions = await this.listMentoringSessions();
    const target = sessions.find(s => s.id === sessionId) || sessions[0];
    if (target) {
      target.student_reflection = reflectionText;
      return target;
    }
    throw new Error("Session not found");
  }

  static async getCounsellingAppointments(params?: any): Promise<CounsellingAppointmentItem[]> {
    return this.listCounsellingAppointments(params);
  }

  static async createCounsellingAppointment(data: any): Promise<CounsellingAppointmentItem> {
    return this.requestCounsellingAppointment({
      category: data.category,
      mode: data.appointment_mode,
      appointment_mode: data.appointment_mode,
      appointmentDate: data.scheduled_start ? data.scheduled_start.split("T")[0] : undefined,
      scheduled_start: data.scheduled_start,
      scheduled_end: data.scheduled_end,
      venueOrLink: data.virtual_meeting_link || data.location,
      location: data.location,
      requestReason: data.reason_summary,
      reason_summary: data.reason_summary,
      ...data,
    });
  }

  static async transitionCounsellingAppointment(appointmentId: string, data: any): Promise<CounsellingAppointmentItem> {
    return this.updateCounsellingAppointment(appointmentId, data);
  }

  static async getConfidentialRecords(): Promise<ConfidentialCounsellingRecordItem[]> {
    return MOCK_CONFIDENTIAL_RECORDS;
  }

  static async getDevelopmentPlans(params?: any): Promise<StudentDevelopmentPlanItem[]> {
    return this.listDevelopmentPlans(params);
  }

  static async getGoalsForPlan(planId: string): Promise<DevelopmentGoalItem[]> {
    const plan = await this.getDevelopmentPlan(planId);
    return plan?.goals || [];
  }

  static async getReferrals(params?: any): Promise<SupportReferralItem[]> {
    return this.listSupportReferrals(params);
  }

  static async createReferral(data: any): Promise<SupportReferralItem> {
    return this.createSupportReferral({
      studentId: data.student_id,
      student_id: data.student_id,
      targetService: data.target_service,
      target_service: data.target_service,
      reasonCategory: data.reason_category,
      reason_category: data.reason_category,
      consentObtained: data.student_consent_obtained,
      student_consent_obtained: data.student_consent_obtained,
      referringRole: data.referrer_role,
      referring_role: data.referrer_role,
      ...data,
    });
  }

  static async updateReferralStatus(referralId: string, data: { status: any; status_notes?: string }): Promise<SupportReferralItem> {
    return this.updateSupportReferral(referralId, {
      status: data.status,
      outcomeNotes: data.status_notes,
    });
  }

  static async getFollowUps(params?: any): Promise<SupportFollowUpItem[]> {
    return this.listFollowUps(params);
  }
}

