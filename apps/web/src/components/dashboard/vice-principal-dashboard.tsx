"use client";

import React from "react";
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
import {
  GraduationCap,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Building,
  Sparkles,
  BookOpen,
  Award,
  Clock,
  ShieldCheck,
  FileCheck,
  Users,
} from "lucide-react";

const DEPARTMENT_ACADEMIC_HEALTH = [
  {
    name: "Computer Science & Engineering",
    hod: "Dr. K. S. Anand",
    students: 720,
    facultyRatio: "1:15",
    attendance: "91.4%",
    syllabusProgress: "86%",
    accreditationScore: "3.78",
    status: "EXEMPLARY",
  },
  {
    name: "Electronics & Communication",
    hod: "Dr. Meenakshi S.",
    students: 640,
    facultyRatio: "1:16",
    attendance: "89.2%",
    syllabusProgress: "84%",
    accreditationScore: "3.65",
    status: "ON_TRACK",
  },
  {
    name: "Mechanical Engineering",
    hod: "Dr. R. Venkatraman",
    students: 480,
    facultyRatio: "1:14",
    attendance: "85.8%",
    syllabusProgress: "79%",
    accreditationScore: "3.52",
    status: "ON_TRACK",
  },
  {
    name: "Civil Engineering",
    hod: "Dr. P. Balaji",
    students: 360,
    facultyRatio: "1:15",
    attendance: "87.1%",
    syllabusProgress: "82%",
    accreditationScore: "3.58",
    status: "ON_TRACK",
  },
  {
    name: "Electrical & Electronics",
    hod: "Dr. S. Gayathri",
    students: 420,
    facultyRatio: "1:17",
    attendance: "84.3%",
    syllabusProgress: "76%",
    accreditationScore: "3.48",
    status: "ATTENTION_NEEDED",
  },
];

const PENDING_STATUTORY_APPROVALS = [
  {
    id: "appr-01",
    type: "Curriculum Syllabus Revision",
    dept: "Computer Science (AI & ML Specialization)",
    submittedBy: "Dr. K. S. Anand",
    date: "Today, 10:30 AM",
    urgency: "HIGH",
    status: "PENDING_REVIEW",
  },
  {
    id: "appr-02",
    type: "End-Semester Exam Question Bank Moderation",
    dept: "School of Computing & Electronics",
    submittedBy: "Board of Examiners",
    date: "Yesterday",
    urgency: "CRITICAL",
    status: "PENDING_AUDIT",
  },
  {
    id: "appr-03",
    type: "Medical Leave Condonation Batch (Attendance <75%)",
    dept: "Student Affairs & Registrar Office",
    submittedBy: "Prof. S. K. Patil",
    date: "Oct 24, 2026",
    urgency: "MEDIUM",
    status: "AWAITING_SANCTION",
  },
  {
    id: "appr-04",
    type: "NIRF Research Publication Audit Signoff",
    dept: "Research & Innovation Cell",
    submittedBy: "Dr. Rajesh Sharma",
    date: "Oct 23, 2026",
    urgency: "MEDIUM",
    status: "READY_FOR_SIGNOFF",
  },
];

export function VicePrincipalDashboard() {
  return (
    <div className="space-y-6">
      {/* Header & Institutional Overview */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
            Vice Principal Operations • Academic Oversight & Statutory Sanctions
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Academic Operations & Institutional Oversight
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Real-time curriculum delivery, teaching quality audits, faculty workloads, and statutory approvals for VSB Campus.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/app/accreditation">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Award className="h-3.5 w-3.5 text-indigo-400" />}
            >
              Accreditation Cell
            </Button>
          </Link>
          <Link href="/app/examinations">
            <Button variant="primary" size="sm">
              Academic Approvals
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Institution Attendance Rate"
          value="88.4%"
          change={{ value: "+2.1% MoM", trend: "up" }}
          description="Average across 14 departments and 4,800 active students"
          variant="indigo"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Faculty Workload Compliance"
          value="96.2%"
          change={{ value: "Optimal", trend: "neutral" }}
          description="UGC/AICTE lecture & lab contact hours balanced"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="NAAC Quality Index (CGPA)"
          value="3.62 / 4.00"
          change={{ value: "A++ Target", trend: "up" }}
          description="Cycle 3 institutional self-study metric readiness"
          variant="amber"
          icon={<Award className="h-4 w-4" />}
        />
        <StatCard
          label="Curricular Syllabus Progress"
          value="81.5%"
          change={{ value: "+4.8% this week", trend: "up" }}
          description="Even semester teaching schedules ahead of exam cutoff"
          variant="sky"
          icon={<BookOpen className="h-4 w-4" />}
        />
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Department Academic Performance Matrix (2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <Building className="h-4 w-4 text-indigo-400" />
                  Department Academic Operations Matrix
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Head of Department academic progress, attendance adherence, and quality audits.
                </CardDescription>
              </div>
              <Link href="/app/departments">
                <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold text-[10px]">
                    <tr>
                      <th className="pb-3">Department & HOD</th>
                      <th className="pb-3 text-center">Students</th>
                      <th className="pb-3 text-center">Attendance</th>
                      <th className="pb-3 text-center">Syllabus</th>
                      <th className="pb-3 text-center">NAAC Score</th>
                      <th className="pb-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-medium">
                    {DEPARTMENT_ACADEMIC_HEALTH.map((dept) => (
                      <tr key={dept.name} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-3">
                          <div className="font-semibold text-slate-200">{dept.name}</div>
                          <div className="text-[11px] text-slate-400">{dept.hod} • Ratio {dept.facultyRatio}</div>
                        </td>
                        <td className="py-3 text-center text-slate-300 font-semibold">{dept.students}</td>
                        <td className="py-3 text-center">
                          <span className="font-semibold text-emerald-400">{dept.attendance}</span>
                        </td>
                        <td className="py-3 text-center">
                          <span className="font-semibold text-sky-400">{dept.syllabusProgress}</span>
                        </td>
                        <td className="py-3 text-center font-bold text-slate-200">{dept.accreditationScore}</td>
                        <td className="py-3 text-right">
                          <Badge
                            variant={
                              dept.status === "EXEMPLARY"
                                ? "success"
                                : dept.status === "ON_TRACK"
                                ? "info"
                                : "warning"
                            }
                          >
                            {dept.status === "EXEMPLARY"
                              ? "Exemplary"
                              : dept.status === "ON_TRACK"
                              ? "On Track"
                              : "Review Needed"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pending Statutory & Executive Approvals Panel (1 Column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <FileCheck className="h-4 w-4 text-amber-400" />
                  Statutory Approvals
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Submissions requiring Vice Principal executive sign-off.
                </CardDescription>
              </div>
              <Badge variant="warning">
                4 Pending
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {PENDING_STATUTORY_APPROVALS.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold text-xs text-slate-200">{item.type}</div>
                    <Badge
                      variant={
                        item.urgency === "CRITICAL"
                          ? "danger"
                          : item.urgency === "HIGH"
                          ? "warning"
                          : "neutral"
                      }
                    >
                      {item.urgency}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">{item.dept}</div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/80 text-[10px] text-slate-400">
                    <span>By {item.submittedBy}</span>
                    <span>{item.date}</span>
                  </div>
                </div>
              ))}

              <Link href="/app/examinations/approvals" className="block w-full pt-1">
                <Button variant="outline" size="sm" className="w-full text-xs">
                  Open Executive Approval Queue
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Quick Institutional Links */}
          <Card className="bg-gradient-to-br from-indigo-950/30 to-slate-900/60 border-indigo-900/40">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs uppercase font-bold tracking-wider text-indigo-300 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5" />
                Executive Governance Links
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link
                href="/app/faculty"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-200 transition-colors"
              >
                <span>Faculty Teaching Registry & Leaves</span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
              </Link>
              <Link
                href="/app/accreditation"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-200 transition-colors"
              >
                <span>NIRF / NAAC Quality Metrics</span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
              </Link>
              <Link
                href="/app/intelligence"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-200 transition-colors"
              >
                <span>Campus AI Predictive Analytics</span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
