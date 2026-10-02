"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { transportService, TransportDashboardData } from "@/services/transport.service";
import { transportRoutesService } from "@/services/transport-routes.service";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { TransportRoute, TransportVehicle, RouteStatus, VehicleStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Bus,
  Compass,
  MapPin,
  Users,
  Wrench,
  ShieldCheck,
  ArrowRight,
  Plus,
  TrendingUp,
  AlertTriangle,
  Clock,
  Car,
} from "lucide-react";

export default function TransportDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TransportDashboardData | null>(null);
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [dashRes, routesRes, vehiclesRes] = await Promise.all([
          transportService.getTransportDashboard(),
          transportRoutesService.listRoutes(),
          transportVehiclesService.listVehicles(),
        ]);
        if (dashRes.success && dashRes.data) setData(dashRes.data);
        if (routesRes.success && routesRes.data) setRoutes(routesRes.data);
        if (vehiclesRes.success && vehiclesRes.data) setVehicles(vehiclesRes.data);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const statCards = [
    {
      title: "Active Routes",
      value: data?.activeRoutesCount ?? 0,
      icon: Compass,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      sub: "Transit corridors",
      href: "/app/infrastructure/transport/routes",
    },
    {
      title: "Designated Stops",
      value: data?.totalStopsCount ?? 0,
      icon: MapPin,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      border: "border-indigo-500/20",
      sub: "Boarding points",
      href: "/app/infrastructure/transport/stops",
    },
    {
      title: "Fleet Vehicles",
      value: data?.activeVehiclesCount ?? 0,
      icon: Bus,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
      sub: "Operational buses",
      href: "/app/infrastructure/transport/vehicles",
    },
    {
      title: "Drivers on Duty",
      value: data?.activeDriversCount ?? 0,
      icon: Users,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
      sub: "Licensed crew",
      href: "/app/infrastructure/transport/drivers",
    },
    {
      title: "Allocated Students",
      value: data?.studentsAllocatedCount ?? 0,
      icon: ShieldCheck,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
      border: "border-violet-500/20",
      sub: "Active bus passes",
      href: "/app/infrastructure/transport/allocations",
    },
    {
      title: "Fleet Utilization",
      value: `${data?.routeCapacityUtilization ?? 0}%`,
      icon: TrendingUp,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      sub: "Seat occupancy",
      href: "/app/infrastructure/transport/routes",
    },
  ];

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-blue-400 tracking-wider uppercase">
              Campus Fleet Operations
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Transport Management
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time route operations, fleet scheduling, student allocations, and vehicle fitness.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/app/infrastructure/transport/routes">
            <Button variant="outline" className="border-slate-800 text-slate-300 hover:text-white gap-2">
              <Compass className="w-4 h-4 text-blue-400" />
              Routes
            </Button>
          </Link>
          <Link href="/app/infrastructure/transport/vehicles">
            <Button variant="outline" className="border-slate-800 text-slate-300 hover:text-white gap-2">
              <Bus className="w-4 h-4 text-emerald-400" />
              Vehicles
            </Button>
          </Link>
          <Link href="/app/infrastructure/transport/allocations">
            <Button className="bg-blue-600 hover:bg-blue-500 text-white gap-2">
              <Plus className="w-4 h-4" />
              Allocate Pass
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <Link
              key={idx}
              href={card.href}
              className={`p-4 rounded-2xl bg-slate-900/60 border ${card.border} backdrop-blur-sm hover:scale-[1.02] transition-all group block`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-xl ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all" />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">{card.value}</div>
              <div className="text-xs font-medium text-slate-300 mt-0.5">{card.title}</div>
              <div className="text-[11px] text-slate-500 mt-1">{card.sub}</div>
            </Link>
          );
        })}
      </div>

      {/* Main Content Grid: Route Utilization & Fleet Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Route Capacity Overview (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Compass className="w-4 h-4 text-blue-400" />
                  Route Capacity & Utilization
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Seat allocations across active transport corridors
                </p>
              </div>
              <Link
                href="/app/infrastructure/transport/routes"
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                View All Routes <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-4">
              {routes.map((route) => {
                const util = route.capacity > 0 ? Math.round((route.allocatedStudents / route.capacity) * 100) : 0;
                return (
                  <div
                    key={route.id}
                    className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                          {route.routeCode}
                        </span>
                        <Link
                          href={`/app/infrastructure/transport/routes/${route.id}`}
                          className="text-sm font-semibold text-white hover:text-blue-300"
                        >
                          {route.name}
                        </Link>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-slate-400">
                          Vehicle: <strong className="text-white">{route.vehicleNumber || "Unassigned"}</strong>
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
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                      <span>{route.startPoint} → {route.endPoint}</span>
                      <span className="font-mono">
                        {route.allocatedStudents} / {route.capacity} seats ({util}%)
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 rounded-full ${
                          util >= 90
                            ? "bg-red-500"
                            : util >= 75
                            ? "bg-amber-500"
                            : "bg-blue-500"
                        }`}
                        style={{ width: `${Math.min(util, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Submodule Navigator */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link
              href="/app/infrastructure/transport/stops"
              className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-slate-700 group transition-all"
            >
              <div className="w-9 h-9 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-3">
                <MapPin className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300">
                Stops Directory
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Pickup points, GPS landmarks, and stop sequence schedules.
              </p>
            </Link>

            <Link
              href="/app/infrastructure/transport/drivers"
              className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-slate-700 group transition-all"
            >
              <div className="w-9 h-9 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-3">
                <Users className="w-5 h-5 text-cyan-400" />
              </div>
              <h3 className="text-sm font-semibold text-white group-hover:text-cyan-300">
                Driver Crew
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Heavy transport license records, emergency contacts & rosters.
              </p>
            </Link>

            <Link
              href="/app/infrastructure/transport/allocations"
              className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-slate-700 group transition-all"
            >
              <div className="w-9 h-9 rounded-xl bg-violet-500/10 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5 text-violet-400" />
              </div>
              <h3 className="text-sm font-semibold text-white group-hover:text-violet-300">
                Student Passes
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Seat passes, boarding confirmation, and transport fee status.
              </p>
            </Link>
          </div>
        </div>

        {/* Right Column: Fleet Health & Maintenance (1 col) */}
        <div className="space-y-6">
          {/* Vehicles Status */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Bus className="w-4 h-4 text-emerald-400" />
                Fleet Readiness
              </h2>
              <Link
                href="/app/infrastructure/transport/vehicles"
                className="text-xs text-emerald-400 hover:text-emerald-300"
              >
                All Vehicles
              </Link>
            </div>

            <div className="space-y-3">
              {vehicles.map((v) => (
                <Link
                  key={v.id}
                  href={`/app/infrastructure/transport/vehicles/${v.id}`}
                  className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 hover:border-slate-700 block transition-all"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-white">{v.registrationNumber}</span>
                    <Badge
                      variant="outline"
                      className={
                        v.status === VehicleStatus.ACTIVE
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : v.status === VehicleStatus.MAINTENANCE
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }
                    >
                      {v.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>{v.make} {v.model} ({v.type})</span>
                    <span>Cap: {v.capacity} seats</span>
                  </div>
                  {v.fitnessExpiry && (
                    <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-600" />
                      Fitness valid till: {new Date(v.fitnessExpiry).toLocaleDateString("en-IN")}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>

          {/* Quick Notice Card */}
          <div className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              Upcoming Service Audits
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              2 buses (KA-01-EQ-4421, KA-01-EQ-9872) are due for mandatory RTO roadworthiness inspection within 30 days. Maintain logbook records.
            </p>
            <Link href="/app/infrastructure/transport/vehicles">
              <Button size="sm" variant="outline" className="border-amber-500/30 text-amber-300 hover:bg-amber-500/10 text-xs w-full">
                Review Fleet Compliance
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
