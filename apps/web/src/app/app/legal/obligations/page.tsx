"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  History,
  Lock,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import {
  calculateObligationHealth,
  formatLegalDate,
  getObligationStatusBadge,
  isObligationOverdue,
} from "@/services/legal-calculator";
import {
  ContractObligation,
  ContractObligationCreateInput,
  ObligationCategory,
  ObligationCompleteInput,
  ObligationStatus,
  ObligationWaiveInput,
} from "@/types/legal";

export default function ObligationsRegisterPage() {
  const [obligations, setObligations] = useState<ContractObligation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [overdueOnly, setOverdueOnly] = useState<boolean>(false);

  // Modals
  const [selectedObligation, setSelectedObligation] = useState<ContractObligation | null>(null);
  const [isCompleteOpen, setIsCompleteOpen] = useState(false);
  const [isWaiveOpen, setIsWaiveOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Complete Form
  const [completionNotes, setCompletionNotes] = useState("");
  const [completionEvidence, setCompletionEvidence] = useState("");

  // Waive Form
  const [waiverRationale, setWaiverRationale] = useState("");
  const [authorizedApprover, setAuthorizedApprover] = useState("University General Counsel / VP");

  // Create Form
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState<ObligationCategory>("DELIVERABLE");
  const [newDueDate, setNewDueDate] = useState("");
  const [newEvidence, setNewEvidence] = useState("");
  const [newContractId, setNewContractId] = useState("c01-campus-wifi");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadObligations();
  }, [overdueOnly, selectedStatus]);

  async function loadObligations() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await legalService.getObligations({
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        overdue_only: overdueOnly,
      });
      setObligations(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load contract obligations");
    } finally {
      setLoading(false);
    }
  }

  async function handleCompleteSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedObligation) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ObligationCompleteInput = {
        completion_notes: completionNotes,
        completion_evidence_ref: completionEvidence,
      };
      await legalService.completeObligation(selectedObligation.id, input);
      setIsCompleteOpen(false);
      setCompletionNotes("");
      setCompletionEvidence("");
      await loadObligations();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to complete obligation");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleWaiveSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedObligation) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ObligationWaiveInput = {
        waiver_rationale: waiverRationale,
        authorized_by: authorizedApprover,
      };
      await legalService.waiveObligation(selectedObligation.id, input);
      setIsWaiveOpen(false);
      setWaiverRationale("");
      await loadObligations();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record formal waiver");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ContractObligationCreateInput = {
        contract_id: newContractId,
        title: newTitle,
        category: newCategory,
        due_date: newDueDate,
        required_evidence: newEvidence,
      };
      await legalService.createObligation(input);
      setIsCreateOpen(false);
      setNewTitle("");
      setNewEvidence("");
      await loadObligations();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register obligation");
    } finally {
      setIsSubmitting(false);
    }
  }

  const health = calculateObligationHealth(obligations);

  const filteredObligations = obligations.filter((obl) => {
    const categoryVal = obl.category || obl.obligation_type || "";
    if (selectedCategory !== "ALL" && categoryVal !== selectedCategory) return false;
    if (
      searchTerm &&
      !obl.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !categoryVal.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header & Primary Action */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              Contract Obligations & Commitments Register
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Auditable tracking of institutional contract deliverables, reporting deadlines, insurance certificates, and service SLAs.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Register New Obligation
          </button>
        </div>

        {/* Telemetry KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <span className="text-xs text-slate-500 block">Total Obligations</span>
            <div className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{health.total}</div>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <span className="text-xs text-slate-500 block">Pending / In Progress</span>
            <div className="text-2xl font-bold mt-1 text-indigo-600 dark:text-indigo-400">
              {health.pending + health.in_progress}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/50 shadow-sm bg-rose-50/20">
            <span className="text-xs text-rose-600 font-semibold block flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" /> Overdue Obligations
            </span>
            <div className="text-2xl font-bold mt-1 text-rose-600">{health.overdue}</div>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <span className="text-xs text-slate-500 block">Satisfied / Completed</span>
            <div className="text-2xl font-bold mt-1 text-emerald-600">{health.completed}</div>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <span className="text-xs text-slate-500 block">Authorized Waivers</span>
            <div className="text-2xl font-bold mt-1 text-slate-600 dark:text-slate-400">{health.waived}</div>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search obligation, title, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Categories</option>
                <option value="DELIVERABLE">Deliverables</option>
                <option value="REPORTING">Reporting Milestones</option>
                <option value="PAYMENT_MILESTONE">Payment Milestones</option>
                <option value="SERVICE_COMMITMENT">Service Commitments / SLAs</option>
                <option value="INSURANCE_REQUIREMENT">Insurance Policies & COIs</option>
                <option value="RENEWAL_NOTICE">Renewal Notice Windows</option>
                <option value="AUDIT_RIGHT">Audit & Inspection Rights</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="OVERDUE">Overdue</option>
                <option value="COMPLETED">Completed</option>
                <option value="WAIVED">Waived</option>
              </select>

              <button
                onClick={() => setOverdueOnly(!overdueOnly)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-colors flex items-center gap-1.5 ${
                  overdueOnly
                    ? "bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                }`}
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Overdue Only
              </button>

              <button
                onClick={loadObligations}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                title="Refresh obligations"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Obligations Table */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
              <p className="text-xs">Loading contractual obligations register...</p>
            </div>
          ) : filteredObligations.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <CheckCircle2 className="h-8 w-8 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Obligations Found</p>
              <p className="text-xs text-slate-500">No obligations match your active filter criteria.</p>
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Obligation Title</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Due Date</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Escalation</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {filteredObligations.map((obl) => {
                  const overdue = isObligationOverdue(obl);
                  return (
                    <tr key={obl.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="px-6 py-4">
                        <strong className="block text-slate-900 dark:text-white">{obl.title}</strong>
                        {obl.required_evidence && (
                          <span className="text-xs text-slate-400 mt-0.5 block">
                            Evidence: {obl.required_evidence}
                          </span>
                        )}
                        {obl.completion_notes && (
                          <span className="text-xs text-emerald-600 mt-0.5 block">
                            Note: {obl.completion_notes}
                          </span>
                        )}
                        {obl.waiver_rationale && (
                          <span className="text-xs text-amber-600 mt-0.5 block">
                            Waiver Rationale: {obl.waiver_rationale}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-slate-600 dark:text-slate-300">
                        {obl.category}
                      </td>
                      <td className="px-6 py-4 text-xs font-mono">
                        <div className="flex items-center gap-1.5">
                          {overdue && <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />}
                          <span className={overdue ? "text-rose-600 font-bold" : "text-slate-600 dark:text-slate-300"}>
                            {formatLegalDate(obl.due_date)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${getObligationStatusBadge(
                            obl.status
                          )}`}
                        >
                          {obl.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {obl.escalation_level > 0 ? (
                          <span className="text-rose-600 font-bold flex items-center gap-1">
                            <AlertTriangle className="h-3.5 w-3.5" /> Level {obl.escalation_level}
                          </span>
                        ) : (
                          <span className="text-slate-400">Normal</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {obl.status !== "COMPLETED" && obl.status !== "WAIVED" && (
                          <>
                            <button
                              onClick={() => {
                                setSelectedObligation(obl);
                                setIsCompleteOpen(true);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs font-medium hover:bg-emerald-100"
                            >
                              Complete
                            </button>
                            <button
                              onClick={() => {
                                setSelectedObligation(obl);
                                setIsWaiveOpen(true);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-medium hover:bg-amber-100"
                            >
                              Waive
                            </button>
                          </>
                        )}
                        <Link
                          href={`/app/legal/contracts/${obl.contract_id}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-medium hover:bg-slate-200 inline-flex items-center gap-1"
                        >
                          Contract <ExternalLink className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* MODAL 1: Complete Obligation */}
      {isCompleteOpen && selectedObligation && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-emerald-600" /> Complete Contract Obligation
              </h3>
              <button
                onClick={() => setIsCompleteOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Record verified completion and evidence for <strong>{selectedObligation.title}</strong>.
            </p>

            <form onSubmit={handleCompleteSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Evidence / Artifact Reference
                </label>
                <input
                  type="text"
                  placeholder="e.g. DOC-EVID-2026-0091 or audit certificate reference"
                  value={completionEvidence}
                  onChange={(e) => setCompletionEvidence(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Completion Verification Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Summarize reviewer findings, deliverable receipt, or SLA confirmation..."
                  value={completionNotes}
                  onChange={(e) => setCompletionNotes(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950 text-rose-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCompleteOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700"
                >
                  {isSubmitting ? "Submitting..." : "Verify & Complete"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Waive Obligation */}
      {isWaiveOpen && selectedObligation && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-amber-600" /> Formal Obligation Waiver
              </h3>
              <button
                onClick={() => setIsWaiveOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                <strong>Institutional Policy:</strong> Waiving a contractual commitment requires documented executive or legal rationale. This action creates an immutable audit entry.
              </span>
            </div>

            <form onSubmit={handleWaiveSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Authorizing Institutional Official
                </label>
                <input
                  type="text"
                  value={authorizedApprover}
                  onChange={(e) => setAuthorizedApprover(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Legal / Executive Waiver Rationale
                </label>
                <textarea
                  rows={3}
                  placeholder="State the justification, compensating controls, or mutual agreement to waive..."
                  value={waiverRationale}
                  onChange={(e) => setWaiverRationale(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950 text-rose-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsWaiveOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-amber-600 text-white text-xs font-medium hover:bg-amber-700"
                >
                  {isSubmitting ? "Recording..." : "Record Official Waiver"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Create Obligation */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-indigo-600" /> Register Contract Obligation
              </h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Obligation Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Quarterly SLA Availability & Uptime Reporting"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as ObligationCategory)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="DELIVERABLE">DELIVERABLE</option>
                    <option value="REPORTING">REPORTING</option>
                    <option value="PAYMENT_MILESTONE">PAYMENT_MILESTONE</option>
                    <option value="SERVICE_COMMITMENT">SERVICE_COMMITMENT</option>
                    <option value="INSURANCE_REQUIREMENT">INSURANCE_REQUIREMENT</option>
                    <option value="RENEWAL_NOTICE">RENEWAL_NOTICE</option>
                    <option value="AUDIT_RIGHT">AUDIT_RIGHT</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Due Date
                  </label>
                  <input
                    type="date"
                    value={newDueDate}
                    onChange={(e) => setNewDueDate(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Required Proof / Deliverable Evidence
                </label>
                <textarea
                  rows={2}
                  placeholder="Specify documentation required for compliance audit..."
                  value={newEvidence}
                  onChange={(e) => setNewEvidence(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Creating..." : "Register Obligation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
