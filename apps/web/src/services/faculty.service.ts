import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { FacultyDetailView, StaffDetailView } from "@/types/domain";
import { MOCK_FACULTY, MOCK_STAFF } from "@/mocks/faculty.mock";

class FacultyService {
  private faculty: FacultyDetailView[] = [...MOCK_FACULTY];

  async list(department?: string): Promise<PaginatedResponse<FacultyDetailView>> {
    await new Promise((r) => setTimeout(r, 60));
    let items = [...this.faculty];
    if (department) {
      items = items.filter((f) => f.department.toLowerCase().includes(department.toLowerCase()));
    }
    return {
      success: true,
      data: items,
      pagination: {
        page: 1,
        pageSize: items.length,
        totalRecords: items.length,
        totalPages: 1,
      },
    };
  }

  async getById(id: string): Promise<ApiResponse<FacultyDetailView | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const member = this.faculty.find((f) => f.id === id || f.employeeCode === id) || null;
    return {
      success: true,
      data: member,
    };
  }

  async create(data: Partial<FacultyDetailView>): Promise<ApiResponse<FacultyDetailView>> {
    await new Promise((r) => setTimeout(r, 100));
    const newFac: FacultyDetailView = {
      id: `fac-${Date.now()}`,
      employeeCode: data.employeeCode || `FAC-CSE-0${this.faculty.length + 10}`,
      firstName: data.firstName || "Faculty",
      lastName: data.lastName || "Member",
      email: data.email || "faculty@campusos.edu",
      phone: data.phone || "+91 94480 00000",
      designation: data.designation || "Assistant Professor",
      department: data.department || "Computer Science & Engineering",
      qualification: data.qualification || "M.Tech / Ph.D.",
      specialization: data.specialization || "Computer Systems",
      joiningDate: new Date().toISOString().split("T")[0],
      status: "ACTIVE",
      teachingLoadHours: 12,
      assignedSubjects: [],
      todayClasses: [],
      stats: {
        coursesCount: 0,
        totalStudents: 0,
        averageAttendance: 90.0,
        pendingCorrections: 0,
      },
    };
    this.faculty.unshift(newFac);
    return {
      success: true,
      data: newFac,
    };
  }
}

class StaffService {
  private staff: StaffDetailView[] = [...MOCK_STAFF];

  async list(): Promise<PaginatedResponse<StaffDetailView>> {
    await new Promise((r) => setTimeout(r, 50));
    return {
      success: true,
      data: this.staff,
      pagination: {
        page: 1,
        pageSize: this.staff.length,
        totalRecords: this.staff.length,
        totalPages: 1,
      },
    };
  }

  async getById(id: string): Promise<ApiResponse<StaffDetailView | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const s = this.staff.find((item) => item.id === id || item.employeeCode === id) || null;
    return {
      success: true,
      data: s,
    };
  }
}

export const facultyService = new FacultyService();
export const staffService = new StaffService();
