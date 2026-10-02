/**
 * CampusOS Examination & Assessment Service Layer
 * In-memory reactive mock adapter implementing all future FastAPI contracts:
 * Assessments, Schedules, Conflict Detection, Eligibility Evaluations, Marks Rosters,
 * Finalization, Corrections, Grade Calculations, Results, Publications, and Reports.
 */

import { ApiResponse } from "@campusos/types";
import {
  Assessment,
  AssessmentComponent,
  Examination,
  ExamSchedule,
  ExamConflictCheck,
  ExamEligibility,
  EligibilityStatus,
  Mark,
  MarkStatus,
  MarkCorrection,
  GradeScale,
  Result,
  ResultPublication,
  ExamReportFilter,
  ExamDashboardSummary,
} from "@/types/examinations";
import {
  AssessmentItem,
  ExamScheduleItem,
  StudentResultItem,
  MOCK_ASSESSMENTS,
  MOCK_EXAM_SCHEDULES,
  MOCK_RESULTS,
  MOCK_EXAMINATIONS,
  MOCK_CANONICAL_ASSESSMENTS,
  MOCK_CANONICAL_EXAM_SCHEDULES,
  MOCK_EXAM_ELIGIBILITY_RECORDS,
  MOCK_CANONICAL_MARKS,
  MOCK_MARK_CORRECTIONS,
  MOCK_CANONICAL_RESULTS,
  MOCK_RESULT_PUBLICATIONS,
  MOCK_EXAM_OPERATIONS_SUMMARY,
} from "@/mocks/examinations.mock";
import {
  DEFAULT_GRADE_SCALE,
  calculateAssessmentTotal,
  calculateGrade,
  calculatePercentage,
  calculateResultStatus,
  calculateGradeDistribution,
} from "./grading-calculator";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export interface MarksRosterEntry {
  id: string;
  student_id: string;
  roll_number: string;
  first_name: string;
  last_name: string;
  marks_obtained: number;
  max_marks: number;
  status: string;
  is_absent: boolean;
  remarks: string;
}

export interface MarksRosterData {
  assessment: AssessmentItem;
  entries: MarksRosterEntry[];
}

export interface AssessmentFilters {
  courseOfferingId?: string;
  department?: string;
  semester?: number;
  status?: string;
  type?: string;
  search?: string;
}

export interface ScheduleFilters {
  examinationId?: string;
  date?: string;
  department?: string;
  semester?: number;
  room?: string;
  facultyId?: string;
  status?: string;
  search?: string;
}

export interface EligibilityFilters {
  examinationId?: string;
  courseOfferingId?: string;
  department?: string;
  status?: EligibilityStatus | "ALL";
  search?: string;
}

export interface ResultFilters {
  examinationId?: string;
  courseOfferingId?: string;
  studentId?: string;
  department?: string;
  semester?: number;
  status?: string;
  search?: string;
}

class ExaminationsService {
  // In-memory canonical collections
  private examinations: Examination[] = [...MOCK_EXAMINATIONS];
  private assessments: Assessment[] = [...MOCK_CANONICAL_ASSESSMENTS];
  private schedules: ExamSchedule[] = [...MOCK_CANONICAL_EXAM_SCHEDULES];
  private eligibilityRecords: ExamEligibility[] = [...MOCK_EXAM_ELIGIBILITY_RECORDS];
  private marks: Mark[] = [...MOCK_CANONICAL_MARKS];
  private corrections: MarkCorrection[] = [...MOCK_MARK_CORRECTIONS];
  private gradeScales: GradeScale[] = [DEFAULT_GRADE_SCALE];
  private results: Result[] = [...MOCK_CANONICAL_RESULTS];
  private publications: ResultPublication[] = [...MOCK_RESULT_PUBLICATIONS];

  // Legacy mirrors
  private legacyAssessments: AssessmentItem[] = [...MOCK_ASSESSMENTS];
  private legacySchedules: ExamScheduleItem[] = [...MOCK_EXAM_SCHEDULES];
  private legacyResults: StudentResultItem[] = [...MOCK_RESULTS];

  // ==========================================
  // 1. Dashboard & Operations Summary
  // ==========================================

  async getDashboardSummary(): Promise<ApiResponse<ExamDashboardSummary>> {
    await new Promise((r) => setTimeout(r, 40));

    const distribution = calculateGradeDistribution(this.results);
    const summary: ExamDashboardSummary = {
      ...MOCK_EXAM_OPERATIONS_SUMMARY,
      activeExaminationsCount: this.examinations.filter((e) => e.status === "ONGOING" || e.status === "SCHEDULED").length,
      upcomingExamsCount: this.schedules.filter((s) => s.status === "CONFIRMED" || s.status === "SCHEDULED").length,
      totalAssessmentsCount: this.assessments.length,
      pendingMarksCount: this.assessments.filter((a) => !a.isFinalized).length,
      marksAwaitingReviewCount: this.corrections.filter((c) => c.status === "PENDING").length,
      eligibleStudentsCount: this.eligibilityRecords.filter((e) => e.eligibilityStatus === "ELIGIBLE" || e.eligibilityStatus === "CONDITIONALLY_ELIGIBLE").length,
      ineligibleStudentsCount: this.eligibilityRecords.filter((e) => e.eligibilityStatus === "INELIGIBLE").length,
      resultsAwaitingFinalizationCount: this.results.filter((r) => !r.isFinalized).length,
      resultsAwaitingPublicationCount: this.publications.filter((p) => p.status === "READY").length,
      publishedResultsCount: this.results.filter((r) => r.isPublished).length,
      gradeDistribution: distribution,
    };

    return { success: true, data: summary };
  }

  // Legacy dashboard support
  async getDashboard(): Promise<ApiResponse<{
    active_terms_count: number;
    assessments_pending_marks: number;
    results_awaiting_publication_count: number;
    total_published_results_count: number;
    recent_assessments?: Assessment[];
    upcoming_schedules?: ExamSchedule[];
  }>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        active_terms_count: this.examinations.filter((e) => e.status === "ONGOING" || e.status === "SCHEDULED").length,
        assessments_pending_marks: this.assessments.filter((a) => !a.isFinalized).length,
        results_awaiting_publication_count: this.publications.filter((p) => p.status === "READY").length,
        total_published_results_count: this.results.filter((r) => r.isPublished).length,
        recent_assessments: this.assessments.slice(0, 5),
        upcoming_schedules: this.schedules.slice(0, 5),
      },
    };
  }

  // ==========================================
  // 2. Examination Cycles
  // ==========================================

  async getExaminations(filters?: { status?: string; semester?: number }): Promise<ApiResponse<Examination[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.examinations];
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((e) => e.status === filters.status);
    }
    if (filters?.semester) {
      items = items.filter((e) => e.semester === filters.semester);
    }
    return { success: true, data: items };
  }

  async getExaminationById(id: string): Promise<ApiResponse<Examination>> {
    await new Promise((r) => setTimeout(r, 30));
    const found = this.examinations.find((e) => e.id === id);
    if (!found) {
      throw new Error(`Examination cycle '${id}' not found`);
    }
    return { success: true, data: found };
  }

  async createExamination(data: Partial<Examination>): Promise<ApiResponse<Examination>> {
    await new Promise((r) => setTimeout(r, 80));
    const newExam: Examination = {
      id: `exam-${Date.now()}`,
      name: data.name || "Semester Examination",
      academicYear: data.academicYear || "2026-2027",
      semester: data.semester || 5,
      type: data.type || "END_SEMESTER",
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      endDate: data.endDate || new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
      status: data.status || "SCHEDULED",
      totalSubjects: data.totalSubjects || 6,
      totalCandidates: data.totalCandidates || 180,
      description: data.description || "",
      createdAt: new Date().toISOString(),
    };
    this.examinations.unshift(newExam);
    return { success: true, data: newExam };
  }

  // ==========================================
  // 3. Assessment Schemes & Components
  // ==========================================

  async getAssessments(filters?: AssessmentFilters | number): Promise<ApiResponse<Assessment[]>> {
    await new Promise((r) => setTimeout(r, 40));
    // Support legacy number semester parameter
    if (typeof filters === "number") {
      return { success: true, data: this.assessments.filter((a) => a.semester === filters) };
    }

    let items = [...this.assessments];
    if (filters?.courseOfferingId) {
      items = items.filter((a) => a.courseOfferingId === filters.courseOfferingId);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((a) => a.department === filters.department);
    }
    if (filters?.semester) {
      items = items.filter((a) => a.semester === Number(filters.semester));
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((a) => a.status === filters.status);
    }
    if (filters?.type && filters.type !== "ALL") {
      items = items.filter((a) => a.type === filters.type);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.courseCode.toLowerCase().includes(q) ||
          a.courseName.toLowerCase().includes(q) ||
          a.facultyName.toLowerCase().includes(q)
      );
    }
    return { success: true, data: items };
  }

  async getAssessmentById(id: string): Promise<ApiResponse<Assessment>> {
    await new Promise((r) => setTimeout(r, 30));
    const found = this.assessments.find((a) => a.id === id);
    if (!found) {
      throw new Error(`Assessment '${id}' not found`);
    }
    return { success: true, data: found };
  }

  async createAssessment(data: Partial<Assessment>): Promise<ApiResponse<Assessment>> {
    await new Promise((r) => setTimeout(r, 80));

    const components: AssessmentComponent[] = data.components || [
      {
        id: `comp-${Date.now()}-1`,
        name: `${data.name || "Internal"} Written Paper`,
        type: data.type || "INTERNAL",
        maxMarks: data.maxMarks || 50,
        passingMarks: data.passingMarks || 20,
        weightage: data.weightage || 50,
        sequence: 1,
      },
    ];

    const { totalMaxMarks, totalWeightage } = calculateAssessmentTotal(components);

    const newAsm: Assessment = {
      id: `asm-${Date.now()}`,
      name: data.name || "Continuous Evaluation Scheme",
      code: data.code || `IA-${this.assessments.length + 1}`,
      type: data.type || "INTERNAL",
      courseOfferingId: data.courseOfferingId || "co-cs301-a",
      courseCode: data.courseCode || "CS301",
      courseName: data.courseName || "Data Structures & Algorithms",
      section: data.section || "A",
      department: data.department || "Computer Science & Engineering",
      academicYear: data.academicYear || "2026-2027",
      semester: data.semester || 5,
      facultyId: data.facultyId || "fac-001",
      facultyName: data.facultyName || "Dr. Ramesh Sundaram",
      maxMarks: totalMaxMarks || data.maxMarks || 100,
      passingMarks: data.passingMarks || 40,
      weightage: totalWeightage || data.weightage || 40,
      sequence: data.sequence || this.assessments.length + 1,
      date: data.date || new Date().toISOString().split("T")[0],
      status: "OPEN",
      isFinalized: false,
      components,
      totalEnrolled: 68,
      totalEntered: 0,
      createdAt: new Date().toISOString(),
    };

    this.assessments.unshift(newAsm);

    // Seed empty mark roster for all enrolled students
    MOCK_STUDENTS.forEach((student) => {
      this.marks.push({
        id: `mark-${newAsm.id}-${student.id}`,
        assessmentId: newAsm.id,
        studentId: student.id,
        studentName: `${student.firstName} ${student.lastName}`,
        rollNumber: student.rollNumber,
        courseOfferingId: newAsm.courseOfferingId,
        maxMarks: newAsm.maxMarks,
        marksObtained: null,
        status: "NOT_ENTERED",
        isAbsent: false,
        isFinalized: false,
        updatedAt: new Date().toISOString(),
      });
    });

    return { success: true, data: newAsm };
  }

  async updateAssessment(id: string, updates: Partial<Assessment>): Promise<ApiResponse<Assessment>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.assessments.findIndex((a) => a.id === id);
    if (idx === -1) {
      throw new Error(`Assessment '${id}' not found`);
    }

    this.assessments[idx] = { ...this.assessments[idx], ...updates };
    return { success: true, data: this.assessments[idx] };
  }

  async finalizeAssessment(id: string): Promise<ApiResponse<Assessment>> {
    await new Promise((r) => setTimeout(r, 80));
    const asm = this.assessments.find((a) => a.id === id);
    if (!asm) {
      throw new Error(`Assessment '${id}' not found`);
    }

    // Verify marks completion
    const associatedMarks = this.marks.filter((m) => m.assessmentId === id);
    const unentered = associatedMarks.filter((m) => m.status === "NOT_ENTERED");
    if (unentered.length > 0) {
      throw new Error(`Cannot finalize: ${unentered.length} student marks have not been entered or accounted for.`);
    }

    asm.isFinalized = true;
    asm.status = "FINALIZED";
    asm.finalizedAt = new Date().toISOString();

    associatedMarks.forEach((m) => {
      m.isFinalized = true;
      m.finalizedAt = asm.finalizedAt;
    });

    return { success: true, data: asm };
  }

  // ==========================================
  // 4. Examination Timetable & Schedules
  // ==========================================

  async getSchedules(filters?: ScheduleFilters): Promise<ApiResponse<ExamSchedule[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.schedules];

    if (filters?.examinationId && filters.examinationId !== "ALL") {
      items = items.filter((s) => s.examinationId === filters.examinationId);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((s) => s.department === filters.department);
    }
    if (filters?.date) {
      items = items.filter((s) => s.date === filters.date);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((s) => s.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (s) =>
          s.courseCode.toLowerCase().includes(q) ||
          s.courseName.toLowerCase().includes(q) ||
          s.room.toLowerCase().includes(q) ||
          s.facultyName.toLowerCase().includes(q)
      );
    }
    return { success: true, data: items };
  }

  async getScheduleById(id: string): Promise<ApiResponse<ExamSchedule>> {
    await new Promise((r) => setTimeout(r, 30));
    const found = this.schedules.find((s) => s.id === id);
    if (!found) {
      throw new Error(`Exam schedule '${id}' not found`);
    }
    return { success: true, data: found };
  }

  /**
   * Conflict Detection Engine:
   * Identifies room double-bookings, section clashes, or invigilator overlaps.
   */
  async checkScheduleConflicts(candidate: {
    date: string;
    startTime: string;
    endTime: string;
    room: string;
    section: string;
    facultyId: string;
    excludeScheduleId?: string;
  }): Promise<ApiResponse<ExamConflictCheck>> {
    await new Promise((r) => setTimeout(r, 40));

    const matches = this.schedules.filter(
      (s) =>
        s.date === candidate.date &&
        s.id !== candidate.excludeScheduleId &&
        s.status !== "CANCELLED"
    );

    // Room collision
    const roomConflict = matches.find((s) => s.room === candidate.room);
    if (roomConflict) {
      return {
        success: true,
        data: {
          hasConflict: true,
          conflictType: "ROOM_OVERLAP",
          message: `Room ${candidate.room} is already booked on ${candidate.date} for ${roomConflict.courseCode} (${roomConflict.startTime} - ${roomConflict.endTime}).`,
          conflictingScheduleId: roomConflict.id,
        },
      };
    }

    // Section clash
    const sectionConflict = matches.find((s) => s.section === candidate.section);
    if (sectionConflict) {
      return {
        success: true,
        data: {
          hasConflict: true,
          conflictType: "SECTION_OVERLAP",
          message: `Section ${candidate.section} already has an exam scheduled (${sectionConflict.courseCode}) on ${candidate.date}.`,
          conflictingScheduleId: sectionConflict.id,
        },
      };
    }

    // Faculty invigilator overlap
    const facultyConflict = matches.find((s) => s.facultyId === candidate.facultyId);
    if (facultyConflict) {
      return {
        success: true,
        data: {
          hasConflict: true,
          conflictType: "FACULTY_OVERLAP",
          message: `Invigilator ${facultyConflict.facultyName} is already assigned to Room ${facultyConflict.room} at this time.`,
          conflictingScheduleId: facultyConflict.id,
        },
      };
    }

    return {
      success: true,
      data: {
        hasConflict: false,
      },
    };
  }

  async createSchedule(data: Partial<ExamSchedule>): Promise<ApiResponse<ExamSchedule>> {
    await new Promise((r) => setTimeout(r, 80));

    const newSch: ExamSchedule = {
      id: `sch-${Date.now()}`,
      examinationId: data.examinationId || "exam-2026-ese",
      examinationName: data.examinationName || "End Semester Examinations Nov/Dec 2026",
      assessmentId: data.assessmentId,
      assessmentTitle: data.assessmentTitle || "Semester Written Paper",
      courseOfferingId: data.courseOfferingId || "co-cs301-a",
      courseCode: data.courseCode || "CS301",
      courseName: data.courseName || "Data Structures & Algorithms",
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      semester: data.semester || 5,
      section: data.section || "A",
      date: data.date || new Date().toISOString().split("T")[0],
      startTime: data.startTime || "10:00 AM",
      endTime: data.endTime || "01:00 PM",
      room: data.room || "CS-LH-201",
      facultyId: data.facultyId || "fac-001",
      facultyName: data.facultyName || "Dr. Ramesh Sundaram",
      totalCandidates: data.totalCandidates || 68,
      status: data.status || "CONFIRMED",
      invigilatorNotes: data.invigilatorNotes || "General university closed book exam guidelines apply.",
      createdAt: new Date().toISOString(),
    };

    this.schedules.unshift(newSch);
    return { success: true, data: newSch };
  }

  async updateSchedule(id: string, updates: Partial<ExamSchedule>): Promise<ApiResponse<ExamSchedule>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.schedules.findIndex((s) => s.id === id);
    if (idx === -1) {
      throw new Error(`Schedule '${id}' not found`);
    }

    this.schedules[idx] = { ...this.schedules[idx], ...updates };
    return { success: true, data: this.schedules[idx] };
  }

  // ==========================================
  // 5. Student Eligibility Evaluations
  // ==========================================

  async getEligibility(filters?: EligibilityFilters): Promise<ApiResponse<ExamEligibility[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.eligibilityRecords];

    if (filters?.examinationId && filters.examinationId !== "ALL") {
      items = items.filter((e) => e.examinationId === filters.examinationId);
    }
    if (filters?.courseOfferingId) {
      items = items.filter((e) => e.courseOfferingId === filters.courseOfferingId);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((e) => e.department === filters.department);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((e) => e.eligibilityStatus === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (e) =>
          e.studentName.toLowerCase().includes(q) ||
          e.rollNumber.toLowerCase().includes(q) ||
          e.courseCode.toLowerCase().includes(q)
      );
    }
    return { success: true, data: items };
  }

  async reviewEligibility(
    id: string,
    action: "APPROVE_EXCEPTION" | "REJECT_EXCEPTION" | "FLAG_FOR_REVIEW",
    overrideReason?: string
  ): Promise<ApiResponse<ExamEligibility>> {
    await new Promise((r) => setTimeout(r, 70));
    const record = this.eligibilityRecords.find((e) => e.id === id);
    if (!record) {
      throw new Error(`Eligibility record '${id}' not found`);
    }

    if (action === "APPROVE_EXCEPTION") {
      record.eligibilityStatus = "CONDITIONALLY_ELIGIBLE";
      record.isOverridden = true;
      record.overrideReason = overrideReason || "Sanctioned by HOD Academic Council.";
      record.overriddenBy = "Dr. Anita Roy (HOD)";
    } else if (action === "REJECT_EXCEPTION") {
      record.eligibilityStatus = "INELIGIBLE";
      record.isOverridden = false;
      record.reason = overrideReason || "Condonation denied; attendance below critical boundary.";
    } else {
      record.eligibilityStatus = "PENDING_REVIEW";
    }

    return { success: true, data: record };
  }

  // ==========================================
  // 6. Marks Entry & Validation
  // ==========================================

  async getMarks(assessmentId: string): Promise<ApiResponse<Mark[]>> {
    await new Promise((r) => setTimeout(r, 40));
    const items = this.marks.filter((m) => m.assessmentId === assessmentId);
    return { success: true, data: items };
  }

  async saveMarks(
    assessmentId: string,
    marksList: { studentId: string; marksObtained: number | null; status: MarkStatus; remarks?: string }[]
  ): Promise<ApiResponse<{ updatedCount: number }>> {
    await new Promise((r) => setTimeout(r, 80));

    const asm = this.assessments.find((a) => a.id === assessmentId);
    if (asm?.isFinalized) {
      throw new Error("This assessment is locked and finalized. Submit a Mark Correction request instead.");
    }

    let updatedCount = 0;
    marksList.forEach((input) => {
      const existing = this.marks.find(
        (m) => m.assessmentId === assessmentId && m.studentId === input.studentId
      );

      if (existing) {
        // Validation: bounds check
        if (input.marksObtained !== null) {
          if (input.marksObtained < 0 || input.marksObtained > existing.maxMarks) {
            throw new Error(
              `Invalid mark for ${existing.studentName}: must be between 0 and ${existing.maxMarks}`
            );
          }
        }

        existing.marksObtained = input.marksObtained;
        existing.status = input.status;
        existing.isAbsent = input.status === "ABSENT";
        existing.remarks = input.remarks || existing.remarks;
        existing.updatedAt = new Date().toISOString();
        updatedCount++;
      }
    });

    if (asm) {
      const enteredCount = this.marks.filter(
        (m) => m.assessmentId === assessmentId && m.status !== "NOT_ENTERED"
      ).length;
      asm.totalEntered = enteredCount;
      if (enteredCount === asm.totalEnrolled) {
        asm.status = "COMPLETED";
      }
    }

    return { success: true, data: { updatedCount } };
  }

  // Legacy marks roster compatibility
  async getMarksRoster(_courseOfferingId: string, assessmentId: string): Promise<ApiResponse<MarksRosterData>> {
    await new Promise((r) => setTimeout(r, 60));
    const currentAsm = this.legacyAssessments.find((a) => a.id === assessmentId) || this.legacyAssessments[0];
    const rosterEntries: MarksRosterEntry[] = MOCK_STUDENTS.map((stu, i) => ({
      id: `mark-${stu.id}-${assessmentId}`,
      student_id: stu.id,
      roll_number: stu.rollNumber,
      first_name: stu.firstName,
      last_name: stu.lastName,
      marks_obtained: i === 0 ? 46 : i === 1 ? 48 : 39,
      max_marks: currentAsm?.totalMarks || 50,
      status: "PRESENT",
      is_absent: false,
      remarks: "Satisfactory",
    }));

    return {
      success: true,
      data: {
        assessment: currentAsm,
        entries: rosterEntries,
      },
    };
  }

  async submitMarks(assessmentId: string, marksData: Record<string, unknown>): Promise<ApiResponse<{ count: number }>> {
    await new Promise((r) => setTimeout(r, 100));
    const asm = this.assessments.find((a) => a.id === assessmentId);
    if (asm) {
      asm.status = "COMPLETED";
    }
    return { success: true, data: { count: Object.keys(marksData || {}).length } };
  }

  // ==========================================
  // 7. Supervised Mark Corrections
  // ==========================================

  async getMarkCorrections(filters?: { status?: string }): Promise<ApiResponse<MarkCorrection[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.corrections];
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((c) => c.status === filters.status);
    }
    return { success: true, data: items };
  }

  async requestMarkCorrection(data: {
    markId: string;
    requestedMark: number | null;
    requestedStatus: MarkStatus;
    reason: string;
    requestedBy: string;
  }): Promise<ApiResponse<MarkCorrection>> {
    await new Promise((r) => setTimeout(r, 80));

    const targetMark = this.marks.find((m) => m.id === data.markId);
    if (!targetMark) {
      throw new Error(`Mark record '${data.markId}' not found.`);
    }

    const asm = this.assessments.find((a) => a.id === targetMark.assessmentId);

    const newCorr: MarkCorrection = {
      id: `corr-${Date.now()}`,
      markId: targetMark.id,
      assessmentId: targetMark.assessmentId,
      assessmentName: asm?.name || "Semester Assessment",
      studentId: targetMark.studentId,
      studentName: targetMark.studentName,
      rollNumber: targetMark.rollNumber,
      courseCode: asm?.courseCode || "CS301",
      courseName: asm?.courseName || "Data Structures",
      originalMark: targetMark.marksObtained,
      requestedMark: data.requestedMark,
      originalStatus: targetMark.status,
      requestedStatus: data.requestedStatus,
      reason: data.reason,
      requestedBy: data.requestedBy,
      requestedDate: new Date().toLocaleString(),
      status: "PENDING",
      timeline: [
        {
          timestamp: new Date().toLocaleString(),
          action: "CORRECTION_REQUESTED",
          actor: data.requestedBy,
          notes: data.reason,
        },
      ],
    };

    this.corrections.unshift(newCorr);
    return { success: true, data: newCorr };
  }

  async reviewMarkCorrection(
    correctionId: string,
    action: "APPROVED" | "REJECTED",
    reviewerNotes: string
  ): Promise<ApiResponse<MarkCorrection>> {
    await new Promise((r) => setTimeout(r, 80));

    const corr = this.corrections.find((c) => c.id === correctionId);
    if (!corr) {
      throw new Error(`Correction '${correctionId}' not found.`);
    }

    corr.status = action;
    corr.reviewedBy = "Dr. Anita Roy (HOD)";
    corr.reviewedDate = new Date().toLocaleString();
    corr.reviewerNotes = reviewerNotes;

    corr.timeline.push({
      timestamp: new Date().toLocaleString(),
      action: action === "APPROVED" ? "CORRECTION_APPROVED" : "CORRECTION_REJECTED",
      actor: "Dr. Anita Roy (HOD)",
      notes: reviewerNotes,
    });

    // If approved, update underlying mark record
    if (action === "APPROVED") {
      const targetMark = this.marks.find((m) => m.id === corr.markId);
      if (targetMark) {
        targetMark.marksObtained = corr.requestedMark;
        targetMark.status = corr.requestedStatus;
        targetMark.isAbsent = corr.requestedStatus === "ABSENT";
        targetMark.updatedAt = new Date().toISOString();

        corr.timeline.push({
          timestamp: new Date().toLocaleString(),
          action: "MARK_RECORD_UPDATED",
          actor: "CampusOS Engine",
          notes: `Synchronized score to ${corr.requestedMark}`,
        });
      }
    }

    return { success: true, data: corr };
  }

  // ==========================================
  // 8. Results & Calculations
  // ==========================================

  async getResults(filters?: ResultFilters | string): Promise<ApiResponse<Result[]>> {
    await new Promise((r) => setTimeout(r, 40));

    // Support legacy string program parameter
    if (typeof filters === "string") {
      return {
        success: true,
        data: this.results.filter((res) => res.program.toLowerCase().includes(filters.toLowerCase())),
      };
    }

    let items = [...this.results];
    if (filters?.examinationId && filters.examinationId !== "ALL") {
      items = items.filter((r) => r.examinationId === filters.examinationId);
    }
    if (filters?.courseOfferingId) {
      items = items.filter((r) => r.courseOfferingId === filters.courseOfferingId);
    }
    if (filters?.studentId) {
      items = items.filter((r) => r.studentId === filters.studentId);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((r) => r.department === filters.department);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((r) => r.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (r) =>
          r.studentName.toLowerCase().includes(q) ||
          r.rollNumber.toLowerCase().includes(q) ||
          r.courseCode.toLowerCase().includes(q)
      );
    }
    return { success: true, data: items };
  }

  async getResultById(id: string): Promise<ApiResponse<Result>> {
    await new Promise((r) => setTimeout(r, 30));
    const found = this.results.find((r) => r.id === id);
    if (!found) {
      throw new Error(`Result '${id}' not found`);
    }
    return { success: true, data: found };
  }

  async getStudentResults(studentId: string): Promise<ApiResponse<Result[]>> {
    await new Promise((r) => setTimeout(r, 40));
    // Filter to published results only for student view
    const items = this.results.filter((r) => r.studentId === studentId && r.isPublished);
    return { success: true, data: items };
  }

  async finalizeResult(id: string): Promise<ApiResponse<Result>> {
    await new Promise((r) => setTimeout(r, 60));
    const target = this.results.find((r) => r.id === id);
    if (!target) {
      throw new Error(`Result '${id}' not found`);
    }
    target.isFinalized = true;
    target.finalizedAt = new Date().toISOString();
    return { success: true, data: target };
  }

  async finalizeResults(examinationId: string): Promise<ApiResponse<{ finalizedCount: number }>> {
    await new Promise((r) => setTimeout(r, 100));

    const pendingResults = this.results.filter(
      (r) => r.examinationId === examinationId && !r.isFinalized
    );

    const now = new Date().toISOString();
    pendingResults.forEach((r) => {
      r.isFinalized = true;
      r.finalizedAt = now;
    });

    return { success: true, data: { finalizedCount: pendingResults.length } };
  }

  // ==========================================
  // 9. Result Publications
  // ==========================================

  async getPublications(filters?: { status?: string }): Promise<ApiResponse<ResultPublication[]>> {
    return this.getResultPublications(filters);
  }

  async getResultPublications(filters?: { status?: string }): Promise<ApiResponse<ResultPublication[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.publications];
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((p) => p.status === filters.status);
    }
    return { success: true, data: items };
  }

  async createPublication(data: Partial<ResultPublication>): Promise<ApiResponse<ResultPublication>> {
    await new Promise((r) => setTimeout(r, 80));

    const newPub: ResultPublication = {
      id: `pub-${Date.now()}`,
      batchNumber: `PUB-2026-S${data.semester || 5}-${Date.now().toString().slice(-4)}`,
      examinationId: data.examinationId || "exam-2026-ese",
      examinationName: data.examinationName || "End Semester Examinations Nov/Dec 2026",
      academicYear: data.academicYear || "2026-2027",
      semester: data.semester || 5,
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      publicationDate: data.publicationDate || new Date().toISOString().split("T")[0],
      status: "READY",
      resultCount: this.results.filter((r) => r.examinationId === data.examinationId).length || 68,
      notes: data.notes || "Ratified by Academic Standing Council.",
    };

    this.publications.unshift(newPub);
    return { success: true, data: newPub };
  }

  async publishResults(publicationId: string): Promise<ApiResponse<ResultPublication>> {
    await new Promise((r) => setTimeout(r, 100));
    const pub = this.publications.find((p) => p.id === publicationId);
    if (!pub) {
      throw new Error(`Publication batch '${publicationId}' not found.`);
    }

    pub.status = "PUBLISHED";
    pub.publishedBy = "Controller of Examinations";
    pub.publishedAt = new Date().toISOString();

    // Mark matching results as published so students can view them
    this.results
      .filter((r) => r.examinationId === pub.examinationId)
      .forEach((r) => {
        r.isPublished = true;
        r.publishedAt = pub.publishedAt;
      });

    return { success: true, data: pub };
  }

  async revokePublication(publicationId: string, notes?: string): Promise<ApiResponse<ResultPublication>> {
    await new Promise((r) => setTimeout(r, 80));
    const pub = this.publications.find((p) => p.id === publicationId);
    if (!pub) {
      throw new Error(`Publication batch '${publicationId}' not found.`);
    }

    pub.status = "REVOKED";
    pub.notes = notes ? `${pub.notes || ""} [REVOKED: ${notes}]` : pub.notes;

    // Unpublish results from student view
    this.results
      .filter((r) => r.examinationId === pub.examinationId)
      .forEach((r) => {
        r.isPublished = false;
      });

    return { success: true, data: pub };
  }

  // ==========================================
  // 10. Grade Scales
  // ==========================================

  async getGradeScales(): Promise<ApiResponse<GradeScale[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.gradeScales };
  }

  // ==========================================
  // 11. Reports Generator
  // ==========================================

  async generateReport(filter: ExamReportFilter): Promise<ApiResponse<{
    title: string;
    generatedAt: string;
    totalRecords: number;
    rows: Record<string, string | number>[];
  }>> {
    await new Promise((r) => setTimeout(r, 120));

    let title = "Examination Report";
    let rows: Record<string, string | number>[] = [];

    switch (filter.reportType) {
      case "COMPLETION":
        title = "Assessment Completion & Finalization Audit Report";
        rows = this.assessments.map((a) => ({
          Assessment: a.name,
          Course: `${a.courseCode} - ${a.courseName}`,
          Section: a.section,
          Faculty: a.facultyName,
          MaxMarks: a.maxMarks,
          Weightage: `${a.weightage}%`,
          Enrolled: a.totalEnrolled,
          MarksEntered: a.totalEntered,
          Status: a.status,
          Finalized: a.isFinalized ? "YES" : "NO",
        }));
        break;

      case "MARKS_ROSTER":
        title = "Class Marks Ledger Report";
        rows = this.marks.map((m) => ({
          RollNumber: m.rollNumber,
          StudentName: m.studentName,
          AssessmentId: m.assessmentId,
          MarksObtained: m.marksObtained !== null ? m.marksObtained : "N/A",
          MaxMarks: m.maxMarks,
          Status: m.status,
          Absent: m.isAbsent ? "YES" : "NO",
          Remarks: m.remarks || "",
        }));
        break;

      case "SCHEDULE":
        title = "Master Examination Timetable Schedule";
        rows = this.schedules.map((s) => ({
          Date: s.date,
          Time: `${s.startTime} - ${s.endTime}`,
          Course: `${s.courseCode} - ${s.courseName}`,
          Section: s.section,
          Room: s.room,
          Invigilator: s.facultyName,
          Candidates: s.totalCandidates,
          Status: s.status,
        }));
        break;

      case "ELIGIBILITY":
        title = "Examination Eligibility & Attendance Audit";
        rows = this.eligibilityRecords.map((e) => ({
          RollNumber: e.rollNumber,
          StudentName: e.studentName,
          Course: e.courseCode,
          AttendancePercentage: `${e.attendancePercentage}%`,
          Requirement: `${e.minimumRequirement}%`,
          Status: e.eligibilityStatus,
          Overridden: e.isOverridden ? "YES" : "NO",
          Reason: e.reason || e.overrideReason || "Satisfies attendance threshold",
        }));
        break;

      case "RESULTS":
      default:
        title = "Semester Results Performance Summary";
        rows = this.results.map((r) => ({
          RollNumber: r.rollNumber,
          StudentName: r.studentName,
          Course: `${r.courseCode} - ${r.courseName}`,
          Credits: r.credits,
          TotalScore: r.totalMarks,
          Percentage: `${r.percentage}%`,
          Grade: r.grade,
          GradePoint: r.gradePoint,
          Status: r.status,
          Published: r.isPublished ? "YES" : "NO",
        }));
        break;
    }

    return {
      success: true,
      data: {
        title,
        generatedAt: new Date().toLocaleString(),
        totalRecords: rows.length,
        rows,
      },
    };
  }
}

export const examinationsService = new ExaminationsService();
