"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/ui/stat-card";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { intelligenceService } from "@/services/intelligence.service";
import {
  CampusMetricCard,
  OperationalAlertItem,
  DepartmentKpiItem,
} from "@/mocks/intelligence.mock";
import {
  GraduationCap,
  DollarSign,
  Briefcase,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Building,
  CheckCircle2,
  Calendar,
  Sparkles,
} from "lucide-react";

export function AdminDashboard() {
  const [metrics, setMetrics] = useState<CampusMetricCard[]>([]);
  const [alerts, setAlerts] = useState<OperationalAlertItem[]>([]);
  const [departmentKpis, setDepartmentKpis] = useState<DepartmentKpiItem[]>([]);

  useEffect(() => {
    intelligenceService.getMetrics().then((res) => setMetrics(res.data));
    intelligenceService.getAlerts().then((res) => setAlerts(res.data));
    intelligenceService
      .getDepartmentKpis()
      .then((res) => setDepartmentKpis(res.data));
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title & Institutional Overview */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            Institutional Governance • Academic Year 2026–2027
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            CampusOS Master Executive Overview
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Real-time operations, attendance compliance, financial collections,
            and academic analytics for VSB Campus.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/app/intelligence">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Sparkles className="h-3.5 w-3.5 text-yellow-600" />}
            >
              Campus Intelligence
            </Button>
          </Link>
          <Link href="/app/students">
            <Button variant="primary" size="sm">
              Admissions Registry
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {metrics.map((m, idx) => {
          const variants: Array<"indigo" | "emerald" | "amber" | "sky"> = [
            "indigo",
            "emerald",
            "sky",
            "amber",
          ];
          const icons = [
            <GraduationCap key={1} className="h-4 w-4" />,
            <CheckCircle2 key={2} className="h-4 w-4" />,
            <DollarSign key={3} className="h-4 w-4" />,
            <Briefcase key={4} className="h-4 w-4" />,
          ];
          return (
            <StatCard
              key={m.label}
              label={m.label}
              value={m.value}
              change={m.change}
              description={m.description}
              variant={variants[idx % 4]}
              icon={icons[idx % 4]}
            />
          );
        })}
      </div>

      {/* Main Split Grid: Departmental Performance & Operational Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Department Performance Table (2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>
                  Departmental Performance & Compliance Matrix
                </CardTitle>
                <CardDescription>
                  Cross-domain metrics evaluated against institutional
                  accreditation benchmarks.
                </CardDescription>
              </div>
              <Link href="/app/departments">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-slate-500 hover:text-slate-900"
                >
                  View All <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-700">
                  <thead className="bg-yellow-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-700 border-b border-slate-200">
                    <tr>
                      <th className="px-5 py-3">Department</th>
                      <th className="px-4 py-3">Students</th>
                      <th className="px-4 py-3">Faculty</th>
                      <th className="px-4 py-3">Avg Attendance</th>
                      <th className="px-4 py-3">Avg CGPA</th>
                      <th className="px-4 py-3">Placement</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {departmentKpis.map((dept) => (
                      <tr
                        key={dept.department}
                        className="hover:bg-yellow-50/40 transition-colors"
                      >
                        <td className="px-5 py-3.5 font-medium text-slate-900">
                          {dept.department}
                        </td>
                        <td className="px-4 py-3.5 font-mono text-slate-600">
                          {dept.studentsCount}
                        </td>
                        <td className="px-4 py-3.5 font-mono text-slate-600">
                          {dept.facultyCount}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={
                              dept.avgAttendancePercent >= 85
                                ? "text-emerald-700 font-semibold"
                                : "text-amber-700 font-semibold"
                            }
                          >
                            {dept.avgAttendancePercent}%
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono text-slate-700">
                          {dept.avgCgpa.toFixed(2)}
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant="success">
                            {dept.placementRatePercent}%
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Quick Domain Navigation Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Link
              href="/app/academics/timetable"
              className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/30 transition-all text-left shadow-xs group"
            >
              <Calendar className="h-4 w-4 text-yellow-600 mb-2" />
              <div className="text-xs font-semibold text-slate-900 group-hover:text-yellow-700">
                Master Timetable
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Hall & Room slots
              </div>
            </Link>

            <Link
              href="/app/examinations/results"
              className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/30 transition-all text-left shadow-xs group"
            >
              <TrendingUp className="h-4 w-4 text-emerald-600 mb-2" />
              <div className="text-xs font-semibold text-slate-900 group-hover:text-emerald-700">
                Exam Results
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                GPA & Rank lists
              </div>
            </Link>

            <Link
              href="/app/finance/invoices"
              className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/30 transition-all text-left shadow-xs group"
            >
              <DollarSign className="h-4 w-4 text-amber-600 mb-2" />
              <div className="text-xs font-semibold text-slate-900 group-hover:text-amber-700">
                Fee Ledger
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Dues & receipts
              </div>
            </Link>

            <Link
              href="/app/hostel"
              className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/30 transition-all text-left shadow-xs group"
            >
              <Building className="h-4 w-4 text-purple-600 mb-2" />
              <div className="text-xs font-semibold text-slate-900 group-hover:text-purple-700">
                Hostels & Transport
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Beds & fleet routes
              </div>
            </Link>
          </div>
        </div>

        {/* Operational Alerts & System Signals (1 Column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                Operational System Alerts
              </CardTitle>
              <CardDescription>
                Urgent institutional attention items requiring administrative
                intervention.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-300 hover:bg-yellow-50/20 transition-all space-y-2 shadow-xs"
                >
                  <div className="flex items-center justify-between">
                    <Badge
                      variant={
                        alert.level === "CRITICAL"
                          ? "destructive"
                          : alert.level === "WARNING"
                            ? "warning"
                            : "info"
                      }
                      dot
                    >
                      {alert.level}
                    </Badge>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {alert.timestamp}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-900">
                    {alert.title}
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {alert.message}
                  </p>
                  {alert.actionHref && (
                    <div className="pt-1">
                      <Link
                        href={alert.actionHref}
                        className="text-[11px] font-medium text-yellow-700 hover:text-yellow-800 inline-flex items-center gap-1"
                      >
                        {alert.actionText || "Inspect"}{" "}
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
