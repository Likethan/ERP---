import { ApiResponse } from "@campusos/types";
import {
  AssessmentItem,
  ExamScheduleItem,
  StudentResultItem,
  MOCK_ASSESSMENTS,
  MOCK_EXAM_SCHEDULES,
  MOCK_RESULTS,
} from "@/mocks/examinations.mock";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

class ExaminationsService {
  private assessments: AssessmentItem[] = [...MOCK_ASSESSMENTS];
  private schedules: ExamScheduleItem[] = [...MOCK_EXAM_SCHEDULES];
  private results: StudentResultItem[] = [...MOCK_RESULTS];

  async getDashboard(): Promise<ApiResponse<{
    active_terms_count: number;
    assessments_pending_marks: number;
    results_awaiting_publication_count: number;
    total_published_results_count: number;
  }>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        active_terms_count: 2,
        assessments_pending_marks: 3,
        results_awaiting_publication_count: 1,
        total_published_results_count: 1240,
      },
    };
  }

  async getAssessments(semester?: number): Promise<ApiResponse<AssessmentItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.assessments];
    if (semester) {
      items = items.filter((a) => a.semester === Number(semester));
    }
    return { success: true, data: items };
  }

  async getSchedules(): Promise<ApiResponse<ExamScheduleItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.schedules };
  }

  async createSchedule(data: Partial<ExamScheduleItem>): Promise<ApiResponse<ExamScheduleItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newSch: ExamScheduleItem = {
      id: `sch-${Date.now()}`,
      examName: data.examName || "Mid-Semester Examination",
      subjectCode: data.subjectCode || "CS301",
      subjectName: data.subjectName || "Data Structures & Algorithms",
      date: data.date || new Date().toISOString().split("T")[0],
      timeSlot: data.timeSlot || "10:00 AM - 11:30 AM",
      roomNumber: data.roomNumber || "Auditorium Hall A",
      chiefInvigilator: data.chiefInvigilator || "Dr. Rajesh Sharma",
      totalCandidates: data.totalCandidates || 68,
      status: "CONFIRMED",
    };
    this.schedules.unshift(newSch);
    return { success: true, data: newSch };
  }

  async getResults(program?: string): Promise<ApiResponse<StudentResultItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.results];
    if (program) {
      items = items.filter((res) => res.program.toLowerCase().includes(program.toLowerCase()));
    }
    return { success: true, data: items };
  }

  async createAssessment(data: Partial<AssessmentItem>): Promise<ApiResponse<AssessmentItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newAsm: AssessmentItem = {
      id: `asm-${Date.now()}`,
      code: data.code || `IA-0${this.assessments.length + 1}`,
      title: data.title || "Continuous Assessment",
      type: data.type || "INTERNAL_TEST",
      academicYear: "2026-2027",
      semester: data.semester || 5,
      totalMarks: data.totalMarks || 50,
      weightagePercent: data.weightagePercent || 20,
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      status: "SCHEDULED",
    };
    this.assessments.push(newAsm);
    return { success: true, data: newAsm };
  }

  async getMarksRoster(courseOfferingId: string, assessmentId: string): Promise<ApiResponse<any>> {
    await new Promise((r) => setTimeout(r, 60));
    const currentAsm = this.assessments.find((a) => a.id === assessmentId) || this.assessments[0];
    const rosterEntries = MOCK_STUDENTS.map((stu, i) => ({
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

  async submitMarks(assessmentId: string, marksData: any): Promise<ApiResponse<{ count: number }>> {
    await new Promise((r) => setTimeout(r, 100));
    const asm = this.assessments.find((a) => a.id === assessmentId);
    if (asm) {
      asm.status = "COMPLETED";
    }
    return { success: true, data: { count: Object.keys(marksData || {}).length } };
  }
}

export const examinationsService = new ExaminationsService();
