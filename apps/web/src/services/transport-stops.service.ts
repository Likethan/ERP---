/**
 * CampusOS Transport Stops Service
 * API Contract:
 * GET  /api/v1/transport/stops
 * GET  /api/v1/transport/stops/:id
 * POST /api/v1/transport/stops
 * PUT  /api/v1/transport/stops/:id
 */

import { ApiResponse, TransportStop, StopStatus } from "@campusos/types";
import { MOCK_TRANSPORT_STOPS } from "@/mocks/infrastructure.mock";

class TransportStopsService {
  private stops: TransportStop[] = JSON.parse(JSON.stringify(MOCK_TRANSPORT_STOPS));

  async listStops(filters?: {
    routeId?: string;
    status?: StopStatus | string;
    search?: string;
  }): Promise<ApiResponse<TransportStop[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.stops];

    if (filters?.routeId && filters.routeId !== "ALL") {
      items = items.filter((s) => s.routeId === filters.routeId || s.routeCode === filters.routeId);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((s) => s.status === filters.status);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.code.toLowerCase().includes(q) ||
          s.routeName.toLowerCase().includes(q) ||
          s.routeCode.toLowerCase().includes(q) ||
          s.landmark?.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getStopById(id: string): Promise<ApiResponse<TransportStop | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const stop = this.stops.find((s) => s.id === id || s.code === id) || null;
    return { success: true, data: stop };
  }

  async createStop(payload: Partial<TransportStop>): Promise<ApiResponse<TransportStop>> {
    await new Promise((r) => setTimeout(r, 50));
    const newStop: TransportStop = {
      id: `stp-${Date.now().toString(36)}`,
      routeId: payload.routeId || "route-01",
      routeName: payload.routeName || "North City Express",
      routeCode: payload.routeCode || "R-01",
      name: payload.name || "New Intermediate Stop",
      code: payload.code || `STP-${Date.now().toString().slice(-4)}`,
      sequence: payload.sequence || this.stops.length + 1,
      pickupTime: payload.pickupTime || "07:30 AM",
      dropTime: payload.dropTime || "05:30 PM",
      landmark: payload.landmark || "Public Landmark",
      studentCount: payload.studentCount || 0,
      status: (payload.status as StopStatus) || StopStatus.ACTIVE,
    };

    this.stops.push(newStop);
    return { success: true, data: newStop };
  }
}

export const transportStopsService = new TransportStopsService();
