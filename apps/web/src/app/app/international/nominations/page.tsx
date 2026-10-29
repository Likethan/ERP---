"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  CheckSquare,
  Clock,
  Compass,
  FileText,
  Globe,
  Mail,
  Send,
  ShieldCheck,
  User,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityApplication } from "@/types/international";

export default function PartnerNominationsPage() {
  const [applications, setApplications] = useState<MobilityApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAppForNomination, setSelectedAppForNomination] = useState<MobilityApplication | null>(null);
  const [selectedAppForDecision, setSelectedAppForDecision] = useState<MobilityApplication | null>(null);

  // Nomination Form
  const [nominationNotes, setNominationNotes] = useState("");
  const [partnerEmail, setPartnerEmail] = useState("");
  const [submittingNomination, setSubmittingNomination] = useState(false);

  // Decision Form
  const [decision, setDecision] = useState<"ACCEPTED" | "REJECTED">("ACCEPTED");
  const [decisionNotes, setDecisionNotes] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const data = await internationalService.getApplications();
      // Show applications that are approved, nominated, or decided
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleNominate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAppForNomination) return;
    setSubmittingNomination(true);
    try {
      await internationalService.nominateStudent(selectedAppForNomination.id, nominationNotes, partnerEmail);
      alert("Candidate successfully nominated to host university!");
      setSelectedAppForNomination(null);
      setNominationNotes("");
      setPartnerEmail("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to record nomination");
    } finally {
      setSubmittingNomination(false);
    }
  }

  async function handleDecision(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAppForDecision) return;
    setSubmittingDecision(true);
    try {
      await internationalService.recordPartnerDecision(selectedAppForDecision.id, decision, decisionNotes);
      alert(`Partner decision recorded: ${decision}`);
      setSelectedAppForDecision(null);
      setDecisionNotes("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to record decision");
    } finally {
      setSubmittingDecision(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <CheckSquare className="h-5 w-5 text-purple-400" />
            Partner Nominations & Acceptance Coordination
          </h2>
          <p className="text-xs text-slate-400">
            Transmit approved student rosters to host university international offices and log admissions
          </p>
        </div>

        {/* Nominations Table */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Candidate & Ref</th>
                  <th className="py-3 px-4">Host Partner University</th>
                  <th className="py-3 px-4">Program</th>
                  <th className="py-3 px-4">Nomination Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      Loading nomination pipeline...
                    </td>
                  </tr>
                ) : applications.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No applications currently in nomination stage.
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">
                          {app.student_name || app.studentName || "Student Candidate"}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                          {app.application_reference_number || app.applicationReferenceNumber}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-medium text-slate-200">
                        {app.partner_name || app.partnerName}
                      </td>

                      <td className="py-3.5 px-4 text-slate-300">
                        {app.program_title || app.programTitle}
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                            app.status === "PARTNER_ACCEPTED" || app.status === "ACTIVE_MOBILITY"
                              ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                              : app.status === "PARTNER_NOMINATED"
                              ? "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                              : app.status === "PARTNER_REJECTED"
                              ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                              : "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right space-x-2">
                        {app.status === "APPROVED" && (
                          <button
                            onClick={() => setSelectedAppForNomination(app)}
                            className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-sm transition-colors"
                          >
                            Nominate to Partner
                          </button>
                        )}
                        {app.status === "PARTNER_NOMINATED" && (
                          <button
                            onClick={() => setSelectedAppForDecision(app)}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                          >
                            Record Decision
                          </button>
                        )}
                        {app.status !== "APPROVED" && app.status !== "PARTNER_NOMINATED" && (
                          <span className="text-slate-500 text-[11px]">Finalized</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Nominate Student Modal */}
        {selectedAppForNomination && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedAppForNomination(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Send className="h-4 w-4 text-purple-400" />
                Nominate Candidate to Host Institution
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Candidate: <strong className="text-slate-200">{selectedAppForNomination.student_name}</strong> to{" "}
                <strong className="text-slate-200">{selectedAppForNomination.partner_name}</strong>
              </p>

              <form onSubmit={handleNominate} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Host University Coordinator Contact Email
                  </label>
                  <input
                    type="email"
                    placeholder="incoming.exchange@partner.edu"
                    value={partnerEmail}
                    onChange={(e) => setPartnerEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Official Nomination Dossier Notes</label>
                  <textarea
                    rows={3}
                    placeholder="Provide candidate ranking, scholarship recommendation, or host course approvals..."
                    value={nominationNotes}
                    onChange={(e) => setNominationNotes(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAppForNomination(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingNomination}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-900/30 disabled:opacity-50"
                  >
                    {submittingNomination ? "Submitting..." : "Send Formal Nomination"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Record Decision Modal */}
        {selectedAppForDecision && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedAppForDecision(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Record Host University Admission Decision
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Candidate: <strong className="text-slate-200">{selectedAppForDecision.student_name}</strong>
              </p>

              <form onSubmit={handleDecision} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Partner Decision *</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setDecision("ACCEPTED")}
                      className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                        decision === "ACCEPTED"
                          ? "bg-emerald-600 border-emerald-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      ACCEPTED (Offer Letter Issued)
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
                      REJECTED
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Official Notes / Reference Code</label>
                  <textarea
                    rows={3}
                    placeholder="Enter partner reference number, admission package details, or rejection rationale..."
                    value={decisionNotes}
                    onChange={(e) => setDecisionNotes(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAppForDecision(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingDecision}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submittingDecision ? "Saving..." : "Commit Partner Decision"}
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
