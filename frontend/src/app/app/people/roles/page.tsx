"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  UserPlus,
  Users,
  Search,
  KeyRound,
  Filter,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Building2,
  Sparkles,
  ArrowLeft,
  X,
  Lock,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import {
  adminRbacService,
  AdminRoleItem,
  AdminUserItem,
  AdminUserCreateParams,
  AdminRoleAssignParams,
} from "@/services/admin-rbac.service";

export default function AdminRolesManagementPage() {
  const [activeTab, setActiveTab] = useState<"users" | "roles" | "policies">(
    "users",
  );
  const [roles, setRoles] = useState<AdminRoleItem[]>([]);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRoleFilter, setSelectedRoleFilter] = useState("ALL");
  const [selectedStatusFilter, setSelectedStatusFilter] = useState("ALL");

  // Create User Modal State
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [createForm, setCreateForm] = useState<AdminUserCreateParams>({
    email: "",
    password: "Password@123",
    firstName: "",
    lastName: "",
    phoneNumber: "",
    roleId: "",
  });

  // Assign Role Modal State
  const [assignRoleOpen, setAssignRoleOpen] = useState(false);
  const [targetUser, setTargetUser] = useState<AdminUserItem | null>(null);
  const [assignRoleForm, setAssignRoleForm] = useState<AdminRoleAssignParams>({
    roleId: "",
  });

  // Revoke Role Confirmation State
  const [revokeConfirmOpen, setRevokeConfirmOpen] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<{
    user: AdminUserItem;
    roleId: string;
    roleName: string;
  } | null>(null);

  // Status Toggle Confirmation State
  const [statusConfirmOpen, setStatusConfirmOpen] = useState(false);
  const [statusTarget, setStatusTarget] = useState<{
    user: AdminUserItem;
    newStatus: "ACTIVE" | "SUSPENDED";
  } | null>(null);

  const loadData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [rolesRes, usersRes] = await Promise.all([
        adminRbacService.listRoles(),
        adminRbacService.listUsers(),
      ]);
      if (rolesRes.data) setRoles(rolesRes.data);
      if (usersRes.data) setUsers(usersRes.data);
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to load RBAC data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered Users
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const matchesSearch =
        searchQuery === "" ||
        u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.lastName.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRole =
        selectedRoleFilter === "ALL" ||
        u.roles.some((r) => r.roleName === selectedRoleFilter);

      const matchesStatus =
        selectedStatusFilter === "ALL" || u.status === selectedStatusFilter;

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, searchQuery, selectedRoleFilter, selectedStatusFilter]);

  // Handle Create User
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await adminRbacService.createUser(createForm);
      setSuccessMessage(`Account created successfully for ${createForm.email}`);
      setCreateUserOpen(false);
      setCreateForm({
        email: "",
        password: "Password@123",
        firstName: "",
        lastName: "",
        phoneNumber: "",
        roleId: "",
      });
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to create user account");
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Assign Role
  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUser || !assignRoleForm.roleId) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await adminRbacService.assignRole(targetUser.id, assignRoleForm);
      setSuccessMessage(`Role assigned to ${targetUser.email}`);
      setAssignRoleOpen(false);
      setTargetUser(null);
      setAssignRoleForm({ roleId: "" });
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to assign role");
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Revoke Role
  const handleRevokeRole = async () => {
    if (!revokeTarget) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await adminRbacService.revokeRole(
        revokeTarget.user.id,
        revokeTarget.roleId,
      );
      setSuccessMessage(
        `Revoked role ${revokeTarget.roleName} from ${revokeTarget.user.email}`,
      );
      setRevokeConfirmOpen(false);
      setRevokeTarget(null);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to revoke role");
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Status Toggle
  const handleStatusToggle = async () => {
    if (!statusTarget) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await adminRbacService.updateUserStatus(statusTarget.user.id, {
        status: statusTarget.newStatus,
        reason: `Administrative status change by administrator to ${statusTarget.newStatus}`,
      });
      setSuccessMessage(
        `Account ${statusTarget.user.email} marked as ${statusTarget.newStatus}`,
      );
      setStatusConfirmOpen(false);
      setStatusTarget(null);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to update account status");
    } finally {
      setActionLoading(false);
    }
  };

  const activeUsersCount = users.filter((u) => u.status === "ACTIVE").length;
  const privilegedUsersCount = users.filter((u) =>
    u.roles.some((r) =>
      ["SUPER_ADMIN", "INSTITUTION_ADMIN"].includes(r.roleName),
    ),
  ).length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/people"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 flex items-center gap-1"
            >
              <ArrowLeft className="h-3 w-3" /> Back to People Master
            </Link>
            <span className="text-slate-300 dark:text-slate-700">&bull;</span>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              <Shield className="h-3 w-3" />
              RBAC & Identity Governance
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            User Accounts & Role-Based Access Control
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Provision user accounts, assign canonical institutional roles,
            enforce separation of duties, and audit active permissions.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCreateUserOpen(true)}
            className="flex items-center gap-1.5 shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <UserPlus className="h-4 w-4" />
            Create User Account
          </Button>
        </div>
      </div>

      {/* Alert Banners */}
      {errorMessage && (
        <div className="rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 p-4 text-xs text-red-800 dark:text-red-300 flex items-start gap-2.5">
          <AlertTriangle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Security Safeguard Alert: </span>
            {errorMessage}
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-red-600 hover:text-red-800"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 p-4 text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
          <div className="flex-1 font-medium">{successMessage}</div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-600 hover:text-emerald-800"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="System Roles"
          value={roles.length.toString()}
          description="Standardized institutional roles"
          icon={<Shield className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Total User Accounts"
          value={users.length.toString()}
          description="Provisioned in identity directory"
          icon={<Users className="h-5 w-5 text-blue-500" />}
        />
        <StatCard
          title="Active Accounts"
          value={activeUsersCount.toString()}
          description={`${Math.round((activeUsersCount / (users.length || 1)) * 100)}% operational`}
          icon={<UserCheck className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Privileged Admins"
          value={privilegedUsersCount.toString()}
          description="Super & Institution Admins"
          icon={<KeyRound className="h-5 w-5 text-amber-500" />}
        />
      </div>

      {/* Tab Controls */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "users"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Users className="h-4 w-4" />
          User Accounts & Role Assignments ({filteredUsers.length})
        </button>
        <button
          onClick={() => setActiveTab("roles")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "roles"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          Roles & Permissions Matrix ({roles.length})
        </button>
        <button
          onClick={() => setActiveTab("policies")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "policies"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Lock className="h-4 w-4" />
          RBAC Security Policies & Safeguards
        </button>
      </div>

      {/* TAB 1: USERS AND ROLE ASSIGNMENTS */}
      {activeTab === "users" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="flex flex-col md:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by name or email address..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-9 text-xs"
                />
              </div>

              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="flex items-center gap-1.5 shrink-0 text-xs text-slate-500">
                  <Filter className="h-3.5 w-3.5" />
                  <span>Role:</span>
                </div>
                <select
                  value={selectedRoleFilter}
                  onChange={(e) => setSelectedRoleFilter(e.target.value)}
                  className="h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="ALL">All Roles</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.name}>
                      {r.displayName || r.name}
                    </option>
                  ))}
                </select>

                <div className="flex items-center gap-1.5 shrink-0 text-xs text-slate-500 ml-2">
                  <span>Status:</span>
                </div>
                <select
                  value={selectedStatusFilter}
                  onChange={(e) => setSelectedStatusFilter(e.target.value)}
                  className="h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="ALL">All Status</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="SUSPENDED">SUSPENDED</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>

                {(searchQuery ||
                  selectedRoleFilter !== "ALL" ||
                  selectedStatusFilter !== "ALL") && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSearchQuery("");
                      setSelectedRoleFilter("ALL");
                      setSelectedStatusFilter("ALL");
                    }}
                    className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                  >
                    Reset
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* Users Table */}
          <Card className="overflow-hidden bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                    <th className="py-3 px-4 font-semibold">User Identity</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">
                      Assigned Roles & Scopes
                    </th>
                    <th className="py-3 px-4 font-semibold">Registered</th>
                    <th className="py-3 px-4 font-semibold text-right">
                      Administrative Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="py-8 text-center text-slate-500 dark:text-slate-400"
                      >
                        No user accounts match the selected filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => {
                      const isSuperAdmin = u.roles.some(
                        (r) => r.roleName === "SUPER_ADMIN",
                      );
                      return (
                        <tr
                          key={u.id}
                          className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          {/* User Identity */}
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                                  isSuperAdmin
                                    ? "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300"
                                    : "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                                }`}
                              >
                                {u.firstName.charAt(0)}
                                {u.lastName.charAt(0)}
                              </div>
                              <div>
                                <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                                  {u.firstName} {u.lastName}
                                  {isSuperAdmin && (
                                    <span title="Super Admin Account">
                                      <KeyRound className="h-3 w-3 text-amber-500" />
                                    </span>
                                  )}
                                </div>
                                <div className="text-slate-500 dark:text-slate-400 text-[11px]">
                                  {u.email}
                                </div>
                                {u.phoneNumber && (
                                  <div className="text-slate-400 dark:text-slate-500 text-[10px]">
                                    {u.phoneNumber}
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4">
                            <Badge
                              variant={
                                u.status === "ACTIVE"
                                  ? "success"
                                  : u.status === "SUSPENDED"
                                    ? "destructive"
                                    : "secondary"
                              }
                            >
                              {u.status}
                            </Badge>
                          </td>

                          {/* Assigned Roles */}
                          <td className="py-3.5 px-4">
                            <div className="flex flex-wrap items-center gap-1.5">
                              {u.roles.length === 0 ? (
                                <span className="text-slate-400 italic text-[11px]">
                                  No roles assigned
                                </span>
                              ) : (
                                u.roles.map((r) => (
                                  <span
                                    key={r.id}
                                    className="inline-flex items-center gap-1 rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                                  >
                                    <Shield className="h-2.5 w-2.5 text-indigo-500" />
                                    <span>{r.displayName || r.roleName}</span>
                                    {r.departmentId && (
                                      <span className="text-[9px] text-slate-400">
                                        {" "}
                                        (Dept)
                                      </span>
                                    )}
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setRevokeTarget({
                                          user: u,
                                          roleId: r.roleId,
                                          roleName: r.displayName || r.roleName,
                                        });
                                        setRevokeConfirmOpen(true);
                                      }}
                                      className="ml-1 text-slate-400 hover:text-red-600 transition-colors"
                                      title="Revoke this role"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </span>
                                ))
                              )}
                            </div>
                          </td>

                          {/* Registered */}
                          <td className="py-3.5 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                            {new Date(u.createdAt).toLocaleDateString()}
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setTargetUser(u);
                                  setAssignRoleForm({ roleId: "" });
                                  setAssignRoleOpen(true);
                                }}
                                className="h-7 text-[11px] px-2.5"
                              >
                                + Assign Role
                              </Button>

                              <Button
                                variant={
                                  u.status === "ACTIVE" ? "outline" : "primary"
                                }
                                size="sm"
                                onClick={() => {
                                  setStatusTarget({
                                    user: u,
                                    newStatus:
                                      u.status === "ACTIVE"
                                        ? "SUSPENDED"
                                        : "ACTIVE",
                                  });
                                  setStatusConfirmOpen(true);
                                }}
                                className={`h-7 text-[11px] px-2.5 ${
                                  u.status === "ACTIVE"
                                    ? "text-amber-600 dark:text-amber-400 hover:border-amber-400"
                                    : "bg-emerald-600 hover:bg-emerald-700 text-white"
                                }`}
                              >
                                {u.status === "ACTIVE" ? "Suspend" : "Activate"}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: ROLES & PERMISSIONS MATRIX */}
      {activeTab === "roles" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles.map((role) => {
            const isSuper = role.name === "SUPER_ADMIN";
            const isInstAdmin = role.name === "INSTITUTION_ADMIN";
            const isVp = role.name === "VICE_PRINCIPAL";

            return (
              <Card
                key={role.id}
                className={`p-5 flex flex-col justify-between border-slate-200 dark:border-slate-800 ${
                  isSuper
                    ? "border-amber-300 dark:border-amber-900/60 bg-amber-50/20 dark:bg-amber-950/10"
                    : "bg-white dark:bg-slate-900"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className={`p-1.5 rounded-lg ${
                          isSuper
                            ? "bg-amber-500/10 text-amber-600"
                            : isInstAdmin
                              ? "bg-indigo-500/10 text-indigo-600"
                              : isVp
                                ? "bg-blue-500/10 text-blue-600"
                                : "bg-slate-500/10 text-slate-600"
                        }`}
                      >
                        <Shield className="h-4 w-4" />
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                          {role.displayName || role.name}
                        </h3>
                        <div className="text-[11px] font-mono text-slate-500">
                          {role.name}
                        </div>
                      </div>
                    </div>
                    {role.isSystem && (
                      <Badge variant="outline" className="text-[10px]">
                        System Role
                      </Badge>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                    {role.description ||
                      "Canonical system role governing institution boundaries."}
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                      <span>Permissions Coverage</span>
                      <span className="text-indigo-600 dark:text-indigo-400 font-mono">
                        {role.permissionsCount > 0
                          ? `${role.permissionsCount} Ops`
                          : "Standard Set"}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {role.permissions.slice(0, 6).map((perm, idx) => (
                        <span
                          key={idx}
                          className="inline-block rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                        >
                          {perm}
                        </span>
                      ))}
                      {role.permissions.length > 6 && (
                        <span className="inline-block rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-500">
                          +{role.permissions.length - 6} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Assigned Users</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {
                      users.filter((u) =>
                        u.roles.some((r) => r.roleName === role.name),
                      ).length
                    }{" "}
                    accounts
                  </span>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* TAB 3: RBAC POLICIES & SAFEGUARDS */}
      {activeTab === "policies" && (
        <div className="space-y-4">
          <Card className="p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <h2 className="text-base font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-indigo-600" />
              Enterprise RBAC Rules & Invariants
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-6">
              CampusOS enforces strict enterprise security boundaries across
              multi-tenant college environments to prevent privilege escalation
              and catastrophic self-lockout.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-1.5">
                  <Lock className="h-4 w-4 text-amber-500" />
                  Self-Lockout & SuperAdmin Invariant
                </div>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  The system prevents an administrator from revoking their own{" "}
                  <code>SUPER_ADMIN</code> role or deactivating their own
                  account. Additionally, an institution must retain at least one
                  active Super Administrator at all times.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-1.5">
                  <Building2 className="h-4 w-4 text-indigo-500" />
                  Tenant & Department Isolation
                </div>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  Roles scoped to a specific department (such as HOD or Faculty)
                  are strictly bounded to that department&apos;s courses,
                  students, and marks. Cross-department modifications require
                  Institutional Administrator authorization.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Separation of Duties (SoD)
                </div>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  Academic monitoring is separated between Vice Principal
                  (institutional oversight, regulatory audits) and HOD
                  (departmental allocation, roster operations). Financial
                  actions require separate finance permissions.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4 text-blue-500" />
                  Immutable Audit Logging
                </div>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  Every user creation, role assignment, revocation, and status
                  modification writes an append-only audit record tagged with
                  the actor&apos;s IP address, timestamp, and authorization
                  context.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* CREATE USER MODAL */}
      <Dialog
        open={createUserOpen}
        onClose={() => setCreateUserOpen(false)}
        title="Create New User Account"
        description="Provision an authenticated identity in the campus directory and assign an initial role."
      >
        <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                First Name *
              </label>
              <Input
                required
                placeholder="e.g. Ramesh"
                value={createForm.firstName}
                onChange={(e) =>
                  setCreateForm({ ...createForm, firstName: e.target.value })
                }
                className="h-9 text-xs"
              />
            </div>
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Last Name *
              </label>
              <Input
                required
                placeholder="e.g. Kumar"
                value={createForm.lastName}
                onChange={(e) =>
                  setCreateForm({ ...createForm, lastName: e.target.value })
                }
                className="h-9 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Email Address *
            </label>
            <Input
              required
              type="email"
              placeholder="e.g. ramesh.kumar@vsb.ac.in"
              value={createForm.email}
              onChange={(e) =>
                setCreateForm({ ...createForm, email: e.target.value })
              }
              className="h-9 text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Phone Number
              </label>
              <Input
                placeholder="e.g. +91 98400 12345"
                value={createForm.phoneNumber || ""}
                onChange={(e) =>
                  setCreateForm({ ...createForm, phoneNumber: e.target.value })
                }
                className="h-9 text-xs"
              />
            </div>
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Initial Password
              </label>
              <Input
                type="password"
                value={createForm.password}
                onChange={(e) =>
                  setCreateForm({ ...createForm, password: e.target.value })
                }
                className="h-9 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Initial Role Assignment
            </label>
            <select
              value={createForm.roleId}
              onChange={(e) =>
                setCreateForm({ ...createForm, roleId: e.target.value })
              }
              className="w-full h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">-- No initial role (assign later) --</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.displayName || r.name} ({r.name})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateUserOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={actionLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {actionLoading ? "Creating..." : "Create Account"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* ASSIGN ROLE MODAL */}
      <Dialog
        open={assignRoleOpen}
        onClose={() => setAssignRoleOpen(false)}
        title="Assign Role to User"
        description={`Grant a new system role to ${targetUser?.email}.`}
      >
        <form onSubmit={handleAssignRole} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Select Role *
            </label>
            <select
              required
              value={assignRoleForm.roleId}
              onChange={(e) =>
                setAssignRoleForm({ ...assignRoleForm, roleId: e.target.value })
              }
              className="w-full h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">-- Select a Role --</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.displayName || r.name} ({r.name})
                </option>
              ))}
            </select>
          </div>

          <div className="p-3 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 text-[11px] text-slate-600 dark:text-slate-400">
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              Note:{" "}
            </span>
            Assigning privileged roles grants immediate access across backend
            APIs. Ensure compliance with institution governance policies.
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAssignRoleOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={actionLoading || !assignRoleForm.roleId}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {actionLoading ? "Assigning..." : "Confirm Role Assignment"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* REVOKE ROLE CONFIRMATION MODAL */}
      <Dialog
        open={revokeConfirmOpen}
        onClose={() => setRevokeConfirmOpen(false)}
        title="Confirm Role Revocation"
        description="Are you sure you want to revoke this role?"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-800 dark:text-red-300">
            <div className="font-semibold flex items-center gap-1.5 mb-1">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              Destructive Privilege Change
            </div>
            <p>
              Revoking <strong>{revokeTarget?.roleName}</strong> from{" "}
              <strong>{revokeTarget?.user.email}</strong> will terminate all
              capabilities associated with this role immediately.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setRevokeConfirmOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={handleRevokeRole}
              disabled={actionLoading}
            >
              {actionLoading ? "Revoking..." : "Revoke Role"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* STATUS TOGGLE CONFIRMATION MODAL */}
      <Dialog
        open={statusConfirmOpen}
        onClose={() => setStatusConfirmOpen(false)}
        title="Confirm Account Status Change"
        description="Modify active status for this user identity."
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600 dark:text-slate-400">
            Are you sure you want to change the status of{" "}
            <strong>{statusTarget?.user.email}</strong> to{" "}
            <strong className="uppercase">{statusTarget?.newStatus}</strong>?
          </p>

          {statusTarget?.newStatus === "SUSPENDED" && (
            <div className="p-3 rounded bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300">
              Suspended users will be immediately locked out of all portal login
              sessions until reactivated.
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setStatusConfirmOpen(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant={
                statusTarget?.newStatus === "SUSPENDED"
                  ? "destructive"
                  : "primary"
              }
              size="sm"
              onClick={handleStatusToggle}
              disabled={actionLoading}
              className={
                statusTarget?.newStatus === "ACTIVE"
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : ""
              }
            >
              {actionLoading
                ? "Updating..."
                : `Confirm ${statusTarget?.newStatus}`}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
