"use client";

import React, { useState } from "react";
import { examinationsService } from "@/services/examinations.service";
import { ExamReportFilter } from "@/types/examinations";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  Download,
  Filter,
  Sparkles,
  Calendar,
  Layers,
  CheckCircle2,
  Table as TableIcon,
} from "lucide-react";

export default function ExaminationReportsPage() {
  const { showToast } = useToast();

  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState<ExamReportFilter["reportType"]>("COMPLETION");
  const [department, setDepartment] = useState("Computer Science & Engineering");
  const [semester, setSemester] = useState(5);
  const [startDate, setStartDate] = useState("2026-08-01");
  const [endDate, setEndDate] = useState("2026-10-31");

  const [reportResult, setReportResult] = useState<{
    title: string;
    generatedAt: string;
    totalRecords: number;
    rows: Record<string, string | number>[];
  } | null>(null);

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      const res = await examinationsService.generateReport({
        reportType,
        department,
        semester,
        startDate,
        endDate,
      });
      setReportResult(res.data);
      showToast({ title: "Report Compiled", message: `Generated ${res.data.totalRecords} records.`, type: "success" });
    } catch {
      showToast({ title: "Compilation Error", message: "Failed to compile report", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!reportResult || reportResult.rows.length === 0) return;

    const headers = Object.keys(reportResult.rows[0]);
    const csvContent = [
      headers.join(","),
      ...reportResult.rows.map((row) =>
        headers.map((h) => `"${String(row[h] ?? "").replace(/"/g, '""')}"`).join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `campusos-exam-report-${reportType.toLowerCase()}-${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast({ title: "Exported", message: "CSV file downloaded successfully.", type: "success" });
  };

  const columns = reportResult?.rows.length ? Object.keys(reportResult.rows[0]) : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300">
              Audit & Compliance
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Institutional Reporting Engine</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Examination & Assessment Reports
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Compile marks registers, timetable schedules, attendance eligibility gates, and semester grade distributions with export.
          </p>
        </div>

        {reportResult && reportResult.rows.length > 0 && (
          <Button variant="primary" onClick={handleExportCSV} className="gap-2">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        )}
      </div>

      {/* Report Parameter Configuration Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Filter className="h-4 w-4 text-indigo-600" />
          Report Compilation Parameters
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Select Report Type *
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as ExamReportFilter["reportType"])}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="COMPLETION">Assessment Completion & Lock Audit</option>
              <option value="MARKS_ROSTER">Class Marks Roster Ledger</option>
              <option value="SCHEDULE">Master Exam Timetable Schedule</option>
              <option value="ELIGIBILITY">Student Attendance Eligibility Audit</option>
              <option value="RESULTS">Semester Cohort Results & GPA</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Department
            </label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="Computer Science & Engineering">Computer Science & Engineering</option>
              <option value="Electronics & Communication">Electronics & Communication</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Semester Term
            </label>
            <select
              value={semester}
              onChange={(e) => setSemester(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value={5}>Semester 5 (Current Odd Term)</option>
              <option value={4}>Semester 4 (Previous Even Term)</option>
            </select>
          </div>

          <div className="flex items-end">
            <Button
              variant="primary"
              onClick={handleGenerateReport}
              disabled={loading}
              className="w-full gap-2 h-9 text-xs"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {loading ? "Compiling..." : "Compile & Preview"}
            </Button>
          </div>
        </div>
      </div>

      {/* Preview Table */}
      {reportResult && (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 overflow-hidden shadow-xs space-y-3 p-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3 dark:border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {reportResult.title}
              </h3>
              <p className="text-xs text-slate-500">
                Compiled at {reportResult.generatedAt} • {reportResult.totalRecords} records
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={handleExportCSV} className="text-xs gap-1.5 self-start">
              <Download className="h-3.5 w-3.5" />
              Download CSV
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  {columns.map((col) => (
                    <th key={col} className="p-2.5 font-semibold capitalize whitespace-nowrap">
                      {col.replace(/([A-Z])/g, " $1")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {reportResult.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    {columns.map((col) => (
                      <td key={col} className="p-2.5 whitespace-nowrap font-mono text-slate-700 dark:text-slate-300">
                        {String(row[col] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
