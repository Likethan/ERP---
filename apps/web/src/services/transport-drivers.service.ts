/**
 * CampusOS Transport Drivers Service
 * API Contract:
 * GET  /api/v1/transport/drivers
 * GET  /api/v1/transport/drivers/:id
 * POST /api/v1/transport/drivers
 * PUT  /api/v1/transport/drivers/:id
 */

import { ApiResponse, TransportDriver, DriverStatus } from "@campusos/types";
import { MOCK_TRANSPORT_DRIVERS } from "@/mocks/infrastructure.mock";

class TransportDriversService {
  private drivers: TransportDriver[] = JSON.parse(
    JSON.stringify(MOCK_TRANSPORT_DRIVERS),
  );

  async listDrivers(filters?: {
    status?: DriverStatus | string;
    licenseStatus?: string;
    search?: string;
  }): Promise<ApiResponse<TransportDriver[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.drivers];

    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((d) => d.status === filters.status);
    }
    if (filters?.licenseStatus && filters.licenseStatus !== "ALL") {
      items = items.filter((d) => d.licenseStatus === filters.licenseStatus);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.employeeId.toLowerCase().includes(q) ||
          d.phone.includes(q) ||
          d.assignedVehicleNumber?.toLowerCase().includes(q) ||
          d.assignedRouteName?.toLowerCase().includes(q) ||
          d.licenseNumber.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getDriverById(
    id: string,
  ): Promise<ApiResponse<TransportDriver | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const driver =
      this.drivers.find((d) => d.id === id || d.employeeId === id) || null;
    return { success: true, data: driver };
  }

  async createDriver(
    payload: Partial<TransportDriver>,
  ): Promise<ApiResponse<TransportDriver>> {
    await new Promise((r) => setTimeout(r, 50));
    const newDriver: TransportDriver = {
      id: `drv-${Date.now().toString(36)}`,
      name: payload.name || "New Fleet Driver",
      employeeId:
        payload.employeeId || `EMP-TR-${Math.floor(100 + Math.random() * 900)}`,
      phone: payload.phone || "+91 98455 00000",
      email: payload.email || "driver@campusos.edu",
      licenseNumber: payload.licenseNumber || "KA-04-2020-0019284",
      licenseType: payload.licenseType || "Heavy Passenger Vehicle (HPV/HMV)",
      licenseExpiry: payload.licenseExpiry || "2030-12-31",
      licenseStatus: payload.licenseStatus || "VALID",
      assignedVehicleId: payload.assignedVehicleId || null,
      assignedVehicleNumber: payload.assignedVehicleNumber || null,
      assignedRouteId: payload.assignedRouteId || null,
      assignedRouteCode: payload.assignedRouteCode || null,
      assignedRouteName: payload.assignedRouteName || null,
      experienceYears: payload.experienceYears || 5,
      joiningDate:
        payload.joiningDate || new Date().toISOString().split("T")[0],
      status: (payload.status as DriverStatus) || DriverStatus.ACTIVE,
    };

    this.drivers.push(newDriver);
    return { success: true, data: newDriver };
  }
}

export const transportDriversService = new TransportDriversService();
