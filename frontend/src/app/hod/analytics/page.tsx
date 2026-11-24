"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Award,
  Users,
  GraduationCap,
  BookOpen,
  CalendarCheck,
  Briefcase,
  FlaskConical,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";
import {
  hodService,
  HodPerformanceAnalyticsData,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodAnalyticsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] =
    useState<HodPerformanceAnalyticsData | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await hodService.getPerformanceAnalytics();
        if (res.data) {
          setAnalytics(res.data);
        }
      } catch {
        addToast({
          title: "Analytics Load Error",
          description: "Could not retrieve department performance metrics.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        Loading multi-dimensional department analytics...
      </div>
    );
  }

  const { academicTrends, facultyAnalytics, departmentGrowth } = analytics || {
    academicTrends: {
      semesterPassRates: [],
      yearWisePerformance: [],
      arrearResolutionVelocity: [],
      attendancePerformanceCorrelation: [],
    },
    facultyAnalytics: {
      totalFaculty: 28,
      cadreDistribution: [],
      workloadCompliance: [],
      lessonPlanDeliveryAverage: 82.8,
      averageMonthlyAttendance: 96.2,
    },
    departmentGrowth: {
      yearlyIntake: [],
      placementRateGrowth: [],
      researchPapersPublished: 34,
      patentsFiled: 7,
      fundedProjectsAmountLakhs: 42.5,
    },
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Department Performance Analytics
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              Multi-Dimensional KPIs
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Real-time correlation across academic pass rates, faculty workloads,
            placement trajectories, and research output.
          </p>
        </div>

        <div className="rounded-lg bg-white border border-slate-200 px-3.5 py-1.5 text-xs text-slate-600 shadow-xs">
          Academic Year: <strong className="text-slate-900">2025-2026</strong>
        </div>
      </div>

      {/* Top Level Growth Banners */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Placement Growth (4Y)
            </span>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            87.8%{" "}
            <span className="text-xs font-normal text-emerald-600">+6.6%</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Up from 81.2% in 2023
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Research Publications
            </span>
            <FlaskConical className="h-4 w-4 text-purple-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {departmentGrowth.researchPapersPublished}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Scopus & SCI indexed papers
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Patents Published
            </span>
            <Award className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {departmentGrowth.patentsFiled}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Indian Patent Office
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Funded Projects Grants
            </span>
            <ShieldCheck className="h-4 w-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            ₹{departmentGrowth.fundedProjectsAmountLakhs}{" "}
            <span className="text-xs font-normal">Lakhs</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            AICTE, DST & Industry Grants
          </div>
        </div>
      </div>

      {/* SECTION 1: ACADEMIC PERFORMANCE TRENDS */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Semester-wise Pass Rate Bar Chart */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Semester Pass Rate Progression (Sem 1 to Sem 6)
              </h2>
              <p className="text-xs text-slate-500">
                Department cohort examination results
              </p>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Avg 90.5%
            </span>
          </div>

          <div className="mt-6 space-y-4">
            {academicTrends.semesterPassRates.map((sem, i) => (
              <div key={i} className="text-xs">
                <div className="flex items-center justify-between font-medium text-slate-700 mb-1">
                  <span className="font-semibold text-slate-900">
                    {sem.semester}
                  </span>
                  <span className="font-mono text-slate-600">
                    {sem.passed} / {sem.appeared} Passed (
                    <strong className="text-slate-900">{sem.passRate}%</strong>)
                  </span>
                </div>
                <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-yellow-400"
                    style={{ width: `${sem.passRate}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Year-wise Performance & CGPA Breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Year-wise Academic Achievement
              </h2>
              <p className="text-xs text-slate-500">
                Pass rates, average CGPA, and distinction holders
              </p>
            </div>
            <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              720 Students
            </span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-semibold text-slate-500">
                <tr>
                  <th className="py-2.5 px-3">Academic Year</th>
                  <th className="py-2.5 px-3 text-center">Pass %</th>
                  <th className="py-2.5 px-3 text-center">Average CGPA</th>
                  <th className="py-2.5 px-3 text-right">Toppers (&gt;=8.5)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {academicTrends.yearWisePerformance.map((yp, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-3 px-3 font-semibold text-slate-900">
                      {yp.year}
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-slate-900">
                      {yp.passPercentage}%
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-medium text-blue-700">
                      {yp.averageCgpa.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-emerald-700">
                      {yp.toppersCount} Students
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* SECTION 2: ATTENDANCE & ARREAR CORRELATIONS */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Attendance vs Academic Performance Correlation */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">
              Attendance vs Academic CGPA Correlation
            </h2>
            <p className="text-xs text-slate-500">
              Empirical correlation proving impact of physical class attendance
            </p>
          </div>

          <div className="mt-4 space-y-3">
            {academicTrends.attendancePerformanceCorrelation.map((tier, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/70 p-3.5"
              >
                <div>
                  <div className="font-semibold text-slate-900 text-xs">
                    {tier.attendanceTier} Attendance
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {tier.students} Students in Cohort
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-base font-bold text-slate-900 font-mono">
                    {tier.averageCgpa.toFixed(2)}{" "}
                    <span className="text-xs font-normal text-slate-500">
                      CGPA
                    </span>
                  </div>
                  <span
                    className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      tier.averageCgpa >= 8
                        ? "bg-emerald-100 text-emerald-800"
                        : tier.averageCgpa >= 7
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                    }`}
                  >
                    {tier.averageCgpa >= 8
                      ? "High Distinction"
                      : tier.averageCgpa >= 7
                        ? "First Class"
                        : "Academic Risk"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Arrear Resolution Velocity */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">
              Arrear Clearance & Recovery Velocity
            </h2>
            <p className="text-xs text-slate-500">
              Effectiveness of remedial coaching and supplementary assessments
            </p>
          </div>

          <div className="mt-4 space-y-3">
            {academicTrends.arrearResolutionVelocity.map((stage, i) => (
              <div key={i} className="text-xs">
                <div className="flex items-center justify-between text-slate-700 font-medium mb-1">
                  <span>{stage.stage}</span>
                  <span className="font-bold text-slate-900">
                    {stage.count} Students ({stage.percentage}%)
                  </span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      i === 0
                        ? "bg-emerald-500"
                        : i === 1
                          ? "bg-yellow-400"
                          : "bg-red-400"
                    }`}
                    style={{ width: `${stage.percentage}%` }}
                  />
                </div>
              </div>
            ))}

            <div className="mt-4 rounded-lg bg-emerald-50 p-3 border border-emerald-200 text-xs text-emerald-800">
              <strong>Remedial Efficacy:</strong> 94% of department backlogs are
              resolved within the subsequent academic cycle.
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: FACULTY WORKLOAD & CADRE DISTRIBUTION */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Cadre Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">
              Faculty Cadre & Ratio Compliance
            </h2>
            <p className="text-xs text-slate-500">
              Cadre ratio 1:2:4 compliance per AICTE and NBA statutory norms
            </p>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            {facultyAnalytics.cadreDistribution.map((cadre, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-center"
              >
                <div className="text-xs font-semibold text-slate-700">
                  {cadre.cadre}
                </div>
                <div className="mt-2 text-2xl font-bold text-slate-900">
                  {cadre.count}
                </div>
                <div className="text-[11px] text-slate-500 font-medium">
                  {cadre.percentage}% of faculty
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 text-xs text-slate-600 flex items-center justify-between border-t border-slate-100 pt-3">
            <span>
              Student-Faculty Ratio (SFR): <strong>1:15 (Compliant)</strong>
            </span>
            <span>
              Faculty Attendance:{" "}
              <strong>{facultyAnalytics.averageMonthlyAttendance}%</strong>
            </span>
          </div>
        </div>

        {/* Workload Compliance Breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">
              Weekly Instructional Workload Distribution
            </h2>
            <p className="text-xs text-slate-500">
              Lecture, tutorial, and lab hours allocation
            </p>
          </div>

          <div className="mt-4 space-y-3">
            {facultyAnalytics.workloadCompliance.map((wl, i) => (
              <div key={i} className="text-xs">
                <div className="flex items-center justify-between text-slate-700 font-medium mb-1">
                  <span>{wl.range}</span>
                  <span className="font-bold text-slate-900">
                    {wl.count} Faculty ({wl.percentage}%)
                  </span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-yellow-400"
                    style={{ width: `${wl.percentage}%` }}
                  />
                </div>
              </div>
            ))}

            <div className="mt-4 rounded-lg bg-blue-50 p-3 border border-blue-200 text-xs text-blue-800">
              <strong>Syllabus Progress:</strong> Department lesson plan
              delivery stands at an average of{" "}
              <strong>{facultyAnalytics.lessonPlanDeliveryAverage}%</strong>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
