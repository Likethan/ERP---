"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  SupportTicketModel,
  SupportTicketDetailModel,
  SupportTeamModel,
  SupportSlaPolicyModel,
  SupportAnalyticsMetricsModel,
} from "@campusos/types";
import {
  SupportTicketStatus,
  SupportPriority,
  SupportSeverity,
  SupportCategory,
  SupportRequestType,
  SupportMessageType,
} from "@campusos/types";

export default function ServiceDeskPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"requester" | "workspace" | "sla_policies" | "analytics">("requester");
  const [tickets, setTickets] = useState<SupportTicketModel[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicketDetailModel | null>(null);
  const [teams, setTeams] = useState<SupportTeamModel[]>([]);
  const [slaPolicies, setSlaPolicies] = useState<SupportSlaPolicyModel[]>([]);
  const [analytics, setAnalytics] = useState<SupportAnalyticsMetricsModel | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Modals & form state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubject, setNewSubject] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCategory, setNewCategory] = useState<string>(SupportCategory.GENERAL_ASSISTANCE);
  const [newPriority, setNewPriority] = useState<string>(SupportPriority.MEDIUM);
  const [newSeverity, setNewSeverity] = useState<string>(SupportSeverity.SEV_3_MODERATE);
  const [newRequestType, setNewRequestType] = useState<string>(SupportRequestType.SERVICE_REQUEST);
  const [newErpModule, setNewErpModule] = useState("");

  // Communication message form
  const [messageBody, setMessageBody] = useState("");
  const [messageType, setMessageType] = useState<string>(SupportMessageType.PUBLIC_REPLY);

  // Transition form
  const [transitionStatus, setTransitionStatus] = useState<string>("");
  const [transitionReason, setTransitionReason] = useState<string>("");

  // CSAT rating form
  const [csatRating, setCsatRating] = useState<number>(5);
  const [csatFeedback, setCsatFeedback] = useState<string>("");

  const isSupportStaff = user?.role === "SUPER_ADMIN" || user?.role === "INSTITUTION_ADMIN" || user?.role === "SUPPORT_AGENT";

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [ticketsRes, teamsRes, slaRes, analyticsRes] = await Promise.all([
        apiFetch<{ items: SupportTicketModel[]; meta: any }>("/api/v1/support/tickets?limit=100").catch(() => ({ data: { items: [] } })),
        apiFetch<SupportTeamModel[]>("/api/v1/support/teams").catch(() => ({ data: [] })),
        apiFetch<SupportSlaPolicyModel[]>("/api/v1/support/sla-policies").catch(() => ({ data: [] })),
        apiFetch<SupportAnalyticsMetricsModel>("/api/v1/support/analytics").catch(() => ({ data: null })),
      ]);

      setTickets(ticketsRes.data?.items || []);
      setTeams(teamsRes.data || []);
      setSlaPolicies(slaRes.data || []);
      setAnalytics(analyticsRes.data || null);
    } catch (err: any) {
      setError(err?.message || "Failed to load support service desk data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectTicket = async (ticketId: string) => {
    try {
      const res = await apiFetch<SupportTicketDetailModel>(`/api/v1/support/tickets/${ticketId}`);
      setSelectedTicket(res.data);
      setTransitionStatus(res.data.status);
    } catch (err: any) {
      setError(err?.message || "Failed to retrieve ticket details.");
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionSuccess(null);
      setError(null);
      await apiFetch<SupportTicketModel>("/api/v1/support/tickets", {
        method: "POST",
        body: JSON.stringify({
          subject: newSubject,
          description: newDescription,
          category: newCategory,
          priority: newPriority,
          severity: newSeverity,
          request_type: newRequestType,
          related_erp_module: newErpModule || null,
        }),
      });

      setShowCreateModal(false);
      setNewSubject("");
      setNewDescription("");
      setActionSuccess("Support ticket created successfully and routed to specialist queue.");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to create support ticket.");
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !messageBody.trim()) return;

    try {
      setError(null);
      await apiFetch(`/api/v1/support/tickets/${selectedTicket.id}/messages`, {
        method: "POST",
        body: JSON.stringify({
          body: messageBody,
          message_type: messageType,
        }),
      });
      setMessageBody("");
      setActionSuccess("Message posted to ticket.");
      await selectTicket(selectedTicket.id);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to post message.");
    }
  };

  const handleStatusTransition = async () => {
    if (!selectedTicket || !transitionStatus || !transitionReason.trim()) return;

    try {
      setError(null);
      await apiFetch(`/api/v1/support/tickets/${selectedTicket.id}/transitions`, {
        method: "POST",
        body: JSON.stringify({
          target_status: transitionStatus,
          reason: transitionReason,
        }),
      });
      setTransitionReason("");
      setActionSuccess(`Ticket status updated to ${transitionStatus}.`);
      await selectTicket(selectedTicket.id);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to update ticket status.");
    }
  };

  const handleSubmitCsat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;

    try {
      setError(null);
      await apiFetch(`/api/v1/support/tickets/${selectedTicket.id}/csat`, {
        method: "POST",
        body: JSON.stringify({
          rating: csatRating,
          feedback: csatFeedback,
        }),
      });
      setActionSuccess("Thank you! Customer satisfaction rating submitted.");
      await selectTicket(selectedTicket.id);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to submit CSAT rating.");
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "URGENT":
        return "bg-rose-500/20 text-rose-400 border-rose-500/30";
      case "HIGH":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "MEDIUM":
        return "bg-sky-500/20 text-sky-400 border-sky-500/30";
      default:
        return "bg-slate-500/20 text-slate-400 border-slate-500/30";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "NEW":
        return "bg-indigo-500/20 text-indigo-400 border-indigo-500/30";
      case "IN_PROGRESS":
        return "bg-sky-500/20 text-sky-400 border-sky-500/30";
      case "WAITING_FOR_REQUESTER":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "RESOLVED":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "CLOSED":
        return "bg-slate-500/20 text-slate-400 border-slate-500/30";
      case "ESCALATED":
        return "bg-rose-500/20 text-rose-400 border-rose-500/30 animate-pulse";
      default:
        return "bg-slate-500/20 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Step 36
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Customer Support & Service Desk
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Enterprise service commitment tracking, multi-tenant isolation, SLA clock management, and verified resolution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors shadow-lg shadow-sky-600/20"
          >
            + New Support Ticket
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3.5 py-2 text-sm font-medium rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Action Alerts */}
      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          <span className="font-semibold">Error:</span> {error}
        </div>
      )}
      {actionSuccess && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          <span className="font-semibold">Success:</span> {actionSuccess}
        </div>
      )}

      {/* Operational Telemetry Summary */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-medium text-slate-400">Total Requests</div>
            <div className="mt-1 text-2xl font-bold text-white">{analytics.total_tickets_created}</div>
            <div className="mt-1 text-xs text-slate-500">{analytics.total_tickets_resolved} resolved</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-medium text-slate-400">Open Backlog</div>
            <div className="mt-1 text-2xl font-bold text-amber-400">{analytics.open_backlog_count}</div>
            <div className="mt-1 text-xs text-rose-400">{analytics.urgent_priority_count} urgent priority</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-medium text-slate-400">SLA Compliance</div>
            <div className="mt-1 text-2xl font-bold text-emerald-400">{analytics.sla_compliance_rate_pct}%</div>
            <div className="mt-1 text-xs text-slate-500">Commitments met</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-medium text-slate-400">Avg First Response</div>
            <div className="mt-1 text-2xl font-bold text-sky-400">{analytics.average_first_response_minutes}m</div>
            <div className="mt-1 text-xs text-slate-500">Minutes to agent response</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-medium text-slate-400">Customer CSAT</div>
            <div className="mt-1 text-2xl font-bold text-purple-400">{analytics.csat_average_score || "5.0"} / 5</div>
            <div className="mt-1 text-xs text-slate-500">{analytics.csat_response_count} verified ratings</div>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="border-b border-slate-800 flex gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("requester")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "requester"
              ? "border-sky-500 text-sky-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          My Support Requests ({tickets.length})
        </button>
        {isSupportStaff && (
          <button
            onClick={() => setActiveTab("workspace")}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === "workspace"
                ? "border-sky-500 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Support Agent Workspace
          </button>
        )}
        <button
          onClick={() => setActiveTab("sla_policies")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "sla_policies"
              ? "border-sky-500 text-sky-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          SLA Targets & Teams ({slaPolicies.length})
        </button>
      </div>

      {/* TAB CONTENT: Requester / Ticket Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Tickets List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
            Active Requests
          </div>

          {loading ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-sm text-slate-400">
              Loading support requests...
            </div>
          ) : tickets.length === 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-sm text-slate-400">
              No tickets submitted yet. Click &quot;+ New Support Ticket&quot; to request assistance.
            </div>
          ) : (
            <div className="space-y-2 max-h-[700px] overflow-y-auto pr-1">
              {tickets.map((t) => (
                <div
                  key={t.id}
                  onClick={() => selectTicket(t.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    selectedTicket?.id === t.id
                      ? "border-sky-500 bg-sky-950/20 shadow-md shadow-sky-950/40"
                      : "border-slate-800/80 bg-slate-900/50 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-semibold text-slate-300">
                      {t.ticket_number}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(
                        t.status
                      )}`}
                    >
                      {t.status}
                    </span>
                  </div>

                  <h3 className="mt-1.5 text-sm font-medium text-white line-clamp-1">{t.subject}</h3>

                  <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                    <span className={`px-1.5 py-0.5 rounded border ${getPriorityBadge(t.priority)}`}>
                      {t.priority}
                    </span>
                    <span>{t.assigned_team_name || "Triage Queue"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Selected Ticket Workspace */}
        <div className="lg:col-span-2">
          {selectedTicket ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-6">
              {/* Ticket Header & Status Controls */}
              <div className="border-b border-slate-800 pb-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-sky-400">
                      {selectedTicket.ticket_number}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold border ${getStatusBadge(
                        selectedTicket.status
                      )}`}
                    >
                      {selectedTicket.status}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold border ${getPriorityBadge(
                        selectedTicket.priority
                      )}`}
                    >
                      {selectedTicket.priority}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400">
                    Opened by <span className="text-slate-200">{selectedTicket.requester_name}</span> (
                    {selectedTicket.requester_email})
                  </div>
                </div>

                <h2 className="mt-3 text-lg font-bold text-white">{selectedTicket.subject}</h2>
                <div className="mt-2 rounded-lg bg-slate-950/60 p-3.5 text-xs text-slate-300 whitespace-pre-wrap border border-slate-800/80">
                  {selectedTicket.description}
                </div>

                {/* SLA Commitments Indicator */}
                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800/80">
                    <div className="text-slate-400 text-[10px]">Response SLA</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedTicket.sla_response_status}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800/80">
                    <div className="text-slate-400 text-[10px]">Resolution SLA</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedTicket.sla_resolution_status}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800/80">
                    <div className="text-slate-400 text-[10px]">Assigned Team</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedTicket.assigned_team_name || "Unassigned"}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800/80">
                    <div className="text-slate-400 text-[10px]">ERP Module</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedTicket.related_erp_module || "General"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Status Transition Control */}
              <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-3">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Lifecycle Status Transition
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <select
                    value={transitionStatus}
                    onChange={(e) => setTransitionStatus(e.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value={SupportTicketStatus.IN_PROGRESS}>IN_PROGRESS</option>
                    <option value={SupportTicketStatus.WAITING_FOR_REQUESTER}>WAITING_FOR_REQUESTER</option>
                    <option value={SupportTicketStatus.WAITING_FOR_ENGINEERING}>WAITING_FOR_ENGINEERING</option>
                    <option value={SupportTicketStatus.ON_HOLD}>ON_HOLD</option>
                    <option value={SupportTicketStatus.RESOLVED}>RESOLVED</option>
                    <option value={SupportTicketStatus.CLOSED}>CLOSED</option>
                    <option value={SupportTicketStatus.CANCELLED}>CANCELLED</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Reason for state transition..."
                    value={transitionReason}
                    onChange={(e) => setTransitionReason(e.target.value)}
                    className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  />

                  <button
                    onClick={handleStatusTransition}
                    className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors"
                  >
                    Update Status
                  </button>
                </div>
              </div>

              {/* Communication Message Thread */}
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Communications & Activity ({selectedTicket.messages?.length || 0})
                </div>

                <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
                  {selectedTicket.messages?.length === 0 ? (
                    <div className="text-xs text-slate-500 italic p-3 text-center border border-dashed border-slate-800 rounded-lg">
                      No communication records yet.
                    </div>
                  ) : (
                    selectedTicket.messages?.map((msg) => (
                      <div
                        key={msg.id}
                        className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                          msg.message_type === "INTERNAL_NOTE"
                            ? "bg-amber-950/20 border-amber-500/30 text-amber-200"
                            : "bg-slate-950/50 border-slate-800 text-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-white">
                            {msg.sender_name} ({msg.sender_role})
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                              msg.message_type === "INTERNAL_NOTE"
                                ? "bg-amber-500/20 text-amber-400"
                                : "bg-sky-500/20 text-sky-400"
                            }`}
                          >
                            {msg.message_type === "INTERNAL_NOTE" ? "Confidential Internal Note" : "Public Reply"}
                          </span>
                        </div>
                        <div className="whitespace-pre-wrap">{msg.body}</div>
                        <div className="text-[10px] text-slate-500 pt-1">
                          {new Date(msg.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Reply Composer */}
                <form onSubmit={handleSendMessage} className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300">Add Message</span>
                    {isSupportStaff && (
                      <div className="flex items-center gap-2 text-xs">
                        <label className="flex items-center gap-1 cursor-pointer text-slate-300">
                          <input
                            type="radio"
                            name="msgType"
                            checked={messageType === SupportMessageType.PUBLIC_REPLY}
                            onChange={() => setMessageType(SupportMessageType.PUBLIC_REPLY)}
                          />
                          Public Reply
                        </label>
                        <label className="flex items-center gap-1 cursor-pointer text-amber-400 font-semibold">
                          <input
                            type="radio"
                            name="msgType"
                            checked={messageType === SupportMessageType.INTERNAL_NOTE}
                            onChange={() => setMessageType(SupportMessageType.INTERNAL_NOTE)}
                          />
                          Internal Note
                        </label>
                      </div>
                    )}
                  </div>

                  <textarea
                    rows={3}
                    placeholder={
                      messageType === SupportMessageType.INTERNAL_NOTE
                        ? "Enter internal investigation notes (confidential - customer will not see this)..."
                        : "Type public response visible to the requester..."
                    }
                    value={messageBody}
                    onChange={(e) => setMessageBody(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!messageBody.trim()}
                      className="px-4 py-1.5 text-xs font-medium rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white transition-colors"
                    >
                      Post {messageType === SupportMessageType.INTERNAL_NOTE ? "Internal Note" : "Reply"}
                    </button>
                  </div>
                </form>
              </div>

              {/* CSAT Rating Submission Section (on resolved tickets) */}
              {(selectedTicket.status === SupportTicketStatus.RESOLVED ||
                selectedTicket.status === SupportTicketStatus.CLOSED) && (
                <div className="rounded-xl border border-purple-500/30 bg-purple-950/10 p-4 space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-purple-300">
                    Customer Satisfaction Feedback (CSAT)
                  </div>
                  {selectedTicket.csat_rating ? (
                    <div className="text-xs text-slate-300">
                      Rated: <span className="font-bold text-amber-400">{selectedTicket.csat_rating}/5 Stars</span>.
                      {selectedTicket.csat_feedback && (
                        <p className="mt-1 italic text-slate-400">&quot;{selectedTicket.csat_feedback}&quot;</p>
                      )}
                    </div>
                  ) : (
                    <form onSubmit={handleSubmitCsat} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-300">Your Rating:</span>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            type="button"
                            key={star}
                            onClick={() => setCsatRating(star)}
                            className={`px-2 py-0.5 rounded text-xs font-bold ${
                              csatRating >= star
                                ? "bg-amber-400 text-slate-950"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {star} ★
                          </button>
                        ))}
                      </div>
                      <input
                        type="text"
                        placeholder="Optional feedback comments..."
                        value={csatFeedback}
                        onChange={(e) => setCsatFeedback(e.target.value)}
                        className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200"
                      />
                      <button
                        type="submit"
                        className="px-3.5 py-1 text-xs font-medium rounded-lg bg-purple-600 hover:bg-purple-500 text-white"
                      >
                        Submit Rating
                      </button>
                    </form>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center text-sm text-slate-400">
              Select a ticket from the left panel to review timeline, communications, and SLA status.
            </div>
          )}
        </div>
      </div>

      {/* CREATE TICKET MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Create Support Ticket</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Subject</label>
                <input
                  type="text"
                  required
                  placeholder="Summary of issue or assistance requested..."
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                  >
                    {Object.values(SupportCategory).map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                  >
                    <option value={SupportPriority.LOW}>LOW</option>
                    <option value={SupportPriority.MEDIUM}>MEDIUM</option>
                    <option value={SupportPriority.HIGH}>HIGH</option>
                    <option value={SupportPriority.URGENT}>URGENT</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                  >
                    <option value={SupportSeverity.SEV_4_MINOR}>SEV_4_MINOR</option>
                    <option value={SupportSeverity.SEV_3_MODERATE}>SEV_3_MODERATE</option>
                    <option value={SupportSeverity.SEV_2_MAJOR}>SEV_2_MAJOR</option>
                    <option value={SupportSeverity.SEV_1_CRITICAL}>SEV_1_CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">ERP Module</label>
                  <input
                    type="text"
                    placeholder="e.g. FINANCE, ATTENDANCE"
                    value={newErpModule}
                    onChange={(e) => setNewErpModule(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Detailed Description</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Provide context, exact error message, or steps to reproduce..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-slate-200"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
