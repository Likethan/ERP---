"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  hodService,
  HodApprovalsData,
  HodApprovalItem,
} from "@/services/hod.service";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import {
  CheckSquare,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  UserCheck,
  GraduationCap,
  Building,
  FileText,
  Paperclip,
  X,
  AlertTriangle,
  History,
  ShieldCheck,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodApprovalsPage() {
  const { activePersona, user } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodApprovalsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [search, setSearch] = useState("");

  // Action Drawer / Modal
  const [selectedRequest, setSelectedRequest] =
    useState<HodApprovalItem | null>(null);
  const [actionRemarks, setActionRemarks] = useState("");
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const res = await hodService.getApprovals(
        selectedCategory,
        selectedStatus,
      );
      if (res.success && res.data) {
        setData(res.data);
      }
    } catch (err) {
      console.error("Failed to load approvals", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, [selectedCategory, selectedStatus]);

  const filteredRequests = (data?.requests || []).filter((r) => {
    const q = search.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      r.submittedBy.toLowerCase().includes(q) ||
      r.id.toLowerCase().includes(q) ||
      r.subCategory.toLowerCase().includes(q)
    );
  });

  const handleAction = async (
    action: "APPROVE" | "REJECT" | "REQUEST_INFO",
  ) => {
    if (!selectedRequest) return;
    setProcessingAction(action);
    try {
      const res = await hodService.processApprovalAction(
        selectedRequest.id,
        action,
        actionRemarks.trim() || undefined,
      );
      if (res.success && res.data) {
        setToastMessage(
          `Request #${selectedRequest.id} has been marked as ${res.data.status}. Audit trail recorded.`,
        );
        setSelectedRequest(res.data);
        setActionRemarks("");
        // Refresh background list
        await loadApprovals();
      }
    } catch (err) {
      alert("Failed to process approval action.");
    } finally {
      setProcessingAction(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-lg text-xs font-semibold flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
          <button
            onClick={() => setToastMessage(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Department Operations
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Statutory Governance Queue
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <CheckSquare className="h-6 w-6 text-yellow-600" />
            Leave & Department Approvals Hub
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Centralized institutional approval authority for faculty leave/OD,
            student requests, academic exemptions, and department logistics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge className="bg-yellow-100 text-yellow-950 border-yellow-300 px-3 py-1 text-xs font-bold">
            {data?.stats.pending || 5} Pending HOD Review
          </Badge>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Pending Actions
              </span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-amber-600 mt-2">
              {data?.stats.pending || 5}
            </div>
            <div className="text-[11px] text-amber-700 font-bold mt-1">
              Requires HOD Statutory Decision
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Approved Decisions
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-2">
              {data?.stats.approved || 4}
            </div>
            <div className="text-[11px] text-emerald-600 font-medium mt-1">
              Endorsed with institutional audit trail
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Clarification Requested
              </span>
              <HelpCircle className="h-4 w-4 text-blue-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.stats.infoRequested || 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Pending applicant response
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Total Submissions
              </span>
              <FileText className="h-4 w-4 text-slate-400" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.stats.totalRequests || 9}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              This Academic Semester
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Category Tabs */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
        <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
          <span className="text-xs font-bold text-slate-500 mr-1">
            Category:
          </span>
          {[
            { id: "ALL", label: "All Requests" },
            { id: "FACULTY", label: "Faculty Requests" },
            { id: "STUDENT", label: "Student Requests" },
            { id: "DEPARTMENT", label: "Departmental Operations" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "px-2.5 py-1 text-xs rounded-md font-bold transition-colors",
                selectedCategory === cat.id
                  ? "bg-yellow-400 text-slate-950 shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200",
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <Input
              placeholder="Search title, applicant, ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs h-8"
            />
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2 py-1.5 font-bold text-slate-800 focus:outline-none h-8"
          >
            <option value="ALL">All Status</option>
            <option value="PENDING">Pending Only</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="INFO_REQUESTED">Clarification</option>
          </select>
        </div>
      </div>

      {/* Approvals Table */}
      <Card className="border-slate-200 bg-white shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                <th className="py-3 px-4">Request ID & Title</th>
                <th className="py-3 px-4">Category & Type</th>
                <th className="py-3 px-4">Submitted By</th>
                <th className="py-3 px-4">Submission Date</th>
                <th className="py-3 px-4 text-center">Urgency</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Review Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {filteredRequests.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <EmptyState
                      title="No approval requests found"
                      description="No requests match the selected category and status filters."
                    />
                  </td>
                </tr>
              ) : (
                filteredRequests.map((req) => (
                  <tr
                    key={req.id}
                    className={cn(
                      "hover:bg-yellow-50/30 transition-colors",
                      req.status === "PENDING" && "bg-amber-50/20",
                    )}
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">
                        {req.title}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="font-mono text-[10px] font-bold text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                          {req.id}
                        </span>
                        {req.attachments.length > 0 && (
                          <span className="text-[10px] text-slate-500 flex items-center gap-0.5">
                            <Paperclip className="h-3 w-3" />
                            {req.attachments.length} file
                            {req.attachments.length > 1 ? "s" : ""}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] font-bold",
                          req.category === "FACULTY"
                            ? "bg-blue-50 text-blue-800 border-blue-200"
                            : req.category === "STUDENT"
                              ? "bg-purple-50 text-purple-800 border-purple-200"
                              : "bg-emerald-50 text-emerald-800 border-emerald-200",
                        )}
                      >
                        {req.category}
                      </Badge>
                      <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                        {req.subCategory.replace(/_/g, " ")}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">
                        {req.submittedBy}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {req.submittedByRole}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-600">
                      {req.submissionDate.split("T")[0]}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={cn(
                          "text-[10px] font-bold px-2 py-0.5 rounded",
                          req.urgency === "CRITICAL"
                            ? "bg-red-100 text-red-800"
                            : req.urgency === "HIGH"
                              ? "bg-amber-100 text-amber-900"
                              : "bg-slate-100 text-slate-700",
                        )}
                      >
                        {req.urgency}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge
                        className={cn(
                          "text-[10px] font-bold",
                          req.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                            : req.status === "REJECTED"
                              ? "bg-red-100 text-red-800 border-red-200"
                              : req.status === "INFO_REQUESTED"
                                ? "bg-blue-100 text-blue-800 border-blue-200"
                                : "bg-yellow-100 text-yellow-950 border-yellow-300 animate-pulse",
                        )}
                      >
                        {req.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        size="sm"
                        onClick={() => setSelectedRequest(req)}
                        className={cn(
                          "text-xs font-bold h-7 px-3",
                          req.status === "PENDING"
                            ? "bg-yellow-400 text-slate-950 hover:bg-yellow-500 shadow-xs"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200",
                        )}
                      >
                        {req.status === "PENDING"
                          ? "Review & Act"
                          : "View Audit Trail"}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Review Drawer / Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full shadow-2xl border border-slate-200 max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-yellow-50/50">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-yellow-400 font-bold text-slate-950 flex items-center justify-center text-xs shrink-0 border border-yellow-500 shadow-xs">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-500 bg-white px-1.5 py-0.2 rounded border border-slate-200">
                      {selectedRequest.id}
                    </span>
                    <Badge
                      className={cn(
                        "text-[10px] font-bold",
                        selectedRequest.status === "APPROVED"
                          ? "bg-emerald-100 text-emerald-800"
                          : selectedRequest.status === "REJECTED"
                            ? "bg-red-100 text-red-800"
                            : selectedRequest.status === "INFO_REQUESTED"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-yellow-100 text-yellow-950",
                      )}
                    >
                      {selectedRequest.status}
                    </Badge>
                  </div>
                  <h3 className="font-black text-sm text-slate-900 mt-0.5">
                    {selectedRequest.title}
                  </h3>
                </div>
              </div>
              <button
                onClick={() => setSelectedRequest(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-md"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {/* Applicant & Summary Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Applicant
                  </div>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {selectedRequest.submittedBy}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {selectedRequest.submittedByRole}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Category
                  </div>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {selectedRequest.category}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    {selectedRequest.subCategory}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Submitted Date
                  </div>
                  <div className="font-bold text-slate-900 mt-0.5 font-mono">
                    {selectedRequest.submissionDate.split("T")[0]}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Urgency: {selectedRequest.urgency}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Department
                  </div>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {selectedRequest.departmentName}
                  </div>
                  <div className="text-[11px] text-emerald-600 font-semibold">
                    Authorized Scoped
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Request Statement & Justification
                </div>
                <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-800 leading-relaxed font-normal">
                  {selectedRequest.description}
                </div>
              </div>

              {/* Specific Details Payload */}
              <div className="space-y-1">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Specific Parameters & Arrangements
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5 font-mono text-[11px]">
                  {Object.entries(selectedRequest.details).map(([key, val]) => (
                    <div
                      key={key}
                      className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200/50 pb-1"
                    >
                      <span className="text-slate-500 font-bold uppercase text-[10px]">
                        {key.replace(/_/g, " ")}:
                      </span>
                      <span className="text-slate-900 font-semibold text-right">
                        {Array.isArray(val) ? val.join(", ") : String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Attachments */}
              {selectedRequest.attachments.length > 0 && (
                <div className="space-y-1">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Supporting Documents & Evidence
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedRequest.attachments.map((att) => (
                      <div
                        key={att.name}
                        onClick={() =>
                          alert(`Opening statutory attachment: ${att.name}`)
                        }
                        className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50 cursor-pointer transition-colors shadow-xs"
                      >
                        <FileText className="h-4 w-4 text-red-500" />
                        <div>
                          <div className="font-bold text-slate-900 text-xs">
                            {att.name}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {att.size} • {att.type}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Institutional Audit History */}
              <div className="space-y-1">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5 text-slate-400" />
                  Statutory Audit Trail
                </div>
                <div className="space-y-1.5 border border-slate-200 rounded-lg p-3 bg-slate-50">
                  {selectedRequest.auditTrail.map((audit, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2.5 text-[11px] border-b border-slate-200/50 pb-1.5 last:border-0"
                    >
                      <span className="font-bold font-mono text-yellow-800 bg-yellow-100 px-1 rounded text-[10px]">
                        {audit.action}
                      </span>
                      <div className="flex-1">
                        <span className="font-semibold text-slate-900">
                          {audit.by}
                        </span>
                        <span className="text-slate-500 text-[10px] ml-1">
                          ({audit.timestamp.replace("T", " ").replace("Z", "")})
                        </span>
                        {audit.notes && (
                          <div className="text-slate-600 mt-0.5 italic">
                            "{audit.notes}"
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Form if PENDING */}
              {selectedRequest.status === "PENDING" && (
                <div className="p-4 bg-yellow-50/60 rounded-xl border border-yellow-300 space-y-3">
                  <div className="text-xs font-bold text-yellow-950 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-yellow-700" />
                    HOD Statutory Decision & Remarks
                  </div>

                  <textarea
                    rows={2}
                    value={actionRemarks}
                    onChange={(e) => setActionRemarks(e.target.value)}
                    placeholder="Enter approval conditions, substitution instructions, or reason for rejection/clarification..."
                    className="w-full text-xs p-2.5 rounded-lg border border-yellow-300 bg-white focus:outline-none focus:ring-1 focus:ring-yellow-500"
                  />

                  <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={processingAction !== null}
                      onClick={() => handleAction("REQUEST_INFO")}
                      className="text-xs border-blue-300 text-blue-800 hover:bg-blue-50"
                    >
                      <HelpCircle className="h-3.5 w-3.5 mr-1 text-blue-600" />
                      Request Clarification
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      disabled={processingAction !== null}
                      onClick={() => handleAction("REJECT")}
                      className="text-xs border-red-300 text-red-800 hover:bg-red-50"
                    >
                      <XCircle className="h-3.5 w-3.5 mr-1 text-red-600" />
                      Reject Request
                    </Button>

                    <Button
                      type="button"
                      disabled={processingAction !== null}
                      onClick={() => handleAction("APPROVE")}
                      className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-xs"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      {processingAction === "APPROVE"
                        ? "Approving..."
                        : "Endorse & Approve"}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 bg-slate-50 border-t border-slate-100 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedRequest(null)}
                className="text-xs"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
