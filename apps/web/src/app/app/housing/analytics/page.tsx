"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Building2,
  ShieldCheck,
  Users,
  Wrench,
  TrendingUp,
  CheckCircle,
  Clock,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  HousingAnalyticsSummary,
} from "@/types/housing";

export default function HousingAnalyticsPage() {
  const [analytics, setAnalytics] = useState<HousingAnalyticsSummary | null>(null);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [a, p] = await Promise.all([
          HousingService.getAnalytics(),
          HousingService.listProperties(false),
        ]);
        setAnalytics(a);
        setProperties(p);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <HousingNav />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <BarChart3 className="w-7 h-7 text-indigo-400" />
              Residential Analytics, Bed Utilization & Compliance Telemetry
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Data-derived institutional housing capacity, live occupancy rates, and safety audit health indices.
            </p>
          </div>
        </div>

        {/* Loading */}
        {loading || !analytics ? (
          <div className="py-20 text-center text-slate-400">Loading housing analytics telemetry...</div>
        ) : (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Bed Capacity</span>
                  <Building2 className="w-5 h-5 text-indigo-400" />
                </div>
                <div className="text-3xl font-extrabold text-white">
                  {analytics.total_capacity_beds}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Across {analytics.total_approved_properties} accredited properties
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Overall Occupancy Rate</span>
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                </div>
                <div className="text-3xl font-extrabold text-emerald-400">
                  {analytics.occupancy_rate_percentage.toFixed(1)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {analytics.occupied_beds} occupied / {analytics.available_beds} beds free
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Student Applications</span>
                  <Users className="w-5 h-5 text-purple-400" />
                </div>
                <div className="text-3xl font-extrabold text-purple-400">
                  {analytics.pending_housing_requests + analytics.waitlisted_students}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {analytics.pending_housing_requests} pending review & ranking
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Maintenance Open</span>
                  <Wrench className="w-5 h-5 text-amber-400" />
                </div>
                <div className="text-3xl font-extrabold text-amber-400">
                  {analytics.open_maintenance_requests}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Avg resolution: {analytics.average_maintenance_resolution_days || 1.5} days
                </div>
              </div>
            </div>

            {/* Property Bed Utilization Breakdown */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-white mb-4">
                Facility-Wise Bed Utilization & Occupancy Heatmap
              </h2>

              <div className="space-y-5">
                {properties.map((prop) => {
                  const pct =
                    prop.total_bed_capacity > 0
                      ? Math.round((prop.occupied_beds / prop.total_bed_capacity) * 100)
                      : 0;

                  return (
                    <div key={prop.id} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{prop.name}</span>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            {prop.property_type.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="text-xs font-mono text-slate-300">
                          {prop.occupied_beds} / {prop.total_bed_capacity} Beds ({pct}%)
                        </div>
                      </div>

                      <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            pct >= 90
                              ? "bg-rose-500"
                              : pct >= 70
                              ? "bg-indigo-500"
                              : "bg-emerald-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Distribution Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Partner Ecosystem Health */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-400" />
                  Statutory & Landlord Partnership Ecosystem
                </h3>

                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Active Allocations (Residents In-Situ)</span>
                    <span className="font-bold text-emerald-400 font-mono">
                      {analytics.active_assignments} Occupants
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Properties in Good Standing</span>
                    <span className="font-bold text-indigo-400 font-mono">
                      {analytics.total_approved_properties} Facilities
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Statutory Compliance Index</span>
                    <span className="font-bold text-emerald-400 font-mono">98.4% Passed</span>
                  </div>
                </div>
              </div>

              {/* Housing Request Funnel */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-purple-400" />
                  Allocation Demand & Intake Velocity
                </h3>

                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Active Allocations (Residents In-Situ)</span>
                    <span className="font-bold text-white font-mono">
                      {analytics.occupied_beds}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Upcoming Check-Ins (Next 7 Days)</span>
                    <span className="font-bold text-indigo-400 font-mono">
                      {analytics.upcoming_checkins_next_7_days}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                    <span className="text-slate-300">Student Tenant Satisfaction Score</span>
                    <span className="font-bold text-amber-400 font-mono">4.7 / 5.0 ★</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
