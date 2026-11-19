"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { DepartmentMonitoringItem } from "@/types/vice-principal";
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
  Building2,
  Users,
  GraduationCap,
  CalendarCheck,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Search,
  BookOpen,
  Mail,
  FlaskConical,
  Award,
  Layers,
  RefreshCw,
} from "lucide-react";

export default function VicePrincipalDepartmentsPage() {
  const [departments, setDepartments] = useState<DepartmentMonitoringItem[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getDepartments();
      if (res.success && res.data) {
        setDepartments(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredDepts = departments.filter((d) => {
    const matchesSearch =
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.hod_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" ? true : d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Department Supervision & Academic Comparison
          </h1>
          <p className="text-sm text-slate-600">
            Monitor Head of Department governance, teaching velocity, student
            attendance, and statutory ratios.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadDepartments}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Reload</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by department, code, or HOD name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:border-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">
            Status Filter:
          </span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Statuses</option>
            <option value="EXEMPLARY">Exemplary</option>
            <option value="ON_TRACK">On Track</option>
            <option value="ATTENTION_NEEDED">Attention Needed</option>
          </select>
        </div>
      </div>

      {/* Department Cards Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {filteredDepts.map((dept) => (
          <Card
            key={dept.id}
            className="shadow-xs border-slate-200 hover:border-indigo-300 transition-colors"
          >
            <CardHeader className="border-b border-slate-100 pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="rounded bg-indigo-50 border border-indigo-200 px-2 py-0.5 font-mono text-xs font-bold text-indigo-700">
                      {dept.code}
                    </span>
                    <Badge
                      variant={
                        dept.status === "EXEMPLARY"
                          ? "success"
                          : dept.status === "ON_TRACK"
                            ? "default"
                            : "warning"
                      }
                      className="text-[10px]"
                    >
                      {dept.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <CardTitle className="text-base font-bold text-slate-900">
                    {dept.name}
                  </CardTitle>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    NAAC Score
                  </div>
                  <div className="text-base font-black text-indigo-700">
                    {dept.accreditation_score} / 4.0
                  </div>
                </div>
              </div>

              {/* HOD Profile Row */}
              <div className="mt-3 flex items-center justify-between rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center">
                    {dept.hod_name
                      .split(" ")
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join("")}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900">
                      {dept.hod_name}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      Head of Department
                    </div>
                  </div>
                </div>
                <a
                  href={`mailto:${dept.hod_email}`}
                  className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  <Mail className="h-3 w-3" />
                  <span>{dept.hod_email}</span>
                </a>
              </div>
            </CardHeader>

            <CardContent className="p-4 space-y-4">
              {/* Core Vital Stats */}
              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Students
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {dept.student_count}
                  </div>
                  <div className="text-[9px] text-slate-500">
                    {dept.faculty_ratio} AICTE
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Faculty
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {dept.faculty_count}
                  </div>
                  <div className="text-[9px] text-emerald-600 font-medium">
                    {dept.faculty_attendance}% Present
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Attendance
                  </div>
                  <div
                    className={`text-sm font-bold ${
                      dept.student_attendance < 85
                        ? "text-amber-600"
                        : "text-slate-900"
                    }`}
                  >
                    {dept.student_attendance}%
                  </div>
                  <div className="text-[9px] text-slate-500">Threshold 75%</div>
                </div>
                <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Approvals
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {dept.pending_approvals}
                  </div>
                  <div className="text-[9px] text-amber-600 font-medium">
                    Pending
                  </div>
                </div>
              </div>

              {/* Syllabus Progress Bar */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-700">
                    Curriculum Syllabus Progress
                  </span>
                  <span className="font-bold text-slate-900">
                    {dept.syllabus_progress}% Completed
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      dept.syllabus_progress < 80
                        ? "bg-amber-500"
                        : "bg-emerald-600"
                    }`}
                    style={{ width: `${dept.syllabus_progress}%` }}
                  />
                </div>
                {dept.delay_alerts_count > 0 && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    <span>
                      {dept.delay_alerts_count} course(s) flagged behind
                      scheduled pace
                    </span>
                  </p>
                )}
              </div>

              {/* Infrastructure Footprint */}
              <div className="flex items-center justify-between text-xs text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <FlaskConical className="h-3.5 w-3.5 text-indigo-600" />
                    <b>{dept.labs_count}</b> Specialized Labs
                  </span>
                  <span className="flex items-center gap-1">
                    <Layers className="h-3.5 w-3.5 text-slate-500" />
                    <b>{dept.classrooms_count}</b> Classrooms
                  </span>
                </div>
                <Link
                  href={`/vice-principal/faculty?department=${dept.name}`}
                  className="text-xs font-semibold text-indigo-600 hover:underline flex items-center gap-1"
                >
                  <span>Faculty Directory</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
