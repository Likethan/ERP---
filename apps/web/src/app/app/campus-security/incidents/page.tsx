"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  Flame,
  CheckCircle,
  Plus,
  Search,
  Filter,
  Clock,
  ArrowUpRight,
  MapPin,
  Users,
  FileText,
  AlertOctagon,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import {
  CampusSecurityIncident,
  IncidentCategory,
  IncidentSeverity,
  IncidentStatus,
} from "@/types/campus-security";

export default function SecurityIncidentsPage() {
  const [incidents, setIncidents] = useState<CampusSecurityIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Modals
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reporting, setReporting] = useState(false);

  const [escalatingIncident, setEscalatingIncident] = useState<CampusSecurityIncident | null>(null);
  const [escalationReason, setEscalationReason] = useState("");
  const [escalating, setEscalating] = useState(false);

  const [resolvingIncident, setResolvingIncident] = useState<CampusSecurityIncident | null>(null);
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [correctiveNotes, setCorrectiveNotes] = useState("");
  const [resolving, setResolving] = useState(false);

  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Report form
  const [reportForm, setReportForm] = useState({
    title: "",
    category: "UNAUTHORIZED_ACCESS" as IncidentCategory,
    severity: "MEDIUM" as IncidentSeverity,
    reported_location: "",
    description: "",
    assigned_team: "CAMPUS_PATROL_ALPHA",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await CampusSecurityService.listIncidents();
      setIncidents(data);
    } catch (err) {
      console.error("Failed to load incidents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleReportIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportForm.title || !reportForm.reported_location || !reportForm.description) return;

    try {
      setReporting(true);
      await CampusSecurityService.reportIncident({
        title: reportForm.title,
        category: reportForm.category,
        severity: reportForm.severity,
        reported_location: reportForm.reported_location,
        description: reportForm.description,
        assigned_team: reportForm.assigned_team,
      });

      setNotification({
        type: "success",
        message: `Security incident "${reportForm.title}" successfully logged and dispatched.`,
      });
      setIsReportModalOpen(false);
      setReportForm({
        title: "",
        category: "UNAUTHORIZED_ACCESS",
        severity: "MEDIUM",
        reported_location: "",
        description: "",
        assigned_team: "CAMPUS_PATROL_ALPHA",
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to log incident. Please verify inputs.",
      });
    } finally {
      setReporting(false);
    }
  };

  const handleEscalateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!escalatingIncident || !escalationReason) return;

    try {
      setEscalating(true);
      await CampusSecurityService.escalateIncident(escalatingIncident.id, escalationReason);
      setNotification({
        type: "success",
        message: `Incident ${escalatingIncident.incident_number} escalated to command level.`,
      });
      setEscalatingIncident(null);
      setEscalationReason("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to escalate incident.",
      });
    } finally {
      setEscalating(false);
    }
  };

  const handleResolveIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingIncident || !resolutionSummary) return;

    try {
      setResolving(true);
      await CampusSecurityService.resolveIncident(
        resolvingIncident.id,
        resolutionSummary,
        correctiveNotes
      );
      setNotification({
        type: "success",
        message: `Incident ${resolvingIncident.incident_number} marked as RESOLVED.`,
      });
      setResolvingIncident(null);
      setResolutionSummary("");
      setCorrectiveNotes("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to resolve incident.",
      });
    } finally {
      setResolving(false);
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch =
      inc.title.toLowerCase().includes(search.toLowerCase()) ||
      inc.incident_number.toLowerCase().includes(search.toLowerCase()) ||
      inc.reported_location.toLowerCase().includes(search.toLowerCase()) ||
      inc.description.toLowerCase().includes(search.toLowerCase());

    const matchesCategory = categoryFilter === "ALL" || inc.category === categoryFilter;
    const matchesSeverity = severityFilter === "ALL" || inc.severity === severityFilter;
    const matchesStatus = statusFilter === "ALL" || inc.status === statusFilter;

    return matchesSearch && matchesCategory && matchesSeverity && matchesStatus;
  });

  const openCount = incidents.filter((i) => i.status !== "RESOLVED" && i.status !== "CLOSED").length;
  const criticalCount = incidents.filter((i) => i.severity === "CRITICAL" && i.status !== "CLOSED").length;
  const escalatedCount = incidents.filter((i) => i.is_escalated && i.status !== "RESOLVED").length;
  const resolvedCount = incidents.filter((i) => i.status === "RESOLVED" || i.status === "CLOSED").length;

  const getSeverityBadge = (severity: IncidentSeverity) => {
    switch (severity) {
      case "CRITICAL":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-300 dark:border-red-800">
            <Flame className="w-3 h-3 text-red-600" /> CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            HIGH
          </span>
        );
      case "MEDIUM":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
            MEDIUM
          </span>
        );
      case "LOW":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            LOW
          </span>
        );
    }
  };

  const getStatusBadge = (status: IncidentStatus) => {
    switch (status) {
      case "ESCALATED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
            <ArrowUpRight className="w-3 h-3" /> ESCALATED
          </span>
        );
      case "IN_PROGRESS":
      case "ASSIGNED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300">
            <Clock className="w-3 h-3" /> IN PROGRESS
          </span>
        );
      case "RESOLVED":
      case "CLOSED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            <CheckCircle className="w-3 h-3" /> RESOLVED
          </span>
        );
      case "REPORTED":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-300">
            REPORTED
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Campus Physical Security Incident Center
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-200 dark:border-red-800">
              Live Operations
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Dispatch response patrols, log unauthorized access breaches, escalate priority alerts, and document corrective actions.
          </p>
        </div>

        <button
          onClick={() => setIsReportModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Report Security Incident
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

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Open Incidents</span>
            <AlertTriangle className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{openCount}</div>
          <div className="text-xs text-slate-500 mt-1">Active response underway</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Critical Severity</span>
            <Flame className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">{criticalCount}</div>
          <div className="text-xs text-slate-500 mt-1">High-risk safety priority</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Escalated</span>
            <ArrowUpRight className="w-5 h-5 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2">{escalatedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Command supervision active</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved</span>
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{resolvedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Corrective actions filed</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search incident number, title, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            <option value="ALL">All Categories</option>
            <option value="UNAUTHORIZED_ACCESS">Unauthorized Access</option>
            <option value="PROPERTY_LOSS_DAMAGE">Property Damage</option>
            <option value="SAFETY_HAZARD">Safety Hazard</option>
            <option value="SUSPICIOUS_ACTIVITY">Suspicious Activity</option>
            <option value="VEHICLE_GATE_INCIDENT">Vehicle / Gate</option>
            <option value="POLICY_VIOLATION">Policy Violation</option>
            <option value="EMERGENCY_ASSISTANCE">Emergency</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            <option value="ALL">All Statuses</option>
            <option value="REPORTED">Reported</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="ESCALATED">Escalated</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Incident Cards / List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-12 text-center text-slate-400">
            Loading security incidents...
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-12 text-center text-slate-400">
            No security incidents matching current filters.
          </div>
        ) : (
          filteredIncidents.map((inc) => (
            <div
              key={inc.id}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {inc.incident_number}
                  </span>
                  <span className="text-slate-300 dark:text-slate-700">|</span>
                  <span className="text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    {inc.category.replace(/_/g, " ")}
                  </span>
                  {getSeverityBadge(inc.severity)}
                  {getStatusBadge(inc.status)}
                </div>

                <div className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {new Date(inc.reported_at).toLocaleString()}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">{inc.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{inc.description}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                  <MapPin className="w-4 h-4 text-indigo-500 shrink-0" />
                  <span>
                    Location: <strong className="text-slate-900 dark:text-white">{inc.reported_location}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                  <Users className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>
                    Assigned: <strong className="text-slate-900 dark:text-white">{inc.assigned_team || "Unassigned"}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                  <FileText className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>
                    Reported By: <strong className="text-slate-900 dark:text-white">{inc.reported_by_name || "Patrol Officer"}</strong>
                  </span>
                </div>
              </div>

              {/* Escalation alert */}
              {inc.is_escalated && (
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800 text-xs text-purple-900 dark:text-purple-200">
                  <div className="font-semibold flex items-center gap-1">
                    <AlertOctagon className="w-4 h-4 text-purple-600" />
                    Escalated Incident: {inc.escalation_reason}
                  </div>
                  {inc.escalated_at && (
                    <div className="text-[11px] text-purple-700 dark:text-purple-300 mt-0.5">
                      Escalated at {new Date(inc.escalated_at).toLocaleString()}
                    </div>
                  )}
                </div>
              )}

              {/* Resolution block */}
              {inc.resolution_summary && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200">
                  <div className="font-semibold flex items-center gap-1">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    Resolution Summary: {inc.resolution_summary}
                  </div>
                  {inc.corrective_action_notes && (
                    <div className="text-[11px] text-emerald-700 dark:text-emerald-300 mt-1">
                      Corrective Action: {inc.corrective_action_notes}
                    </div>
                  )}
                </div>
              )}

              {/* Actions toolbar */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                {!inc.is_escalated && inc.status !== "RESOLVED" && inc.status !== "CLOSED" && (
                  <button
                    onClick={() => setEscalatingIncident(inc)}
                    className="px-3 py-1.5 text-xs font-semibold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/50 hover:bg-purple-100 rounded-lg border border-purple-200 dark:border-purple-800 transition-colors"
                  >
                    Escalate Incident
                  </button>
                )}

                {inc.status !== "RESOLVED" && inc.status !== "CLOSED" && (
                  <button
                    onClick={() => setResolvingIncident(inc)}
                    className="px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 hover:bg-emerald-100 rounded-lg border border-emerald-200 dark:border-emerald-800 transition-colors"
                  >
                    Resolve Incident
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Report Incident Modal */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-600" />
                Report Campus Security Incident
              </h2>
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReportIncident} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Incident Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unauthorized badge clone detected at Server Room A"
                  value={reportForm.title}
                  onChange={(e) => setReportForm({ ...reportForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Category *
                  </label>
                  <select
                    value={reportForm.category}
                    onChange={(e) => setReportForm({ ...reportForm, category: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="UNAUTHORIZED_ACCESS">Unauthorized Access</option>
                    <option value="PROPERTY_LOSS_DAMAGE">Property Loss / Damage</option>
                    <option value="SAFETY_HAZARD">Safety Hazard</option>
                    <option value="SUSPICIOUS_ACTIVITY">Suspicious Activity</option>
                    <option value="VEHICLE_GATE_INCIDENT">Vehicle / Gate Breach</option>
                    <option value="POLICY_VIOLATION">Campus Policy Violation</option>
                    <option value="EMERGENCY_ASSISTANCE">Emergency Assistance</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Severity *
                  </label>
                  <select
                    value={reportForm.severity}
                    onChange={(e) => setReportForm({ ...reportForm, severity: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Reported Location *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Building C, 3rd Floor"
                    value={reportForm.reported_location}
                    onChange={(e) => setReportForm({ ...reportForm, reported_location: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Assign Response Team
                  </label>
                  <select
                    value={reportForm.assigned_team}
                    onChange={(e) => setReportForm({ ...reportForm, assigned_team: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="CAMPUS_PATROL_ALPHA">Campus Patrol Alpha</option>
                    <option value="CAMPUS_PATROL_BRAVO">Campus Patrol Bravo</option>
                    <option value="RAPID_RESPONSE_TEAM">Rapid Response Team</option>
                    <option value="FACILITY_SECURITY_LEAD">Facility Security Lead</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Incident Description & Field Notes *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Detail observed activity, involved individuals, immediate mitigation steps taken..."
                  value={reportForm.description}
                  onChange={(e) => setReportForm({ ...reportForm, description: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsReportModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reporting}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {reporting ? "Logging..." : "Dispatch Incident"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Escalate Modal */}
      {escalatingIncident && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-md shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-purple-600 dark:text-purple-400 flex items-center gap-2">
                <AlertOctagon className="w-5 h-5" />
                Escalate Incident {escalatingIncident.incident_number}
              </h2>
              <button
                onClick={() => setEscalatingIncident(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEscalateIncident} className="p-6 space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Escalating this incident triggers high-priority alerts to the Dean of Operations and Security Director.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Escalation Justification *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Repeated unauthorized entry attempts; potential perimeter surveillance identified..."
                  value={escalationReason}
                  onChange={(e) => setEscalationReason(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setEscalatingIncident(null)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={escalating}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {escalating ? "Escalating..." : "Confirm Escalation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {resolvingIncident && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Resolve Incident {resolvingIncident.incident_number}
              </h2>
              <button
                onClick={() => setResolvingIncident(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveIncident} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Resolution Summary *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Detail findings, containment action, individual contacted, and immediate resolution..."
                  value={resolutionSummary}
                  onChange={(e) => setResolutionSummary(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Corrective & Preventative Actions
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Replaced lock cylinder, re-trained front desk guards, updated turnstile firmware..."
                  value={correctiveNotes}
                  onChange={(e) => setCorrectiveNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setResolvingIncident(null)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {resolving ? "Resolving..." : "Mark as Resolved"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

