"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { FacultySupervisionData } from "@/types/vice-principal";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Users,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Clock,
  BookOpen,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalFacultyPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<FacultySupervisionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadFaculty();
  }, [departmentFilter]);

  const loadFaculty = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getFacultySupervision({
        department: departmentFilter !== "ALL" ? departmentFilter : undefined,
      });
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSendAdvisory = (facultyName: string, dept: string) => {
    showToast({
      title: "Workload Advisory Dispatched",
      message: `Dispatched workload equalization notice to HOD ${dept} regarding ${facultyName}.`,
      type: "success",
    });
  };

  const filteredFaculty =
    data?.faculty.filter((f) => {
      const matchesSearch =
        f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.employee_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.department.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === "ALL" ? true : f.status === statusFilter;
      return matchesSearch && matchesStatus;
    }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Faculty Workload & Allocation Oversight
          </h1>
          <p className="text-sm text-slate-600">
            Ensure compliance with statutory AICTE teaching norms (12-18 contact
            hours/week) and manage escalated faculty leaves.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/vice-principal/approvals?category=FACULTY_LEAVE">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 text-indigo-600"
            >
              <Calendar className="h-3.5 w-3.5" />
              <span>Escalated Leave Queue</span>
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={loadFaculty}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Workload Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Total Monitored Faculty
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900">
            {data?.workload_summary.total_faculty ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Across 5 Academic Departments
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Statutory Compliant Load
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">
            {data?.workload_summary.compliant_workload_count ?? 0} Faculty
          </div>
          <div className="mt-1 text-[11px] text-emerald-700 font-semibold">
            Within 12 - 18 hours/week
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Overloaded Faculty
          </div>
          <div className="mt-1 text-2xl font-bold text-rose-600">
            {data?.workload_summary.overloaded_count ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-rose-700 font-semibold">
            &gt;18 hours/week (Action advised)
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Underloaded Faculty
          </div>
          <div className="mt-1 text-2xl font-bold text-amber-600">
            {data?.workload_summary.underloaded_count ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-amber-700 font-semibold">
            &lt;12 hours/week (Capacity available)
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search faculty by name, ID or department..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:border-indigo-500"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">
              Department:
            </span>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 focus:outline-hidden"
            >
              <option value="ALL">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Electronics">Electronics & Comm</option>
              <option value="Mechanical">Mechanical</option>
              <option value="Civil">Civil</option>
              <option value="Electrical">Electrical & Electronics</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">
              Workload Status:
            </span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 focus:outline-hidden"
            >
              <option value="ALL">All Statuses</option>
              <option value="NORMAL">Normal (12-18 hrs)</option>
              <option value="OVERLOADED">Overloaded (&gt;18 hrs)</option>
              <option value="UNDERLOADED">Underloaded (&lt;12 hrs)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Faculty Workload Table */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-bold text-slate-900">
              Institutional Faculty Directory & Contact Hour Allocations
            </CardTitle>
            <span className="text-xs text-slate-500">
              Showing {filteredFaculty.length} Faculty Members
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Faculty Member</th>
                  <th className="px-3 py-3">Department</th>
                  <th className="px-3 py-3">Assigned Subjects</th>
                  <th className="px-3 py-3">Teaching Hours</th>
                  <th className="px-3 py-3">Workload Status</th>
                  <th className="px-3 py-3">Attendance</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredFaculty.map((f) => (
                  <tr
                    key={f.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{f.name}</div>
                      <div className="text-[10px] text-slate-500">
                        {f.employee_code} · {f.designation}
                      </div>
                    </td>
                    <td className="px-3 py-3 font-medium text-slate-800">
                      {f.department}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      <div className="space-y-0.5">
                        {f.assigned_subjects.map((sub, idx) => (
                          <div
                            key={idx}
                            className="inline-block mr-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-800"
                          >
                            {sub}
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-3 py-3 font-bold text-slate-900">
                      {f.weekly_teaching_hours} hrs/wk
                    </td>
                    <td className="px-3 py-3">
                      <Badge
                        variant={
                          f.status === "NORMAL"
                            ? "success"
                            : f.status === "OVERLOADED"
                              ? "destructive"
                              : "warning"
                        }
                        className="text-[10px]"
                      >
                        {f.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <span className="font-semibold text-slate-800">
                        {f.attendance_rate}%
                      </span>
                      {f.active_leaves > 0 && (
                        <span className="ml-1 rounded bg-amber-100 text-amber-900 text-[9px] px-1 font-bold">
                          {f.active_leaves} Leave
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {f.status !== "NORMAL" ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleSendAdvisory(f.name, f.department)
                          }
                          className="text-xs text-indigo-600 hover:text-indigo-800"
                        >
                          Advise HOD
                        </Button>
                      ) : (
                        <span className="text-[11px] text-slate-400 font-medium">
                          Compliant
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
