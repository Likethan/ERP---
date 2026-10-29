/**
 * CampusOS Unified Infrastructure Service Facade
 * API Contract:
 * GET  /api/v1/infrastructure/dashboard
 */

import { ApiResponse, InfrastructureDashboardSummary } from "@campusos/types";
import { hostelsService } from "./hostels.service";
import { hostelRoomsService } from "./hostel-rooms.service";
import { hostelAllocationsService } from "./hostel-allocations.service";
import { hostelLeavesService } from "./hostel-leaves.service";
import { hostelComplaintsService } from "./hostel-complaints.service";
import {
  transportService,
  transportRoutesService,
  transportStopsService,
  transportVehiclesService,
  transportDriversService,
  transportAllocationsService,
} from "./transport.service";
import { facilitiesService } from "./facilities.service";
import { maintenanceService } from "./maintenance.service";
import { infrastructureReportsService } from "./infrastructure-reports.service";
import {
  calculateHostelOccupancy,
  calculateRouteUtilization,
} from "./infrastructure-calculator";

class InfrastructureService {
  async getInfrastructureDashboard(): Promise<
    ApiResponse<InfrastructureDashboardSummary>
  > {
    await new Promise((r) => setTimeout(r, 40));

    const [
      hostelsRes,
      roomsRes,
      complaintsRes,
      routesRes,
      vehiclesRes,
      allocationsRes,
      facilitiesRes,
      maintRes,
    ] = await Promise.all([
      hostelsService.listHostels(),
      hostelRoomsService.listRooms(),
      hostelComplaintsService.listHostelComplaints(),
      transportRoutesService.listRoutes(),
      transportVehiclesService.listVehicles(),
      transportAllocationsService.listTransportAllocations(),
      facilitiesService.listFacilities(),
      maintenanceService.listMaintenanceRequests(),
    ]);

    const hostels = hostelsRes.data || [];
    const rooms = roomsRes.data || [];
    const complaints = complaintsRes.data || [];
    const routes = routesRes.data || [];
    const vehicles = vehiclesRes.data || [];
    const allocations = allocationsRes.data || [];
    const facilities = facilitiesRes.data || [];
    const maint = maintRes.data || [];

    const totalBeds = hostels.reduce((acc, h) => acc + (h.totalBeds || 0), 0);
    const occupiedBeds = hostels.reduce(
      (acc, h) => acc + (h.occupiedBeds || 0),
      0,
    );
    const availableBeds = Math.max(0, totalBeds - occupiedBeds);
    const occupancyPercentage = calculateHostelOccupancy(
      occupiedBeds,
      totalBeds,
    );

    const activeRoutes = routes.filter((r) => r.status === "ACTIVE").length;
    const activeVehicles = vehicles.filter((v) => v.status === "ACTIVE").length;
    const studentsUsingTransport = allocations.filter(
      (a) => a.status === "ACTIVE",
    ).length;

    const openComplaints = complaints.filter(
      (c) => c.status !== "RESOLVED" && c.status !== "CLOSED",
    ).length;
    const openMaintenance = maint.filter(
      (m) =>
        m.status !== "RESOLVED" &&
        m.status !== "CLOSED" &&
        m.status !== "CANCELLED",
    ).length;
    const criticalMaintenance = maint.filter(
      (m) => m.priority === "CRITICAL" && m.status !== "CLOSED",
    ).length;
    const facilitiesAttention = facilities.filter(
      (f) => f.status === "UNDER_MAINTENANCE" || f.status === "INACTIVE",
    ).length;

    return {
      success: true,
      data: {
        totalHostels: hostels.length,
        totalBeds,
        occupiedBeds,
        availableBeds,
        hostelOccupancyPercentage: occupancyPercentage,
        activeTransportRoutes: activeRoutes,
        activeVehicles,
        studentsUsingTransport,
        openComplaints,
        openMaintenanceRequests: openMaintenance,
        criticalMaintenance,
        facilitiesRequiringAttention: facilitiesAttention,
      },
    };
  }

  // Backwards compatibility methods
  async getHostels() {
    return hostelsService.listHostels();
  }

  async getRooms(hostelId?: string) {
    return hostelRoomsService.listRooms({ hostelId });
  }

  async getTransportRoutes() {
    return transportRoutesService.listRoutes();
  }

  async getVehicles() {
    return transportVehiclesService.listVehicles();
  }
}

export const infrastructureService = new InfrastructureService();

export {
  hostelsService,
  hostelRoomsService,
  hostelAllocationsService,
  hostelLeavesService,
  hostelComplaintsService,
  transportService,
  transportRoutesService,
  transportStopsService,
  transportVehiclesService,
  transportDriversService,
  transportAllocationsService,
  facilitiesService,
  maintenanceService,
  infrastructureReportsService,
};
