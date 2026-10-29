"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
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
  ShieldAlert,
  ShieldCheck,
  User,
  Users,
  Wrench,
  X,
  XCircle,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import {
  formatLegalDate,
  getComplianceStatusBadge,
} from "@/services/legal-calculator";
import {
  ComplianceAssessInput,
  ComplianceCategory,
  ComplianceCreateInput,
  ComplianceStatus,
  InstitutionalComplianceObligation,
} from "@/types/legal";

export default function ComplianceEvidencePage() {
  const [obligations, setObligations] = useState<InstitutionalComplianceObligation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Modals
  const [isAssessOpen, setIsAssessOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedObligation, setSelectedObligation] = useState<InstitutionalComplianceObligation | null>(null);

  // Assess form
  const [assessStatus, setAssessStatus] = useState<ComplianceStatus>("COMPLIANT");
  const [assessFindings, setAssessFindings] = useState("");
  const [evidenceRef, setEvidenceRef] = useState("");
  const [actionTitle, setActionTitle] = useState("");
  const [actionOwner, setActionOwner] = useState("University Compliance Director");
  const [actionDueDate, setActionDueDate] = useState("");

  // Create form
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState<ComplianceCategory>("DATA_PRIVACY_SECURITY");
  const [newAuthority, setNewAuthority] = useState("");
  const [newSourceRef, setNewSourceRef] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newDueDate, setNewDueDate] = useState("");
  const [newFrequency, setNewFrequency] = useState("ANNUAL");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadCompliance();
  }, [selectedCategory, selectedStatus]);

  async function loadCompliance() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await legalService.getComplianceObligations({
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
      });
      setObligations(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load compliance obligations");
    } finally {
      setLoading(false);
    }
  }

  async function handleAssessSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedObligation) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ComplianceAssessInput = {
        status: assessStatus,
        findings_summary: assessFindings,
        evidence_reference: evidenceRef || undefined,
        corrective_action_plan: actionTitle
          ? {
              action: actionTitle,
              owner: actionOwner,
              target_date: actionDueDate || undefined,
            }
          : undefined,
      };
      await legalService.assessCompliance(selectedObligation.id, input);
      setIsAssessOpen(false);
      resetAssessForm();
      await loadCompliance();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record compliance assessment");
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetAssessForm() {
    setAssessFindings("");
    setEvidenceRef("");
    setActionTitle("");
    setActionDueDate("");
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: ComplianceCreateInput = {
        title: newTitle,
        category: newCategory,
        governing_authority: newAuthority,
        source_reference: newSourceRef,
        description: newDescription,
        next_review_due: newDueDate,
        review_frequency: newFrequency,
      };
      await legalService.createComplianceObligation(input);
      setIsCreateOpen(false);
      resetCreateForm();
      await loadCompliance();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register compliance requirement");
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetCreateForm() {
    setNewTitle("");
    setNewAuthority("");
    setNewSourceRef("");
    setNewDescription("");
    setNewDueDate("");
  }

  function openAssessModal(item: InstitutionalComplianceObligation) {
    setSelectedObligation(item);
    setAssessStatus(item.status);
    setAssessFindings(item.review_findings || item.assessment_findings || "");
    setEvidenceRef(item.required_evidence_reference || "");
    setIsAssessOpen(true);
  }

  const filteredObligations = obligations.filter((item) => {
    const titleVal = item.title || item.name || "";
    const authVal = item.governing_authority || item.authoritative_source_reference || "";
    if (
      searchTerm &&
      !titleVal.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !authVal.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !item.category.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="h-6 w-6 text-indigo-600" /> Statutory Compliance & Evidence Assessment
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Institutional compliance oversight for Accreditation, FERPA, Title IX, Clery Act, Research Ethics, and Financial Aid regulations.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Register Compliance Requirement
          </button>
        </div>

        {/* Filter and Search Bar */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search obligation, authority, or standard..."
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
                <option value="ALL">All Statutory Frameworks</option>
                <option value="ACCREDITATION">Accreditation (Regional / Professional)</option>
                <option value="FERPA_PRIVACY">FERPA & Student Privacy</option>
                <option value="TITLE_IX">Title IX & Gender Equity</option>
                <option value="CLERY_ACT">Clery Act & Campus Safety</option>
                <option value="RESEARCH_ETHICS">Research Ethics & Animal Welfare</option>
                <option value="ADA_ACCESSIBILITY">ADA & Digital Accessibility</option>
                <option value="ENVIRONMENTAL_SAFETY">OSHA & Environmental Safety</option>
                <option value="FINANCIAL_AID">Financial Aid (Title IV HEA)</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Assessment Statuses</option>
                <option value="COMPLIANT">Compliant</option>
                <option value="PARTIALLY_COMPLIANT">Partially Compliant</option>
                <option value="EVIDENCE_REQUIRED">Evidence Required</option>
                <option value="REMEDIATION_IN_PROGRESS">Remediation in Progress</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="NOT_ASSESSED">Not Assessed</option>
                <option value="NON_COMPLIANT">Non-Compliant</option>
              </select>

              <button
                onClick={loadCompliance}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                title="Refresh compliance list"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Compliance Table */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
              <p className="text-xs">Loading statutory compliance obligations...</p>
            </div>
          ) : filteredObligations.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <CheckCircle2 className="h-8 w-8 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Compliance Records Found</p>
              <p className="text-xs text-slate-500">No records match your query.</p>
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Requirement / Standard</th>
                  <th className="px-6 py-3.5">Governing Authority</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Next Review</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {filteredObligations.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-6 py-4">
                      <strong className="block text-slate-900 dark:text-white">{item.title || item.name}</strong>
                      {(item.source_reference || item.authoritative_source_reference) && (
                        <span className="text-xs font-mono text-slate-400 block mt-0.5">
                          Ref: {item.source_reference || item.authoritative_source_reference}
                        </span>
                      )}
                      {(item.review_findings || item.assessment_findings) && (
                        <span className="text-xs text-slate-500 block mt-1">
                          Findings: {item.review_findings || item.assessment_findings}
                        </span>
                      )}
                      {item.corrective_action_plan && (
                        <span className="text-xs text-amber-600 font-medium block mt-1 flex items-center gap-1">
                          <Wrench className="h-3 w-3" /> CAP: {item.corrective_action_plan.action}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-700 dark:text-slate-300">
                      {item.governing_authority || item.category}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-500">
                      {item.category.replace(/_/g, " ")}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono">
                      {formatLegalDate(item.next_review_due || item.next_review_date || item.due_date)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-medium ${getComplianceStatusBadge(
                          item.status
                        )}`}
                      >
                        {item.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => openAssessModal(item)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-xs font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900 transition-colors"
                      >
                        Assess / Audit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* MODAL 1: Assess Compliance */}
      {isAssessOpen && selectedObligation && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-indigo-600" /> Record Compliance Assessment
              </h3>
              <button
                onClick={() => setIsAssessOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Evaluating: <strong>{selectedObligation.title || selectedObligation.name}</strong> ({selectedObligation.governing_authority || selectedObligation.category})
            </p>

            <form onSubmit={handleAssessSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Determination Status
                </label>
                <select
                  value={assessStatus}
                  onChange={(e) => setAssessStatus(e.target.value as ComplianceStatus)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="COMPLIANT">COMPLIANT — All controls and audits verified</option>
                  <option value="PARTIALLY_COMPLIANT">PARTIALLY_COMPLIANT — Minor gaps identified</option>
                  <option value="EVIDENCE_REQUIRED">EVIDENCE_REQUIRED — Pending documentation</option>
                  <option value="REMEDIATION_IN_PROGRESS">REMEDIATION_IN_PROGRESS — Active corrective plan</option>
                  <option value="NON_COMPLIANT">NON_COMPLIANT — Material deficiency</option>
                  <option value="UNDER_REVIEW">UNDER_REVIEW — External audit underway</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Supporting Evidence / Document Reference
                </label>
                <input
                  type="text"
                  placeholder="e.g. DOC-AUDIT-2026-NECHE-04"
                  value={evidenceRef}
                  onChange={(e) => setEvidenceRef(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Assessment Findings & Auditor Review
                </label>
                <textarea
                  rows={3}
                  placeholder="Detail test results, sample reviews, and regulatory findings..."
                  value={assessFindings}
                  onChange={(e) => setAssessFindings(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {/* Corrective Action Plan section */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block flex items-center gap-1.5">
                  <Wrench className="h-3.5 w-3.5 text-amber-500" /> Corrective Action Plan (Optional)
                </span>
                <div>
                  <input
                    type="text"
                    placeholder="Remediation action (e.g. Conduct campus-wide Title IX training)"
                    value={actionTitle}
                    onChange={(e) => setActionTitle(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Action Owner"
                    value={actionOwner}
                    onChange={(e) => setActionOwner(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
                  />
                  <input
                    type="date"
                    value={actionDueDate}
                    onChange={(e) => setActionDueDate(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950 text-rose-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAssessOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Submitting..." : "Save Assessment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Register Compliance Requirement */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-indigo-600" /> Register Compliance Requirement
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
                  placeholder="e.g. Annual Campus Security & Fire Safety (Clery Report)"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Regulatory Framework
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as ComplianceCategory)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="ACCREDITATION">ACCREDITATION</option>
                    <option value="FERPA_PRIVACY">FERPA_PRIVACY</option>
                    <option value="TITLE_IX">TITLE_IX</option>
                    <option value="CLERY_ACT">CLERY_ACT</option>
                    <option value="RESEARCH_ETHICS">RESEARCH_ETHICS</option>
                    <option value="ADA_ACCESSIBILITY">ADA_ACCESSIBILITY</option>
                    <option value="ENVIRONMENTAL_SAFETY">ENVIRONMENTAL_SAFETY</option>
                    <option value="FINANCIAL_AID">FINANCIAL_AID</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Governing Authority
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. U.S. Dept. of Education / NECHE"
                    value={newAuthority}
                    onChange={(e) => setNewAuthority(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Source Standard Reference
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 20 U.S.C. § 1092(f)"
                    value={newSourceRef}
                    onChange={(e) => setNewSourceRef(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Next Review Due Date
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
                  Scope & Compliance Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Outline statutory requirements, institutional controls, and department accountability..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
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
                  {isSubmitting ? "Creating..." : "Save Requirement"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
