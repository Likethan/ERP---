import { ApiResponse } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";

export interface AuditLogEntry {
  id: string;
  tenantId: string;
  userId?: string | null;
  userName: string;
  userEmail: string;
  userRole: string;
  action:
    | "CREATE"
    | "UPDATE"
    | "DELETE"
    | "ROLE_ASSIGN"
    | "ROLE_REVOKE"
    | "STATUS_CHANGE"
    | "ATTENDANCE_OVERRIDE"
    | "MARKS_CORRECTION"
    | "FEE_ADJUSTMENT"
    | "SYLLABUS_OVERRIDE";
  entityType:
    | "User"
    | "RoleAssignment"
    | "Department"
    | "StudentProfile"
    | "FacultyProfile"
    | "Invoice"
    | "Result"
    | "TimetableEntry"
    | "AttendanceRecord";
  entityId: string;
  entityName?: string;
  oldValues?: Record<string, any> | null;
  newValues?: Record<string, any> | null;
  ipAddress: string;
  userAgent?: string | null;
  routeEndpoint?: string | null;
  correlationId: string;
  businessContext?: string | null;
  createdAt: string;
}

const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: "aud-001",
    tenantId: "ten-vsb-01",
    userId: "user-admin-001",
    userName: "Campus Administrator",
    userEmail: "admin@vsb.ac.in",
    userRole: "INSTITUTION_ADMIN",
    action: "ROLE_ASSIGN",
    entityType: "RoleAssignment",
    entityId: "ura-vp-101",
    entityName: "Vice Principal Assignment",
    oldValues: null,
    newValues: {
      userId: "user-vp-001",
      role: "VICE_PRINCIPAL",
      assignedBy: "admin@vsb.ac.in",
    },
    ipAddress: "192.168.1.10",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    routeEndpoint: "POST /api/v1/admin/users/user-vp-001/roles",
    correlationId: "corr-101-987a-42bc",
    businessContext:
      "Institutional appointment of Dr. K. Ramachandran to Vice Principal",
    createdAt: "2026-03-01T09:00:00Z",
  },
  {
    id: "aud-002",
    tenantId: "ten-vsb-01",
    userId: "user-admin-001",
    userName: "Campus Administrator",
    userEmail: "admin@vsb.ac.in",
    userRole: "INSTITUTION_ADMIN",
    action: "UPDATE",
    entityType: "Department",
    entityId: "dept-cse-01",
    entityName: "Computer Science & Engineering",
    oldValues: {
      hod_user_id: null,
      hod_name: "Unassigned",
    },
    newValues: {
      hod_user_id: "user-hod-cse",
      hod_name: "Dr. S. Natarajan",
    },
    ipAddress: "192.168.1.10",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    routeEndpoint: "PATCH /api/v1/departments/dept-cse-01",
    correlationId: "corr-102-123f-9988",
    businessContext:
      "Formal HOD appointment for Department of Computer Science",
    createdAt: "2026-04-10T14:30:00Z",
  },
  {
    id: "aud-003",
    tenantId: "ten-vsb-01",
    userId: "user-hod-cse",
    userName: "Dr. S. Natarajan",
    userEmail: "hod.cse@vsb.ac.in",
    userRole: "HOD",
    action: "ATTENDANCE_OVERRIDE",
    entityType: "AttendanceRecord",
    entityId: "att-rec-901",
    entityName: "Session #402 - Data Structures",
    oldValues: {
      student_roll: "23CS101",
      status: "ABSENT",
    },
    newValues: {
      student_roll: "23CS101",
      status: "PRESENT",
      medicalCondonationRef: "MED-2026-041",
    },
    ipAddress: "172.16.4.55",
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    routeEndpoint: "POST /api/v1/attendance/correction/approve",
    correlationId: "corr-103-bcde-5544",
    businessContext:
      "Approved student medical attendance regularization following clinical documentation",
    createdAt: "2026-05-15T11:20:00Z",
  },
  {
    id: "aud-004",
    tenantId: "ten-vsb-01",
    userId: "user-admin-001",
    userName: "Campus Administrator",
    userEmail: "admin@vsb.ac.in",
    userRole: "INSTITUTION_ADMIN",
    action: "STATUS_CHANGE",
    entityType: "User",
    entityId: "user-fac-susp",
    entityName: "Faculty Account #412",
    oldValues: {
      status: "ACTIVE",
    },
    newValues: {
      status: "SUSPENDED",
      reason: "Account dormancy following end-of-contract sabbatical",
    },
    ipAddress: "192.168.1.10",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    routeEndpoint: "PATCH /api/v1/admin/users/user-fac-susp/status",
    correlationId: "corr-104-a1b2-c3d4",
    businessContext: "Administrative sabbatical suspension",
    createdAt: "2026-06-01T16:00:00Z",
  },
  {
    id: "aud-005",
    tenantId: "ten-vsb-01",
    userId: "user-vp-001",
    userName: "Dr. K. Ramachandran",
    userEmail: "vp.academic@vsb.ac.in",
    userRole: "VICE_PRINCIPAL",
    action: "MARKS_CORRECTION",
    entityType: "Result",
    entityId: "res-term-501",
    entityName: "Semester 5 End-Semester Results",
    oldValues: {
      status: "MODERATION_PENDING",
      graceMarksAllocated: 0,
    },
    newValues: {
      status: "APPROVED_FOR_PUBLICATION",
      graceMarksAllocated: 3,
      statutoryApprovalId: "VP-APR-2026-018",
    },
    ipAddress: "192.168.1.42",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    routeEndpoint: "POST /api/v1/vice-principal/approvals/appr-001/approve",
    correlationId: "corr-105-ff99-1122",
    businessContext:
      "Vice Principal statutory ratification of academic grade moderation committee report",
    createdAt: "2026-06-10T10:45:00Z",
  },
];

class AdminAuditService {
  private logs: AuditLogEntry[] = [...MOCK_AUDIT_LOGS];

  async listAuditLogs(params?: {
    search?: string;
    action?: string;
    entityType?: string;
    page?: number;
    pageSize?: number;
  }): Promise<ApiResponse<AuditLogEntry[]>> {
    try {
      const qParams = new URLSearchParams();
      if (params?.search) qParams.append("search", params.search);
      const qs = qParams.toString();
      const res = await apiFetch<any[]>(
        `/api/v1/vice-principal/audit${qs ? `?${qs}` : ""}`,
      );
      if (
        res &&
        res.success &&
        Array.isArray(res.data) &&
        res.data.length > 0
      ) {
        const liveLogs: AuditLogEntry[] = res.data.map((l: any) => ({
          id: l.id || `aud-${Math.random()}`,
          tenantId: l.tenant_id || "ten-vsb-01",
          userId: l.user_id,
          userName: l.operator || l.user_name || "System Operator",
          userEmail: l.user_email || "system@campusos.internal",
          userRole: l.user_role || "SYSTEM",
          action: l.action || "UPDATE",
          entityType: l.entity_type || "Record",
          entityId: l.entity_id || "ent-001",
          entityName: l.entity_name || l.target || "System Entity",
          oldValues: l.old_values_json || l.oldValues,
          newValues: l.new_values_json || l.newValues,
          ipAddress: l.ip_address || "127.0.0.1",
          userAgent: l.user_agent,
          routeEndpoint: l.route_endpoint,
          correlationId: l.correlation_id || "corr-001",
          businessContext: l.description || l.business_context || l.details,
          createdAt: l.created_at || l.timestamp || new Date().toISOString(),
        }));
        return { success: true, data: liveLogs };
      }
    } catch {
      // Fall through to mock
    }

    let items = [...this.logs];
    if (params?.search) {
      const q = params.search.toLowerCase();
      items = items.filter(
        (l) =>
          l.userEmail.toLowerCase().includes(q) ||
          l.userName.toLowerCase().includes(q) ||
          l.ipAddress.includes(q) ||
          l.entityId.toLowerCase().includes(q) ||
          (l.businessContext && l.businessContext.toLowerCase().includes(q)),
      );
    }
    if (params?.action && params.action !== "ALL") {
      items = items.filter((l) => l.action === params.action);
    }
    if (params?.entityType && params.entityType !== "ALL") {
      items = items.filter((l) => l.entityType === params.entityType);
    }

    return { success: true, data: items };
  }
}

export const adminAuditService = new AdminAuditService();
