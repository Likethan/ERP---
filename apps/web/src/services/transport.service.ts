/**
 * CampusOS Unified Transport Service
 * API Contract:
 * GET  /api/v1/transport/dashboard
 */

import { ApiResponse } from "@campusos/types";
import { transportRoutesService } from "./transport-routes.service";
import { transportStopsService } from "./transport-stops.service";
import { transportVehiclesService } from "./transport-vehicles.service";
import { transportDriversService } from "./transport-drivers.service";
import { transportAllocationsService } from "./transport-allocations.service";

export interface TransportDashboardData {
  activeRoutesCount: number;
  totalStopsCount: number;
  activeVehiclesCount: number;
  vehiclesUnderMaintenanceCount: number;
  activeDriversCount: number;
  studentsAllocatedCount: number;
  routeCapacityUtilization: number;
  unassignedStudentsCount: number;
  upcomingVehicleMaintenanceCount: number;
}

class TransportService {
  async getTransportDashboard(): Promise<ApiResponse<TransportDashboardData>> {
    await new Promise((r) => setTimeout(r, 40));

    const routesRes = await transportRoutesService.listRoutes();
    const stopsRes = await transportStopsService.listStops();
    const vehiclesRes = await transportVehiclesService.listVehicles();
    const driversRes = await transportDriversService.listDrivers();
    const allocationsRes = await transportAllocationsService.listTransportAllocations();

    const routes = routesRes.data || [];
    const stops = stopsRes.data || [];
    const vehicles = vehiclesRes.data || [];
    const drivers = driversRes.data || [];
    const allocations = allocationsRes.data || [];

    const activeRoutes = routes.filter((r) => r.status === "ACTIVE").length;
    const activeVehicles = vehicles.filter((v) => v.status === "ACTIVE").length;
    const maintVehicles = vehicles.filter((v) => v.status === "MAINTENANCE").length;
    const activeDrivers = drivers.filter((d) => d.status === "ACTIVE").length;
    const allocatedStudents = allocations.filter((a) => a.status === "ACTIVE").length;

    const totalCapacity = routes.reduce((acc, r) => acc + (r.capacity || 0), 0);
    const totalAllocatedInRoutes = routes.reduce((acc, r) => acc + (r.allocatedStudents || 0), 0);
    const avgUtilization = totalCapacity > 0 ? Math.round((totalAllocatedInRoutes / totalCapacity) * 1000) / 10 : 0;

    return {
      success: true,
      data: {
        activeRoutesCount: activeRoutes,
        totalStopsCount: stops.length,
        activeVehiclesCount: activeVehicles,
        vehiclesUnderMaintenanceCount: maintVehicles,
        activeDriversCount: activeDrivers,
        studentsAllocatedCount: allocatedStudents,
        routeCapacityUtilization: avgUtilization,
        unassignedStudentsCount: 6,
        upcomingVehicleMaintenanceCount: 2,
      },
    };
  }
}

export const transportService = new TransportService();
export {
  transportRoutesService,
  transportStopsService,
  transportVehiclesService,
  transportDriversService,
  transportAllocationsService,
};
