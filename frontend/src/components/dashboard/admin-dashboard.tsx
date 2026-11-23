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
    <div className="space-y-7">
      {/* Page Title & Institutional Overview */}
      <div className="flex flex-col gap-5 border-b border-slate-200/80 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-amber-900">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            Academic year 2026–2027
          </div>
          <h1 className="text-3xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-[34px]">
            Institutional overview
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            A clear view of academic activity, attendance, finance, and campus operations.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((m, idx) => {
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
              variant="default"
              icon={icons[idx % 4]}
            />
          );
        })}
      </div>

      {/* Main Split Grid: Departmental Performance & Operational Alerts */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Department Performance Table (2 Columns) */}
        <div className="space-y-5 xl:col-span-2">
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
                <table className="w-full min-w-[680px] text-left text-[13px] text-slate-700">
                  <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">
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
                        className="transition-colors hover:bg-amber-50/40"
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
              className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-[0_8px_24px_rgba(16,24,40,0.07)]"
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
              className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-[0_8px_24px_rgba(16,24,40,0.07)]"
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
              className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-[0_8px_24px_rgba(16,24,40,0.07)]"
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
              className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-[0_8px_24px_rgba(16,24,40,0.07)]"
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
        <div className="space-y-5">
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
                  className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-colors hover:border-amber-200"
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
