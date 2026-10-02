"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { examinationsService } from "@/services/examinations.service";
import { Assessment, Mark } from "@/types/examinations";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  Calendar,
  Lock,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Layers,
  Users,
  Award,
  History,
  FileSpreadsheet,
  AlertCircle,
} from "lucide-react";

export default function AssessmentDetailPage() {
  const params = useParams();
  const assessmentId = params?.id as string;
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [marks, setMarks] = useState<Mark[]>([]);
  const [finalizing, setFinalizing] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    async function loadData() {
      if (!assessmentId) return;
      try {
        setLoading(true);
        const [asmRes, marksRes] = await Promise.all([
          examinationsService.getAssessmentById(assessmentId),
          examinationsService.getMarks(assessmentId),
        ]);
        setAssessment(asmRes.data);
        setMarks(marksRes.data);
      } catch (err: unknown) {
        showToast({
          title: "Error",
          message: err instanceof Error ? err.message : "Failed to load assessment details",
          type: "error",
        });
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [assessmentId]);

  const handleFinalize = async () => {
    if (!assessment) return;
    try {
      setFinalizing(true);
      const res = await examinationsService.finalizeAssessment(assessment.id);
      setAssessment(res.data);
      showToast({ title: "Finalized", message: "Assessment scheme locked and finalized.", type: "success" });
    } catch (err: unknown) {
      showToast({
        title: "Finalization Blocked",
        message: err instanceof Error ? err.message : "All marks must be entered prior to finalization.",
        type: "error",
      });
    } finally {
      setFinalizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Loading assessment profile...
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-slate-500">Assessment not found</p>
        <Link href="/app/examinations/assessments">
          <Button variant="outline" size="sm" className="mt-4">
            Back to Assessments
          </Button>
        </Link>
      </div>
    );
  }

  const enteredMarks = marks.filter((m) => m.status !== "NOT_ENTERED");
  const completionRate = Math.round((enteredMarks.length / (marks.length || 1)) * 100);

  const tabs = [
    {
      id: "overview",
      label: "Overview & Structure",
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Course Context
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400">Course:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.courseCode} - {assessment.courseName}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Section:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    Section {assessment.section}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Faculty Instructor:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.facultyName}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Department:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.department}
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Evaluation Parameters
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400">Total Marks:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.maxMarks} marks
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Passing Score:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.passingMarks} marks
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Aggregate Weightage:</span>
                  <p className="font-semibold text-indigo-600 dark:text-indigo-400">
                    {assessment.weightage}% of term
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Assessment Type:</span>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {assessment.type}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Sub-Components Breakdown */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-600" />
              Sub-Components Breakdown ({assessment.components?.length || 0})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="p-2.5">#</th>
                    <th className="p-2.5">Component Name</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5 text-right">Max Marks</th>
                    <th className="p-2.5 text-right">Pass Marks</th>
                    <th className="p-2.5 text-right">Weightage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {assessment.components?.map((c, idx) => (
                    <tr key={c.id}>
                      <td className="p-2.5 font-mono text-slate-400">{idx + 1}</td>
                      <td className="p-2.5 font-medium text-slate-900 dark:text-white">{c.name}</td>
                      <td className="p-2.5 text-slate-500">{c.type}</td>
                      <td className="p-2.5 text-right font-semibold text-slate-800 dark:text-slate-200">{c.maxMarks}</td>
                      <td className="p-2.5 text-right text-slate-500">{c.passingMarks}</td>
                      <td className="p-2.5 text-right font-medium text-indigo-600 dark:text-indigo-400">{c.weightage}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "students",
      label: `Students & Marks (${marks.length})`,
      content: (
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Candidate Roster Marks
            </h3>
            <Link href={`/app/examinations/marks?course_offering_id=${assessment.courseOfferingId}&assessment_id=${assessment.id}`}>
              <Button size="sm" variant="primary" className="h-7 text-xs gap-1.5">
                <FileSpreadsheet className="h-3 w-3" />
                Open Entry Matrix
              </Button>
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="p-2.5">Roll No</th>
                  <th className="p-2.5">Student Name</th>
                  <th className="p-2.5 text-right">Score</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {marks.map((m) => (
                  <tr key={m.id}>
                    <td className="p-2.5 font-mono text-slate-600 dark:text-slate-300">{m.rollNumber}</td>
                    <td className="p-2.5 font-medium text-slate-900 dark:text-white">{m.studentName}</td>
                    <td className="p-2.5 text-right font-bold text-slate-800 dark:text-slate-100">
                      {m.marksObtained !== null ? `${m.marksObtained} / ${m.maxMarks}` : "—"}
                    </td>
                    <td className="p-2.5">
                      <span
                        className={`inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                          m.status === "ENTERED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : m.status === "ABSENT"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    <td className="p-2.5 text-slate-400">{m.remarks || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ),
    },
    {
      id: "timeline",
      label: "Lifecycle Timeline",
      content: (
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
            Assessment Lifecycle Audit Trail
          </h3>
          <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-700 pl-8">
            <div className="relative">
              <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-emerald-500 ring-4 ring-white dark:ring-slate-900" />
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                Assessment Scheme Created
              </p>
              <p className="text-[11px] text-slate-400">
                Created by {assessment.facultyName} • {new Date(assessment.createdAt).toLocaleString()}
              </p>
            </div>
            <div className="relative">
              <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-blue-500 ring-4 ring-white dark:ring-slate-900" />
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                Marks Entry Opened
              </p>
              <p className="text-[11px] text-slate-400">
                Class cohort roster loaded with {assessment.totalEnrolled} students
              </p>
            </div>
            {assessment.isFinalized ? (
              <div className="relative">
                <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-purple-500 ring-4 ring-white dark:ring-slate-900" />
                <p className="text-xs font-semibold text-slate-900 dark:text-white">
                  Assessment Finalized & Locked
                </p>
                <p className="text-[11px] text-slate-400">
                  Locked at {new Date(assessment.finalizedAt || "").toLocaleString()}
                </p>
              </div>
            ) : (
              <div className="relative">
                <span className="absolute -left-8 top-1 h-3 w-3 rounded-full bg-slate-300 ring-4 ring-white dark:ring-slate-900" />
                <p className="text-xs font-semibold text-slate-400">
                  Pending Finalization
                </p>
                <p className="text-[11px] text-slate-400">
                  Will lock marks ledger permanently once all grades are verified.
                </p>
              </div>
            )}
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <Link
            href="/app/examinations/assessments"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Assessment Schemes
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {assessment.name}
            </h1>
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
                assessment.isFinalized
                  ? "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                  : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
              }`}
            >
              {assessment.isFinalized && <Lock className="h-3 w-3" />}
              {assessment.status}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {assessment.courseCode} • {assessment.courseName} (Section {assessment.section})
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/examinations/marks?course_offering_id=${assessment.courseOfferingId}&assessment_id=${assessment.id}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <FileSpreadsheet className="h-3.5 w-3.5" />
              Enter Marks
            </Button>
          </Link>
          {!assessment.isFinalized && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleFinalize}
              disabled={finalizing}
              className="gap-1.5 text-xs"
            >
              <Lock className="h-3.5 w-3.5" />
              {finalizing ? "Locking..." : "Finalize Assessment"}
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Maximum Score"
          value={`${assessment.maxMarks} pts`}
          description={`Pass mark: ${assessment.passingMarks}`}
          icon={<Award className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Overall Weightage"
          value={`${assessment.weightage}%`}
          description="Of semester course grade"
          icon={<Layers className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Enrolled Cohort"
          value={`${marks.length} students`}
          description={`Section ${assessment.section}`}
          icon={<Users className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Marks Completion"
          value={`${completionRate}%`}
          description={`${enteredMarks.length} of ${marks.length} scored`}
          icon={<CheckCircle2 className="h-5 w-5 text-amber-600" />}
        />
      </div>

      {/* Tabs Layout */}
      <Tabs
        tabs={tabs.map((t) => ({ id: t.id, label: t.label }))}
        activeTab={activeTab}
        onChange={setActiveTab}
      />
      <div className="mt-4">
        {tabs.find((t) => t.id === activeTab)?.content}
      </div>
    </div>
  );
}
