import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { StudentComprehensiveDetail } from "@/types/domain";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export interface StudentFilterParams {
  search?: string;
  programId?: string;
  department?: string;
  semester?: number;
  status?: string;
  page?: number;
  pageSize?: number;
}

class StudentsService {
  private students: StudentComprehensiveDetail[] = [...MOCK_STUDENTS];

  async list(params?: StudentFilterParams): Promise<PaginatedResponse<StudentComprehensiveDetail>> {
    // Simulate lightweight async delay for realistic UI transition
    await new Promise((r) => setTimeout(r, 80));

    let filtered = [...this.students];

    if (params?.search) {
      const q = params.search.toLowerCase().trim();
      filtered = filtered.filter(
        (s) =>
          s.firstName.toLowerCase().includes(q) ||
          s.lastName.toLowerCase().includes(q) ||
          s.rollNumber.toLowerCase().includes(q) ||
          s.email.toLowerCase().includes(q)
      );
    }

    if (params?.department) {
      filtered = filtered.filter((s) => s.program.department === params.department);
    }

    if (params?.status) {
      filtered = filtered.filter((s) => s.status === params.status);
    }

    if (params?.semester) {
      filtered = filtered.filter((s) => s.currentSemester === Number(params.semester));
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const totalRecords = filtered.length;
    const totalPages = Math.ceil(totalRecords / pageSize) || 1;
    const startIndex = (page - 1) * pageSize;
    const paginatedItems = filtered.slice(startIndex, startIndex + pageSize);

    return {
      success: true,
      data: paginatedItems,
      pagination: {
        page,
        pageSize,
        totalRecords,
        totalPages,
        page_size: pageSize,
        total_records: totalRecords,
        total_pages: totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1,
      },
    };
  }

  async getById(id: string): Promise<ApiResponse<StudentComprehensiveDetail | null>> {
    await new Promise((r) => setTimeout(r, 60));
    const student = this.students.find(
      (s) => s.id === id || s.rollNumber.toLowerCase() === id.toLowerCase()
    ) || null;
    return {
      success: true,
      data: student,
    };
  }

  async create(data: Partial<StudentComprehensiveDetail>): Promise<ApiResponse<StudentComprehensiveDetail>> {
    await new Promise((r) => setTimeout(r, 120));
    const newStudent: StudentComprehensiveDetail = {
      id: `stu-${Date.now()}`,
      rollNumber: data.rollNumber || `24CSE0${this.students.length + 101}`,
      registrationNumber: `REG2024CS0${this.students.length + 101}`,
      firstName: data.firstName || "New",
      lastName: data.lastName || "Student",
      email: data.email || "new.student@student.campusos.edu",
      phone: data.phone || "+91 90000 00000",
      gender: data.gender || "Male",
      dateOfBirth: data.dateOfBirth || "2004-01-01",
      bloodGroup: data.bloodGroup || "O+",
      status: data.status || "ACTIVE",
      admissionDate: new Date().toISOString().split("T")[0],
      program: data.program || {
        id: "prog-cse-btech",
        code: "BTECH-CSE",
        name: "B.Tech Computer Science & Engineering",
        department: "Computer Science & Engineering",
      },
      academicYear: "2026-2027",
      currentSemester: data.currentSemester || 1,
      section: data.section || "A",
      batch: "2024-2028",
      quota: "MERIT",
      address: data.address || {
        street: "University Campus Road",
        city: "Bengaluru",
        state: "Karnataka",
        pincode: "560001",
      },
      guardian: data.guardian || {
        name: "Guardian Name",
        relation: "Father",
        phone: "+91 98450 00000",
        email: "guardian@example.com",
        occupation: "Professional",
      },
      academicStats: {
        cgpa: 8.0,
        totalCreditsEarned: 24,
        backlogs: 0,
        rank: this.students.length + 1,
      },
      attendanceSummary: {
        overallPercentage: 85.0,
        totalClasses: 120,
        attendedClasses: 102,
        status: "EXCELLENT",
      },
      financeSummary: {
        totalBilled: 145000,
        totalPaid: 145000,
        pendingDue: 0,
        status: "CLEAR",
      },
      placementSummary: {
        isEligible: true,
        appliedDrives: 0,
        interviewsScheduled: 0,
        offersReceived: 0,
      },
      enrolledCourses: [],
      recentActivity: [
        {
          id: `act-${Date.now()}`,
          action: "Student record formally registered into CampusOS People Registry",
          timestamp: "Just now",
          domain: "Admissions",
          actor: "Registrar Office",
        },
      ],
      documents: [],
    };

    this.students.unshift(newStudent);
    return {
      success: true,
      data: newStudent,
    };
  }

  async update(id: string, data: Partial<StudentComprehensiveDetail>): Promise<ApiResponse<StudentComprehensiveDetail>> {
    await new Promise((r) => setTimeout(r, 100));
    const idx = this.students.findIndex(
      (s) => s.id === id || s.rollNumber.toLowerCase() === id.toLowerCase()
    );
    if (idx === -1) {
      throw new Error(`Student not found with ID ${id}`);
    }
    this.students[idx] = { ...this.students[idx], ...data };
    return {
      success: true,
      data: this.students[idx],
    };
  }
}

export const studentsService = new StudentsService();
