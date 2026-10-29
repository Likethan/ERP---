"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Award,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  Filter,
  Plus,
  Search,
  ShieldCheck,
  TrendingUp,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityFundingRequest, MobilityScholarship } from "@/types/international";

export default function ScholarshipsPage() {
  const [scholarships, setScholarships] = useState<MobilityScholarship[]>([]);
  const [fundingRequests, setFundingRequests] = useState<MobilityFundingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedFundingForApproval, setSelectedFundingForApproval] = useState<MobilityFundingRequest | null>(null);

  // New Scholarship Form
  const [form, setForm] = useState({
    scholarship_name: "",
    funding_source: "Institutional Mobility Trust",
    award_amount_per_student: 2500,
    total_available_slots: 5,
    application_deadline: new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0],
    eligibility_criteria_notes: "CGPA >= 8.5 with approved semester exchange admission.",
  });
  const [submitting, setSubmitting] = useState(false);

  // Approval Form
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [approvedAmount, setApprovedAmount] = useState<number>(2500);
  const [financeRef, setFinanceRef] = useState("FIN-INTL-2026-");
  const [submittingApproval, setSubmittingApproval] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [schs, fnds] = await Promise.all([
        internationalService.getScholarships(),
        internationalService.getFundingRequests(),
      ]);
      setScholarships(schs);
      setFundingRequests(fnds);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateScholarship(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await internationalService.createScholarship(form);
      setScholarships([res, ...scholarships]);
      setShowCreateModal(false);
      alert("Mobility scholarship program created successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to create scholarship");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleApproveFunding(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFundingForApproval) return;
    setSubmittingApproval(true);
    try {
      await internationalService.approveFundingRequest(
        selectedFundingForApproval.id,
        decision,
        approvedAmount,
        financeRef
      );
      alert(`Funding request ${decision.toLowerCase()} and linked to finance ledger reference: ${financeRef}`);
      setSelectedFundingForApproval(null);
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to commit funding approval");
    } finally {
      setSubmittingApproval(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-400" />
              Mobility Scholarships & Travel Funding Coordination
            </h2>
            <p className="text-xs text-slate-400">
              Institutional endowment fellowships, partner travel grants, and unified finance ledger disbursements
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md shadow-amber-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Create Scholarship Program
          </button>
        </div>

        {/* Scholarships Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">
            Active Fellowship Programs
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scholarships.map((sch) => (
              <div
                key={sch.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-amber-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
                      {sch.scholarship_code || sch.scholarshipCode}
                    </span>
                    <span className="text-xs text-slate-400">
                      {sch.total_available_slots || sch.totalAvailableSlots} Award Slots
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-white mt-3">
                    {sch.scholarship_name || sch.title}
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Sponsor: {sch.funding_source || sch.sponsor_organization}
                  </p>

                  <div className="mt-3.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 space-y-1">
                    <span className="text-slate-500 font-semibold block text-[11px]">Criteria:</span>
                    <p>{sch.eligibility_criteria_notes || "General Merit"}</p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <div className="text-xs">
                    <span className="text-slate-500 block">Award Amount:</span>
                    <span className="font-bold text-emerald-400 text-sm">
                      ${(sch.award_amount_per_student || sch.award_amount || 2500).toLocaleString()} / Scholar
                    </span>
                  </div>
                  <span className="text-[11px] text-amber-400/90 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Deadline: {sch.application_deadline || sch.applicationDeadline}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Funding Requests Table */}
        <div className="space-y-3 pt-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">
            Student Travel Grant & Subsidy Requests
          </h3>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Student & Fellowship</th>
                    <th className="py-3 px-4">Requested Amount</th>
                    <th className="py-3 px-4">Approved Amount</th>
                    <th className="py-3 px-4">Finance Ledger Reference</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Committee Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {fundingRequests.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No funding requests recorded.
                      </td>
                    </tr>
                  ) : (
                    fundingRequests.map((req) => (
                      <tr key={req.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{req.student_name || "Student Applicant"}</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{req.scholarship_name || "General Aid"}</div>
                        </td>

                        <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                          ${req.requested_amount.toLocaleString()} {req.currency}
                        </td>

                        <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                          {req.approved_amount ? `$${req.approved_amount.toLocaleString()}` : "—"}
                        </td>

                        <td className="py-3.5 px-4 font-mono text-cyan-400 text-[11px]">
                          {req.finance_disbursement_ref || "Pending Ledger Link"}
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                              req.status === "APPROVED"
                                ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                                : req.status === "REJECTED"
                                ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                                : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            }`}
                          >
                            {req.status}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          {req.status === "REQUESTED" ? (
                            <button
                              onClick={() => {
                                setSelectedFundingForApproval(req);
                                setApprovedAmount(req.requested_amount);
                              }}
                              className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-sm transition-colors"
                            >
                              Disbursement Review
                            </button>
                          ) : (
                            <span className="text-slate-500 text-[11px]">Ledger Linked</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Approval Modal */}
        {selectedFundingForApproval && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedFundingForApproval(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-emerald-400" />
                Approve Mobility Travel Grant Disbursement
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Scholar: <strong className="text-slate-200">{selectedFundingForApproval.student_name}</strong> · Requested:{" "}
                <strong className="text-emerald-400">${selectedFundingForApproval.requested_amount}</strong>
              </p>

              <form onSubmit={handleApproveFunding} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Decision *</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setDecision("APPROVED")}
                      className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                        decision === "APPROVED"
                          ? "bg-emerald-600 border-emerald-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      APPROVE GRANT
                    </button>
                    <button
                      type="button"
                      onClick={() => setDecision("REJECTED")}
                      className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                        decision === "REJECTED"
                          ? "bg-rose-600 border-rose-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      DECLINE FUNDING
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Approved Grant Amount ($ USD) *</label>
                  <input
                    required
                    type="number"
                    value={approvedAmount}
                    onChange={(e) => setApprovedAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Finance Disbursement Reference Code *
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. FIN-INTL-2026-9921"
                    value={financeRef}
                    onChange={(e) => setFinanceRef(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedFundingForApproval(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingApproval}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submittingApproval ? "Saving..." : "Commit Disbursement"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Create Scholarship Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowCreateModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Award className="h-4 w-4 text-amber-400" />
                Create Mobility Scholarship Program
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Establish an institutional travel subsidy or bilateral grant track for international scholars
              </p>

              <form onSubmit={handleCreateScholarship} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Scholarship Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. CampusOS Global Excellence Travel Fellowship"
                    value={form.scholarship_name}
                    onChange={(e) => setForm({ ...form, scholarship_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Funding Sponsor *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Institutional Endowment"
                      value={form.funding_source}
                      onChange={(e) => setForm({ ...form, funding_source: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Grant Per Student ($ USD) *</label>
                    <input
                      required
                      type="number"
                      value={form.award_amount_per_student}
                      onChange={(e) => setForm({ ...form, award_amount_per_student: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Total Available Slots *</label>
                    <input
                      required
                      type="number"
                      value={form.total_available_slots}
                      onChange={(e) => setForm({ ...form, total_available_slots: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Application Deadline *</label>
                    <input
                      required
                      type="date"
                      value={form.application_deadline}
                      onChange={(e) => setForm({ ...form, application_deadline: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Eligibility Criteria Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Specify merit thresholds, minimum GPA, or target countries..."
                    value={form.eligibility_criteria_notes}
                    onChange={(e) => setForm({ ...form, eligibility_criteria_notes: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md shadow-amber-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Publishing..." : "Publish Scholarship"}
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
