"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import {
  DepartmentItem,
  ProgramItem,
  SubjectItem,
  CurriculumSchemeItem,
  CourseOfferingItem,
  TimetableSlotItem,
} from "@/mocks/academics.mock";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/ui/skeleton";
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
} from "lucide-react";

export default function AcademicsHubPage() {
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [curricula, setCurricula] = useState<CurriculumSchemeItem[]>([]);
  const [offerings, setOfferings] = useState<CourseOfferingItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [deptRes, subRes, curRes, offRes] = await Promise.all([
        academicsService.getDepartments(),
        academicsService.getSubjects(),
        academicsService.getCurricula(),
        academicsService.getCourseOfferings(),
      ]);
      setDepartments(deptRes.data);
      setSubjects(subRes.data);
      setCurricula(curRes.data);
      setOfferings(offRes.data);
      setLoading(false);
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <BookOpen className="h-3 w-3" />
            Academic Operations • Engine Hub
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Academic Programs, Curriculum & Timetable
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Regulated CBCS curricula schemes, syllabus course offerings, faculty allocations, and conflict-free timetables.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/app/academics/subjects">
            <Button variant="outline" size="sm" leftIcon={<BookOpen className="h-3.5 w-3.5" />}>
              Subjects Catalog
            </Button>
          </Link>
          <Link href="/app/academics/timetable">
            <Button variant="primary" size="sm" leftIcon={<Calendar className="h-3.5 w-3.5" />}>
              Master Timetable
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Curricula Schemes"
          value={curricula.length}
          description="Autonomous R-2024 & R-2026 CBCS"
          variant="indigo"
          icon={<FileSpreadsheet className="h-4 w-4" />}
        />
        <StatCard
          label="Catalogued Subjects"
          value={subjects.length + 38}
          description="Theory, Labs, and Electives"
          variant="emerald"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Active Course Offerings"
          value={offerings.length + 24}
          description="Sections with assigned faculty"
          variant="sky"
          icon={<CheckSquare className="h-4 w-4" />}
        />
        <StatCard
          label="Weekly Scheduled Slots"
          value="184 Slots"
          description="0 lecture or room collisions"
          variant="amber"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Navigation Sub-Modules Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
            Semester structure, elective groups, and credit schemes.
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
            Subject to faculty assignment, sections, and student enrollment.
          </p>
        </Link>

        <Link
          href="/app/academics/timetable"
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-all text-left group"
        >
          <Calendar className="h-5 w-5 text-amber-400 mb-3" />
          <h3 className="text-sm font-semibold text-white group-hover:text-amber-300">
            Conflict-Free Timetable
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Day, slot, room number, faculty, and student section mapping.
          </p>
        </Link>
      </div>

      {/* Active Course Offerings Roster */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Active Course Offerings (Odd Semester 2026–2027)</CardTitle>
            <CardDescription>
              Sections running with faculty lead assignments and live student enrollment.
            </CardDescription>
          </div>
          <Link href="/app/academics/course-offerings">
            <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
              All Offerings <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Section</th>
                  <th className="px-4 py-3">Primary Faculty</th>
                  <th className="px-4 py-3">Enrolled</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {offerings.map((off) => (
                  <tr key={off.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-white">
                      <div>{off.subjectCode} — {off.subjectName}</div>
                      <div className="text-[11px] text-slate-400">{off.credits} Credits</div>
                    </td>
                    <td className="px-4 py-3.5 text-slate-300">{off.department}</td>
                    <td className="px-4 py-3.5">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300 border border-slate-700">
                        Sem {off.semester} - Sec {off.section}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-200">{off.facultyName}</td>
                    <td className="px-4 py-3.5 font-mono">{off.enrolledStudents} Students</td>
                    <td className="px-4 py-3.5">
                      <Badge variant="success" dot>{off.status}</Badge>
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
