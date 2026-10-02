"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { hostelLeavesService } from "@/services/hostel-leaves.service";
import { HostelLeave, LeaveStatus } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileCheck2,
  Calendar,
  User,
  Phone,
  MapPin,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowLeft,
  Building2,
} from "lucide-react";

export default function HostelLeaveDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const leaveId = resolvedParams.id;
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [leave, setLeave] = useState<HostelLeave | null>(null);

  const isWardenOrAdmin =
    user?.roles?.[0]?.name === "SUPER_ADMIN" ||
    user?.roles?.[0]?.name === "ADMIN" ||
    user?.roles?.[0]?.name === "WARDEN";

  const loadLeave = async () => {
    setLoading(true);
    try {
      const res = await hostelLeavesService.getHostelLeaveById(leaveId);
      if (res.success && res.data) {
        setLeave(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeave();
  }, [leaveId]);

  const handleApprove = async () => {
    if (!leave) return;
    await hostelLeavesService.approveHostelLeave(
      leave.id,
      user?.first_name ? `${user.first_name} ${user.last_name} (Warden)` : "Prof. S. K. Patil (Warden)",
      "Approved after telephonic parent confirmation"
    );
    loadLeave();
  };

  const handleReject = async () => {
    if (!leave) return;
    await hostelLeavesService.rejectHostelLeave(
      leave.id,
      user?.first_name ? `${user.first_name} ${user.last_name}` : "Warden Office",
      "Conflicting internal assessment exams on scheduled return date"
    );
    loadLeave();
  };

  const handleReturn = async () => {
    if (!leave) return;
    await hostelLeavesService.markLeaveReturn(leave.id);
    loadLeave();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    );
  }

  if (!leave) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Leave Record Not Found</h2>
        <Link href="/app/infrastructure/hostel/leaves">
          <Button variant="outline" className="border-slate-700">
            Back to Leaves
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto text-slate-100">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/app/infrastructure" className="hover:text-white">
          Infrastructure
        </Link>
        <span>/</span>
        <Link href="/app/infrastructure/hostel/leaves" className="hover:text-white">
          Leaves
        </Link>
        <span>/</span>
        <span className="text-indigo-400 font-mono">{leave.studentName}</span>
      </div>

      {/* Hero Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant="outline" className="text-xs">
              {leave.approvalStatus}
            </Badge>
            <span className="text-xs font-mono text-slate-400">{leave.registerNumber}</span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileCheck2 className="h-6 w-6 text-indigo-400" />
            Gate Pass: {leave.studentName}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {leave.hostelName} • Room {leave.roomNumber}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          {leave.approvalStatus === LeaveStatus.PENDING && isWardenOrAdmin && (
            <>
              <Button onClick={handleReject} variant="outline" className="border-rose-800 text-rose-400 hover:bg-rose-950 text-xs">
                <XCircle className="h-3.5 w-3.5 mr-1.5" />
                Reject
              </Button>
              <Button onClick={handleApprove} className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs">
                <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
                Approve Gate Pass
              </Button>
            </>
          )}
          {leave.approvalStatus === LeaveStatus.APPROVED && (
            <Button onClick={handleReturn} className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
              Mark Returned to Campus
            </Button>
          )}
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider pb-2 border-b border-slate-800">
            Travel & Duration Details
          </h3>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Departure Date:</span>
              <span className="font-mono text-white">{leave.startDate}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Expected Return:</span>
              <span className="font-mono text-white">{leave.endDate}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Destination:</span>
              <span className="text-white font-medium">{leave.destination}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Reason:</span>
              <span className="text-slate-200">{leave.reason}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider pb-2 border-b border-slate-800">
            Emergency Contact & Warden Decision
          </h3>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Parent / Guardian:</span>
              <span className="text-white font-medium">{leave.emergencyContact.name} ({leave.emergencyContact.relationship})</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Emergency Phone:</span>
              <span className="font-mono text-indigo-400">{leave.emergencyContact.phone}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Approved By:</span>
              <span>{leave.approvedBy || "Pending Review"}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Warden Remarks:</span>
              <span className="text-slate-200 italic">{leave.remarks || "No remarks noted"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
