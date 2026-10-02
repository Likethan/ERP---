"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { infrastructureReportsService } from "@/services/infrastructure-reports.service";
import { InfrastructureReportData } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart3,
  Building2,
  BedDouble,
  Bus,
  Wrench,
  Download,
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  TrendingUp,
  Percent,
  Layers,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export default function InfrastructureReportsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<InfrastructureReportData | null>(null);
  const [activeTab, setActiveTab] = useState("hostels");

  const loadReports = useCallback(async () => {
    setLoading(true);
    try {
      const res = await infrastructureReportsService.getInfrastructureReports();
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  if (loading || !data) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const { hostelSummary, transportSummary, facilitiesSummary, maintenanceSummary } = data;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/infrastructure"
              className="text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
            >
              Infrastructure
            </Link>
            <span className="text-xs text-slate-600">/</span>
            <span className="text-xs text-indigo-400 font-medium">Reports & Analytics</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2 mt-1">
            <BarChart3 className="h-6 w-6 text-indigo-400" />
            Infrastructure Operations & Asset Analytics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Institutional capacity utilization, fleet telemetry, facility condition indices, and maintenance SLA compliance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="gap-2 text-xs"
          >
            <Download className="h-4 w-4" /> Export Report (PDF)
          </Button>
        </div>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Hostel Bed Occupancy"
          value={`${Math.round((hostelSummary.occupiedBeds / hostelSummary.totalBeds) * 100)}%`}
          description={`${hostelSummary.occupiedBeds} of ${hostelSummary.totalBeds} beds assigned`}
          icon={<BedDouble className="h-5 w-5 text-indigo-400" />}
          change={{ value: "+4.2%", trend: "up" }}
        />
        <StatCard
          title="Transport Fleet Health"
          value={`${Math.round(
            (transportSummary.vehicleFleetStatus.find((s) => s.status.includes("Active"))?.count || 4) /
              (transportSummary.vehicleFleetStatus.reduce((acc, s) => acc + s.count, 0) || 6) *
              100
          )}%`}
          description="Active fleet routes in service"
          icon={<Bus className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Maintenance SLA Rate"
          value="94%"
          description="Target response within SLA"
          icon={<Clock className="h-5 w-5 text-purple-400" />}
        />
        <StatCard
          title="Total Maintenance Cost"
          value={`₹${((maintenanceSummary?.totalMaintenanceCostInr || 240000) / 100000).toFixed(2)}L`}
          description="Fiscal Term 2026-27"
          icon={<Wrench className="h-5 w-5 text-amber-400" />}
        />
      </div>

      {/* Domain Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        <button
          onClick={() => setActiveTab("hostels")}
          className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors flex items-center gap-2 border-b-2 ${
            activeTab === "hostels"
              ? "text-indigo-400 border-indigo-500 bg-slate-900/60"
              : "text-slate-400 border-transparent hover:text-slate-200"
          }`}
        >
          <BedDouble className="h-4 w-4" /> Residential Halls & Occupancy
        </button>
        <button
          onClick={() => setActiveTab("transport")}
          className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors flex items-center gap-2 border-b-2 ${
            activeTab === "transport"
              ? "text-indigo-400 border-indigo-500 bg-slate-900/60"
              : "text-slate-400 border-transparent hover:text-slate-200"
          }`}
        >
          <Bus className="h-4 w-4" /> Transit Routes & Fleet Capacity
        </button>
        <button
          onClick={() => setActiveTab("facilities")}
          className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors flex items-center gap-2 border-b-2 ${
            activeTab === "facilities"
              ? "text-indigo-400 border-indigo-500 bg-slate-900/60"
              : "text-slate-400 border-transparent hover:text-slate-200"
          }`}
        >
          <Building2 className="h-4 w-4" /> Facilities & SLA Performance
        </button>
      </div>

      {/* Tab 1: Hostels */}
      {activeTab === "hostels" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hostel-wise Capacity Table */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <BedDouble className="h-4 w-4 text-indigo-400" />
                  Hall of Residence Capacity Breakdown
                </h3>
                <span className="text-xs font-mono text-slate-500">{hostelSummary.totalHostels} Halls</span>
              </div>

              <div className="divide-y divide-slate-800 text-xs">
                {hostelSummary.hostelWiseStats.map((h) => (
                  <div key={h.code} className="py-3 first:pt-0 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-white">{h.hostelName}</span>
                      <span className="font-mono text-indigo-400 font-bold">{h.occupancyPercentage}%</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400 text-[11px]">
                      <span>
                        Occupied: <span className="text-white font-mono">{h.occupiedBeds}</span> / {h.totalBeds} beds
                      </span>
                      <span className="text-emerald-400 font-mono">
                        {h.totalBeds - h.occupiedBeds} vacant
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          h.occupancyPercentage >= 95
                            ? "bg-rose-500"
                            : h.occupancyPercentage >= 85
                            ? "bg-indigo-500"
                            : "bg-emerald-500"
                        }`}
                        style={{ width: `${Math.min(100, h.occupancyPercentage)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Resident Program Distribution */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-purple-400" />
                  Resident Demographic by Academic Program
                </h3>
                <span className="text-xs font-mono text-slate-500">{hostelSummary.occupiedBeds} Residents</span>
              </div>

              <div className="space-y-3 text-xs">
                {hostelSummary.programWiseAllocations.map((p) => (
                  <div key={p.programCode} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-slate-300 font-mono">{p.programCode}</span>
                      <span className="font-mono text-white font-semibold">
                        {p.studentCount} students ({p.percentage}%)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500" style={{ width: `${p.percentage}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Monthly Leave Requests Trend */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Calendar className="h-4 w-4 text-emerald-400" />
                Monthly Hostel Gate-pass & Outing Request Trends
              </h3>
              <div className="grid grid-cols-5 gap-2 pt-2">
                {hostelSummary.monthlyLeaveTrends.map((m) => (
                  <div key={m.month} className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-center space-y-1">
                    <span className="text-[10px] text-slate-400 block">{m.month}</span>
                    <span className="text-sm font-bold text-white font-mono block">{m.leaveRequests}</span>
                    <span className="text-[9px] text-emerald-400 font-mono block">{m.approved} approved</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Complaint Resolution Distribution */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-teal-400" />
                Complaint Resolution Rate by Maintenance Category
              </h3>
              <div className="divide-y divide-slate-800 text-xs">
                {hostelSummary.complaintDistribution.map((c) => (
                  <div key={c.category} className="py-2.5 first:pt-0 flex justify-between items-center">
                    <div>
                      <span className="font-medium text-white">{c.category}</span>
                      <span className="text-[11px] text-slate-500 font-mono ml-2">({c.count} complaints)</span>
                    </div>
                    <Badge variant={c.resolvedRate >= 95 ? "success" : "info"}>
                      {c.resolvedRate}% Resolved
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Transport */}
      {activeTab === "transport" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Route Capacity Utilization */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Bus className="h-4 w-4 text-emerald-400" />
                  Bus Route Utilization & Passenger Seat Load
                </h3>
                <span className="text-xs font-mono text-slate-500">4 Active Circuits</span>
              </div>

              <div className="divide-y divide-slate-800 text-xs">
                {transportSummary.routeUtilization.map((r) => (
                  <div key={r.routeCode} className="py-3 first:pt-0 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-mono font-bold text-indigo-400 mr-2">{r.routeCode}</span>
                        <span className="font-medium text-white">{r.routeName}</span>
                      </div>
                      <span className="font-mono text-emerald-400 font-bold">{r.utilizationPercentage}%</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400 text-[11px]">
                      <span>
                        Boarding: <span className="text-white font-mono">{r.allocated}</span> / {r.capacity} seats
                      </span>
                      <span className="text-slate-500 font-mono">
                        {r.capacity - r.allocated} seats vacant
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          r.utilizationPercentage >= 95 ? "bg-rose-500" : "bg-emerald-500"
                        }`}
                        style={{ width: `${r.utilizationPercentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Fleet Status & Top Boarding Stops */}
            <div className="space-y-6">
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-purple-400" />
                  Vehicle Fleet Readiness & Deployment
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {transportSummary.vehicleFleetStatus.map((v) => (
                    <div key={v.status} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-center">
                      <span className="text-xl font-bold font-mono text-white block">{v.count}</span>
                      <span className="text-[11px] text-slate-400 block mt-1">{v.status}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-rose-400" />
                  Top Boarding Hubs by Student Volume
                </h3>
                <div className="divide-y divide-slate-800 text-xs">
                  {transportSummary.stopWiseStudentDistribution.slice(0, 5).map((s) => (
                    <div key={s.stopName} className="py-2 first:pt-0 flex justify-between items-center">
                      <div>
                        <span className="text-white font-medium">{s.stopName}</span>
                        <span className="text-slate-500 font-mono text-[10px] ml-2">({s.routeCode})</span>
                      </div>
                      <span className="font-mono text-indigo-400 font-bold">{s.studentCount} students</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Facilities */}
      {activeTab === "facilities" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 text-center">
              <span className="text-xs text-slate-400">Total Registered Facilities</span>
              <p className="text-3xl font-bold text-white font-mono">{facilitiesSummary.totalFacilities}</p>
              <span className="text-[11px] text-emerald-400 block">All main campus blocks cataloged</span>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 text-center">
              <span className="text-xs text-slate-400">Under Repair / Maintenance</span>
              <p className="text-3xl font-bold text-amber-400 font-mono">
                {maintenanceSummary?.inProgressRequests || 1}
              </p>
              <span className="text-[11px] text-slate-500 block">Active civil & HVAC work</span>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 text-center">
              <span className="text-xs text-slate-400">SLA Adherence Ratio</span>
              <p className="text-3xl font-bold text-purple-400 font-mono">
                94%
              </p>
              <span className="text-[11px] text-slate-500 block">SLA resolution benchmark met</span>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Building2 className="h-4 w-4 text-indigo-400" />
              Institutional Estate Governance & Work Order Recommendations
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                <span className="font-semibold text-emerald-400 block">Auditorium & Sports Complex Scheduling</span>
                <p className="leading-relaxed text-slate-400">
                  Peak utilization occurs between October and November during national technical symposiums and university fests. Preventive HVAC servicing should be scheduled during end-semester examination breaks.
                </p>
              </div>

              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                <span className="font-semibold text-purple-400 block">High Performance Computing Lab Maintenance</span>
                <p className="leading-relaxed text-slate-400">
                  Precision AC units and UPS battery banks in Turing AI Lab require quarterly thermal load audits. Contractor SLA contracts should be renewed prior to academic term start.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
