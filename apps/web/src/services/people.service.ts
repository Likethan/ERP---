import { ApiResponse } from "@campusos/types";
import {
  PeopleSummaryMetrics,
  DepartmentPeopleDistribution,
  UnifiedPersonSearchResult,
} from "@/types/people";
import {
  MOCK_PEOPLE_METRICS,
  MOCK_DEPARTMENT_DISTRIBUTION,
} from "@/mocks/people.mock";
import { studentsService } from "./students.service";
import { facultyService } from "./faculty.service";
import { staffService } from "./staff.service";

class PeopleService {
  private metrics: PeopleSummaryMetrics = { ...MOCK_PEOPLE_METRICS };
  private departments: DepartmentPeopleDistribution[] = [...MOCK_DEPARTMENT_DISTRIBUTION];

  async getMetrics(): Promise<ApiResponse<PeopleSummaryMetrics>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: this.metrics,
    };
  }

  async getDepartmentDistribution(): Promise<ApiResponse<DepartmentPeopleDistribution[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: this.departments,
    };
  }

  async searchPeople(query: string): Promise<ApiResponse<UnifiedPersonSearchResult[]>> {
    await new Promise((r) => setTimeout(r, 50));
    const q = query.toLowerCase().trim();
    if (!q) return { success: true, data: [] };

    const [studentsRes, facultyRes, staffRes] = await Promise.all([
      studentsService.list({ search: q, pageSize: 5 }),
      facultyService.list({ search: q, pageSize: 5 }),
      staffService.list({ search: q, pageSize: 5 }),
    ]);

    const results: UnifiedPersonSearchResult[] = [];

    // Map Students
    (studentsRes.data || []).forEach((s) => {
      results.push({
        id: s.id,
        name: `${s.firstName} ${s.lastName}`,
        personType: "STUDENT",
        code: s.rollNumber,
        email: s.email,
        phone: s.phone,
        department: s.program?.department || "Academic Department",
        designationOrProgram: `${s.program?.name || "B.Tech"} • Sem ${s.currentSemester}`,
        status: s.status,
        href: `/app/students/${s.id}`,
      });
    });

    // Map Faculty
    (facultyRes.data || []).forEach((f) => {
      results.push({
        id: f.id,
        name: `${f.firstName} ${f.lastName}`,
        personType: "FACULTY",
        code: f.employeeCode,
        email: f.email,
        phone: f.phone,
        department: f.department,
        designationOrProgram: f.designation,
        status: f.status,
        href: `/app/faculty/${f.id}`,
      });
    });

    // Map Staff
    (staffRes.data || []).forEach((st) => {
      results.push({
        id: st.id,
        name: `${st.firstName} ${st.lastName}`,
        personType: "STAFF",
        code: st.employeeCode,
        email: st.email,
        phone: st.phone,
        department: st.department,
        designationOrProgram: st.role || st.designation || "Staff",
        status: st.status,
        href: `/app/staff/${st.id}`,
      });
    });

    return {
      success: true,
      data: results,
    };
  }
}

export const peopleService = new PeopleService();
