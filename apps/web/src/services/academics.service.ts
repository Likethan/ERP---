import { ApiResponse, PaginatedResponse } from "@campusos/types";
import {
  DepartmentItem,
  ProgramItem,
  SubjectItem,
  CurriculumSchemeItem,
  CourseOfferingItem,
  TimetableSlotItem,
  MOCK_DEPARTMENTS,
  MOCK_PROGRAMS,
  MOCK_SUBJECTS,
  MOCK_CURRICULA,
  MOCK_COURSE_OFFERINGS,
  MOCK_TIMETABLE,
} from "@/mocks/academics.mock";

class AcademicsService {
  private departments: DepartmentItem[] = [...MOCK_DEPARTMENTS];
  private programs: ProgramItem[] = [...MOCK_PROGRAMS];
  private subjects: SubjectItem[] = [...MOCK_SUBJECTS];
  private curricula: CurriculumSchemeItem[] = [...MOCK_CURRICULA];
  private offerings: CourseOfferingItem[] = [...MOCK_COURSE_OFFERINGS];
  private timetable: TimetableSlotItem[] = [...MOCK_TIMETABLE];

  async getDepartments(): Promise<ApiResponse<DepartmentItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.departments };
  }

  async getPrograms(): Promise<ApiResponse<ProgramItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.programs };
  }

  async getSubjects(department?: string): Promise<ApiResponse<SubjectItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.subjects];
    if (department) {
      items = items.filter((s) => s.department === department);
    }
    return { success: true, data: items };
  }

  async getCurricula(): Promise<ApiResponse<CurriculumSchemeItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.curricula };
  }

  async getCourseOfferings(params?: { semester?: number; department?: string }): Promise<ApiResponse<CourseOfferingItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.offerings];
    if (params?.semester) {
      items = items.filter((o) => o.semester === Number(params.semester));
    }
    if (params?.department) {
      items = items.filter((o) => o.department === params.department);
    }
    return { success: true, data: items };
  }

  async getTimetable(day?: string, section?: string): Promise<ApiResponse<TimetableSlotItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.timetable];
    if (day) {
      items = items.filter((t) => t.day.toLowerCase() === day.toLowerCase());
    }
    return { success: true, data: items };
  }

  async createSubject(data: Partial<SubjectItem>): Promise<ApiResponse<SubjectItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newSub: SubjectItem = {
      id: `sub-${Date.now()}`,
      code: data.code || `CS${this.subjects.length + 301}`,
      name: data.name || "New Subject",
      department: data.department || "Computer Science & Engineering",
      credits: data.credits || 3,
      type: data.type || "THEORY",
      lectureHours: data.lectureHours || 3,
      tutorialHours: data.tutorialHours || 0,
      practicalHours: data.practicalHours || 0,
      status: "ACTIVE",
    };
    this.subjects.push(newSub);
    return { success: true, data: newSub };
  }
}

export const academicsService = new AcademicsService();
