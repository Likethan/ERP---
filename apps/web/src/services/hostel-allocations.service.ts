/**
 * CampusOS Hostel Allocations Service
 * API Contract:
 * GET  /api/v1/infrastructure/allocations
 * GET  /api/v1/infrastructure/allocations/:id
 * POST /api/v1/infrastructure/allocations
 * PUT  /api/v1/infrastructure/allocations/:id
 * POST /api/v1/infrastructure/allocations/:id/transfer
 * POST /api/v1/infrastructure/allocations/:id/vacate
 */

import {
  ApiResponse,
  HostelAllocation,
  AllocationStatus,
  BedStatus,
} from "@campusos/types";
import { MOCK_HOSTEL_ALLOCATIONS } from "@/mocks/infrastructure.mock";
import { hostelRoomsService } from "./hostel-rooms.service";

class HostelAllocationsService {
  private allocations: HostelAllocation[] = JSON.parse(
    JSON.stringify(MOCK_HOSTEL_ALLOCATIONS),
  );

  async listHostelAllocations(filters?: {
    hostelId?: string;
    status?: AllocationStatus | string;
    studentId?: string;
    programCode?: string;
    year?: number | string;
    search?: string;
  }): Promise<ApiResponse<HostelAllocation[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.allocations];

    if (filters?.hostelId && filters.hostelId !== "ALL") {
      items = items.filter((a) => a.hostelId === filters.hostelId);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((a) => a.status === filters.status);
    }
    if (filters?.studentId) {
      items = items.filter((a) => a.studentId === filters.studentId);
    }
    if (filters?.programCode && filters.programCode !== "ALL") {
      items = items.filter((a) => a.programCode === filters.programCode);
    }
    if (filters?.year && filters.year !== "ALL") {
      const yr = Number(filters.year);
      items = items.filter((a) => a.year === yr);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (a) =>
          a.studentName.toLowerCase().includes(q) ||
          a.registerNumber.toLowerCase().includes(q) ||
          a.roomNumber.toLowerCase().includes(q) ||
          a.hostelName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getAllocationById(
    id: string,
  ): Promise<ApiResponse<HostelAllocation | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const alloc = this.allocations.find((a) => a.id === id) || null;
    return { success: true, data: alloc };
  }

  async createHostelAllocation(payload: {
    studentId: string;
    studentName: string;
    registerNumber: string;
    programCode: string;
    programName: string;
    departmentCode: string;
    year: number;
    semester: number;
    hostelId: string;
    hostelName: string;
    blockId: string;
    blockName: string;
    floor: number;
    roomId: string;
    roomNumber: string;
    bedId: string;
    bedNumber: string;
    allocatedDate?: string;
    expectedEndDate?: string;
    remarks?: string;
    allocatedBy?: string;
  }): Promise<ApiResponse<HostelAllocation>> {
    await new Promise((r) => setTimeout(r, 60));

    const newAlloc: HostelAllocation = {
      id: `alloc-${Date.now().toString(36)}`,
      studentId: payload.studentId,
      studentName: payload.studentName,
      registerNumber: payload.registerNumber,
      programCode: payload.programCode,
      programName: payload.programName,
      departmentCode: payload.departmentCode,
      year: payload.year,
      semester: payload.semester,
      hostelId: payload.hostelId,
      hostelName: payload.hostelName,
      blockId: payload.blockId,
      blockName: payload.blockName,
      floor: payload.floor,
      roomId: payload.roomId,
      roomNumber: payload.roomNumber,
      bedId: payload.bedId,
      bedNumber: payload.bedNumber,
      allocatedDate:
        payload.allocatedDate || new Date().toISOString().split("T")[0],
      expectedEndDate: payload.expectedEndDate || "2027-05-30",
      status: AllocationStatus.ALLOCATED,
      financeRefId: `INV-HOSTEL-${Date.now().toString().slice(-4)}`,
      remarks: payload.remarks || "Fresh allocation confirmed",
      history: [
        {
          id: `h-${Date.now().toString(36)}`,
          action: "Allocation Created",
          description: `Allocated Room ${payload.roomNumber} ${payload.bedNumber} in ${payload.hostelName}`,
          timestamp: new Date().toISOString(),
          performedBy: payload.allocatedBy || "Hostel Warden",
        },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Update bed status in room inventory
    await hostelRoomsService.updateBedStatus(
      payload.roomId,
      payload.bedId,
      BedStatus.ALLOCATED,
      {
        studentId: payload.studentId,
        studentName: payload.studentName,
        studentRollNumber: payload.registerNumber,
      },
    );

    this.allocations.unshift(newAlloc);
    return { success: true, data: newAlloc };
  }

  async transferHostelAllocation(
    id: string,
    transferTo: {
      hostelId: string;
      hostelName: string;
      blockId: string;
      blockName: string;
      floor: number;
      roomId: string;
      roomNumber: string;
      bedId: string;
      bedNumber: string;
      reason: string;
      transferredBy?: string;
    },
  ): Promise<ApiResponse<HostelAllocation | null>> {
    await new Promise((r) => setTimeout(r, 60));
    const alloc = this.allocations.find((a) => a.id === id);
    if (!alloc) return { success: false, data: null };

    // Release old bed
    await hostelRoomsService.updateBedStatus(
      alloc.roomId,
      alloc.bedId,
      BedStatus.AVAILABLE,
    );

    // Book new bed
    await hostelRoomsService.updateBedStatus(
      transferTo.roomId,
      transferTo.bedId,
      BedStatus.ALLOCATED,
      {
        studentId: alloc.studentId,
        studentName: alloc.studentName,
        studentRollNumber: alloc.registerNumber,
      },
    );

    const previousLocation = `${alloc.hostelName}, Room ${alloc.roomNumber} ${alloc.bedNumber}`;
    alloc.hostelId = transferTo.hostelId;
    alloc.hostelName = transferTo.hostelName;
    alloc.blockId = transferTo.blockId;
    alloc.blockName = transferTo.blockName;
    alloc.floor = transferTo.floor;
    alloc.roomId = transferTo.roomId;
    alloc.roomNumber = transferTo.roomNumber;
    alloc.bedId = transferTo.bedId;
    alloc.bedNumber = transferTo.bedNumber;
    alloc.status = AllocationStatus.TRANSFERRED;
    alloc.updatedAt = new Date().toISOString();

    alloc.history = alloc.history || [];
    alloc.history.push({
      id: `h-${Date.now().toString(36)}`,
      action: "Room Transferred",
      description: `Transferred from ${previousLocation} to ${transferTo.hostelName} Room ${transferTo.roomNumber}. Reason: ${transferTo.reason}`,
      timestamp: new Date().toISOString(),
      performedBy: transferTo.transferredBy || "Hostel Warden",
    });

    return { success: true, data: alloc };
  }

  async vacateHostelAllocation(
    id: string,
    reason?: string,
    vacatedBy?: string,
  ): Promise<ApiResponse<HostelAllocation | null>> {
    await new Promise((r) => setTimeout(r, 60));
    const alloc = this.allocations.find((a) => a.id === id);
    if (!alloc) return { success: false, data: null };

    // Free the bed
    await hostelRoomsService.updateBedStatus(
      alloc.roomId,
      alloc.bedId,
      BedStatus.AVAILABLE,
    );

    alloc.status = AllocationStatus.VACATED;
    alloc.vacatedDate = new Date().toISOString().split("T")[0];
    alloc.updatedAt = new Date().toISOString();

    alloc.history = alloc.history || [];
    alloc.history.push({
      id: `h-${Date.now().toString(36)}`,
      action: "Vacated",
      description: `Student vacated room ${alloc.roomNumber}. Reason: ${reason || "Graduation / Withdrawal"}. No-dues cleared.`,
      timestamp: new Date().toISOString(),
      performedBy: vacatedBy || "Hostel Warden",
    });

    return { success: true, data: alloc };
  }
}

export const hostelAllocationsService = new HostelAllocationsService();
