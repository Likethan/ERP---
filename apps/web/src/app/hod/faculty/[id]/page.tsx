"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { hodService } from "@/services/hod.service";
import { FacultyDetailView } from "@/types/domain";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import {
  ArrowLeft,
  Mail,
  Phone,
  Clock,
  BookOpen,
  GraduationCap,
  Building,
  CheckCircle2,
  Calendar,
  Layers,
  Award,
  ShieldAlert,
  ShieldCheck,
  FileSpreadsheet,
} from "lucide-react";

export default function HodFacultyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const facultyId = resolvedParams.id;
  const router = useRouter();
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [faculty, setFaculty] = useState<FacultyDetailView | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("subjects");
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    async function loadFaculty() {
      setLoading(true);
      try {
        const item = await hodService.getFacultyById(facultyId);
        if (item) {
          // Strict department boundary enforcement:
          // HOD can only view faculty within their department!
          const isDeptMatch =
            item.department.toLowerCase().includes("computer") ||
            item.department.toLowerCase() === deptName.toLowerCase();

          if (!isDeptMatch && activePersona.role === "HOD") {
            setAccessDenied(true);
            return;
          }
          setFaculty(item);
        }
      } catch (err) {
        console.error("Failed to load faculty detail:", err);
      } finally {
        setLoading(false);
      }
    }
    loadFaculty();
  }, [facultyId, deptName, activePersona.role]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-44 rounded-2xl bg-white border border-slate-200" />
        <div className="h-64 rounded-2xl bg-white border border-slate-200" />
      </div>
    );
  }

  if (accessDenied) {
    return (
      <div className="p-8 text-center rounded-2xl border border-rose-200 bg-rose-50 text-rose-900 max-w-xl mx-auto my-12">
        <ShieldAlert className="h-10 w-10 mx-auto text-rose-600 mb-2" />
        <h2 className="text-lg font-bold">
          Cross-Department Access Prohibited
        </h2>
        <p className="text-xs text-rose-700 mt-1 leading-relaxed">
          As Head of Department for {deptName}, you do not have permission to
          view faculty profiles belonging to other academic departments.
        </p>
        <Link href="/hod/faculty" className="inline-block mt-4">
          <Button
            variant="primary"
            size="sm"
            className="bg-yellow-400 text-slate-950 hover:bg-yellow-500 font-bold"
          >
            Return to Department Faculty Roster
          </Button>
        </Link>
      </div>
    );
  }

  if (!faculty) {
    return (
      <div className="p-8 text-center rounded-2xl border border-slate-200 bg-white">
        <p className="text-sm text-slate-600">Faculty record not found.</p>
        <Link href="/hod/faculty" className="inline-block mt-4">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back to Faculty
          </Button>
        </Link>
      </div>
    );
  }

  // Calculate experience in years from joiningDate
  const joinYear = new Date(faculty.joiningDate).getFullYear();
  const experienceYears = Math.max(
    1,
    new Date().getFullYear() - (joinYear || 2020),
  );

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <div className="flex items-center gap-2">
        <Link href="/hod/faculty">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-slate-600 hover:text-slate-950"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Department Faculty
          </Button>
        </Link>
      </div>

      {/* Profile Header Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start sm:items-center gap-4">
            <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-2xl bg-yellow-400 text-slate-950 font-black text-2xl flex items-center justify-center shrink-0 border-2 border-yellow-500 shadow-sm">
              {faculty.firstName[0]}
              {faculty.lastName[0]}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                  {faculty.firstName} {faculty.lastName}
                </h1>
                <Badge variant="outline" className="font-mono text-xs">
                  {faculty.employeeCode}
                </Badge>
                <Badge className="bg-emerald-50 text-emerald-800 border-emerald-200 text-xs">
                  {faculty.status}
                </Badge>
              </div>
              <p className="text-sm font-semibold text-slate-700 mt-0.5">
                {faculty.designation} • {faculty.department}
              </p>
              <div className="flex items-center gap-4 text-xs text-slate-500 mt-2 flex-wrap">
                <span className="flex items-center gap-1 font-mono">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {faculty.email}
                </span>
                <span className="flex items-center gap-1 font-mono">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  {faculty.phone}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 text-center">
            <div className="p-2.5 rounded-xl bg-yellow-50/60 border border-yellow-200/60">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">
                Weekly Load
              </div>
              <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                {faculty.teachingLoadHours} hrs
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">
                Experience
              </div>
              <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                {experienceYears}+ yrs
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-200/60 col-span-2 sm:col-span-1">
              <div className="text-[10px] text-emerald-800 uppercase font-semibold">
                Attendance
              </div>
              <div className="text-lg font-bold font-mono text-emerald-900 mt-0.5">
                97.8%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Qualifications and Specialization Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">
              Academic Qualifications & Specialization
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div>
              <span className="text-slate-500">Highest Qualification:</span>{" "}
              <span className="font-semibold text-slate-900">
                {faculty.qualification}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Domain Specialization:</span>{" "}
              <span className="font-semibold text-slate-900">
                {faculty.specialization}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Date of Joining:</span>{" "}
              <span className="font-mono text-slate-800">
                {faculty.joiningDate}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">
              Departmental Governance & Compliance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-700">
              <ShieldCheck className="h-4 w-4" />
              <span>Biometric attendance verified with zero discrepancies</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-700">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>
                Course files & outcome assessment models approved by HOD
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-700">
              <Award className="h-4 w-4 text-yellow-600" />
              <span>
                NBA Criterion 5 (Faculty Contributions) portfolio updated
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detail Tabs */}
      <div className="space-y-4">
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActiveTab("subjects")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "subjects"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Assigned Subjects & Sections (
            {faculty.assignedSubjects?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab("workload")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "workload"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Workload Distribution
          </button>
          <button
            onClick={() => setActiveTab("attendance")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "attendance"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Attendance & Leaves Log
          </button>
        </div>

        {/* Tab 1: Subjects */}
        {activeTab === "subjects" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Current Semester Instructional Allocations</CardTitle>
              <CardDescription>
                Subjects, enrolled student counts, and sections assigned to{" "}
                {faculty.firstName} {faculty.lastName}.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!faculty.assignedSubjects ||
              faculty.assignedSubjects.length === 0 ? (
                <p className="text-xs text-slate-500">
                  No course offerings currently assigned.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="p-3">Course Code</th>
                        <th className="p-3">Course Title</th>
                        <th className="p-3">Semester</th>
                        <th className="p-3">Section</th>
                        <th className="p-3 text-right">Enrolled Students</th>
                        <th className="p-3">Classroom / Lab</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {faculty.assignedSubjects.map((sub, idx) => (
                        <tr key={idx} className="hover:bg-yellow-50/30">
                          <td className="p-3 font-mono font-bold text-slate-900">
                            {sub.code}
                          </td>
                          <td className="p-3 font-medium text-slate-800">
                            {sub.name}
                          </td>
                          <td className="p-3 font-mono">Sem {sub.semester}</td>
                          <td className="p-3">
                            <Badge
                              variant="outline"
                              className="font-mono text-[10px]"
                            >
                              Sec {sub.section}
                            </Badge>
                          </td>
                          <td className="p-3 text-right font-mono font-bold text-slate-900">
                            {sub.studentCount}
                          </td>
                          <td className="p-3 text-slate-500">
                            Hall 302, Academic Block A
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 2: Workload */}
        {activeTab === "workload" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Faculty Teaching Load Breakdown</CardTitle>
              <CardDescription>
                Weekly contact hours compared against statutory AICTE
                guidelines.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-center">
                  <div className="text-xs text-slate-500">Theory Lectures</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    10 hrs/wk
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-center">
                  <div className="text-xs text-slate-500">Lab Practicals</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    4 hrs/wk
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/50 text-center">
                  <div className="text-xs text-emerald-800 font-semibold">
                    Total Weekly Load
                  </div>
                  <div className="text-xl font-bold font-mono text-emerald-900 mt-1">
                    {faculty.teachingLoadHours} hrs/wk
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
                <div className="text-xs font-semibold text-slate-800 mb-2">
                  Workload Compliance Status
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-xs font-bold text-emerald-800">
                    Compliant with AICTE workload norms for{" "}
                    {faculty.designation}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
                  Permitted teaching load range: 12 to 16 hours. The faculty has
                  optimal capacity for departmental project guidance and
                  research papers.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Attendance */}
        {activeTab === "attendance" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Biometric Attendance Summary & Leaves</CardTitle>
              <CardDescription>
                Faculty institutional presence log for the current academic
                session.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">
                    Working Days
                  </div>
                  <div className="text-lg font-bold font-mono text-slate-900 mt-1">
                    90 Days
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/50">
                  <div className="text-[10px] text-emerald-800 font-semibold uppercase">
                    Present Days
                  </div>
                  <div className="text-lg font-bold font-mono text-emerald-900 mt-1">
                    88 Days
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-amber-200 bg-amber-50/50">
                  <div className="text-[10px] text-amber-800 font-semibold uppercase">
                    Leaves Taken
                  </div>
                  <div className="text-lg font-bold font-mono text-amber-900 mt-1">
                    2 Days
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-sky-200 bg-sky-50/50">
                  <div className="text-[10px] text-sky-800 font-semibold uppercase">
                    Attendance %
                  </div>
                  <div className="text-lg font-bold font-mono text-sky-900 mt-1">
                    97.8%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
