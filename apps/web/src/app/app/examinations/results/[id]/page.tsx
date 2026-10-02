"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { examinationsService } from "@/services/examinations.service";
import { Result } from "@/types/examinations";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Award,
  ArrowLeft,
  CheckCircle2,
  Calendar,
  Layers,
  Globe,
  Lock,
  ExternalLink,
  BookOpen,
} from "lucide-react";

export default function ResultDetailPage() {
  const params = useParams();
  const resultId = params?.id as string;
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    async function loadResult() {
      if (!resultId) return;
      try {
        setLoading(true);
        const res = await examinationsService.getResultById(resultId);
        setResult(res.data);
      } catch (err: unknown) {
        showToast({
          title: "Error",
          message: err instanceof Error ? err.message : "Result not found",
          type: "error",
        });
      } finally {
        setLoading(false);
      }
    }

    loadResult();
  }, [resultId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Loading candidate result...
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-slate-500">Result record not found</p>
        <Link href="/app/examinations/results">
          <Button variant="outline" size="sm" className="mt-4">
            Back to Results
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <Link
            href="/app/examinations/results"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Results Ledger
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {result.studentName}
            </h1>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                result.status === "PASS"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
              }`}
            >
              {result.status}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {result.rollNumber} • {result.program} (Semester {result.semester})
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/students/${result.studentId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <ExternalLink className="h-3.5 w-3.5" />
              Student 360° Profile
            </Button>
          </Link>
          <Link href={`/app/attendance/students/${result.studentId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <BookOpen className="h-3.5 w-3.5" />
              Attendance 360°
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Percentage"
          value={`${result.percentage}%`}
          description={`${result.totalMarks} / ${result.maxMarks} points`}
          icon={<Award className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Awarded Letter Grade"
          value={result.grade}
          description="UGC 10-Point CBCS Scale"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Grade Point"
          value={`${result.gradePoint}.0`}
          description={`${result.credits} Academic Credits`}
          icon={<Layers className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Publication Status"
          value={result.isPublished ? "Published" : "Internal"}
          description={result.isPublished ? "Visible to student" : "Pending batch release"}
          icon={<Globe className="h-5 w-5 text-purple-600" />}
        />
      </div>

      {/* Course Context & Assessment Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white border-b border-slate-100 pb-2 dark:border-slate-800">
            Course & Paper Details
          </h3>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400">Subject Code & Name:</span>
              <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                {result.courseCode} - {result.courseName}
              </p>
            </div>
            <div>
              <span className="text-slate-400">Course Credits:</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                {result.credits} Credits (Choice Based)
              </p>
            </div>
            <div>
              <span className="text-slate-400">Faculty Instructor:</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                {result.facultyName}
              </p>
            </div>
            <div>
              <span className="text-slate-400">Examination Session:</span>
              <p className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                {result.examinationName}
              </p>
            </div>
          </div>
        </div>

        {/* Detailed Assessment Breakdown */}
        <div className="md:col-span-2 p-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white border-b border-slate-100 pb-2 dark:border-slate-800 flex items-center justify-between">
            <span>Evaluation Components Breakdown</span>
            <span className="text-xs text-indigo-600 font-normal">Weighted CBCS Aggregate</span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="p-2.5">Component</th>
                  <th className="p-2.5">Category</th>
                  <th className="p-2.5 text-right">Raw Score</th>
                  <th className="p-2.5 text-right">Weight</th>
                  <th className="p-2.5 text-right">Weighted Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {result.assessmentBreakdown.map((item, idx) => (
                  <tr key={idx}>
                    <td className="p-2.5 font-medium text-slate-900 dark:text-white">
                      {item.componentName}
                    </td>
                    <td className="p-2.5 text-slate-500">{item.componentType}</td>
                    <td className="p-2.5 text-right font-mono font-semibold">
                      {item.obtainedMarks} / {item.maxMarks}
                    </td>
                    <td className="p-2.5 text-right text-slate-500">{item.weightage}%</td>
                    <td className="p-2.5 text-right font-bold text-indigo-600 dark:text-indigo-400">
                      {item.weightedScore.toFixed(1)} pts
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="border-t-2 border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30 font-bold">
                <tr>
                  <td colSpan={2} className="p-2.5">Final Computed Total</td>
                  <td className="p-2.5 text-right font-mono">{result.totalMarks} / {result.maxMarks}</td>
                  <td className="p-2.5 text-right">100%</td>
                  <td className="p-2.5 text-right text-indigo-700 dark:text-indigo-300">
                    {result.percentage}% ({result.grade})
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* Lifecycle Timeline */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          Result Lifecycle & Publication Timeline
        </h3>
        <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-700 pl-8 text-xs">
          <div className="relative">
            <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-emerald-500 ring-4 ring-white dark:ring-slate-900" />
            <p className="font-semibold text-slate-900 dark:text-white">Marks Scored & Verified</p>
            <p className="text-slate-400">Submitted by course faculty {result.facultyName}</p>
          </div>
          <div className="relative">
            <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-blue-500 ring-4 ring-white dark:ring-slate-900" />
            <p className="font-semibold text-slate-900 dark:text-white">Grades Computed (CBCS CBCS Scale)</p>
            <p className="text-slate-400">Mapped to Grade {result.grade} ({result.gradePoint}.0 GP)</p>
          </div>
          <div className="relative">
            <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-purple-500 ring-4 ring-white dark:ring-slate-900" />
            <p className="font-semibold text-slate-900 dark:text-white">Result Ratified & Finalized</p>
            <p className="text-slate-400">{new Date(result.finalizedAt || "").toLocaleString()}</p>
          </div>
          {result.isPublished && (
            <div className="relative">
              <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-teal-500 ring-4 ring-white dark:ring-slate-900" />
              <p className="font-semibold text-slate-900 dark:text-white">Published to Student Portal</p>
              <p className="text-slate-400">{new Date(result.publishedAt || "").toLocaleString()}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
