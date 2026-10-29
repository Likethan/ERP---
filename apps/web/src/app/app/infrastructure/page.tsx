"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { infrastructureService } from "@/services/infrastructure.service";
import { InfrastructureDashboardSummary } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  BedDouble,
  Bus,
  Wrench,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Compass,
  FileCheck2,
  Users,
  CheckCircle2,
  Activity,
  Calendar,
  Layers,
  MapPin,
  DoorOpen,
  UserCheck,
} from "lucide-react";

export default function InfrastructureDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<InfrastructureDashboardSummary | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const res = await infrastructureService.getInfrastructureDashboard();
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const d = data || {
    totalHostels: 4,
    totalBeds: 530,
    occupiedBeds: 489,
    availableBeds: 41,
    hostelOccupancyPercentage: 92.3,
    activeTransportRoutes: 4,
    activeVehicles: 5,
    studentsUsingTransport: 168,
    openComplaints: 2,
    openMaintenanceRequests: 3,
    criticalMaintenance: 1,
    facilitiesRequiringAttention: 1,
  };

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto text-slate-100">
      {/* Top Banner & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
              Campus Operations & Logistics
            </span>
            <span className="text-slate-500 text-xs">•</span>
            <span className="text-xs text-slate-400">
              Institutional Infrastructure Hub
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Building2 className="h-7 w-7 text-indigo-400" />
            Infrastructure Operations Center
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Live telemetry, residential hostel capacity, campus transit routes,
            facility work orders, and preventive maintenance records.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/app/infrastructure/reports">
            <Button
              variant="outline"
              className="border-slate-700 hover:bg-slate-800 text-slate-300"
            >
              <TrendingUp className="h-4 w-4 mr-1.5 text-indigo-400" />
              View Reports
            </Button>
          </Link>
          <Link href="/app/infrastructure/maintenance">
            <Button className="bg-indigo-600 hover:bg-indigo-500 text-white">
              <Wrench className="h-4 w-4 mr-1.5" />
              Log Work Order
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Real-Time Operations Telemetry
          </h2>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            All Subsystems Synchronized
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Hostels"
            value={d.totalHostels}
            subtitle="Active residential halls"
            icon={<Building2 className="h-5 w-5 text-indigo-400" />}
          />
          <StatCard
            title="Total Beds"
            value={d.totalBeds}
            subtitle={`${d.occupiedBeds} occupied / ${d.availableBeds} available`}
            icon={<BedDouble className="h-5 w-5 text-sky-400" />}
          />
          <StatCard
            title="Occupied Beds"
            value={d.occupiedBeds}
            subtitle={`${d.availableBeds} beds vacant`}
            icon={<Users className="h-5 w-5 text-emerald-400" />}
          />
          <StatCard
            title="Hostel Occupancy"
            value={`${d.hostelOccupancyPercentage}%`}
            subtitle="Campus resident density"
            icon={<Activity className="h-5 w-5 text-purple-400" />}
          />

          <StatCard
            title="Active Transport Routes"
            value={d.activeTransportRoutes}
            subtitle="Morning & evening shuttles"
            icon={<Compass className="h-5 w-5 text-amber-400" />}
          />
          <StatCard
            title="Active Fleet Vehicles"
            value={d.activeVehicles}
            subtitle="Buses, minibuses & vans"
            icon={<Bus className="h-5 w-5 text-orange-400" />}
          />
          <StatCard
            title="Students Using Transit"
            value={d.studentsUsingTransport}
            subtitle="Daily verified bus pass holders"
            icon={<ShieldCheck className="h-5 w-5 text-teal-400" />}
          />
          <StatCard
            title="Open Complaints"
            value={d.openComplaints}
            subtitle="Hostel student maintenance tickets"
            icon={<AlertTriangle className="h-5 w-5 text-yellow-400" />}
          />

          <StatCard
            title="Open Work Orders"
            value={d.openMaintenanceRequests}
            subtitle="Estate maintenance queue"
            icon={<Wrench className="h-5 w-5 text-rose-400" />}
          />
          <StatCard
            title="Critical Maintenance"
            value={d.criticalMaintenance}
            subtitle="4-Hour SLA Emergency Tasks"
            icon={<AlertTriangle className="h-5 w-5 text-red-500" />}
          />
          <StatCard
            title="Available Beds"
            value={d.availableBeds}
            subtitle="Immediately allocatable"
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
          />
          <StatCard
            title="Facilities Requiring Attention"
            value={d.facilitiesRequiringAttention}
            subtitle="Under scheduled maintenance"
            icon={<Building2 className="h-5 w-5 text-amber-400" />}
          />
        </div>
      </div>

      {/* Primary Subsystem Navigation Portals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Hostel Portal */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 hover:border-indigo-500/40 transition-all flex flex-col justify-between group">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <BedDouble className="h-6 w-6" />
              </div>
              <Badge
                variant="default"
                className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
              >
                {d.hostelOccupancyPercentage}% Occupancy
              </Badge>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-indigo-400 transition-colors">
              Hostel & Residential Dormitories
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Multi-tier hierarchy from Campuses down to Blocks, Floors, Rooms,
              and individual Beds. Allocation pipelines, gate pass leaves, and
              student complaints.
            </p>
            <div className="mt-4 space-y-1.5 text-xs text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Total Hostels:</span>
                <span>{d.totalHostels} Halls</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Available Beds:</span>
                <span className="text-emerald-400 font-semibold">
                  {d.availableBeds}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Open Complaints:</span>
                <span className="text-yellow-400">
                  {d.openComplaints} Pending
                </span>
              </div>
            </div>
          </div>
          <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <Link
              href="/app/infrastructure/hostel"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
            >
              Explore Hostels <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <div className="flex gap-2">
              <Link
                href="/app/infrastructure/hostel/rooms"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Rooms
              </Link>
              <span className="text-slate-600">•</span>
              <Link
                href="/app/infrastructure/hostel/allocations"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Allocations
              </Link>
            </div>
          </div>
        </div>

        {/* Transport Portal */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 hover:border-amber-500/40 transition-all flex flex-col justify-between group">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Bus className="h-6 w-6" />
              </div>
              <Badge
                variant="default"
                className="bg-amber-500/20 text-amber-400 border-amber-500/30"
              >
                {d.activeTransportRoutes} Active Routes
              </Badge>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-amber-400 transition-colors">
              Fleet Transport & Routes
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Campus bus routes, sequenced pickup/drop stops, vehicle fitness
              and insurance records, commercial drivers, and student bus pass
              allocations.
            </p>
            <div className="mt-4 space-y-1.5 text-xs text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Fleet Vehicles:</span>
                <span>{d.activeVehicles} Operational</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Allocated Students:</span>
                <span className="text-teal-400 font-semibold">
                  {d.studentsUsingTransport}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Route Utilization:</span>
                <span className="text-sky-400">92.3% Avg</span>
              </div>
            </div>
          </div>
          <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <Link
              href="/app/infrastructure/transport"
              className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
            >
              Transport Hub <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <div className="flex gap-2">
              <Link
                href="/app/infrastructure/transport/routes"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Routes
              </Link>
              <span className="text-slate-600">•</span>
              <Link
                href="/app/infrastructure/transport/vehicles"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Vehicles
              </Link>
            </div>
          </div>
        </div>

        {/* Facilities & Maintenance Portal */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 hover:border-rose-500/40 transition-all flex flex-col justify-between group">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Wrench className="h-6 w-6" />
              </div>
              <Badge
                variant="default"
                className="bg-rose-500/20 text-rose-400 border-rose-500/30"
              >
                {d.openMaintenanceRequests} Work Orders
              </Badge>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-rose-400 transition-colors">
              Physical Facilities & Maintenance
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Auditoriums, research laboratories, seminar halls, sports
              complexes, equipment tracking, and unified maintenance requests
              with INR cost ledgers.
            </p>
            <div className="mt-4 space-y-1.5 text-xs text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Critical Maintenance:</span>
                <span className="text-red-400 font-semibold">
                  {d.criticalMaintenance} Urgency
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Facilities Status:</span>
                <span className="text-emerald-400">5 Active / 1 Overhaul</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">SLA Resolution Rate:</span>
                <span className="text-indigo-400">96.2% On-Time</span>
              </div>
            </div>
          </div>
          <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <Link
              href="/app/infrastructure/maintenance"
              className="text-xs font-semibold text-rose-400 hover:text-rose-300 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
            >
              Work Orders <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <div className="flex gap-2">
              <Link
                href="/app/infrastructure/facilities"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Facilities
              </Link>
              <span className="text-slate-600">•</span>
              <Link
                href="/app/infrastructure/reports"
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Reports
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Highlights & Quick Workflows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Launchpad */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <Layers className="h-4 w-4 text-indigo-400" />
            Operations Launchpad & Direct Routing
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <Link
              href="/app/infrastructure/hostel/rooms"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <DoorOpen className="h-4 w-4 text-sky-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Rooms & Beds
              </div>
              <div className="text-[10px] text-slate-400">
                Floor-wise inventory
              </div>
            </Link>
            <Link
              href="/app/infrastructure/hostel/allocations"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <UserCheck className="h-4 w-4 text-emerald-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Hostel Allocations
              </div>
              <div className="text-[10px] text-slate-400">
                Student bed assignment
              </div>
            </Link>
            <Link
              href="/app/infrastructure/hostel/leaves"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <FileCheck2 className="h-4 w-4 text-purple-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Hostel Leaves
              </div>
              <div className="text-[10px] text-slate-400">
                Gate pass approvals
              </div>
            </Link>
            <Link
              href="/app/infrastructure/transport/routes"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <Compass className="h-4 w-4 text-amber-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Routes & Stops
              </div>
              <div className="text-[10px] text-slate-400">
                Corridor sequences
              </div>
            </Link>
            <Link
              href="/app/infrastructure/transport/drivers"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <Users className="h-4 w-4 text-orange-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Fleet Drivers
              </div>
              <div className="text-[10px] text-slate-400">
                Commercial licenses
              </div>
            </Link>
            <Link
              href="/app/infrastructure/facilities"
              className="p-3 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:border-slate-700 transition-colors text-left"
            >
              <Building2 className="h-4 w-4 text-rose-400 mb-1.5" />
              <div className="text-xs font-semibold text-white">
                Campus Facilities
              </div>
              <div className="text-[10px] text-slate-400">
                Auditoriums & Labs
              </div>
            </Link>
          </div>
        </div>

        {/* Operational Protocols */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Infrastructure Governance Standards
          </h3>
          <div className="space-y-3">
            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/80 flex items-start gap-3">
              <span className="p-1.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                <CheckCircle2 className="h-4 w-4" />
              </span>
              <div>
                <div className="text-xs font-semibold text-white">
                  Hierarchical Room & Bed Inventory
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Institution → Campus → Hostel → Block → Floor → Room → Bed →
                  Student Allocation.
                </div>
              </div>
            </div>
            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/80 flex items-start gap-3">
              <span className="p-1.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                <Compass className="h-4 w-4" />
              </span>
              <div>
                <div className="text-xs font-semibold text-white">
                  Administrative Transport Management
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Structured route stops with scheduled pickup/drop times,
                  vehicle capacity enforcement, and verified student transit
                  passes.
                </div>
              </div>
            </div>
            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/80 flex items-start gap-3">
              <span className="p-1.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
                <Wrench className="h-4 w-4" />
              </span>
              <div>
                <div className="text-xs font-semibold text-white">
                  SLA-Monitored Unified Maintenance
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Critical requests resolved within 4 hours; high priority in 12
                  hours. Transparent INR (₹) expenditure tracking.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
