"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Briefcase,
  Calendar,
  CheckCircle2,
  DollarSign,
  Eye,
  EyeOff,
  FileCheck,
  FileText,
  Filter,
  Gavel,
  History,
  Lock,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  User,
  Users,
  X,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import {
  formatCurrency,
  formatLegalDate,
  getConfidentialityBadge,
  getMatterPriorityBadge,
  getMatterStatusBadge,
} from "@/services/legal-calculator";
import {
  InstitutionalLegalMatter,
  LegalMatterCategory,
  LegalMatterPriority,
  LegalMatterStatus,
  MatterCreateInput,
  MatterUpdateInput,
} from "@/types/legal";

export default function LegalMattersRegisterPage() {
  const [matters, setMatters] = useState<InstitutionalLegalMatter[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedPriority, setSelectedPriority] = useState<string>("ALL");

  // Privileged notes reveal toggles per matter id
  const [revealedNotes, setRevealedNotes] = useState<Record<string, boolean>>({});

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isUpdateOpen, setIsUpdateOpen] = useState(false);
  const [selectedMatter, setSelectedMatter] = useState<InstitutionalLegalMatter | null>(null);

  // Create form state
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState<LegalMatterCategory>("CONTRACT_DISPUTE");
  const [newPriority, setNewPriority] = useState<LegalMatterPriority>("MEDIUM");
  const [newSummary, setNewSummary] = useState("");
  const [newCounselName, setNewCounselName] = useState("");
  const [newCounselFirm, setNewCounselFirm] = useState("");
  const [newOpposingParty, setNewOpposingParty] = useState("");
  const [newPrivilegedNotes, setNewPrivilegedNotes] = useState("");

  // Update form state
  const [updateStatus, setUpdateStatus] = useState<LegalMatterStatus>("UNDER_REVIEW");
  const [updatePriority, setUpdatePriority] = useState<LegalMatterPriority>("HIGH");
  const [updateResolutionSummary, setUpdateResolutionSummary] = useState("");
  const [updateSettlementAmount, setUpdateSettlementAmount] = useState<number | undefined>(undefined);
  const [updateConfidentialNotes, setUpdateConfidentialNotes] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadMatters();
  }, [selectedCategory, selectedStatus, selectedPriority]);

  async function loadMatters() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await legalService.getMatters({
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        priority: selectedPriority !== "ALL" ? selectedPriority : undefined,
      });
      setMatters(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load restricted legal matters");
    } finally {
      setLoading(false);
    }
  }

  function toggleNoteReveal(matterId: string) {
    setRevealedNotes((prev) => ({
      ...prev,
      [matterId]: !prev[matterId],
    }));
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: MatterCreateInput = {
        title: newTitle,
        category: newCategory,
        priority: newPriority,
        description: newSummary,
        outside_counsel_json: newCounselName
          ? { attorney: newCounselName, firm: newCounselFirm || "Retained External Counsel" }
          : undefined,
        opposing_party_name: newOpposingParty || undefined,
        confidential_notes: newPrivilegedNotes || undefined,
      };
      await legalService.createMatter(input);
      setIsCreateOpen(false);
      resetCreateForm();
      await loadMatters();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create restricted legal matter");
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetCreateForm() {
    setNewTitle("");
    setNewSummary("");
    setNewCounselName("");
    setNewCounselFirm("");
    setNewOpposingParty("");
    setNewPrivilegedNotes("");
  }

  async function handleUpdateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedMatter) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: MatterUpdateInput = {
        status: updateStatus,
        priority: updatePriority,
        resolution_summary: updateResolutionSummary || undefined,
        settlement_amount: updateSettlementAmount,
        confidential_notes: updateConfidentialNotes || undefined,
      };
      await legalService.updateMatter(selectedMatter.id, input);
      setIsUpdateOpen(false);
      await loadMatters();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update legal matter");
    } finally {
      setIsSubmitting(false);
    }
  }

  function openUpdateModal(m: InstitutionalLegalMatter) {
    setSelectedMatter(m);
    setUpdateStatus(m.status);
    setUpdatePriority(m.priority);
    setUpdateResolutionSummary(m.resolution_summary || "");
    setUpdateSettlementAmount(m.settlement_amount ?? undefined);
    setUpdateConfidentialNotes(m.confidential_notes || "");
    setIsUpdateOpen(true);
  }

  const filteredMatters = matters.filter((m) => {
    if (
      searchTerm &&
      !m.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !m.matter_number.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !m.category.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Gavel className="h-6 w-6 text-indigo-600" /> Restricted Institutional Legal Matters
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Confidential case tracking for contract disputes, regulatory inquiries, litigation defense, and retained counsel engagements.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Open New Legal Matter
          </button>
        </div>

        {/* Security & Confidentiality Notice Banner */}
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0" />
            <div>
              <strong className="font-semibold block">RESTRICTED LEGAL PRIVILEGE CLASSIFICATION</strong>
              Records in this register are subject to institutional attorney-client privilege and work-product doctrine. Access is audited under CampusOS Compliance controls.
            </div>
          </div>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-amber-100 dark:bg-amber-950/80 border border-amber-300 dark:border-amber-800">
            CONFIDENTIALITY: RESTRICTED
          </span>
        </div>

        {/* Filter and Search Bar */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search matter title, number, or category..."
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
                <option value="CONTRACT_DISPUTE">Contract Dispute</option>
                <option value="VENDOR_DISPUTE">Vendor Dispute</option>
                <option value="EMPLOYMENT_MATTER">Employment Dispute</option>
                <option value="REGULATORY_INQUIRY">Regulatory Inquiry</option>
                <option value="LITIGATION_PROCEEDING">Litigation / Proceedings</option>
                <option value="LEGAL_OPINION">Legal Opinion / Advice</option>
                <option value="EXTERNAL_COUNSEL">External Counsel Engagement</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_INVESTIGATION">In Investigation</option>
                <option value="SETTLEMENT_NEGOTIATION">Settlement Negotiation</option>
                <option value="LITIGATION_PENDING">Litigation Pending</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>

              <select
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Priorities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              <button
                onClick={loadMatters}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                title="Refresh legal matters"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Matters Cards Grid */}
        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
            <p className="text-xs">Loading privileged legal matters...</p>
          </div>
        ) : filteredMatters.length === 0 ? (
          <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3">
            <Gavel className="h-10 w-10 text-slate-300 mx-auto" />
            <p className="text-base font-semibold text-slate-700 dark:text-slate-300">No Legal Matters Found</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No confidential legal matters match your current query or permissions scope.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredMatters.map((m) => {
              const isRevealed = revealedNotes[m.id];
              return (
                <div
                  key={m.id}
                  className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4 transition-all hover:border-slate-300 dark:hover:border-slate-700"
                >
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                          {m.matter_number}
                        </span>
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${getMatterPriorityBadge(
                            m.priority
                          )}`}
                        >
                          {m.priority}
                        </span>
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${getMatterStatusBadge(
                            m.status
                          )}`}
                        >
                          {m.status.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                          {m.category.replace(/_/g, " ")}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">{m.title}</h3>
                      {m.description && (
                        <p className="text-xs text-slate-600 dark:text-slate-400 max-w-3xl">
                          {m.description}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => openUpdateModal(m)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                      >
                        Update Status / Close
                      </button>
                    </div>
                  </div>

                  {/* Metadata Sub-grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-100 dark:border-slate-800">
                    <div>
                      <span className="text-slate-400 block">Opposing Party</span>
                      <strong className="text-slate-700 dark:text-slate-200">
                        {m.opposing_party_name || "Confidential / Unspecified"}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Outside Counsel</span>
                      <strong className="text-slate-700 dark:text-slate-200">
                        {m.outside_counsel_json?.attorney
                          ? `${m.outside_counsel_json.attorney} (${m.outside_counsel_json.firm || "Firm"})`
                          : "In-House Legal Counsel"}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Filed / Opened Date</span>
                      <strong className="text-slate-700 dark:text-slate-200">
                        {formatLegalDate(m.opened_date || m.created_at)}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Settlement / Exposure</span>
                      <strong className="text-slate-700 dark:text-slate-200">
                        {m.settlement_amount ? formatCurrency(m.settlement_amount) : "No Direct Claim"}
                      </strong>
                    </div>
                  </div>

                  {/* Resolution Summary (if resolved) */}
                  {m.resolution_summary && (
                    <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs">
                      <strong className="text-emerald-800 dark:text-emerald-300 block mb-0.5">
                        Resolution & Settlement Summary:
                      </strong>
                      <p className="text-emerald-900 dark:text-emerald-200">{m.resolution_summary}</p>
                    </div>
                  )}

                  {/* Privileged Legal Notes Toggle */}
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <button
                      onClick={() => toggleNoteReveal(m.id)}
                      className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1.5"
                    >
                      {isRevealed ? (
                        <>
                          <EyeOff className="h-3.5 w-3.5" /> Hide Attorney-Client Privileged Notes
                        </>
                      ) : (
                        <>
                          <Eye className="h-3.5 w-3.5" /> View Attorney-Client Privileged Notes
                        </>
                      )}
                    </button>
                    <span className="text-[10px] text-slate-400">
                      Last Updated: {formatLegalDate(m.updated_at)}
                    </span>
                  </div>

                  {/* Revealed Notes Content */}
                  {isRevealed && (
                    <div className="p-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/80 text-xs space-y-2">
                      <div className="flex items-center gap-2 text-indigo-800 dark:text-indigo-300 font-bold">
                        <Lock className="h-3.5 w-3.5" />
                        Privileged Counsel Work-Product Record
                      </div>
                      <p className="text-indigo-950 dark:text-indigo-200 font-mono text-xs leading-relaxed">
                        {m.confidential_notes || "No restricted counsel notes recorded for this matter."}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* MODAL 1: Open New Legal Matter */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-xl w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Gavel className="h-5 w-5 text-indigo-600" /> Open Institutional Legal Matter
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
                  Matter Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. In the Matter of SaaS Vendor Cloud SLA Dispute"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Matter Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as LegalMatterCategory)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="CONTRACT_DISPUTE">Contract Dispute</option>
                    <option value="VENDOR_DISPUTE">Vendor Dispute</option>
                    <option value="EMPLOYMENT_MATTER">Employment Dispute</option>
                    <option value="REGULATORY_INQUIRY">Regulatory Inquiry</option>
                    <option value="LITIGATION_PROCEEDING">Litigation / Proceedings</option>
                    <option value="LEGAL_OPINION">Legal Opinion / Advice</option>
                    <option value="EXTERNAL_COUNSEL">External Counsel Engagement</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Matter Priority
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as LegalMatterPriority)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Opposing Party / Counterparty
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Apex Network Technologies Inc."
                    value={newOpposingParty}
                    onChange={(e) => setNewOpposingParty(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Outside Counsel Attorney
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Adv. Margaret Vance"
                    value={newCounselName}
                    onChange={(e) => setNewCounselName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Public Administrative Summary
                </label>
                <textarea
                  rows={2}
                  placeholder="High-level description of matter scope and key dates..."
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-amber-600 dark:text-amber-400 mb-1 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5" /> Confidential Counsel Notes (Privileged)
                </label>
                <textarea
                  rows={3}
                  placeholder="Record confidential legal strategy, litigation risk assessment, and privileged discussions..."
                  value={newPrivilegedNotes}
                  onChange={(e) => setNewPrivilegedNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50/20 dark:bg-amber-950/20 text-slate-900 dark:text-white text-xs font-mono"
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
                  {isSubmitting ? "Creating..." : "Register Legal Matter"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Update / Resolve Matter */}
      {isUpdateOpen && selectedMatter && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-indigo-600" /> Update Matter Status / Closure
              </h3>
              <button
                onClick={() => setIsUpdateOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateSubmit} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Matter Status
                  </label>
                  <select
                    value={updateStatus}
                    onChange={(e) => setUpdateStatus(e.target.value as LegalMatterStatus)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="IN_INVESTIGATION">IN_INVESTIGATION</option>
                    <option value="SETTLEMENT_NEGOTIATION">SETTLEMENT_NEGOTIATION</option>
                    <option value="LITIGATION_PENDING">LITIGATION_PENDING</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Priority Level
                  </label>
                  <select
                    value={updatePriority}
                    onChange={(e) => setUpdatePriority(e.target.value as LegalMatterPriority)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Settlement / Exposure Amount ($)
                </label>
                <input
                  type="number"
                  value={updateSettlementAmount !== undefined ? updateSettlementAmount : ""}
                  onChange={(e) =>
                    setUpdateSettlementAmount(e.target.value ? parseFloat(e.target.value) : undefined)
                  }
                  placeholder="0.00"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Resolution / Outcome Summary
                </label>
                <textarea
                  rows={2}
                  placeholder="Record formal resolution terms, settlement agreements, or dismissal orders..."
                  value={updateResolutionSummary}
                  onChange={(e) => setUpdateResolutionSummary(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-amber-600 dark:text-amber-400 mb-1 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5" /> Confidential Legal Notes
                </label>
                <textarea
                  rows={3}
                  value={updateConfidentialNotes}
                  onChange={(e) => setUpdateConfidentialNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50/20 dark:bg-amber-950/20 text-slate-900 dark:text-white text-xs font-mono"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUpdateOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Saving..." : "Save Updates"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
