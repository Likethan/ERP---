/**
 * CampusOS Transport Allocations Service
 * API Contract:
 * GET  /api/v1/transport/allocations
 * GET  /api/v1/transport/allocations/:id
 * POST /api/v1/transport/allocations
 * PUT  /api/v1/transport/allocations/:id
 * DELETE /api/v1/transport/allocations/:id
 */

import {
  ApiResponse,
  TransportAllocation,
  TransportAllocationStatus,
} from "@campusos/types";
import { MOCK_TRANSPORT_ALLOCATIONS } from "@/mocks/infrastructure.mock";

class TransportAllocationsService {
  private allocations: TransportAllocation[] = JSON.parse(
    JSON.stringify(MOCK_TRANSPORT_ALLOCATIONS),
  );

  async listTransportAllocations(filters?: {
    routeId?: string;
    stopId?: string;
    studentId?: string;
    status?: TransportAllocationStatus | string;
    programCode?: string;
    search?: string;
  }): Promise<ApiResponse<TransportAllocation[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.allocations];

    if (filters?.routeId && filters.routeId !== "ALL") {
      items = items.filter(
        (a) => a.routeId === filters.routeId || a.routeCode === filters.routeId,
      );
    }
    if (filters?.stopId && filters.stopId !== "ALL") {
      items = items.filter((a) => a.stopId === filters.stopId);
    }
    if (filters?.studentId) {
      items = items.filter((a) => a.studentId === filters.studentId);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((a) => a.status === filters.status);
    }
    if (filters?.programCode && filters.programCode !== "ALL") {
      items = items.filter((a) => a.programCode === filters.programCode);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (a) =>
          a.studentName.toLowerCase().includes(q) ||
          a.registerNumber.toLowerCase().includes(q) ||
          a.routeName.toLowerCase().includes(q) ||
          a.stopName.toLowerCase().includes(q) ||
          a.vehicleNumber.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getAllocationById(
    id: string,
  ): Promise<ApiResponse<TransportAllocation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const alloc = this.allocations.find((a) => a.id === id) || null;
    return { success: true, data: alloc };
  }

  async createTransportAllocation(payload: {
    studentId: string;
    studentName: string;
    registerNumber: string;
    programCode?: string;
    departmentCode?: string;
    routeId: string;
    routeCode?: string;
    routeName?: string;
    stopId: string;
    stopName?: string;
    vehicleId?: string;
    vehicleNumber?: string;
    seatNumber?: string | null;
    feeStatus?: string | null;
    academicYear?: string;
    semester?: number;
    status?: TransportAllocationStatus;
  }): Promise<ApiResponse<TransportAllocation>> {
    await new Promise((r) => setTimeout(r, 60));

    const newAlloc: TransportAllocation = {
      id: `tr-alloc-${Date.now().toString(36)}`,
      studentId: payload.studentId,
      studentName: payload.studentName,
      registerNumber: payload.registerNumber,
      programCode: payload.programCode || "B.TECH",
      departmentCode: payload.departmentCode || "CSE",
      routeId: payload.routeId,
      routeCode: payload.routeCode || "R-01",
      routeName: payload.routeName || "Campus Route",
      stopId: payload.stopId,
      stopName: payload.stopName || "Main Stop",
      vehicleId: payload.vehicleId || "veh-default",
      vehicleNumber: payload.vehicleNumber || "KA-04-E-1892",
      seatNumber: payload.seatNumber || null,
      feeStatus: payload.feeStatus || "PAID",
      academicYear: payload.academicYear || "2026-2027",
      semester: payload.semester || 5,
      allocatedDate: new Date().toISOString().split("T")[0],
      status: payload.status || TransportAllocationStatus.ACTIVE,
      financeFeeRefId: `FEE-TR-2026-${Date.now().toString().slice(-4)}`,
      createdAt: new Date().toISOString(),
    };

    this.allocations.unshift(newAlloc);
    return { success: true, data: newAlloc };
  }

  async cancelTransportAllocation(
    id: string,
    reason?: string,
  ): Promise<ApiResponse<TransportAllocation | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const alloc = this.allocations.find((a) => a.id === id);
    if (!alloc) return { success: false, data: null };

    alloc.status = TransportAllocationStatus.CANCELLED;
    return { success: true, data: alloc };
  }
}

export const transportAllocationsService = new TransportAllocationsService();
