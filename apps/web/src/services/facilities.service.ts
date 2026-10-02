/**
 * CampusOS Facilities Service
 * API Contract:
 * GET  /api/v1/facilities
 * GET  /api/v1/facilities/:id
 * POST /api/v1/facilities
 * PUT  /api/v1/facilities/:id
 */

import { ApiResponse, Facility, FacilityStatus, FacilityType } from "@campusos/types";
import { MOCK_FACILITIES } from "@/mocks/infrastructure.mock";

class FacilitiesService {
  private facilities: Facility[] = JSON.parse(JSON.stringify(MOCK_FACILITIES));

  async listFacilities(filters?: {
    campusId?: string;
    type?: FacilityType | string;
    status?: FacilityStatus | string;
    building?: string;
    search?: string;
  }): Promise<ApiResponse<Facility[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.facilities];

    if (filters?.campusId && filters.campusId !== "ALL") {
      items = items.filter((f) => f.campusId === filters.campusId);
    }
    if (filters?.type && filters.type !== "ALL") {
      items = items.filter((f) => f.type === filters.type);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((f) => f.status === filters.status);
    }
    if (filters?.building && filters.building !== "ALL") {
      items = items.filter((f) => f.building.toLowerCase().includes(filters.building!.toLowerCase()));
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.code.toLowerCase().includes(q) ||
          f.building.toLowerCase().includes(q) ||
          f.managerName.toLowerCase().includes(q) ||
          f.type.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getFacilityById(id: string): Promise<ApiResponse<Facility | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const facility = this.facilities.find((f) => f.id === id || f.code === id) || null;
    return { success: true, data: facility };
  }

  async createFacility(payload: Partial<Facility>): Promise<ApiResponse<Facility>> {
    await new Promise((r) => setTimeout(r, 50));
    const newFacility: Facility = {
      id: `fac-${Date.now().toString(36)}`,
      name: payload.name || "New Campus Facility",
      code: payload.code || `FAC-${Date.now().toString().slice(-4)}`,
      campusId: payload.campusId || "cmp-main-01",
      campusName: payload.campusName || "Main Engineering Campus",
      building: payload.building || "Academic Block A",
      floor: payload.floor || 1,
      type: (payload.type as FacilityType) || FacilityType.LABORATORY,
      capacity: payload.capacity || 60,
      status: (payload.status as FacilityStatus) || FacilityStatus.ACTIVE,
      managerName: payload.managerName || "Estate Officer",
      managerEmail: payload.managerEmail || "facilities@campusos.edu",
      managerPhone: payload.managerPhone || "+91 94480 00000",
      description: payload.description || "",
      equipment: payload.equipment || [],
      connectedEventsCount: 0,
      activeWorkOrdersCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.facilities.push(newFacility);
    return { success: true, data: newFacility };
  }

  async updateFacility(id: string, updates: Partial<Facility>): Promise<ApiResponse<Facility | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const index = this.facilities.findIndex((f) => f.id === id);
    if (index === -1) return { success: false, data: null };

    const updated: Facility = {
      ...this.facilities[index],
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    this.facilities[index] = updated;
    return { success: true, data: updated };
  }
}

export const facilitiesService = new FacilitiesService();
