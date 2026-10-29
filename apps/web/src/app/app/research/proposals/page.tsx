"use client";

import React, { useEffect, useState } from "react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { validateProposalSubmissionReadiness } from "@/services/research-calculator";
import { ResearchGrantApplication } from "@/types/research";
import {
  FileEdit,
  Search,
  CheckCircle2,
  AlertTriangle,
  Send,
  Award,
  Clock,
  Plus,
  RefreshCw,
  ExternalLink,
  DollarSign,
  UserCheck,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

export default function ProposalsLifecyclePage() {
  const [applications, setApplications] = useState<ResearchGrantApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [internalFilter, setInternalFilter] = useState("ALL");
  const [externalFilter, setExternalFilter] = useState("ALL");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Sponsor Decision Modal
  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
  const [selectedApp, setSelectedApp] = useState<ResearchGrantApplication | null>(null);
  const [decisionForm, setDecisionForm] = useState({
    decision: "AWARDED",
    award_number: `AWD-GRNT-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    award_amount: 180000,
    decision_notes: "Sponsor review score: Category 1 (Meritorious for Full Funding).",
    sponsor_feedback: "Exemplary experimental methodology and strong interdisciplinary investigator team.",
    award_letter_url: "https://docs.campusos.edu/awards/grant-sanction-letter.pdf",
    create_award_record: true,
  });

  // External Submission Modal
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState({
    external_submission_reference: `SUB-AGENCY-${Math.floor(10000 + Math.random() * 90000)}`,
    portal_url: "https://research.gov/portal",
  });

  const loadProposals = async () => {
    setLoading(true);
    try {
      const data = await ResearchService.getGrantApplications({
        internal_status: internalFilter !== "ALL" ? internalFilter : undefined,
        external_status: externalFilter !== "ALL" ? externalFilter : undefined,
      });
      setApplications(data);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to load proposals." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProposals();
  }, [internalFilter, externalFilter]);

  const handleReviewDecision = async (appId: string, decision: string) => {
    const comments = prompt("Enter formal review decision comments for audit ledger:");
    if (!comments) return;
    try {
      await ResearchService.reviewGrantApplication(appId, decision, comments);
      setFeedback({ type: "success", message: `Application recorded as ${decision}.` });
      loadProposals();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Review action failed." });
    }
  };

  const handleOpenSubmit = (app: ResearchGrantApplication) => {
    const readiness = validateProposalSubmissionReadiness(app);
    if (!readiness.ready) {
      setFeedback({
        type: "error",
        message: `Submission blocked: ${readiness.blockers.join(" ")}`,
      });
      return;
    }
    setSelectedApp(app);
    setIsSubmitModalOpen(true);
  };

  const handleConfirmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApp) return;
    try {
      await ResearchService.confirmExternalSubmission(selectedApp.id, submitForm);
      setFeedback({
        type: "success",
        message: `Submission to external sponsor agency confirmed with reference '${submitForm.external_submission_reference}'.`,
      });
      setIsSubmitModalOpen(false);
      loadProposals();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "External submission confirmation failed." });
    }
  };

  const handleOpenDecision = (app: ResearchGrantApplication) => {
    setSelectedApp(app);
    setDecisionForm({
      ...decisionForm,
      award_amount: app.proposed_budget || 180000,
    });
    setIsDecisionModalOpen(true);
  };

  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApp) return;
    try {
      await ResearchService.recordSponsorDecision(selectedApp.id, {
        decision: decisionForm.decision,
        award_number: decisionForm.award_number,
        award_amount: Number(decisionForm.award_amount),
        decision_notes: decisionForm.decision_notes,
        sponsor_feedback: decisionForm.sponsor_feedback,
        award_letter_url: decisionForm.award_letter_url,
        create_award_record: decisionForm.create_award_record,
      });
      setFeedback({
        type: "success",
        message: `Verified sponsor decision '${decisionForm.decision}' recorded. Authoritative award synchronized.`,
      });
      setIsDecisionModalOpen(false);
      loadProposals();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Recording sponsor decision failed." });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Page Title & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileEdit className="h-6 w-6 text-emerald-400" />
              Grant Proposal Lifecycle & Institutional Approval Chain
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Multi-round internal institutional review, separation of duties, external sponsor dispatch, and verified awards.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadProposals}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-4 rounded-xl border text-sm flex items-center justify-between ${
              feedback.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="text-xs underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by proposal title or application code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Internal Review:</span>
              <select
                value={internalFilter}
                onChange={(e) => setInternalFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Internal</option>
                <option value="DRAFT">Draft</option>
                <option value="SUBMITTED_INTERNAL">Submitted Internal</option>
                <option value="INSTITUTIONALLY_APPROVED">Institutionally Approved</option>
                <option value="REJECTED_INTERNAL">Rejected</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Sponsor Outcome:</span>
              <select
                value={externalFilter}
                onChange={(e) => setExternalFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Sponsor Statuses</option>
                <option value="NOT_SUBMITTED">Not Submitted</option>
                <option value="SUBMITTED_EXTERNAL">Submitted External</option>
                <option value="AWARDED">Awarded</option>
                <option value="REJECTED_EXTERNAL">Declined</option>
              </select>
            </div>
          </div>
        </div>

        {/* Proposals List */}
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="h-8 w-8 animate-spin text-emerald-400 mx-auto" />
            <p className="text-sm text-slate-400">Loading grant proposals...</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 space-y-3">
            <FileEdit className="h-12 w-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-semibold text-white">No grant proposals in pipeline</h3>
            <p className="text-xs text-slate-400">Create a proposal draft linked to an institutional research project.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {applications.map((app) => (
              <div
                key={app.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                      {app.application_code}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                        app.internal_review_status === "INSTITUTIONALLY_APPROVED"
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      Internal: {app.internal_review_status}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                        app.external_submission_status === "AWARDED"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : app.external_submission_status === "SUBMITTED_EXTERNAL"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-slate-800 text-slate-500 border-slate-700"
                      }`}
                    >
                      Sponsor: {app.external_submission_status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white">{app.title}</h3>
                  <p className="text-xs text-slate-400 line-clamp-2">{app.research_proposal_summary}</p>

                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>
                      Requested:{" "}
                      <strong className="text-emerald-400 font-mono">
                        {app.currency} {Number(app.proposed_budget).toLocaleString()}
                      </strong>
                    </span>
                    {app.external_reference_number && (
                      <span>
                        Sponsor Ref: <strong className="font-mono text-slate-300">{app.external_reference_number}</strong>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* Step 1: Internal Review */}
                  {app.internal_review_status !== "INSTITUTIONALLY_APPROVED" && (
                    <button
                      onClick={() => handleReviewDecision(app.id, "INSTITUTIONALLY_APPROVED")}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-sm"
                    >
                      Institutional Approval
                    </button>
                  )}

                  {/* Step 2: Confirm External Submission */}
                  {app.internal_review_status === "INSTITUTIONALLY_APPROVED" &&
                    app.external_submission_status === "NOT_SUBMITTED" && (
                      <button
                        onClick={() => handleOpenSubmit(app)}
                        className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white shadow-sm flex items-center gap-1.5"
                      >
                        <Send className="h-3.5 w-3.5" />
                        Confirm Submission
                      </button>
                    )}

                  {/* Step 3: Record Verified Sponsor Decision */}
                  {["SUBMITTED_EXTERNAL", "UNDER_EXTERNAL_REVIEW"].includes(
                    app.external_submission_status
                  ) && (
                    <button
                      onClick={() => handleOpenDecision(app)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm flex items-center gap-1.5"
                    >
                      <Award className="h-3.5 w-3.5" />
                      Record Sponsor Decision
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* External Submission Modal */}
      {isSubmitModalOpen && selectedApp && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Send className="h-5 w-5 text-amber-400" />
              Confirm External Grant Submission
            </h3>
            <p className="text-xs text-slate-400">
              Only institutionally approved proposals may be confirmed for external dispatch to sponsor portals.
            </p>

            <form onSubmit={handleConfirmSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Agency Submission Reference / ID</label>
                <input
                  type="text"
                  value={submitForm.external_submission_reference}
                  onChange={(e) =>
                    setSubmitForm({ ...submitForm, external_submission_reference: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Submission Portal URL</label>
                <input
                  type="url"
                  value={submitForm.portal_url}
                  onChange={(e) => setSubmitForm({ ...submitForm, portal_url: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsSubmitModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 font-semibold text-white shadow-sm"
                >
                  Confirm External Submission
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verified Sponsor Decision Modal */}
      {isDecisionModalOpen && selectedApp && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-emerald-400" />
              Record Verified External Sponsor Funding Decision
            </h3>
            <p className="text-xs text-slate-400">
              Preserves institutional audit history and synchronizes sanctioned grant awards directly into project budget planning.
            </p>

            <form onSubmit={handleRecordDecision} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Sponsor Decision</label>
                  <select
                    value={decisionForm.decision}
                    onChange={(e) => setDecisionForm({ ...decisionForm, decision: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="AWARDED">AWARDED (Sanctioned)</option>
                    <option value="DECLINED">DECLINED</option>
                    <option value="WITHDRAWN">WITHDRAWN</option>
                    <option value="RESUBMISSION_REQUESTED">RESUBMISSION REQUESTED</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">Sanctioned Award Number</label>
                  <input
                    type="text"
                    value={decisionForm.award_number}
                    onChange={(e) => setDecisionForm({ ...decisionForm, award_number: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Sanctioned Funding Amount ({selectedApp.currency})</label>
                <input
                  type="number"
                  value={decisionForm.award_amount}
                  onChange={(e) => setDecisionForm({ ...decisionForm, award_amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Sponsor Evaluation Notes</label>
                <textarea
                  rows={2}
                  value={decisionForm.decision_notes}
                  onChange={(e) => setDecisionForm({ ...decisionForm, decision_notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Award Letter URL (Evidence Document)</label>
                <input
                  type="url"
                  value={decisionForm.award_letter_url}
                  onChange={(e) => setDecisionForm({ ...decisionForm, award_letter_url: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="create_award_flag"
                  checked={decisionForm.create_award_record}
                  onChange={(e) =>
                    setDecisionForm({ ...decisionForm, create_award_record: e.target.checked })
                  }
                  className="rounded bg-slate-950 border-slate-800 text-emerald-600"
                />
                <label htmlFor="create_award_flag" className="text-slate-300">
                  Automatically create and attach authoritative ResearchGrantAward to project
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsDecisionModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-sm"
                >
                  Record Verified Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
