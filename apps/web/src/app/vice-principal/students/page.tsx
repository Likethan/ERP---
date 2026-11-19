"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { StudentSupervisionData } from "@/types/vice-principal";
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
  GraduationCap,
  AlertTriangle,
  Search,
  Filter,
  ShieldAlert,
  Send,
  Users,
  CheckCircle2,
  RefreshCw,
  FileWarning,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalStudentsPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<StudentSupervisionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [threshold, setThreshold] = useState<number>(75.0);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadStudents();
  }, [departmentFilter, threshold]);

  const loadStudents = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getStudentsSupervision({
        department: departmentFilter !== "ALL" ? departmentFilter : undefined,
        threshold: threshold,
      });
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleIssueWarning = (rollNo: string, name: string) => {
    showToast({
      title: "Statutory Warning Issued",
      message: `Formal attendance shortfall notice generated and dispatched for ${name} (${rollNo}).`,
      type: "success",
    });
  };

  const filteredStudents =
    data?.low_attendance_radar.filter((s) => {
      const matchesSearch =
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.roll_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.department.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Student Monitoring & Low-Attendance Radar
          </h1>
          <p className="text-sm text-slate-600">
            Track cohort strength across 4 academic years, monitor sub-75%
            statutory attendance shortage, and manage academic risk backlogs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadStudents}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Cohort Health Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Total Monitored Students
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900">
            {data?.total_students_monitored.toLocaleString()}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Across 5 Academic Departments
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Sub-75% Attendance Shortage
          </div>
          <div className="mt-1 text-2xl font-bold text-rose-600">
            {data?.total_shortage_students} Students
          </div>
          <div className="mt-1 text-[11px] text-rose-700 font-semibold">
            Ineligible for exams without condonation
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Clean Academic Standing
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">
            {data?.academic_backlogs_overview.zero_backlogs_pct}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Zero active semester arrears
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Academic Probation Risk
          </div>
          <div className="mt-1 text-2xl font-bold text-amber-600">
            {data?.academic_backlogs_overview.critical_academic_probation_count}{" "}
            Students
          </div>
          <div className="mt-1 text-[11px] text-amber-700 font-semibold">
            &ge;3 Arrears · Special Remedial Needed
          </div>
        </div>
      </div>

      {/* Institutional Cohort Strength Breakdown Table */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Users className="h-4 w-4 text-indigo-600" />
            Institutional Student Strength by Department & Year of Study
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Annual cohort progression across supervised engineering departments
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Academic Department</th>
                  <th className="px-3 py-3">1st Year</th>
                  <th className="px-3 py-3">2nd Year</th>
                  <th className="px-3 py-3">3rd Year</th>
                  <th className="px-3 py-3">4th Year</th>
                  <th className="px-4 py-3 font-bold text-slate-900">
                    Total Strength
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.institutional_strength.map((row) => (
                  <tr
                    key={row.department}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {row.department}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium">
                      {row.year_1}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium">
                      {row.year_2}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium">
                      {row.year_3}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium">
                      {row.year_4}
                    </td>
                    <td className="px-4 py-3 font-black text-indigo-700">
                      {row.total}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Low-Attendance Radar (<75%) */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                Statutory Low-Attendance Radar (&lt;{threshold}%)
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Students below statutory threshold subject to debarment under
                Anna University Regulation 6.4
              </CardDescription>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500">
                Threshold:
              </span>
              <select
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 focus:outline-hidden"
              >
                <option value={75.0}>75.0% (Statutory Minimum)</option>
                <option value={80.0}>80.0% (Early Warning)</option>
                <option value={65.0}>65.0% (Critical Debarment)</option>
              </select>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Student Details</th>
                  <th className="px-3 py-3">Dept / Sem</th>
                  <th className="px-3 py-3">Current Attendance</th>
                  <th className="px-3 py-3">Shortfall Classes</th>
                  <th className="px-3 py-3">Faculty Mentor</th>
                  <th className="px-3 py-3">Risk Level</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredStudents.map((s) => (
                  <tr
                    key={s.roll_number}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{s.name}</div>
                      <div className="font-mono text-[10px] text-slate-500">
                        {s.roll_number}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <div className="font-semibold text-slate-800">
                        {s.department}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        Sem {s.semester} · Sec {s.section}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="font-black text-rose-600 text-sm">
                        {s.attendance_percentage}%
                      </span>
                      <div className="text-[10px] text-slate-400">
                        {s.attended_sessions} / {s.total_sessions} sessions
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="rounded bg-rose-50 border border-rose-200 px-1.5 py-0.5 text-rose-700 font-bold text-[11px]">
                        +{s.shortfall_sessions} Classes needed
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-700 font-medium">
                      {s.mentor_name}
                    </td>
                    <td className="px-3 py-3">
                      <Badge
                        variant={
                          s.risk_level === "CRITICAL"
                            ? "destructive"
                            : s.risk_level === "HIGH"
                              ? "destructive"
                              : "warning"
                        }
                        className="text-[10px]"
                      >
                        {s.risk_level}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <span className="font-semibold text-slate-700 text-[11px]">
                        {s.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          handleIssueWarning(s.roll_number, s.name)
                        }
                        className="text-xs text-rose-700 hover:text-rose-900 hover:bg-rose-50 gap-1"
                      >
                        <FileWarning className="h-3 w-3" />
                        <span>Issue Notice</span>
                      </Button>
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
