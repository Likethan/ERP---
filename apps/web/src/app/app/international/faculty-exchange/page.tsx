"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Globe,
  Plus,
  Search,
  ShieldCheck,
  User,
  UserCheck,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { FacultyMobilityDirection, FacultyMobilityRecord, InternationalPartner } from "@/types/international";

export default function FacultyExchangePage() {
  const [records, setRecords] = useState<FacultyMobilityRecord[]>([]);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [directionFilter, setDirectionFilter] = useState("ALL");
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedRecordForApproval, setSelectedRecordForApproval] = useState<FacultyMobilityRecord | null>(null);

  // New Faculty Mobility Form
  const [form, setForm] = useState({
    partner_id: "",
    mobility_type: "OUTBOUND" as FacultyMobilityDirection,
    visit_start_date: new Date().toISOString().split("T")[0],
    visit_end_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    purpose_summary: "",
    academic_visit_plan: "",
  });
  const [submitting, setSubmitting] = useState(false);

  // Approval Form
  const [approvalLevel, setApprovalLevel] = useState<"HOD" | "VP">("HOD");
  const [approvalDecision, setApprovalDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [approvalComments, setApprovalComments] = useState("");
  const [submittingApproval, setSubmittingApproval] = useState(false);

  useEffect(() => {
    loadData();
  }, [directionFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const [recs, pts] = await Promise.all([
        internationalService.getFacultyMobilities({
          direction: directionFilter !== "ALL" ? directionFilter : undefined,
        }),
        internationalService.getPartners(),
      ]);
      setRecords(recs);
      setPartners(pts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const partner = partners.find((p) => p.id === form.partner_id);
      const res = await internationalService.createFacultyMobility({
        ...form,
        partner_name: partner?.partner_name || partner?.name || "Partner Institution",
        faculty_name: "Prof. Current Faculty",
      });
      setRecords([res, ...records]);
      setShowAddModal(false);
      alert("Faculty mobility proposal submitted for HOD review.");
    } catch (err) {
      console.error(err);
      alert("Failed to create proposal");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleApproval(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedRecordForApproval) return;
    setSubmittingApproval(true);
    try {
      await internationalService.approveFacultyMobility(
        selectedRecordForApproval.id,
        approvalLevel,
        approvalDecision,
        approvalComments
      );
      alert(`Faculty mobility proposal ${approvalDecision.toLowerCase()} by ${approvalLevel}.`);
      setSelectedRecordForApproval(null);
      setApprovalComments("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to submit approval");
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
              <UserCheck className="h-5 w-5 text-cyan-400" />
              Faculty Mobility & Visiting Scholars
            </h2>
            <p className="text-xs text-slate-400">
              Institutional endorsements, visiting professorships, and outbound academic fellowships requiring HOD & Vice Principal approval
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Propose Faculty Mobility
          </button>
        </div>

        {/* Direction Filter */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDirectionFilter("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              directionFilter === "ALL" ? "bg-cyan-600 text-white" : "bg-slate-900 text-slate-400 border border-slate-800"
            }`}
          >
            All Fellowships
          </button>
          <button
            onClick={() => setDirectionFilter("OUTBOUND")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              directionFilter === "OUTBOUND" ? "bg-cyan-600 text-white" : "bg-slate-900 text-slate-400 border border-slate-800"
            }`}
          >
            Outbound Faculty
          </button>
          <button
            onClick={() => setDirectionFilter("INBOUND")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              directionFilter === "INBOUND" ? "bg-cyan-600 text-white" : "bg-slate-900 text-slate-400 border border-slate-800"
            }`}
          >
            Inbound Visiting Professors
          </button>
        </div>

        {/* Records Grid */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading faculty mobility dossiers...</div>
        ) : records.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No faculty mobility records found for this category.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {records.map((rec) => (
              <div
                key={rec.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        (rec.mobility_type || rec.mobilityType) === "OUTBOUND"
                          ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                          : "bg-purple-500/10 text-purple-300 border border-purple-500/20"
                      }`}
                    >
                      {rec.mobility_type || rec.mobilityType} Mobility
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        rec.status === "APPROVED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                      }`}
                    >
                      {rec.status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mt-3">{rec.faculty_name || "Faculty Scholar"}</h3>

                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <Globe className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span>{rec.partner_name || "Partner University"}</span>
                  </p>

                  <div className="mt-3.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 space-y-1">
                    <span className="text-slate-500 font-semibold block text-[11px]">Academic Visit Purpose:</span>
                    <p className="line-clamp-2">{rec.purpose_summary}</p>
                  </div>

                  <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
                    <span>Period:</span>
                    <span className="text-slate-300 font-mono text-[11px]">
                      {rec.visit_start_date} to {rec.visit_end_date}
                    </span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500">Dual HOD & VP Endorsement</span>
                  <button
                    onClick={() => {
                      setSelectedRecordForApproval(rec);
                      setApprovalLevel("HOD");
                    }}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                  >
                    Review Proposal
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Approval Modal */}
        {selectedRecordForApproval && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedRecordForApproval(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Faculty Mobility Endorsement
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Candidate: <strong className="text-slate-200">{selectedRecordForApproval.faculty_name}</strong> · Partner:{" "}
                <strong className="text-slate-200">{selectedRecordForApproval.partner_name}</strong>
              </p>

              <form onSubmit={handleApproval} className="mt-5 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Approval Authority Level</label>
                    <select
                      value={approvalLevel}
                      onChange={(e) => setApprovalLevel(e.target.value as "HOD" | "VP")}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="HOD">Head of Department (HOD)</option>
                      <option value="VP">Vice Principal (Academic Affairs)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Decision</label>
                    <select
                      value={approvalDecision}
                      onChange={(e) => setApprovalDecision(e.target.value as "APPROVED" | "REJECTED")}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="APPROVED">Endorse & Approve</option>
                      <option value="REJECTED">Decline Proposal</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Academic Endorsement Comments *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Enter endorsement justification or special provisions..."
                    value={approvalComments}
                    onChange={(e) => setApprovalComments(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedRecordForApproval(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingApproval}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submittingApproval ? "Saving..." : "Commit Endorsement"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Propose Mobility Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowAddModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Compass className="h-4 w-4 text-cyan-400" />
                Propose Faculty Mobility / Academic Fellowship
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Initiate formal institutional proposal for outbound teaching or international research fellowship
              </p>

              <form onSubmit={handleCreate} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Host Partner University *</label>
                  <select
                    required
                    value={form.partner_id}
                    onChange={(e) => setForm({ ...form, partner_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select partner institution...</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.partner_name || p.name} ({p.country_name || p.country || p.country_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Mobility Direction</label>
                    <select
                      value={form.mobility_type}
                      onChange={(e) => setForm({ ...form, mobility_type: e.target.value as FacultyMobilityDirection })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="OUTBOUND">Outbound Faculty Member</option>
                      <option value="INBOUND">Inbound Visiting Scholar</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Visit Start Date *</label>
                    <input
                      required
                      type="date"
                      value={form.visit_start_date}
                      onChange={(e) => setForm({ ...form, visit_start_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Visit End Date *</label>
                    <input
                      required
                      type="date"
                      value={form.visit_end_date}
                      onChange={(e) => setForm({ ...form, visit_end_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Academic Purpose Summary *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Briefly state the research or curriculum objective..."
                    value={form.purpose_summary}
                    onChange={(e) => setForm({ ...form, purpose_summary: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
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
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Submitting..." : "Submit Proposal"}
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
