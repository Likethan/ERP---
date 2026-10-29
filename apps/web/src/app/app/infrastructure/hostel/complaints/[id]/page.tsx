"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { hostelComplaintsService } from "@/services/hostel-complaints.service";
import {
  HostelComplaint,
  ComplaintStatus,
  ComplaintPriority,
} from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  MessageSquare,
  ShieldAlert,
  User,
  Wrench,
  UserCheck,
} from "lucide-react";

export default function HostelComplaintDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const complaintId = resolvedParams.id;
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [complaint, setComplaint] = useState<HostelComplaint | null>(null);
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [staffNameInput, setStaffNameInput] = useState("");

  const isStaffOrAdmin =
    user?.roles?.[0]?.name === "SUPER_ADMIN" ||
    user?.roles?.[0]?.name === "ADMIN" ||
    user?.roles?.[0]?.name === "WARDEN" ||
    user?.roles?.[0]?.name === "FACILITY_OFFICER";

  const loadComplaint = async () => {
    setLoading(true);
    try {
      const res =
        await hostelComplaintsService.getHostelComplaintById(complaintId);
      if (res.success && res.data) {
        setComplaint(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaint();
  }, [complaintId]);

  const handleStartWork = async () => {
    if (!complaint) return;
    const actor = user?.first_name
      ? `${user.first_name} ${user.last_name}`
      : "Maintenance Staff";
    await hostelComplaintsService.updateComplaintStatus(
      complaint.id,
      ComplaintStatus.IN_PROGRESS,
      actor,
      "Technician commenced on-site assessment and repairs",
    );
    loadComplaint();
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaint || !resolutionNotes.trim()) return;
    const actor = user?.first_name
      ? `${user.first_name} ${user.last_name}`
      : "Maintenance Supervisor";
    await hostelComplaintsService.updateComplaintStatus(
      complaint.id,
      ComplaintStatus.RESOLVED,
      actor,
      resolutionNotes.trim(),
    );
    setResolveModalOpen(false);
    setResolutionNotes("");
    loadComplaint();
  };

  const handleClose = async () => {
    if (!complaint) return;
    const actor = user?.first_name
      ? `${user.first_name} ${user.last_name}`
      : "Hostel Warden";
    await hostelComplaintsService.updateComplaintStatus(
      complaint.id,
      ComplaintStatus.CLOSED,
      actor,
      "Resident confirmed issue resolution. Ticket formally closed.",
    );
    loadComplaint();
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaint || !staffNameInput.trim()) return;
    const actor = user?.first_name
      ? `${user.first_name} ${user.last_name}`
      : "Warden Office";
    await hostelComplaintsService.assignComplaint(
      complaint.id,
      `tech-${Date.now().toString(36)}`,
      staffNameInput.trim(),
      actor,
    );
    setAssignModalOpen(false);
    setStaffNameInput("");
    loadComplaint();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!complaint) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">
          Complaint Record Not Found
        </h2>
        <Link href="/app/infrastructure/hostel/complaints">
          <Button variant="outline" className="border-slate-700">
            Back to Complaints
          </Button>
        </Link>
      </div>
    );
  }

  const priorityColors = {
    [ComplaintPriority.CRITICAL]:
      "bg-red-500/10 text-red-400 border-red-500/20",
    [ComplaintPriority.HIGH]:
      "bg-amber-500/10 text-amber-400 border-amber-500/20",
    [ComplaintPriority.MEDIUM]:
      "bg-blue-500/10 text-blue-400 border-blue-500/20",
    [ComplaintPriority.LOW]:
      "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  const statusColors: Record<ComplaintStatus, string> = {
    [ComplaintStatus.OPEN]:
      "bg-amber-500/10 text-amber-400 border-amber-500/20",
    [ComplaintStatus.ASSIGNED]:
      "bg-blue-500/10 text-blue-400 border-blue-500/20",
    [ComplaintStatus.IN_PROGRESS]:
      "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    [ComplaintStatus.RESOLVED]:
      "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    [ComplaintStatus.CLOSED]:
      "bg-slate-500/10 text-slate-400 border-slate-500/20",
    [ComplaintStatus.REJECTED]: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/hostel/complaints"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Hostel Complaints
        </Link>
      </div>

      {/* Header Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-md border border-indigo-500/20">
                {complaint.ticketNumber}
              </span>
              <Badge
                variant="outline"
                className={priorityColors[complaint.priority]}
              >
                {complaint.priority} PRIORITY
              </Badge>
              <Badge
                variant="outline"
                className={statusColors[complaint.status]}
              >
                {complaint.status}
              </Badge>
              <Badge
                variant="outline"
                className="bg-slate-800 text-slate-300 border-slate-700"
              >
                {complaint.category}
              </Badge>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {complaint.title}
            </h1>
            <p className="text-slate-400 text-sm max-w-2xl">
              {complaint.description}
            </p>
          </div>

          {/* Action Buttons for Warden / Admin */}
          {isStaffOrAdmin && (
            <div className="flex flex-wrap md:flex-col gap-2 shrink-0">
              {complaint.status === ComplaintStatus.OPEN && (
                <Button
                  onClick={() => setAssignModalOpen(true)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 text-xs"
                >
                  <UserCheck className="w-4 h-4" />
                  Assign Technician
                </Button>
              )}
              {complaint.status === ComplaintStatus.ASSIGNED && (
                <Button
                  onClick={handleStartWork}
                  className="bg-blue-600 hover:bg-blue-500 text-white gap-2 text-xs"
                >
                  <Wrench className="w-4 h-4" />
                  Start In-Progress
                </Button>
              )}
              {(complaint.status === ComplaintStatus.ASSIGNED ||
                complaint.status === ComplaintStatus.IN_PROGRESS) && (
                <Button
                  onClick={() => setResolveModalOpen(true)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 text-xs"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Mark Resolved
                </Button>
              )}
              {complaint.status === ComplaintStatus.RESOLVED && (
                <Button
                  onClick={handleClose}
                  className="bg-slate-700 hover:bg-slate-600 text-white gap-2 text-xs"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Close Ticket
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Two Column Layout: Details & SLAs vs Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Location & Resident Details */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              Location & Resident Information
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Hostel Facility
                </span>
                <span className="font-medium text-white">
                  {complaint.hostelName}
                </span>
              </div>
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Room Number
                </span>
                <span className="font-semibold text-indigo-300">
                  Room {complaint.roomNumber}
                </span>
              </div>
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Resident Student
                </span>
                <Link
                  href={`/app/students/${complaint.studentId}`}
                  className="font-medium text-indigo-400 hover:underline flex items-center gap-1.5"
                >
                  <User className="w-3.5 h-3.5" />
                  {complaint.studentName}
                </Link>
              </div>
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Register Number
                </span>
                <span className="font-mono text-slate-300">
                  {complaint.registerNumber}
                </span>
              </div>
            </div>
          </div>

          {/* Assigned Technician & Resolution notes */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Wrench className="w-4 h-4 text-emerald-400" />
              Service & Assignment Details
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Assigned Technician
                </span>
                <span className="font-medium text-white">
                  {complaint.assignedStaffName || "Unassigned"}
                </span>
              </div>
              <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-500 block mb-1">
                  Resolution SLA Target
                </span>
                <span className="font-medium text-white">
                  {complaint.slaTargetHours} Hours
                </span>
              </div>
            </div>

            {complaint.resolutionNotes && (
              <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  Official Resolution Note
                </div>
                <p className="text-sm text-slate-300">
                  {complaint.resolutionNotes}
                </p>
                {complaint.resolvedAt && (
                  <span className="text-xs text-emerald-500/80 block mt-1">
                    Resolved at:{" "}
                    {new Date(complaint.resolvedAt).toLocaleString("en-IN")}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: SLA & Activity Timeline (1 col) */}
        <div className="space-y-6">
          {/* SLA Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              SLA Health
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Target Resolution</span>
                <span className="font-mono text-white">
                  {complaint.slaTargetHours}h SLA
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Breach Status</span>
                {complaint.slaBreached ? (
                  <Badge
                    variant="outline"
                    className="bg-red-500/10 text-red-400 border-red-500/20 gap-1"
                  >
                    <ShieldAlert className="w-3 h-3" /> SLA Breached
                  </Badge>
                ) : (
                  <Badge
                    variant="outline"
                    className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 gap-1"
                  >
                    <CheckCircle2 className="w-3 h-3" /> Within SLA
                  </Badge>
                )}
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Reported</span>
                <span className="text-xs text-slate-300">
                  {new Date(complaint.createdAt).toLocaleDateString("en-IN")}
                </span>
              </div>
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              Lifecycle Timeline
            </h2>
            <div className="relative pl-6 space-y-6 border-l border-slate-800">
              {complaint.activityTimeline?.map((item, idx) => (
                <div key={item.id || idx} className="relative group">
                  <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-indigo-500 border-2 border-slate-900 group-hover:scale-125 transition-transform" />
                  <div className="space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-white">
                        {item.action}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <span className="text-xs text-indigo-400 block font-medium">
                      {item.actor}
                    </span>
                    {item.notes && (
                      <p className="text-xs text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                        {item.notes}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Assign Modal */}
      {assignModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-indigo-400" />
              Assign Maintenance Technician
            </h3>
            <form onSubmit={handleAssign} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Technician / Staff Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar (Electrician)"
                  value={staffNameInput}
                  onChange={(e) => setStaffNameInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAssignModalOpen(false)}
                  className="border-slate-800 text-slate-400"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white"
                >
                  Assign Staff
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {resolveModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Mark Complaint Resolved
            </h3>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Resolution Summary
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detail the work carried out to rectify the issue..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setResolveModalOpen(false)}
                  className="border-slate-800 text-slate-400"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  Confirm Resolution
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
