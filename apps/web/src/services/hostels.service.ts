/**
 * CampusOS Hostels Service
 * API Contract:
 * GET  /api/v1/infrastructure/hostels
 * GET  /api/v1/infrastructure/hostels/:id
 * POST /api/v1/infrastructure/hostels
 * PUT  /api/v1/infrastructure/hostels/:id
 */

import { ApiResponse, Hostel, HostelStatus, HostelType } from "@campusos/types";
import { MOCK_HOSTELS } from "@/mocks/infrastructure.mock";
import { calculateHostelOccupancy } from "./infrastructure-calculator";

class HostelsService {
  private hostels: Hostel[] = JSON.parse(JSON.stringify(MOCK_HOSTELS));

  async listHostels(filters?: {
    campusId?: string;
    type?: HostelType | string;
    status?: HostelStatus | string;
    gender?: string;
    search?: string;
  }): Promise<ApiResponse<Hostel[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.hostels];

    if (filters?.campusId && filters.campusId !== "ALL") {
      items = items.filter((h) => h.campusId === filters.campusId);
    }
    if (filters?.type && filters.type !== "ALL") {
      items = items.filter((h) => h.type === filters.type);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((h) => h.status === filters.status);
    }
    if (filters?.gender && filters.gender !== "ALL") {
      items = items.filter((h) => h.gender === filters.gender);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (h) =>
          h.name.toLowerCase().includes(q) ||
          h.code.toLowerCase().includes(q) ||
          h.wardenName.toLowerCase().includes(q) ||
          h.campusName.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getHostelById(id: string): Promise<ApiResponse<Hostel | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const hostel = this.hostels.find((h) => h.id === id || h.code === id) || null;
    return { success: true, data: hostel };
  }

  async createHostel(payload: Partial<Hostel>): Promise<ApiResponse<Hostel>> {
    await new Promise((r) => setTimeout(r, 60));
    const totalBeds = payload.totalBeds || 100;
    const occupiedBeds = payload.occupiedBeds || 0;
    const availableBeds = Math.max(0, totalBeds - occupiedBeds);
    const occupancyPercentage = calculateHostelOccupancy(occupiedBeds, totalBeds);

    const newHostel: Hostel = {
      id: `hst-${Date.now().toString(36)}`,
      name: payload.name || "New Hall of Residence",
      code: payload.code || `HOSTEL-${Date.now().toString().slice(-4)}`,
      campusId: payload.campusId || "cmp-main-01",
      campusName: payload.campusName || "Main Engineering Campus",
      type: (payload.type as HostelType) || HostelType.BOYS,
      gender: payload.gender || "BOYS",
      wardenName: payload.wardenName || "Assigned Warden",
      wardenPhone: payload.wardenPhone || "+91 94480 00000",
      wardenEmail: payload.wardenEmail || "warden@campusos.edu",
      totalBlocks: payload.totalBlocks || 1,
      totalRooms: payload.totalRooms || 50,
      totalBeds,
      occupiedBeds,
      availableBeds,
      occupancyPercentage,
      status: (payload.status as HostelStatus) || HostelStatus.ACTIVE,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.hostels.unshift(newHostel);
    return { success: true, data: newHostel };
  }

  async updateHostel(id: string, updates: Partial<Hostel>): Promise<ApiResponse<Hostel | null>> {
    await new Promise((r) => setTimeout(r, 60));
    const index = this.hostels.findIndex((h) => h.id === id);
    if (index === -1) return { success: false, data: null };

    const current = this.hostels[index];
    const totalBeds = updates.totalBeds ?? current.totalBeds;
    const occupiedBeds = updates.occupiedBeds ?? current.occupiedBeds;
    const availableBeds = Math.max(0, totalBeds - occupiedBeds);
    const occupancyPercentage = calculateHostelOccupancy(occupiedBeds, totalBeds);

    const updated: Hostel = {
      ...current,
      ...updates,
      totalBeds,
      occupiedBeds,
      availableBeds,
      occupancyPercentage,
      updatedAt: new Date().toISOString(),
    };

    this.hostels[index] = updated;
    return { success: true, data: updated };
  }
}

export const hostelsService = new HostelsService();
