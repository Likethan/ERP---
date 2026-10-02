/**
 * CampusOS Campus Operations — Pure Business Logic Calculators
 * Centralized calculation routines for attendance rates, capacity usage,
 * registration percentages, club memberships, unread alerts, and delivery telemetry.
 */

import { ClubMemberItem, NotificationItem } from "@/types/campus";

/**
 * Calculates event attendance rate as percentage.
 * Example: 150 registered, 126 present -> 84%
 */
export function calculateEventAttendanceRate(
  presentCount: number,
  registeredCount: number
): number {
  if (!registeredCount || registeredCount <= 0) return 0;
  if (!presentCount || presentCount <= 0) return 0;
  const rate = (presentCount / registeredCount) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates event venue/registration capacity utilization as percentage.
 * Example: 180 registered, capacity 200 -> 90%
 */
export function calculateEventCapacityUsage(
  registeredCount: number,
  capacity: number
): number {
  if (!capacity || capacity <= 0) return 0;
  if (!registeredCount || registeredCount <= 0) return 0;
  const usage = (registeredCount / capacity) * 100;
  return Math.round(usage * 10) / 10;
}

/**
 * Calculates event registration rate against targeted audience cohort.
 */
export function calculateRegistrationRate(
  registeredCount: number,
  totalAudience: number
): number {
  if (!totalAudience || totalAudience <= 0) return 0;
  if (!registeredCount || registeredCount <= 0) return 0;
  const rate = (registeredCount / totalAudience) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}

/**
 * Calculates active, pending, and total membership statistics for a club.
 */
export function calculateClubMembershipCount(members: ClubMemberItem[]): {
  active: number;
  pending: number;
  suspended: number;
  total: number;
} {
  if (!Array.isArray(members)) {
    return { active: 0, pending: 0, suspended: 0, total: 0 };
  }

  let active = 0;
  let pending = 0;
  let suspended = 0;

  for (const m of members) {
    if (m.status === "ACTIVE") active++;
    else if (m.status === "PENDING") pending++;
    else if (m.status === "SUSPENDED") suspended++;
  }

  return {
    active,
    pending,
    suspended,
    total: members.length,
  };
}

/**
 * Calculates total unread notification count.
 */
export function calculateUnreadNotificationCount(
  notifications: NotificationItem[]
): number {
  if (!Array.isArray(notifications)) return 0;
  return notifications.filter((n) => n.status === "UNREAD").length;
}

/**
 * Calculates audience size estimation based on filter parameters.
 */
export function calculateAudienceSize(target: {
  type: string;
  departmentName?: string;
  semester?: number;
  programName?: string;
}): number {
  // Baseline campus student body is ~4200 across 8 departments
  // Average dept size = ~525, average sem per dept = ~65, section = ~35
  switch (target.type) {
    case "ALL_USERS":
      return 4750;
    case "ALL_STUDENTS":
    case "STUDENTS":
      return 4200;
    case "FACULTY":
      return 320;
    case "STAFF":
      return 230;
    case "SPECIFIC_DEPARTMENT":
      return 525;
    case "SPECIFIC_PROGRAM":
      return 280;
    case "SPECIFIC_SEMESTER":
      return target.departmentName ? 68 : 520;
    case "SPECIFIC_SECTION":
      return 36;
    case "CLUB_MEMBERS":
      return 145;
    case "CUSTOM":
      return 142;
    default:
      return 150;
  }
}

/**
 * Calculates message delivery conversion rate.
 */
export function calculateDeliveryRate(
  deliveredCount: number,
  totalAudience: number
): number {
  if (!totalAudience || totalAudience <= 0) return 0;
  if (!deliveredCount || deliveredCount <= 0) return 0;
  const rate = (deliveredCount / totalAudience) * 100;
  return Math.min(100, Math.round(rate * 10) / 10);
}
