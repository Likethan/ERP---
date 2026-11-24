"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { InstitutionalReportsData } from "@/types/vice-principal";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileSpreadsheet,
  Download,
  Calendar,
  Award,
  CheckCircle2,
  FileText,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalReportsPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<InstitutionalReportsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [academicYear, setAcademicYear] = useState("2026-2027");

  useEffect(() => {
    loadReports();
  }, [academicYear]);

  const loadReports = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getReports({
        academic_year: academicYear,
      });
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (reportName: string, format: string) => {
    showToast({
      title: "Export Initiated",
      message: `Generating authenticated institutional ${format} dossier for "${reportName}"...`,
      type: "success",
    });
  };

  if (loading && !data) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Reports & Regulatory Analytics
          </h1>
          <p className="text-sm text-slate-600">
            Export comprehensive multi-department academic audits, attendance
            condonation forecasts, and AICTE compliance dossiers.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 focus:outline-hidden"
          >
            <option value="2026-2027">AY 2026-2027 (Current)</option>
            <option value="2025-2026">AY 2025-2026</option>
          </select>
        </div>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Overall Institutional Compliance
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">
            {data?.summary_metrics.overall_institutional_compliance}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Academic & Attendance standard
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Accreditation Readiness (NAAC/NBA)
          </div>
          <div className="mt-1 text-2xl font-bold text-indigo-600">
            {data?.summary_metrics.accreditation_readiness_index} / 4.0
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Criterion 1, 2 & 3 audited
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Teaching Workload Equity
          </div>
          <div className="mt-1 text-2xl font-bold text-blue-600">
            {data?.summary_metrics.teaching_workload_adherence}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            AICTE contact hours compliance
          </div>
        </div>
      </div>

      {/* Available Executive Reports Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {data?.available_reports.map((rep) => (
          <Card
            key={rep.id}
            className="shadow-xs border-slate-200 hover:border-indigo-300 transition-colors"
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="rounded bg-indigo-50 border border-indigo-200 px-2 py-0.5 font-mono text-[10px] font-bold text-indigo-700 uppercase">
                    {rep.type.replace(/_/g, " ")}
                  </span>
                  <CardTitle className="text-base font-bold text-slate-900 mt-2">
                    {rep.name}
                  </CardTitle>
                </div>
              </div>
              <CardDescription className="text-xs text-slate-600 mt-1 leading-relaxed">
                {rep.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>Audited on {rep.generated_on}</span>
              <div className="flex items-center gap-2">
                {rep.format.map((fmt) => (
                  <Button
                    key={fmt}
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(rep.name, fmt)}
                    className="h-7 text-xs px-2.5 gap-1 font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    <Download className="h-3 w-3" />
                    <span>{fmt}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
