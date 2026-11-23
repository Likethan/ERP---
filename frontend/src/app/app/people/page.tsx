"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { peopleService } from "@/services/people.service";
import {
  PeopleSummaryMetrics,
  DepartmentPeopleDistribution,
} from "@/types/people";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import {
  Users,
  GraduationCap,
  Briefcase,
  FileText,
  ArrowRight,
} from "lucide-react";

export default function PeopleOverviewPage() {
  const [metrics, setMetrics] = useState<PeopleSummaryMetrics | null>(null);
  const [departments, setDepartments] = useState<
    DepartmentPeopleDistribution[]
  >([]);

  useEffect(() => {
    async function loadData() {
      const [metricsRes, deptsRes] = await Promise.all([
        peopleService.getMetrics(),
        peopleService.getDepartmentDistribution(),
      ]);
      if (metricsRes.data) setMetrics(metricsRes.data);
      if (deptsRes.data) setDepartments(deptsRes.data);
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <Users className="h-3 w-3" />
            Institutional Governance &bull; People Master Registry
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            People Management & Canonical Directory
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Centralized registry uniting Students, Faculty, Support Staff, and
            Departmental personnel.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/app/students">
            <Button
              variant="primary"
              size="sm"
              rightIcon={<ArrowRight className="h-3.5 w-3.5" />}
            >
              Open Students Directory
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Students"
          value={metrics ? metrics.totalStudents.toLocaleString() : "..."}
          description={`${metrics?.activeStudents || 0} active in good standing`}
          variant="indigo"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="Academic Faculty"
          value={metrics ? metrics.totalFaculty.toLocaleString() : "..."}
          description={`${metrics?.phdFacultyCount || 0} Ph.D. doctorate holders`}
          variant="purple"
          icon={<GraduationCap className="h-5 w-5" />}
        />
        <StatCard
          label="Support Personnel"
          value={metrics ? metrics.totalStaff.toLocaleString() : "..."}
          description={`${metrics?.staffOnDutyToday || 0} active on shift duty`}
          variant="emerald"
          icon={<Briefcase className="h-5 w-5" />}
        />
        <StatCard
          label="Pending Scrutiny"
          value={
            metrics ? metrics.pendingDocumentVerifications.toString() : "..."
          }
          description="Certificates awaiting verification"
          variant="amber"
          icon={<FileText className="h-5 w-5" />}
        />
      </div>

      {/* Navigation Domain Hub */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link href="/app/students" className="block group">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs group-hover:border-indigo-500 group-hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                <Users className="h-6 w-6" />
              </div>
              <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white mt-4">
              Student Master Registry
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Search, filter, admit, and inspect 360-degree profiles, guardians,
              credentials, and achievements.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-indigo-600 dark:text-indigo-400 font-medium">
              <span>{metrics?.totalStudents || 1420} Enrolled Records</span>
              <span>Manage &rarr;</span>
            </div>
          </div>
        </Link>

        <Link href="/app/faculty" className="block group">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs group-hover:border-purple-500 group-hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
                <GraduationCap className="h-6 w-6" />
              </div>
              <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-purple-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white mt-4">
              Professorial Faculty Roster
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Professorial workload allocations, laboratory supervisory duties,
              scholarly publications, and appointments.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-purple-600 dark:text-purple-400 font-medium">
              <span>{metrics?.totalFaculty || 84} Faculty Appointed</span>
              <span>Manage &rarr;</span>
            </div>
          </div>
        </Link>

        <Link href="/app/staff" className="block group">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs group-hover:border-emerald-500 group-hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
                <Briefcase className="h-6 w-6" />
              </div>
              <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-emerald-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white mt-4">
              Support Staff Operations
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Operational shifts, technical laboratory staff, facility
              maintenance, and leave workflows.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              <span>{metrics?.totalStaff || 48} Staff Members</span>
              <span>Manage &rarr;</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Department Distribution Matrix */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Departmental People Distribution
            </h3>
            <p className="text-xs text-slate-500">
              Student cohort enrollment, faculty strength, and administrative
              staff allocated per department.
            </p>
          </div>
        </div>

        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Department Code</th>
              <th className="px-4 py-3">Department Name</th>
              <th className="px-4 py-3">Head of Department</th>
              <th className="px-4 py-3 font-mono">Students</th>
              <th className="px-4 py-3 font-mono">Faculty</th>
              <th className="px-4 py-3 font-mono">Staff</th>
              <th className="px-4 py-3 font-mono text-right">Total Strength</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {departments.map((dept) => (
              <tr
                key={dept.departmentId}
                className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition"
              >
                <td className="px-4 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                  {dept.departmentCode}
                </td>
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                  {dept.departmentName}
                </td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                  {dept.hodName}
                </td>
                <td className="px-4 py-3 font-mono font-semibold">
                  {dept.studentCount}
                </td>
                <td className="px-4 py-3 font-mono text-purple-600 dark:text-purple-400 font-semibold">
                  {dept.facultyCount}
                </td>
                <td className="px-4 py-3 font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                  {dept.staffCount}
                </td>
                <td className="px-4 py-3 font-mono font-bold text-right text-slate-900 dark:text-white">
                  {dept.studentCount + dept.facultyCount + dept.staffCount}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
