import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { FacultyDetailView } from "@/types/domain";
import {
  FacultyWorkloadSummary,
  LabDesignationItem,
  FacultyPublication,
  WorkloadAllocationStatus,
} from "@/types/people";
import { MOCK_FACULTY } from "@/mocks/faculty.mock";
import {
  MOCK_FACULTY_WORKLOADS,
  MOCK_FACULTY_PUBLICATIONS,
} from "@/mocks/people.mock";

export interface FacultyFilterParams {
  department?: string;
  designation?: string;
  employmentType?: string;
  status?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}

class FacultyService {
  private faculty: FacultyDetailView[] = [...MOCK_FACULTY];
  private workloadsPool: Record<string, FacultyWorkloadSummary> = {
    ...MOCK_FACULTY_WORKLOADS,
  };
  private publicationsPool: Record<string, FacultyPublication[]> = {
    ...MOCK_FACULTY_PUBLICATIONS,
  };

  async list(
    params?: FacultyFilterParams | string,
  ): Promise<PaginatedResponse<FacultyDetailView>> {
    await new Promise((r) => setTimeout(r, 60));

    let items = [...this.faculty];

    if (typeof params === "string") {
      // Legacy signature compatibility: list(department?: string)
      items = items.filter((f) =>
        f.department.toLowerCase().includes(params.toLowerCase()),
      );
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

    if (params?.search) {
      const q = params.search.toLowerCase().trim();
      items = items.filter(
        (f) =>
          f.firstName.toLowerCase().includes(q) ||
          f.lastName.toLowerCase().includes(q) ||
          f.employeeCode.toLowerCase().includes(q) ||
          f.email.toLowerCase().includes(q) ||
          f.specialization.toLowerCase().includes(q),
      );
    }

    if (params?.department && params.department !== "ALL") {
      items = items.filter(
        (f) => f.department.toLowerCase() === params.department?.toLowerCase(),
      );
    }

    if (params?.designation && params.designation !== "ALL") {
      items = items.filter((f) =>
        f.designation.toLowerCase().includes(params.designation!.toLowerCase()),
      );
    }

    if (params?.status && params.status !== "ALL") {
      items = items.filter((f) => f.status === params.status);
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const totalRecords = items.length;
    const totalPages = Math.ceil(totalRecords / pageSize) || 1;
    const startIndex = (page - 1) * pageSize;
    const paginatedItems = items.slice(startIndex, startIndex + pageSize);

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

  async getById(id: string): Promise<ApiResponse<FacultyDetailView | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const member = this.faculty.find(
      (f) => f.id === id || f.employeeCode === id,
    );
    if (!member) {
      return { success: true, data: null };
    }

    // Attach workload, labs, and publications
    const workload = this.workloadsPool[member.id] ||
      this.workloadsPool[member.employeeCode] || {
        facultyId: member.id,
        academicYear: "2026-2027",
        semester: 5,
        totalAssignedHours: member.teachingLoadHours || 12,
        lectureHours: 8,
        labHours: 4,
        preparationHours: 2,
        weeklyTargetHours: 16,
        status: (member.teachingLoadHours >= 16
          ? "BALANCED"
          : "UNDER_ALLOCATED") as WorkloadAllocationStatus,
        assignments: member.assignedSubjects.map((s) => ({
          id: s.id,
          code: s.code,
          name: s.name,
          semester: s.semester,
          section: s.section,
          studentCount: s.studentCount,
          lectureHours: 3,
          labHours: 1,
          credits: 4,
        })),
        labDesignations: [],
      };

    const publications =
      this.publicationsPool[member.id] ||
      this.publicationsPool[member.employeeCode] ||
      [];

    const fullFaculty: FacultyDetailView = {
      ...member,
      workloadSummary: workload,
      labDesignations: workload.labDesignations,
      publications,
    };

    return {
      success: true,
      data: fullFaculty,
    };
  }

  async create(
    data: Partial<FacultyDetailView>,
  ): Promise<ApiResponse<FacultyDetailView>> {
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
      specialization: data.specialization || "Computer Systems & Intelligence",
      joiningDate: data.joiningDate || new Date().toISOString().split("T")[0],
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

  async update(
    id: string,
    data: Partial<FacultyDetailView>,
  ): Promise<ApiResponse<FacultyDetailView>> {
    await new Promise((r) => setTimeout(r, 80));
    const idx = this.faculty.findIndex(
      (f) => f.id === id || f.employeeCode === id,
    );
    if (idx === -1) throw new Error("Faculty member not found");
    this.faculty[idx] = { ...this.faculty[idx], ...data };
    return { success: true, data: this.faculty[idx] };
  }

  // ==========================================
  // Workload & Lab Methods
  // ==========================================

  async getWorkload(
    facultyId: string,
  ): Promise<ApiResponse<FacultyWorkloadSummary>> {
    await new Promise((r) => setTimeout(r, 40));
    const fac = await this.getById(facultyId);
    return {
      success: true,
      data: fac.data?.workloadSummary || {
        facultyId,
        academicYear: "2026-2027",
        semester: 5,
        totalAssignedHours: 12,
        lectureHours: 8,
        labHours: 4,
        preparationHours: 2,
        weeklyTargetHours: 16,
        status: "BALANCED",
        assignments: [],
        labDesignations: [],
      },
    };
  }

  async assignLab(
    facultyId: string,
    lab: Partial<LabDesignationItem>,
  ): Promise<ApiResponse<LabDesignationItem>> {
    await new Promise((r) => setTimeout(r, 60));
    const newLab: LabDesignationItem = {
      id: `lab-des-${Date.now()}`,
      labName: lab.labName || "Computer Systems Lab",
      courseCode: lab.courseCode || "CS301-L",
      courseName: lab.courseName || "Laboratory Component",
      section: lab.section || "A-Batch 1",
      dayOfWeek: lab.dayOfWeek || "Monday",
      timeSlot: lab.timeSlot || "02:00 PM - 04:00 PM",
      roomNumber: lab.roomNumber || "Lab 201, Turing Block",
      weeklyHours: lab.weeklyHours || 2,
      batchCapacity: lab.batchCapacity || 32,
    };

    if (!this.workloadsPool[facultyId]) {
      const fac = await this.getById(facultyId);
      if (fac.data?.workloadSummary) {
        this.workloadsPool[facultyId] = fac.data.workloadSummary;
      }
    }

    if (this.workloadsPool[facultyId]) {
      this.workloadsPool[facultyId].labDesignations.push(newLab);
      this.workloadsPool[facultyId].labHours += newLab.weeklyHours;
      this.workloadsPool[facultyId].totalAssignedHours += newLab.weeklyHours;
    }

    return { success: true, data: newLab };
  }

  async removeLabAssignment(
    facultyId: string,
    labId: string,
  ): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 50));
    if (this.workloadsPool[facultyId]) {
      const target = this.workloadsPool[facultyId].labDesignations.find(
        (l) => l.id === labId,
      );
      if (target) {
        this.workloadsPool[facultyId].labHours -= target.weeklyHours;
        this.workloadsPool[facultyId].totalAssignedHours -= target.weeklyHours;
        this.workloadsPool[facultyId].labDesignations = this.workloadsPool[
          facultyId
        ].labDesignations.filter((l) => l.id !== labId);
      }
    }
    return { success: true, data: true };
  }

  // ==========================================
  // Publication Methods
  // ==========================================

  async getPublications(
    facultyId: string,
  ): Promise<ApiResponse<FacultyPublication[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: this.publicationsPool[facultyId] || [],
    };
  }

  async createPublication(
    facultyId: string,
    pub: Partial<FacultyPublication>,
  ): Promise<ApiResponse<FacultyPublication>> {
    await new Promise((r) => setTimeout(r, 80));
    const newPub: FacultyPublication = {
      id: `pub-${Date.now()}`,
      title: pub.title || "Research Publication",
      publicationType: pub.publicationType || "JOURNAL",
      venueName: pub.venueName || "International Journal of Engineering",
      publicationYear: pub.publicationYear || new Date().getFullYear(),
      authors:
        pub.authors && pub.authors.length > 0
          ? pub.authors
          : ["Faculty Author"],
      doi: pub.doi,
      status: pub.status || "PUBLISHED",
      citationCount: pub.citationCount || 0,
      url: pub.url,
      abstractSummary: pub.abstractSummary,
    };

    if (!this.publicationsPool[facultyId]) {
      this.publicationsPool[facultyId] = [];
    }
    this.publicationsPool[facultyId].unshift(newPub);
    return { success: true, data: newPub };
  }

  async updatePublication(
    facultyId: string,
    pubId: string,
    pub: Partial<FacultyPublication>,
  ): Promise<ApiResponse<FacultyPublication>> {
    await new Promise((r) => setTimeout(r, 60));
    const list = this.publicationsPool[facultyId] || [];
    const idx = list.findIndex((p) => p.id === pubId);
    if (idx === -1) throw new Error("Publication not found");
    list[idx] = { ...list[idx], ...pub };
    return { success: true, data: list[idx] };
  }

  async deletePublication(
    facultyId: string,
    pubId: string,
  ): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 50));
    if (this.publicationsPool[facultyId]) {
      this.publicationsPool[facultyId] = this.publicationsPool[
        facultyId
      ].filter((p) => p.id !== pubId);
    }
    return { success: true, data: true };
  }
}

export const facultyService = new FacultyService();
