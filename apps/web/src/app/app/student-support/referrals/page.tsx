"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import {
  SupportReferralItem,
  MenteeItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  ArrowRightLeft,
  PlusCircle,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  ShieldCheck,
  Building,
  UserCheck,
  XCircle,
} from "lucide-react";

const TARGET_SERVICES = [
  "ACADEMIC_ADVISING",
  "CAREER_SERVICES",
  "COUNSELLING_SERVICES",
  "DISABILITY_SUPPORT",
  "FINANCIAL_AID",
  "HEALTH_SERVICES",
];

export default function StudentSupportReferralsPage() {
  const [referrals, setReferrals] = useState<SupportReferralItem[]>([]);
  const [mentees, setMentees] = useState<MenteeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [serviceFilter, setServiceFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Referral Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [targetService, setTargetService] = useState("CAREER_SERVICES");
  const [reasonCategory, setReasonCategory] = useState("Skill Gap & Placement Strategy");
  const [studentConsent, setStudentConsent] = useState(true);
  const [referralNotes, setReferralNotes] = useState("");
  const [submittingReferral, setSubmittingReferral] = useState(false);

  // Status Transition Modal State
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [selectedRef, setSelectedRef] = useState<SupportReferralItem | null>(null);
  const [newStatus, setNewStatus] = useState<"ACCEPTED" | "IN_PROGRESS" | "COMPLETED" | "DECLINED">("ACCEPTED");
  const [statusNotes, setStatusNotes] = useState("");
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadReferrals();
  }, []);

  async function loadReferrals() {
    setLoading(true);
    try {
      const [allReferrals, allMentees] = await Promise.all([
        StudentSupportService.getReferrals(),
        StudentSupportService.getAssignedMentees(),
      ]);
      setReferrals(allReferrals);
      setMentees(allMentees);
      if (allMentees.length > 0) {
        setStudentId(allMentees[0].student_id || allMentees[0].studentId || "");
      }
    } catch (err) {
      console.error("Failed to load referrals:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateReferral(e: React.FormEvent) {
    e.preventDefault();
    if (!studentId || !targetService || !reasonCategory) return;
    setSubmittingReferral(true);
    try {
      await StudentSupportService.createReferral({
        student_id: studentId,
        target_service: targetService,
        reason_category: reasonCategory,
        student_consent_obtained: studentConsent,
        referrer_role: "FACULTY_MENTOR",
      });

      setNotification("Support referral initiated and transmitted to receiving department.");
      setCreateModalOpen(false);
      setReferralNotes("");
      loadReferrals();
    } catch (err) {
      console.error("Failed to create referral:", err);
      alert("Error initiating referral.");
    } finally {
      setSubmittingReferral(false);
    }
  }

  async function handleUpdateStatus(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedRef) return;
    setUpdatingStatus(true);
    try {
      await StudentSupportService.updateReferralStatus(selectedRef.id, {
        status: newStatus,
        status_notes: statusNotes,
      });

      setNotification(`Referral ${selectedRef.referral_number} updated to ${newStatus}.`);
      setStatusModalOpen(false);
      setSelectedRef(null);
      setStatusNotes("");
      loadReferrals();
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("Unable to transition referral status.");
    } finally {
      setUpdatingStatus(false);
    }
  }

  const filteredReferrals = referrals.filter((r) => {
    const sName = r.student_name || r.studentName || "";
    const sReg = r.student_reg_no || r.studentId || "";
    const refNum = r.referral_number || r.referralCode || "";
    const tService = r.target_service || r.targetService || "";
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    const matchesService = serviceFilter === "ALL" || tService === serviceFilter;
    const matchesSearch =
      sName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sReg.toLowerCase().includes(searchQuery.toLowerCase()) ||
      refNum.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesService && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Support Referrals", href: "/app/student-support/referrals" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <ArrowRightLeft className="h-6 w-6 text-cyan-400" />
              Cross-Department Student Referrals
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Coordinated referral pipelines across academic advising, career guidance, counselling, financial aid, and health services.
            </p>
          </div>
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
          >
            <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
            Initiate Referral
          </Button>
        </div>
      </div>

      <StudentSupportNav />

      {/* Cross-Department Access Boundary Alert */}
      <div className="rounded-xl border border-cyan-900/40 bg-cyan-950/20 p-4">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-cyan-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-300">
            <span className="font-semibold text-white">Controlled Referral Policy:</span> Initiating a referral informs the receiving service of the general guidance category. Referrals do not grant the receiving department access to the originating unit's confidential clinical notes or internal observations.
          </div>
        </div>
      </div>

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search referrals by student, reg no, or referral reference..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Services</option>
            {TARGET_SERVICES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="DECLINED">Declined</option>
          </select>
        </div>
      </Card>

      {/* Referrals Table */}
      <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-medium">
              <tr>
                <th className="py-3 px-4">Ref Number</th>
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Target Service</th>
                <th className="py-3 px-4">Reason Category</th>
                <th className="py-3 px-4">Consent Status</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading referrals...
                  </td>
                </tr>
              ) : filteredReferrals.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No support referrals matching the criteria.
                  </td>
                </tr>
              ) : (
                filteredReferrals.map((ref) => (
                  <tr key={ref.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono font-semibold text-white">
                      {ref.referral_number || ref.referralCode}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">{ref.student_name || ref.studentName}</div>
                      <div className="text-[11px] text-slate-500">{ref.student_reg_no || ref.studentId}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-cyan-300">
                        {String(ref.target_service || ref.targetService || "").replace("_", " ")}
                      </span>
                      <div className="text-[11px] text-slate-500">By: {ref.referrer_role || ref.referring_role || ref.referringRole || "Faculty"}</div>
                    </td>
                    <td className="py-3 px-4">{ref.reason_category}</td>
                    <td className="py-3 px-4">
                      {ref.student_consent_obtained ? (
                        <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/30">
                          Consent Granted
                        </span>
                      ) : (
                        <span className="text-[10px] text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/30">
                          Pending Consent
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant="outline"
                        className={
                          ref.status === "COMPLETED"
                            ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                            : ref.status === "IN_PROGRESS"
                            ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                            : ref.status === "PENDING"
                            ? "border-amber-500/30 text-amber-400 bg-amber-500/10 text-[10px]"
                            : "border-slate-700 text-slate-400 text-[10px]"
                        }
                      >
                        {ref.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {ref.status !== "COMPLETED" && ref.status !== "DECLINED" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedRef(ref);
                            setStatusModalOpen(true);
                          }}
                          className="text-xs text-indigo-400 hover:text-indigo-300"
                        >
                          Update Status
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create Referral Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
              Initiate Student Support Referral
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateReferral} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Select Student *</label>
              <select
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
              >
                {mentees.map((m) => (
                  <option key={m.student_id || m.studentId} value={m.student_id || m.studentId}>
                    {m.student_name || m.studentName} ({m.student_reg_no || m.rollNumber})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Receiving Institutional Service *</label>
              <select
                value={targetService}
                onChange={(e) => setTargetService(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
              >
                {TARGET_SERVICES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Reason / Referral Objective *</label>
              <Input
                required
                placeholder="e.g. Guidance on financial aid eligibility, placement resume coaching"
                value={reasonCategory}
                onChange={(e) => setReasonCategory(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={studentConsent}
                  onChange={(e) => setStudentConsent(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                />
                <span className="text-slate-300">
                  Student informed consent has been obtained for this service referral
                </span>
              </label>
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setCreateModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingReferral}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submittingReferral ? "Dispatching..." : "Dispatch Referral"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Status Transition Modal */}
      <Dialog open={statusModalOpen} onOpenChange={setStatusModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-indigo-400" />
              Update Referral Status
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateStatus} className="space-y-4 pt-2 text-xs">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Referral: </span>
              <strong className="text-white">{selectedRef?.referral_number}</strong> for{" "}
              <span className="text-cyan-300">{selectedRef?.student_name}</span>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">New Status *</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
              >
                <option value="ACCEPTED">Accepted by Service</option>
                <option value="IN_PROGRESS">In Progress / Active Case</option>
                <option value="COMPLETED">Completed / Goal Fulfilled</option>
                <option value="DECLINED">Declined / Ineligible</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Resolution Notes / Comments</label>
              <Textarea
                placeholder="Brief notes on resolution or referral progress..."
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setStatusModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updatingStatus}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {updatingStatus ? "Saving..." : "Update Status"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
