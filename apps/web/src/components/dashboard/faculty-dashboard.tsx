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
import { facultyService } from "@/services/faculty.service";
import { FacultyDetailView } from "@/types/domain";
import {
  Clock,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  FileSpreadsheet,
  Users,
} from "lucide-react";

export function FacultyDashboard() {
  const [faculty, setFaculty] = useState<FacultyDetailView | null>(null);

  useEffect(() => {
    // Default faculty: Dr. Rajesh Sharma
    facultyService.getById("fac-cse-01").then((res) => {
      if (res.data) setFaculty(res.data);
    });
  }, []);

  if (!faculty) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading faculty profile...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Faculty Welcome Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-sky-950/40 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/10 px-2.5 py-0.5 text-xs font-semibold text-sky-400 border border-sky-500/20 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
            Faculty Academic Workspace • {faculty.employeeCode}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Welcome, {faculty.firstName} {faculty.lastName}!
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            {faculty.designation} • {faculty.department}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/attendance/sessions">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
            >
              Mark Class Attendance
            </Button>
          </Link>
          <Link href="/app/examinations/marks">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            >
              Enter CIA Marks
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
          description="Across 3 lecture sections"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Course Attendance Rate"
          value={`${faculty.stats.averageAttendance}%`}
          change={{ value: "Compliant", trend: "up" }}
          description="Average student attendance"
          variant="sky"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Weekly Teaching Load"
          value={`${faculty.teachingLoadHours} Hrs`}
          description="14 of 16 prescribed credit hours"
          variant="amber"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Main Grid: Today's Lectures & Pending Attendance Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Classes List (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-sky-400" />
                  Today's Assigned Lecture Slots
                </CardTitle>
                <CardDescription>
                  Sessions scheduled for today across assigned halls.
                </CardDescription>
              </div>
              <Link href="/app/academics/timetable">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-slate-400 hover:text-white"
                >
                  My Timetable <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {faculty.todayClasses.map((cls, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-slate-950/60"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-600/20 text-sky-300 border border-sky-500/30 text-xs font-mono font-bold">
                      0{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-white">
                        {cls.subject}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {cls.section} • {cls.room}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-medium text-slate-300">
                      {cls.time}
                    </span>
                    <div className="mt-1">
                      {cls.attendanceMarked ? (
                        <Badge variant="success" dot>
                          Marked
                        </Badge>
                      ) : (
                        <Badge variant="warning" dot>
                          Pending
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Assigned Subjects & Student Inquiries */}
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
                  className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-semibold text-white">
                      {sub.code} — {sub.name}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Sem {sub.semester} ({sub.section}) • {sub.studentCount}{" "}
                      Students
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
        </div>
      </div>
    </div>
  );
}
