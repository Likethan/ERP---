"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Filter,
  Plus,
  RefreshCw,
  Search,
  Building2,
  Calendar,
  DollarSign,
  Shield,
  ArrowUpDown,
  X,
  CheckCircle2,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { getContractStatusBadge } from "@/services/legal-calculator";
import { LegalService } from "@/services/legal.service";
import {
  ConfidentialityLevel,
  ContractCategory,
  ContractCreateInput,
  ContractStatus,
  InstitutionalContract,
} from "@/types/legal";

const CATEGORIES: { label: string; value: ContractCategory }[] = [
  { label: "Vendor & Procurement", value: "VENDOR_PROCUREMENT" },
  { label: "Employment & Consulting", value: "EMPLOYMENT_CONSULTING" },
  { label: "Service Level Agreement (SLA)", value: "SERVICE_LEVEL" },
  { label: "Student & Campus Service", value: "STUDENT_SERVICE" },
  { label: "Research & Sponsored Projects", value: "RESEARCH_SPONSORED" },
  { label: "Industry Collaboration", value: "INDUSTRY_COLLABORATION" },
  { label: "Data Processing & NDA", value: "DATA_PROCESSING_NDA" },
  { label: "Facility Use & Partnership", value: "FACILITY_PARTNERSHIP" },
  { label: "International Institutional", value: "INTERNATIONAL_INSTITUTIONAL" },
  { label: "Other Configured Type", value: "OTHER" },
];

export default function ContractsRegisterPage() {
  const [contracts, setContracts] = useState<InstitutionalContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState<Partial<ContractCreateInput>>({
    title: "",
    category: "VENDOR_PROCUREMENT",
    purpose: "",
    counterparty_name: "",
    effective_date: new Date().toISOString().split("T")[0],
    expiration_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
    financial_value: 0,
    currency: "USD",
    confidentiality_level: "INTERNAL",
    renewal_notice_days: 30,
    termination_notice_days: 30,
    auto_renew: false,
    internal_owner_id: "00000000-0000-0000-0000-000000000001",
  });
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    loadContracts();
  }, [selectedCategory, selectedStatus]);

  async function loadContracts() {
    setLoading(true);
    try {
      const data = await LegalService.getContracts({
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        search: search.trim() || undefined,
      });
      setContracts(data);
    } catch (err) {
      console.error("Failed to load contracts", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.title || !formData.counterparty_name) {
      setFormError("Title and counterparty organization are required fields.");
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      await LegalService.createContract(formData as ContractCreateInput);
      setShowCreateModal(false);
      setFormData({
        title: "",
        category: "VENDOR_PROCUREMENT",
        purpose: "",
        counterparty_name: "",
        effective_date: new Date().toISOString().split("T")[0],
        expiration_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
        financial_value: 0,
        currency: "USD",
        confidentiality_level: "INTERNAL",
        renewal_notice_days: 30,
        termination_notice_days: 30,
        auto_renew: false,
        internal_owner_id: "00000000-0000-0000-0000-000000000001",
      });
      await loadContracts();
    } catch (err: any) {
      setFormError(err.message || "Failed to create contract draft");
    } finally {
      setSubmitting(false);
    }
  }

  const filteredContracts = contracts.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.title.toLowerCase().includes(q) ||
      c.contract_number.toLowerCase().includes(q) ||
      c.counterparty_name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <LegalNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              Institutional Contracts Register
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Complete centralized lifecycle tracking across procurement, employment, research, and campus partnerships.
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-1.5 transition self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>New Contract Draft</span>
          </button>
        </div>

        {/* Filters Bar */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search contracts by number, title, or counterparty..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              <option value="ALL">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="INTERNAL_REVIEW">Internal Review</option>
              <option value="DEPARTMENT_APPROVAL">Department Approval</option>
              <option value="LEGAL_REVIEW">Legal Review</option>
              <option value="AUTHORIZED_APPROVAL">Authorized Approval</option>
              <option value="READY_FOR_EXECUTION">Ready for Execution</option>
              <option value="EXECUTED">Executed</option>
              <option value="ACTIVE">Active</option>
              <option value="EXPIRING">Expiring Soon</option>
              <option value="RENEWED">Renewed</option>
              <option value="TERMINATED">Terminated</option>
              <option value="EXPIRED">Expired</option>
            </select>

            <button
              onClick={loadContracts}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition"
              title="Refresh register"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Contracts Table */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold">
                <tr>
                  <th className="py-3 px-4">Contract Code & Title</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Counterparty</th>
                  <th className="py-3 px-4">Lifecycle Status</th>
                  <th className="py-3 px-4">Effective / Expiration</th>
                  <th className="py-3 px-4 text-right">Value</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      <RefreshCw className="h-4 w-4 animate-spin inline-block mr-2" />
                      Loading contracts...
                    </td>
                  </tr>
                ) : filteredContracts.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No matching contracts found.
                    </td>
                  </tr>
                ) : (
                  filteredContracts.map((c) => {
                    const badge = getContractStatusBadge(c.status);
                    return (
                      <tr
                        key={c.id}
                        className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition"
                      >
                        <td className="py-3 px-4">
                          <Link
                            href={`/app/legal/contracts/${c.id}`}
                            className="font-bold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 block"
                          >
                            {c.title}
                          </Link>
                          <span className="font-mono text-[10px] text-slate-500">
                            {c.contract_number}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-[11px] text-slate-600 dark:text-slate-300">
                            {c.category.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-800 dark:text-slate-200">
                            {c.counterparty_name}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badge.className}`}
                          >
                            {badge.label}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[11px] text-slate-600 dark:text-slate-300">
                          {c.effective_date || "—"} &rarr; {c.expiration_date || "—"}
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-slate-900 dark:text-white">
                          {c.financial_value ? `$${c.financial_value.toLocaleString()}` : "N/A"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link
                            href={`/app/legal/contracts/${c.id}`}
                            className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-indigo-950 transition"
                          >
                            Workspace
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-600" />
                Initialize Institutional Contract Draft
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {formError && (
              <div className="p-3 text-xs bg-red-50 text-red-700 border border-red-200 rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Contract Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Campus Wide Cloud ERP Hosting Agreement"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value as ContractCategory })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Counterparty Organization *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. AWS Cloud Services Inc."
                    value={formData.counterparty_name}
                    onChange={(e) => setFormData({ ...formData, counterparty_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Financial Value ($ USD)</label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={formData.financial_value || 0}
                    onChange={(e) => setFormData({ ...formData, financial_value: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Effective Date</label>
                  <input
                    type="date"
                    value={formData.effective_date}
                    onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">Expiration Date</label>
                  <input
                    type="date"
                    value={formData.expiration_date}
                    onChange={(e) => setFormData({ ...formData, expiration_date: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700 dark:text-slate-300">Purpose & Scope Summary</label>
                <textarea
                  rows={3}
                  placeholder="Summarize the core institutional commitments and contractual objectives..."
                  value={formData.purpose || ""}
                  onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submitting ? "Initializing..." : "Create Contract Draft"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
