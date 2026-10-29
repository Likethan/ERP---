"use client";

import React, { useEffect, useState } from "react";
import {
  KeyRound,
  ShieldCheck,
  Clock,
  Ban,
  Plus,
  Search,
  Filter,
  User,
  Calendar,
  AlertCircle,
  FileCheck,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { AccessGrant, SecurityZone } from "@/types/campus-security";

export default function AccessGrantsPage() {
  const [grants, setGrants] = useState<AccessGrant[]>([]);
  const [zones, setZones] = useState<SecurityZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Revoke Modal
  const [revokingGrant, setRevokingGrant] = useState<AccessGrant | null>(null);
  const [revocationReason, setRevocationReason] = useState("");
  const [revoking, setRevoking] = useState(false);

  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const now = new Date();
  const defaultValidFrom = now.toISOString().slice(0, 16);
  const defaultValidUntil = new Date(now.getTime() + 7 * 24 * 3600 * 1000).toISOString().slice(0, 16);

  // Form state
  const [form, setForm] = useState({
    zone_id: "",
    grantee_type: "STAFF" as "STUDENT" | "STAFF" | "CONTRACTOR" | "VISITOR",
    grantee_id: "",
    grantee_name: "",
    valid_from: defaultValidFrom,
    valid_until: defaultValidUntil,
    is_temporary: true,
    grant_reason: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [grantsData, zonesData] = await Promise.all([
        CampusSecurityService.listAccessGrants(),
        CampusSecurityService.listZones(),
      ]);
      setGrants(grantsData);
      setZones(zonesData);
      if (zonesData.length > 0 && !form.zone_id) {
        setForm((prev) => ({ ...prev, zone_id: zonesData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load access grants:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.grantee_name || !form.grant_reason || !form.zone_id) return;

    try {
      setSubmitting(true);
      await CampusSecurityService.createAccessGrant({
        zone_id: form.zone_id,
        grantee_type: form.grantee_type,
        grantee_id: form.grantee_id || `USR-${Date.now().toString().slice(-4)}`,
        grantee_name: form.grantee_name,
        valid_from: new Date(form.valid_from).toISOString(),
        valid_until: new Date(form.valid_until).toISOString(),
        is_temporary: form.is_temporary,
        grant_reason: form.grant_reason,
      });

      setNotification({
        type: "success",
        message: `Logical access grant created for ${form.grantee_name}.`,
      });
      setIsModalOpen(false);
      setForm({
        zone_id: zones[0]?.id || "",
        grantee_type: "STAFF",
        grantee_id: "",
        grantee_name: "",
        valid_from: defaultValidFrom,
        valid_until: defaultValidUntil,
        is_temporary: true,
        grant_reason: "",
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to issue access grant. Please verify inputs.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokeGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revokingGrant || !revocationReason) return;

    try {
      setRevoking(true);
      await CampusSecurityService.revokeAccessGrant(revokingGrant.id, revocationReason);
      setNotification({
        type: "success",
        message: `Grant ${revokingGrant.grant_number} successfully revoked.`,
      });
      setRevokingGrant(null);
      setRevocationReason("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to revoke access grant.",
      });
    } finally {
      setRevoking(false);
    }
  };

  const filteredGrants = grants.filter((g) => {
    const matchesSearch =
      g.grantee_name.toLowerCase().includes(search.toLowerCase()) ||
      g.grant_number.toLowerCase().includes(search.toLowerCase()) ||
      g.grant_reason.toLowerCase().includes(search.toLowerCase());

    const matchesType = typeFilter === "ALL" || g.grantee_type === typeFilter;
    const matchesStatus = statusFilter === "ALL" || g.status === statusFilter;

    return matchesSearch && matchesType && matchesStatus;
  });

  const activeGrantsCount = grants.filter((g) => g.status === "ACTIVE").length;
  const tempGrantsCount = grants.filter((g) => g.is_temporary && g.status === "ACTIVE").length;
  const revokedGrantsCount = grants.filter((g) => g.status === "REVOKED").length;

  const getZoneName = (zoneId: string) => {
    const zone = zones.find((z) => z.id === zoneId);
    return zone ? `${zone.name} (${zone.code})` : zoneId;
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Access Grants & Authorization Registry
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              Audit-Enforced
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Issue, audit, and revoke time-bounded zone authorizations for students, staff, research fellows, and technical contractors.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Issue Access Grant
        </button>
      </div>

      {/* Nav */}
      <SecurityNav />

      {/* Notification banner */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between text-sm ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800"
              : "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-200 border border-red-200 dark:border-red-800"
          }`}
        >
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs font-bold"
          >
            DISMISS
          </button>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Grants Issued</span>
            <FileCheck className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{grants.length}</div>
          <div className="text-xs text-slate-500 mt-1">Historical authorization log</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Grants</span>
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{activeGrantsCount}</div>
          <div className="text-xs text-slate-500 mt-1">Currently valid permissions</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Temporary Passes</span>
            <Clock className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-2">{tempGrantsCount}</div>
          <div className="text-xs text-slate-500 mt-1">Subject to automatic expiry</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Revoked Grants</span>
            <Ban className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">{revokedGrantsCount}</div>
          <div className="text-xs text-slate-500 mt-1">Terminated for security policy</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search grantee, grant number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-slate-400 mr-1 shrink-0" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">All Grantee Types</option>
              <option value="STAFF">Staff</option>
              <option value="STUDENT">Student</option>
              <option value="CONTRACTOR">Contractor</option>
              <option value="VISITOR">Visitor</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="EXPIRED">EXPIRED</option>
              <option value="REVOKED">REVOKED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grants Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4">Grant Number</th>
                <th className="px-6 py-4">Grantee</th>
                <th className="px-6 py-4">Authorized Zone</th>
                <th className="px-6 py-4">Validity Window</th>
                <th className="px-6 py-4">Justification</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    Loading access grants...
                  </td>
                </tr>
              ) : filteredGrants.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No access grants matching criteria.
                  </td>
                </tr>
              ) : (
                filteredGrants.map((grant) => (
                  <tr key={grant.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                        {grant.grant_number}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {grant.is_temporary ? "Temporary Pass" : "Permanent Clearance"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900 dark:text-white flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        {grant.grantee_name}
                      </div>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 mt-1">
                        {grant.grantee_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-900 dark:text-slate-200 font-medium">
                        {getZoneName(grant.zone_id)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        {new Date(grant.valid_from).toLocaleDateString()} – {new Date(grant.valid_until).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 max-w-xs truncate" title={grant.grant_reason}>
                      <span className="text-xs text-slate-600 dark:text-slate-400">{grant.grant_reason}</span>
                    </td>
                    <td className="px-6 py-4">
                      {grant.status === "ACTIVE" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                          <ShieldCheck className="w-3 h-3" /> ACTIVE
                        </span>
                      )}
                      {grant.status === "EXPIRED" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                          <Clock className="w-3 h-3" /> EXPIRED
                        </span>
                      )}
                      {grant.status === "REVOKED" && (
                        <div>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
                            <Ban className="w-3 h-3" /> REVOKED
                          </span>
                          {grant.revocation_reason && (
                            <div className="text-[10px] text-red-600 dark:text-red-400 mt-0.5">
                              {grant.revocation_reason}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {grant.status === "ACTIVE" ? (
                        <button
                          onClick={() => setRevokingGrant(grant)}
                          className="px-2.5 py-1 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded border border-red-200 dark:border-red-900"
                        >
                          Revoke
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Issue Grant Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-indigo-600" />
                Issue Logical Access Grant
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateGrant} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Grantee Type *
                  </label>
                  <select
                    value={form.grantee_type}
                    onChange={(e) => setForm({ ...form, grantee_type: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="STAFF">Faculty / Staff</option>
                    <option value="STUDENT">Student Researcher</option>
                    <option value="CONTRACTOR">Contractor / Vendor</option>
                    <option value="VISITOR">Official Guest</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Grantee Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Jane Doe"
                    value={form.grantee_name}
                    onChange={(e) => setForm({ ...form, grantee_name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Target Clearance Zone *
                </label>
                <select
                  value={form.zone_id}
                  onChange={(e) => setForm({ ...form, zone_id: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                >
                  {zones.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name} ({zone.code}) - {zone.clearance_level}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Valid From *
                  </label>
                  <input
                    type="datetime-local"
                    value={form.valid_from}
                    onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Valid Until *
                  </label>
                  <input
                    type="datetime-local"
                    value={form.valid_until}
                    onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Grant Justification / Purpose *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Detail operational necessity, project assignment, or authorized supervisor approval..."
                  value={form.grant_reason}
                  onChange={(e) => setForm({ ...form, grant_reason: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="is_temporary"
                  checked={form.is_temporary}
                  onChange={(e) => setForm({ ...form, is_temporary: e.target.checked })}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <label htmlFor="is_temporary" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Temporary Time-Bounded Grant (Revokes automatically upon expiration)
                </label>
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {submitting ? "Granting..." : "Authorize Grant"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Revocation Modal */}
      {revokingGrant && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-md shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-red-600 dark:text-red-400 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Revoke Access Grant
              </h2>
              <button
                onClick={() => setRevokingGrant(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleRevokeGrant} className="p-6 space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">
                You are revoking access grant <strong className="font-mono text-slate-900 dark:text-white">{revokingGrant.grant_number}</strong> for{" "}
                <strong className="text-slate-900 dark:text-white">{revokingGrant.grantee_name}</strong>. This action takes effect immediately.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Reason for Revocation *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Security policy breach, work completed, or role reassignment..."
                  value={revocationReason}
                  onChange={(e) => setRevocationReason(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setRevokingGrant(null)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={revoking}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {revoking ? "Revoking..." : "Confirm Revocation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

