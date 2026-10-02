/**
 * CampusOS Hostel Complaints Service
 * API Contract:
 * GET  /api/v1/infrastructure/complaints
 * GET  /api/v1/infrastructure/complaints/:id
 * POST /api/v1/infrastructure/complaints
 * PUT  /api/v1/infrastructure/complaints/:id/status
 * POST /api/v1/infrastructure/complaints/:id/assign
 */

import { ApiResponse, HostelComplaint, ComplaintStatus, ComplaintPriority, ComplaintCategory } from "@campusos/types";
import { MOCK_HOSTEL_COMPLAINTS } from "@/mocks/infrastructure.mock";

class HostelComplaintsService {
  private complaints: HostelComplaint[] = JSON.parse(JSON.stringify(MOCK_HOSTEL_COMPLAINTS));

  async listHostelComplaints(filters?: {
    hostelId?: string;
    studentId?: string;
    category?: ComplaintCategory | string;
    status?: ComplaintStatus | string;
    priority?: ComplaintPriority | string;
    search?: string;
  }): Promise<ApiResponse<HostelComplaint[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.complaints];

    if (filters?.hostelId && filters.hostelId !== "ALL") {
      items = items.filter((c) => c.hostelId === filters.hostelId);
    }
    if (filters?.studentId) {
      items = items.filter((c) => c.studentId === filters.studentId);
    }
    if (filters?.category && filters.category !== "ALL") {
      items = items.filter((c) => c.category === filters.category);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((c) => c.status === filters.status);
    }
    if (filters?.priority && filters.priority !== "ALL") {
      items = items.filter((c) => c.priority === filters.priority);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.ticketNumber.toLowerCase().includes(q) ||
          c.studentName.toLowerCase().includes(q) ||
          c.roomNumber.toLowerCase().includes(q) ||
          c.hostelName.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getHostelComplaintById(id: string): Promise<ApiResponse<HostelComplaint | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const comp = this.complaints.find((c) => c.id === id || c.ticketNumber === id) || null;
    return { success: true, data: comp };
  }

  async createHostelComplaint(payload: {
    studentId: string;
    studentName: string;
    registerNumber: string;
    hostelId: string;
    hostelName: string;
    roomNumber: string;
    category: ComplaintCategory;
    priority: ComplaintPriority;
    title: string;
    description: string;
  }): Promise<ApiResponse<HostelComplaint>> {
    await new Promise((r) => setTimeout(r, 60));

    const targetSlaHours = payload.priority === ComplaintPriority.CRITICAL ? 4 : payload.priority === ComplaintPriority.HIGH ? 12 : 24;

    const newComplaint: HostelComplaint = {
      id: `cmp-${Date.now().toString(36)}`,
      ticketNumber: `CMP-HST-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
      ...payload,
      status: ComplaintStatus.OPEN,
      slaTargetHours: targetSlaHours,
      slaBreached: false,
      resolutionNotes: null,
      activityTimeline: [
        {
          id: `act-${Date.now().toString(36)}`,
          action: "Complaint Logged",
          status: ComplaintStatus.OPEN,
          timestamp: new Date().toISOString(),
          actor: payload.studentName,
          notes: "Ticket created via student portal",
        },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.complaints.unshift(newComplaint);
    return { success: true, data: newComplaint };
  }

  async updateComplaintStatus(
    id: string,
    newStatus: ComplaintStatus,
    actorName: string,
    notes?: string
  ): Promise<ApiResponse<HostelComplaint | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const comp = this.complaints.find((c) => c.id === id);
    if (!comp) return { success: false, data: null };

    comp.status = newStatus;
    comp.updatedAt = new Date().toISOString();
    if (newStatus === ComplaintStatus.RESOLVED) {
      comp.resolvedAt = new Date().toISOString();
      if (notes) comp.resolutionNotes = notes;
    } else if (newStatus === ComplaintStatus.CLOSED) {
      comp.closedAt = new Date().toISOString();
    }

    comp.activityTimeline = comp.activityTimeline || [];
    comp.activityTimeline.push({
      id: `act-${Date.now().toString(36)}`,
      action: `Status Changed to ${newStatus}`,
      status: newStatus,
      timestamp: new Date().toISOString(),
      actor: actorName,
      notes,
    });

    return { success: true, data: comp };
  }

  async assignComplaint(
    id: string,
    staffId: string,
    staffName: string,
    assignedBy: string
  ): Promise<ApiResponse<HostelComplaint | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const comp = this.complaints.find((c) => c.id === id);
    if (!comp) return { success: false, data: null };

    comp.assignedStaffId = staffId;
    comp.assignedStaffName = staffName;
    comp.status = ComplaintStatus.ASSIGNED;
    comp.updatedAt = new Date().toISOString();

    comp.activityTimeline = comp.activityTimeline || [];
    comp.activityTimeline.push({
      id: `act-${Date.now().toString(36)}`,
      action: "Technician Assigned",
      status: ComplaintStatus.ASSIGNED,
      timestamp: new Date().toISOString(),
      actor: assignedBy,
      notes: `Assigned to ${staffName}`,
    });

    return { success: true, data: comp };
  }

  // Aliases
  async listComplaints(filters?: any) {
    return this.listHostelComplaints(filters);
  }

  async getComplaintById(id: string) {
    return this.getHostelComplaintById(id);
  }

  async createComplaint(payload: any) {
    return this.createHostelComplaint({
      registerNumber: payload.registerNumber || "REG-01",
      ...payload,
    });
  }
}

export const hostelComplaintsService = new HostelComplaintsService();
