"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import {
  AcademicOperationsSummary,
  CourseOfferingDetail,
  TimetableConflict,
} from "@/types/academics";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth-context";
import {
  BookOpen,
  Calendar,
  Layers,
  FileSpreadsheet,
  CheckSquare,
  ArrowRight,
  Plus,
  Clock,
  Sparkles,
  Users,
  AlertTriangle,
  UserCheck,
  Building2,
  GraduationCap,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";

export default function AcademicsHubPage() {
  const { activePersona } = useAuth();
  const [summary, setSummary] = useState<AcademicOperationsSummary | null>(
    null,
  );
  const [offerings, setOfferings] = useState<CourseOfferingDetail[]>([]);
  const [conflicts, setConflicts] = useState<TimetableConflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [sumRes, offRes, confRes] = await Promise.all([
          academicsService.getSummaryMetrics(),
          academicsService.getCourseOfferingDetails(),
          academicsService.getTimetableConflicts(),
        ]);
        setSummary(sumRes.data);
        setOfferings(offRes.data);
        setConflicts(confRes.data);
      } catch (err) {
        console.error("Failed to load academic hub data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !summary) {
    return (
      <div className="space-y-6">
        <div className="h-20 bg-slate-900/60 rounded-xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-28 bg-slate-900/60 rounded-xl animate-pulse"
            />
          ))}
        </div>
        <TableSkeleton rows={5} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <BookOpen className="h-3 w-3" />
            Academic Operations Hub • Academic Year {
              summary.activeAcademicYear
            }{" "}
            (Semester {summary.currentSemester})
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Academic Management & Governance
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Regulated CBCS curricula schemes, syllabus course offerings, faculty
            allocations, student enrollments, and timetables.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/app/academics/subjects">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<BookOpen className="h-3.5 w-3.5" />}
            >
              Subjects Catalog
            </Button>
          </Link>
          <Link href="/app/academics/timetable">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Calendar className="h-3.5 w-3.5" />}
            >
              Master Timetable
            </Button>
          </Link>
        </div>
      </div>

      {/* Institutional Hierarchy Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-indigo-400" />
              <span className="text-slate-400">Departments:</span>
              <span className="font-semibold text-white">
                {summary.totalDepartments}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-sky-400" />
              <span className="text-slate-400">Programs:</span>
              <span className="font-semibold text-white">
                {summary.totalPrograms}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-emerald-400" />
              <span className="text-slate-400">Active Sections:</span>
              <span className="font-semibold text-white">
                {summary.totalSections}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Active Term:</span>
            <span className="rounded bg-indigo-500/10 px-2 py-0.5 font-mono text-indigo-300 border border-indigo-500/20">
              AY {summary.activeAcademicYear} • Sem {summary.currentSemester}
            </span>
          </div>
        </div>
      </div>

      {/* Operational Conflicts / Warning Notice */}
      {(conflicts.length > 0 || summary.unassignedOfferingsCount > 0) && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-amber-300">
                Academic Operations Attention Required
              </h4>
              <p className="text-xs text-amber-200/80 mt-0.5">
                {conflicts.length > 0 &&
                  `${conflicts.length} timetable collision/conflict detected in the active schedule. `}
                {summary.unassignedOfferingsCount > 0 &&
                  `${summary.unassignedOfferingsCount} course offering(s) currently lack faculty instructor assignment.`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {conflicts.length > 0 && (
              <Link href="/app/academics/timetable">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-amber-500/40 text-amber-300 hover:bg-amber-500/20 text-xs"
                >
                  Review Conflicts
                </Button>
              </Link>
            )}
            {summary.unassignedOfferingsCount > 0 && (
              <Link href="/app/academics/course-offerings">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-amber-500/40 text-amber-300 hover:bg-amber-500/20 text-xs"
                >
                  Assign Faculty
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Real Mock Service Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Curricula Schemes"
          value={summary.activeCurriculaCount}
          description="Autonomous R-2024 & R-2026 CBCS"
          variant="indigo"
          icon={<FileSpreadsheet className="h-4 w-4" />}
        />
        <StatCard
          label="Active Subjects"
          value={summary.activeSubjectsCount}
          description="Theory, Labs, and Electives"
          variant="emerald"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Course Offerings"
          value={summary.activeOfferingsCount}
          description={`${summary.unassignedOfferingsCount} require faculty allocation`}
          variant="sky"
          icon={<CheckSquare className="h-4 w-4" />}
        />
        <StatCard
          label="Course Enrollments"
          value={summary.enrolledStudentsCount}
          description={`${summary.assignedFacultyCount} faculty instructors active`}
          variant="amber"
          icon={<UserCheck className="h-4 w-4" />}
        />
      </div>

      {/* Navigation Sub-Modules Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Link
          href="/app/academics/subjects"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <BookOpen className="h-5 w-5 text-indigo-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300">
            Subject Catalog
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Course codes, credits, lecture/lab ratios, and syllabus units.
          </p>
        </Link>

        <Link
          href="/app/academics/curricula"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <FileSpreadsheet className="h-5 w-5 text-emerald-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-emerald-300">
            Curriculum Builder
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Semester structure, elective groups, credit totals, and versioning.
          </p>
        </Link>

        <Link
          href="/app/academics/course-offerings"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <CheckSquare className="h-5 w-5 text-sky-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-sky-300">
            Course Offerings
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Offerings creation wizard, faculty staffing, and section capacities.
          </p>
        </Link>

        <Link
          href="/app/academics/enrollments"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <UserCheck className="h-5 w-5 text-purple-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-purple-300">
            Course Enrollments
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Student course registrations, elective selection, and bulk
            enrollment.
          </p>
        </Link>

        <Link
          href="/app/academics/timetable"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <Calendar className="h-5 w-5 text-amber-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-amber-300">
            Master Timetable
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Weekly slots, section schedules, faculty allocations, and conflict
            check.
          </p>
        </Link>
      </div>

      {/* Active Course Offerings Roster */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>
              Active Course Offerings ({summary.activeAcademicYear})
            </CardTitle>
            <CardDescription>
              Sections running with faculty lead assignments, room mappings, and
              live student enrollment.
            </CardDescription>
          </div>
          <Link href="/app/academics/course-offerings">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-400 hover:text-white"
            >
              All Offerings <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3">Subject & Code</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Section</th>
                  <th className="px-4 py-3">Assigned Faculty</th>
                  <th className="px-4 py-3">Enrolled / Cap</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {offerings.slice(0, 6).map((off) => {
                  const primaryFac =
                    off.facultyAssignments.find(
                      (f) => f.role === "PRIMARY_INSTRUCTOR",
                    ) || off.facultyAssignments[0];
                  return (
                    <tr
                      key={off.id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-5 py-3.5 font-medium text-white">
                        <Link
                          href={`/app/academics/course-offerings/${off.id}`}
                          className="hover:text-indigo-400 transition-colors"
                        >
                          <div className="font-semibold">
                            {off.subjectCode} — {off.subjectName}
                          </div>
                          <div className="text-[11px] text-slate-400 font-normal">
                            {off.credits} Credits • {off.type}
                          </div>
                        </Link>
                      </td>
                      <td className="px-4 py-3.5 text-slate-300">
                        {off.department}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300 border border-slate-700">
                          Sem {off.semester} • Sec {off.section}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-200">
                        {primaryFac ? (
                          <div>
                            <span className="font-medium">
                              {primaryFac.facultyName}
                            </span>
                            <span className="block text-[10px] text-slate-400">
                              {primaryFac.role.replace("_", " ")}
                            </span>
                          </div>
                        ) : (
                          <span className="text-amber-400 font-medium italic">
                            Unassigned
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 font-mono">
                        <div className="flex items-center gap-2">
                          <span>
                            {off.enrolledCount} / {off.maxCapacity}
                          </span>
                          <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-indigo-500 h-1.5 rounded-full"
                              style={{
                                width: `${Math.min(100, (off.enrolledCount / off.maxCapacity) * 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge
                          variant={
                            off.status === "ACTIVE"
                              ? "success"
                              : off.status === "OPEN"
                                ? "info"
                                : "warning"
                          }
                          dot
                        >
                          {off.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <Link
                          href={`/app/academics/course-offerings/${off.id}`}
                        >
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-indigo-400 hover:text-indigo-300"
                          >
                            Details
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
