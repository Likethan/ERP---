/**
 * CampusOS Unified Maintenance Service
 * API Contract:
 * GET  /api/v1/maintenance
 * GET  /api/v1/maintenance/:id
 * POST /api/v1/maintenance
 * PUT  /api/v1/maintenance/:id/status
 * POST /api/v1/maintenance/:id/assign
 */

import {
  ApiResponse,
  MaintenanceRequest,
  MaintenanceStatus,
  MaintenancePriority,
} from "@campusos/types";
import { MOCK_MAINTENANCE_REQUESTS } from "@/mocks/infrastructure.mock";
import { calculateMaintenanceSLAStatus } from "./infrastructure-calculator";

class MaintenanceService {
  private requests: MaintenanceRequest[] = JSON.parse(
    JSON.stringify(MOCK_MAINTENANCE_REQUESTS),
  );

  async listMaintenanceRequests(filters?: {
    sourceType?: string;
    category?: string;
    priority?: MaintenancePriority | string;
    status?: MaintenanceStatus | string;
    search?: string;
  }): Promise<ApiResponse<MaintenanceRequest[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.requests];

    if (filters?.sourceType && filters.sourceType !== "ALL") {
      items = items.filter((m) => m.sourceType === filters.sourceType);
    }
    if (filters?.category && filters.category !== "ALL") {
      items = items.filter((m) => m.category === filters.category);
    }
    if (filters?.priority && filters.priority !== "ALL") {
      items = items.filter((m) => m.priority === filters.priority);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((m) => m.status === filters.status);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (m) =>
          m.workOrderNumber.toLowerCase().includes(q) ||
          m.title.toLowerCase().includes(q) ||
          m.assetOrFacilityName.toLowerCase().includes(q) ||
          m.location.toLowerCase().includes(q) ||
          m.assignedTo?.name.toLowerCase().includes(q) ||
          m.reportedBy.name.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getMaintenanceRequestById(
    id: string,
  ): Promise<ApiResponse<MaintenanceRequest | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const req =
      this.requests.find((m) => m.id === id || m.workOrderNumber === id) ||
      null;
    return { success: true, data: req };
  }

  async createMaintenanceRequest(payload: {
    assetOrFacilityId: string;
    assetOrFacilityName: string;
    category:
      | "ELECTRICAL"
      | "PLUMBING"
      | "CIVIL"
      | "HVAC"
      | "IT_EQUIPMENT"
      | "CARPENTRY"
      | "TRANSPORT_VEHICLE"
      | "OTHER";
    sourceType:
      "HOSTEL" | "ROOM" | "FACILITY" | "VEHICLE" | "EQUIPMENT" | "CAMPUS";
    location: string;
    reportedBy: {
      userId: string;
      name: string;
      role: string;
      phone?: string;
    };
    priority: MaintenancePriority;
    title: string;
    description: string;
    estimatedCostInr?: number;
  }): Promise<ApiResponse<MaintenanceRequest>> {
    await new Promise((r) => setTimeout(r, 60));

    const slaCalc = calculateMaintenanceSLAStatus(
      new Date().toISOString(),
      payload.priority,
    );

    const newRequest: MaintenanceRequest = {
      id: `maint-${Date.now().toString(36)}`,
      workOrderNumber: `WO-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
      ...payload,
      estimatedCostInr: payload.estimatedCostInr || 5000,
      actualCostInr: null,
      status: MaintenanceStatus.REQUESTED,
      slaTargetHours: slaCalc.slaTargetHours,
      isSlaBreached: false,
      resolutionSummary: null,
      history: [
        {
          id: `mh-${Date.now().toString(36)}`,
          fromStatus: MaintenanceStatus.REQUESTED,
          toStatus: MaintenanceStatus.REQUESTED,
          timestamp: new Date().toISOString(),
          changedBy: payload.reportedBy.name,
          notes:
            "Work order created and submitted to Estate Engineering queue.",
        },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.requests.unshift(newRequest);
    return { success: true, data: newRequest };
  }

  async assignMaintenanceRequest(
    id: string,
    assignedTo: {
      staffId: string;
      name: string;
      department: string;
      phone: string;
    },
    assignedBy: string = "Estate Supervisor",
  ): Promise<ApiResponse<MaintenanceRequest | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const req = this.requests.find((m) => m.id === id);
    if (!req) return { success: false, data: null };

    const prevStatus = req.status;
    req.assignedTo = assignedTo;
    req.status = MaintenanceStatus.ASSIGNED;
    req.updatedAt = new Date().toISOString();

    req.history = req.history || [];
    req.history.push({
      id: `mh-${Date.now().toString(36)}`,
      fromStatus: prevStatus,
      toStatus: MaintenanceStatus.ASSIGNED,
      timestamp: new Date().toISOString(),
      changedBy: assignedBy,
      notes: `Assigned to ${assignedTo.name} (${assignedTo.department})`,
    });

    return { success: true, data: req };
  }

  async assignMaintenanceTechnician(
    id: string,
    assignedTo: {
      staffId: string;
      name: string;
      department: string;
      phone: string;
    },
    assignedBy?: string,
  ): Promise<ApiResponse<MaintenanceRequest | null>> {
    return this.assignMaintenanceRequest(
      id,
      assignedTo,
      assignedBy || "Estate Supervisor",
    );
  }

  async updateMaintenanceStatus(
    id: string,
    newStatusOrPayload:
      | MaintenanceStatus
      | {
          status: MaintenanceStatus;
          changedBy: string;
          notes?: string;
          resolutionSummary?: string;
          actualCostInr?: number;
        },
    changedBy?: string,
    notes?: string,
    actualCostInr?: number,
  ): Promise<ApiResponse<MaintenanceRequest | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const req = this.requests.find((m) => m.id === id);
    if (!req) return { success: false, data: null };

    let targetStatus: MaintenanceStatus;
    let targetChangedBy = changedBy || "Staff";
    let targetNotes = notes;
    let targetCost = actualCostInr;

    if (typeof newStatusOrPayload === "object") {
      targetStatus = newStatusOrPayload.status;
      targetChangedBy = newStatusOrPayload.changedBy || "Staff";
      targetNotes =
        newStatusOrPayload.resolutionSummary || newStatusOrPayload.notes;
      targetCost = newStatusOrPayload.actualCostInr;
    } else {
      targetStatus = newStatusOrPayload;
    }

    const prevStatus = req.status;
    req.status = targetStatus;
    req.updatedAt = new Date().toISOString();

    if (targetCost !== undefined) {
      req.actualCostInr = targetCost;
    }

    if (targetStatus === MaintenanceStatus.RESOLVED) {
      req.resolvedAt = new Date().toISOString();
      if (targetNotes) req.resolutionSummary = targetNotes;
    } else if (targetStatus === MaintenanceStatus.CLOSED) {
      req.closedAt = new Date().toISOString();
    }

    req.history = req.history || [];
    req.history.push({
      id: `mh-${Date.now().toString(36)}`,
      fromStatus: prevStatus,
      toStatus: targetStatus,
      timestamp: new Date().toISOString(),
      changedBy: targetChangedBy,
      notes: targetNotes,
    });

    return { success: true, data: req };
  }
}

export const maintenanceService = new MaintenanceService();
