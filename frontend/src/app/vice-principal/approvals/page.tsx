"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import {
  StatutoryApprovalItem,
  StatutoryApprovalCategory,
  StatutoryApprovalStatus,
} from "@/types/vice-principal";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
  FileText,
  AlertTriangle,
  History,
  Send,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalApprovalsPage() {
  const { showToast } = useToast();
  const [approvals, setApprovals] = useState<StatutoryApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Action Dialog State
  const [activeItem, setActiveItem] = useState<StatutoryApprovalItem | null>(
    null,
  );
  const [actionType, setActionType] = useState<
    "APPROVE" | "REJECT" | "REQUEST_MODIFICATION" | null
  >(null);
  const [remarks, setRemarks] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, [statusFilter, categoryFilter]);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getApprovals({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
      });
      if (res.success && res.data) {
        setApprovals(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAction = (
    item: StatutoryApprovalItem,
    type: "APPROVE" | "REJECT" | "REQUEST_MODIFICATION",
  ) => {
    setActiveItem(item);
    setActionType(type);
    setRemarks(
      type === "APPROVE"
        ? "Sanctioned by Vice Principal in compliance with academic regulations."
        : type === "REQUEST_MODIFICATION"
          ? "Please revise syllabus coverage schedule and resubmit."
          : "Declined due to scheduling conflict with statutory examination dates.",
    );
  };

  const handleExecuteAction = async () => {
    if (!activeItem || !actionType) return;
    if (!remarks.trim()) {
      showToast({
        title: "Mandatory Remarks Required",
        message:
          "Please provide official remarks for the statutory audit trail.",
        type: "error",
      });
      return;
    }

    setSubmitting(true);
    try {
      await vicePrincipalService.processApprovalAction(
        activeItem.id,
        actionType,
        remarks,
      );
      showToast({
        title: "Statutory Decision Recorded",
        message: `Successfully executed ${actionType} for #${activeItem.id}.`,
        type: "success",
      });
      setActiveItem(null);
      setActionType(null);
      setRemarks("");
      loadApprovals();
    } catch (e: any) {
      showToast({
        title: "Processing Failed",
        message: e.message || "Failed to execute approval action.",
        type: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Statutory Approval Management Center
          </h1>
          <p className="text-sm text-slate-600">
            Institutional approval authority for department academic requests,
            faculty leaves, timetable swaps, and examinations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadApprovals}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Reload Queue</span>
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        {/* Status Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {[
            "ALL",
            "PENDING",
            "APPROVED",
            "REJECTED",
            "MODIFICATION_REQUESTED",
          ].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {st === "ALL"
                ? "All Statuses"
                : st === "MODIFICATION_REQUESTED"
                  ? "Modification Needed"
                  : st}
            </button>
          ))}
        </div>

        {/* Category Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">
            Category:
          </span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Categories (8)</option>
            <option value="DEPARTMENT_ACADEMIC_REQUEST">
              Department Academic Request
            </option>
            <option value="ACADEMIC_CALENDAR_CHANGE">
              Academic Calendar Change
            </option>
            <option value="TIMETABLE_CHANGE">Timetable Change</option>
            <option value="FACULTY_LEAVE">Faculty Leave</option>
            <option value="EXAMINATION_REQUEST">Examination Request</option>
            <option value="ACADEMIC_PERFORMANCE_INTERVENTION">
              Academic Intervention
            </option>
            <option value="ACADEMIC_EVENT">Academic Event</option>
            <option value="SPECIAL_ACADEMIC_PERMISSION">
              Special Permission
            </option>
          </select>
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {approvals.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
            <h3 className="mt-2 text-sm font-bold text-slate-900">
              No Approvals in Current Queue
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              All statutory submissions matching filter criteria have been
              processed.
            </p>
          </div>
        ) : (
          approvals.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <Card
                key={item.id}
                className={`shadow-xs transition-all ${
                  item.status === "PENDING"
                    ? "border-indigo-300 bg-white"
                    : "border-slate-200 bg-slate-50/50"
                }`}
              >
                <CardContent className="p-5">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-2 flex-1">
                      {/* Meta Tags */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-500">
                          #{item.id}
                        </span>
                        <span className="rounded bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-indigo-700">
                          {item.category.replace(/_/g, " ")}
                        </span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                            item.urgency === "CRITICAL"
                              ? "bg-rose-100 text-rose-800"
                              : item.urgency === "HIGH"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {item.urgency} URGENCY
                        </span>
                        <Badge
                          variant={
                            item.status === "APPROVED"
                              ? "success"
                              : item.status === "PENDING"
                                ? "warning"
                                : item.status === "REJECTED"
                                  ? "destructive"
                                  : "default"
                          }
                          className="text-[10px]"
                        >
                          {item.status.replace(/_/g, " ")}
                        </Badge>
                      </div>

                      {/* Title & Originator */}
                      <div>
                        <h3 className="text-base font-bold text-slate-900">
                          {item.title}
                        </h3>
                        <div className="mt-0.5 text-xs text-slate-500">
                          {item.department_name} · Submitted by{" "}
                          <b>{item.submitted_by}</b> on{" "}
                          {new Date(item.submission_date).toLocaleDateString()}
                        </div>
                      </div>

                      {/* Brief Details */}
                      <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 border border-slate-100 font-sans">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {Object.entries(item.details).map(([k, v]) => (
                            <div key={k}>
                              <span className="font-semibold text-slate-500 uppercase text-[10px] tracking-wider">
                                {k.replace(/_/g, " ")}:
                              </span>{" "}
                              <span className="font-medium text-slate-900">
                                {String(v)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Official Remarks if Decided */}
                      {item.remarks && (
                        <div className="text-xs bg-emerald-50 border border-emerald-200 p-2.5 rounded-lg text-emerald-900">
                          <span className="font-bold">
                            Official Decision Remarks:
                          </span>{" "}
                          {item.remarks}
                          <div className="text-[10px] text-emerald-700 mt-1 font-mono">
                            Decided by {item.decided_by} on{" "}
                            {item.decision_date
                              ? new Date(item.decision_date).toLocaleString()
                              : "—"}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action Controls for Pending Item */}
                    <div className="flex flex-col gap-2 shrink-0 pt-2 lg:pt-0">
                      {item.status === "PENDING" ? (
                        <div className="flex flex-wrap items-center gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleOpenAction(item, "APPROVE")}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-1"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              handleOpenAction(item, "REQUEST_MODIFICATION")
                            }
                            className="text-amber-700 border-amber-300 hover:bg-amber-50 text-xs gap-1"
                          >
                            <HelpCircle className="h-3.5 w-3.5" />
                            Modify
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenAction(item, "REJECT")}
                            className="text-rose-700 border-rose-300 hover:bg-rose-50 text-xs gap-1"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Reject
                          </Button>
                        </div>
                      ) : (
                        <div className="text-right">
                          <span className="text-[11px] font-semibold text-slate-400">
                            Decision Recorded
                          </span>
                        </div>
                      )}

                      {/* Toggle Audit Trail */}
                      <button
                        onClick={() =>
                          setExpandedId(isExpanded ? null : item.id)
                        }
                        className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:underline mt-1 font-medium"
                      >
                        <History className="h-3 w-3" />
                        <span>
                          {isExpanded
                            ? "Hide Audit Trail"
                            : `Audit Trail (${item.audit_trail.length})`}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3" />
                        ) : (
                          <ChevronDown className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Audit Trail Accordion Content */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Statutory Verification & Audit History
                      </div>
                      <div className="space-y-2">
                        {item.audit_trail.map((entry, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2.5 text-xs text-slate-700"
                          >
                            <div className="h-2 w-2 rounded-full bg-indigo-500 mt-1 shrink-0" />
                            <div className="flex-1">
                              <span className="font-bold text-slate-900">
                                {entry.action}
                              </span>{" "}
                              by{" "}
                              <span className="font-semibold">{entry.by}</span>{" "}
                              <span className="text-[10px] text-slate-400 font-mono">
                                ({new Date(entry.timestamp).toLocaleString()})
                              </span>
                              <div className="text-slate-600 italic mt-0.5">
                                "{entry.notes}"
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Official Decision Action Modal Dialog */}
      {activeItem && actionType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Execute Statutory Decision ({actionType})
                </h3>
              </div>
              <button
                onClick={() => {
                  setActiveItem(null);
                  setActionType(null);
                }}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-500">
                Subject Item:
              </div>
              <div className="text-sm font-bold text-slate-900">
                {activeItem.title}
              </div>
              <div className="text-xs text-slate-500">
                Originating: {activeItem.department_name} (
                {activeItem.submitted_by})
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Official Regulatory Remarks (Mandatory for Audit Trail)
              </label>
              <textarea
                rows={4}
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Detail the institutional basis, stipulations or required modifications..."
                className="w-full rounded-lg border border-slate-200 p-2.5 text-xs text-slate-900 focus:outline-hidden focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setActiveItem(null);
                  setActionType(null);
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleExecuteAction}
                disabled={submitting}
                className={
                  actionType === "APPROVE"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                    : actionType === "REJECT"
                      ? "bg-rose-600 hover:bg-rose-700 text-white text-xs"
                      : "bg-amber-600 hover:bg-amber-700 text-white text-xs"
                }
              >
                {submitting
                  ? "Signing & Recording..."
                  : `Confirm ${actionType}`}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
