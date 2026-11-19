"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { hodService, HodSemesterResultsData } from "@/services/hod.service";
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
  TrendingUp,
  Award,
  AlertTriangle,
  CheckCircle2,
  Users,
  BookOpen,
  Download,
  Sparkles,
  BarChart3,
  Layers,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodSemesterResultsPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodSemesterResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "toppers" | "support" | "arrears"
  >("overview");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await hodService.getSemesterResults();
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to load semester results", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Academic Analytics
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Autonomous Term Result Audit
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <TrendingUp className="h-6 w-6 text-yellow-600" />
            Semester Results & Performance Analytics
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Comprehensive academic performance analytics, subject-wise pass
            percentages, department toppers, and arrear remediation tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            onClick={() =>
              alert(
                "Downloading Department Comprehensive Semester Result Gazette (PDF)...",
              )
            }
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export Result Gazette
          </Button>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Students Appeared
              </span>
              <Users className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.overview.totalStudentsAppeared || 240}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Semesters 3, 5, and 7
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Overall Pass Rate
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-2">
              {data?.overview.passPercentage || 90.8}%
            </div>
            <div className="text-[11px] text-emerald-600 font-bold mt-1">
              {data?.overview.percentageDelta} vs previous semester
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Passed / Cleared
              </span>
              <Award className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.overview.totalStudentsPassed || 218} /{" "}
              {data?.overview.totalStudentsAppeared || 240}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              All registered courses cleared
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Arrear Radar
              </span>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-amber-700 mt-2">
              {data?.overview.totalStudentsFailed || 22}
            </div>
            <div className="text-[11px] text-amber-700 font-semibold mt-1">
              {data?.arrearAnalytics.repeatedArrearsCount || 3} Repeated
              Backlogs
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("overview")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "overview"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <BarChart3 className="h-3.5 w-3.5" />
          Subject-Wise Performance & Pass Rates (
          {data?.subjectResults.length || 4})
        </button>

        <button
          onClick={() => setActiveTab("toppers")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "toppers"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <Award className="h-3.5 w-3.5" />
          Department High Achievers & Toppers ({data?.toppers.length || 3})
        </button>

        <button
          onClick={() => setActiveTab("support")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "support"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
          Students Requiring Support ({data?.studentsNeedingSupport.length || 2}
          )
        </button>

        <button
          onClick={() => setActiveTab("arrears")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "arrears"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900",
          )}
        >
          <Layers className="h-3.5 w-3.5" />
          Arrear Distribution Radar
        </button>
      </div>

      {/* Tab 1: Subject Wise Performance */}
      {activeTab === "overview" && (
        <Card className="border-slate-200 bg-white shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900">
              Subject-Wise Autonomous Result Analysis
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Department pass percentages and average grade points across all
              core instructional subjects.
            </CardDescription>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                  <th className="py-3 px-4">Subject & Faculty</th>
                  <th className="py-3 px-4 text-center">Appeared</th>
                  <th className="py-3 px-4 text-center">Passed</th>
                  <th className="py-3 px-4 text-center">Failed</th>
                  <th className="py-3 px-4">Pass Rate Progress</th>
                  <th className="py-3 px-4 text-center">Avg Grade Point</th>
                  <th className="py-3 px-4 text-right">Academic Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {(data?.subjectResults || []).map((sub) => (
                  <tr key={sub.courseCode} className="hover:bg-yellow-50/30">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">
                        {sub.courseName}
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <span className="font-mono font-bold text-yellow-800 bg-yellow-100 px-1 rounded">
                          {sub.courseCode}
                        </span>
                        • Faculty: {sub.faculty}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-900">
                      {sub.appeared}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-700">
                      {sub.passed}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-red-600">
                      {sub.failed}
                    </td>
                    <td className="py-3 px-4 w-44">
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <span className="font-bold text-slate-800">
                          {sub.passPercentage}%
                        </span>
                        <span className="text-[10px] text-slate-400">
                          Target 85%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={cn(
                            "h-1.5 rounded-full",
                            sub.passPercentage >= 90
                              ? "bg-emerald-500"
                              : sub.passPercentage >= 85
                                ? "bg-yellow-500"
                                : "bg-amber-500",
                          )}
                          style={{ width: `${sub.passPercentage}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-black text-slate-900">
                      {sub.averageGradePoint} / 10.0
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Badge
                        className={cn(
                          "text-[10px] font-bold",
                          sub.passPercentage >= 90
                            ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                            : "bg-yellow-100 text-yellow-900 border-yellow-300",
                        )}
                      >
                        {sub.passPercentage >= 90 ? "EXEMPLARY" : "COMPLIANT"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 2: Toppers */}
      {activeTab === "toppers" && (
        <Card className="border-slate-200 bg-white shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900">
              Department Academic Merit & Top Achievers
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Recognized students with CGPA $\ge 8.5$ and First Class with
              Distinction eligibility.
            </CardDescription>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                  <th className="py-3 px-4 text-center">Rank</th>
                  <th className="py-3 px-4">Student Details</th>
                  <th className="py-3 px-4">Semester</th>
                  <th className="py-3 px-4 text-center">Cumulative CGPA</th>
                  <th className="py-3 px-4 text-center">Term SGPA</th>
                  <th className="py-3 px-4 text-center">Credits Earned</th>
                  <th className="py-3 px-4 text-right">Academic Standing</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {(data?.toppers || []).map((t) => (
                  <tr key={t.rollNumber} className="hover:bg-yellow-50/30">
                    <td className="py-3 px-4 text-center">
                      <div className="h-7 w-7 rounded-full bg-yellow-400 text-slate-950 font-black text-xs flex items-center justify-center mx-auto border border-yellow-500 shadow-xs">
                        #{t.rank}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{t.name}</div>
                      <div className="font-mono text-[11px] text-slate-500">
                        {t.rollNumber}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-700">
                      Semester {t.semester}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-black text-sm text-emerald-700">
                      {t.cgpa}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-900">
                      {t.sgpa}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-700">
                      {t.totalCredits} Credits
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Badge className="bg-yellow-100 text-yellow-950 border-yellow-300 font-bold text-[10px]">
                        {t.status.replace(/_/g, " ")}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Students Needing Support */}
      {activeTab === "support" && (
        <Card className="border-slate-200 bg-white shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900">
              Students Requiring Academic Mentoring & Remedial Support
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Identified based on CGPA &lt; 6.0 or active semester backlogs for
              institutional NAAC Criteria 2.2 remedial tracking.
            </CardDescription>
          </CardHeader>
          <div className="divide-y divide-slate-100">
            {(data?.studentsNeedingSupport || []).map((stu) => (
              <div
                key={stu.rollNumber}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">
                      {stu.name}
                    </span>
                    <span className="font-mono text-xs text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                      {stu.rollNumber}
                    </span>
                    <Badge className="bg-red-100 text-red-800 border-red-200 text-[10px]">
                      {stu.arrears} Arrear{stu.arrears > 1 ? "s" : ""}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-600 mt-1">
                    Arrear Subject(s):{" "}
                    <span className="font-semibold text-red-700 font-mono">
                      {stu.arrearSubjects.join(", ")}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                    <span className="font-bold text-slate-700">
                      Remedial Action:
                    </span>
                    <span>{stu.supportPlan}</span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="font-mono font-bold text-slate-900 text-sm">
                    CGPA: {stu.cgpa}{" "}
                    <span className="text-xs text-slate-400 font-normal">
                      (SGPA: {stu.sgpa})
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-[11px] h-7 px-2.5 mt-1 border-slate-300 text-slate-700 hover:bg-yellow-50"
                    onClick={() =>
                      alert(`Assigned Senior Faculty Mentor to ${stu.name}.`)
                    }
                  >
                    Assign Faculty Mentor
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Tab 4: Arrears Radar */}
      {activeTab === "arrears" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900">
                Subject-Wise Arrear Distribution
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Breakdown of active backlog occurrences by instructional
                subject.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {(data?.arrearAnalytics.subjectWiseArrearBreakdown || []).map(
                (item) => (
                  <div key={item.courseCode} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-900">
                        {item.courseCode} - {item.subject}
                      </span>
                      <span className="font-mono font-bold text-red-600">
                        {item.arrearCount} Arrears
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${(item.arrearCount / 14) * 100}%` }}
                      />
                    </div>
                  </div>
                ),
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900">
                Arrear Classification & Repetition Index
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Identification of students with repeated vs first-time arrears.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div>
                  <div className="font-bold text-slate-900">
                    Single Course Arrear
                  </div>
                  <div className="text-slate-500 text-[11px]">
                    Cleared with targeted coaching
                  </div>
                </div>
                <div className="font-mono font-bold text-base text-slate-900">
                  {data?.arrearAnalytics.singleArrearCount || 16} Students
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div>
                  <div className="font-bold text-slate-900">
                    Multiple Arrears (2+ Courses)
                  </div>
                  <div className="text-slate-500 text-[11px]">
                    Academic counselling initiated
                  </div>
                </div>
                <div className="font-mono font-bold text-base text-amber-700">
                  {data?.arrearAnalytics.multipleArrearsCount || 6} Students
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-red-50/70 border border-red-200">
                <div>
                  <div className="font-bold text-red-900">
                    Repeated Consecutive Arrears
                  </div>
                  <div className="text-red-700 text-[11px]">
                    HOD Proctorial Review mandated
                  </div>
                </div>
                <div className="font-mono font-bold text-base text-red-700">
                  {data?.arrearAnalytics.repeatedArrearsCount || 3} Students
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
