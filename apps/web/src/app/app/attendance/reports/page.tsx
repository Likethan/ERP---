"use client";

import React, { useState } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceReportType, AttendanceReportFilter } from "@/types/attendance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  Download,
  Filter,
  ArrowLeft,
  Calendar,
  Layers,
  Building,
  CheckCircle2,
  AlertTriangle,
  Printer,
  Sparkles,
} from "lucide-react";

export default function AttendanceReportsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState<AttendanceReportType>("LOW_ATTENDANCE");
  const [department, setDepartment] = useState("ALL");
  const [semester, setSemester] = useState("ALL");
  const [section, setSection] = useState("ALL");
  const [startDate, setStartDate] = useState("2026-08-01");
  const [endDate, setEndDate] = useState("2026-10-02");

  const [generatedData, setGeneratedData] = useState<{
    title: string;
    generatedAt: string;
    totalRows: number;
    rows: Record<string, unknown>[];
  } | null>(null);

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.generateReport({
        reportType,
        department: department !== "ALL" ? department : undefined,
        semester: semester !== "ALL" ? Number(semester) : undefined,
        section: section !== "ALL" ? section : undefined,
        startDate,
        endDate,
      });

      if (res.success) {
        setGeneratedData(res.data);
        showToast({
          type: "success",
          title: "Report Generated",
          message: `Generated "${res.data.title}" with ${res.data.totalRows} records.`,
        });
      }
    } catch (err) {
      console.error("Failed to generate report", err);
      showToast({ type: "error", title: "Generation Error", message: "Failed to compile attendance report." });
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!generatedData || generatedData.rows.length === 0) return;
    const headers = Object.keys(generatedData.rows[0]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [
        headers.join(","),
        ...generatedData.rows.map((row) =>
          headers.map((h) => `"${String(row[h] || "").replace(/"/g, '""')}"`).join(",")
        ),
      ].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${generatedData.title.toLowerCase().replace(/\s+/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast({ type: "info", title: "Export Started", message: "CSV file downloaded successfully." });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/app/attendance">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                Institutional Audits
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Export & Compliance Engine</span>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Attendance Reports & Registers
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Compile statutory attendance rosters, low-attendance shortfalls, and hall-ticket debarment audit files.
            </p>
          </div>
        </div>
      </div>

      {/* Report Configuration Controls Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
          Report Parameters & Scope
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as AttendanceReportType)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="LOW_ATTENDANCE">Low Attendance & Shortage Report</option>
              <option value="STUDENT">Student Cohort Aggregate Roster</option>
              <option value="COURSE">Course Offering Attendance Summary</option>
              <option value="DEPARTMENT">Departmental Compliance Summary</option>
              <option value="FACULTY_SESSION">Faculty Session Delivery Register</option>
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
              <option value="ALL">All Departments</option>
              <option value="Computer Science">Computer Science & Engineering</option>
              <option value="Electronics">Electronics & Communication</option>
              <option value="Mechanical">Mechanical Engineering</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Semester
            </label>
            <select
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="ALL">All Semesters</option>
              <option value="1">Semester 1</option>
              <option value="3">Semester 3</option>
              <option value="5">Semester 5</option>
              <option value="7">Semester 7</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Section
            </label>
            <select
              value={section}
              onChange={(e) => setSection(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="ALL">All Sections</option>
              <option value="A">Section A</option>
              <option value="B">Section B</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Term Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Term End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div className="sm:col-span-2 flex items-end">
            <Button
              variant="primary"
              onClick={handleGenerateReport}
              disabled={loading}
              className="w-full gap-2 h-9 text-xs"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {loading ? "Compiling Report..." : "Compile & Preview Report"}
            </Button>
          </div>
        </div>
      </div>

      {/* Generated Report Preview */}
      {generatedData && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-3">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                {generatedData.title}
              </h3>
              <p className="text-xs text-slate-500">
                Compiled on {new Date(generatedData.generatedAt).toLocaleString()} • {generatedData.totalRows} Records
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={handleExportCSV} className="gap-1.5 text-xs">
                <Download className="h-3.5 w-3.5" />
                Export CSV
              </Button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 dark:bg-slate-800/50 dark:border-slate-800 dark:text-slate-400">
                  {Object.keys(generatedData.rows[0] || {}).map((header) => (
                    <th key={header} className="py-2.5 px-3 font-semibold">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {generatedData.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    {Object.values(row).map((val, cIdx) => (
                      <td key={cIdx} className="py-2.5 px-3 text-slate-800 dark:text-slate-200">
                        {String(val)}
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
