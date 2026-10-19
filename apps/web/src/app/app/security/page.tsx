"use client";

import React, { useEffect, useState } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Clock,
  KeyRound,
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
  Plus,
  RefreshCw,
  Search,
  Filter,
} from "lucide-react";

interface SocOverview {
  critical_incidents: number;
  high_incidents: number;
  medium_incidents: number;
  low_incidents: number;
  recent_detections_24h: number;
  pending_action_approvals: number;
  oldest_unresolved_hours: number;
  timestamp: string;
}

interface IncidentItem {
  id: string;
  incident_number: string;
  title: string;
  description: string;
  severity: string;
  confidence: string;
  status: string;
  created_at: string;
  detections?: DetectionItem[];
  notes?: NoteItem[];
  actions?: ActionItem[];
  remediation_tasks?: TaskItem[];
}

interface DetectionItem {
  id: string;
  rule_id: string;
  event_type: string;
  severity: string;
  detection_source: string;
  actor_type: string;
  actor_id: string | null;
  ip_address: string;
  occurrence_count: number;
  last_seen_at: string;
  status: string;
}

interface NoteItem {
  id: string;
  note_type: string;
  content: string;
  created_at: string;
}

interface ActionItem {
  id: string;
  action_type: string;
  target_type: string;
  target_identifier: string;
  risk_level: string;
  requires_approval: boolean;
  status: string;
  idempotency_key: string;
  created_at: string;
}

interface TaskItem {
  id: string;
  title: string;
  status: string;
  due_at: string | null;
}

interface RuleItem {
  id: string;
  rule_id: string;
  name: string;
  category: string;
  severity: string;
  is_enabled: boolean;
  evaluation_window_seconds: number;
  threshold: number;
  recommended_action: string | null;
}

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<"soc" | "credentials">("soc");

  // SOC state
  const [socSubTab, setSocSubTab] = useState<"incidents" | "detections" | "rules" | "actions">("incidents");
  const [overview, setOverview] = useState<SocOverview | null>(null);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [detections, setDetections] = useState<DetectionItem[]>([]);
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [socError, setSocError] = useState<string | null>(null);

  // Filter & Search
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Incident status update dialog state
  const [newStatus, setNewStatus] = useState<string>("");
  const [transitionReason, setTransitionReason] = useState<string>("");
  const [newNoteContent, setNewNoteContent] = useState<string>("");

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Policy validation
  const hasMinLength = newPassword.length >= 8;
  const hasUpper = /[A-Z]/.test(newPassword);
  const hasLower = /[a-z]/.test(newPassword);
  const hasNumberOrSpecial = /[0-9!@#$%^&*(),.?":{}|<>]/.test(newPassword);
  const isMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const isFormValid =
    currentPassword.length > 0 &&
    hasMinLength &&
    hasUpper &&
    hasLower &&
    hasNumberOrSpecial &&
    isMatch;

  const loadSocData = async () => {
    setLoading(true);
    setSocError(null);
    try {
      const [overviewData, incidentsData, detectionsData, rulesData] = await Promise.allSettled([
        apiFetch<SocOverview>("/api/v1/security/overview"),
        apiFetch<{ items: IncidentItem[]; total: number }>("/api/v1/security/incidents"),
        apiFetch<{ items: DetectionItem[]; total: number }>("/api/v1/security/detections"),
        apiFetch<RuleItem[]>("/api/v1/security/rules"),
      ]);

      if (overviewData.status === "fulfilled") setOverview(overviewData.value.data);
      if (incidentsData.status === "fulfilled") setIncidents(incidentsData.value.data?.items || []);
      if (detectionsData.status === "fulfilled") setDetections(detectionsData.value.data?.items || []);
      if (rulesData.status === "fulfilled") setRules(rulesData.value.data || []);
    } catch (err: unknown) {
      if (err instanceof Error) setSocError(err.message);
      else setSocError("Failed to fetch security operations data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "soc") {
      loadSocData();
    }
  }, [activeTab]);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await apiFetch<{ message: string }>("/api/v1/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      setSuccessMessage("Password changed successfully. All other active sessions have been invalidated across devices.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.errorResponse.error.message || "Failed to update password.");
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred while changing password.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusTransition = async (incidentId: string) => {
    if (!newStatus) return;
    try {
      const updated = await apiFetch<IncidentItem>(`/api/v1/security/incidents/${incidentId}/status`, {
        method: "POST",
        body: JSON.stringify({
          status: newStatus,
          reason: transitionReason || undefined,
        }),
      });
      setSelectedIncident(updated.data);
      setNewStatus("");
      setTransitionReason("");
      loadSocData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update status");
    }
  };

  const handleAddNote = async (incidentId: string) => {
    if (!newNoteContent.trim()) return;
    try {
      await apiFetch(`/api/v1/security/incidents/${incidentId}/notes`, {
        method: "POST",
        body: JSON.stringify({
          content: newNoteContent,
          note_type: "INVESTIGATION",
        }),
      });
      setNewNoteContent("");
      // Refresh selected incident details
      const refreshed = await apiFetch<IncidentItem>(`/api/v1/security/incidents/${incidentId}`);
      setSelectedIncident(refreshed.data);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to add note");
    }
  };

  const handleExecuteAction = async (actionId: string) => {
    try {
      await apiFetch(`/api/v1/security/actions/${actionId}/execute`, {
        method: "POST",
      });
      if (selectedIncident) {
        const refreshed = await apiFetch<IncidentItem>(`/api/v1/security/incidents/${selectedIncident.id}`);
        setSelectedIncident(refreshed.data);
      }
      loadSocData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to execute containment action");
    }
  };

  const handleApproveAction = async (actionId: string) => {
    try {
      await apiFetch(`/api/v1/security/actions/${actionId}/approve`, {
        method: "POST",
      });
      if (selectedIncident) {
        const refreshed = await apiFetch<IncidentItem>(`/api/v1/security/incidents/${selectedIncident.id}`);
        setSelectedIncident(refreshed.data);
      }
      loadSocData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to approve containment action");
    }
  };

  const handleToggleRule = async (ruleId: string, currentEnabled: boolean) => {
    try {
      await apiFetch(`/api/v1/security/rules/${ruleId}`, {
        method: "PATCH",
        body: JSON.stringify({
          is_enabled: !currentEnabled,
        }),
      });
      loadSocData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to toggle rule");
    }
  };

  const getSeverityBadgeVariant = (sev: string): "destructive" | "warning" | "info" | "secondary" | "neutral" => {
    switch (sev.toUpperCase()) {
      case "CRITICAL":
        return "destructive";
      case "HIGH":
        return "warning";
      case "MEDIUM":
        return "secondary";
      case "LOW":
        return "info";
      default:
        return "neutral";
    }
  };

  const getStatusBadgeVariant = (st: string): "destructive" | "warning" | "success" | "info" | "secondary" | "neutral" => {
    switch (st.toUpperCase()) {
      case "NEW":
        return "destructive";
      case "TRIAGED":
      case "INVESTIGATING":
        return "warning";
      case "CONTAINED":
      case "REMEDIATING":
        return "secondary";
      case "RESOLVED":
      case "CLOSED":
        return "success";
      case "REOPENED":
        return "warning";
      default:
        return "neutral";
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (statusFilter !== "ALL" && inc.status.toUpperCase() !== statusFilter) return false;
    if (severityFilter !== "ALL" && inc.severity.toUpperCase() !== severityFilter) return false;
    if (
      searchQuery &&
      !inc.incident_number.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !inc.title.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header and Top-level Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <ShieldAlert className="h-6 w-6 text-indigo-400" />
            Security & Operations Center
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Enterprise threat detection, incident containment, forensic investigation, and credential governance.
          </p>
        </div>

        <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("soc")}
            className={`px-4 py-2 text-xs font-semibold rounded-md transition-colors ${
              activeTab === "soc"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Security Operations (SOC)
          </button>
          <button
            onClick={() => setActiveTab("credentials")}
            className={`px-4 py-2 text-xs font-semibold rounded-md transition-colors ${
              activeTab === "credentials"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Account Credentials
          </button>
        </div>
      </div>

      {/* TAB 1: SOC DASHBOARD */}
      {activeTab === "soc" && (
        <div className="space-y-6">
          {/* Telemetry Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <StatCard
              title="Critical Threats"
              value={overview?.critical_incidents ?? 0}
              subtitle="Immediate action required"
              icon={<ShieldAlert className="h-5 w-5 text-red-400" />}
              variant={overview && overview.critical_incidents > 0 ? "amber" : "default"}
            />
            <StatCard
              title="High Threats"
              value={overview?.high_incidents ?? 0}
              subtitle="Active investigation"
              icon={<AlertTriangle className="h-5 w-5 text-amber-400" />}
              variant="default"
            />
            <StatCard
              title="Signals (24h)"
              value={overview?.recent_detections_24h ?? 0}
              subtitle="Normalized detections"
              icon={<Activity className="h-5 w-5 text-sky-400" />}
              variant="default"
            />
            <StatCard
              title="Pending Approvals"
              value={overview?.pending_action_approvals ?? 0}
              subtitle="Containment actions"
              icon={<Clock className="h-5 w-5 text-purple-400" />}
              variant="default"
            />
            <StatCard
              title="Oldest Unresolved"
              value={`${overview?.oldest_unresolved_hours ?? 0}h`}
              subtitle="Age of open incidents"
              icon={<ShieldCheck className="h-5 w-5 text-emerald-400" />}
              variant="default"
            />
          </div>

          {socError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
              {socError}
            </div>
          )}

          {/* SOC Navigation & Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex gap-2">
              <button
                onClick={() => setSocSubTab("incidents")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border ${
                  socSubTab === "incidents"
                    ? "bg-slate-800 border-indigo-500 text-white"
                    : "border-slate-800 text-slate-400 hover:bg-slate-900"
                }`}
              >
                Incidents ({incidents.length})
              </button>
              <button
                onClick={() => setSocSubTab("detections")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border ${
                  socSubTab === "detections"
                    ? "bg-slate-800 border-indigo-500 text-white"
                    : "border-slate-800 text-slate-400 hover:bg-slate-900"
                }`}
              >
                Detections ({detections.length})
              </button>
              <button
                onClick={() => setSocSubTab("rules")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border ${
                  socSubTab === "rules"
                    ? "bg-slate-800 border-indigo-500 text-white"
                    : "border-slate-800 text-slate-400 hover:bg-slate-900"
                }`}
              >
                Detection Rules ({rules.length})
              </button>
            </div>

            <button
              onClick={loadSocData}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded border border-slate-800 hover:bg-slate-900"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh Telemetry
            </button>
          </div>

          {/* SUBTAB 1: INCIDENTS TABLE */}
          {socSubTab === "incidents" && (
            <div className="space-y-4">
              {/* Search & Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search by incident # or title..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-800 bg-slate-900 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Status:</span>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="text-xs rounded-lg border border-slate-800 bg-slate-900 text-slate-300 px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="NEW">New</option>
                    <option value="TRIAGED">Triaged</option>
                    <option value="INVESTIGATING">Investigating</option>
                    <option value="CONTAINED">Contained</option>
                    <option value="REMEDIATING">Remediating</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="CLOSED">Closed</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Severity:</span>
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                    className="text-xs rounded-lg border border-slate-800 bg-slate-900 text-slate-300 px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="ALL">All Severities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              {/* Incidents Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Incident #</th>
                      <th className="py-3 px-4">Title</th>
                      <th className="py-3 px-4">Severity</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Created</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {filteredIncidents.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-500">
                          No security incidents found matching criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredIncidents.map((inc) => (
                        <tr key={inc.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3.5 px-4 font-mono font-medium text-indigo-400">
                            {inc.incident_number}
                          </td>
                          <td className="py-3.5 px-4 font-medium text-white max-w-xs truncate">
                            {inc.title}
                          </td>
                          <td className="py-3.5 px-4">
                            <Badge variant={getSeverityBadgeVariant(inc.severity)}>
                              {inc.severity}
                            </Badge>
                          </td>
                          <td className="py-3.5 px-4">
                            <Badge variant={getStatusBadgeVariant(inc.status)}>
                              {inc.status}
                            </Badge>
                          </td>
                          <td className="py-3.5 px-4 text-slate-400">
                            {new Date(inc.created_at).toLocaleString()}
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={async () => {
                                const details = await apiFetch<IncidentItem>(`/api/v1/security/incidents/${inc.id}`);
                                setSelectedIncident(details.data);
                              }}
                              className="text-indigo-400 hover:text-indigo-300 font-medium px-2 py-1 rounded hover:bg-indigo-950/50"
                            >
                              Inspect Details →
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SUBTAB 2: DETECTIONS TABLE */}
          {socSubTab === "detections" && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Rule ID</th>
                    <th className="py-3 px-4">Event Type</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">IP Address</th>
                    <th className="py-3 px-4">Count</th>
                    <th className="py-3 px-4">Last Seen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {detections.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No active detections recorded.
                      </td>
                    </tr>
                  ) : (
                    detections.map((det) => (
                      <tr key={det.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4 font-mono font-medium text-amber-400">
                          {det.rule_id}
                        </td>
                        <td className="py-3 px-4 text-white font-medium">{det.event_type}</td>
                        <td className="py-3 px-4 text-slate-400">{det.detection_source}</td>
                        <td className="py-3 px-4 text-slate-300">{det.actor_id || "ANONYMOUS"}</td>
                        <td className="py-3 px-4 font-mono text-slate-400">{det.ip_address}</td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-200">
                            {det.occurrence_count}x
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {new Date(det.last_seen_at).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* SUBTAB 3: DETECTION RULES CONFIGURATION */}
          {socSubTab === "rules" && (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Rule ID</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Window</th>
                    <th className="py-3 px-4">Threshold</th>
                    <th className="py-3 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-indigo-400">{rule.rule_id}</td>
                      <td className="py-3.5 px-4 font-medium text-white">{rule.name}</td>
                      <td className="py-3.5 px-4 text-slate-400">{rule.category}</td>
                      <td className="py-3.5 px-4">
                        <Badge variant={getSeverityBadgeVariant(rule.severity)}>{rule.severity}</Badge>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">{rule.evaluation_window_seconds}s</td>
                      <td className="py-3.5 px-4 font-medium text-white">{rule.threshold} events</td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleToggleRule(rule.rule_id, rule.is_enabled)}
                          className={`px-2.5 py-1 text-xs font-semibold rounded ${
                            rule.is_enabled
                              ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800 hover:bg-emerald-900/80"
                              : "bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700"
                          }`}
                        >
                          {rule.is_enabled ? "Enabled" : "Disabled"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* INCIDENT DETAILS DRAWER / MODAL */}
          {selectedIncident && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
              <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div>
                    <span className="font-mono text-xs text-indigo-400 font-semibold">
                      {selectedIncident.incident_number}
                    </span>
                    <h2 className="text-lg font-bold text-white mt-1">{selectedIncident.title}</h2>
                  </div>
                  <button
                    onClick={() => setSelectedIncident(null)}
                    className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800"
                  >
                    ✕
                  </button>
                </div>

                {/* Metadata & Status */}
                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950 p-4 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-slate-500">Severity: </span>
                    <Badge variant={getSeverityBadgeVariant(selectedIncident.severity)}>
                      {selectedIncident.severity}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-slate-500">Current Status: </span>
                    <Badge variant={getStatusBadgeVariant(selectedIncident.status)}>
                      {selectedIncident.status}
                    </Badge>
                  </div>
                  <div className="col-span-2 text-slate-300 whitespace-pre-line mt-1">
                    {selectedIncident.description}
                  </div>
                </div>

                {/* Lifecycle Transition Action */}
                <div className="space-y-3 bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    State Machine Transition
                  </h3>
                  <div className="flex gap-2">
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="text-xs rounded border border-slate-700 bg-slate-900 text-white px-2 py-1.5 focus:outline-none"
                    >
                      <option value="">Select Next State...</option>
                      <option value="TRIAGED">Triaged</option>
                      <option value="INVESTIGATING">Investigating</option>
                      <option value="CONTAINED">Contained</option>
                      <option value="REMEDIATING">Remediating</option>
                      <option value="RESOLVED">Resolved</option>
                      <option value="CLOSED">Closed</option>
                      <option value="REOPENED">Reopened</option>
                    </select>

                    <input
                      type="text"
                      placeholder="Transition reason / closure summary..."
                      value={transitionReason}
                      onChange={(e) => setTransitionReason(e.target.value)}
                      className="flex-1 text-xs rounded border border-slate-700 bg-slate-900 text-white px-2.5 py-1.5 focus:outline-none"
                    />

                    <button
                      onClick={() => handleStatusTransition(selectedIncident.id)}
                      disabled={!newStatus}
                      className="px-3 py-1.5 text-xs font-semibold rounded bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50"
                    >
                      Update State
                    </button>
                  </div>
                </div>

                {/* Containment Response Actions */}
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Containment & Response Actions
                  </h3>
                  {selectedIncident.actions && selectedIncident.actions.length > 0 ? (
                    <div className="space-y-2">
                      {selectedIncident.actions.map((act) => (
                        <div
                          key={act.id}
                          className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950 text-xs"
                        >
                          <div>
                            <span className="font-semibold text-white">{act.action_type}</span>
                            <span className="text-slate-400 ml-2">→ {act.target_identifier}</span>
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              Status: <span className="text-indigo-300 font-mono">{act.status}</span> | Risk: {act.risk_level}
                            </div>
                          </div>

                          <div className="flex gap-2">
                            {act.status === "PROPOSED" && act.requires_approval && (
                              <button
                                onClick={() => handleApproveAction(act.id)}
                                className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium"
                              >
                                Approve
                              </button>
                            )}
                            {act.status === "APPROVED" && (
                              <button
                                onClick={() => handleExecuteAction(act.id)}
                                className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
                              >
                                Execute
                              </button>
                            )}
                            {act.status === "EXECUTED" && (
                              <span className="text-emerald-400 font-medium">✓ Executed</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No response actions proposed for this incident.</p>
                  )}
                </div>

                {/* Investigation Timeline Notes */}
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Investigation Notes & Evidence
                  </h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {selectedIncident.notes?.map((note) => (
                      <div key={note.id} className="p-2.5 rounded bg-slate-950 border border-slate-800/80 text-xs space-y-1">
                        <div className="flex justify-between text-[11px] text-slate-500">
                          <span className="font-semibold text-slate-400">{note.note_type}</span>
                          <span>{new Date(note.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-slate-300 whitespace-pre-line">{note.content}</p>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2 pt-2">
                    <input
                      type="text"
                      placeholder="Add investigation observation or forensic note..."
                      value={newNoteContent}
                      onChange={(e) => setNewNoteContent(e.target.value)}
                      className="flex-1 text-xs rounded border border-slate-700 bg-slate-900 text-white px-2.5 py-1.5 focus:outline-none"
                    />
                    <button
                      onClick={() => handleAddNote(selectedIncident.id)}
                      disabled={!newNoteContent.trim()}
                      className="px-3 py-1.5 text-xs font-semibold rounded bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50"
                    >
                      Add Note
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CREDENTIALS MANAGEMENT (PRESERVED) */}
      {activeTab === "credentials" && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              Change Account Password
            </h2>

            {successMessage && (
              <div
                role="status"
                className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-sm text-emerald-300"
              >
                {successMessage}
              </div>
            )}

            {errorMessage && (
              <div
                role="alert"
                className="rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 text-sm text-red-300"
              >
                {errorMessage}
              </div>
            )}

            <form onSubmit={handlePasswordSubmit} className="space-y-5" noValidate>
              <div>
                <label
                  htmlFor="current-password"
                  className="block text-xs font-medium uppercase tracking-wider text-slate-300"
                >
                  Current Password
                </label>
                <input
                  id="current-password"
                  type="password"
                  autoComplete="current-password"
                  required
                  disabled={isSubmitting}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label
                  htmlFor="new-password"
                  className="block text-xs font-medium uppercase tracking-wider text-slate-300"
                >
                  New Password
                </label>
                <input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  disabled={isSubmitting}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label
                  htmlFor="confirm-password"
                  className="block text-xs font-medium uppercase tracking-wider text-slate-300"
                >
                  Confirm New Password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  disabled={isSubmitting}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                />
              </div>

              {/* Real-time Policy Rules Checklist */}
              <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 space-y-2">
                <span className="text-xs font-medium text-slate-400">Institutional Password Policy:</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className={`flex items-center gap-1.5 ${hasMinLength ? "text-emerald-400" : "text-slate-500"}`}>
                    <span>{hasMinLength ? "✓" : "○"}</span> Minimum 8 characters
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasUpper ? "text-emerald-400" : "text-slate-500"}`}>
                    <span>{hasUpper ? "✓" : "○"}</span> Uppercase letter (A-Z)
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasLower ? "text-emerald-400" : "text-slate-500"}`}>
                    <span>{hasLower ? "✓" : "○"}</span> Lowercase letter (a-z)
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasNumberOrSpecial ? "text-emerald-400" : "text-slate-500"}`}>
                    <span>{hasNumberOrSpecial ? "✓" : "○"}</span> Number or symbol
                  </div>
                  <div className={`col-span-2 flex items-center gap-1.5 ${isMatch ? "text-emerald-400" : "text-slate-500"}`}>
                    <span>{isMatch ? "✓" : "○"}</span> Passwords match
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting || !isFormValid}
                  className="flex justify-center rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 transition-colors"
                >
                  {isSubmitting ? "Updating Password..." : "Update Password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
