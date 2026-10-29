/**
 * CampusOS Transport Routes Service
 * API Contract:
 * GET  /api/v1/transport/routes
 * GET  /api/v1/transport/routes/:id
 * POST /api/v1/transport/routes
 * PUT  /api/v1/transport/routes/:id
 */

import { ApiResponse, TransportRoute, RouteStatus } from "@campusos/types";
import { MOCK_TRANSPORT_ROUTES } from "@/mocks/infrastructure.mock";
import { calculateRouteUtilization } from "./infrastructure-calculator";

class TransportRoutesService {
  private routes: TransportRoute[] = JSON.parse(
    JSON.stringify(MOCK_TRANSPORT_ROUTES),
  );

  async listRoutes(filters?: {
    campusId?: string;
    status?: RouteStatus | string;
    search?: string;
  }): Promise<ApiResponse<TransportRoute[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.routes];

    if (filters?.campusId && filters.campusId !== "ALL") {
      items = items.filter((r) => r.campusId === filters.campusId);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((r) => r.status === filters.status);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.routeCode.toLowerCase().includes(q) ||
          r.startPoint.toLowerCase().includes(q) ||
          r.endPoint.toLowerCase().includes(q) ||
          r.vehicleNumber?.toLowerCase().includes(q) ||
          r.driverName?.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getRouteById(id: string): Promise<ApiResponse<TransportRoute | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const route =
      this.routes.find((r) => r.id === id || r.routeCode === id) || null;
    return { success: true, data: route };
  }

  async createRoute(
    payload: Partial<TransportRoute>,
  ): Promise<ApiResponse<TransportRoute>> {
    await new Promise((r) => setTimeout(r, 50));
    const capacity = payload.capacity || 52;
    const allocated = payload.allocatedStudents || 0;
    const utilization = calculateRouteUtilization(allocated, capacity);

    const newRoute: TransportRoute = {
      id: `route-${Date.now().toString(36)}`,
      routeCode: payload.routeCode || `R-0${this.routes.length + 1}`,
      name: payload.name || "New Transport Route",
      campusId: payload.campusId || "cmp-main-01",
      campusName: payload.campusName || "Main Engineering Campus",
      startPoint: payload.startPoint || "City Center",
      endPoint: payload.endPoint || "Campus Gate 2",
      stopsCount: payload.stopsCount || 0,
      stops: payload.stops || [],
      vehicleId: payload.vehicleId || null,
      vehicleNumber: payload.vehicleNumber || null,
      driverId: payload.driverId || null,
      driverName: payload.driverName || null,
      driverPhone: payload.driverPhone || null,
      capacity,
      allocatedStudents: allocated,
      utilizationPercentage: utilization,
      morningDeparture: payload.morningDeparture || "07:15 AM",
      eveningReturn: payload.eveningReturn || "05:15 PM",
      status: (payload.status as RouteStatus) || RouteStatus.ACTIVE,
    };

    this.routes.push(newRoute);
    return { success: true, data: newRoute };
  }

  async getStopsByRouteId(routeId: string) {
    const { transportStopsService } = await import("./transport-stops.service");
    return transportStopsService.listStops({ routeId });
  }
}

export const transportRoutesService = new TransportRoutesService();
