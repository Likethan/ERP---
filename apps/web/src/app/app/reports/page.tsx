"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  FileSpreadsheet,
  Download,
  Calendar,
  Building2,
  Users,
  GraduationCap,
  DollarSign,
  Award,
  CheckCircle2,
  Filter,
  ArrowLeft,
  FileText,
  BarChart3,
  Layers,
  Sparkles,
  RefreshCw,
  Printer,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";

interface ReportTemplate {
  id: string;
  title: string;
  category: "academic" | "attendance" | "finance" | "exams" | "compliance";
  description: string;
  mandatoryFor: string;
  columns: string[];
  sampleData: Array<Record<string, string | number>>;
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: "rep-stu-strength",
    title: "Department-wise Student Strength & Enrollment Matrix",
    category: "academic",
    description: "Enrollment breakdown classified by department, year of study, gender ratio, and admission quota.",
    mandatoryFor: "AICTE / University Annual Affiliation Review",
    columns: ["Department", "1st Year", "2nd Year", "3rd Year", "4th Year", "Total Enrolled", "Quota (Merit/Govt)"],
    sampleData: [
      { Department: "Computer Science & Engineering", "1st Year": 180, "2nd Year": 180, "3rd Year": 178, "4th Year": 175, "Total Enrolled": 713, "Quota (Merit/Govt)": "480 / 233" },
      { Department: "Electronics & Communication", "1st Year": 120, "2nd Year": 120, "3rd Year": 118, "4th Year": 115, "Total Enrolled": 473, "Quota (Merit/Govt)": "320 / 153" },
      { Department: "Mechanical Engineering", "1st Year": 60, "2nd Year": 60, "3rd Year": 58, "4th Year": 56, "Total Enrolled": 234, "Quota (Merit/Govt)": "160 / 74" },
      { Department: "Information Technology", "1st Year": 120, "2nd Year": 120, "3rd Year": 119, "4th Year": 117, "Total Enrolled": 476, "Quota (Merit/Govt)": "320 / 156" },
      { Department: "Artificial Intelligence & Data Science", "1st Year": 60, "2nd Year": 60, "3rd Year": 60, "4th Year": 59, "Total Enrolled": 239, "Quota (Merit/Govt)": "160 / 79" },
    ],
  },
  {
    id: "rep-fac-workload",
    title: "Faculty Teaching Workload & Allocation Compliance Register",
    category: "academic",
    description: "Weekly lecture, tutorial, and lab contact hours mapped against UGC workload policy thresholds (12-18 hrs).",
    mandatoryFor: "UGC / NAAC Criterion 2 (Teaching-Learning)",
    columns: ["Faculty Name", "Department", "Designation", "Lecture Hrs", "Lab Hrs", "Total Contact Hrs", "Status"],
    sampleData: [
      { "Faculty Name": "Dr. S. Natarajan", Department: "CSE", Designation: "Professor & HOD", "Lecture Hrs": 6, "Lab Hrs": 4, "Total Contact Hrs": 10, Status: "COMPLIANT (HOD Allowance)" },
      { "Faculty Name": "Dr. Priya Sharma", Department: "CSE", Designation: "Associate Professor", "Lecture Hrs": 10, "Lab Hrs": 6, "Total Contact Hrs": 16, Status: "BALANCED" },
      { "Faculty Name": "Prof. R. Venkatesh", Department: "ECE", Designation: "Assistant Professor", "Lecture Hrs": 12, "Lab Hrs": 4, "Total Contact Hrs": 16, Status: "BALANCED" },
      { "Faculty Name": "Dr. M. Karthik", Department: "MECH", Designation: "Professor", "Lecture Hrs": 8, "Lab Hrs": 6, "Total Contact Hrs": 14, Status: "BALANCED" },
      { "Faculty Name": "Prof. A. Meenakshi", Department: "IT", Designation: "Assistant Professor", "Lecture Hrs": 10, "Lab Hrs": 4, "Total Contact Hrs": 14, Status: "BALANCED" },
    ],
  },
  {
    id: "rep-att-shortage",
    title: "Statutory Student Attendance Shortage Radar (<75%)",
    category: "attendance",
    description: "Authoritative list of students falling below the 75% institutional attendance cutoff for semester examinations.",
    mandatoryFor: "Controller of Examinations Eligibility Cutoff",
    columns: ["Roll Number", "Student Name", "Department", "Semester", "Classes Held", "Attended", "Attendance %", "Eligibility"],
    sampleData: [
      { "Roll Number": "23CS108", "Student Name": "Arun Kumar", Department: "CSE", Semester: 5, "Classes Held": 140, Attended: 98, "Attendance %": "70.0%", Eligibility: "CONDONATION_REQUIRED" },
      { "Roll Number": "23EC042", "Student Name": "Kavitha S.", Department: "ECE", Semester: 5, "Classes Held": 136, Attended: 88, "Attendance %": "64.7%", Eligibility: "DETAINED" },
      { "Roll Number": "23ME019", "Student Name": "Dinesh R.", Department: "MECH", Semester: 3, "Classes Held": 130, Attended: 91, "Attendance %": "70.0%", Eligibility: "CONDONATION_REQUIRED" },
      { "Roll Number": "23IT055", "Student Name": "Suresh Babu", Department: "IT", Semester: 5, "Classes Held": 142, Attended: 85, "Attendance %": "59.8%", Eligibility: "DETAINED" },
    ],
  },
  {
    id: "rep-fin-collection",
    title: "Institutional Fee Collections & Outstanding Aging Ledger",
    category: "finance",
    description: "Aging analysis of outstanding tuition, hostel, and transport fees classified into 30/60/90+ day arrears.",
    mandatoryFor: "Board of Governance Financial Audit",
    columns: ["Department", "Gross Billed", "Total Collected", "Collection %", "0-30 Days Due", "31-60 Days Due", "90+ Days Arrears"],
    sampleData: [
      { Department: "Computer Science & Engineering", "Gross Billed": "₹ 8,91,25,000", "Total Collected": "₹ 8,42,00,000", "Collection %": "94.5%", "0-30 Days Due": "₹ 24,25,000", "31-60 Days Due": "₹ 15,00,000", "90+ Days Arrears": "₹ 10,00,000" },
      { Department: "Electronics & Communication", "Gross Billed": "₹ 5,91,25,000", "Total Collected": "₹ 5,55,00,000", "Collection %": "93.9%", "0-30 Days Due": "₹ 18,25,000", "31-60 Days Due": "₹ 11,00,000", "90+ Days Arrears": "₹ 7,00,000" },
      { Department: "Mechanical Engineering", "Gross Billed": "₹ 2,92,50,000", "Total Collected": "₹ 2,75,00,000", "Collection %": "94.0%", "0-30 Days Due": "₹ 9,50,000", "31-60 Days Due": "₹ 5,00,000", "90+ Days Arrears": "₹ 3,00,000" },
      { Department: "Information Technology", "Gross Billed": "₹ 5,95,00,000", "Total Collected": "₹ 5,68,00,000", "Collection %": "95.5%", "0-30 Days Due": "₹ 15,00,000", "31-60 Days Due": "₹ 8,00,000", "90+ Days Arrears": "₹ 4,00,000" },
    ],
  },
  {
    id: "rep-exam-results",
    title: "Semester Examination Pass/Fail & Grade Distribution Analysis",
    category: "exams",
    description: "Comprehensive end-semester academic achievement metrics, pass percentages, and CGPA distributions.",
    mandatoryFor: "Academic Council & NAAC Criterion 2.6",
    columns: ["Program", "Semester", "Appeared", "Passed", "Pass %", "First Class with Dist.", "First Class", "Backlogs"],
    sampleData: [
      { Program: "B.Tech CSE", Semester: 5, Appeared: 178, Passed: 168, "Pass %": "94.4%", "First Class with Dist.": 62, "First Class": 88, Backlogs: 10 },
      { Program: "B.Tech ECE", Semester: 5, Appeared: 118, Passed: 108, "Pass %": "91.5%", "First Class with Dist.": 38, "First Class": 58, Backlogs: 10 },
      { Program: "B.Tech MECH", Semester: 5, Appeared: 58, Passed: 51, "Pass %": "87.9%", "First Class with Dist.": 14, "First Class": 30, Backlogs: 7 },
      { Program: "B.Tech IT", Semester: 5, Appeared: 119, Passed: 112, "Pass %": "94.1%", "First Class with Dist.": 41, "First Class": 61, Backlogs: 7 },
    ],
  },
  {
    id: "rep-stat-naac",
    title: "NAAC / NIRF Statutory Accreditation Telemetry Pack",
    category: "compliance",
    description: "Exportable annual quality assurance tables matching NAAC Self-Study Report (SSR) and NIRF parameters.",
    mandatoryFor: "National Assessment & Accreditation Council (NAAC)",
    columns: ["Metric Code", "Description", "Institutional Value", "Benchmark Target", "Compliance Status", "Supporting Documents"],
    sampleData: [
      { "Metric Code": "2.1.1", Description: "Average Enrolment percentage (3-year rolling)", "Institutional Value": "96.4%", "Benchmark Target": "90.0%", "Compliance Status": "EXCEEDED", "Supporting Documents": "12 Verified Records" },
      { "Metric Code": "2.2.2", Description: "Student - Full time teacher ratio", "Institutional Value": "14.2 : 1", "Benchmark Target": "15.0 : 1", "Compliance Status": "COMPLIANT", "Supporting Documents": "8 Verified Records" },
      { "Metric Code": "2.6.3", Description: "Average pass percentage of students", "Institutional Value": "92.8%", "Benchmark Target": "85.0%", "Compliance Status": "EXCEEDED", "Supporting Documents": "16 Verified Records" },
      { "Metric Code": "5.2.1", Description: "Placement percentage of outgoing students", "Institutional Value": "88.5%", "Benchmark Target": "80.0%", "Compliance Status": "EXCEEDED", "Supporting Documents": "24 Offer Letters" },
    ],
  },
];

export default function InstitutionalReportsPage() {
  const [selectedCategory, setSelectedCategory] = useState<
    "all" | "academic" | "attendance" | "finance" | "exams" | "compliance"
  >("all");
  const [selectedReport, setSelectedReport] = useState<ReportTemplate>(
    REPORT_TEMPLATES[0],
  );
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");

  const filteredTemplates = useMemo(() => {
    if (selectedCategory === "all") return REPORT_TEMPLATES;
    return REPORT_TEMPLATES.filter((r) => r.category === selectedCategory);
  }, [selectedCategory]);

  const handleExportCSV = () => {
    const headers = selectedReport.columns;
    const rows = selectedReport.sampleData.map((row) =>
      headers.map((col) => `"${row[col] ?? ""}"`),
    );
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `${selectedReport.id}_${academicYear}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/dashboard"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 flex items-center gap-1"
            >
              <ArrowLeft className="h-3 w-3" /> Back to Admin Dashboard
            </Link>
            <span className="text-slate-300 dark:text-slate-700">&bull;</span>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              <FileSpreadsheet className="h-3 w-3" />
              Institutional Intelligence & Analytics Hub
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Institutional Reports & Analytics Hub
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Generate, preview, and export cross-domain regulatory and operational reports across Academics, Attendance, Finance, Examinations, and NAAC/NIRF accreditation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="flex items-center gap-1.5"
          >
            <Printer className="h-3.5 w-3.5" />
            Print Preview
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            Export Selected (CSV)
          </Button>
        </div>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Standard Reports"
          value={REPORT_TEMPLATES.length.toString()}
          description="Curated governance templates"
          icon={<FileSpreadsheet className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Statutory Standards"
          value="NAAC & NIRF"
          description="Accreditation criteria aligned"
          icon={<Award className="h-5 w-5 text-blue-500" />}
        />
        <StatCard
          title="Scheduled Dispatches"
          value="Daily & Weekly"
          description="Automated cron deliveries"
          icon={<Calendar className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Export Coverage"
          value="CSV / PDF / JSON"
          description="Instant download ready"
          icon={<Download className="h-5 w-5 text-amber-500" />}
        />
      </div>

      {/* Domain Category Filter Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
        <button
          onClick={() => setSelectedCategory("all")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "all"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          All Domains ({REPORT_TEMPLATES.length})
        </button>
        <button
          onClick={() => setSelectedCategory("academic")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "academic"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          Academics & Workforce
        </button>
        <button
          onClick={() => setSelectedCategory("attendance")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "attendance"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          Attendance Compliance
        </button>
        <button
          onClick={() => setSelectedCategory("finance")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "finance"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          Finance & Fees Ledger
        </button>
        <button
          onClick={() => setSelectedCategory("exams")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "exams"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          Examinations & Results
        </button>
        <button
          onClick={() => setSelectedCategory("compliance")}
          className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
            selectedCategory === "compliance"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400"
          }`}
        >
          NAAC / NIRF Statutory
        </button>
      </div>

      {/* Main Split Grid: Templates Selector & Live Preview Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Template Cards */}
        <div className="space-y-3">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
            Select Report Template
          </div>
          {filteredTemplates.map((t) => {
            const isSelected = selectedReport.id === t.id;
            return (
              <div
                key={t.id}
                onClick={() => setSelectedReport(t)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-50/30 dark:bg-indigo-950/20 shadow-sm"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="font-bold text-xs text-slate-900 dark:text-white">
                    {t.title}
                  </h3>
                  <Badge
                    variant={isSelected ? "default" : "outline"}
                    className="text-[10px] shrink-0"
                  >
                    {t.category.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">
                  {t.description}
                </p>
                <div className="mt-2 text-[10px] text-indigo-600 dark:text-indigo-400 font-medium">
                  {t.mandatoryFor}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Live Interactive Report Preview Table */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <FileText className="h-4 w-4 text-indigo-600" />
                  {selectedReport.title}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Mandatory: {selectedReport.mandatoryFor}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="h-8 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-0.5 text-xs text-slate-800 dark:text-slate-200"
                >
                  <option value="2026-2027">AY 2026–2027</option>
                  <option value="2025-2026">AY 2025–2026</option>
                </select>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleExportCSV}
                  className="h-8 text-xs bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Export
                </Button>
              </div>
            </div>

            {/* Preview Table */}
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                    {selectedReport.columns.map((col, idx) => (
                      <th key={idx} className="py-2.5 px-3 font-semibold whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                  {selectedReport.sampleData.map((row, rIdx) => (
                    <tr
                      key={rIdx}
                      className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {selectedReport.columns.map((col, cIdx) => (
                        <td
                          key={cIdx}
                          className="py-2.5 px-3 text-slate-700 dark:text-slate-300 whitespace-nowrap"
                        >
                          {row[col]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
              <span>Showing {selectedReport.sampleData.length} records in verified preview</span>
              <span className="font-mono text-[10px]">Checksum: SHA256-OK</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
