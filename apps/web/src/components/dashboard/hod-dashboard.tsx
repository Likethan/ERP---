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
import { academicsService } from "@/services/academics.service";
import { facultyService } from "@/services/faculty.service";
import { DepartmentItem } from "@/mocks/academics.mock";
import { FacultyDetailView } from "@/types/domain";
import {
  Building,
  Users,
  GraduationCap,
  CheckCircle2,
  ArrowRight,
  FileSpreadsheet,
  BookOpen,
  Award,
  ShieldCheck,
  Layers,
  FileText,
  Calendar,
} from "lucide-react";

export function HodDashboard() {
  const [dept, setDept] = useState<DepartmentItem | null>(null);
  const [facultyList, setFacultyList] = useState<FacultyDetailView[]>([]);

  useEffect(() => {
    academicsService.getDepartments().then((res) => {
      const cse = res.data.find((d) => d.code === "CSE") || res.data[0];
      setDept(cse);
    });
    facultyService.list("Computer Science").then((res) => {
      setFacultyList(res.data);
    });
  }, []);

  return (
    <div className="space-y-6">
      {/* HOD Header Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Departmental Leadership Workspace • CSE
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Department of Computer Science & Engineering
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Head of Department: Dr. K. S. Anand • 720 Students • 28 Faculty
            Members
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/curricula">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            >
              Curriculum Scheme
            </Button>
          </Link>
          <Link href="/app/attendance">
            <Button variant="primary" size="sm">
              Attendance Trends
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total CSE Students"
          value={dept?.studentCount || 720}
          description="Across B.Tech & M.Tech schemes"
          variant="indigo"
          icon={<GraduationCap className="h-4 w-4" />}
        />
        <StatCard
          label="Department Faculty"
          value={dept?.facultyCount || 28}
          description="Ph.D. / M.Tech qualified professors"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Average Attendance"
          value="88.4%"
          change={{ value: "+2.1% this week", trend: "up" }}
          description="18 students flagged under 75%"
          variant="sky"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Accredited Placement"
          value="92.5%"
          change={{ value: "Rank 1 in College", trend: "up" }}
          description="Highest offer: ₹24.0 LPA (Microsoft)"
          variant="amber"
          icon={<Building className="h-4 w-4" />}
        />
      </div>

      {/* Department Faculty Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Department Faculty Teaching Workload</CardTitle>
            <CardDescription>
              Current semester course allocations, student counts, and class
              load hours.
            </CardDescription>
          </div>
          <Link href="/app/faculty">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-500 hover:text-slate-900"
            >
              Full Faculty Directory <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-700">
              <thead className="bg-yellow-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-700 border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">Faculty Member</th>
                  <th className="px-4 py-3">Designation</th>
                  <th className="px-4 py-3">Specialization</th>
                  <th className="px-4 py-3">Weekly Hours</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {facultyList.map((f) => (
                  <tr
                    key={f.id}
                    className="hover:bg-yellow-50/40 transition-colors"
                  >
                    <td className="px-5 py-3.5 font-medium text-slate-900">
                      <div>
                        {f.firstName} {f.lastName}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {f.employeeCode}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-slate-700">
                      {f.designation}
                    </td>
                    <td className="px-4 py-3.5 text-slate-600 truncate max-w-xs">
                      {f.specialization}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-700">
                      {f.teachingLoadHours} Hrs
                    </td>
                    <td className="px-4 py-3.5">
                      <Badge variant="success" dot>
                        {f.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Departmental Operations & Governance Hub */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Building className="h-4 w-4 text-yellow-600" />
            Departmental Operations & Governance Hub
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Direct access to departmental academic programs, workloads, and
            student compliance.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <Link
              href="/app/programs"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Layers className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Programs & Structure
                  </div>
                  <div className="text-[11px] text-slate-500">
                    B.Tech & M.Tech course schemes
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/attendance/leaves"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Calendar className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Faculty & Student Leave Endorsements
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Department faculty leaves & student exemptions
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/attendance/policies"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Attendance Regulations
                  </div>
                  <div className="text-[11px] text-slate-500">
                    75% threshold & leave rules
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/examinations/reports"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <FileText className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Exam Performance & GPA
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Semester pass analysis & rank
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/student-support/assignments"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Users className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Faculty Mentors & Mentees
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Department student allocations
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/accreditation"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Award className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Department Accreditation
                  </div>
                  <div className="text-[11px] text-slate-500">
                    NBA / NAAC criterion metrics
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>

            <Link
              href="/app/students"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/40 hover:border-yellow-300 shadow-xs transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <GraduationCap className="h-4 w-4 text-slate-500" />
                <div>
                  <div className="text-xs font-semibold text-slate-900">
                    Department Students Roster
                  </div>
                  <div className="text-[11px] text-slate-500">
                    720 enrolled student records
                  </div>
                </div>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
