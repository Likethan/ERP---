/**
 * CampusOS Hostel Leaves Service
 * API Contract:
 * GET  /api/v1/infrastructure/leaves
 * GET  /api/v1/infrastructure/leaves/:id
 * POST /api/v1/infrastructure/leaves
 * POST /api/v1/infrastructure/leaves/:id/approve
 * POST /api/v1/infrastructure/leaves/:id/reject
 * POST /api/v1/infrastructure/leaves/:id/return
 */

import { ApiResponse, HostelLeave, LeaveStatus } from "@campusos/types";
import { MOCK_HOSTEL_LEAVES } from "@/mocks/infrastructure.mock";

class HostelLeavesService {
  private leaves: HostelLeave[] = JSON.parse(JSON.stringify(MOCK_HOSTEL_LEAVES));

  async listHostelLeaves(filters?: {
    hostelId?: string;
    studentId?: string;
    approvalStatus?: LeaveStatus | string;
    search?: string;
  }): Promise<ApiResponse<HostelLeave[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.leaves];

    if (filters?.hostelId && filters.hostelId !== "ALL") {
      items = items.filter((l) => l.hostelId === filters.hostelId);
    }
    if (filters?.studentId) {
      items = items.filter((l) => l.studentId === filters.studentId);
    }
    if (filters?.approvalStatus && filters.approvalStatus !== "ALL") {
      items = items.filter((l) => l.approvalStatus === filters.approvalStatus);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (l) =>
          l.studentName.toLowerCase().includes(q) ||
          l.registerNumber.toLowerCase().includes(q) ||
          l.reason.toLowerCase().includes(q) ||
          l.destination.toLowerCase().includes(q) ||
          l.roomNumber.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getHostelLeaveById(id: string): Promise<ApiResponse<HostelLeave | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const leave = this.leaves.find((l) => l.id === id) || null;
    return { success: true, data: leave };
  }

  async submitHostelLeave(payload: {
    studentId: string;
    studentName: string;
    registerNumber: string;
    hostelId: string;
    hostelName: string;
    roomNumber: string;
    startDate: string;
    endDate: string;
    reason: string;
    destination: string;
    emergencyContact: {
      name: string;
      relationship: string;
      phone: string;
    };
  }): Promise<ApiResponse<HostelLeave>> {
    await new Promise((r) => setTimeout(r, 60));

    const newLeave: HostelLeave = {
      id: `leave-${Date.now().toString(36)}`,
      ...payload,
      approvalStatus: LeaveStatus.PENDING,
      approvedBy: null,
      approvedAt: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.leaves.unshift(newLeave);
    return { success: true, data: newLeave };
  }

  async approveHostelLeave(id: string, approvedBy: string, remarks?: string): Promise<ApiResponse<HostelLeave | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) return { success: false, data: null };

    leave.approvalStatus = LeaveStatus.APPROVED;
    leave.approvedBy = approvedBy;
    leave.approvedAt = new Date().toISOString();
    if (remarks) leave.remarks = remarks;
    leave.updatedAt = new Date().toISOString();

    return { success: true, data: leave };
  }

  async rejectHostelLeave(id: string, rejectedBy: string, reason: string): Promise<ApiResponse<HostelLeave | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) return { success: false, data: null };

    leave.approvalStatus = LeaveStatus.REJECTED;
    leave.approvedBy = rejectedBy;
    leave.remarks = reason;
    leave.updatedAt = new Date().toISOString();

    return { success: true, data: leave };
  }

  async markLeaveReturn(id: string): Promise<ApiResponse<HostelLeave | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const leave = this.leaves.find((l) => l.id === id);
    if (!leave) return { success: false, data: null };

    leave.approvalStatus = LeaveStatus.COMPLETED;
    leave.updatedAt = new Date().toISOString();

    return { success: true, data: leave };
  }

  // Aliases
  async listLeaves(filters?: any) {
    return this.listHostelLeaves(filters);
  }

  async getLeaveById(id: string) {
    return this.getHostelLeaveById(id);
  }

  async createLeaveRequest(payload: any) {
    const formatted = {
      studentId: payload.studentId,
      studentName: payload.studentName,
      registerNumber: payload.registerNumber || "REG-01",
      hostelId: payload.hostelId,
      hostelName: payload.hostelName,
      roomNumber: payload.roomNumber,
      startDate: payload.startDate,
      endDate: payload.endDate,
      reason: payload.reason,
      destination: payload.destination || "Hometown",
      emergencyContact: payload.emergencyContact || {
        name: "Parent",
        relationship: "Parent",
        phone: payload.parentContactNumber || "+91 99999 00000",
      },
    };
    return this.submitHostelLeave(formatted);
  }

  async approveLeave(id: string, approvedBy: string, remarks?: string) {
    return this.approveHostelLeave(id, approvedBy, remarks);
  }

  async rejectLeave(id: string, rejectedBy: string, reason: string) {
    return this.rejectHostelLeave(id, rejectedBy, reason);
  }
}

export const hostelLeavesService = new HostelLeavesService();
