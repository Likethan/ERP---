import { ApiResponse, PaginatedResponse } from "@campusos/types";
import {
  AttendanceSessionItem,
  StudentAttendanceSheetEntry,
  StudentLeaveRequestItem,
  AttendanceCorrectionItem,
  MOCK_ATTENDANCE_SESSIONS,
  MOCK_LEAVE_REQUESTS,
  MOCK_ATTENDANCE_CORRECTIONS,
} from "@/mocks/attendance.mock";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

class AttendanceService {
  private sessions: AttendanceSessionItem[] = [...MOCK_ATTENDANCE_SESSIONS];
  private leaves: StudentLeaveRequestItem[] = [...MOCK_LEAVE_REQUESTS];
  private corrections: AttendanceCorrectionItem[] = [...MOCK_ATTENDANCE_CORRECTIONS];

  async getSessions(date?: string): Promise<ApiResponse<AttendanceSessionItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.sessions];
    if (date) {
      items = items.filter((s) => s.sessionDate === date);
    }
    return { success: true, data: items };
  }

  async getSessionById(id: string): Promise<ApiResponse<AttendanceSessionItem | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const session = this.sessions.find((s) => s.id === id) || null;
    return { success: true, data: session };
  }

  async getSessionRoster(sessionId: string): Promise<ApiResponse<StudentAttendanceSheetEntry[]>> {
    await new Promise((r) => setTimeout(r, 60));
    // Generate class roster based on canonical mock students
    const roster: StudentAttendanceSheetEntry[] = MOCK_STUDENTS.map((stu, idx) => ({
      studentId: stu.id,
      rollNumber: stu.rollNumber,
      name: `${stu.firstName} ${stu.lastName}`,
      status: idx === 2 ? "ABSENT" : "PRESENT",
      remarks: idx === 2 ? "Unexcused absence" : undefined,
    }));
    return { success: true, data: roster };
  }

  async submitAttendance(
    sessionId: string,
    records: StudentAttendanceSheetEntry[]
  ): Promise<ApiResponse<{ updatedCount: number }>> {
    await new Promise((r) => setTimeout(r, 120));
    const session = this.sessions.find((s) => s.id === sessionId);
    if (session) {
      session.status = "MARKED";
      session.presentCount = records.filter((r) => r.status === "PRESENT").length;
      session.absentCount = records.filter((r) => r.status === "ABSENT").length;
    }
    return {
      success: true,
      data: { updatedCount: records.length },
    };
  }

  async getDashboard(): Promise<ApiResponse<{
    todaySessionsCount: number;
    sessionsMarkedToday: number;
    overallAttendancePercentage: number;
    studentsBelowThresholdCount: number;
    pendingLeaveRequestsCount: number;
    pendingCorrectionsCount: number;
  }>> {
    await new Promise((r) => setTimeout(r, 40));
    const today = "2026-09-30";
    const todaySessions = this.sessions.filter((s) => s.sessionDate === today);
    const marked = todaySessions.filter((s) => s.status === "MARKED").length;
    const pendingLeaves = this.leaves.filter((l) => l.status === "PENDING").length;
    const pendingCorr = this.corrections.filter((c) => c.status === "PENDING").length;

    return {
      success: true,
      data: {
        todaySessionsCount: todaySessions.length || 6,
        sessionsMarkedToday: marked || 4,
        overallAttendancePercentage: 88.6,
        studentsBelowThresholdCount: 14,
        pendingLeaveRequestsCount: pendingLeaves,
        pendingCorrectionsCount: pendingCorr,
      },
    };
  }

  async createSession(data: Partial<AttendanceSessionItem>): Promise<ApiResponse<AttendanceSessionItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const session: AttendanceSessionItem = {
      id: `att-sess-${Date.now()}`,
      sessionDate: data.sessionDate || new Date().toISOString().split("T")[0],
      courseCode: data.courseCode || "CS301",
      courseName: data.courseName || "Data Structures & Algorithms",
      section: data.section || "5th Sem CSE — Sec A",
      facultyName: data.facultyName || "Dr. Rajesh Sharma",
      periodSlot: data.periodSlot || "09:30 - 10:30 AM",
      room: data.room || "Hall 302",
      totalStudents: 68,
      presentCount: 0,
      absentCount: 0,
      status: "SCHEDULED",
    };
    this.sessions.unshift(session);
    return { success: true, data: session };
  }

  async getLeaves(): Promise<ApiResponse<StudentLeaveRequestItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.leaves };
  }

  async submitLeave(data: Partial<StudentLeaveRequestItem>): Promise<ApiResponse<StudentLeaveRequestItem>> {
    await new Promise((r) => setTimeout(r, 90));
    const newLeave: StudentLeaveRequestItem = {
      id: `leave-${Date.now()}`,
      studentId: data.studentId || "stu-24cse0101",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      leaveType: data.leaveType || "CASUAL",
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      endDate: data.endDate || new Date().toISOString().split("T")[0],
      totalDays: data.totalDays || 1,
      reason: data.reason || "Personal work",
      status: "PENDING",
      submittedOn: new Date().toISOString().split("T")[0],
    };
    this.leaves.unshift(newLeave);
    return { success: true, data: newLeave };
  }

  async updateLeaveStatus(id: string, status: "APPROVED" | "REJECTED"): Promise<ApiResponse<StudentLeaveRequestItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) throw new Error("Leave request not found");
    leave.status = status;
    return { success: true, data: leave };
  }

  async getCorrections(): Promise<ApiResponse<AttendanceCorrectionItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.corrections };
  }

  async submitCorrection(data: Partial<AttendanceCorrectionItem>): Promise<ApiResponse<AttendanceCorrectionItem>> {
    await new Promise((r) => setTimeout(r, 90));
    const correction: AttendanceCorrectionItem = {
      id: `corr-${Date.now()}`,
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      courseCode: data.courseCode || "CS301",
      sessionDate: data.sessionDate || new Date().toISOString().split("T")[0],
      currentStatus: data.currentStatus || "ABSENT",
      requestedStatus: data.requestedStatus || "PRESENT",
      reason: data.reason || "Present in lab; marked absent by proxy issue",
      status: "PENDING",
    };
    this.corrections.unshift(correction);
    return { success: true, data: correction };
  }

  async updateCorrectionStatus(
    id: string,
    status: "APPROVED" | "REJECTED"
  ): Promise<ApiResponse<AttendanceCorrectionItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const corr = this.corrections.find((c) => c.id === id);
    if (!corr) throw new Error("Correction request not found");
    corr.status = status;
    return { success: true, data: corr };
  }
}

export const attendanceService = new AttendanceService();
