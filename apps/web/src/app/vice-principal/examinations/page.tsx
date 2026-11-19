"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { ExaminationsOversightData } from "@/types/vice-principal";
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
  ClipboardCheck,
  Calendar,
  Lock,
  FileText,
  Award,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  RefreshCw,
  Download,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalExaminationsPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<ExaminationsOversightData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExaminations();
  }, []);

  const loadExaminations = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getExaminationsOversight();
      if (res.success && res.data) {
        setData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLockMarks = (dept: string) => {
    showToast({
      title: "CIA Marks Sealed & Locked",
      message: `All CIA marks for ${dept} locked. Further mark corrections require statutory VP sanction.`,
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

  const results = data?.results_analysis;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Examination Oversight & Mark Moderation
          </h1>
          <p className="text-sm text-slate-600">
            Supervise Continuous Internal Assessments (CIA), question bank
            moderation, mark lockouts, and university result analytics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadExaminations}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Results Overview Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Institutional Pass Rate
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-600">
            {results?.overall_institutional_pass_pct}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Across 5 Engineering Programs
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Distinction & First Class
          </div>
          <div className="mt-1 text-2xl font-bold text-indigo-600">
            {(
              (results?.first_class_with_distinction_pct || 0) +
              (results?.first_class_pct || 0)
            ).toFixed(1)}
            %
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            {results?.first_class_with_distinction_pct}% Distinction
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Institutional Arrear Rate
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-900">
            {results?.arrear_rate_pct}%
          </div>
          <div className="mt-1 text-[11px] text-emerald-600 font-semibold">
            Under 8% NAAC benchmark
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="text-xs font-semibold text-slate-500">
            Question Banks Moderated
          </div>
          <div className="mt-1 text-2xl font-bold text-blue-600">40 / 42</div>
          <div className="mt-1 text-[11px] text-slate-500">
            Board of Scrutiny certified
          </div>
        </div>
      </div>

      {/* Master Examination Schedules */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="h-4 w-4 text-indigo-600" />
            Statutory Examination Schedules & Logistics
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Confidential timetable, seating allocations, and invigilation duty
            rosters
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Examination Name</th>
                  <th className="px-3 py-3">Date Range</th>
                  <th className="px-3 py-3">Category</th>
                  <th className="px-3 py-3">Logistics Status</th>
                  <th className="px-3 py-3">Seating Plan</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.schedules.map((sch) => (
                  <tr
                    key={sch.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {sch.name}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-mono">
                      {sch.date_range}
                    </td>
                    <td className="px-3 py-3">
                      <span className="rounded bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">
                        {sch.type}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {sch.question_papers_moderated
                        ? `${sch.question_papers_moderated} of ${sch.question_papers_total} QPs Moderated`
                        : sch.external_examiners_count
                          ? `${sch.external_examiners_count} External Examiners Confirmed`
                          : `${sch.total_halls} Examination Halls Allocated`}
                    </td>
                    <td className="px-3 py-3">
                      {sch.seating_plan_published ? (
                        <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Published
                        </span>
                      ) : (
                        <span className="text-slate-400">In Preparation</span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant="default" className="text-[10px]">
                        {sch.status.replace(/_/g, " ")}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* CIA Mark Submissions & Lock Status */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Lock className="h-4 w-4 text-slate-700" />
                Department CIA Mark Submissions & Statutory Lockouts
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Verification of continuous assessment marks prior to university
                portal synchronization
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-3 py-3">Total Courses</th>
                  <th className="px-3 py-3">Marks Submitted</th>
                  <th className="px-3 py-3">Locked & Sealed</th>
                  <th className="px-3 py-3">Pending</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Statutory Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.cia_mark_submissions.map((sub) => (
                  <tr
                    key={sub.department}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {sub.department}
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium">
                      {sub.total_courses}
                    </td>
                    <td className="px-3 py-3 text-emerald-600 font-bold">
                      {sub.submitted}
                    </td>
                    <td className="px-3 py-3 text-slate-900 font-semibold">
                      {sub.locked}
                    </td>
                    <td className="px-3 py-3">
                      {sub.pending > 0 ? (
                        <span className="font-bold text-rose-600">
                          {sub.pending} Overdue
                        </span>
                      ) : (
                        <span className="text-emerald-600 font-semibold">
                          0
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <Badge
                        variant={
                          sub.status === "COMPLETED"
                            ? "success"
                            : sub.status === "LOCK_PENDING"
                              ? "warning"
                              : "destructive"
                        }
                        className="text-[10px]"
                      >
                        {sub.status.replace(/_/g, " ")}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {sub.pending === 0 && sub.locked === sub.total_courses ? (
                        <span className="text-[11px] text-slate-400 font-medium flex items-center justify-end gap-1">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          Sealed
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleLockMarks(sub.department)}
                          className="text-xs text-indigo-600 hover:text-indigo-800 gap-1"
                        >
                          <Lock className="h-3 w-3" />
                          Lock & Seal
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
