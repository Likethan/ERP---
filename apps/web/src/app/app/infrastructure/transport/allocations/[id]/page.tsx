"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { transportAllocationsService } from "@/services/transport-allocations.service";
import { TransportAllocation, TransportAllocationStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ShieldCheck,
  ArrowLeft,
  User,
  Compass,
  MapPin,
  Bus,
  CreditCard,
  QrCode,
  Calendar,
  Clock,
  Printer,
  XCircle,
} from "lucide-react";

export default function TransportAllocationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const allocId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [alloc, setAlloc] = useState<TransportAllocation | null>(null);

  const loadAlloc = async () => {
    setLoading(true);
    try {
      const res = await transportAllocationsService.getAllocationById(allocId);
      if (res.success && res.data) {
        setAlloc(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlloc();
  }, [allocId]);

  const handleCancelPass = async () => {
    if (!alloc) return;
    await transportAllocationsService.cancelTransportAllocation(alloc.id, "Student requested hostel relocation");
    loadAlloc();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!alloc) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Transport Pass Not Found</h2>
        <Link href="/app/infrastructure/transport/allocations">
          <Button variant="outline" className="border-slate-700">
            Back to Passes
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/transport/allocations"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Student Passes
        </Link>
      </div>

      {/* Digital Transit Pass Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 rounded-3xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden shadow-2xl">
        {/* Pass Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Bus className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider block">
                Official CampusOS Boarding Pass
              </span>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Academic Year 2026 – 2027
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={
                alloc.status === TransportAllocationStatus.ACTIVE
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-red-500/10 text-red-400 border-red-500/20"
              }
            >
              {alloc.status}
            </Badge>
            <Badge
              variant="outline"
              className={
                alloc.feeStatus === "PAID"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }
            >
              Fee: {alloc.feeStatus}
            </Badge>
          </div>
        </div>

        {/* Student Profile Row */}
        <div className="py-6 border-b border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-1">
            <span className="text-xs text-slate-500 uppercase tracking-wider block">
              Passenger Name
            </span>
            <Link
              href={`/app/students/${alloc.studentId}`}
              className="text-base font-bold text-white hover:text-indigo-300 flex items-center gap-1.5"
            >
              <User className="w-4 h-4 text-indigo-400" />
              {alloc.studentName}
            </Link>
            <span className="font-mono text-xs text-slate-400 block">{alloc.registerNumber}</span>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-slate-500 uppercase tracking-wider block">
              Assigned Seat
            </span>
            <div className="text-2xl font-mono font-bold text-indigo-400">
              #{alloc.seatNumber || "General"}
            </div>
            <span className="text-xs text-slate-400">Reserved Window/Aisle</span>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-slate-500 uppercase tracking-wider block">
              Assigned Bus
            </span>
            <div className="text-base font-mono font-bold text-white">
              {alloc.vehicleNumber || "KA-04-E-1892"}
            </div>
            <span className="text-xs text-slate-400">Main Route Transit</span>
          </div>
        </div>

        {/* Route & Boarding Stop */}
        <div className="py-6 border-b border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1">
            <span className="text-xs text-slate-500 uppercase tracking-wider block">
              Transit Route Corridor
            </span>
            <div className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                {alloc.routeCode || "R-01"}
              </span>
              <span>{alloc.routeName}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-slate-500 uppercase tracking-wider block">
              Boarding Stop Landmark
            </span>
            <div className="text-sm font-semibold text-white flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>{alloc.stopName}</span>
            </div>
          </div>
        </div>

        {/* Pass Actions */}
        <div className="pt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <QrCode className="w-4 h-4 text-slate-400" />
            <span>Digital verification pass ID: {alloc.id}</span>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => window.print()}
              className="border-slate-700 text-slate-300 hover:text-white gap-2 text-xs"
            >
              <Printer className="w-4 h-4" />
              Print Pass
            </Button>

            {alloc.status === TransportAllocationStatus.ACTIVE && (
              <Button
                variant="outline"
                onClick={handleCancelPass}
                className="border-red-500/30 text-red-400 hover:bg-red-500/10 gap-2 text-xs"
              >
                <XCircle className="w-4 h-4" />
                Cancel Pass
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
