"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import {
  hodService,
  HodLessonPlansData,
  HodLessonPlanItem,
  HodLessonPlanUnit,
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
  ListChecks,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  UserCheck,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Download,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodLessonPlansPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodLessonPlansData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCourse, setSelectedCourse] = useState<string>("CS301");
  const [expandedUnits, setExpandedUnits] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: true,
    4: true,
    5: true,
  });

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await hodService.getLessonPlans();
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to load lesson plans", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const currentPlan: HodLessonPlanItem | undefined = data?.lessonPlans.find(
    (p) => p.courseCode === selectedCourse,
  );

  const toggleUnit = (unitNumber: number) => {
    setExpandedUnits((prev) => ({
      ...prev,
      [unitNumber]: !prev[unitNumber],
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Academic Management
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Semester 5 (Odd 2026)
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <ListChecks className="h-6 w-6 text-yellow-600" />
            Lesson Plan Monitoring & Syllabus Progress
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Real-time tracking of unit-wise teaching progress, planned vs
            completed instructional hours, and topic delivery compliance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            onClick={() =>
              alert(
                "Exporting Department Syllabus Delivery Audit Report (PDF)...",
              )
            }
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export Audit Report
          </Button>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Monitored Courses
              </span>
              <FileSpreadsheet className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.summary.totalMonitoredCourses || 3}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Active Core Theory Offerings
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Avg Department Progress
              </span>
              <Sparkles className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.summary.averageSyllabusCompletion || 80.0}%
            </div>
            <div className="text-[11px] text-emerald-600 font-bold mt-1">
              Aligned with Week 12 Target (75%)
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Courses On Track
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-2">
              {(data?.summary.totalMonitoredCourses || 3) -
                (data?.summary.coursesBehindSchedule || 1)}{" "}
              / {data?.summary.totalMonitoredCourses || 3}
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-1">
              $\ge$ 75% Syllabus Completed
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Attention / Behind Schedule
              </span>
              <AlertCircle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-amber-700 mt-2">
              {data?.summary.coursesBehindSchedule || 1}
            </div>
            <div className="text-[11px] text-amber-700 font-bold mt-1">
              CS303 (73.3% - Compensatory planned)
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Course Selector Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {(data?.lessonPlans || []).map((plan) => (
          <button
            key={plan.courseCode}
            onClick={() => setSelectedCourse(plan.courseCode)}
            className={cn(
              "flex items-center gap-2.5 px-4 py-2 rounded-lg text-xs font-bold transition-all border",
              selectedCourse === plan.courseCode
                ? "bg-yellow-400 text-slate-950 border-yellow-500 shadow-xs"
                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50",
            )}
          >
            <span className="font-mono">{plan.courseCode}</span>
            <span className="hidden sm:inline font-normal text-slate-800">
              {plan.courseName}
            </span>
            <span
              className={cn(
                "px-1.5 py-0.2 rounded text-[10px] font-mono",
                plan.overallCompletionPercentage >= 80
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-amber-100 text-amber-900",
              )}
            >
              {plan.overallCompletionPercentage}%
            </span>
          </button>
        ))}
      </div>

      {/* Selected Course Detail Card */}
      {currentPlan && (
        <div className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-xs">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm bg-yellow-100 text-yellow-900 px-2 py-0.5 rounded border border-yellow-300">
                      {currentPlan.courseCode} - Section {currentPlan.section}
                    </span>
                    <Badge variant="outline" className="text-slate-600 text-xs">
                      {currentPlan.status}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg font-black text-slate-900 mt-1">
                    {currentPlan.courseName}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-600 flex items-center gap-1.5 mt-0.5">
                    <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
                    Faculty In-charge:{" "}
                    <span className="font-bold text-slate-900">
                      {currentPlan.facultyName}
                    </span>{" "}
                    ({currentPlan.facultyDesignation})
                  </CardDescription>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-black text-slate-900">
                    {currentPlan.totalCompletedHours} /{" "}
                    {currentPlan.totalPlannedHours}{" "}
                    <span className="text-xs text-slate-500 font-normal">
                      Hours Delivered
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-36 bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={cn(
                          "h-2 rounded-full",
                          currentPlan.overallCompletionPercentage >= 80
                            ? "bg-emerald-500"
                            : "bg-yellow-500",
                        )}
                        style={{
                          width: `${currentPlan.overallCompletionPercentage}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs font-bold font-mono text-slate-800">
                      {currentPlan.overallCompletionPercentage}%
                    </span>
                  </div>
                </div>
              </div>
            </CardHeader>

            {/* Units Accordion */}
            <CardContent className="p-4 space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Unit-Wise Instructional Delivery & Topic Checklist (5 Units)
              </div>

              {currentPlan.units.map((unit) => {
                const isExpanded = expandedUnits[unit.unitNumber] ?? true;
                const completedCount = unit.topics.filter(
                  (t) => t.completed,
                ).length;

                return (
                  <div
                    key={unit.unitNumber}
                    className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50/30"
                  >
                    {/* Unit Header Bar */}
                    <div
                      onClick={() => toggleUnit(unit.unitNumber)}
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-yellow-50/40 transition-colors bg-white border-b border-slate-100"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "h-7 w-7 rounded-md font-bold text-xs flex items-center justify-center shrink-0 border",
                            unit.status === "COMPLETED"
                              ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                              : "bg-yellow-100 text-yellow-900 border-yellow-300",
                          )}
                        >
                          U{unit.unitNumber}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 text-xs sm:text-sm">
                            Unit {unit.unitNumber}: {unit.title}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            {unit.completedHours} of {unit.plannedHours} hours
                            completed • {completedCount} of {unit.topics.length}{" "}
                            topics covered
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Badge
                          className={cn(
                            "text-[10px] font-bold",
                            unit.status === "COMPLETED"
                              ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                              : "bg-blue-100 text-blue-800 border-blue-200",
                          )}
                        >
                          {unit.completionPercentage}% {unit.status}
                        </Badge>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Unit Topics Checklist */}
                    {isExpanded && (
                      <div className="p-3 bg-slate-50 space-y-2 text-xs">
                        {unit.topics.map((t, idx) => (
                          <div
                            key={idx}
                            className={cn(
                              "flex items-center gap-2.5 p-2 rounded-md border transition-colors",
                              t.completed
                                ? "bg-white border-slate-200 text-slate-900"
                                : "bg-amber-50/60 border-amber-200 text-amber-950 font-medium",
                            )}
                          >
                            {t.completed ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                            ) : (
                              <Clock className="h-4 w-4 text-amber-600 shrink-0" />
                            )}
                            <span
                              className={cn(
                                t.completed
                                  ? "text-slate-700"
                                  : "text-amber-900",
                              )}
                            >
                              {t.topic}
                            </span>
                            {!t.completed && (
                              <span className="ml-auto text-[10px] font-mono text-amber-700 font-bold bg-amber-100 px-1.5 py-0.2 rounded">
                                Planned for Week 13
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
