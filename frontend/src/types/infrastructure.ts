/**
 * CampusOS Infrastructure Management Domain Types
 * "One Campus. One System. One Source of Truth."
 */

export * from "@campusos/types";

import {
  Hostel,
  HostelRoom,
  HostelAllocation,
  HostelLeave,
  HostelComplaint,
  TransportRoute,
  TransportStop,
  TransportVehicle,
  TransportDriver,
  TransportAllocation,
  Facility,
  MaintenanceRequest,
  InfrastructureDashboardSummary,
  InfrastructureReportData,
} from "@campusos/types";

// UI Filter Types
export interface HostelFilterState {
  campus: string;
  type: string;
  gender: string;
  status: string;
  occupancy: string;
  warden: string;
  search: string;
}

export interface RoomFilterState {
  hostelId: string;
  block: string;
  floor: string;
  roomType: string;
  status: string;
  gender: string;
  search: string;
}

export interface AllocationFilterState {
  hostelId: string;
  block: string;
  room: string;
  status: string;
  program: string;
  year: string;
  search: string;
}

export interface LeaveFilterState {
  hostelId: string;
  status: string;
  startDate?: string;
  endDate?: string;
  search: string;
}

export interface ComplaintFilterState {
  hostelId: string;
  category: string;
  priority: string;
  status: string;
  search: string;
}

export interface RouteFilterState {
  campus: string;
  status: string;
  vehicle: string;
  search: string;
}

export interface StopFilterState {
  routeId: string;
  status: string;
  search: string;
}

export interface VehicleFilterState {
  type: string;
  status: string;
  fuelType: string;
  search: string;
}

export interface DriverFilterState {
  status: string;
  licenseStatus: string;
  routeId: string;
  search: string;
}

export interface TransportAllocationFilterState {
  routeId: string;
  stopId: string;
  status: string;
  program: string;
  search: string;
}

export interface FacilityFilterState {
  campus: string;
  type: string;
  status: string;
  building: string;
  search: string;
}

export interface MaintenanceFilterState {
  sourceType: string;
  category: string;
  priority: string;
  status: string;
  assetId: string;
  assignedTo: string;
  search: string;
}

// Re-export entity aliases for convenience
export type {
  Hostel,
  HostelRoom,
  HostelAllocation,
  HostelLeave,
  HostelComplaint,
  TransportRoute,
  TransportStop,
  TransportVehicle,
  TransportDriver,
  TransportAllocation,
  Facility,
  MaintenanceRequest,
  InfrastructureDashboardSummary,
  InfrastructureReportData,
};
