"use client";

import React, { useEffect, useState } from "react";
import {
  FileSpreadsheet,
  Download,
  Printer,
  Calendar,
  Filter,
  Users,
  GraduationCap,
  CalendarCheck,
  BookOpen,
  Briefcase,
  PartyPopper,
  CheckCircle2,
  FileText,
  Clock,
  Sparkles,
} from "lucide-react";
import {
  hodService,
  HodReportCategoryItem,
  HodReportGeneratePayload,
  HodReportResult,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodReportsPage() {
  const { addToast } = useToast();
  const [categories, setCategories] = useState<HodReportCategoryItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("STUDENT");
  const [selectedReportCode, setSelectedReportCode] =
    useState("STUDENT_STRENGTH");
  const [academicYear, setAcademicYear] = useState("2025-2026");
  const [semester, setSemester] = useState("ODD");
  const [section, setSection] = useState("ALL");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [generating, setGenerating] = useState(false);
  const [reportResult, setReportResult] = useState<HodReportResult | null>(
    null,
  );

  useEffect(() => {
    async function loadCategories() {
      try {
        const res = await hodService.getReportCategories();
        if (res.data?.categories) {
          setCategories(res.data.categories);
        }
      } catch {
        addToast({
          title: "Error Loading Report Categories",
          description: "Could not fetch department report definitions.",
          variant: "destructive",
        });
      }
    }
    loadCategories();
  }, []);

  // Update selected report code when category changes
  useEffect(() => {
    const cat = categories.find((c) => c.category === selectedCategory);
    if (cat && cat.types.length > 0) {
      setSelectedReportCode(cat.types[0].code);
    }
  }, [selectedCategory, categories]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      const activeCat = categories.find((c) => c.category === selectedCategory);
      const activeType = activeCat?.types.find(
        (t) => t.code === selectedReportCode,
      );

      const payload: HodReportGeneratePayload = {
        category: selectedCategory,
        reportType: activeType ? activeType.name : selectedReportCode,
        academicYear,
        semester,
        section,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      };

      const res = await hodService.generateDepartmentReport(payload);
      if (res.data) {
        setReportResult(res.data);
        addToast({
          title: "Report Generated",
          description: `"${res.data.title}" compiled with ${res.data.totalRecords} records.`,
          variant: "success",
        });
      }
    } catch {
      addToast({
        title: "Generation Failed",
        description: "Could not compile statutory report.",
        variant: "destructive",
      });
    } finally {
      setGenerating(false);
    }
  };

  const exportCsv = () => {
    if (!reportResult) return;
    const headerRow = reportResult.columns.map((c) => `"${c.label}"`).join(",");
    const rows = reportResult.rows.map((row) =>
      reportResult.columns
        .map((col) => `"${row[col.key] !== undefined ? row[col.key] : ""}"`)
        .join(","),
    );
    const csvContent =
      "data:text/csv;charset=utf-8," + [headerRow, ...rows].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `${selectedReportCode}_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const printReport = () => {
    window.print();
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "STUDENT":
        return <GraduationCap className="h-4 w-4" />;
      case "FACULTY":
        return <Users className="h-4 w-4" />;
      case "ATTENDANCE":
        return <CalendarCheck className="h-4 w-4" />;
      case "ACADEMIC":
        return <BookOpen className="h-4 w-4" />;
      case "TIMETABLE":
        return <Calendar className="h-4 w-4" />;
      case "PLACEMENT":
        return <Briefcase className="h-4 w-4" />;
      case "EVENTS":
        return <PartyPopper className="h-4 w-4" />;
      default:
        return <FileSpreadsheet className="h-4 w-4" />;
    }
  };

  const activeCategoryObj = categories.find(
    (c) => c.category === selectedCategory,
  );

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Department Reports & Exports
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              Statutory Reporting Engine
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Generate, preview, and export accredited institutional reports
            across students, faculty, academics, and placements.
          </p>
        </div>

        {reportResult && (
          <div className="flex items-center gap-2">
            <button
              onClick={printReport}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50"
            >
              <Printer className="h-4 w-4" />
              Print / Save PDF
            </button>
            <button
              onClick={exportCsv}
              className="inline-flex items-center gap-1.5 rounded-lg bg-yellow-400 px-3.5 py-2 text-xs font-semibold text-slate-950 shadow-xs hover:bg-yellow-300"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        )}
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {categories.map((cat) => {
          const isActive = selectedCategory === cat.category;
          return (
            <button
              key={cat.category}
              onClick={() => setSelectedCategory(cat.category)}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all ${
                isActive
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              {getCategoryIcon(cat.category)}
              {cat.title}
            </button>
          );
        })}
      </div>

      {/* Generator Form Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <form onSubmit={handleGenerate} className="space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                {activeCategoryObj?.title || "Report Generator"}
              </h2>
              <p className="text-xs text-slate-500">
                {activeCategoryObj?.description}
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Department: Computer Science & Engineering
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            {/* Report Type */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Report Type *
              </label>
              <select
                value={selectedReportCode}
                onChange={(e) => setSelectedReportCode(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-800 focus:border-yellow-400 focus:outline-hidden"
              >
                {activeCategoryObj?.types.map((type) => (
                  <option key={type.code} value={type.code}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Academic Year */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Academic Year *
              </label>
              <select
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-800 focus:outline-hidden"
              >
                <option value="2025-2026">2025 - 2026 (Current)</option>
                <option value="2024-2025">2024 - 2025</option>
                <option value="2023-2024">2023 - 2024</option>
              </select>
            </div>

            {/* Semester */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Semester Filter
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-800 focus:outline-hidden"
              >
                <option value="ODD">Odd Semesters (1, 3, 5, 7)</option>
                <option value="EVEN">Even Semesters (2, 4, 6, 8)</option>
                <option value="FULL_YEAR">Full Academic Year</option>
              </select>
            </div>

            {/* Section */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Section
              </label>
              <select
                value={section}
                onChange={(e) => setSection(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-800 focus:outline-hidden"
              >
                <option value="ALL">All Sections (A, B, C)</option>
                <option value="A">Section A</option>
                <option value="B">Section B</option>
                <option value="C">Section C</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={generating}
              className="inline-flex items-center gap-2 rounded-lg bg-yellow-400 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-xs hover:bg-yellow-300 disabled:opacity-50 transition-colors"
            >
              <Sparkles className="h-4 w-4" />
              {generating ? "Compiling Report..." : "Generate Live Report"}
            </button>
          </div>
        </form>
      </div>

      {/* Live Preview Section */}
      {reportResult ? (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
          {/* Metadata Banner */}
          <div className="border-b border-slate-200 bg-slate-50/60 p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
                  Report ID: {reportResult.reportId}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-0.5">
                  {reportResult.title}
                </h3>
              </div>
              <div className="text-left sm:text-right text-xs text-slate-500">
                <div>
                  Generated by:{" "}
                  <strong className="text-slate-800">
                    {reportResult.generatedBy}
                  </strong>
                </div>
                <div className="text-[11px] font-mono">
                  Timestamp: {reportResult.generatedAt}
                </div>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-600">
              <span className="rounded bg-slate-200/70 px-2 py-0.5">
                Year: {reportResult.academicYear}
              </span>
              <span className="rounded bg-slate-200/70 px-2 py-0.5">
                Semester: {reportResult.filtersApplied.semester}
              </span>
              <span className="rounded bg-slate-200/70 px-2 py-0.5">
                Section: {reportResult.filtersApplied.section}
              </span>
              <span className="rounded bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5">
                Total Rows: {reportResult.totalRecords}
              </span>
            </div>
          </div>

          {/* Tabular Output */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                <tr>
                  {reportResult.columns.map((col) => (
                    <th key={col.key} className="px-5 py-3">
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reportResult.rows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    className="hover:bg-yellow-50/30 transition-colors"
                  >
                    {reportResult.columns.map((col) => (
                      <td
                        key={col.key}
                        className="px-5 py-3.5 font-medium text-slate-800"
                      >
                        {row[col.key] !== undefined
                          ? String(row[col.key])
                          : "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-12 text-center">
          <FileSpreadsheet className="mx-auto h-8 w-8 text-slate-400" />
          <h3 className="mt-2 text-sm font-semibold text-slate-800">
            No report currently compiled
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Choose your report category and filters above, then click "Generate
            Live Report" to preview and export.
          </p>
        </div>
      )}
    </div>
  );
}
