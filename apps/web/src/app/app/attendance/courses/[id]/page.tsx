"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceCourseSummary, AttendanceStudentSummary } from "@/types/attendance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  ArrowLeft,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  User,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function CourseAttendanceDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const courseOfferingId = resolvedParams.id;
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [course, setCourse] = useState<AttendanceCourseSummary | null>(null);
  const [students, setStudents] = useState<AttendanceStudentSummary[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [cRes, sRes] = await Promise.all([
          attendanceService.getCourseAttendanceSummary(courseOfferingId),
          attendanceService.listStudentSummaries(),
        ]);

        if (cRes.success && cRes.data) {
          setCourse(cRes.data);
        }
        if (sRes.success) {
          setStudents(sRes.data);
        }
      } catch (err) {
        console.error("Failed to load course attendance detail", err);
        showToast({ type: "error", title: "Load Error", message: "Failed to load course attendance detail." });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [courseOfferingId]);

  if (loading && !course) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">Course Not Found</h3>
        <p className="mt-1 text-xs text-slate-500">The requested course offering attendance register could not be resolved.</p>
        <Link href="/app/attendance/courses" className="mt-4 inline-block">
          <Button variant="outline" size="sm">Back to Courses</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/app/attendance/courses">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {course.courseCode}: {course.courseName}
              </h1>
              <Badge variant="info">Section {course.section}</Badge>
            </div>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Faculty Instructor: <strong className="text-slate-700 dark:text-slate-300">{course.facultyName}</strong> • Semester 5
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/academics/course-offerings/${course.courseOfferingId}`}>
            <Button variant="outline" size="sm" className="text-xs">
              View Course Offering
            </Button>
          </Link>
          <Link href="/app/attendance/sessions">
            <Button variant="primary" size="sm" className="text-xs">
              Take Attendance
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Lectures Delivered"
          value={String(course.totalSessions)}
          description="Academic period sessions"
          icon={<CalendarCheck className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Class Average Attendance"
          value={`${course.percentage}%`}
          description="Effective student attendance rate"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Students Below 75%"
          value={String(course.studentsBelowThresholdCount || 0)}
          description="Debarment threshold violation"
          icon={<ShieldAlert className="h-5 w-5 text-rose-600" />}
        />
        <StatCard
          title="Students in Warning Zone"
          value={String(course.studentsAtRiskCount || 0)}
          description="Attendance between 75% and 79.9%"
          icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
        />
      </div>

      {/* Student Attendance Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Enrolled Cohort Attendance Registry
            </h3>
            <p className="text-[11px] text-slate-500">
              Student-by-student attendance tallies for {course.courseCode}
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            {students.length} Students
          </Badge>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400">
                <th className="pb-3 font-semibold">Student Name</th>
                <th className="pb-3 font-semibold">Roll Number</th>
                <th className="pb-3 font-semibold text-center">Attended Sessions</th>
                <th className="pb-3 font-semibold text-center">Attendance %</th>
                <th className="pb-3 font-semibold text-right">Status</th>
                <th className="pb-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {students.map((student) => {
                const courseRecord = student.courseSummaries.find(
                  (c) => c.courseCode === course.courseCode
                );
                const percent = courseRecord ? courseRecord.percentage : student.percentage;
                const attended = courseRecord ? courseRecord.presentCount : student.presentCount;

                return (
                  <tr key={student.studentId} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-3 font-semibold text-slate-900 dark:text-white">
                      {student.studentName}
                    </td>
                    <td className="py-3 text-slate-500">{student.rollNumber}</td>
                    <td className="py-3 text-center text-slate-600 dark:text-slate-400">
                      {attended} / {course.totalSessions}
                    </td>
                    <td className="py-3 text-center">
                      <span
                        className={`font-bold ${
                          percent >= 80
                            ? "text-emerald-600 dark:text-emerald-400"
                            : percent >= 75
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {percent}%
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <Badge
                        variant={
                          percent >= 80 ? "success" : percent >= 75 ? "warning" : "destructive"
                        }
                        className="text-[10px]"
                      >
                        {percent >= 80 ? "Eligible" : percent >= 75 ? "Warning" : "Shortage"}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      <Link href={`/app/attendance/students/${student.studentId}`}>
                        <Button size="sm" variant="ghost" className="h-7 text-xs text-indigo-600 hover:text-indigo-700">
                          Student 360°
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
