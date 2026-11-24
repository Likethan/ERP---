"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import {
  hodService,
  HodExaminationsData,
  HodExamSchedule,
  HodExamSubmissionProgress,
  HodExamTerm,
} from "@/services/hod.service";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import {
  FileText,
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  Building,
  Layers,
  Sparkles,
  Download,
  AlertCircle,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodExaminationsPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodExaminationsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "schedules" | "submissions" | "terms"
  >("schedules");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await hodService.getExaminations();
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to load examinations data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Academic Operations
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Autonomous Term 2026-2027
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <FileText className="h-6 w-6 text-yellow-600" />
            Department Examination Management
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Examination timetable scheduling, hall allocations, marks submission
            compliance tracking, and missing marks identification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            onClick={() =>
              alert("Downloading Department Examination Timetable (PDF)...")
            }
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Download Exam Schedule
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Scheduled Exams
              </span>
              <Calendar className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.summary.totalScheduledExams || 4}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Model Examinations Nov 2026
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Marks Compliance
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-2">
              {data?.summary.submissionComplianceRate || 95.6}%
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-1">
              IA-1 & IA-2 Evaluated
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Missing / Pending Marks
              </span>
              <AlertCircle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-amber-700 mt-2">
              {data?.summary.missingMarksTotal || 4}
            </div>
            <div className="text-[11px] text-amber-700 font-bold mt-1">
              In CS303 Computer Networks (Sec A)
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Upcoming ESE Window
              </span>
              <Sparkles className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              Dec 08 - 22
            </div>
            <div className="text-[11px] text-yellow-800 font-medium mt-1">
              Controller of Exams Autonomous Window
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("schedules")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "schedules"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <Calendar className="h-3.5 w-3.5" />
          Examination Timetable & Hall Allocations (
          {data?.schedules.length || 4})
        </button>

        <button
          onClick={() => setActiveTab("submissions")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "submissions"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          Faculty Marks Submission Monitoring
        </button>

        <button
          onClick={() => setActiveTab("terms")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "terms"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <Layers className="h-3.5 w-3.5" />
          Assessment Terms & Windows
        </button>
      </div>

      {/* Tab 1: Schedules */}
      {activeTab === "schedules" && (
        <Card className="border-slate-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                  <th className="py-3 px-4">Exam Date & Time</th>
                  <th className="py-3 px-4">Course Details</th>
                  <th className="py-3 px-4">Semester & Class</th>
                  <th className="py-3 px-4">Examination Type</th>
                  <th className="py-3 px-4">Hall & Invigilation</th>
                  <th className="py-3 px-4 text-center">Candidates</th>
                  <th className="py-3 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {(data?.schedules || []).map((sch) => (
                  <tr
                    key={sch.id}
                    className="hover:bg-yellow-50/30 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900 flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        {sch.date}
                      </div>
                      <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1 mt-0.5">
                        <Clock className="h-3 w-3 text-slate-400" />
                        {sch.time} ({sch.duration})
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">
                        {sch.courseName}
                      </div>
                      <span className="font-mono text-[10px] font-bold text-yellow-800 bg-yellow-100 px-1.5 py-0.2 rounded">
                        {sch.courseCode}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-700">
                        Sem {sch.semester}
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">
                        Sec {sch.section}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant="outline"
                        className="text-[10px] font-bold bg-slate-50"
                      >
                        {sch.examType.replace(/_/g, " ")}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                        <Building className="h-3.5 w-3.5 text-blue-600" />
                        {sch.hallNumber}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        Invigilator: {sch.chiefInvigilator}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="font-mono font-bold text-slate-900">
                        {sch.totalCandidates} Students
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-[10px] font-semibold">
                        CONFIRMED
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 2: Submissions */}
      {activeTab === "submissions" && (
        <div className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-xs">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900">
                Department Faculty Marks Submission Progress
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                HOD statutory audit of marks entries across Internal Assessment
                1, 2, and Model Exams.
              </CardDescription>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                    <th className="py-3 px-4">Course & Faculty</th>
                    <th className="py-3 px-4">IA-1 Marks</th>
                    <th className="py-3 px-4">IA-2 Marks</th>
                    <th className="py-3 px-4">Model Exam</th>
                    <th className="py-3 px-4 text-center">Missing Marks</th>
                    <th className="py-3 px-4 text-right">Compliance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {(data?.submissionProgress || []).map((row) => (
                    <tr key={row.courseCode} className="hover:bg-yellow-50/30">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">
                          {row.courseName}
                        </div>
                        <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                          <span className="font-mono font-bold text-yellow-800 bg-yellow-100 px-1 rounded">
                            {row.courseCode}
                          </span>
                          • Faculty: {row.facultyName}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-[10px]">
                          {row.ia1Status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          className={cn(
                            "text-[10px]",
                            row.ia2Status.includes("PARTIAL")
                              ? "bg-amber-100 text-amber-900 border-amber-300 font-bold"
                              : "bg-emerald-100 text-emerald-800 border-emerald-200",
                          )}
                        >
                          {row.ia2Status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant="outline"
                          className="text-[10px] bg-slate-50"
                        >
                          {row.modelStatus.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {row.missingMarks > 0 ? (
                          <span className="font-mono font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                            {row.missingMarks} Missing
                          </span>
                        ) : (
                          <span className="text-emerald-600 text-xs font-bold flex items-center justify-center gap-1">
                            <CheckCircle2 className="h-3.5 w-3.5" /> None
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={cn(
                            "text-[10px] font-bold px-2 py-0.5 rounded",
                            row.missingMarks > 0
                              ? "bg-amber-100 text-amber-800"
                              : "bg-emerald-100 text-emerald-800",
                          )}
                        >
                          {row.missingMarks > 0
                            ? "ACTION REQUIRED"
                            : "COMPLIANT"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 3: Terms */}
      {activeTab === "terms" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(data?.terms || []).map((term) => (
            <Card key={term.id} className="border-slate-200 bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <Badge
                    className={cn(
                      "text-[10px] font-bold",
                      term.status === "COMPLETED"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                        : term.status === "ONGOING"
                          ? "bg-yellow-100 text-yellow-900 border-yellow-300"
                          : "bg-blue-100 text-blue-800 border-blue-200",
                    )}
                  >
                    {term.status}
                  </Badge>
                  <span className="text-[10px] font-mono text-slate-400">
                    {term.academicYear}
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-1">
                  {term.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Examination Window:</span>
                  <span className="font-semibold text-slate-900">
                    {term.startDate} to {term.endDate}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">
                    Marks Submission Deadline:
                  </span>
                  <span className="font-mono font-bold text-red-600">
                    {term.marksSubmissionDeadline}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-500">Submission Progress:</span>
                  <span className="font-bold text-slate-800">
                    {term.submissionStatus}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
