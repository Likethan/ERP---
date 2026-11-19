"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { AcademicMonitoringData } from "@/types/vice-principal";
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
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  BookOpen,
  CalendarDays,
  Send,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalAcademicsPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<AcademicMonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [semesterType, setSemesterType] = useState("ODD");
  const [academicYear, setAcademicYear] = useState("2026-2027");

  useEffect(() => {
    loadAcademics();
  }, [semesterType, academicYear]);

  const loadAcademics = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getAcademicsMonitoring({
        academic_year: academicYear,
        semester_type: semesterType,
      });
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleIssueDirective = (subjectCode: string, faculty: string) => {
    showToast({
      title: "Remediation Directive Dispatched",
      message: `Formal extra-class schedule directive sent to ${faculty} for ${subjectCode}.`,
      type: "success",
    });
  };

  if (loading && !data) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Academic Calendar & Syllabus Velocity
          </h1>
          <p className="text-sm text-slate-600">
            Enforce statutory milestone compliance, monitor lesson plan
            progress, and remediate curriculum delays.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
            <button
              onClick={() => setSemesterType("ODD")}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                semesterType === "ODD"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Odd Semesters
            </button>
            <button
              onClick={() => setSemesterType("EVEN")}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                semesterType === "EVEN"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Even Semesters
            </button>
          </div>
        </div>
      </div>

      {/* Timetable Integrity Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Scheduled Lecture Hours
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900">
            {data?.timetable_coverage.total_scheduled_hours_weekly} hrs/wk
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Across 5 Engineering Departments
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            On-Schedule Execution
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">
            {data?.timetable_coverage.classes_conducted_on_schedule_pct}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Punctuality and delivery index
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Faculty Substitution Rate
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900">
            {data?.timetable_coverage.faculty_substitution_rate_pct}%
          </div>
          <div className="mt-1 text-[11px] text-emerald-600 font-semibold">
            Within 5% statutory threshold
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Unassigned Slots
          </div>
          <div className="mt-1 text-2xl font-bold text-indigo-600">0</div>
          <div className="mt-1 text-[11px] text-slate-500">
            100% Timetable coverage achieved
          </div>
        </div>
      </div>

      {/* Institutional Academic Calendar Milestones */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="h-4 w-4 text-indigo-600" />
            Statutory Academic Calendar Milestones ({academicYear})
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Continuous Internal Assessment dates, model exams, and university
            evaluation windows
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Milestone Event</th>
                  <th className="px-3 py-3">Scheduled Date</th>
                  <th className="px-3 py-3">Actual Date</th>
                  <th className="px-3 py-3">Variance</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.milestones.map((ms) => (
                  <tr
                    key={ms.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-semibold text-slate-900">
                      {ms.event}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-mono">
                      {ms.scheduled_date}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-mono">
                      {ms.actual_date || "—"}
                    </td>
                    <td className="px-3 py-3">
                      {ms.variance_days === 0 ? (
                        <span className="text-emerald-700 font-semibold">
                          On Schedule
                        </span>
                      ) : (
                        <span className="text-amber-700 font-semibold">
                          +{ms.variance_days} Day(s) Lag
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <Badge
                        variant={
                          ms.status === "COMPLETED"
                            ? "success"
                            : ms.status === "UPCOMING"
                              ? "default"
                              : "destructive"
                        }
                        className="text-[10px]"
                      >
                        {ms.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Syllabus Delay Tracking & Remediation Plan */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Syllabus Completion Delay Radar & Remedial Interventions
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Subjects with syllabus delivery lagging &gt;3 days behind
                institutional teaching plan
              </CardDescription>
            </div>
            <Badge variant="warning" className="text-xs">
              {data?.syllabus_delay_tracking.length ?? 0} Courses Flagged
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Course</th>
                  <th className="px-3 py-3">Dept / Sem</th>
                  <th className="px-3 py-3">Faculty In-Charge</th>
                  <th className="px-3 py-3">Topics Covered</th>
                  <th className="px-3 py-3">Lag</th>
                  <th className="px-3 py-3">Remedial Action</th>
                  <th className="px-4 py-3 text-right">Intervention</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.syllabus_delay_tracking.map((item) => (
                  <tr
                    key={item.subject_code}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">
                        {item.subject_name}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500">
                        {item.subject_code}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="font-semibold text-slate-800">
                        {item.department}
                      </span>{" "}
                      · Sem {item.semester}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {item.faculty_name}
                    </td>
                    <td className="px-3 py-3">
                      <div className="text-xs font-bold text-slate-900">
                        {item.completed_topics} / {item.planned_topics} (
                        {item.completion_percentage}%)
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Expected: {item.expected_percentage}%
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="rounded bg-rose-50 border border-rose-200 px-1.5 py-0.5 font-bold text-rose-700 text-[11px]">
                        -{item.lag_days} Days
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <span className="font-semibold text-slate-800">
                        {item.remedial_status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          handleIssueDirective(
                            item.subject_code,
                            item.faculty_name,
                          )
                        }
                        className="text-xs gap-1"
                      >
                        <Send className="h-3 w-3" />
                        <span>Issue Directive</span>
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
