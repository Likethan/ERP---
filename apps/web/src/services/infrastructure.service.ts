import { ApiResponse } from "@campusos/types";
import {
  HostelItem,
  HostelRoomItem,
  TransportRouteItem,
  TransportVehicleItem,
  MOCK_HOSTELS,
  MOCK_HOSTEL_ROOMS,
  MOCK_TRANSPORT_ROUTES,
  MOCK_VEHICLES,
} from "@/mocks/infrastructure.mock";

class InfrastructureService {
  private hostels: HostelItem[] = [...MOCK_HOSTELS];
  private rooms: HostelRoomItem[] = [...MOCK_HOSTEL_ROOMS];
  private routes: TransportRouteItem[] = [...MOCK_TRANSPORT_ROUTES];
  private vehicles: TransportVehicleItem[] = [...MOCK_VEHICLES];

  async getHostels(): Promise<ApiResponse<HostelItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.hostels };
  }

  async getRooms(hostelId?: string): Promise<ApiResponse<HostelRoomItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.rooms];
    if (hostelId) {
      items = items.filter((r) => r.hostelId === hostelId || r.hostelName === hostelId);
    }
    return { success: true, data: items };
  }

  async getTransportRoutes(): Promise<ApiResponse<TransportRouteItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.routes };
  }

  async getVehicles(): Promise<ApiResponse<TransportVehicleItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.vehicles };
  }
}

export const infrastructureService = new InfrastructureService();
