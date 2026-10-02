/**
 * CampusOS Transport Vehicles Service
 * API Contract:
 * GET  /api/v1/transport/vehicles
 * GET  /api/v1/transport/vehicles/:id
 * POST /api/v1/transport/vehicles
 * PUT  /api/v1/transport/vehicles/:id
 * POST /api/v1/transport/vehicles/:id/service
 */

import { ApiResponse, TransportVehicle, VehicleStatus, VehicleType } from "@campusos/types";
import { MOCK_TRANSPORT_VEHICLES } from "@/mocks/infrastructure.mock";

class TransportVehiclesService {
  private vehicles: TransportVehicle[] = JSON.parse(JSON.stringify(MOCK_TRANSPORT_VEHICLES));

  async listVehicles(filters?: {
    type?: VehicleType | string;
    status?: VehicleStatus | string;
    search?: string;
  }): Promise<ApiResponse<TransportVehicle[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.vehicles];

    if (filters?.type && filters.type !== "ALL") {
      items = items.filter((v) => v.type === filters.type);
    }
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((v) => v.status === filters.status);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (v) =>
          v.registrationNumber.toLowerCase().includes(q) ||
          v.vehicleNumber.toLowerCase().includes(q) ||
          v.makeModel.toLowerCase().includes(q) ||
          v.assignedDriverName?.toLowerCase().includes(q) ||
          v.currentRouteName?.toLowerCase().includes(q)
      );
    }

    return { success: true, data: items };
  }

  async getVehicleById(id: string): Promise<ApiResponse<TransportVehicle | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const vehicle = this.vehicles.find((v) => v.id === id || v.registrationNumber === id || v.vehicleNumber === id) || null;
    return { success: true, data: vehicle };
  }

  async addServiceRecord(
    id: string,
    service: {
      serviceDate: string;
      serviceType: string;
      mileageKm: number;
      costInr: number;
      nextServiceDate: string;
      vendorName: string;
      notes?: string;
    }
  ): Promise<ApiResponse<TransportVehicle | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const vehicle = this.vehicles.find((v) => v.id === id);
    if (!vehicle) return { success: false, data: null };

    vehicle.services = vehicle.services || [];
    vehicle.services.unshift({
      id: `srv-${Date.now().toString(36)}`,
      ...service,
      status: "COMPLETED",
    });
    vehicle.lastServiceDate = service.serviceDate;
    vehicle.nextServiceDate = service.nextServiceDate;

    return { success: true, data: vehicle };
  }

  async createVehicle(payload: Partial<TransportVehicle>): Promise<ApiResponse<TransportVehicle>> {
    await new Promise((r) => setTimeout(r, 50));
    const newVehicle: TransportVehicle = {
      id: `veh-${Date.now().toString(36)}`,
      registrationNumber: payload.registrationNumber || `KA-04-TR-${Math.floor(1000 + Math.random() * 9000)}`,
      vehicleNumber: payload.vehicleNumber || `BUS-${this.vehicles.length + 1}`,
      type: (payload.type as VehicleType) || VehicleType.BUS,
      makeModel: payload.makeModel || "Tata Starbus 52-Seater",
      capacity: payload.capacity || 52,
      fuelType: payload.fuelType || "DIESEL",
      insurancePolicyNumber: payload.insurancePolicyNumber || `POL-NIA-${Date.now().toString().slice(-6)}`,
      insuranceValidUntil: payload.insuranceValidUntil || "2027-04-30",
      fitnessCertificateValidUntil: payload.fitnessCertificateValidUntil || "2027-05-15",
      pollutionCertificateValidUntil: payload.pollutionCertificateValidUntil || "2027-01-31",
      lastServiceDate: payload.lastServiceDate || new Date().toISOString().split("T")[0],
      nextServiceDate: payload.nextServiceDate || "2026-12-15",
      status: (payload.status as VehicleStatus) || VehicleStatus.AVAILABLE,
      services: [],
    };

    this.vehicles.push(newVehicle);
    return { success: true, data: newVehicle };
  }
}

export const transportVehiclesService = new TransportVehiclesService();
