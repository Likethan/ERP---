/**
 * CampusOS Hostel Rooms & Beds Service
 * API Contract:
 * GET  /api/v1/infrastructure/rooms
 * GET  /api/v1/infrastructure/rooms/:id
 * POST /api/v1/infrastructure/rooms
 * PUT  /api/v1/infrastructure/rooms/:id
 * POST /api/v1/infrastructure/rooms/:id/beds/:bedId/status
 */

import { ApiResponse, HostelRoom, HostelBed, RoomStatus, BedStatus, RoomType } from "@campusos/types";
import { MOCK_HOSTEL_ROOMS } from "@/mocks/infrastructure.mock";

class HostelRoomsService {
  private rooms: HostelRoom[] = JSON.parse(JSON.stringify(MOCK_HOSTEL_ROOMS));

  async listRooms(filters?: {
    hostelId?: string;
    blockId?: string;
    floor?: number | string;
    roomType?: RoomType | string;
    status?: RoomStatus | string;
    gender?: string;
    search?: string;
  }): Promise<ApiResponse<HostelRoom[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.rooms];

    if (filters?.hostelId && filters.hostelId !== "ALL") {
      items = items.filter((r) => r.hostelId === filters.hostelId);
    }
    if (filters?.blockId && filters.blockId !== "ALL") {
      items = items.filter((r) => r.blockId === filters.blockId || (filters.blockId && r.blockName.includes(filters.blockId)));
    }
    if (filters?.floor && filters.floor !== "ALL") {
      const flr = Number(filters.floor);
      items = items.filter((r) => r.floor === flr);
    }
    if (filters?.roomType && filters.roomType !== "ALL") {
      items = items.filter((r) => r.roomType === filters.roomType);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((r) => r.status === filters.status);
    }
    if (filters?.gender && filters.gender !== "ALL") {
      items = items.filter((r) => r.gender === filters.gender);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (r) =>
          r.roomNumber.toLowerCase().includes(q) ||
          r.hostelName.toLowerCase().includes(q) ||
          r.blockName.toLowerCase().includes(q) ||
          r.beds?.some((b: HostelBed) => b.studentName?.toLowerCase().includes(q) || b.studentRollNumber?.toLowerCase().includes(q))
      );
    }

    return { success: true, data: items };
  }

  async getRoomById(id: string): Promise<ApiResponse<HostelRoom | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const room = this.rooms.find((r) => r.id === id || r.roomNumber === id) || null;
    return { success: true, data: room };
  }

  async updateBedStatus(
    roomId: string,
    bedId: string,
    status: BedStatus,
    studentInfo?: { studentId: string; studentName: string; studentRollNumber: string }
  ): Promise<ApiResponse<HostelRoom | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const room = this.rooms.find((r) => r.id === roomId);
    if (!room || !room.beds) return { success: false, data: null };

    const bed = room.beds.find((b: HostelBed) => b.id === bedId);
    if (!bed) return { success: false, data: null };

    bed.status = status;
    if (status === BedStatus.ALLOCATED && studentInfo) {
      bed.studentId = studentInfo.studentId;
      bed.studentName = studentInfo.studentName;
      bed.studentRollNumber = studentInfo.studentRollNumber;
      bed.allocatedAt = new Date().toISOString();
    } else if (status === BedStatus.AVAILABLE || status === BedStatus.MAINTENANCE || status === BedStatus.BLOCKED) {
      bed.studentId = null;
      bed.studentName = null;
      bed.studentRollNumber = null;
      bed.allocatedAt = null;
    }

    // Recalculate room occupancy
    const occupied = room.beds.filter((b: HostelBed) => b.status === BedStatus.ALLOCATED).length;
    const available = room.beds.filter((b: HostelBed) => b.status === BedStatus.AVAILABLE).length;
    room.occupied = occupied;
    room.available = available;

    if (occupied === 0) {
      room.status = RoomStatus.AVAILABLE;
    } else if (occupied >= room.capacity) {
      room.status = RoomStatus.FULL;
    } else {
      room.status = RoomStatus.PARTIALLY_OCCUPIED;
    }

    return { success: true, data: room };
  }

  async createRoom(payload: Partial<HostelRoom>): Promise<ApiResponse<HostelRoom>> {
    await new Promise((r) => setTimeout(r, 50));
    const capacity = payload.capacity || 2;
    const beds: HostelBed[] = [];
    for (let i = 1; i <= capacity; i++) {
      beds.push({
        id: `bed-${Date.now().toString(36)}-${i}`,
        roomId: `rm-${Date.now().toString(36)}`,
        bedNumber: `Bed ${String.fromCharCode(64 + i)}`,
        status: BedStatus.AVAILABLE,
      });
    }

    const newRoom: HostelRoom = {
      id: `rm-${Date.now().toString(36)}`,
      hostelId: payload.hostelId || "hst-raman",
      hostelName: payload.hostelName || "Sir C. V. Raman Hall",
      blockId: payload.blockId || "blk-raman-a",
      blockName: payload.blockName || "Block A",
      floor: payload.floor || 1,
      roomNumber: payload.roomNumber || "101",
      roomType: payload.roomType || RoomType.DOUBLE,
      capacity,
      occupied: 0,
      available: capacity,
      gender: payload.gender || "MALE",
      status: RoomStatus.AVAILABLE,
      beds,
    };

    this.rooms.push(newRoom);
    return { success: true, data: newRoom };
  }
}

export const hostelRoomsService = new HostelRoomsService();
