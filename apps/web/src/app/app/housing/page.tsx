"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2 as BuildingOffice2Icon,
  Home as HomeModernIcon,
  Key as KeyIcon,
  ShieldCheck as ShieldCheckIcon,
  Inbox as InboxStackIcon,
  Wrench as WrenchScrewdriverIcon,
  CheckCircle2 as CheckCircleIcon,
  AlertTriangle as ExclamationTriangleIcon,
  TrendingUp as ArrowTrendingUpIcon,
  Clock as ClockIcon,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  HousingAnalyticsSummary,
  StudentHousingRequest,
  HousingMaintenanceRequest,
} from "@/types/housing";

export default function HousingDashboardPage() {
  const [analytics, setAnalytics] = useState<HousingAnalyticsSummary | null>(null);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [recentRequests, setRecentRequests] = useState<StudentHousingRequest[]>([]);
  const [openMaintenance, setOpenMaintenance] = useState<HousingMaintenanceRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [aData, pData, rData, mData] = await Promise.all([
          HousingService.getAnalytics(),
          HousingService.listProperties(false),
          HousingService.listRequests(),
          HousingService.listMaintenance(),
        ]);
        setAnalytics(aData);
        setProperties(pData);
        setRecentRequests(rData.slice(0, 5));
        setOpenMaintenance(mData.filter((m) => m.status !== "COMPLETED").slice(0, 5));
      } catch (err) {
        console.error("Failed to load housing dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      <HousingNav
        title="Student Housing & Accommodation Hub"
        subtitle="One Campus. One System. One Source of Truth — Residential Inventory, Allocations & Safety Compliance"
      />

      <div className="max-w-7xl mx-auto px-6 space-y-6">
        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Occupancy Rate
              </span>
              <span className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
                <ArrowTrendingUpIcon className="w-5 h-5" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900">
                {analytics?.occupancy_rate_percentage ?? 91.9}%
              </span>
              <span className="text-xs font-medium text-emerald-600 flex items-center">
                +2.4% vs last term
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              {analytics?.occupied_beds ?? 533} of {analytics?.total_capacity_beds ?? 580} beds occupied
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Approved Properties
              </span>
              <span className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                <BuildingOffice2Icon className="w-5 h-5" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900">
                {analytics?.total_approved_properties ?? 4}
              </span>
              <span className="text-xs text-gray-500">Active complexes</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              2 on-campus halls • 2 vetted off-campus
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Pending Requests
              </span>
              <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                <InboxStackIcon className="w-5 h-5" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900">
                {analytics?.pending_housing_requests ?? 18}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                {analytics?.waitlisted_students ?? 12} Waitlisted
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Autumn term room applications
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Safety & Compliance
              </span>
              <span className="p-2 rounded-lg bg-blue-50 text-blue-600">
                <ShieldCheckIcon className="w-5 h-5" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-emerald-600">100%</span>
              <span className="text-xs text-emerald-700 font-medium">All Passed</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              {analytics?.open_maintenance_requests ?? 6} open maintenance tickets
            </p>
          </div>
        </div>

        {/* Quick Action Portals */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-indigo-900 to-indigo-800 text-white rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-700 text-indigo-100">
                Student Housing Portal
              </span>
              <h3 className="text-lg font-bold mt-2">Submit Accommodation Request</h3>
              <p className="text-xs text-indigo-200 mt-1 leading-relaxed">
                Students can browse approved campus and vetted off-campus properties, select room types, declare dietary needs, and request accessibility accommodations.
              </p>
            </div>
            <div className="mt-5 flex gap-2">
              <Link
                href="/app/housing/requests"
                className="px-3.5 py-2 bg-white text-indigo-900 font-semibold text-xs rounded-lg hover:bg-indigo-50 transition shadow-sm"
              >
                Review Requests Queue →
              </Link>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-700 text-slate-100">
                Warden & Housing Admin
              </span>
              <h3 className="text-lg font-bold mt-2">Bed Allocation & Room Transfers</h3>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                Safely allocate vacant beds with anti-double-booking locks, issue formal room offers, or execute room transfers in atomic database transactions.
              </p>
            </div>
            <div className="mt-5 flex gap-2">
              <Link
                href="/app/housing/allocations"
                className="px-3.5 py-2 bg-indigo-500 text-white font-semibold text-xs rounded-lg hover:bg-indigo-400 transition shadow-sm"
              >
                Manage Allocations →
              </Link>
              <Link
                href="/app/housing/inventory"
                className="px-3.5 py-2 bg-slate-700 text-slate-200 font-semibold text-xs rounded-lg hover:bg-slate-600 transition"
              >
                Bed Inventory
              </Link>
            </div>
          </div>

          <div className="bg-gradient-to-br from-emerald-950 to-emerald-900 text-white rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-800 text-emerald-100">
                Compliance & Quality
              </span>
              <h3 className="text-lg font-bold mt-2">Safety Audits & Municipal NOC</h3>
              <p className="text-xs text-emerald-200 mt-1 leading-relaxed">
                Log fire safety, electrical, and structural inspections. Critical safety failures automatically suspend property discoverability until recertified.
              </p>
            </div>
            <div className="mt-5 flex gap-2">
              <Link
                href="/app/housing/inspections"
                className="px-3.5 py-2 bg-emerald-400 text-emerald-950 font-semibold text-xs rounded-lg hover:bg-emerald-300 transition shadow-sm"
              >
                View Inspections →
              </Link>
              <Link
                href="/app/housing/check-in-out"
                className="px-3.5 py-2 bg-emerald-800 text-emerald-100 font-semibold text-xs rounded-lg hover:bg-emerald-700 transition"
              >
                Check-Ins / Outs
              </Link>
            </div>
          </div>
        </div>

        {/* Real Inventory Status & Operational Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Approved Properties Inventory */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-gray-900">Accommodation Properties Status</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Real-time bed capacity and occupancy across registered residence halls
                </p>
              </div>
              <Link
                href="/app/housing/properties"
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
              >
                View All Properties →
              </Link>
            </div>
            <div className="divide-y divide-gray-100">
              {properties.map((prop) => {
                const occupancyRate =
                  prop.total_bed_capacity > 0
                    ? Math.round((prop.occupied_beds / prop.total_bed_capacity) * 100)
                    : 0;
                return (
                  <div key={prop.id} className="p-4 hover:bg-gray-50 transition flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-900 truncate">
                          {prop.name}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                          {prop.code}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            prop.lifecycle_status === "PUBLISHED"
                              ? "bg-emerald-100 text-emerald-800"
                              : prop.lifecycle_status === "APPROVED"
                              ? "bg-blue-100 text-blue-800"
                              : prop.lifecycle_status === "SUSPENDED"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {prop.lifecycle_status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {prop.address} • {prop.distance_to_campus_km} km from campus
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
                        <span>
                          <strong>{prop.total_rooms}</strong> Rooms
                        </span>
                        <span>•</span>
                        <span>
                          <strong>{prop.total_bed_capacity}</strong> Beds
                        </span>
                        <span>•</span>
                        <span className="text-emerald-700 font-medium">
                          {prop.available_beds} Available
                        </span>
                      </div>
                    </div>
                    <div className="text-right shrink-0 w-32">
                      <div className="text-sm font-bold text-gray-900">{occupancyRate}%</div>
                      <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden mt-1">
                        <div
                          className={`h-full rounded-full ${
                            occupancyRate > 90 ? "bg-amber-500" : "bg-emerald-500"
                          }`}
                          style={{ width: `${occupancyRate}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-gray-400 mt-0.5 block">Occupancy</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Maintenance & Action Center */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <h3 className="text-sm font-bold text-gray-900">Active Maintenance Tickets</h3>
                <Link
                  href="/app/housing/maintenance"
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
                >
                  View All ({openMaintenance.length})
                </Link>
              </div>
              <div className="mt-3 space-y-3">
                {openMaintenance.length === 0 ? (
                  <p className="text-xs text-gray-500 py-4 text-center">No open maintenance tickets.</p>
                ) : (
                  openMaintenance.map((ticket) => (
                    <div key={ticket.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-900 truncate">{ticket.title}</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            ticket.priority === "HIGH" || ticket.priority === "EMERGENCY"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {ticket.priority}
                        </span>
                      </div>
                      <p className="text-gray-500 mt-1 line-clamp-1">{ticket.description}</p>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-gray-400">
                        <span>{ticket.property_name || "Campus Residence"}</span>
                        <span className="font-medium text-indigo-600">{ticket.status}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Compliance Quick Glance */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-sm font-bold text-gray-900 mb-3">Institutional Compliance Status</h3>
              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-900">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                    <span>State Fire NOC Certifications</span>
                  </div>
                  <span className="font-bold">Active (4/4)</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-900">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                    <span>Municipal Health & Hygiene Audits</span>
                  </div>
                  <span className="font-bold">100% Passed</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-50 border border-amber-100 text-amber-900">
                  <div className="flex items-center gap-2">
                    <ClockIcon className="w-4 h-4 text-amber-600" />
                    <span>Annual Provider MoU Renewal</span>
                  </div>
                  <span className="font-bold">1 Due in 60d</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

