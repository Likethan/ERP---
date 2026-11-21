import { ApiResponse } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";

export interface AdminRoleItem {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  isSystem: boolean;
  permissionsCount: number;
  permissions: string[];
}

export interface AdminUserRoleItem {
  id: string;
  roleId: string;
  roleName: string;
  displayName: string;
  campusId?: string | null;
  departmentId?: string | null;
}

export interface AdminUserItem {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string | null;
  status: "ACTIVE" | "SUSPENDED" | "INACTIVE";
  roles: AdminUserRoleItem[];
  createdAt: string;
  updatedAt: string;
}

export interface AdminUserCreateParams {
  email: string;
  password?: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string;
  roleId?: string;
  campusId?: string;
  departmentId?: string;
}

export interface AdminRoleAssignParams {
  roleId: string;
  campusId?: string;
  departmentId?: string;
}

export interface AdminUserStatusUpdateParams {
  status: "ACTIVE" | "SUSPENDED" | "INACTIVE";
  reason?: string;
}

const MOCK_ROLES: AdminRoleItem[] = [
  {
    id: "role-super-admin",
    name: "SUPER_ADMIN",
    displayName: "Super Administrator",
    description: "Full root access across all institutions and system configurations",
    isSystem: true,
    permissionsCount: 840,
    permissions: ["*"],
  },
  {
    id: "role-inst-admin",
    name: "INSTITUTION_ADMIN",
    displayName: "Institution Administrator",
    description: "Comprehensive management over campus, departments, users, and academics",
    isSystem: true,
    permissionsCount: 420,
    permissions: ["tenant:manage", "people:manage", "academics:manage", "finance:manage"],
  },
  {
    id: "role-vice-principal",
    name: "VICE_PRINCIPAL",
    displayName: "Vice Principal",
    description: "Institutional academic monitoring, department supervision, and institutional approvals",
    isSystem: true,
    permissionsCount: 165,
    permissions: ["academics:read", "approvals:manage", "curriculum:audit", "workload:view"],
  },
  {
    id: "role-hod",
    name: "HOD",
    displayName: "Head of Department",
    description: "Department level academic leadership, faculty allocation, and student governance",
    isSystem: true,
    permissionsCount: 120,
    permissions: ["dept:manage", "faculty:workload", "course:assign", "student:manage"],
  },
  {
    id: "role-faculty",
    name: "FACULTY",
    displayName: "Faculty / Instructor",
    description: "Course delivery, attendance marking, grading, and student mentoring",
    isSystem: true,
    permissionsCount: 65,
    permissions: ["attendance:mark", "grades:post", "course:teach", "materials:upload"],
  },
  {
    id: "role-student",
    name: "STUDENT",
    displayName: "Student",
    description: "Enrolled student portal access to courses, attendance, fees, and exams",
    isSystem: true,
    permissionsCount: 25,
    permissions: ["student:portal", "attendance:view", "fees:pay", "exam:register"],
  },
];

const MOCK_USERS: AdminUserItem[] = [
  {
    id: "user-sa-001",
    email: "superadmin@campusos.internal",
    firstName: "Root",
    lastName: "SuperAdmin",
    phoneNumber: "+91 98400 11223",
    status: "ACTIVE",
    roles: [
      {
        id: "ura-sa-1",
        roleId: "role-super-admin",
        roleName: "SUPER_ADMIN",
        displayName: "Super Administrator",
      },
    ],
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2026-01-10T10:00:00Z",
  },
  {
    id: "user-admin-001",
    email: "admin@vsb.ac.in",
    firstName: "Campus",
    lastName: "Administrator",
    phoneNumber: "+91 94432 12345",
    status: "ACTIVE",
    roles: [
      {
        id: "ura-ia-1",
        roleId: "role-inst-admin",
        roleName: "INSTITUTION_ADMIN",
        displayName: "Institution Administrator",
      },
    ],
    createdAt: "2025-01-05T00:00:00Z",
    updatedAt: "2026-02-15T12:00:00Z",
  },
  {
    id: "user-vp-001",
    email: "vp.academic@vsb.ac.in",
    firstName: "Dr. K.",
    lastName: "Ramachandran",
    phoneNumber: "+91 94433 22110",
    status: "ACTIVE",
    roles: [
      {
        id: "ura-vp-1",
        roleId: "role-vice-principal",
        roleName: "VICE_PRINCIPAL",
        displayName: "Vice Principal",
      },
    ],
    createdAt: "2025-02-01T00:00:00Z",
    updatedAt: "2026-03-01T09:00:00Z",
  },
  {
    id: "user-hod-cse",
    email: "hod.cse@vsb.ac.in",
    firstName: "Dr. S.",
    lastName: "Natarajan",
    phoneNumber: "+91 98411 55667",
    status: "ACTIVE",
    roles: [
      {
        id: "ura-hod-1",
        roleId: "role-hod",
        roleName: "HOD",
        displayName: "Head of Department",
      },
    ],
    createdAt: "2025-03-01T00:00:00Z",
    updatedAt: "2026-04-10T14:30:00Z",
  },
  {
    id: "user-fac-001",
    email: "priya.sharma@vsb.ac.in",
    firstName: "Dr. Priya",
    lastName: "Sharma",
    phoneNumber: "+91 98401 23456",
    status: "ACTIVE",
    roles: [
      {
        id: "ura-fac-1",
        roleId: "role-faculty",
        roleName: "FACULTY",
        displayName: "Faculty / Instructor",
      },
    ],
    createdAt: "2025-04-10T00:00:00Z",
    updatedAt: "2026-05-12T11:00:00Z",
  },
];

class AdminRbacService {
  private users: AdminUserItem[] = [...MOCK_USERS];
  private roles: AdminRoleItem[] = [...MOCK_ROLES];

  async listRoles(): Promise<ApiResponse<AdminRoleItem[]>> {
    try {
      const res = await apiFetch<any[]>("/api/v1/admin/roles");
      if (res && res.success && Array.isArray(res.data) && res.data.length > 0) {
        const liveRoles: AdminRoleItem[] = res.data.map((r: any) => ({
          id: r.id,
          name: r.name,
          displayName: r.display_name || r.name,
          description: r.description,
          isSystem: Boolean(r.is_system),
          permissionsCount: r.permissions_count || (r.permissions ? r.permissions.length : 0),
          permissions: r.permissions || [],
        }));
        this.roles = liveRoles;
        return { success: true, data: liveRoles };
      }
    } catch (e) {
      console.warn("[AdminRbacService] Falling back to offline roles:", e);
    }
    return { success: true, data: this.roles };
  }

  async listUsers(params?: {
    search?: string;
    role?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<ApiResponse<AdminUserItem[]>> {
    try {
      const qParams = new URLSearchParams();
      if (params?.search) qParams.append("search", params.search);
      if (params?.role && params.role !== "ALL") qParams.append("role", params.role);
      if (params?.status && params.status !== "ALL") qParams.append("status", params.status);
      if (params?.page) qParams.append("page", params.page.toString());
      if (params?.pageSize) qParams.append("page_size", params.pageSize.toString());

      const qs = qParams.toString();
      const res = await apiFetch<any[]>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
      if (res && res.success && Array.isArray(res.data)) {
        const liveUsers: AdminUserItem[] = res.data.map((u: any) => ({
          id: u.id,
          email: u.email,
          firstName: u.first_name,
          lastName: u.last_name,
          phoneNumber: u.phone_number,
          status: u.status,
          roles: (u.roles || []).map((r: any) => ({
            id: r.id,
            roleId: r.role_id,
            roleName: r.role_name,
            displayName: r.display_name || r.role_name,
            campusId: r.campus_id,
            departmentId: r.department_id,
          })),
          createdAt: u.created_at,
          updatedAt: u.updated_at,
        }));
        return { success: true, data: liveUsers };
      }
    } catch (e) {
      console.warn("[AdminRbacService] Falling back to offline users:", e);
    }

    let filtered = [...this.users];
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (u) =>
          u.email.toLowerCase().includes(q) ||
          u.firstName.toLowerCase().includes(q) ||
          u.lastName.toLowerCase().includes(q),
      );
    }
    if (params?.role && params.role !== "ALL") {
      filtered = filtered.filter((u) => u.roles.some((r) => r.roleName === params.role));
    }
    if (params?.status && params.status !== "ALL") {
      filtered = filtered.filter((u) => u.status === params.status);
    }
    return { success: true, data: filtered };
  }

  async createUser(payload: AdminUserCreateParams): Promise<ApiResponse<AdminUserItem>> {
    try {
      const body: any = {
        email: payload.email,
        password: payload.password || "Welcome@123",
        first_name: payload.firstName,
        last_name: payload.lastName,
        phone_number: payload.phoneNumber || null,
        role_id: payload.roleId || null,
        campus_id: payload.campusId || null,
        department_id: payload.departmentId || null,
      };
      const res = await apiFetch<any>("/api/v1/admin/users", {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (res && res.success && res.data) {
        const u = res.data;
        const newUser: AdminUserItem = {
          id: u.id,
          email: u.email,
          firstName: u.first_name,
          lastName: u.last_name,
          phoneNumber: u.phone_number,
          status: u.status,
          roles: (u.roles || []).map((r: any) => ({
            id: r.id,
            roleId: r.role_id,
            roleName: r.role_name,
            displayName: r.display_name || r.role_name,
            campusId: r.campus_id,
            departmentId: r.department_id,
          })),
          createdAt: u.created_at,
          updatedAt: u.updated_at,
        };
        this.users.unshift(newUser);
        return { success: true, data: newUser };
      }
    } catch (e: any) {
      console.warn("[AdminRbacService] API create failed, using local fallback:", e);
    }

    const assignedRole = this.roles.find((r) => r.id === payload.roleId);
    const mockUser: AdminUserItem = {
      id: `user-${Date.now()}`,
      email: payload.email,
      firstName: payload.firstName,
      lastName: payload.lastName,
      phoneNumber: payload.phoneNumber,
      status: "ACTIVE",
      roles: assignedRole
        ? [
            {
              id: `ura-${Date.now()}`,
              roleId: assignedRole.id,
              roleName: assignedRole.name,
              displayName: assignedRole.displayName,
              campusId: payload.campusId,
              departmentId: payload.departmentId,
            },
          ]
        : [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.users.unshift(mockUser);
    return { success: true, data: mockUser };
  }

  async assignRole(userId: string, payload: AdminRoleAssignParams): Promise<ApiResponse<AdminUserRoleItem>> {
    try {
      const res = await apiFetch<any>(`/api/v1/admin/users/${userId}/roles`, {
        method: "POST",
        body: JSON.stringify({
          role_id: payload.roleId,
          campus_id: payload.campusId || null,
          department_id: payload.departmentId || null,
        }),
      });
      if (res && res.success && res.data) {
        return {
          success: true,
          data: {
            id: res.data.id,
            roleId: res.data.role_id,
            roleName: res.data.role_name,
            displayName: res.data.display_name || res.data.role_name,
            campusId: res.data.campus_id,
            departmentId: res.data.department_id,
          },
        };
      }
    } catch (e: any) {
      console.warn("[AdminRbacService] API assignRole failed, using local fallback:", e);
    }

    const role = this.roles.find((r) => r.id === payload.roleId);
    const user = this.users.find((u) => u.id === userId);
    const newRoleItem: AdminUserRoleItem = {
      id: `ura-${Date.now()}`,
      roleId: payload.roleId,
      roleName: role ? role.name : "ROLE",
      displayName: role ? role.displayName : "Role",
      campusId: payload.campusId,
      departmentId: payload.departmentId,
    };
    if (user) {
      user.roles.push(newRoleItem);
    }
    return { success: true, data: newRoleItem };
  }

  async revokeRole(userId: string, roleId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const res = await apiFetch<{ message: string }>(`/api/v1/admin/users/${userId}/roles/${roleId}`, {
        method: "DELETE",
      });
      if (res && res.success) {
        return res;
      }
    } catch (e: any) {
      console.warn("[AdminRbacService] API revokeRole failed, using local fallback:", e);
    }

    const user = this.users.find((u) => u.id === userId);
    if (user) {
      user.roles = user.roles.filter((r) => r.roleId !== roleId);
    }
    return { success: true, data: { message: "Role revoked successfully" } };
  }

  async updateUserStatus(
    userId: string,
    payload: AdminUserStatusUpdateParams,
  ): Promise<ApiResponse<AdminUserItem>> {
    try {
      const res = await apiFetch<any>(`/api/v1/admin/users/${userId}/status`, {
        method: "PATCH",
        body: JSON.stringify({
          status: payload.status,
          reason: payload.reason || null,
        }),
      });
      if (res && res.success && res.data) {
        const u = res.data;
        const updated: AdminUserItem = {
          id: u.id,
          email: u.email,
          firstName: u.first_name,
          lastName: u.last_name,
          phoneNumber: u.phone_number,
          status: u.status,
          roles: (u.roles || []).map((r: any) => ({
            id: r.id,
            roleId: r.role_id,
            roleName: r.role_name,
            displayName: r.display_name || r.role_name,
            campusId: r.campus_id,
            departmentId: r.department_id,
          })),
          createdAt: u.created_at,
          updatedAt: u.updated_at,
        };
        return { success: true, data: updated };
      }
    } catch (e: any) {
      console.warn("[AdminRbacService] API updateUserStatus failed, using local fallback:", e);
    }

    const user = this.users.find((u) => u.id === userId);
    if (user) {
      user.status = payload.status;
      return { success: true, data: user };
    }
    throw new Error("User not found");
  }
}

export const adminRbacService = new AdminRbacService();
