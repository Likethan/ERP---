"use client";

import React, { useState } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import {
  BarChart3,
  Download,
  Users,
  Activity,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  FileSpreadsheet,
} from "lucide-react";

export default function ReportsPage() {
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const handleExport = (reportName: string) => {
    setExportNotice(`Exported ${reportName} into institutional compliance archive.`);
    setTimeout(() => setExportNotice(null), 4000);
  };

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Sports Analytics & Institutional Reports
          </h1>
          <p className="text-sm text-slate-500">
            Facility utilization rates, student participation demographics, and athletic compliance telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("Annual Athletics Accreditation Report (PDF)")}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-sm font-medium shadow-sm transition-colors"
          >
            <Download className="w-4 h-4 text-slate-500" />
            Export Executive Report
          </button>
          <button
            onClick={() => handleExport("Medical Clearance & Participation Audit (CSV)")}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Export Compliance Audit
          </button>
        </div>
      </div>

      {exportNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-emerald-800 text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          {exportNotice}
        </div>
      )}

      {/* KPI Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Total Student Athletes</span>
            <Users className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">480 Active</p>
          <p className="text-xs text-emerald-600 font-medium mt-1 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> +18% over previous semester
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Facility Utilization Rate</span>
            <Calendar className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">76.4%</p>
          <p className="text-xs text-slate-500 mt-1">Average 5.8 hours / facility / day</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Training Roll Call Rate</span>
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">89.2%</p>
          <p className="text-xs text-emerald-600 font-medium mt-1">Consistent squad attendance</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Clearance Compliance</span>
            <ShieldCheck className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">98.5%</p>
          <p className="text-xs text-slate-500 mt-1">Only 7 athletes pending checkup</p>
        </div>
      </div>

      {/* Two-Column Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Sport Participation Distribution */}
        <div className="lg:col-span-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900">Discipline Participation Distribution</h2>
            <span className="text-xs text-slate-500 font-medium">Semester 1 - 2026</span>
          </div>

          <div className="space-y-3.5">
            {[
              { sport: "Football", count: 124, pct: 26, color: "bg-indigo-600" },
              { sport: "Cricket", count: 98, pct: 20, color: "bg-blue-600" },
              { sport: "Basketball", count: 86, pct: 18, color: "bg-purple-600" },
              { sport: "Badminton", count: 72, pct: 15, color: "bg-emerald-600" },
              { sport: "Volleyball", count: 54, pct: 11, color: "bg-amber-500" },
              { sport: "Athletics & Track", count: 46, pct: 10, color: "bg-rose-500" },
            ].map((item) => (
              <div key={item.sport} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-800">{item.sport}</span>
                  <span className="text-slate-500">
                    {item.count} athletes ({item.pct}%)
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.pct * 3.5}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Facility Occupancy & Maintenance Metrics */}
        <div className="lg:col-span-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900">Facility Operating Load & Inspection Status</h2>
            <span className="text-xs text-slate-500 font-medium">All Campuses</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-3">Facility</th>
                  <th className="py-2 px-3">Weekly Hours</th>
                  <th className="py-2 px-3">Occupancy</th>
                  <th className="py-2 px-3">Maintenance Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {[
                  {
                    name: "Main Athletics Stadium",
                    hours: "64 hrs",
                    rate: "88%",
                    status: "Operational",
                    statusColor: "text-emerald-700 bg-emerald-50",
                  },
                  {
                    name: "Indoor Badminton Complex",
                    hours: "78 hrs",
                    rate: "94%",
                    status: "Operational",
                    statusColor: "text-emerald-700 bg-emerald-50",
                  },
                  {
                    name: "Varsity Cricket Oval",
                    hours: "42 hrs",
                    rate: "65%",
                    status: "Pitch Mowing",
                    statusColor: "text-amber-700 bg-amber-50",
                  },
                  {
                    name: "Olympic Aquatic Arena",
                    hours: "52 hrs",
                    rate: "70%",
                    status: "Operational",
                    statusColor: "text-emerald-700 bg-emerald-50",
                  },
                  {
                    name: "Fitness Gymnasium",
                    hours: "84 hrs",
                    rate: "96%",
                    status: "Operational",
                    statusColor: "text-emerald-700 bg-emerald-50",
                  },
                ].map((f) => (
                  <tr key={f.name}>
                    <td className="py-2.5 px-3 font-medium text-slate-900">{f.name}</td>
                    <td className="py-2.5 px-3 text-slate-600">{f.hours}</td>
                    <td className="py-2.5 px-3 font-semibold text-indigo-700">{f.rate}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${f.statusColor}`}>
                        {f.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
