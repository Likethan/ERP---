/**
 * CampusOS Infrastructure Management — Centralized Pure Domain Calculators
 * "One Campus. One System. One Source of Truth."
 *
 * Implements deterministic arithmetic and status evaluations for:
 * - Hostel & Bed Occupancy
 * - Room Availability
 * - Transport Route & Vehicle Fleet Utilization
 * - Complaint & Maintenance Resolution Rates
 * - Maintenance SLA Status Determination
 * - Facility Availability Rates
 */

import { MaintenancePriority } from "@campusos/types";

/**
 * Calculates hostel occupancy percentage rounded to 1 decimal place.
 * Clamped between 0% and 100%.
 */
export function calculateHostelOccupancy(occupiedBeds: number, totalBeds: number): number {
  if (!totalBeds || totalBeds <= 0 || occupiedBeds <= 0) return 0;
  const rate = (occupiedBeds / totalBeds) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates room occupancy percentage.
 */
export function calculateRoomOccupancy(occupiedBeds: number, capacityBeds: number): number {
  if (!capacityBeds || capacityBeds <= 0 || occupiedBeds <= 0) return 0;
  const rate = (occupiedBeds / capacityBeds) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates bed availability metrics.
 */
export function calculateBedAvailability(
  totalBeds: number,
  occupiedBeds: number,
  maintenanceBeds: number = 0
): {
  availableBeds: number;
  availabilityRate: number;
  usableBeds: number;
} {
  const safeTotal = Math.max(0, totalBeds);
  const safeOccupied = Math.max(0, occupiedBeds);
  const safeMaint = Math.max(0, maintenanceBeds);
  const usableBeds = Math.max(0, safeTotal - safeMaint);
  const availableBeds = Math.max(0, usableBeds - safeOccupied);
  const availabilityRate = safeTotal > 0 ? Math.round((availableBeds / safeTotal) * 1000) / 10 : 0;

  return {
    availableBeds,
    availabilityRate,
    usableBeds,
  };
}

/**
 * Calculates route capacity utilization percentage.
 */
export function calculateRouteUtilization(allocatedStudents: number, capacity: number): number {
  if (!capacity || capacity <= 0 || allocatedStudents <= 0) return 0;
  const rate = (allocatedStudents / capacity) * 100;
  return Math.round(rate * 10) / 10;
}

/**
 * Calculates vehicle fleet capacity utilization percentage.
 */
export function calculateVehicleUtilization(assignedRoutesCapacity: number, totalFleetCapacity: number): number {
  if (!totalFleetCapacity || totalFleetCapacity <= 0 || assignedRoutesCapacity <= 0) return 0;
  const rate = (assignedRoutesCapacity / totalFleetCapacity) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates transport adoption rate among eligible students.
 */
export function calculateTransportAllocationRate(allocatedStudents: number, totalEligibleStudents: number): number {
  if (!totalEligibleStudents || totalEligibleStudents <= 0 || allocatedStudents <= 0) return 0;
  const rate = (allocatedStudents / totalEligibleStudents) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates hostel complaint resolution percentage.
 */
export function calculateComplaintResolutionRate(resolvedCount: number, totalComplaints: number): number {
  if (!totalComplaints || totalComplaints <= 0 || resolvedCount <= 0) return 0;
  const rate = (resolvedCount / totalComplaints) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates infrastructure maintenance resolution percentage.
 */
export function calculateMaintenanceResolutionRate(resolvedRequests: number, totalRequests: number): number {
  if (!totalRequests || totalRequests <= 0 || resolvedRequests <= 0) return 0;
  const rate = (resolvedRequests / totalRequests) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Determines SLA status and remaining hours for maintenance requests.
 * Standard SLA targets:
 * - CRITICAL: 4 hours
 * - HIGH: 12 hours
 * - MEDIUM: 24 hours
 * - LOW: 48 hours
 */
export function calculateMaintenanceSLAStatus(
  createdAtIso: string,
  priority: MaintenancePriority | string,
  resolvedAtIso?: string | null
): {
  isBreached: boolean;
  slaTargetHours: number;
  elapsedHours: number;
  remainingHours: number;
  statusText: "ON_TRACK" | "APPROACHING_DEADLINE" | "BREACHED" | "RESOLVED_WITHIN_SLA" | "RESOLVED_OVERDUE";
} {
  const targetHoursMap: Record<string, number> = {
    [MaintenancePriority.CRITICAL]: 4,
    [MaintenancePriority.HIGH]: 12,
    [MaintenancePriority.MEDIUM]: 24,
    [MaintenancePriority.LOW]: 48,
  };

  const slaTargetHours = targetHoursMap[priority] || 24;
  const createdTime = new Date(createdAtIso).getTime();
  const nowOrResolved = resolvedAtIso ? new Date(resolvedAtIso).getTime() : Date.now();
  
  const elapsedMillis = Math.max(0, nowOrResolved - createdTime);
  const elapsedHours = Math.round((elapsedMillis / (1000 * 60 * 60)) * 10) / 10;
  const remainingHours = Math.round((slaTargetHours - elapsedHours) * 10) / 10;
  const isBreached = elapsedHours > slaTargetHours;

  let statusText: "ON_TRACK" | "APPROACHING_DEADLINE" | "BREACHED" | "RESOLVED_WITHIN_SLA" | "RESOLVED_OVERDUE";
  if (resolvedAtIso) {
    statusText = isBreached ? "RESOLVED_OVERDUE" : "RESOLVED_WITHIN_SLA";
  } else if (isBreached) {
    statusText = "BREACHED";
  } else if (remainingHours <= (slaTargetHours * 0.25)) {
    statusText = "APPROACHING_DEADLINE";
  } else {
    statusText = "ON_TRACK";
  }

  return {
    isBreached,
    slaTargetHours,
    elapsedHours,
    remainingHours,
    statusText,
  };
}

/**
 * Calculates operational availability percentage for physical facilities.
 */
export function calculateFacilityAvailability(totalFacilities: number, maintenanceFacilities: number): number {
  if (!totalFacilities || totalFacilities <= 0) return 0;
  const activeCount = Math.max(0, totalFacilities - (maintenanceFacilities || 0));
  const rate = (activeCount / totalFacilities) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}
