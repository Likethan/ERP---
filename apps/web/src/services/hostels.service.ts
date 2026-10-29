/**
 * CampusOS Hostels Service
 * API Contract:
 * GET  /api/v1/residential/hostels
 * GET  /api/v1/residential/hostels/:id
 * POST /api/v1/residential/hostels
 * PUT  /api/v1/residential/hostels/:id
 */

import { ApiResponse, Hostel, HostelStatus, HostelType } from "@campusos/types";
import { MOCK_HOSTELS } from "@/mocks/infrastructure.mock";
import { calculateHostelOccupancy } from "./infrastructure-calculator";
import { apiFetch } from "@/lib/api-client";

class HostelsService {
  private hostels: Hostel[] = JSON.parse(JSON.stringify(MOCK_HOSTELS));

  async listHostels(filters?: {
    campusId?: string;
    type?: HostelType | string;
    status?: HostelStatus | string;
    gender?: string;
    search?: string;
  }): Promise<ApiResponse<Hostel[]>> {
    try {
      const params = new URLSearchParams();
      if (filters?.campusId && filters.campusId !== "ALL") params.append("campus_id", filters.campusId);
      if (filters?.status && filters.status !== "ALL") params.append("status", filters.status);
      const qs = params.toString() ? `?${params.toString()}` : "";

      const res = await apiFetch<any[]>(`/api/v1/residential/hostels${qs}`);
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        let items: Hostel[] = res.data.map((h: any) => ({
          id: h.id,
          name: h.name,
          code: h.code,
          campusId: h.campus_id || "cmp-main-01",
          campusName: "Main Engineering Campus",
          type: (h.hostel_type as HostelType) || HostelType.BOYS,
          gender: h.gender || "BOYS",
          wardenName: "Residential Warden",
          wardenPhone: h.contact_phone || "+91 94480 00000",
          wardenEmail: h.contact_email || "warden@campusos.edu",
          totalBlocks: 2,
          totalRooms: 50,
          totalBeds: 100,
          occupiedBeds: 0,
          availableBeds: 100,
          occupancyPercentage: 0,
          status: (h.status as HostelStatus) || HostelStatus.ACTIVE,
          createdAt: h.created_at,
          updatedAt: h.updated_at,
        }));

        if (filters?.type && filters.type !== "ALL") {
          items = items.filter((h) => h.type === filters.type);
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
              h.campusName.toLowerCase().includes(q),
          );
        }
        return { success: true, data: items };
      }
    } catch {
      // Gracefully fall back to local store
    }

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
          h.campusName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getHostelById(id: string): Promise<ApiResponse<Hostel | null>> {
    try {
      const res = await apiFetch<any>(`/api/v1/residential/hostels/${id}`);
      if (res && res.data) {
        const h = res.data;
        const hostel: Hostel = {
          id: h.id,
          name: h.name,
          code: h.code,
          campusId: h.campus_id || "cmp-main-01",
          campusName: "Main Engineering Campus",
          type: (h.hostel_type as HostelType) || HostelType.BOYS,
          gender: h.gender || "BOYS",
          wardenName: "Residential Warden",
          wardenPhone: h.contact_phone || "+91 94480 00000",
          wardenEmail: h.contact_email || "warden@campusos.edu",
          totalBlocks: 2,
          totalRooms: 50,
          totalBeds: 100,
          occupiedBeds: 0,
          availableBeds: 100,
          occupancyPercentage: 0,
          status: (h.status as HostelStatus) || HostelStatus.ACTIVE,
          createdAt: h.created_at,
          updatedAt: h.updated_at,
        };
        return { success: true, data: hostel };
      }
    } catch {
      // Fallback to local store
    }

    const hostel =
      this.hostels.find((h) => h.id === id || h.code === id) || null;
    return { success: true, data: hostel };
  }

  async createHostel(payload: Partial<Hostel>): Promise<ApiResponse<Hostel>> {
    const totalBeds = payload.totalBeds || 100;
    const occupiedBeds = payload.occupiedBeds || 0;
    const availableBeds = Math.max(0, totalBeds - occupiedBeds);
    const occupancyPercentage = calculateHostelOccupancy(
      occupiedBeds,
      totalBeds,
    );

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

    try {
      const res = await apiFetch<any>("/api/v1/residential/hostels", {
        method: "POST",
        body: JSON.stringify({
          name: newHostel.name,
          code: newHostel.code,
          campus_id: newHostel.campusId,
          hostel_type: newHostel.type,
          gender: newHostel.gender === "BOYS" ? "MALE" : newHostel.gender === "GIRLS" ? "FEMALE" : "CO_ED",
          status: newHostel.status,
          contact_phone: newHostel.wardenPhone,
          contact_email: newHostel.wardenEmail,
        }),
      });
      if (res && res.data) {
        newHostel.id = res.data.id;
      }
    } catch {
      // Persisted to local store
    }

    this.hostels.unshift(newHostel);
    return { success: true, data: newHostel };
  }

  async updateHostel(
    id: string,
    updates: Partial<Hostel>,
  ): Promise<ApiResponse<Hostel | null>> {
    try {
      await apiFetch<any>(`/api/v1/residential/hostels/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          name: updates.name,
          hostel_type: updates.type,
          gender: updates.gender === "BOYS" ? "MALE" : updates.gender === "GIRLS" ? "FEMALE" : "CO_ED",
          status: updates.status,
          contact_phone: updates.wardenPhone,
          contact_email: updates.wardenEmail,
        }),
      });
    } catch {
      // Handled via local update
    }

    const index = this.hostels.findIndex((h) => h.id === id);
    if (index === -1) return { success: false, data: null };

    const current = this.hostels[index];
    const totalBeds = updates.totalBeds ?? current.totalBeds;
    const occupiedBeds = updates.occupiedBeds ?? current.occupiedBeds;
    const availableBeds = Math.max(0, totalBeds - occupiedBeds);
    const occupancyPercentage = calculateHostelOccupancy(
      occupiedBeds,
      totalBeds,
    );

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
