/**
 * CampusOS Core Shared Type Definitions
 * "One Campus. One System. One Source of Truth."
 */

export type UUID = string;

/**
 * Supported User Roles in CampusOS
 */
export enum UserRole {
  SUPER_ADMIN = "SUPER_ADMIN",
  PRINCIPAL = "PRINCIPAL",
  HOD = "HOD",
  FACULTY = "FACULTY",
  ACCOUNTS = "ACCOUNTS",
  PLACEMENT_OFFICER = "PLACEMENT_OFFICER",
  STUDENT = "STUDENT",
  PARENT = "PARENT",
  STAFF = "STAFF",
}

/**
 * Core Domains within the CampusOS Modular Monolith
 */
export enum DomainName {
  CORE = "core",
  PEOPLE = "people",
  ACADEMICS = "academics",
  ATTENDANCE = "attendance",
  EXAMINATION = "examination",
  FINANCE = "finance",
  PLACEMENT = "placement",
  CAMPUS = "campus",
  INFRASTRUCTURE = "infrastructure",
  DOCUMENTS = "documents",
  INTELLIGENCE = "intelligence",
}

/**
 * Standard Tenant Context for multi-tenancy isolation
 */
export interface TenantContext {
  tenantId: UUID;
  institutionCode: string;
  name: string;
  isActive: boolean;
}

/**
 * Standard API Envelope for all successful REST responses
 */
export interface ApiResponse<T> {
  success: true;
  data: T;
  meta?: {
    timestamp: string;
    requestId?: string;
    [key: string]: unknown;
  };
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  pageSize: number;
  totalRecords: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

/**
 * Standard Paginated API Envelope
 */
export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: PaginationMeta;
  meta?: {
    timestamp: string;
    requestId?: string;
  };
}

/**
 * Standard API Error Detail
 */
export interface ApiErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

/**
 * Standard API Error Envelope for all failed REST responses
 */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetail[];
    requestId?: string;
    timestamp: string;
  };
}

/**
 * Health Check Payload
 */
export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  timestamp: string;
  environment: string;
}
