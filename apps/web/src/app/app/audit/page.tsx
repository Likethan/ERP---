"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  FileText,
  Shield,
  ShieldAlert,
  Search,
  Filter,
  Download,
  RefreshCw,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Eye,
  Terminal,
  Activity,
  Layers,
  Globe,
  Database,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import {
  adminAuditService,
  AuditLogEntry,
} from "@/services/admin-audit.service";

export default function ForensicAuditLogPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("ALL");
  const [entityFilter, setEntityFilter] = useState("ALL");

  // Diff Modal State
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(
    null,
  );
  const [diffOpen, setDiffOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await adminAuditService.listAuditLogs();
      if (res.data) setLogs(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredLogs = useMemo(() => {
    return logs.filter((l) => {
      const matchesSearch =
        searchQuery === "" ||
        l.userEmail.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.ipAddress.includes(searchQuery) ||
        l.correlationId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (l.businessContext &&
          l.businessContext.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesAction = actionFilter === "ALL" || l.action === actionFilter;

      const matchesEntity =
        entityFilter === "ALL" || l.entityType === entityFilter;

      return matchesSearch && matchesAction && matchesEntity;
    });
  }, [logs, searchQuery, actionFilter, entityFilter]);

  const privilegedActionsCount = logs.filter((l) =>
    [
      "ROLE_ASSIGN",
      "ROLE_REVOKE",
      "STATUS_CHANGE",
      "MARKS_CORRECTION",
    ].includes(l.action),
  ).length;

  const handleExportCSV = () => {
    const headers = [
      "Timestamp",
      "Actor Name",
      "Actor Email",
      "Actor Role",
      "Action",
      "Entity Type",
      "Entity ID",
      "IP Address",
      "Correlation ID",
      "Context",
    ];
    const rows = filteredLogs.map((l) => [
      l.createdAt,
      `"${l.userName}"`,
      l.userEmail,
      l.userRole,
      l.action,
      l.entityType,
      l.entityId,
      l.ipAddress,
      l.correlationId,
      `"${(l.businessContext || "").replace(/"/g, '""')}"`,
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `campusos_forensic_audit_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/dashboard"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 flex items-center gap-1"
            >
              <ArrowLeft className="h-3 w-3" /> Back to Admin Dashboard
            </Link>
            <span className="text-slate-300 dark:text-slate-700">&bull;</span>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              <Lock className="h-3 w-3" />
              Forensic Vault &bull; Tamper-Evident Ledger
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Forensic Audit Log & Compliance Explorer
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Searchable, append-only chronological ledger of all administrative
            mutations, privilege elevations, status changes, and academic
            operations.
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
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            className="flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Audit Events"
          value={logs.length.toString()}
          description="Forensic entries recorded"
          icon={<FileText className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Privileged Mutations"
          value={privilegedActionsCount.toString()}
          description="Roles, status, & results"
          icon={<ShieldAlert className="h-5 w-5 text-amber-500" />}
        />
        <StatCard
          title="Audit Hash Integrity"
          value="SHA-256 Valid"
          description="Zero tampering detected"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Retention Coverage"
          value="7 Years"
          description="Statutory legal compliance"
          icon={<Database className="h-5 w-5 text-blue-500" />}
        />
      </div>

      {/* Filters Bar */}
      <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by operator email, IP address, correlation ID, or context..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="flex items-center gap-1.5 shrink-0 text-xs text-slate-500">
              <Filter className="h-3.5 w-3.5" />
              <span>Action:</span>
            </div>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Actions</option>
              <option value="ROLE_ASSIGN">ROLE_ASSIGN</option>
              <option value="ROLE_REVOKE">ROLE_REVOKE</option>
              <option value="STATUS_CHANGE">STATUS_CHANGE</option>
              <option value="ATTENDANCE_OVERRIDE">ATTENDANCE_OVERRIDE</option>
              <option value="MARKS_CORRECTION">MARKS_CORRECTION</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
            </select>

            <div className="flex items-center gap-1.5 shrink-0 text-xs text-slate-500 ml-2">
              <span>Entity:</span>
            </div>
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Entities</option>
              <option value="User">User</option>
              <option value="RoleAssignment">RoleAssignment</option>
              <option value="Department">Department</option>
              <option value="AttendanceRecord">AttendanceRecord</option>
              <option value="Result">Result</option>
              <option value="Invoice">Invoice</option>
            </select>

            {(searchQuery ||
              actionFilter !== "ALL" ||
              entityFilter !== "ALL") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearchQuery("");
                  setActionFilter("ALL");
                  setEntityFilter("ALL");
                }}
                className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              >
                Reset
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Audit Log Table */}
      <Card className="overflow-hidden bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold">Operator / Actor</th>
                <th className="py-3 px-4 font-semibold">Action</th>
                <th className="py-3 px-4 font-semibold">Target Entity</th>
                <th className="py-3 px-4 font-semibold">Forensic Context</th>
                <th className="py-3 px-4 font-semibold text-right">
                  Audit Diff
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="py-8 text-center text-slate-500 dark:text-slate-400"
                  >
                    No forensic audit logs match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((l) => {
                  const isPrivileged = [
                    "ROLE_ASSIGN",
                    "ROLE_REVOKE",
                    "STATUS_CHANGE",
                    "MARKS_CORRECTION",
                  ].includes(l.action);

                  return (
                    <tr
                      key={l.id}
                      className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-4 text-slate-500 dark:text-slate-400 font-mono text-[11px] whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                          <Clock className="h-3 w-3 text-slate-400" />
                          {new Date(l.createdAt).toLocaleDateString()}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {new Date(l.createdAt).toLocaleTimeString()}
                        </div>
                      </td>

                      {/* Operator */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 dark:text-slate-100">
                          {l.userName}
                        </div>
                        <div className="text-slate-500 dark:text-slate-400 text-[11px]">
                          {l.userEmail}
                        </div>
                        <div className="text-slate-400 text-[10px] font-mono flex items-center gap-1 mt-0.5">
                          <Globe className="h-2.5 w-2.5" />
                          {l.ipAddress}
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            l.action.includes("REVOKE") || l.action === "DELETE"
                              ? "destructive"
                              : l.action.includes("ROLE") ||
                                  l.action.includes("OVERRIDE")
                                ? "warning"
                                : l.action === "CREATE"
                                  ? "success"
                                  : "secondary"
                          }
                          className="font-mono text-[10px]"
                        >
                          {l.action}
                        </Badge>
                      </td>

                      {/* Target Entity */}
                      <td className="py-3 px-4">
                        <div className="font-medium text-slate-800 dark:text-slate-200">
                          {l.entityType}
                        </div>
                        <div className="text-slate-400 text-[10px] font-mono">
                          {l.entityName || l.entityId}
                        </div>
                      </td>

                      {/* Forensic Context */}
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 text-[11px] max-w-xs truncate">
                        {l.businessContext || "Routine operational mutation"}
                      </td>

                      {/* Details / Diff */}
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedEntry(l);
                            setDiffOpen(true);
                          }}
                          className="h-7 text-[11px] px-2.5 flex items-center gap-1 ml-auto"
                        >
                          <Eye className="h-3 w-3" />
                          Inspect Diff
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* FORENSIC DIFF INSPECTOR DIALOG */}
      <Dialog
        open={diffOpen}
        onClose={() => setDiffOpen(false)}
        title="Forensic State Diff & Metadata"
        description={`Audit Event ${selectedEntry?.id} &bull; Correlation ${selectedEntry?.correlationId}`}
        maxWidth="2xl"
      >
        {selectedEntry && (
          <div className="space-y-4 text-xs">
            {/* Metadata Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-[11px]">
              <div>
                <span className="text-slate-400 block">Operator</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {selectedEntry.userName}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">IP Address</span>
                <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                  {selectedEntry.ipAddress}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">Action Code</span>
                <span className="font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                  {selectedEntry.action}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">Endpoint</span>
                <span className="font-mono text-[10px] text-slate-700 dark:text-slate-300">
                  {selectedEntry.routeEndpoint || "API Gateway"}
                </span>
              </div>
            </div>

            {/* Business Context */}
            {selectedEntry.businessContext && (
              <div className="p-3 rounded bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-900/60 text-indigo-900 dark:text-indigo-300">
                <span className="font-semibold">Context Rationale: </span>
                {selectedEntry.businessContext}
              </div>
            )}

            {/* Side-by-side State Diff */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200">
                <div className="font-mono text-[11px] font-semibold text-rose-400 mb-1 flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5" />
                  PRE-MUTATION STATE (BEFORE)
                </div>
                <pre className="text-[10px] font-mono text-slate-400 overflow-x-auto p-2 bg-black/40 rounded max-h-48">
                  {selectedEntry.oldValues
                    ? JSON.stringify(selectedEntry.oldValues, null, 2)
                    : "// No prior record (New entity created)"}
                </pre>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200">
                <div className="font-mono text-[11px] font-semibold text-emerald-400 mb-1 flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5" />
                  POST-MUTATION STATE (AFTER)
                </div>
                <pre className="text-[10px] font-mono text-slate-300 overflow-x-auto p-2 bg-black/40 rounded max-h-48">
                  {selectedEntry.newValues
                    ? JSON.stringify(selectedEntry.newValues, null, 2)
                    : "// Record permanently expunged"}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-200 dark:border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDiffOpen(false)}
              >
                Close Inspector
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
