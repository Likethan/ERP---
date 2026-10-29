"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Filter,
  Plus,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { AgreementAmendment, InstitutionalAgreement, InternationalPartner } from "@/types/international";

export default function AgreementsManagementPage() {
  const [agreements, setAgreements] = useState<InstitutionalAgreement[]>([]);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedAgreementForAmendment, setSelectedAgreementForAmendment] = useState<InstitutionalAgreement | null>(null);

  // New Agreement Form
  const [formData, setFormData] = useState({
    partner_id: "",
    agreement_reference_number: "",
    agreement_title: "",
    agreement_type: "MOU",
    effective_start_date: new Date().toISOString().split("T")[0],
    effective_end_date: new Date(Date.now() + 365 * 86400000 * 3).toISOString().split("T")[0],
    renewal_warning_days: 90,
  });
  const [submitting, setSubmitting] = useState(false);

  // New Amendment Form
  const [amendmentForm, setAmendmentForm] = useState({
    title: "",
    description: "",
    amendment_type: "EXTENSION",
    new_effective_end_date: "",
  });
  const [submittingAmendment, setSubmittingAmendment] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const [agrs, pts] = await Promise.all([
        internationalService.getAgreements({
          status: statusFilter !== "ALL" ? statusFilter : undefined,
        }),
        internationalService.getPartners(),
      ]);
      setAgreements(agrs);
      setPartners(pts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAgreement(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const partner = partners.find((p) => p.id === formData.partner_id);
      const res = await internationalService.createAgreement({
        ...formData,
        partner_name: partner?.partner_name || partner?.name || "Partner",
      });
      setAgreements([res, ...agreements]);
      setShowAddModal(false);
    } catch (err) {
      console.error(err);
      alert("Failed to create agreement");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddAmendment(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAgreementForAmendment) return;
    setSubmittingAmendment(true);
    try {
      await internationalService.addAmendment(selectedAgreementForAmendment.id, amendmentForm);
      alert("Amendment recorded successfully and agreement expiry updated.");
      setSelectedAgreementForAmendment(null);
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to add amendment");
    } finally {
      setSubmittingAmendment(false);
    }
  }

  const filtered = agreements.filter((a) => {
    const text = `${a.agreement_title || a.title} ${a.agreement_reference_number || a.agreementReferenceNumber} ${a.partner_name || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-400" />
              Institutional Agreements & MoUs Management
            </h2>
            <p className="text-xs text-slate-400">
              Maintain bilateral treaties, student exchange protocols, and legal renewal audit trails
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            New Institutional Agreement
          </button>
        </div>

        {/* Filters */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by MoU title, reference number, or partner institution..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-full md:w-auto"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="EXPIRING">Expiring Soon</option>
            <option value="APPROVED">Approved</option>
            <option value="DRAFT">Draft</option>
            <option value="EXPIRED">Expired</option>
          </select>
        </div>

        {/* Agreements Table */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Agreement Ref & Title</th>
                  <th className="py-3 px-4">Partner Institution</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Validity Period</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      Loading agreements...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No agreements found matching your search.
                    </td>
                  </tr>
                ) : (
                  filtered.map((agr) => (
                    <tr key={agr.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">
                          {agr.agreement_title || agr.agreementTitle || agr.title}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                          {agr.agreement_reference_number || agr.agreementReferenceNumber}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-medium text-slate-200">
                        {agr.partner_name || agr.partnerName || "Institutional Partner"}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                          {agr.agreement_type || agr.agreementType}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-slate-300">
                        <div>{agr.effective_start_date || agr.start_date}</div>
                        <div className="text-[11px] text-slate-500">
                          to {agr.effective_end_date || agr.expiry_date}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                            agr.is_expiring_soon || agr.status === "EXPIRING"
                              ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                              : agr.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {agr.is_expiring_soon ? "Expiring Soon" : agr.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setSelectedAgreementForAmendment(agr)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                        >
                          + Amendment
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create Agreement Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setShowAddModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                Record New Institutional Agreement / MoU
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Enter bilateral legal covenants and set automated renewal notification windows
              </p>

              <form onSubmit={handleCreateAgreement} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Partner Institution *</label>
                  <select
                    required
                    value={formData.partner_id}
                    onChange={(e) => setFormData({ ...formData, partner_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select foreign partner institution...</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.partner_name || p.name} ({p.country_name || p.country || p.country_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Agreement Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Student Mobility Agreement in Engineering Sciences"
                    value={formData.agreement_title}
                    onChange={(e) => setFormData({ ...formData, agreement_title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Agreement Type</label>
                    <select
                      value={formData.agreement_type}
                      onChange={(e) => setFormData({ ...formData, agreement_type: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="MOU">General MoU</option>
                      <option value="EXCHANGE_AGREEMENT">Student Exchange</option>
                      <option value="DUAL_DEGREE_ARTICULATION">Dual Degree Articulation</option>
                      <option value="RESEARCH_CONSORTIUM">Research Consortium</option>
                      <option value="LETTER_OF_INTENT">Letter of Intent</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Renewal Warning Days</label>
                    <input
                      type="number"
                      value={formData.renewal_warning_days}
                      onChange={(e) => setFormData({ ...formData, renewal_warning_days: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Effective Start Date *</label>
                    <input
                      required
                      type="date"
                      value={formData.effective_start_date}
                      onChange={(e) => setFormData({ ...formData, effective_start_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Effective End Date *</label>
                    <input
                      required
                      type="date"
                      value={formData.effective_end_date}
                      onChange={(e) => setFormData({ ...formData, effective_end_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Create Agreement"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Amendment Drawer */}
        {selectedAgreementForAmendment && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedAgreementForAmendment(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-cyan-400" />
                Add Agreement Amendment
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Attach an extension amendment or scope modification for:{" "}
                <span className="text-slate-200 font-semibold">
                  {selectedAgreementForAmendment.agreement_title || selectedAgreementForAmendment.title}
                </span>
              </p>

              <form onSubmit={handleAddAmendment} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Amendment Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Scope Extension: Adding Joint AI Research"
                    value={amendmentForm.title}
                    onChange={(e) => setAmendmentForm({ ...amendmentForm, title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Change Summary / Notes *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Detail the modified terms, added quota, or revised validity..."
                    value={amendmentForm.description}
                    onChange={(e) => setAmendmentForm({ ...amendmentForm, description: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    New Validity End Date (Optional Date Extension)
                  </label>
                  <input
                    type="date"
                    value={amendmentForm.new_effective_end_date}
                    onChange={(e) => setAmendmentForm({ ...amendmentForm, new_effective_end_date: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAgreementForAmendment(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingAmendment}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submittingAmendment ? "Saving..." : "Record Amendment"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
