"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  Calendar,
  CheckCircle2,
  FileCheck2,
  FileText,
  Filter,
  Plus,
  Scale,
  Search,
  ShieldAlert,
  ShieldCheck,
  User,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import {
  CourseEquivalencyMapping,
  CreditTransferRequest,
  InternationalPartner,
} from "@/types/international";

export default function CreditTransferPage() {
  const [equivalencies, setEquivalencies] = useState<CourseEquivalencyMapping[]>([]);
  const [transfers, setTransfers] = useState<CreditTransferRequest[]>([]);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"TRANSFERS" | "MAPPINGS">("TRANSFERS");

  // Approval Modal State
  const [selectedTransferForApproval, setSelectedTransferForApproval] = useState<CreditTransferRequest | null>(null);
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [committeeNotes, setCommitteeNotes] = useState("");
  const [councilRef, setCouncilRef] = useState("AC-2026-RES-");
  const [submittingApproval, setSubmittingApproval] = useState(false);

  // New Equivalency Modal State
  const [showEquivalencyModal, setShowEquivalencyModal] = useState(false);
  const [eqForm, setEqForm] = useState({
    partner_id: "",
    host_course_code: "",
    host_course_title: "",
    host_credits: 6,
    target_course_code: "",
    target_course_title: "",
    target_credits: 4,
    department_id: "dept-cse",
    evaluation_notes: "",
  });
  const [submittingEq, setSubmittingEq] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [eqs, cts, pts] = await Promise.all([
        internationalService.getCourseEquivalencies(),
        internationalService.getCreditTransfers(),
        internationalService.getPartners(),
      ]);
      setEquivalencies(eqs);
      setTransfers(cts);
      setPartners(pts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleApproveTransfer(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTransferForApproval) return;
    setSubmittingApproval(true);
    try {
      await internationalService.approveCreditTransfer(
        selectedTransferForApproval.id,
        decision,
        committeeNotes,
        councilRef
      );
      alert(`Credit transfer request has been ${decision.toLowerCase()} by Academic Council.`);
      setSelectedTransferForApproval(null);
      setCommitteeNotes("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to submit decision");
    } finally {
      setSubmittingApproval(false);
    }
  }

  async function handleCreateEquivalency(e: React.FormEvent) {
    e.preventDefault();
    setSubmittingEq(true);
    try {
      const partner = partners.find((p) => p.id === eqForm.partner_id);
      const res = await internationalService.createCourseEquivalency({
        ...eqForm,
        partner_name: partner?.partner_name || partner?.name || "Partner",
      });
      setEquivalencies([res, ...equivalencies]);
      setShowEquivalencyModal(false);
      alert("Course equivalency proposed successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to create equivalency");
    } finally {
      setSubmittingEq(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Scale className="h-5 w-5 text-purple-400" />
              Academic Credit Transfer & Course Equivalency Governance
            </h2>
            <p className="text-xs text-slate-400">
              Strictly non-automated, committee-governed academic credit recognition with formal Academic Council resolutions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowEquivalencyModal(true)}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-all"
            >
              <Plus className="h-4 w-4" />
              Propose Course Equivalency
            </button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("TRANSFERS")}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors flex items-center gap-2 ${
              activeTab === "TRANSFERS"
                ? "bg-purple-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Credit Transfer Reviews ({transfers.length})
          </button>
          <button
            onClick={() => setActiveTab("MAPPINGS")}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors flex items-center gap-2 ${
              activeTab === "MAPPINGS"
                ? "bg-purple-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <BookOpen className="h-4 w-4" />
            Pre-Approved Course Equivalencies ({equivalencies.length})
          </button>
        </div>

        {/* Tab 1: Credit Transfers */}
        {activeTab === "TRANSFERS" && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Student & Application</th>
                    <th className="py-3 px-4">Host Institution</th>
                    <th className="py-3 px-4">Host Credits Earned</th>
                    <th className="py-3 px-4">Target Campus Credits</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Committee Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        Loading credit transfer dossiers...
                      </td>
                    </tr>
                  ) : transfers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No credit transfer dossiers pending committee review.
                      </td>
                    </tr>
                  ) : (
                    transfers.map((ct) => (
                      <tr key={ct.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{ct.student_name || "Scholar"}</div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">App: {ct.application_id}</div>
                        </td>

                        <td className="py-3.5 px-4 font-medium text-slate-200">{ct.host_institution_name}</td>

                        <td className="py-3.5 px-4">
                          <span className="font-mono font-semibold text-slate-200">{ct.host_credits_earned} ECTS/Credits</span>
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-mono font-bold text-cyan-400">{ct.target_campus_credits} Credits</span>
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                              ct.status === "APPROVED"
                                ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                                : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            }`}
                          >
                            {ct.status}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => setSelectedTransferForApproval(ct)}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                          >
                            Committee Review &rarr;
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Course Equivalency Mappings */}
        {activeTab === "MAPPINGS" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {equivalencies.map((eq) => (
              <div
                key={eq.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {eq.status}
                    </span>
                    <span className="text-xs text-slate-400">{eq.department_id}</span>
                  </div>

                  <div className="mt-3 space-y-2">
                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block uppercase font-bold">Host University Course</span>
                      <div className="text-xs font-bold text-slate-200 mt-0.5">
                        {eq.host_course_code}: {eq.host_course_title}
                      </div>
                      <span className="text-[11px] text-cyan-400 font-mono mt-0.5 block">{eq.host_credits} Host Credits</span>
                    </div>

                    <div className="text-center text-slate-500 text-xs font-bold">↕ Maps to Equivalent</div>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block uppercase font-bold">Target Campus Course</span>
                      <div className="text-xs font-bold text-slate-200 mt-0.5">
                        {eq.target_course_code}: {eq.target_course_title}
                      </div>
                      <span className="text-[11px] text-emerald-400 font-mono mt-0.5 block">{eq.target_credits} Internal Credits</span>
                    </div>
                  </div>

                  {eq.evaluation_notes && (
                    <p className="mt-3 text-[11px] text-slate-400 italic">&quot;{eq.evaluation_notes}&quot;</p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
                  <span>Evaluator: {eq.evaluator_name || "Faculty Member"}</span>
                  <span className="text-emerald-400 font-medium">UGC Verified</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Credit Transfer Approval Modal */}
        {selectedTransferForApproval && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedTransferForApproval(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-purple-400" />
                Academic Council Credit Recognition Review
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Candidate: <strong className="text-slate-200">{selectedTransferForApproval.student_name}</strong> ·{" "}
                {selectedTransferForApproval.host_institution_name}
              </p>

              <form onSubmit={handleApproveTransfer} className="mt-5 space-y-4">
                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-500 block">Host Credits Earned</span>
                    <span className="font-bold text-slate-200 text-sm mt-0.5 block">
                      {selectedTransferForApproval.host_credits_earned} ECTS
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 block">Target Credits to Recognize</span>
                    <span className="font-bold text-cyan-400 text-sm mt-0.5 block">
                      {selectedTransferForApproval.target_campus_credits} Credits
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Committee Decision *</label>
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
                      APPROVE CREDIT RECOGNITION
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
                      REJECT / INSUFFICIENT PARITY
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Academic Council Approval Resolution Reference *
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. AC-2026-RES-991"
                    value={councilRef}
                    onChange={(e) => setCouncilRef(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Committee Review Notes & Grade Parity Justification *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Document transcript authenticity verification, syllabus match percentage, and council minutes..."
                    value={committeeNotes}
                    onChange={(e) => setCommitteeNotes(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedTransferForApproval(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingApproval}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-900/30 disabled:opacity-50"
                  >
                    {submittingApproval ? "Recording..." : "Commit Council Approval"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Propose Equivalency Modal */}
        {showEquivalencyModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowEquivalencyModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-cyan-400" />
                Propose New Course Equivalency Mapping
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Map an external foreign university course syllabus to an internal curriculum subject code
              </p>

              <form onSubmit={handleCreateEquivalency} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Foreign Partner Institution *</label>
                  <select
                    required
                    value={eqForm.partner_id}
                    onChange={(e) => setEqForm({ ...eqForm, partner_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select partner university...</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.partner_name || p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Host Course Code *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. IN2106"
                      value={eqForm.host_course_code}
                      onChange={(e) => setEqForm({ ...eqForm, host_course_code: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Host Credits *</label>
                    <input
                      required
                      type="number"
                      value={eqForm.host_credits}
                      onChange={(e) => setEqForm({ ...eqForm, host_credits: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Host Course Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Advanced Computer Architecture"
                    value={eqForm.host_course_title}
                    onChange={(e) => setEqForm({ ...eqForm, host_course_title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Campus Subject Code *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. CS401"
                      value={eqForm.target_course_code}
                      onChange={(e) => setEqForm({ ...eqForm, target_course_code: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Campus Recognized Credits *</label>
                    <input
                      required
                      type="number"
                      value={eqForm.target_credits}
                      onChange={(e) => setEqForm({ ...eqForm, target_credits: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Campus Subject Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Advanced Computer Architecture"
                    value={eqForm.target_course_title}
                    onChange={(e) => setEqForm({ ...eqForm, target_course_title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Syllabus Evaluation Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Document topics overlapping and practical lab components alignment..."
                    value={eqForm.evaluation_notes}
                    onChange={(e) => setEqForm({ ...eqForm, evaluation_notes: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowEquivalencyModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingEq}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submittingEq ? "Proposing..." : "Propose Equivalency"}
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
