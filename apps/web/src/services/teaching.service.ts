import { ApiResponse } from "@campusos/types";
import {
  LessonPlanUnit,
  ClassDiaryEntry,
  CourseStudyMaterial,
  CourseAssignment,
  AssignmentSubmission,
  FacultyLeaveApplication,
  FacultyLeaveBalance,
} from "@/types/teaching";
import {
  MOCK_LESSON_PLANS,
  MOCK_CLASS_DIARY,
  MOCK_STUDY_MATERIALS,
  MOCK_ASSIGNMENTS,
  MOCK_SUBMISSIONS,
  MOCK_FACULTY_LEAVES,
  MOCK_FACULTY_LEAVE_BALANCES,
} from "@/mocks/teaching.mock";

const STORAGE_KEYS = {
  LESSON_PLANS: "campusos_lesson_plans_v1",
  CLASS_DIARY: "campusos_class_diary_v1",
  MATERIALS: "campusos_study_materials_v1",
  ASSIGNMENTS: "campusos_assignments_v1",
  SUBMISSIONS: "campusos_submissions_v1",
  FACULTY_LEAVES: "campusos_faculty_leaves_v1",
  FACULTY_BALANCES: "campusos_faculty_balances_v1",
};

function safeStorageGet<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function safeStorageSet<T>(key: string, data: T): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.warn("localStorage write error", e);
  }
}

class TeachingService {
  private lessonPlans: LessonPlanUnit[] = [];
  private classDiary: ClassDiaryEntry[] = [];
  private materials: CourseStudyMaterial[] = [];
  private assignments: CourseAssignment[] = [];
  private submissions: AssignmentSubmission[] = [];
  private facultyLeaves: FacultyLeaveApplication[] = [];
  private facultyBalances: FacultyLeaveBalance[] = [];

  constructor() {
    this.init();
  }

  private init() {
    this.lessonPlans = safeStorageGet(STORAGE_KEYS.LESSON_PLANS, [
      ...MOCK_LESSON_PLANS,
    ]);
    this.classDiary = safeStorageGet(STORAGE_KEYS.CLASS_DIARY, [
      ...MOCK_CLASS_DIARY,
    ]);
    this.materials = safeStorageGet(STORAGE_KEYS.MATERIALS, [
      ...MOCK_STUDY_MATERIALS,
    ]);
    this.assignments = safeStorageGet(STORAGE_KEYS.ASSIGNMENTS, [
      ...MOCK_ASSIGNMENTS,
    ]);
    this.submissions = safeStorageGet(STORAGE_KEYS.SUBMISSIONS, [
      ...MOCK_SUBMISSIONS,
    ]);
    this.facultyLeaves = safeStorageGet(STORAGE_KEYS.FACULTY_LEAVES, [
      ...MOCK_FACULTY_LEAVES,
    ]);
    this.facultyBalances = safeStorageGet(STORAGE_KEYS.FACULTY_BALANCES, [
      ...MOCK_FACULTY_LEAVE_BALANCES,
    ]);
  }

  // =========================================================================
  // LESSON PLANS & SYLLABUS TRACKING
  // =========================================================================

  async getLessonPlans(
    courseOfferingId?: string,
  ): Promise<ApiResponse<LessonPlanUnit[]>> {
    let items = [...this.lessonPlans];
    if (courseOfferingId && courseOfferingId !== "ALL") {
      items = items.filter((p) => p.courseOfferingId === courseOfferingId);
    }
    return { success: true, data: items };
  }

  async createLessonPlan(
    plan: Omit<LessonPlanUnit, "id" | "lastUpdated">,
  ): Promise<ApiResponse<LessonPlanUnit>> {
    const newPlan: LessonPlanUnit = {
      ...plan,
      id: `lp-${Date.now()}`,
      lastUpdated: new Date().toISOString(),
      completionPercentage:
        plan.plannedHours > 0
          ? Math.min(
              100,
              Math.round((plan.completedHours / plan.plannedHours) * 100),
            )
          : 0,
      status:
        plan.completedHours >= plan.plannedHours
          ? "COMPLETED"
          : plan.completedHours > 0
            ? "IN_PROGRESS"
            : "NOT_STARTED",
    };
    this.lessonPlans.push(newPlan);
    safeStorageSet(STORAGE_KEYS.LESSON_PLANS, this.lessonPlans);
    return { success: true, data: newPlan };
  }

  async updateLessonPlanHours(
    id: string,
    completedHours: number,
  ): Promise<ApiResponse<LessonPlanUnit>> {
    const idx = this.lessonPlans.findIndex((p) => p.id === id);
    if (idx === -1) throw new Error("Lesson plan not found");

    const plan = this.lessonPlans[idx];
    const newHours = Math.max(0, Math.min(plan.plannedHours, completedHours));
    const pct = Math.round((newHours / plan.plannedHours) * 100);
    const status =
      newHours >= plan.plannedHours
        ? "COMPLETED"
        : newHours > 0
          ? "IN_PROGRESS"
          : "NOT_STARTED";

    this.lessonPlans[idx] = {
      ...plan,
      completedHours: newHours,
      completionPercentage: pct,
      status,
      lastUpdated: new Date().toISOString(),
    };
    safeStorageSet(STORAGE_KEYS.LESSON_PLANS, this.lessonPlans);
    return { success: true, data: this.lessonPlans[idx] };
  }

  // =========================================================================
  // CLASS DIARY / TEACHING LOG
  // =========================================================================

  async getClassDiaryEntries(
    courseOfferingId?: string,
  ): Promise<ApiResponse<ClassDiaryEntry[]>> {
    let items = [...this.classDiary];
    if (courseOfferingId && courseOfferingId !== "ALL") {
      items = items.filter((e) => e.courseOfferingId === courseOfferingId);
    }
    // Sort descending by date
    items.sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    );
    return { success: true, data: items };
  }

  async logClassDiaryEntry(
    entry: Omit<ClassDiaryEntry, "id" | "createdAt">,
  ): Promise<ApiResponse<ClassDiaryEntry>> {
    const newEntry: ClassDiaryEntry = {
      ...entry,
      id: `cd-${Date.now()}`,
      createdAt: new Date().toISOString(),
      attendancePercentage:
        entry.totalStudents > 0
          ? Math.round((entry.studentsPresent / entry.totalStudents) * 1000) /
            10
          : 100,
    };
    this.classDiary.unshift(newEntry);
    safeStorageSet(STORAGE_KEYS.CLASS_DIARY, this.classDiary);

    // Automatically update corresponding lesson plan unit if exists
    const plan = this.lessonPlans.find(
      (p) =>
        p.courseOfferingId === entry.courseOfferingId &&
        p.unitNumber === entry.unitNumber,
    );
    if (plan && plan.completedHours < plan.plannedHours) {
      await this.updateLessonPlanHours(plan.id, plan.completedHours + 1);
    }

    return { success: true, data: newEntry };
  }

  // =========================================================================
  // STUDY MATERIALS REPOSITORY
  // =========================================================================

  async getStudyMaterials(params?: {
    courseOfferingId?: string;
    unitNumber?: number;
    materialType?: string;
  }): Promise<ApiResponse<CourseStudyMaterial[]>> {
    let items = [...this.materials];
    if (params?.courseOfferingId && params.courseOfferingId !== "ALL") {
      items = items.filter(
        (m) => m.courseOfferingId === params.courseOfferingId,
      );
    }
    if (params?.unitNumber && params.unitNumber > 0) {
      items = items.filter((m) => m.unitNumber === params.unitNumber);
    }
    if (params?.materialType && params.materialType !== "ALL") {
      items = items.filter((m) => m.materialType === params.materialType);
    }
    return { success: true, data: items };
  }

  async uploadStudyMaterial(
    material: Omit<CourseStudyMaterial, "id" | "uploadedAt" | "downloadCount">,
  ): Promise<ApiResponse<CourseStudyMaterial>> {
    const newMaterial: CourseStudyMaterial = {
      ...material,
      id: `mat-${Date.now()}`,
      uploadedAt: new Date().toISOString(),
      downloadCount: 0,
    };
    this.materials.unshift(newMaterial);
    safeStorageSet(STORAGE_KEYS.MATERIALS, this.materials);
    return { success: true, data: newMaterial };
  }

  async incrementMaterialDownload(id: string): Promise<ApiResponse<number>> {
    const item = this.materials.find((m) => m.id === id);
    if (item) {
      item.downloadCount += 1;
      safeStorageSet(STORAGE_KEYS.MATERIALS, this.materials);
      return { success: true, data: item.downloadCount };
    }
    return { success: true, data: 0 };
  }

  // =========================================================================
  // ASSIGNMENTS & EVALUATIONS
  // =========================================================================

  async getAssignments(params?: {
    courseOfferingId?: string;
    status?: string;
  }): Promise<ApiResponse<CourseAssignment[]>> {
    let items = [...this.assignments];
    if (params?.courseOfferingId && params.courseOfferingId !== "ALL") {
      items = items.filter(
        (a) => a.courseOfferingId === params.courseOfferingId,
      );
    }
    if (params?.status && params.status !== "ALL") {
      items = items.filter((a) => a.status === params.status);
    }
    return { success: true, data: items };
  }

  async createAssignment(
    assignment: Omit<
      CourseAssignment,
      "id" | "totalSubmissions" | "evaluatedCount" | "averageScore"
    >,
  ): Promise<ApiResponse<CourseAssignment>> {
    const newAsg: CourseAssignment = {
      ...assignment,
      id: `asg-${Date.now()}`,
      totalSubmissions: 0,
      evaluatedCount: 0,
    };
    this.assignments.unshift(newAsg);
    safeStorageSet(STORAGE_KEYS.ASSIGNMENTS, this.assignments);
    return { success: true, data: newAsg };
  }

  async getSubmissions(
    assignmentId?: string,
    studentId?: string,
  ): Promise<ApiResponse<AssignmentSubmission[]>> {
    let items = [...this.submissions];
    if (assignmentId && assignmentId !== "ALL") {
      items = items.filter((s) => s.assignmentId === assignmentId);
    }
    if (studentId) {
      items = items.filter((s) => s.studentId === studentId);
    }
    return { success: true, data: items };
  }

  async submitAssignment(
    submission: Omit<
      AssignmentSubmission,
      "id" | "submittedAt" | "status" | "isLate"
    >,
  ): Promise<ApiResponse<AssignmentSubmission>> {
    const targetAssignment = this.assignments.find(
      (a) => a.id === submission.assignmentId,
    );
    const now = new Date();
    const isLate = targetAssignment
      ? now > new Date(targetAssignment.dueDate)
      : false;

    // Check if late submissions are prohibited
    if (isLate && targetAssignment && !targetAssignment.allowLateSubmission) {
      throw new Error(
        "Deadline has passed and late submissions are strictly not permitted.",
      );
    }

    const newSub: AssignmentSubmission = {
      ...submission,
      id: `sub-${Date.now()}`,
      submittedAt: now.toISOString(),
      isLate,
      status: "SUBMITTED",
    };

    // Remove old submission from same student if re-submitting
    this.submissions = this.submissions.filter(
      (s) =>
        !(
          s.assignmentId === submission.assignmentId &&
          s.studentId === submission.studentId
        ),
    );
    this.submissions.push(newSub);
    safeStorageSet(STORAGE_KEYS.SUBMISSIONS, this.submissions);

    // Update assignment counter
    if (targetAssignment) {
      targetAssignment.totalSubmissions = this.submissions.filter(
        (s) => s.assignmentId === submission.assignmentId,
      ).length;
      safeStorageSet(STORAGE_KEYS.ASSIGNMENTS, this.assignments);
    }

    return { success: true, data: newSub };
  }

  async evaluateSubmission(
    submissionId: string,
    evalData: {
      marksObtained: number;
      feedback: string;
      facultyId: string;
      facultyName: string;
    },
  ): Promise<ApiResponse<AssignmentSubmission>> {
    const idx = this.submissions.findIndex((s) => s.id === submissionId);
    if (idx === -1) throw new Error("Submission not found");

    const targetSub = this.submissions[idx];
    if (
      evalData.marksObtained < 0 ||
      evalData.marksObtained > targetSub.maxMarks
    ) {
      throw new Error(
        `Marks must be between 0 and maximum ${targetSub.maxMarks}.`,
      );
    }

    this.submissions[idx] = {
      ...targetSub,
      marksObtained: evalData.marksObtained,
      feedback: evalData.feedback,
      evaluatedByFacultyId: evalData.facultyId,
      evaluatedByFacultyName: evalData.facultyName,
      evaluatedAt: new Date().toISOString(),
      status: "EVALUATED",
    };
    safeStorageSet(STORAGE_KEYS.SUBMISSIONS, this.submissions);

    // Update assignment evaluated count and average
    const targetAsg = this.assignments.find(
      (a) => a.id === targetSub.assignmentId,
    );
    if (targetAsg) {
      const allEvaluated = this.submissions.filter(
        (s) =>
          s.assignmentId === targetSub.assignmentId &&
          s.status === "EVALUATED" &&
          s.marksObtained !== undefined,
      );
      targetAsg.evaluatedCount = allEvaluated.length;
      if (allEvaluated.length > 0) {
        const sum = allEvaluated.reduce(
          (acc, curr) => acc + (curr.marksObtained || 0),
          0,
        );
        targetAsg.averageScore =
          Math.round((sum / allEvaluated.length) * 10) / 10;
      }
      safeStorageSet(STORAGE_KEYS.ASSIGNMENTS, this.assignments);
    }

    return { success: true, data: this.submissions[idx] };
  }

  // =========================================================================
  // FACULTY LEAVE WORKFLOW
  // =========================================================================

  async getFacultyLeaveBalances(
    facultyId?: string,
  ): Promise<ApiResponse<FacultyLeaveBalance[]>> {
    return { success: true, data: [...this.facultyBalances] };
  }

  async getFacultyLeaves(
    facultyId?: string,
  ): Promise<ApiResponse<FacultyLeaveApplication[]>> {
    let items = [...this.facultyLeaves];
    if (facultyId) {
      items = items.filter((l) => l.facultyId === facultyId);
    }
    return { success: true, data: items };
  }

  async applyFacultyLeave(
    app: Omit<FacultyLeaveApplication, "id" | "status" | "appliedAt">,
  ): Promise<ApiResponse<FacultyLeaveApplication>> {
    // Check balance
    const bal = this.facultyBalances.find((b) => b.leaveType === app.leaveType);
    if (bal && bal.availableDays < app.totalDays) {
      throw new Error(
        `Insufficient leave balance. Available: ${bal.availableDays} days, Requested: ${app.totalDays} days.`,
      );
    }

    const newApp: FacultyLeaveApplication = {
      ...app,
      id: `fleave-${Date.now()}`,
      status: "PENDING_HOD",
      appliedAt: new Date().toISOString(),
    };
    this.facultyLeaves.unshift(newApp);
    safeStorageSet(STORAGE_KEYS.FACULTY_LEAVES, this.facultyLeaves);

    return { success: true, data: newApp };
  }

  async processFacultyLeaveHOD(
    leaveId: string,
    action: "APPROVE" | "REJECT",
    remarks: string,
  ): Promise<ApiResponse<FacultyLeaveApplication>> {
    const idx = this.facultyLeaves.findIndex((l) => l.id === leaveId);
    if (idx === -1) throw new Error("Leave request not found");

    const app = this.facultyLeaves[idx];
    const newStatus = action === "APPROVE" ? "APPROVED" : "REJECTED";

    this.facultyLeaves[idx] = {
      ...app,
      status: newStatus,
      hodRemarks: remarks,
    };

    if (action === "APPROVE") {
      const bal = this.facultyBalances.find(
        (b) => b.leaveType === app.leaveType,
      );
      if (bal) {
        bal.consumedDays += app.totalDays;
        bal.availableDays = Math.max(0, bal.allocatedDays - bal.consumedDays);
        safeStorageSet(STORAGE_KEYS.FACULTY_BALANCES, this.facultyBalances);
      }
    }

    safeStorageSet(STORAGE_KEYS.FACULTY_LEAVES, this.facultyLeaves);
    return { success: true, data: this.facultyLeaves[idx] };
  }
}

export const teachingService = new TeachingService();
