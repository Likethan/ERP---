"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import { facultyService } from "@/services/faculty.service";
import { FacultyDetailView } from "@/types/domain";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import {
  UserCheck,
  ArrowLeft,
  Mail,
  Phone,
  Clock,
  BookOpen,
  CheckCircle2,
  Calendar,
  Building,
  GraduationCap,
  Users,
} from "lucide-react";

export default function FacultyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const facultyId = resolvedParams.id;

  const [faculty, setFaculty] = useState<FacultyDetailView | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    facultyService.getById(facultyId).then((res) => {
      setFaculty(res.data);
      setLoading(false);
    });
  }, [facultyId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center text-slate-400">
        Loading Faculty Record...
      </div>
    );
  }

  if (!faculty) {
    return (
      <div className="space-y-4">
        <Link href="/app/faculty">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Directory
          </Button>
        </Link>
        <EmptyState
          title="Faculty Member Not Found"
          description={`No faculty record found matching ID "${facultyId}".`}
          actionLabel="Return to Faculty Directory"
          onAction={() => window.location.href = "/app/faculty"}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/app/faculty">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Directory
          </Button>
        </Link>
      </div>

      {/* Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-sky-600/30 text-sky-300 border border-sky-500/40 text-2xl font-bold font-mono shrink-0">
              {faculty.firstName[0]}
              {faculty.lastName[0]}
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {faculty.firstName} {faculty.lastName}
                </h1>
                <Badge variant="success" dot>{faculty.status}</Badge>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-300 border border-slate-700">
                  {faculty.employeeCode}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {faculty.designation} • {faculty.department}
              </p>
              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-500" />
                  {faculty.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-500" />
                  {faculty.phone}
                </span>
                <span className="flex items-center gap-1.5">
                  <GraduationCap className="h-3.5 w-3.5 text-slate-500" />
                  {faculty.qualification}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Link href="/app/attendance/sessions">
              <Button variant="primary" size="sm" leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}>
                Mark Attendance
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-xs text-slate-400">Teaching Load</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {faculty.teachingLoadHours} Hrs/wk
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Assigned lecture periods</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-slate-400">Courses Assigned</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {faculty.assignedSubjects.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Odd Semester 2026-27</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-slate-400">Total Enrolled Students</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {faculty.stats.totalStudents}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Across lecture sections</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-slate-400">Average Student Attendance</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {faculty.stats.averageAttendance}%
          </div>
          <div className="text-[11px] text-emerald-400 mt-0.5">Compliant with regulations</div>
        </Card>
      </div>

      {/* Teaching Courses & Today's Schedule Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Assigned Courses */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-sky-400" />
              Assigned Subjects & Sections
            </CardTitle>
            <CardDescription>Courses registered under this faculty member.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {faculty.assignedSubjects.map((sub) => (
              <div
                key={sub.id}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-white">
                    {sub.code} — {sub.name}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Semester {sub.semester} (Section {sub.section}) • {sub.studentCount} Students
                  </div>
                </div>
                <Link href="/app/attendance/sessions">
                  <Button variant="ghost" size="sm" className="text-xs">
                    View Roster
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Today's Schedule */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-indigo-400" />
              Today's Lectures & Labs
            </CardTitle>
            <CardDescription>Scheduled timetable slots for today.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {faculty.todayClasses.map((cls, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-white">{cls.subject}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {cls.section} • {cls.room}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-slate-300 font-medium">{cls.time}</div>
                  <Badge variant={cls.attendanceMarked ? "success" : "warning"} dot className="mt-1">
                    {cls.attendanceMarked ? "Marked" : "Pending"}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
