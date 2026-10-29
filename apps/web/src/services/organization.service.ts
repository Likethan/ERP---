import type {
  AcademicYear,
  ApiResponse,
  Batch,
  Campus,
  Department,
  Institution,
  Program,
  Regulation,
  Section,
  Semester,
} from "@campusos/types";
import { apiFetch } from "@/lib/api-client";
import {
  MOCK_ACADEMIC_YEARS_LIST,
  MOCK_BATCHES_LIST,
  MOCK_CAMPUSES,
  MOCK_DEPARTMENTS_LIST,
  MOCK_INSTITUTION,
  MOCK_PROGRAMS_LIST,
  MOCK_REGULATIONS_LIST,
  MOCK_SECTIONS_LIST,
  MOCK_SEMESTERS_LIST,
} from "@/mocks/organization.mock";

class OrganizationService {
  private institution: Institution = { ...MOCK_INSTITUTION };
  private campuses: Campus[] = [...MOCK_CAMPUSES];
  private departments: Department[] = [...MOCK_DEPARTMENTS_LIST];
  private programs: Program[] = [...MOCK_PROGRAMS_LIST];
  private regulations: Regulation[] = [...MOCK_REGULATIONS_LIST];
  private academicYears: AcademicYear[] = [...MOCK_ACADEMIC_YEARS_LIST];
  private semesters: Semester[] = [...MOCK_SEMESTERS_LIST];
  private batches: Batch[] = [...MOCK_BATCHES_LIST];
  private sections: Section[] = [...MOCK_SECTIONS_LIST];

  // --- Institution ---
  async getInstitution(): Promise<ApiResponse<Institution>> {
    try {
      const res = await apiFetch<Institution>("/api/v1/institutions");
      if (res?.data) {
        this.institution = res.data;
        return res;
      }
    } catch {
      // Backend unreachable or unauthenticated in demo mode; fall back to local mock
    }
    return {
      success: true,
      data: { ...this.institution },
    };
  }

  async updateInstitution(
    id: string,
    payload: Partial<Institution>,
  ): Promise<ApiResponse<Institution>> {
    try {
      const res = await apiFetch<Institution>(`/api/v1/institutions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        this.institution = res.data;
        return res;
      }
    } catch {
      // Fall back to local update
    }
    this.institution = {
      ...this.institution,
      ...payload,
      updated_at: new Date().toISOString(),
    };
    return {
      success: true,
      data: { ...this.institution },
    };
  }

  // --- Campuses ---
  async listCampuses(): Promise<ApiResponse<Campus[]>> {
    try {
      const res = await apiFetch<Campus[]>("/api/v1/campuses");
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.campuses = res.data;
        return res;
      }
    } catch {
      // Backend unreachable or unauthenticated in demo mode; fall back to local mock
    }
    return {
      success: true,
      data: [...this.campuses],
    };
  }

  async createCampus(payload: {
    code: string;
    name: string;
    city: string;
    address: string;
  }): Promise<ApiResponse<Campus>> {
    try {
      const res = await apiFetch<Campus>("/api/v1/campuses", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        this.campuses.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back to local creation
    }
    const newCampus: Campus = {
      id: `camp-${Date.now()}`,
      tenant_id: this.institution.id,
      code: payload.code.trim().toUpperCase(),
      name: payload.name.trim(),
      city: payload.city.trim(),
      address: payload.address.trim(),
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.campuses.unshift(newCampus);
    return {
      success: true,
      data: newCampus,
    };
  }

  async updateCampus(
    campusId: string,
    payload: Partial<Campus>,
  ): Promise<ApiResponse<Campus>> {
    try {
      const res = await apiFetch<Campus>(`/api/v1/campuses/${campusId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        const idx = this.campuses.findIndex((c) => c.id === campusId);
        if (idx !== -1) this.campuses[idx] = res.data;
        return res;
      }
    } catch {
      // Fall back to local update
    }
    const idx = this.campuses.findIndex((c) => c.id === campusId);
    if (idx !== -1) {
      this.campuses[idx] = {
        ...this.campuses[idx],
        ...payload,
        updated_at: new Date().toISOString(),
      };
      return { success: true, data: this.campuses[idx] };
    }
    throw new Error(`Campus not found: ${campusId}`);
  }

  // --- Departments ---
  async listDepartments(
    campusId?: string,
    search?: string,
  ): Promise<ApiResponse<Department[]>> {
    try {
      const params = new URLSearchParams();
      if (campusId) params.append("campus_id", campusId);
      if (search) params.append("search", search);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await apiFetch<Department[]>(`/api/v1/departments${qs}`);
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.departments = res.data;
        return res;
      }
    } catch {
      // Backend unreachable or unauthenticated in demo mode; fall back to local mock
    }

    let filtered = [...this.departments];
    if (campusId) {
      filtered = filtered.filter((d) => d.campus_id === campusId);
    }
    if (search) {
      const q = search.toLowerCase().trim();
      filtered = filtered.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.code.toLowerCase().includes(q) ||
          (d.hod_name && d.hod_name.toLowerCase().includes(q)),
      );
    }
    return {
      success: true,
      data: filtered,
    };
  }

  async createDepartment(payload: {
    code: string;
    name: string;
    department_type: string;
    campus_id?: string;
  }): Promise<ApiResponse<Department>> {
    try {
      const res = await apiFetch<Department>("/api/v1/departments", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        this.departments.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back to local creation
    }
    const newDept: Department = {
      id: `dept-${Date.now()}`,
      tenant_id: this.institution.id,
      campus_id: payload.campus_id || null,
      code: payload.code.trim().toUpperCase(),
      name: payload.name.trim(),
      department_type: payload.department_type || "ACADEMIC",
      hod_user_id: null,
      hod_name: "Unassigned",
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.departments.unshift(newDept);
    return {
      success: true,
      data: newDept,
    };
  }

  async updateDepartment(
    deptId: string,
    payload: Partial<Department>,
  ): Promise<ApiResponse<Department>> {
    try {
      const res = await apiFetch<Department>(`/api/v1/departments/${deptId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        const idx = this.departments.findIndex((d) => d.id === deptId);
        if (idx !== -1) this.departments[idx] = res.data;
        return res;
      }
    } catch {
      // Fall back to local update
    }
    const idx = this.departments.findIndex((d) => d.id === deptId);
    if (idx !== -1) {
      this.departments[idx] = {
        ...this.departments[idx],
        ...payload,
        updated_at: new Date().toISOString(),
      };
      return { success: true, data: this.departments[idx] };
    }
    throw new Error(`Department not found: ${deptId}`);
  }

  // --- Programs ---
  async listPrograms(
    departmentId?: string,
    search?: string,
  ): Promise<ApiResponse<Program[]>> {
    try {
      const params = new URLSearchParams();
      if (departmentId) params.append("department_id", departmentId);
      if (search) params.append("search", search);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await apiFetch<Program[]>(`/api/v1/programs${qs}`);
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.programs = res.data;
        return res;
      }
    } catch {
      // Backend unreachable or unauthenticated in demo mode; fall back to local mock
    }

    let filtered = [...this.programs];
    if (departmentId) {
      filtered = filtered.filter((p) => p.department_id === departmentId);
    }
    if (search) {
      const q = search.toLowerCase().trim();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.code.toLowerCase().includes(q) ||
          (p.department_name && p.department_name.toLowerCase().includes(q)),
      );
    }
    return {
      success: true,
      data: filtered,
    };
  }

  async createProgram(payload: {
    department_id: string;
    code: string;
    name: string;
    degree_level: string;
    duration_years: number;
    total_semesters: number;
    required_credits: number;
  }): Promise<ApiResponse<Program>> {
    try {
      const res = await apiFetch<Program>("/api/v1/programs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        this.programs.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back to local creation
    }
    const dept = this.departments.find((d) => d.id === payload.department_id);
    const newProgram: Program = {
      id: `prog-${Date.now()}`,
      tenant_id: this.institution.id,
      department_id: payload.department_id,
      department_name: dept?.name || "Academic Department",
      code: payload.code.trim().toUpperCase(),
      name: payload.name.trim(),
      degree_level: payload.degree_level,
      duration_years: payload.duration_years,
      total_semesters: payload.total_semesters,
      required_credits: payload.required_credits,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.programs.unshift(newProgram);
    return {
      success: true,
      data: newProgram,
    };
  }

  async updateProgram(
    programId: string,
    payload: Partial<Program>,
  ): Promise<ApiResponse<Program>> {
    try {
      const res = await apiFetch<Program>(`/api/v1/programs/${programId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        const idx = this.programs.findIndex((p) => p.id === programId);
        if (idx !== -1) this.programs[idx] = res.data;
        return res;
      }
    } catch {
      // Fall back to local update
    }
    const idx = this.programs.findIndex((p) => p.id === programId);
    if (idx !== -1) {
      this.programs[idx] = {
        ...this.programs[idx],
        ...payload,
        updated_at: new Date().toISOString(),
      };
      return { success: true, data: this.programs[idx] };
    }
    throw new Error(`Program not found: ${programId}`);
  }

  // --- Academic Structure ---
  async listAcademicYears(): Promise<ApiResponse<AcademicYear[]>> {
    try {
      const res = await apiFetch<AcademicYear[]>(
        "/api/v1/academic-structure/academic-years",
      );
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.academicYears = res.data;
        return res;
      }
    } catch {
      // Fall back to local mock
    }
    return {
      success: true,
      data: [...this.academicYears],
    };
  }

  async createAcademicYear(payload: {
    name: string;
    start_date: string;
    end_date: string;
    is_current: boolean;
  }): Promise<ApiResponse<AcademicYear>> {
    try {
      const res = await apiFetch<AcademicYear>(
        "/api/v1/academic-structure/academic-years",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      if (res?.data) {
        this.academicYears.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back to local
    }
    const newYear: AcademicYear = {
      id: `ay-${Date.now()}`,
      tenant_id: this.institution.id,
      name: payload.name.trim(),
      start_date: payload.start_date,
      end_date: payload.end_date,
      is_current: payload.is_current,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    if (payload.is_current) {
      this.academicYears.forEach((y) => (y.is_current = false));
    }
    this.academicYears.unshift(newYear);
    return { success: true, data: newYear };
  }

  async listSemesters(): Promise<ApiResponse<Semester[]>> {
    try {
      const res = await apiFetch<Semester[]>(
        "/api/v1/academic-structure/semesters",
      );
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.semesters = res.data;
        return res;
      }
    } catch {
      // Fall back
    }
    return {
      success: true,
      data: [...this.semesters],
    };
  }

  async createSemester(payload: {
    academic_year_id: string;
    name: string;
    semester_number: number;
    term_type: string;
    start_date: string;
    end_date: string;
  }): Promise<ApiResponse<Semester>> {
    try {
      const res = await apiFetch<Semester>(
        "/api/v1/academic-structure/semesters",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      if (res?.data) {
        this.semesters.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back
    }
    const newSem: Semester = {
      id: `sem-${Date.now()}`,
      tenant_id: this.institution.id,
      academic_year_id: payload.academic_year_id,
      name: payload.name.trim(),
      semester_number: payload.semester_number,
      term_type: payload.term_type,
      start_date: payload.start_date,
      end_date: payload.end_date,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.semesters.unshift(newSem);
    return { success: true, data: newSem };
  }

  async listRegulations(): Promise<ApiResponse<Regulation[]>> {
    try {
      const res = await apiFetch<Regulation[]>(
        "/api/v1/academic-structure/regulations",
      );
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.regulations = res.data;
        return res;
      }
    } catch {
      // Fall back
    }
    return {
      success: true,
      data: [...this.regulations],
    };
  }

  async createRegulation(payload: {
    code: string;
    title: string;
    effective_year: number;
    description?: string;
  }): Promise<ApiResponse<Regulation>> {
    try {
      const res = await apiFetch<Regulation>(
        "/api/v1/academic-structure/regulations",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      if (res?.data) {
        this.regulations.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back
    }
    const newReg: Regulation = {
      id: `reg-${Date.now()}`,
      tenant_id: this.institution.id,
      code: payload.code.trim().toUpperCase(),
      title: payload.title.trim(),
      effective_year: payload.effective_year,
      description: payload.description || null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.regulations.unshift(newReg);
    return { success: true, data: newReg };
  }

  async listBatches(): Promise<ApiResponse<Batch[]>> {
    try {
      const res = await apiFetch<Batch[]>("/api/v1/academic-structure/batches");
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.batches = res.data;
        return res;
      }
    } catch {
      // Fall back
    }
    return {
      success: true,
      data: [...this.batches],
    };
  }

  async createBatch(payload: {
    program_id: string;
    regulation_id: string;
    name: string;
    admission_year: number;
    graduation_year: number;
  }): Promise<ApiResponse<Batch>> {
    try {
      const res = await apiFetch<Batch>("/api/v1/academic-structure/batches", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.data) {
        this.batches.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back
    }
    const newBatch: Batch = {
      id: `batch-${Date.now()}`,
      tenant_id: this.institution.id,
      program_id: payload.program_id,
      regulation_id: payload.regulation_id,
      name: payload.name.trim(),
      admission_year: payload.admission_year,
      graduation_year: payload.graduation_year,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.batches.unshift(newBatch);
    return { success: true, data: newBatch };
  }

  async listSections(): Promise<ApiResponse<Section[]>> {
    try {
      const res = await apiFetch<Section[]>(
        "/api/v1/academic-structure/sections",
      );
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        this.sections = res.data;
        return res;
      }
    } catch {
      // Fall back
    }
    return {
      success: true,
      data: [...this.sections],
    };
  }

  async createSection(payload: {
    program_id: string;
    batch_id: string;
    semester_id: string;
    name: string;
    capacity: number;
  }): Promise<ApiResponse<Section>> {
    try {
      const res = await apiFetch<Section>(
        "/api/v1/academic-structure/sections",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      if (res?.data) {
        this.sections.unshift(res.data);
        return res;
      }
    } catch {
      // Fall back
    }
    const newSection: Section = {
      id: `sec-${Date.now()}`,
      tenant_id: this.institution.id,
      program_id: payload.program_id,
      batch_id: payload.batch_id,
      semester_id: payload.semester_id,
      name: payload.name.trim(),
      capacity: payload.capacity,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.sections.unshift(newSection);
    return { success: true, data: newSection };
  }
}

export const organizationService = new OrganizationService();
