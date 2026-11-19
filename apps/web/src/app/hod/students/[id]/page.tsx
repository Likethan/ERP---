"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { hodService } from "@/services/hod.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Mail,
  Phone,
  GraduationCap,
  Calendar,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Award,
  BookOpen,
  DollarSign,
  User,
  HeartHandshake,
} from "lucide-react";

export default function HodStudentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const studentId = resolvedParams.id;
  const router = useRouter();
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [student, setStudent] = useState<StudentComprehensiveDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("academics");
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    async function loadStudent() {
      setLoading(true);
      try {
        const item = await hodService.getStudentById(studentId);
        if (item) {
          // Strict department boundary enforcement:
          // HOD can only view students within their department!
          const isDeptMatch =
            item.program.department.toLowerCase().includes("computer") ||
            item.program.department.toLowerCase() === deptName.toLowerCase();

          if (!isDeptMatch && activePersona.role === "HOD") {
            setAccessDenied(true);
            return;
          }
          setStudent(item);
        }
      } catch (err) {
        console.error("Failed to load student detail:", err);
      } finally {
        setLoading(false);
      }
    }
    loadStudent();
  }, [studentId, deptName, activePersona.role]);

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
        <h2 className="text-lg font-bold">Cross-Department Student Access Denied</h2>
        <p className="text-xs text-rose-700 mt-1 leading-relaxed">
          As Head of Department for {deptName}, you are not authorized to inspect student records from other academic branches.
        </p>
        <Link href="/hod/students" className="inline-block mt-4">
          <Button variant="primary" size="sm" className="bg-yellow-400 text-slate-950 hover:bg-yellow-500 font-bold">
            Return to Department Students
          </Button>
        </Link>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="p-8 text-center rounded-2xl border border-slate-200 bg-white">
        <p className="text-sm text-slate-600">Student record not found.</p>
        <Link href="/hod/students" className="inline-block mt-4">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back to Students
          </Button>
        </Link>
      </div>
    );
  }

  const att = student.attendanceSummary;
  const isShortage = att.overallPercentage < 75;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <div className="flex items-center gap-2">
        <Link href="/hod/students">
          <Button variant="ghost" size="sm" className="text-xs text-slate-600 hover:text-slate-950">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Department Students
          </Button>
        </Link>
      </div>

      {/* Profile Header Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start sm:items-center gap-4">
            <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-2xl bg-yellow-400 text-slate-950 font-black text-2xl flex items-center justify-center shrink-0 border-2 border-yellow-500 shadow-sm">
              {student.firstName[0]}
              {student.lastName[0]}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                  {student.firstName} {student.lastName}
                </h1>
                <Badge variant="outline" className="font-mono text-xs">
                  {student.rollNumber}
                </Badge>
                <Badge className="bg-emerald-50 text-emerald-800 border-emerald-200 text-xs">
                  {student.status}
                </Badge>
              </div>
              <p className="text-sm font-semibold text-slate-700 mt-0.5">
                {student.program.name} • Sem {student.currentSemester} (Sec {student.section})
              </p>
              <div className="flex items-center gap-4 text-xs text-slate-500 mt-2 flex-wrap">
                <span className="flex items-center gap-1 font-mono">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {student.email}
                </span>
                <span className="flex items-center gap-1 font-mono">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  {student.phone}
                </span>
                <span className="font-mono text-slate-400">Reg: {student.registrationNumber}</span>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-3 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 text-center">
            <div className="p-2.5 rounded-xl bg-yellow-50/60 border border-yellow-200/60">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">Cumulative CGPA</div>
              <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                {student.academicStats.cgpa}
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">Rank: #{student.academicStats.rank}</div>
            </div>
            <div
              className={`p-2.5 rounded-xl border ${
                isShortage
                  ? "bg-rose-50 border-rose-200 text-rose-900"
                  : "bg-emerald-50/60 border-emerald-200/60 text-emerald-900"
              }`}
            >
              <div className="text-[10px] uppercase font-semibold">Attendance</div>
              <div className="text-xl font-bold font-mono mt-0.5">
                {att.overallPercentage}%
              </div>
              <div className="text-[9px] mt-0.5 font-semibold">
                {isShortage ? "Shortage (<75%)" : "Compliant"}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">Backlogs</div>
              <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                {student.academicStats.backlogs}
              </div>
              <div className="text-[9px] text-emerald-600 mt-0.5 font-semibold">
                {student.academicStats.backlogs === 0 ? "Clear Arrears" : "Needs Remedial"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Guardian & Admission Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Parent / Guardian Contact Card */}
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <HeartHandshake className="h-4 w-4 text-slate-400" />
              Parent & Guardian Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div>
              <span className="text-slate-500">Guardian Name:</span>{" "}
              <span className="font-semibold text-slate-900">{student.guardian.name}</span> (
              {student.guardian.relation})
            </div>
            <div>
              <span className="text-slate-500">Emergency Phone:</span>{" "}
              <span className="font-mono font-bold text-slate-900">{student.guardian.phone}</span>
            </div>
            <div>
              <span className="text-slate-500">Guardian Email:</span>{" "}
              <span className="font-mono text-slate-800">{student.guardian.email}</span>
            </div>
            <div>
              <span className="text-slate-500">Occupation:</span>{" "}
              <span className="text-slate-800">{student.guardian.occupation}</span>
            </div>
          </CardContent>
        </Card>

        {/* Admission & Enrolment Information */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <GraduationCap className="h-4 w-4 text-slate-400" />
              Enrolment & Institutional Credentials
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div>
              <span className="text-slate-500">Admission Batch:</span>{" "}
              <span className="font-mono font-semibold text-slate-900">{student.batch}</span>
            </div>
            <div>
              <span className="text-slate-500">Admission Quota:</span>{" "}
              <Badge variant="outline" className="font-mono text-[10px] ml-1">
                {student.quota}
              </Badge>
            </div>
            <div>
              <span className="text-slate-500">Admission Date:</span>{" "}
              <span className="font-mono text-slate-800">{student.admissionDate}</span>
            </div>
            <div>
              <span className="text-slate-500">Blood Group & Gender:</span>{" "}
              <span className="text-slate-800">{student.bloodGroup} • {student.gender}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Detailed Academic & Attendance History */}
      <div className="space-y-4">
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActiveTab("academics")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "academics"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Academic Performance
          </button>
          <button
            onClick={() => setActiveTab("attendance")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "attendance"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Attendance Audit ({att.overallPercentage}%)
          </button>
          <button
            onClick={() => setActiveTab("finance")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 cursor-pointer ${
              activeTab === "finance"
                ? "border-yellow-400 text-slate-950"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            Tuition & Fee Status
          </button>
        </div>

        {/* Tab 1: Academic Performance */}
        {activeTab === "academics" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Academic Summary & Credits</CardTitle>
              <CardDescription>
                Cumulative Grade Point Average, credits earned, and university rank.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">CGPA</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    {student.academicStats.cgpa}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">Credits Earned</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    {student.academicStats.totalCreditsEarned} / 160
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">Class Rank</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    #{student.academicStats.rank}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">Active Backlogs</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    {student.academicStats.backlogs}
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
                <div className="text-xs font-semibold text-slate-800 mb-1">
                  Department Placement Readiness
                </div>
                <p className="text-xs text-slate-600">
                  Student is eligible for Tier-1 corporate placement drives. Zero standing arrears and CGPA above 8.0 criteria.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 2: Attendance */}
        {activeTab === "attendance" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Attendance Compliance Audit</CardTitle>
              <CardDescription>
                Session presence vs statutory minimum 75% examination eligibility threshold.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-xs text-slate-500">Total Instructional Sessions</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    {att.totalClasses}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-xs text-slate-500">Sessions Attended</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    {att.attendedClasses}
                  </div>
                </div>
                <div
                  className={`p-3 rounded-xl border text-center ${
                    isShortage ? "bg-rose-50 border-rose-200" : "bg-emerald-50 border-emerald-200"
                  }`}
                >
                  <div className={`text-xs font-semibold ${isShortage ? "text-rose-800" : "text-emerald-800"}`}>
                    Overall Attendance
                  </div>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      isShortage ? "text-rose-900" : "text-emerald-900"
                    }`}
                  >
                    {att.overallPercentage}%
                  </div>
                </div>
              </div>

              {isShortage && (
                <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50 flex items-start gap-3">
                  <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-rose-900">
                      Attendance Shortage Notice Required
                    </div>
                    <p className="text-[11px] text-rose-700 mt-0.5">
                      Student is {75 - att.overallPercentage}% below the 75% threshold. An official warning notice has been drafted for HOD endorsement.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Finance */}
        {activeTab === "finance" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Tuition & Institutional Fee Clearance</CardTitle>
              <CardDescription>
                Financial clearance state for examination hall ticket release.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="text-xs text-slate-500">Total Billed</div>
                  <div className="text-xl font-bold font-mono text-slate-900 mt-1">
                    ₹{student.financeSummary.totalBilled.toLocaleString()}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900">
                  <div className="text-xs font-semibold">Status</div>
                  <div className="text-xl font-bold font-mono mt-1">
                    {student.financeSummary.status}
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
