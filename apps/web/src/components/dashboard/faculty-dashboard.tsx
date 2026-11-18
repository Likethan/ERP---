"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
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
import { facultyService } from "@/services/faculty.service";
import { teachingService } from "@/services/teaching.service";
import { FacultyDetailView } from "@/types/domain";
import {
  Clock,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  FileSpreadsheet,
  Users,
  GraduationCap,
  Award,
  Heart,
  FlaskConical,
  Layers,
  Calendar,
  ClipboardCheck,
  TrendingUp,
  FileText,
  UserCheck,
} from "lucide-react";

export function FacultyDashboard() {
  const { user, activePersona } = useAuth();
  const [faculty, setFaculty] = useState<FacultyDetailView | null>(null);
  const [pendingEvaluations, setPendingEvaluations] = useState<number>(0);
  const [syllabusCompletion, setSyllabusCompletion] = useState<number>(68);

  useEffect(() => {
    // Determine effective faculty ID from persona/user
    const targetId = activePersona?.id || "fac-cse-01";

    facultyService.getById(targetId).then((res) => {
      if (res.data) {
        setFaculty(res.data);
      } else {
        // Fallback to primary faculty if custom ID
        facultyService.getById("fac-cse-01").then((fallbackRes) => {
          if (fallbackRes.data) {
            // Personalize fallback with active persona credentials
            setFaculty({
              ...fallbackRes.data,
              id: activePersona.id,
              firstName: activePersona.name.split(" ")[0] || "Faculty",
              lastName: activePersona.name.split(" ").slice(1).join(" ") || "Member",
              email: activePersona.email,
              department: activePersona.department || fallbackRes.data.department,
            });
          }
        });
      }
    });

    // Pull live metrics from teaching service
    teachingService.getAssignments().then((res) => {
      if (res.success) {
        const pending = res.data.reduce(
          (acc, a) => acc + (a.totalSubmissions - a.evaluatedCount),
          0
        );
        setPendingEvaluations(pending);
      }
    });

    teachingService.getLessonPlans().then((res) => {
      if (res.success && res.data.length > 0) {
        const planned = res.data.reduce((acc, p) => acc + p.plannedHours, 0);
        const completed = res.data.reduce((acc, p) => acc + p.completedHours, 0);
        if (planned > 0) {
          setSyllabusCompletion(Math.round((completed / planned) * 100));
        }
      }
    });
  }, [activePersona, user]);

  if (!faculty) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading faculty workspace...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Faculty Welcome Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Faculty Academic Workspace • {faculty.employeeCode}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Welcome, {faculty.firstName} {faculty.lastName}!
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            {faculty.designation} • {faculty.department}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link href="/app/attendance/sessions">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
            >
              Mark Attendance
            </Button>
          </Link>
          <Link href="/app/academics/assignments">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<ClipboardCheck className="h-3.5 w-3.5" />}
            >
              Grading ({pendingEvaluations})
            </Button>
          </Link>
          <Link href="/app/faculty/leaves">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Calendar className="h-3.5 w-3.5" />}
            >
              Faculty Leave
            </Button>
          </Link>
          <Link href="/app/examinations/marks">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            >
              CIA Marks
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <StatCard
          label="Assigned Course Offerings"
          value={faculty.stats.coursesCount}
          description="CS301 (Sec A & B), CS501"
          variant="indigo"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Total Enrolled Students"
          value={faculty.stats.totalStudents}
          description="Across active course cohorts"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Syllabus Completion"
          value={`${syllabusCompletion}%`}
          change={{ value: syllabusCompletion >= 50 ? "On Track" : "Lagging", trend: "up" }}
          description="Unit-wise curriculum delivery"
          variant="sky"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          label="Pending Evaluations"
          value={pendingEvaluations}
          description="Coursework submissions awaiting marks"
          variant="amber"
          icon={<ClipboardCheck className="h-4 w-4" />}
        />
      </div>

      {/* Main Grid: Today's Lectures & Teaching Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Classes List (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-sky-500" />
                  Today's Assigned Lecture Slots
                </CardTitle>
                <CardDescription>
                  Sessions scheduled for today across assigned lecture halls.
                </CardDescription>
              </div>
              <Link href="/app/academics/timetable">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-slate-500 hover:text-slate-900"
                >
                  My Timetable <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {faculty.todayClasses.map((cls, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white hover:bg-yellow-50/20 shadow-xs transition-all"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-100 text-yellow-950 border border-yellow-300 text-xs font-mono font-bold">
                      0{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900">
                        {cls.subject}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {cls.section} • {cls.room}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-medium text-slate-700">
                      {cls.time}
                    </span>
                    <div className="mt-1">
                      {cls.attendanceMarked ? (
                        <Badge variant="success" dot>
                          Marked
                        </Badge>
                      ) : (
                        <Link href="/app/attendance/sessions">
                          <Badge variant="warning" dot className="cursor-pointer hover:bg-yellow-200">
                            Mark Now
                          </Badge>
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Shortcuts to New Modules */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              href="/app/academics/lesson-plans"
              className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/20 transition-all shadow-xs flex items-start gap-3"
            >
              <div className="p-2.5 rounded-lg bg-yellow-100 text-yellow-950 border border-yellow-300">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Lesson Plans & Syllabus</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Unit-wise syllabus tracking, learning outcomes, and delivery hours.
                </p>
              </div>
            </Link>

            <Link
              href="/app/academics/class-diary"
              className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/20 transition-all shadow-xs flex items-start gap-3"
            >
              <div className="p-2.5 rounded-lg bg-indigo-100 text-indigo-950 border border-indigo-200">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Class Diary / Teaching Log</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Log lecture delivery topics, pedagogy methods, and turnout.
                </p>
              </div>
            </Link>

            <Link
              href="/app/academics/materials"
              className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/20 transition-all shadow-xs flex items-start gap-3"
            >
              <div className="p-2.5 rounded-lg bg-emerald-100 text-emerald-950 border border-emerald-200">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Course Study Materials</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Upload lecture notes, slide decks, lab worksheets, and reference links.
                </p>
              </div>
            </Link>

            <Link
              href="/app/academics/assignments"
              className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/20 transition-all shadow-xs flex items-start gap-3"
            >
              <div className="p-2.5 rounded-lg bg-sky-100 text-sky-950 border border-sky-200">
                <ClipboardCheck className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Assignments & Grading</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Set homework deadlines, review student submissions, and award marks.
                </p>
              </div>
            </Link>
          </div>
        </div>

        {/* Right Col: Assigned Subjects & Mentoring Hub */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Assigned Subjects & Rosters</CardTitle>
              <CardDescription>
                Odd Semester 2026-27 teaching responsibilities.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {faculty.assignedSubjects.map((sub) => (
                <div
                  key={sub.id}
                  className="p-3 rounded-lg border border-slate-200 bg-white hover:bg-yellow-50/20 shadow-xs transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-900">
                      {sub.code} — {sub.name}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Sem {sub.semester} ({sub.section}) • {sub.studentCount} Students
                    </div>
                  </div>
                  <Link href="/app/attendance/sessions">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                    >
                      Roster
                    </Button>
                  </Link>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Faculty Teaching & Governance Hub */}
          <Card className="bg-white border-slate-200 shadow-xs">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs uppercase font-bold tracking-wider text-slate-800 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-yellow-600" />
                Teaching Governance Hub
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Departmental courses, grading, and student mentoring.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link
                href="/app/attendance/leaves"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <UserCheck className="h-3.5 w-3.5 text-slate-500" />
                  <span>Student Leave Approvals</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
              <Link
                href="/app/faculty/leaves"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Calendar className="h-3.5 w-3.5 text-slate-500" />
                  <span>Apply for Faculty Leave (to HOD)</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
              <Link
                href="/app/attendance/courses"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-slate-500" />
                  <span>Course Registers & Attendance</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
              <Link
                href="/app/examinations/assessments"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Award className="h-3.5 w-3.5 text-slate-500" />
                  <span>Assessments & Exam Schedules</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
              <Link
                href="/app/student-support/mentees"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Heart className="h-3.5 w-3.5 text-slate-500" />
                  <span>Assigned Student Mentees</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
              <Link
                href="/app/research"
                className="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-yellow-50/40 hover:border-yellow-300 border border-slate-200 text-xs font-medium text-slate-800 shadow-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-3.5 w-3.5 text-slate-500" />
                  <span>Research Projects & Grants</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
