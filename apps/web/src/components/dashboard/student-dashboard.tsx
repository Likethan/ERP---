"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/ui/stat-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { studentsService } from "@/services/students.service";
import { academicsService } from "@/services/academics.service";
import { placementsService } from "@/services/placements.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import { TimetableSlotItem } from "@/mocks/academics.mock";
import { JobDriveItem } from "@/mocks/placements.mock";
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  GraduationCap,
  Briefcase,
  ArrowRight,
  FileText,
  BedDouble,
  Bus,
  Sparkles,
  AlertCircle,
} from "lucide-react";

export function StudentDashboard() {
  const [student, setStudent] = useState<StudentComprehensiveDetail | null>(null);
  const [todaySchedule, setTodaySchedule] = useState<TimetableSlotItem[]>([]);
  const [activeDrives, setActiveDrives] = useState<JobDriveItem[]>([]);

  useEffect(() => {
    // Default student persona: Aarav Patel (24CSE0101)
    studentsService.getById("stu-24cse0101").then((res) => {
      if (res.data) setStudent(res.data);
    });
    academicsService.getTimetable("MONDAY").then((res) => {
      setTodaySchedule(res.data.slice(0, 4));
    });
    placementsService.getDrives("INTERVIEWS_ACTIVE").then((res) => {
      setActiveDrives(res.data);
    });
  }, []);

  if (!student) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading student profile...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Student Welcome Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-indigo-950/40 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
            Active Student Portal • {student.rollNumber}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Welcome back, {student.firstName}!
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            {student.program.name} • Semester {student.currentSemester} (Section {student.section})
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/attendance/leaves">
            <Button variant="outline" size="sm">
              Apply for Leave
            </Button>
          </Link>
          <Link href="/app/documents">
            <Button variant="primary" size="sm" leftIcon={<FileText className="h-3.5 w-3.5" />}>
              Document Vault
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Attendance Compliance"
          value={`${student.attendanceSummary.overallPercentage}%`}
          change={{ value: "Safe threshold (>75%)", trend: "up" }}
          description={`${student.attendanceSummary.attendedClasses} of ${student.attendanceSummary.totalClasses} lectures attended`}
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Cumulative GPA"
          value={student.academicStats.cgpa.toFixed(2)}
          change={{ value: `Rank #${student.academicStats.rank} in CSE`, trend: "up" }}
          description={`${student.academicStats.totalCreditsEarned} credits earned • 0 backlogs`}
          variant="indigo"
          icon={<GraduationCap className="h-4 w-4" />}
        />
        <StatCard
          label="Fee Dues Status"
          value={student.financeSummary.pendingDue === 0 ? "₹0 Due" : `₹${student.financeSummary.pendingDue}`}
          change={{ value: "All cleared", trend: "neutral" }}
          description="Annual tuition & hostel levy settled"
          variant="sky"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <StatCard
          label="Placement Pipeline"
          value={`${student.placementSummary.offersReceived} Offer`}
          change={{ value: "18.5 LPA (Cisco)", trend: "up" }}
          description="Round 2 Interview Scheduled"
          variant="amber"
          icon={<Briefcase className="h-4 w-4" />}
        />
      </div>

      {/* Grid: Timetable & Academic Courses vs Career & Logistics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Today's Schedule & Enrolled Courses */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Timetable */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-indigo-400" />
                  Today's Class Schedule
                </CardTitle>
                <CardDescription>
                  Live lecture slots, hall locations, and assigned professors.
                </CardDescription>
              </div>
              <Link href="/app/academics/timetable">
                <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                  Full Timetable <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {todaySchedule.map((slot, idx) => (
                <div
                  key={slot.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-slate-950/60"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono font-bold">
                      0{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-white">
                        {slot.subjectCode} — {slot.subjectName}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {slot.facultyName} • {slot.roomNumber}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-medium text-slate-300">
                      {slot.timeSlot}
                    </span>
                    <div className="text-[10px] text-emerald-400 font-semibold mt-0.5">
                      Confirmed Room
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Enrolled Courses Progress */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Enrolled Academic Courses (5th Semester)</CardTitle>
                <CardDescription>
                  Continuous Internal Assessment marks & individual course attendance.
                </CardDescription>
              </div>
              <Link href="/app/academics/subjects">
                <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                  Curriculum View <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Course</th>
                      <th className="px-4 py-3">Faculty</th>
                      <th className="px-4 py-3">Credits</th>
                      <th className="px-4 py-3">Attendance</th>
                      <th className="px-4 py-3">CIA Marks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {student.enrolledCourses.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-medium text-white">
                          <div>{c.code}</div>
                          <div className="text-[11px] text-slate-400 font-normal">{c.title}</div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-300">{c.faculty}</td>
                        <td className="px-4 py-3.5 font-mono">{c.credits}</td>
                        <td className="px-4 py-3.5">
                          <span className="font-semibold text-emerald-400 font-mono">
                            {c.attendanceRate}%
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono text-slate-200">
                          {c.internalMarks} / 50
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 Col): Placement Status & Campus Logistics */}
        <div className="space-y-6">
          {/* Active Job Opportunities */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-purple-400" />
                Placement Opportunities
              </CardTitle>
              <CardDescription>
                Recruitment drives open for B.Tech CSE students.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeDrives.map((drive) => (
                <div
                  key={drive.id}
                  className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">
                      {drive.companyName}
                    </span>
                    <Badge variant="success">₹{drive.packageLPA} LPA</Badge>
                  </div>
                  <div className="text-xs text-slate-300">{drive.roleTitle}</div>
                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                    <span>Min CGPA: {drive.minimumCGPA}</span>
                    <Link
                      href="/app/placement"
                      className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                    >
                      Status <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Residential & Transport Logistics */}
          <Card>
            <CardHeader>
              <CardTitle>Campus Residential & Logistics</CardTitle>
              <CardDescription>Allocated room & daily bus corridor subscription.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              {student.hostel && (
                <div className="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-950/40">
                  <BedDouble className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-white">{student.hostel.hostelName}</div>
                    <div className="text-slate-400 text-[11px] mt-0.5">
                      {student.hostel.block} • Room {student.hostel.roomNumber} ({student.hostel.bed})
                    </div>
                  </div>
                </div>
              )}

              {student.transport && (
                <div className="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-950/40">
                  <Bus className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-white">
                      {student.transport.routeCode} — {student.transport.routeName}
                    </div>
                    <div className="text-slate-400 text-[11px] mt-0.5">
                      Boarding: {student.transport.stopName} (Bus {student.transport.busNumber})
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
