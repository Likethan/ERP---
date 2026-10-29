import { ApiResponse } from "@campusos/types";
import {
  AttendancePolicy,
  AttendanceSession,
  AttendanceRecord,
  AttendanceStatus,
  AttendanceStudentSummary,
  AttendanceCourseSummary,
  AttendanceLeave,
  AttendanceLeaveStatus,
  AttendanceCorrection,
  AttendanceCorrectionStatus,
  AttendanceSummary,
  LowAttendanceAlertItem,
  AttendanceReportFilter,
} from "@/types/attendance";
import {
  StudentAttendanceSheetEntry,
  MOCK_ATTENDANCE_POLICIES,
  MOCK_CANONICAL_SESSIONS,
  MOCK_ATTENDANCE_RECORDS,
  MOCK_ATTENDANCE_STUDENT_SUMMARIES,
  MOCK_ATTENDANCE_COURSE_SUMMARIES,
  MOCK_LOW_ATTENDANCE_ALERTS,
  MOCK_ATTENDANCE_LEAVES,
  MOCK_ATTENDANCE_CORRECTIONS_DETAIL,
  MOCK_ATTENDANCE_OPERATIONS_SUMMARY,
} from "@/mocks/attendance.mock";
import { MOCK_STUDENTS } from "@/mocks/students.mock";
import { calculateAttendancePercentage } from "./attendance-calculator";

export interface SessionFilters {
  date?: string;
  department?: string;
  program?: string;
  semester?: number;
  section?: string;
  facultyId?: string;
  subject?: string;
  status?: string;
  search?: string;
}

export interface RecordFilters {
  sessionId?: string;
  studentId?: string;
  courseCode?: string;
  section?: string;
  status?: string;
  date?: string;
  search?: string;
}

export interface StudentAttendanceFilters {
  department?: string;
  semester?: number;
  section?: string;
  riskLevel?: string;
  search?: string;
}

export interface CourseAttendanceFilters {
  department?: string;
  semester?: number;
  section?: string;
  riskLevel?: string;
  search?: string;
}

class AttendanceService {
  private policies: AttendancePolicy[] = [...MOCK_ATTENDANCE_POLICIES];
  private sessions: AttendanceSession[] = [...MOCK_CANONICAL_SESSIONS];
  private records: AttendanceRecord[] = [...MOCK_ATTENDANCE_RECORDS];
  private studentSummaries: AttendanceStudentSummary[] = [
    ...MOCK_ATTENDANCE_STUDENT_SUMMARIES,
  ];
  private courseSummaries: AttendanceCourseSummary[] = [
    ...MOCK_ATTENDANCE_COURSE_SUMMARIES,
  ];
  private leaves: AttendanceLeave[] = [...MOCK_ATTENDANCE_LEAVES];
  private corrections: AttendanceCorrection[] = [
    ...MOCK_ATTENDANCE_CORRECTIONS_DETAIL,
  ];
  private operationsSummary: AttendanceSummary = {
    ...MOCK_ATTENDANCE_OPERATIONS_SUMMARY,
  };

  // ==========================================
  // 1. OPERATIONS DASHBOARD & SUMMARY
  // ==========================================

  async getDashboardSummary(): Promise<ApiResponse<AttendanceSummary>> {
    await new Promise((r) => setTimeout(r, 40));
    // Dynamically calculate pending items
    const pendingLeaves = this.leaves.filter(
      (l) => l.status === "PENDING",
    ).length;
    const pendingCorrections = this.corrections.filter(
      (c) => c.status === "PENDING",
    ).length;
    const today = "2026-10-02";
    const todaySessions = this.sessions.filter((s) => s.date === today);
    const todayCompleted = todaySessions.filter(
      (s) => s.status === "COMPLETED",
    ).length;
    const todayPending = todaySessions.filter(
      (s) => s.status !== "COMPLETED" && s.status !== "CANCELLED",
    ).length;

    return {
      success: true,
      data: {
        ...this.operationsSummary,
        todaySessionsCount: todaySessions.length || 6,
        todaySessionsCompleted: todayCompleted || 4,
        todaySessionsPending: todayPending || 2,
        pendingLeaveRequestsCount: pendingLeaves,
        pendingCorrectionsCount: pendingCorrections,
      },
    };
  }

  // Legacy getDashboard() method
  async getDashboard(): Promise<
    ApiResponse<{
      todaySessionsCount: number;
      sessionsMarkedToday: number;
      overallAttendancePercentage: number;
      studentsBelowThresholdCount: number;
      pendingLeaveRequestsCount: number;
      pendingCorrectionsCount: number;
    }>
  > {
    const res = await this.getDashboardSummary();
    return {
      success: true,
      data: {
        todaySessionsCount: res.data.todaySessionsCount,
        sessionsMarkedToday: res.data.todaySessionsCompleted,
        overallAttendancePercentage: res.data.overallAttendancePercentage,
        studentsBelowThresholdCount: res.data.studentsBelowThresholdCount,
        pendingLeaveRequestsCount: res.data.pendingLeaveRequestsCount,
        pendingCorrectionsCount: res.data.pendingCorrectionsCount,
      },
    };
  }

  // ==========================================
  // 2. ATTENDANCE POLICIES
  // ==========================================

  async getPolicies(): Promise<ApiResponse<AttendancePolicy[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...this.policies] };
  }

  async getPolicyById(id: string): Promise<ApiResponse<AttendancePolicy>> {
    await new Promise((r) => setTimeout(r, 30));
    const policy = this.policies.find((p) => p.id === id);
    if (!policy) throw new Error("Policy not found");
    return { success: true, data: policy };
  }

  async updatePolicy(
    id: string,
    updates: Partial<AttendancePolicy>,
  ): Promise<ApiResponse<AttendancePolicy>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.policies.findIndex((p) => p.id === id);
    if (idx === -1) throw new Error("Policy not found");
    this.policies[idx] = { ...this.policies[idx], ...updates };
    return { success: true, data: this.policies[idx] };
  }

  async createPolicy(
    policyData: Omit<AttendancePolicy, "id">,
  ): Promise<ApiResponse<AttendancePolicy>> {
    await new Promise((r) => setTimeout(r, 70));
    const newPolicy: AttendancePolicy = {
      ...policyData,
      id: `pol-${Date.now()}`,
    };
    this.policies.push(newPolicy);
    return { success: true, data: newPolicy };
  }

  // ==========================================
  // 3. ATTENDANCE SESSIONS
  // ==========================================

  async getSessions(
    filters?: SessionFilters,
  ): Promise<ApiResponse<AttendanceSession[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.sessions];

    if (filters?.date && filters.date !== "ALL") {
      items = items.filter((s) => s.date === filters.date);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((s) =>
        s.department.toLowerCase().includes(filters.department!.toLowerCase()),
      );
    }
    if (filters?.section && filters.section !== "ALL") {
      items = items.filter((s) =>
        s.section.toLowerCase().includes(filters.section!.toLowerCase()),
      );
    }
    if (filters?.facultyId && filters.facultyId !== "ALL") {
      items = items.filter(
        (s) =>
          s.facultyId === filters.facultyId ||
          s.facultyName
            .toLowerCase()
            .includes(filters.facultyId!.toLowerCase()),
      );
    }
    if (filters?.subject && filters.subject !== "ALL") {
      items = items.filter(
        (s) =>
          s.courseCode === filters.subject ||
          s.courseName.toLowerCase().includes(filters.subject!.toLowerCase()),
      );
    }
    if (filters?.status && (filters.status as string) !== "ALL") {
      items = items.filter((s) => s.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (s) =>
          s.courseCode.toLowerCase().includes(q) ||
          s.courseName.toLowerCase().includes(q) ||
          s.section.toLowerCase().includes(q) ||
          s.facultyName.toLowerCase().includes(q) ||
          s.room.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getSessionById(
    id: string,
  ): Promise<ApiResponse<AttendanceSession | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const session = this.sessions.find((s) => s.id === id) || null;
    return { success: true, data: session };
  }

  async createSession(
    data: Partial<AttendanceSession>,
  ): Promise<ApiResponse<AttendanceSession>> {
    await new Promise((r) => setTimeout(r, 80));
    const newSession: AttendanceSession = {
      id: `att-sess-${Date.now()}`,
      courseOfferingId: data.courseOfferingId || "off-cs301-a",
      courseCode: data.courseCode || "CS301",
      courseName: data.courseName || "Data Structures & Algorithms",
      section: data.section || "5th Sem CSE — Sec A",
      department: data.department || "Computer Science & Engineering",
      facultyId: data.facultyId || "fac-cse-001",
      facultyName: data.facultyName || "Dr. Rajesh Sharma",
      date: data.date || new Date().toISOString().split("T")[0],
      startTime: data.startTime || "09:30 AM",
      endTime: data.endTime || "10:30 AM",
      room: data.room || "Hall 302, Academic Block A",
      sessionType: data.sessionType || "THEORY",
      status: data.status || "SCHEDULED",
      totalStudents: data.totalStudents || 68,
      presentCount: 0,
      absentCount: 0,
      lateCount: 0,
      excusedCount: 0,
      attendancePercentage: 0,
      topicCovered: data.topicCovered || "",
      remarks: data.remarks || "",
      createdAt: new Date().toISOString(),
    };
    this.sessions.unshift(newSession);
    return { success: true, data: newSession };
  }

  async updateSession(
    id: string,
    updates: Partial<AttendanceSession>,
  ): Promise<ApiResponse<AttendanceSession>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.sessions.findIndex((s) => s.id === id);
    if (idx === -1) throw new Error("Session not found");
    this.sessions[idx] = { ...this.sessions[idx], ...updates };
    return { success: true, data: this.sessions[idx] };
  }

  // ==========================================
  // 4. ATTENDANCE RECORDING & ROSTER
  // ==========================================

  async getSessionRoster(
    sessionId: string,
  ): Promise<ApiResponse<AttendanceRecord[]>> {
    await new Promise((r) => setTimeout(r, 50));
    const existing = this.records.filter((r) => r.sessionId === sessionId);
    if (existing.length > 0) {
      return { success: true, data: existing };
    }

    // Auto-synthesize roster from canonical students if not recorded yet
    const session = this.sessions.find((s) => s.id === sessionId);
    const pool = MOCK_STUDENTS.slice(0, 10); // Active cohort
    const roster: AttendanceRecord[] = pool.map((stu, idx) => ({
      id: `rec-${sessionId}-${stu.id}`,
      sessionId,
      studentId: stu.id,
      studentName: `${stu.firstName} ${stu.lastName}`,
      rollNumber: stu.rollNumber,
      courseOfferingId: session?.courseOfferingId || "off-cs301-a",
      courseCode: session?.courseCode || "CS301",
      courseName: session?.courseName || "Data Structures & Algorithms",
      section: session?.section || "5th Sem CSE — Sec A",
      status: idx === 2 ? "ABSENT" : idx === 4 ? "LATE" : "PRESENT",
      remarks: idx === 2 ? "Medical notice submitted" : undefined,
      markedAt: new Date().toISOString(),
      markedBy: session?.facultyName || "Faculty Instructor",
    }));

    return { success: true, data: roster };
  }

  async submitSessionAttendance(
    sessionId: string,
    records: {
      studentId: string;
      status: AttendanceStatus;
      remarks?: string;
    }[],
  ): Promise<ApiResponse<{ updatedCount: number }>> {
    await new Promise((r) => setTimeout(r, 100));
    const session = this.sessions.find((s) => s.id === sessionId);
    if (!session) throw new Error("Session not found");

    const presentCount = records.filter((r) => r.status === "PRESENT").length;
    const absentCount = records.filter((r) => r.status === "ABSENT").length;
    const lateCount = records.filter((r) => r.status === "LATE").length;
    const excusedCount = records.filter((r) => r.status === "EXCUSED").length;

    const percentage = calculateAttendancePercentage({
      present: presentCount,
      absent: absentCount,
      late: lateCount,
      excused: excusedCount,
      total: records.length,
    });

    session.presentCount = presentCount;
    session.absentCount = absentCount;
    session.lateCount = lateCount;
    session.excusedCount = excusedCount;
    session.totalStudents = records.length;
    session.attendancePercentage = percentage;
    session.status = "COMPLETED";
    session.submittedAt = new Date().toISOString();

    // Persist or replace records
    this.records = this.records.filter((r) => r.sessionId !== sessionId);
    records.forEach((rec) => {
      const student = MOCK_STUDENTS.find((s) => s.id === rec.studentId);
      this.records.push({
        id: `rec-${sessionId}-${rec.studentId}`,
        sessionId,
        studentId: rec.studentId,
        studentName: student
          ? `${student.firstName} ${student.lastName}`
          : "Student",
        rollNumber: student?.rollNumber || "24CSE0000",
        courseOfferingId: session.courseOfferingId,
        courseCode: session.courseCode,
        courseName: session.courseName,
        section: session.section,
        status: rec.status,
        remarks: rec.remarks,
        markedAt: new Date().toISOString(),
        markedBy: session.facultyName,
      });
    });

    return { success: true, data: { updatedCount: records.length } };
  }

  // Legacy submitAttendance() alias
  async submitAttendance(
    sessionId: string,
    records: StudentAttendanceSheetEntry[],
  ): Promise<ApiResponse<{ updatedCount: number }>> {
    return this.submitSessionAttendance(
      sessionId,
      records.map((r) => ({
        studentId: r.studentId,
        status: (r.status === "ON_LEAVE" || r.status === "ON_DUTY"
          ? "EXCUSED"
          : r.status) as AttendanceStatus,
        remarks: r.remarks,
      })),
    );
  }

  // ==========================================
  // 5. ATTENDANCE RECORDS DIRECTORY
  // ==========================================

  async getRecords(
    filters?: RecordFilters,
  ): Promise<ApiResponse<AttendanceRecord[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.records];

    if (filters?.sessionId && filters.sessionId !== "ALL") {
      items = items.filter((r) => r.sessionId === filters.sessionId);
    }
    if (filters?.studentId && filters.studentId !== "ALL") {
      items = items.filter(
        (r) =>
          r.studentId === filters.studentId ||
          r.rollNumber === filters.studentId,
      );
    }
    if (filters?.courseCode && filters.courseCode !== "ALL") {
      items = items.filter((r) => r.courseCode === filters.courseCode);
    }
    if (filters?.section && filters.section !== "ALL") {
      items = items.filter((r) =>
        r.section.toLowerCase().includes(filters.section!.toLowerCase()),
      );
    }
    if (filters?.status && (filters.status as string) !== "ALL") {
      items = items.filter((r) => r.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (r) =>
          r.studentName.toLowerCase().includes(q) ||
          r.rollNumber.toLowerCase().includes(q) ||
          r.courseCode.toLowerCase().includes(q) ||
          r.courseName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  // ==========================================
  // 6. STUDENT ATTENDANCE 360 & SUMMARIES
  // ==========================================

  async getStudentAttendanceSummary(
    studentId: string,
  ): Promise<ApiResponse<AttendanceStudentSummary>> {
    await new Promise((r) => setTimeout(r, 50));
    const found = this.studentSummaries.find(
      (s) =>
        s.studentId === studentId ||
        s.rollNumber.toLowerCase() === studentId.toLowerCase(),
    );
    if (found) {
      return { success: true, data: found };
    }

    // Fallback: Build synthetic summary for any student from MOCK_STUDENTS
    const student = MOCK_STUDENTS.find(
      (s) =>
        s.id === studentId ||
        s.rollNumber.toLowerCase() === studentId.toLowerCase(),
    );
    if (!student) throw new Error("Student not found");

    const fallback: AttendanceStudentSummary = {
      studentId: student.id,
      studentName: `${student.firstName} ${student.lastName}`,
      rollNumber: student.rollNumber,
      program: student.program.name,
      department: student.program.department,
      semester: student.currentSemester,
      section: student.section,
      totalSessions: 180,
      attendedSessions: 155,
      presentCount: 152,
      absentCount: 22,
      lateCount: 6,
      excusedCount: 0,
      percentage: 86.1,
      riskLevel: "HEALTHY",
      courseSummaries: [
        {
          courseOfferingId: "off-cs301-a",
          courseCode: "CS301",
          courseName: "Data Structures & Algorithms",
          section: student.section,
          facultyName: "Dr. Rajesh Sharma",
          totalSessions: 42,
          presentCount: 37,
          absentCount: 4,
          lateCount: 1,
          excusedCount: 0,
          percentage: 89.2,
          riskLevel: "HEALTHY",
        },
        {
          courseOfferingId: "off-cs302-a",
          courseCode: "CS302",
          courseName: "Database Management Systems",
          section: student.section,
          facultyName: "Dr. K. S. Anand",
          totalSessions: 40,
          presentCount: 35,
          absentCount: 4,
          lateCount: 1,
          excusedCount: 0,
          percentage: 88.7,
          riskLevel: "HEALTHY",
        },
      ],
      trend: [
        { period: "Week 1", percentage: 90.0, present: 18, total: 20 },
        { period: "Week 2", percentage: 85.0, present: 17, total: 20 },
        { period: "Week 3", percentage: 88.0, present: 22, total: 25 },
        { period: "Week 4", percentage: 86.0, present: 20, total: 23 },
      ],
    };

    return { success: true, data: fallback };
  }

  async listStudentSummaries(
    filters?: StudentAttendanceFilters,
  ): Promise<ApiResponse<AttendanceStudentSummary[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.studentSummaries];

    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((s) =>
        s.department.toLowerCase().includes(filters.department!.toLowerCase()),
      );
    }
    if (
      filters?.semester &&
      (filters.semester as unknown as string) !== "ALL"
    ) {
      items = items.filter((s) => s.semester === Number(filters.semester));
    }
    if (filters?.section && filters.section !== "ALL") {
      items = items.filter(
        (s) => s.section.toLowerCase() === filters.section!.toLowerCase(),
      );
    }
    if (filters?.riskLevel && (filters.riskLevel as string) !== "ALL") {
      items = items.filter((s) => s.riskLevel === filters.riskLevel);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (s) =>
          s.studentName.toLowerCase().includes(q) ||
          s.rollNumber.toLowerCase().includes(q) ||
          s.program.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  // ==========================================
  // 7. COURSE ATTENDANCE SUMMARIES
  // ==========================================

  async getCourseAttendanceSummary(
    courseOfferingId: string,
  ): Promise<ApiResponse<AttendanceCourseSummary>> {
    await new Promise((r) => setTimeout(r, 40));
    const found = this.courseSummaries.find(
      (c) =>
        c.courseOfferingId === courseOfferingId ||
        c.courseCode.toLowerCase() === courseOfferingId.toLowerCase(),
    );
    if (!found) {
      // Default placeholder course summary
      return {
        success: true,
        data: {
          courseOfferingId,
          courseCode: "CS301",
          courseName: "Data Structures & Algorithms",
          section: "A",
          facultyName: "Dr. Rajesh Sharma",
          totalSessions: 42,
          presentCount: 2590,
          absentCount: 210,
          lateCount: 56,
          excusedCount: 0,
          percentage: 91.2,
          riskLevel: "HEALTHY",
          studentsBelowThresholdCount: 2,
          studentsAtRiskCount: 4,
          averageAttendance: 91.2,
        },
      };
    }
    return { success: true, data: found };
  }

  async listCourseSummaries(
    filters?: CourseAttendanceFilters,
  ): Promise<ApiResponse<AttendanceCourseSummary[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.courseSummaries];

    if (filters?.riskLevel && (filters.riskLevel as string) !== "ALL") {
      items = items.filter((c) => c.riskLevel === filters.riskLevel);
    }
    if (filters?.section && filters.section !== "ALL") {
      items = items.filter(
        (c) => c.section.toLowerCase() === filters.section!.toLowerCase(),
      );
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (c) =>
          c.courseCode.toLowerCase().includes(q) ||
          c.courseName.toLowerCase().includes(q) ||
          c.facultyName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  // ==========================================
  // 8. LOW ATTENDANCE & RISK ALERTS
  // ==========================================

  async getLowAttendanceAlerts(): Promise<
    ApiResponse<LowAttendanceAlertItem[]>
  > {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...MOCK_LOW_ATTENDANCE_ALERTS] };
  }

  // ==========================================
  // 9. LEAVE WORKFLOW
  // ==========================================

  async getLeaves(filters?: {
    studentId?: string;
    status?: string;
    department?: string;
  }): Promise<ApiResponse<AttendanceLeave[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.leaves];

    if (filters?.studentId && filters.studentId !== "ALL") {
      items = items.filter(
        (l) =>
          l.studentId === filters.studentId ||
          l.rollNumber === filters.studentId,
      );
    }
    if (filters?.status && (filters.status as string) !== "ALL") {
      items = items.filter((l) => l.status === filters.status);
    }
    if (filters?.department && filters.department !== "ALL") {
      items = items.filter((l) =>
        l.department.toLowerCase().includes(filters.department!.toLowerCase()),
      );
    }

    return { success: true, data: items };
  }

  async getLeaveById(id: string): Promise<ApiResponse<AttendanceLeave>> {
    await new Promise((r) => setTimeout(r, 30));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) throw new Error("Leave request not found");
    return { success: true, data: leave };
  }

  async submitLeave(
    data: Partial<AttendanceLeave>,
  ): Promise<ApiResponse<AttendanceLeave>> {
    await new Promise((r) => setTimeout(r, 80));
    const newLeave: AttendanceLeave = {
      id: `leave-${Date.now()}`,
      studentId: data.studentId || "stu-24cse0101",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      department: data.department || "Computer Science & Engineering",
      program: data.program || "B.Tech Computer Science & Engineering",
      section: data.section || "A",
      leaveType: data.leaveType || "CASUAL",
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      endDate: data.endDate || new Date().toISOString().split("T")[0],
      totalDays: data.totalDays || 1,
      reason: data.reason || "Personal work",
      supportingDocName: data.supportingDocName,
      supportingDocUrl: data.supportingDocUrl,
      status: "PENDING",
      requestedAt: new Date().toISOString(),
    };
    this.leaves.unshift(newLeave);
    return { success: true, data: newLeave };
  }

  async updateLeaveStatus(
    id: string,
    status: AttendanceLeaveStatus,
    reviewerNotes?: string,
    reviewerName: string = "Dr. K. S. Anand (HOD - CSE)",
  ): Promise<ApiResponse<AttendanceLeave>> {
    await new Promise((r) => setTimeout(r, 70));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) throw new Error("Leave request not found");
    leave.status = status;
    leave.reviewedBy = reviewerName;
    leave.reviewedAt = new Date().toISOString();
    if (status === "REJECTED" && reviewerNotes) {
      leave.rejectionReason = reviewerNotes;
    }
    return { success: true, data: leave };
  }

  // ==========================================
  // 10. ATTENDANCE CORRECTIONS WORKFLOW
  // ==========================================

  async getCorrections(filters?: {
    status?: string;
    studentId?: string;
    courseCode?: string;
  }): Promise<ApiResponse<AttendanceCorrection[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.corrections];

    if (filters?.status && (filters.status as string) !== "ALL") {
      items = items.filter((c) => c.status === filters.status);
    }
    if (filters?.studentId && filters.studentId !== "ALL") {
      items = items.filter(
        (c) =>
          c.studentId === filters.studentId ||
          c.rollNumber === filters.studentId,
      );
    }
    if (filters?.courseCode && filters.courseCode !== "ALL") {
      items = items.filter((c) => c.courseCode === filters.courseCode);
    }

    return { success: true, data: items };
  }

  async submitCorrection(
    data: Partial<AttendanceCorrection>,
  ): Promise<ApiResponse<AttendanceCorrection>> {
    await new Promise((r) => setTimeout(r, 80));
    const newCorr: AttendanceCorrection = {
      id: `corr-${Date.now()}`,
      recordId: data.recordId || `rec-${Date.now()}`,
      sessionId: data.sessionId || "att-sess-01",
      studentId: data.studentId || "stu-24cse0101",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      courseCode: data.courseCode || "CS301",
      courseName: data.courseName || "Data Structures & Algorithms",
      sessionDate: data.sessionDate || new Date().toISOString().split("T")[0],
      originalStatus: data.originalStatus || "ABSENT",
      requestedStatus: data.requestedStatus || "PRESENT",
      reason:
        data.reason || "Student attended class; error in biometric punch.",
      requestedBy: data.requestedBy || "Dr. Rajesh Sharma",
      requestedRole: data.requestedRole || "FACULTY",
      requestedAt: new Date().toISOString(),
      status: "PENDING",
      auditTimeline: [
        {
          timestamp: new Date().toISOString(),
          action: `Correction requested from ${data.originalStatus || "ABSENT"} to ${data.requestedStatus || "PRESENT"}`,
          actor: data.requestedBy || "Faculty Instructor",
          details: data.reason,
        },
      ],
    };
    this.corrections.unshift(newCorr);
    return { success: true, data: newCorr };
  }

  async updateCorrectionStatus(
    id: string,
    status: AttendanceCorrectionStatus,
    reviewerNotes?: string,
    reviewerName: string = "Dr. K. S. Anand (HOD - CSE)",
  ): Promise<ApiResponse<AttendanceCorrection>> {
    await new Promise((r) => setTimeout(r, 80));
    const corr = this.corrections.find((c) => c.id === id);
    if (!corr) throw new Error("Correction request not found");

    corr.status = status;
    corr.reviewedBy = reviewerName;
    corr.reviewedAt = new Date().toISOString();

    corr.auditTimeline.push({
      timestamp: new Date().toISOString(),
      action: `Correction ${status}`,
      actor: reviewerName,
      details: reviewerNotes || `Status updated to ${status}`,
    });

    // If APPROVED, update the corresponding record
    if (status === "APPROVED") {
      const record = this.records.find((r) => r.id === corr.recordId);
      if (record) {
        record.status = corr.requestedStatus;
        record.remarks = `Corrected from ${corr.originalStatus} to ${corr.requestedStatus}: ${corr.reason}`;
      }
      corr.auditTimeline.push({
        timestamp: new Date().toISOString(),
        action: `Attendance record updated to ${corr.requestedStatus}`,
        actor: "System Engine",
      });
    }

    return { success: true, data: corr };
  }

  // ==========================================
  // 11. REPORTS GENERATION
  // ==========================================

  async generateReport(filter: AttendanceReportFilter): Promise<
    ApiResponse<{
      title: string;
      generatedAt: string;
      totalRows: number;
      rows: Record<string, unknown>[];
    }>
  > {
    await new Promise((r) => setTimeout(r, 70));

    if (filter.reportType === "LOW_ATTENDANCE") {
      const rows = MOCK_LOW_ATTENDANCE_ALERTS.map((a) => ({
        "Student Name": a.studentName,
        "Roll Number": a.rollNumber,
        Department: a.department,
        Semester: a.semester,
        Section: a.section,
        Course: `${a.courseCode} — ${a.courseName}`,
        "Attendance %": `${a.attendancePercentage}%`,
        "Required %": `${a.requiredPercentage}%`,
        "Sessions Needed": a.sessionsNeededToRecover,
        Risk: a.riskLevel,
      }));
      return {
        success: true,
        data: {
          title: "Low Attendance & Risk Alert Report",
          generatedAt: new Date().toISOString(),
          totalRows: rows.length,
          rows,
        },
      };
    }

    if (filter.reportType === "COURSE") {
      const rows = this.courseSummaries.map((c) => ({
        "Course Code": c.courseCode,
        "Course Title": c.courseName,
        Section: c.section,
        Faculty: c.facultyName,
        "Total Sessions": c.totalSessions,
        "Average Attendance": `${c.percentage}%`,
        "Students at Risk": c.studentsAtRiskCount || 0,
        Status: c.riskLevel,
      }));
      return {
        success: true,
        data: {
          title: "Course Attendance Summary Report",
          generatedAt: new Date().toISOString(),
          totalRows: rows.length,
          rows,
        },
      };
    }

    // Default student report
    const rows = this.studentSummaries.map((s) => ({
      "Student Name": s.studentName,
      "Roll Number": s.rollNumber,
      Department: s.department,
      Semester: s.semester,
      Section: s.section,
      "Total Sessions": s.totalSessions,
      Attended: s.attendedSessions,
      "Overall %": `${s.percentage}%`,
      "Risk Level": s.riskLevel,
    }));

    return {
      success: true,
      data: {
        title: "Student Cohort Attendance Report",
        generatedAt: new Date().toISOString(),
        totalRows: rows.length,
        rows,
      },
    };
  }
}

export const attendanceService = new AttendanceService();
