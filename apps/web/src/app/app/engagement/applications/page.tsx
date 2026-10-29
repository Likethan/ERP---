"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck2,
  Filter,
  GraduationCap,
  ListOrdered,
  Search,
  ShieldCheck,
  UserCheck,
  UserX,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  ApplicationReviewInput,
  ParticipationApplication,
} from "@/types/engagement";

export default function EngagementApplicationsPage() {
  const [applications, setApplications] = useState<ParticipationApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedApp, setSelectedApp] = useState<ParticipationApplication | null>(null);

  // Review Dialog State
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [reviewApp, setReviewApp] = useState<ParticipationApplication | null>(null);
  const [reviewStatus, setReviewStatus] = useState<"APPROVED" | "WAITLISTED" | "REJECTED">("APPROVED");
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications() {
    setLoading(true);
    try {
      const data = await EngagementService.listApplications();
      setApplications(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleReviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reviewApp) return;

    try {
      const review: ApplicationReviewInput = {
        status: reviewStatus,
        reviewer_notes: reviewerNotes,
        rejection_reason: reviewStatus === "REJECTED" ? rejectionReason : undefined,
      };

      await EngagementService.reviewApplication(reviewApp.id, review);
      setActionMessage(`Application marked as ${reviewStatus}!`);
      setIsReviewOpen(false);
      setReviewerNotes("");
      setRejectionReason("");
      await loadApplications();
    } catch (err: any) {
      setActionMessage(`Review submission error: ${err.message}`);
    }
  }

  const filteredApps = applications.filter((app) => {
    const matchesSearch =
      (app.student_name && app.student_name.toLowerCase().includes(search.toLowerCase())) ||
      (app.student_roll_number && app.student_roll_number.toLowerCase().includes(search.toLowerCase())) ||
      (app.statement_of_interest && app.statement_of_interest.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {actionMessage && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-medium flex items-center justify-between">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <FileCheck2 className="h-6 w-6 text-emerald-500" />
              Participation Applications & Waitlist
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Review volunteer candidacies, manage safety clearances, and supervise automated waitlists
            </p>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by student name, roll number, or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="APPLIED">Applied (Pending)</option>
              <option value="APPROVED">Approved</option>
              <option value="WAITLISTED">Waitlisted</option>
              <option value="REJECTED">Rejected</option>
              <option value="WITHDRAWN">Withdrawn</option>
            </select>
          </div>
        </div>

        {/* Applications Table */}
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">Student Volunteer</th>
                  <th className="px-4 py-3">Opportunity</th>
                  <th className="px-4 py-3">Submission Date</th>
                  <th className="px-4 py-3">Safety Clearance</th>
                  <th className="px-4 py-3">Status / Queue</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium text-foreground">
                      <div className="flex items-center gap-2">
                        <GraduationCap className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span>{app.student_name || "Student Participant"}</span>
                          <span className="block text-[10px] text-muted-foreground font-mono">
                            {app.student_roll_number || "Verified"}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-3 text-foreground">
                      <span className="font-semibold line-clamp-1">
                        {app.opportunity?.title || "Volunteering Opportunity"}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(app.applied_at).toLocaleDateString()}
                    </td>

                    <td className="px-4 py-3">
                      {app.has_safety_clearance ? (
                        <span className="inline-flex items-center gap-1 text-emerald-500 font-medium">
                          <ShieldCheck className="h-3.5 w-3.5" /> Cleared
                        </span>
                      ) : (
                        <span className="text-amber-500 font-medium">Pending Sign-off</span>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            app.status === "APPROVED"
                              ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                              : app.status === "WAITLISTED"
                              ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                              : app.status === "REJECTED"
                              ? "bg-red-500/10 text-red-500 border border-red-500/20"
                              : "bg-blue-500/10 text-blue-500 border border-blue-500/20"
                          }`}
                        >
                          {app.status}
                        </span>
                        {app.status === "WAITLISTED" && app.waitlist_position && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-muted text-muted-foreground font-mono flex items-center gap-0.5">
                            <ListOrdered className="h-3 w-3" /> #{app.waitlist_position}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => setSelectedApp(app)}
                        className="px-2.5 py-1 rounded border border-border text-foreground hover:bg-accent text-[11px] font-medium"
                      >
                        View
                      </button>
                      <button
                        onClick={() => {
                          setReviewApp(app);
                          setReviewStatus("APPROVED");
                          setIsReviewOpen(true);
                        }}
                        className="px-2.5 py-1 rounded bg-primary text-primary-foreground text-[11px] font-semibold hover:opacity-90"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Application Details Modal */}
        {selectedApp && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground block">Application Dossier</span>
                  <h2 className="text-base font-bold text-foreground">
                    {selectedApp.student_name || "Applicant Record"}
                  </h2>
                </div>
                <button onClick={() => setSelectedApp(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-2">
                  <h4 className="font-semibold text-foreground">Student Statement of Interest</h4>
                  <p className="text-muted-foreground italic">
                    &ldquo;{selectedApp.statement_of_interest || "No statement provided."}&rdquo;
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2.5 rounded-lg bg-background border border-border">
                    <span className="text-[10px] text-muted-foreground block">Safety Clearance</span>
                    <span className="font-semibold text-emerald-500">
                      {selectedApp.has_safety_clearance ? "Verified & Cleared" : "Pending Waiver"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-background border border-border">
                    <span className="text-[10px] text-muted-foreground block">Current Status</span>
                    <span className="font-semibold text-foreground">{selectedApp.status}</span>
                  </div>
                </div>

                {selectedApp.reviewer_notes && (
                  <div className="p-3 rounded-lg bg-muted/20 border border-border">
                    <span className="font-semibold text-foreground block mb-0.5">Coordinator Review Notes:</span>
                    <p className="text-muted-foreground">{selectedApp.reviewer_notes}</p>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedApp(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Review Action Modal */}
        {isReviewOpen && reviewApp && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <UserCheck className="h-5 w-5 text-emerald-500" />
                  Review Application
                </h2>
                <button onClick={() => setIsReviewOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleReviewSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Decision *</label>
                  <select
                    value={reviewStatus}
                    onChange={(e) => setReviewStatus(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="APPROVED">Approve for Opportunity</option>
                    <option value="WAITLISTED">Place on Waitlist</option>
                    <option value="REJECTED">Reject Application</option>
                  </select>
                </div>

                {reviewStatus === "REJECTED" && (
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Rejection Reason *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ineligible cohort / Capacity reached"
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                )}

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Coordinator Notes</label>
                  <textarea
                    rows={3}
                    placeholder="Document feedback or shift allocation notes for the student..."
                    value={reviewerNotes}
                    onChange={(e) => setReviewerNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsReviewOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Confirm Decision
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

