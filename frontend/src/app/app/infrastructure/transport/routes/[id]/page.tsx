"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { transportRoutesService } from "@/services/transport-routes.service";
import { transportStopsService } from "@/services/transport-stops.service";
import { transportAllocationsService } from "@/services/transport-allocations.service";
import {
  TransportRoute,
  TransportStop,
  TransportAllocation,
  RouteStatus,
} from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Compass,
  ArrowLeft,
  MapPin,
  Bus,
  Users,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Phone,
  FileText,
  User,
} from "lucide-react";

export default function TransportRouteDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const routeId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [route, setRoute] = useState<TransportRoute | null>(null);
  const [stops, setStops] = useState<TransportStop[]>([]);
  const [allocations, setAllocations] = useState<TransportAllocation[]>([]);
  const [activeTab, setActiveTab] = useState<"stops" | "students" | "crew">(
    "stops",
  );

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [rRes, sRes, aRes] = await Promise.all([
          transportRoutesService.getRouteById(routeId),
          transportStopsService.listStops({ routeId }),
          transportAllocationsService.listTransportAllocations({ routeId }),
        ]);

        if (rRes.success && rRes.data) setRoute(rRes.data);
        if (sRes.success && sRes.data) setStops(sRes.data);
        if (aRes.success && aRes.data) setAllocations(aRes.data);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [routeId]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!route) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">
          Transit Route Not Found
        </h2>
        <Link href="/app/infrastructure/transport/routes">
          <Button variant="outline" className="border-slate-700">
            Back to Routes
          </Button>
        </Link>
      </div>
    );
  }

  const util =
    route.capacity > 0
      ? Math.round((route.allocatedStudents / route.capacity) * 100)
      : 0;

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-6xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/transport/routes"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Routes
        </Link>
      </div>

      {/* Hero Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-md border border-blue-500/20">
                {route.routeCode}
              </span>
              <Badge
                variant="outline"
                className={
                  route.status === RouteStatus.ACTIVE
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }
              >
                {route.status}
              </Badge>
              <span className="text-xs text-slate-400">
                {stops.length} designated boarding stops
              </span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {route.name}
            </h1>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-400 shrink-0" />
              <span>
                {route.startPoint} <strong className="text-white">↔</strong>{" "}
                {route.endPoint}
              </span>
            </p>
          </div>

          {/* Quick Metrics Badge */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 min-w-[260px] space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Pass Occupancy</span>
              <span
                className={`font-semibold ${
                  util >= 90
                    ? "text-red-400"
                    : util >= 75
                      ? "text-amber-400"
                      : "text-emerald-400"
                }`}
              >
                {util}% Utilized
              </span>
            </div>
            <div className="text-lg font-bold text-white font-mono">
              {route.allocatedStudents} / {route.capacity} seats
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  util >= 90
                    ? "bg-red-500"
                    : util >= 75
                      ? "bg-amber-500"
                      : "bg-blue-500"
                }`}
                style={{ width: `${Math.min(util, 100)}%` }}
              />
            </div>
            <div className="text-[11px] text-slate-500 flex justify-between pt-1">
              <span>
                Available: {route.capacity - route.allocatedStudents} seats
              </span>
              <span>
                Morning:{" "}
                {route.morningDeparture || route.morningStartTime || "07:15 AM"}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 mt-8 gap-6">
          <button
            onClick={() => setActiveTab("stops")}
            className={`pb-3 text-sm font-medium transition-colors flex items-center gap-2 relative ${
              activeTab === "stops"
                ? "text-blue-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <MapPin className="w-4 h-4" />
            Route Sequence ({stops.length} Stops)
            {activeTab === "stops" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("students")}
            className={`pb-3 text-sm font-medium transition-colors flex items-center gap-2 relative ${
              activeTab === "students"
                ? "text-blue-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Users className="w-4 h-4" />
            Allocated Students ({allocations.length})
            {activeTab === "students" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("crew")}
            className={`pb-3 text-sm font-medium transition-colors flex items-center gap-2 relative ${
              activeTab === "crew"
                ? "text-blue-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Bus className="w-4 h-4" />
            Vehicle & Driver Assigned
            {activeTab === "crew" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
        </div>
      </div>

      {/* Tab 1: Stops Sequence */}
      {activeTab === "stops" && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-400" />
              Stops & Boarding Schedule
            </h2>
            <span className="text-xs text-slate-400">
              Sequential Corridor Progression
            </span>
          </div>

          <div className="relative pl-8 space-y-8 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
            {stops
              .sort((a, b) => a.sequence - b.sequence)
              .map((stop, idx) => (
                <div key={stop.id} className="relative group">
                  {/* Sequence Node Number */}
                  <div className="absolute -left-[30px] top-0 w-6 h-6 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center text-[10px] font-bold text-blue-400 group-hover:scale-110 transition-transform">
                    {stop.sequence}
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2.5">
                        <Link
                          href={`/app/infrastructure/transport/stops/${stop.id}`}
                          className="font-semibold text-white hover:text-blue-300 text-sm"
                        >
                          {stop.name}
                        </Link>
                        <span className="font-mono text-[11px] text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                          {stop.code}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>Landmark: {stop.landmark}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 text-xs shrink-0">
                      <div className="space-y-0.5 text-right md:text-left">
                        <span className="text-slate-500 block text-[10px] uppercase">
                          Boarding Times
                        </span>
                        <span className="font-mono text-white">
                          AM: {stop.pickupTime}
                        </span>
                        <span className="text-slate-400 mx-1">|</span>
                        <span className="font-mono text-slate-300">
                          PM: {stop.dropTime}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-center min-w-[70px]">
                        <span className="block text-sm font-bold text-blue-400">
                          {stop.studentCount}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          Passes
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Tab 2: Allocated Students */}
      {activeTab === "students" && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-violet-400" />
                Active Bus Pass Holders
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Students registered and cleared for this transit corridor
              </p>
            </div>
            <Link href="/app/infrastructure/transport/allocations">
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 text-xs"
              >
                Manage Passes
              </Button>
            </Link>
          </div>

          <div className="space-y-3">
            {allocations.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-sm">
                No active student allocations recorded for this route.
              </div>
            ) : (
              allocations.map((alloc) => (
                <div
                  key={alloc.id}
                  className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <Link
                        href={`/app/students/${alloc.studentId}`}
                        className="font-medium text-white hover:text-blue-300 text-sm flex items-center gap-1.5"
                      >
                        <User className="w-3.5 h-3.5 text-blue-400" />
                        {alloc.studentName}
                      </Link>
                      <span className="font-mono text-xs text-slate-400">
                        ({alloc.registerNumber})
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 flex items-center gap-2">
                      <span>
                        Stop:{" "}
                        <strong className="text-slate-300">
                          {alloc.stopName}
                        </strong>
                      </span>
                      <span>•</span>
                      <span>
                        Seat:{" "}
                        <strong className="text-white">
                          #{alloc.seatNumber || "General"}
                        </strong>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
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
                    <Badge
                      variant="outline"
                      className="bg-blue-500/10 text-blue-400 border-blue-500/20"
                    >
                      Pass Active
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Vehicle & Driver */}
      {activeTab === "crew" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Vehicle Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Bus className="w-4 h-4 text-emerald-400" />
                Assigned Vehicle
              </h2>
              {route.vehicleId && (
                <Link
                  href={`/app/infrastructure/transport/vehicles/${route.vehicleId}`}
                  className="text-xs text-blue-400 hover:underline"
                >
                  View Vehicle Record
                </Link>
              )}
            </div>

            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <div>
                <span className="text-xs text-slate-500 block mb-0.5">
                  Registration Number
                </span>
                <span className="font-mono text-base font-bold text-white">
                  {route.vehicleNumber || "Unassigned"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Seating Capacity</span>
                  <span className="font-semibold text-slate-200">
                    {route.capacity} Seats
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Fleet Type</span>
                  <span className="font-semibold text-slate-200">
                    Heavy Passenger Bus
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Driver Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-cyan-400" />
                Assigned Driver
              </h2>
              {route.driverId && (
                <Link
                  href={`/app/infrastructure/transport/drivers/${route.driverId}`}
                  className="text-xs text-blue-400 hover:underline"
                >
                  View Driver Dossier
                </Link>
              )}
            </div>

            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <div>
                <span className="text-xs text-slate-500 block mb-0.5">
                  Driver Full Name
                </span>
                <span className="font-medium text-base text-white">
                  {route.driverName || "Unassigned"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Contact Phone</span>
                  <span className="font-mono text-slate-200 flex items-center gap-1 mt-0.5">
                    <Phone className="w-3 h-3 text-slate-400" />
                    {route.driverPhone || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Duty Status</span>
                  <Badge
                    variant="outline"
                    className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 mt-0.5"
                  >
                    On Duty
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
