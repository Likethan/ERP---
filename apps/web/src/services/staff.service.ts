import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { StaffDetailView } from "@/types/domain";
import {
  StaffShiftItem,
  StaffLeaveRequest,
} from "@/types/people";
import {
  MOCK_STAFF_ROSTER,
  MOCK_STAFF_SHIFTS,
  MOCK_STAFF_LEAVES,
} from "@/mocks/people.mock";

export interface StaffFilterParams {
  search?: string;
  department?: string;
  shift?: string;
  status?: string;
  employmentType?: string;
  page?: number;
  pageSize?: number;
}

class DedicatedStaffService {
  private staff: StaffDetailView[] = [...MOCK_STAFF_ROSTER];
  private shifts: StaffShiftItem[] = [...MOCK_STAFF_SHIFTS];
  private leaves: StaffLeaveRequest[] = [...MOCK_STAFF_LEAVES];

  async list(params?: StaffFilterParams): Promise<PaginatedResponse<StaffDetailView>> {
    await new Promise((r) => setTimeout(r, 50));

    let items = [...this.staff];

    if (params?.search) {
      const q = params.search.toLowerCase().trim();
      items = items.filter(
        (s) =>
          s.firstName.toLowerCase().includes(q) ||
          s.lastName.toLowerCase().includes(q) ||
          s.employeeCode.toLowerCase().includes(q) ||
          s.email.toLowerCase().includes(q) ||
          s.role.toLowerCase().includes(q) ||
          s.department.toLowerCase().includes(q)
      );
    }

    if (params?.department && params.department !== "ALL") {
      items = items.filter((s) => s.department.toLowerCase().includes(params.department!.toLowerCase()));
    }

    if (params?.shift && params.shift !== "ALL") {
      items = items.filter((s) => s.shift?.shiftType === params.shift || s.shift?.id === params.shift);
    }

    if (params?.status && params.status !== "ALL") {
      items = items.filter((s) => s.status === params.status);
    }

    if (params?.employmentType && params.employmentType !== "ALL") {
      items = items.filter((s) => s.employmentType === params.employmentType);
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

  async getById(id: string): Promise<ApiResponse<StaffDetailView | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const member = this.staff.find((s) => s.id === id || s.employeeCode.toLowerCase() === id.toLowerCase());
    if (!member) {
      return { success: true, data: null };
    }

    const memberLeaves = this.leaves.filter((l) => l.staffId === member.id);
    const fullStaff: StaffDetailView = {
      ...member,
      leaves: memberLeaves,
    };

    return {
      success: true,
      data: fullStaff,
    };
  }

  async create(data: Partial<StaffDetailView>): Promise<ApiResponse<StaffDetailView>> {
    await new Promise((r) => setTimeout(r, 80));
    const newStaff: StaffDetailView = {
      id: `stf-${Date.now()}`,
      employeeCode: data.employeeCode || `STF-ADM-0${this.staff.length + 10}`,
      firstName: data.firstName || "New",
      lastName: data.lastName || "Staff",
      email: data.email || "staff@campusos.edu",
      phone: data.phone || "+91 94480 00000",
      department: data.department || "Academic Administration",
      role: data.role || "Administrative Staff Officer",
      designation: data.designation || "Assistant Officer",
      employmentType: data.employmentType || "PERMANENT",
      joiningDate: data.joiningDate || new Date().toISOString().split("T")[0],
      status: "ACTIVE",
      shift: data.shift || this.shifts[1],
      leaveBalance: { casual: 10, sick: 10, earned: 20 },
      leaves: [],
    };

    this.staff.unshift(newStaff);
    return {
      success: true,
      data: newStaff,
    };
  }

  async update(id: string, data: Partial<StaffDetailView>): Promise<ApiResponse<StaffDetailView>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.staff.findIndex((s) => s.id === id || s.employeeCode.toLowerCase() === id.toLowerCase());
    if (idx === -1) throw new Error("Staff member not found");
    this.staff[idx] = { ...this.staff[idx], ...data };
    return { success: true, data: this.staff[idx] };
  }

  // ==========================================
  // Shift Management Methods
  // ==========================================

  async getShifts(): Promise<ApiResponse<StaffShiftItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.shifts };
  }

  async assignShift(staffId: string, shiftId: string): Promise<ApiResponse<StaffDetailView>> {
    await new Promise((r) => setTimeout(r, 60));
    const targetShift = this.shifts.find((sh) => sh.id === shiftId);
    if (!targetShift) throw new Error("Shift schedule not found");

    const idx = this.staff.findIndex((s) => s.id === staffId);
    if (idx === -1) throw new Error("Staff member not found");

    this.staff[idx].shift = targetShift;
    return { success: true, data: this.staff[idx] };
  }

  // ==========================================
  // Leave Workflow Methods
  // ==========================================

  async getLeaves(staffId?: string): Promise<ApiResponse<StaffLeaveRequest[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.leaves];
    if (staffId) {
      items = items.filter((l) => l.staffId === staffId);
    }
    return { success: true, data: items };
  }

  async createLeaveRequest(data: Partial<StaffLeaveRequest>): Promise<ApiResponse<StaffLeaveRequest>> {
    await new Promise((r) => setTimeout(r, 80));
    const newLeave: StaffLeaveRequest = {
      id: `lv-${Date.now()}`,
      staffId: data.staffId || "stf-001",
      staffName: data.staffName || "Staff Member",
      department: data.department || "Academic Administration",
      leaveType: data.leaveType || "CASUAL",
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      endDate: data.endDate || new Date().toISOString().split("T")[0],
      totalDays: data.totalDays || 1,
      reason: data.reason || "Personal circumstances.",
      status: "PENDING",
      requestedAt: new Date().toISOString().split("T")[0],
    };

    this.leaves.unshift(newLeave);
    return { success: true, data: newLeave };
  }

  async approveLeave(leaveId: string, reviewerName = "Registrar Office", remarks?: string): Promise<ApiResponse<StaffLeaveRequest>> {
    await new Promise((r) => setTimeout(r, 60));
    const target = this.leaves.find((l) => l.id === leaveId);
    if (!target) throw new Error("Leave request not found");
    target.status = "APPROVED";
    target.reviewedBy = reviewerName;
    target.reviewedAt = new Date().toISOString().split("T")[0];
    if (remarks) target.reviewRemarks = remarks;
    return { success: true, data: target };
  }

  async rejectLeave(leaveId: string, reviewerName = "Registrar Office", remarks?: string): Promise<ApiResponse<StaffLeaveRequest>> {
    await new Promise((r) => setTimeout(r, 60));
    const target = this.leaves.find((l) => l.id === leaveId);
    if (!target) throw new Error("Leave request not found");
    target.status = "REJECTED";
    target.reviewedBy = reviewerName;
    target.reviewedAt = new Date().toISOString().split("T")[0];
    if (remarks) target.reviewRemarks = remarks;
    return { success: true, data: target };
  }
}

export const dedicatedStaffService = new DedicatedStaffService();
export const staffService = dedicatedStaffService;
