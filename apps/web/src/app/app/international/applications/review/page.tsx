"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  FileText,
  Filter,
  Globe,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  User,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityApplication } from "@/types/international";

export default function ApplicationReviewWorkspacePage() {
  const [applications, setApplications] = useState<MobilityApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStage, setFilterStage] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [selectedApp, setSelectedApp] = useState<MobilityApplication | null>(null);

  // Review Decision State
  const [reviewAction, setReviewAction] = useState<"APPROVE" | "REJECT" | "RETURN" | "ESCALATE">("APPROVE");
  const [comments, setComments] = useState("");
  const [reasons, setReasons] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [filterStage]);

  async function loadData() {
    setLoading(true);
    try {
      const data = await internationalService.getApplications({
        department_pending: filterStage === "DEPT",
        intl_office_pending: filterStage === "INTL",
      });
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedApp) return;
    setSubmitting(true);
    try {
      await internationalService.reviewApplication(selectedApp.id, reviewAction, comments, reasons);
      alert(`Decision recorded successfully: ${reviewAction}`);
      setSelectedApp(null);
      setComments("");
      setReasons("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = applications.filter((app) => {
    const text = `${app.student_name || ""} ${app.program_title || ""} ${app.application_reference_number || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              Application Review & Endorsement Workspace
            </h2>
            <p className="text-xs text-slate-400">
              Department Coordinators, HODs, and International Office multi-stage approval queue
            </p>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative flex-1 w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search candidate by name, application ID, or partner university..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => setFilterStage("ALL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStage === "ALL" ? "bg-cyan-600 text-white" : "bg-slate-950 text-slate-400 hover:text-slate-200"
              }`}
            >
              All Stages
            </button>
            <button
              onClick={() => setFilterStage("DEPT")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStage === "DEPT" ? "bg-cyan-600 text-white" : "bg-slate-950 text-slate-400 hover:text-slate-200"
              }`}
            >
              Dept Queue
            </button>
            <button
              onClick={() => setFilterStage("INTL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStage === "INTL" ? "bg-cyan-600 text-white" : "bg-slate-950 text-slate-400 hover:text-slate-200"
              }`}
            >
              Intl Office Queue
            </button>
          </div>
        </div>

        {/* Applications List */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading review queue...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No mobility applications awaiting review in this stage.
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((app) => (
              <div
                key={app.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                      {app.application_reference_number || app.applicationReferenceNumber}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 uppercase">
                      {app.status}
                    </span>
                    {!app.eligibility_check_passed && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        Prerequisites Flagged
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-bold text-white">
                    {app.student_name || app.studentName || "Candidate Student"}{" "}
                    <span className="text-xs font-normal text-slate-400">
                      (Roll: {app.student_roll_number || "2023CSE014"})
                    </span>
                  </h3>

                  <p className="text-xs text-slate-300 flex items-center gap-2">
                    <Compass className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span>{app.program_title || app.programTitle}</span>
                    <span className="text-slate-500">·</span>
                    <span className="text-slate-400">{app.partner_name || app.partnerName}</span>
                  </p>

                  <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                    <span>CGPA: <strong className="text-slate-200">{app.student_cgpa_at_application || "8.8"}</strong></span>
                    <span>Credits: <strong className="text-slate-200">{app.credits_completed_at_application || "56"}</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                  <button
                    onClick={() => {
                      setSelectedApp(app);
                      setReviewAction("APPROVE");
                    }}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 flex items-center gap-1.5 transition-colors"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Endorse / Approve
                  </button>
                  <button
                    onClick={() => {
                      setSelectedApp(app);
                      setReviewAction("REJECT");
                    }}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-rose-950 hover:text-rose-300 text-slate-300 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
                  >
                    <XCircle className="h-4 w-4" />
                    Reject / Return
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Review Action Modal */}
        {selectedApp && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedApp(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Record Formal Application Review Decision
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Candidate: <span className="font-semibold text-slate-200">{selectedApp.student_name || "Student"}</span> · Ref:{" "}
                <span className="font-mono text-cyan-400">{selectedApp.application_reference_number}</span>
              </p>

              <form onSubmit={handleSubmitReview} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Decision Action *</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {(["APPROVE", "REJECT", "RETURN", "ESCALATE"] as const).map((act) => (
                      <button
                        type="button"
                        key={act}
                        onClick={() => setReviewAction(act)}
                        className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-all ${
                          reviewAction === act
                            ? act === "APPROVE"
                              ? "bg-emerald-600 border-emerald-500 text-white"
                              : act === "REJECT"
                              ? "bg-rose-600 border-rose-500 text-white"
                              : act === "RETURN"
                              ? "bg-amber-600 border-amber-500 text-white"
                              : "bg-purple-600 border-purple-500 text-white"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        {act}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Review Committee Comments / Endorsement Notes *
                  </label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Enter academic committee endorsement justification or specific feedback..."
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                {reviewAction !== "APPROVE" && (
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">
                      Reason for Rejection / Return / Conditions
                    </label>
                    <input
                      type="text"
                      placeholder="Specify reasons or required documents to re-submit..."
                      value={reasons}
                      onChange={(e) => setReasons(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                )}

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedApp(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Recording Decision..." : "Commit Decision"}
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
