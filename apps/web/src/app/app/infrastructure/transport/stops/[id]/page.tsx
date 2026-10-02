"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { transportStopsService } from "@/services/transport-stops.service";
import { transportAllocationsService } from "@/services/transport-allocations.service";
import { TransportStop, TransportAllocation, StopStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  MapPin,
  ArrowLeft,
  Clock,
  Compass,
  Users,
  User,
  CheckCircle2,
  Calendar,
} from "lucide-react";

export default function TransportStopDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const stopId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [stop, setStop] = useState<TransportStop | null>(null);
  const [allocations, setAllocations] = useState<TransportAllocation[]>([]);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [sRes, aRes] = await Promise.all([
          transportStopsService.getStopById(stopId),
          transportAllocationsService.listTransportAllocations({ stopId }),
        ]);

        if (sRes.success && sRes.data) setStop(sRes.data);
        if (aRes.success && aRes.data) setAllocations(aRes.data);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [stopId]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (!stop) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Transit Stop Not Found</h2>
        <Link href="/app/infrastructure/transport/stops">
          <Button variant="outline" className="border-slate-700">
            Back to Stops
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/transport/stops"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Stops
        </Link>
      </div>

      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-md border border-indigo-500/20">
                {stop.code}
              </span>
              <Badge
                variant="outline"
                className={
                  stop.status === StopStatus.ACTIVE
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }
              >
                {stop.status}
              </Badge>
              <span className="text-xs text-slate-400">
                Sequence Order: <strong className="text-white">#{stop.sequence}</strong>
              </span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {stop.name}
            </h1>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <MapPin className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>{stop.landmark || "General pickup boarding zone"}</span>
            </p>
          </div>

          <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="p-3 rounded-lg bg-indigo-500/10">
              <Users className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white font-mono">{allocations.length}</div>
              <div className="text-xs text-slate-400">Boarding Passholders</div>
            </div>
          </div>
        </div>
      </div>

      {/* Stop Metadata & Timings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-3">
          <span className="text-xs text-slate-500 uppercase tracking-wider block">
            Corridor Route
          </span>
          <div className="text-base font-semibold text-white">{stop.routeName}</div>
          <Link
            href={`/app/infrastructure/transport/routes/${stop.routeId}`}
            className="text-xs text-blue-400 hover:underline flex items-center gap-1 font-mono"
          >
            <Compass className="w-3.5 h-3.5" />
            View {stop.routeCode} Route Sequence
          </Link>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-3">
          <span className="text-xs text-slate-500 uppercase tracking-wider block">
            Morning Pickup
          </span>
          <div className="text-xl font-bold text-white font-mono flex items-center gap-2">
            <Clock className="w-5 h-5 text-emerald-400" />
            {stop.pickupTime}
          </div>
          <p className="text-xs text-slate-400">Students advised to assemble 5 mins prior</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-3">
          <span className="text-xs text-slate-500 uppercase tracking-wider block">
            Evening Drop
          </span>
          <div className="text-xl font-bold text-white font-mono flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-400" />
            {stop.dropTime}
          </div>
          <p className="text-xs text-slate-400">Estimated drop timestamp from Campus Gate 2</p>
        </div>
      </div>

      {/* Boarding Students Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-violet-400" />
            Boarding Students at this Stop ({allocations.length})
          </h2>
          <span className="text-xs text-slate-500">Transit Pass Clearances</span>
        </div>

        {allocations.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-sm">
            No students currently allocated to board at this stop.
          </div>
        ) : (
          <div className="space-y-3">
            {allocations.map((alloc) => (
              <div
                key={alloc.id}
                className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div>
                  <Link
                    href={`/app/students/${alloc.studentId}`}
                    className="font-medium text-white hover:text-blue-300 text-sm flex items-center gap-1.5"
                  >
                    <User className="w-3.5 h-3.5 text-blue-400" />
                    {alloc.studentName}
                  </Link>
                  <span className="text-xs font-mono text-slate-400 block mt-0.5">
                    {alloc.registerNumber}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-300 font-mono">
                    Seat: #{alloc.seatNumber || "General"}
                  </span>
                  <Badge
                    variant="outline"
                    className={
                      alloc.feeStatus === "PAID"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }
                  >
                    {alloc.feeStatus}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
