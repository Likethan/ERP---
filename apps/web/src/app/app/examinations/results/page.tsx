"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import { Result, ResultStatus } from "@/types/examinations";
import { DEFAULT_GRADE_SCALE } from "@/services/grading-calculator";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Award,
  Lock,
  Globe,
  CheckCircle2,
  Filter,
  GraduationCap,
  ArrowRight,
  Sparkles,
  BookOpen,
  Info,
} from "lucide-react";

export default function ResultsAndFinalizationPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<Result[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedDept, setSelectedDept] = useState<string>("ALL");

  // Finalization State
  const [finalizeModalOpen, setFinalizeModalOpen] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  // Grade Scale Modal
  const [scaleModalOpen, setScaleModalOpen] = useState(false);

  const loadResults = async () => {
    try {
      setLoading(true);
      const res = await examinationsService.getResults({
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        department: selectedDept !== "ALL" ? selectedDept : undefined,
      });
      setResults(res.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load results", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, [selectedStatus, selectedDept]);

  const handleFinalizeBatch = async () => {
    try {
      setFinalizing(true);
      await examinationsService.finalizeResults("exam-2026-ese");
      showToast({ title: "Finalized", message: "All semester candidate results finalized successfully.", type: "success" });
      setFinalizeModalOpen(false);
      loadResults();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to finalize results",
        type: "error",
      });
    } finally {
      setFinalizing(false);
    }
  };

  const passCount = results.filter((r) => r.status === "PASS").length;
  const failCount = results.filter((r) => r.status === "FAIL" || r.status === "ABSENT").length;
  const passRate = Math.round((passCount / (results.length || 1)) * 100);

  const columns: ColumnDef<Result>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Candidate",
        cell: (row) => (
          <div>
            <Link
              href={`/app/examinations/results/${row.id}`}
              className="font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
            >
              {row.studentName}
            </Link>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
              <span className="font-mono font-medium text-slate-600 dark:text-slate-300">
                {row.rollNumber}
              </span>
              <span>•</span>
              <span>{row.program}</span>
            </div>
          </div>
        ),
      },
      {
        id: "course",
        header: "Course & Subject",
        cell: (row) => (
          <div className="text-xs">
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              {row.courseCode}
            </span>
            <p className="text-slate-500">{row.courseName}</p>
            <span className="text-[11px] text-slate-400">{row.credits} Credits</span>
          </div>
        ),
      },
      {
        id: "score",
        header: "Percentage & Total",
        cell: (row) => (
          <div className="text-xs font-mono">
            <span className="font-bold text-slate-900 dark:text-white">
              {row.percentage}%
            </span>
            <div className="text-[11px] text-slate-400 font-normal">
              {row.totalMarks} / {row.maxMarks} pts
            </div>
          </div>
        ),
      },
      {
        id: "grade",
        header: "Grade & GP",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-bold text-xs ${
                row.grade === "A+" || row.grade === "A"
                  ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                  : row.grade === "B+" || row.grade === "B"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : row.grade === "C" || row.grade === "D"
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
              }`}
            >
              {row.grade}
            </span>
            <div className="text-xs">
              <p className="font-bold text-slate-800 dark:text-slate-200">{row.gradePoint}.0</p>
              <p className="text-[10px] text-slate-400">Grade Point</p>
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Result Status",
        cell: (row) => (
          <div>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                row.status === "PASS"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : row.status === "FAIL"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              {row.status}
            </span>
            {row.isPublished && (
              <span className="block text-[10px] text-blue-600 dark:text-blue-400 mt-0.5 font-medium">
                Published to Student
              </span>
            )}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <Link href={`/app/examinations/results/${row.id}`}>
            <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
              Breakdown
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              UGC CBCS Evaluation
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Semester 5 Grade Ledger</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Semester Examination Results
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Weighted assessment outcomes, 10-point grade conversions, and formal finalization gates prior to publication.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => setScaleModalOpen(true)}>
            <GraduationCap className="h-3.5 w-3.5" />
            View Grade Scale
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setFinalizeModalOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Lock className="h-3.5 w-3.5" />
            Finalize Cohort Results
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Evaluated Candidates"
          value={String(results.length)}
          description="Semester 5 courses"
          icon={<Award className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Cohort Pass Rate"
          value={`${passRate}%`}
          description={`${passCount} candidates passing`}
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Fails / Arrears"
          value={String(failCount)}
          description="Eligible for supplementary"
          icon={<Info className="h-5 w-5 text-rose-600" />}
        />
        <StatCard
          title="Published Results"
          value={String(results.filter((r) => r.isPublished).length)}
          description="Visible on student portal"
          icon={<Globe className="h-5 w-5 text-blue-600" />}
        />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Outcome:
        </div>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Outcomes</option>
          <option value="PASS">Passed (Grade A+ to D)</option>
          <option value="FAIL">Failed (Grade F)</option>
          <option value="ABSENT">Absent</option>
          <option value="WITHHELD">Withheld</option>
        </select>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Departments</option>
          <option value="Computer Science & Engineering">Computer Science & Engineering</option>
          <option value="Electronics & Communication">Electronics & Communication</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<Result>
        data={results}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search result by candidate name, roll number, or course code..."
        emptyTitle="No results found"
        emptyDescription="Finalize assessment marks to compile course results."
      />

      {/* Finalization Confirmation Modal */}
      <Dialog open={finalizeModalOpen} onClose={() => setFinalizeModalOpen(false)}>
        <div className="p-6 space-y-4 max-w-md">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Finalize Semester Results
              </h2>
              <p className="text-xs text-slate-500">Lock course outcomes for publication</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Finalizing results locks all grades across the semester cohort and compiles official GPA scores. Once finalized, results will be ready for release via the <strong>Publications Ledger</strong>.
          </p>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 text-xs space-y-1.5">
            <div className="flex justify-between">
              <span>Total Candidate Records:</span>
              <span className="font-bold">{results.length}</span>
            </div>
            <div className="flex justify-between text-emerald-600">
              <span>Passing:</span>
              <span>{passCount}</span>
            </div>
            <div className="flex justify-between text-rose-600">
              <span>Arrears / Fails:</span>
              <span>{failCount}</span>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" onClick={() => setFinalizeModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleFinalizeBatch} disabled={finalizing}>
              {finalizing ? "Finalizing..." : "Confirm Finalization"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Grade Scale Reference Modal */}
      <Dialog open={scaleModalOpen} onClose={() => setScaleModalOpen(false)}>
        <div className="p-6 space-y-4 max-w-lg">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-indigo-600" />
              {DEFAULT_GRADE_SCALE.name}
            </h2>
            <p className="text-xs text-slate-500">Academic Year {DEFAULT_GRADE_SCALE.academicYear}</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="p-2">Grade</th>
                  <th className="p-2">Range %</th>
                  <th className="p-2">Grade Point</th>
                  <th className="p-2">Classification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {DEFAULT_GRADE_SCALE.rules.map((rule) => (
                  <tr key={rule.grade}>
                    <td className="p-2 font-bold">{rule.grade}</td>
                    <td className="p-2 font-mono text-slate-500">{rule.minPercentage}% - {rule.maxPercentage}%</td>
                    <td className="p-2 font-bold text-indigo-600">{rule.gradePoint}.0</td>
                    <td className="p-2 text-slate-600 dark:text-slate-400">{rule.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" onClick={() => setScaleModalOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
