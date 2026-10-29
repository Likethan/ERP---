"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Edit3,
  FileCheck2,
  FileText,
  Filter,
  History,
  PlusCircle,
  Search,
  ShieldAlert,
  UserCheck,
  UserX,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  EngagementProgram,
  ServiceHourCorrectionInput,
  ServiceHourEntry,
  ServiceHourLogInput,
  ServiceHourStatus,
  ServiceHourVerifyInput,
} from "@/types/engagement";

export default function EngagementServiceHoursPage() {
  const [hours, setHours] = useState<ServiceHourEntry[]>([]);
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedEntry, setSelectedEntry] = useState<ServiceHourEntry | null>(null);

  // Log Hours Modal State
  const [isLogOpen, setIsLogOpen] = useState(false);
  const [progId, setProgId] = useState("");
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split("T")[0]);
  const [duration, setDuration] = useState(3.5);
  const [description, setDescription] = useState("");
  const [beneficiaries, setBeneficiaries] = useState(15);
  const [supervisorName, setSupervisorName] = useState("");
  const [supervisorEmail, setSupervisorEmail] = useState("");

  // Verification Modal State
  const [isVerifyOpen, setIsVerifyOpen] = useState(false);
  const [verifyEntry, setVerifyEntry] = useState<ServiceHourEntry | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<"APPROVED" | "REJECTED" | "CORRECTION_REQUESTED">("APPROVED");
  const [supervisorComments, setSupervisorComments] = useState("");

  // Correction Modal State
  const [isCorrectOpen, setIsCorrectOpen] = useState(false);
  const [correctEntry, setCorrectEntry] = useState<ServiceHourEntry | null>(null);
  const [newHours, setNewHours] = useState(4.0);
  const [reasonForChange, setReasonForChange] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [h, p] = await Promise.all([
        EngagementService.listServiceHours(),
        EngagementService.listPrograms(),
      ]);
      setHours(h);
      setPrograms(p);
      if (p.length > 0) setProgId(p[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogHours(e: React.FormEvent) {
    e.preventDefault();
    if (!progId || !description || duration <= 0 || duration > 24) return;

    try {
      const input: ServiceHourLogInput = {
        program_id: progId,
        activity_date: activityDate,
        duration_hours: Number(duration),
        activity_description: description,
        community_beneficiaries_served: Number(beneficiaries),
        supervisor_name: supervisorName,
        supervisor_email: supervisorEmail,
      };

      await EngagementService.submitServiceHours(input);
      setActionMessage("Service hours logged successfully in PENDING review status.");
      setIsLogOpen(false);
      setDescription("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error logging service hours: ${err.message}`);
    }
  }

  async function handleVerifySubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!verifyEntry) return;

    try {
      const input: ServiceHourVerifyInput = {
        status: verifyStatus,
        supervisor_comments: supervisorComments,
      };

      await EngagementService.verifyServiceHours(verifyEntry.id, input);
      setActionMessage(`Service hours verified as ${verifyStatus}!`);
      setIsVerifyOpen(false);
      setSupervisorComments("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Verification error: ${err.message}`);
    }
  }

  async function handleCorrectSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!correctEntry || !reasonForChange) return;

    try {
      const input: ServiceHourCorrectionInput = {
        new_hours: Number(newHours),
        reason_for_change: reasonForChange,
      };

      await EngagementService.correctServiceHours(correctEntry.id, input);
      setActionMessage("Hours corrected and recorded in the audit history ledger.");
      setIsCorrectOpen(false);
      setReasonForChange("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Correction error: ${err.message}`);
    }
  }

  const filteredHours = hours.filter((h) => {
    const matchesSearch =
      (h.student_name && h.student_name.toLowerCase().includes(search.toLowerCase())) ||
      (h.activity_description && h.activity_description.toLowerCase().includes(search.toLowerCase())) ||
      (h.supervisor_name && h.supervisor_name.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || h.status === statusFilter;
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
              <Clock className="h-6 w-6 text-amber-500" />
              Service Hours, Verification & Audit Ledger
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Strict multi-tier review, attendance cross-check, and tamper-evident adjustments ledger
            </p>
          </div>

          <button
            onClick={() => setIsLogOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Log Service Hours</span>
          </button>
        </div>

        {/* Filter Controls */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by student, task description, or supervisor..."
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
              <option value="PENDING">Pending Verification</option>
              <option value="APPROVED">Approved & Credited</option>
              <option value="CORRECTION_REQUESTED">Correction Requested</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>

        {/* Service Hours Table */}
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Hours</th>
                  <th className="px-4 py-3">Description & Beneficiaries</th>
                  <th className="px-4 py-3">Supervisor</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredHours.map((entry) => (
                  <tr key={entry.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium text-foreground">
                      <span>{entry.student_name || "Enrolled Student"}</span>
                      <span className="block text-[10px] text-muted-foreground font-mono">
                        {entry.student_roll_number || "Verified"}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-muted-foreground">{entry.activity_date}</td>

                    <td className="px-4 py-3 font-bold text-foreground">
                      <div className="flex items-center gap-1.5">
                        <span>{entry.duration_hours} hrs</span>
                        {entry.corrections && entry.corrections.length > 0 && (
                          <span className="text-[10px] px-1 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20 font-normal">
                            Edited
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-3 text-muted-foreground max-w-xs">
                      <p className="truncate text-foreground">{entry.activity_description}</p>
                      {entry.community_beneficiaries_served && (
                        <span className="text-[10px] text-muted-foreground">
                          {entry.community_beneficiaries_served} community beneficiaries served
                        </span>
                      )}
                    </td>

                    <td className="px-4 py-3 text-muted-foreground">
                      {entry.supervisor_name || "Partner Field Lead"}
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          entry.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                            : entry.status === "PENDING"
                            ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                            : entry.status === "CORRECTION_REQUESTED"
                            ? "bg-blue-500/10 text-blue-500 border border-blue-500/20"
                            : "bg-red-500/10 text-red-500 border border-red-500/20"
                        }`}
                      >
                        {entry.status}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => setSelectedEntry(entry)}
                        className="px-2 py-1 rounded border border-border text-foreground hover:bg-accent text-[11px]"
                      >
                        Ledger
                      </button>
                      <button
                        onClick={() => {
                          setVerifyEntry(entry);
                          setVerifyStatus("APPROVED");
                          setIsVerifyOpen(true);
                        }}
                        className="px-2 py-1 rounded bg-emerald-500 text-white hover:bg-emerald-600 text-[11px] font-semibold"
                      >
                        Verify
                      </button>
                      <button
                        onClick={() => {
                          setCorrectEntry(entry);
                          setNewHours(entry.duration_hours);
                          setIsCorrectOpen(true);
                        }}
                        className="px-2 py-1 rounded border border-amber-500/30 text-amber-500 hover:bg-amber-500/10 text-[11px]"
                      >
                        Adjust
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Audit Ledger Modal */}
        {selectedEntry && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <History className="h-5 w-5 text-amber-500" />
                  <div>
                    <h2 className="text-base font-bold text-foreground">Service-Hour Audit Ledger</h2>
                    <span className="text-[10px] text-muted-foreground">
                      ID: {selectedEntry.id}
                    </span>
                  </div>
                </div>
                <button onClick={() => setSelectedEntry(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Current Duration:</span>
                    <span className="font-bold text-foreground">{selectedEntry.duration_hours} hours</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Verification Status:</span>
                    <span className="font-semibold text-emerald-500">{selectedEntry.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Activity Date:</span>
                    <span className="text-foreground">{selectedEntry.activity_date}</span>
                  </div>
                  {selectedEntry.supervisor_comments && (
                    <div className="pt-1 border-t border-border">
                      <span className="text-muted-foreground block text-[10px]">Supervisor Comments:</span>
                      <p className="text-foreground italic">&ldquo;{selectedEntry.supervisor_comments}&rdquo;</p>
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
                    <History className="h-4 w-4 text-muted-foreground" />
                    Historical Corrections & Adjustments
                  </h4>

                  {selectedEntry.corrections && selectedEntry.corrections.length > 0 ? (
                    <div className="border border-border rounded-lg divide-y divide-border">
                      {selectedEntry.corrections.map((corr) => (
                        <div key={corr.id} className="p-3 space-y-1">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-medium text-foreground">
                              {corr.previous_hours} hrs → {corr.new_hours} hrs
                            </span>
                            <span className="text-muted-foreground">
                              {new Date(corr.changed_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-muted-foreground italic">&ldquo;{corr.reason_for_change}&rdquo;</p>
                          <span className="text-[10px] text-muted-foreground block">
                            Logged by: {corr.changed_by_name || "Authorized Coordinator"}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground italic bg-muted/20 p-3 rounded-lg text-center">
                      No manual corrections recorded. Original submission intact.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Verification Modal */}
        {isVerifyOpen && verifyEntry && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <UserCheck className="h-5 w-5 text-emerald-500" />
                  Verify Service Hours
                </h2>
                <button onClick={() => setIsVerifyOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleVerifySubmit} className="space-y-4">
                <div className="p-3 rounded-lg bg-muted/30 border border-border space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Student:</span>
                    <span className="font-semibold text-foreground">{verifyEntry.student_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Submitted Duration:</span>
                    <span className="font-bold text-foreground">{verifyEntry.duration_hours} hours</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Decision *</label>
                  <select
                    value={verifyStatus}
                    onChange={(e) => setVerifyStatus(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="APPROVED">Approve and Credit Hours</option>
                    <option value="CORRECTION_REQUESTED">Request Student Correction</option>
                    <option value="REJECTED">Reject Hours Submission</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Supervisor Evaluation Comments</label>
                  <textarea
                    rows={3}
                    placeholder="Document qualitative feedback on field performance and civic engagement..."
                    value={supervisorComments}
                    onChange={(e) => setSupervisorComments(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsVerifyOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Submit Verification
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Correction Modal */}
        {isCorrectOpen && correctEntry && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Edit3 className="h-5 w-5 text-amber-500" />
                  Adjust Service Hours (Audit Ledger)
                </h2>
                <button onClick={() => setIsCorrectOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleCorrectSubmit} className="space-y-4">
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>
                    Any adjustment to service hours is immutably recorded in the institutional audit ledger.
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-muted-foreground">Original Hours</label>
                    <input
                      type="text"
                      disabled
                      value={`${correctEntry.duration_hours} hrs`}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-muted text-muted-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Adjusted Hours *</label>
                    <input
                      type="number"
                      step="0.25"
                      min="0.25"
                      max="24"
                      required
                      value={newHours}
                      onChange={(e) => setNewHours(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Documented Reason for Adjustment *</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="e.g. Added 30 minutes for site handover and waste weighing..."
                    value={reasonForChange}
                    onChange={(e) => setReasonForChange(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsCorrectOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-amber-500 text-white font-semibold shadow hover:opacity-95"
                  >
                    Save Correction
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Log Service Hours Modal */}
        {isLogOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-primary" />
                  Log Volunteer Service Hours
                </h2>
                <button onClick={() => setIsLogOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleLogHours} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Program *</label>
                  <select
                    value={progId}
                    onChange={(e) => setProgId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    required
                  >
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.code} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Activity Date *</label>
                    <input
                      type="date"
                      required
                      value={activityDate}
                      onChange={(e) => setActivityDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Duration (Hours) *</label>
                    <input
                      type="number"
                      step="0.25"
                      min="0.25"
                      max="24"
                      required
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Activity Description *</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Specify the community work completed, field site tasks, and deliverables..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Beneficiaries Served</label>
                    <input
                      type="number"
                      min={0}
                      value={beneficiaries}
                      onChange={(e) => setBeneficiaries(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Field Supervisor Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Dr. Ananya Roy"
                      value={supervisorName}
                      onChange={(e) => setSupervisorName(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsLogOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Submit Hours
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

