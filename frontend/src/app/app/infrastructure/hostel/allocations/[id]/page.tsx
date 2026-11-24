"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { hostelAllocationsService } from "@/services/hostel-allocations.service";
import { HostelAllocation, AllocationStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  UserCheck,
  BedDouble,
  User,
  Calendar,
  Clock,
  ArrowLeft,
  ExternalLink,
  DoorOpen,
  Building2,
  CheckCircle2,
  ArrowRight,
  RotateCcw,
  LogOut,
} from "lucide-react";

export default function AllocationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const allocId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [allocation, setAllocation] = useState<HostelAllocation | null>(null);

  // Transfer Modal
  const [transferModalOpen, setTransferModalOpen] = useState(false);
  const [transferForm, setTransferForm] = useState({
    hostelName: "Sir C. V. Raman Hall of Residence",
    roomNumber: "305",
    bedNumber: "Bed B",
    reason: "Requested quiet study corner room",
  });

  // Vacate Modal
  const [vacateModalOpen, setVacateModalOpen] = useState(false);
  const [vacateReason, setVacateReason] = useState(
    "Semester internship outside campus",
  );

  const loadAllocation = async () => {
    setLoading(true);
    try {
      const res = await hostelAllocationsService.getAllocationById(allocId);
      if (res.success && res.data) {
        setAllocation(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllocation();
  }, [allocId]);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allocation) return;

    await hostelAllocationsService.transferHostelAllocation(allocation.id, {
      hostelId: allocation.hostelId,
      hostelName: transferForm.hostelName,
      blockId: allocation.blockId,
      blockName: allocation.blockName,
      floor: allocation.floor,
      roomId: `rm-${transferForm.roomNumber}`,
      roomNumber: transferForm.roomNumber,
      bedId: `bed-${transferForm.roomNumber}-b`,
      bedNumber: transferForm.bedNumber,
      reason: transferForm.reason,
      transferredBy: "Chief Warden Office",
    });

    setTransferModalOpen(false);
    loadAllocation();
  };

  const handleVacate = async () => {
    if (!allocation) return;
    await hostelAllocationsService.vacateHostelAllocation(
      allocation.id,
      vacateReason,
      "Chief Warden Office",
    );
    setVacateModalOpen(false);
    loadAllocation();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!allocation) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">
          Allocation Not Found
        </h2>
        <p className="text-xs mb-4">
          No record matching ID &ldquo;{allocId}&rdquo;.
        </p>
        <Link href="/app/infrastructure/hostel/allocations">
          <Button variant="outline" className="border-slate-700">
            Back to Allocations
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto text-slate-100">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/app/infrastructure" className="hover:text-white">
          Infrastructure
        </Link>
        <span>/</span>
        <Link
          href="/app/infrastructure/hostel/allocations"
          className="hover:text-white"
        >
          Allocations
        </Link>
        <span>/</span>
        <span className="text-indigo-400 font-mono">
          {allocation.registerNumber}
        </span>
      </div>

      {/* Hero Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Badge
              variant="outline"
              className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            >
              {allocation.status}
            </Badge>
            <span className="text-xs font-mono text-slate-400">
              Ref: {allocation.financeRefId}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <UserCheck className="h-6 w-6 text-indigo-400" />
            {allocation.studentName}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Roll: {allocation.registerNumber} • {allocation.programName} (Year{" "}
            {allocation.year})
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {allocation.status === AllocationStatus.ALLOCATED && (
            <>
              <Button
                variant="outline"
                onClick={() => setTransferModalOpen(true)}
                className="border-slate-700 hover:bg-slate-800 text-slate-300 text-xs"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1.5 text-indigo-400" />
                Room Transfer
              </Button>
              <Button
                variant="outline"
                onClick={() => setVacateModalOpen(true)}
                className="border-slate-700 hover:bg-slate-800 text-rose-400 text-xs"
              >
                <LogOut className="h-3.5 w-3.5 mr-1.5" />
                Vacate Bed
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Grid: Student Profile & Allocation Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Student 360 Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <User className="h-4 w-4 text-indigo-400" />
              Canonical Student Entity
            </h3>
            {allocation.studentId && (
              <Link
                href={`/app/students/${allocation.studentId}`}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                Student 360° Profile <ExternalLink className="h-3 w-3" />
              </Link>
            )}
          </div>

          <div className="space-y-2.5 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Full Name:</span>
              <span className="font-semibold text-white">
                {allocation.studentName}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Registration Number:</span>
              <span className="font-mono">{allocation.registerNumber}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Academic Program:</span>
              <span>{allocation.programName}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Current Semester:</span>
              <span>
                Semester {allocation.semester} (Year {allocation.year})
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Department:</span>
              <span>{allocation.departmentCode}</span>
            </div>
          </div>
        </div>

        {/* Allocation Spec Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider pb-3 border-b border-slate-800 flex items-center gap-2">
            <BedDouble className="h-4 w-4 text-indigo-400" />
            Bed Slot Assignment
          </h3>

          <div className="space-y-2.5 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Hostel Hall:</span>
              <Link
                href={`/app/infrastructure/hostel/${allocation.hostelId}`}
                className="text-indigo-400 hover:underline font-medium"
              >
                {allocation.hostelName}
              </Link>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Block & Floor:</span>
              <span>
                {allocation.blockName} • Floor {allocation.floor}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Room & Bed Slot:</span>
              <Link
                href={`/app/infrastructure/hostel/rooms/${allocation.roomId}`}
                className="text-white font-bold hover:text-indigo-400"
              >
                Room {allocation.roomNumber} ({allocation.bedNumber})
              </Link>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Allocation Date:</span>
              <span className="font-mono">{allocation.allocatedDate}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Expected Tenure End:</span>
              <span className="font-mono">
                {allocation.expectedEndDate || "End of Degree"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* History Timeline */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Clock className="h-4 w-4 text-indigo-400" />
          Allocation Lifecycle History
        </h3>

        <div className="space-y-4 pl-4 border-l-2 border-slate-800">
          {allocation.history?.map((entry) => (
            <div key={entry.id} className="relative">
              <span className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-indigo-500 border-2 border-slate-950" />
              <div className="text-xs font-semibold text-white">
                {entry.action}
              </div>
              <div className="text-[11px] text-slate-300 mt-0.5">
                {entry.description}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                {entry.timestamp.split("T")[0]} • Performed by{" "}
                {entry.performedBy}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Transfer Dialog */}
      <Dialog
        open={transferModalOpen}
        onOpenChange={setTransferModalOpen}
        title="Hostel Room Transfer"
        description="Transfer resident to another room or bed slot."
      >
        <form onSubmit={handleTransfer} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Target Room Number
              </label>
              <Input
                required
                value={transferForm.roomNumber}
                onChange={(e) =>
                  setTransferForm({
                    ...transferForm,
                    roomNumber: e.target.value,
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Target Bed
              </label>
              <Input
                required
                value={transferForm.bedNumber}
                onChange={(e) =>
                  setTransferForm({
                    ...transferForm,
                    bedNumber: e.target.value,
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Transfer Justification
            </label>
            <Input
              required
              value={transferForm.reason}
              onChange={(e) =>
                setTransferForm({ ...transferForm, reason: e.target.value })
              }
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>
          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setTransferModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
            >
              Confirm Transfer
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Vacate Dialog */}
      <Dialog
        open={vacateModalOpen}
        onOpenChange={setVacateModalOpen}
        title="Vacate Bed Slot"
        description="Initiate student checkout, no-dues clearance, and key return."
      >
        <div className="space-y-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Checkout Reason
            </label>
            <Input
              value={vacateReason}
              onChange={(e) => setVacateReason(e.target.value)}
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>
          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setVacateModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button
              onClick={handleVacate}
              className="bg-rose-600 hover:bg-rose-500 text-white text-xs"
            >
              Confirm & Vacate
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
