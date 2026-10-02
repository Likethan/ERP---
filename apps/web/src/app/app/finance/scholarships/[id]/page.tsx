"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Award,
  ArrowLeft,
  CheckCircle2,
  Calendar,
  Users,
  DollarSign,
  ShieldCheck,
  FileText,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast, ToastType } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Scholarship, StudentScholarship } from "@/types/finance";

export default function ScholarshipDetailPage() {
  const params = useParams();
  const scholarshipId = params?.id as string;
  const { hasPermission } = useAuth();
  const { showToast } = useToast();
  const notify = (title: string, type: ToastType = "info") => showToast({ title, type });

  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [recipients, setRecipients] = useState<StudentScholarship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  const canApprove = hasPermission("finance.manage_scholarships") || hasPermission("scholarships:approve");

  const loadData = async () => {
    if (!scholarshipId) return;
    try {
      setLoading(true);
      setError(null);
      const [schRes, recRes] = await Promise.all([
        financeService.getScholarshipById(scholarshipId),
        financeService.getStudentScholarships(),
      ]);
      setScholarship(schRes.data);
      const matched = recRes.data.filter(
        (r) => r.scholarshipId === scholarshipId || r.scholarshipName === schRes.data.name
      );
      setRecipients(matched);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Scholarship scheme not found.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [scholarshipId]);

  const handleApprove = async () => {
    if (!scholarship) return;
    try {
      setApproving(true);
      await financeService.approveScholarship(scholarship.id);
      notify("Scholarship scheme approved and activated!", "success");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve scholarship.";
      notify(msg, "error");
    } finally {
      setApproving(false);
    }
  };

  const totalDisbursed = useMemo(() => {
    return recipients.reduce((sum, r) => sum + r.discountAmount, 0);
  }, [recipients]);

  const avgDiscount = useMemo(() => {
    if (recipients.length === 0) return 0;
    return Math.round(totalDisbursed / recipients.length);
  }, [recipients, totalDisbursed]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-500">Loading scholarship scheme profile...</div>
      </div>
    );
  }

  if (error || !scholarship) {
    return (
      <div className="space-y-4">
        <Link href="/app/finance/scholarships">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Scholarships
          </Button>
        </Link>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          <h2 className="text-lg font-bold">Scheme Not Found</h2>
          <p className="mt-1 text-sm">{error || "Requested scheme does not exist."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <Link href="/app/finance/scholarships" className="hover:text-emerald-600 transition">
              Scholarships
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {scholarship.code}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {scholarship.name}
            </h1>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                scholarship.status === "APPROVED"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
              }`}
            >
              {scholarship.status}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {scholarship.description}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {scholarship.status === "PENDING_APPROVAL" && canApprove && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleApprove}
              disabled={approving}
              className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {approving ? "Approving..." : "Approve Scheme"}
            </Button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Total Disbursed"
          value={formatMoney(totalDisbursed)}
          description="Cumulative waiver given to students"
          icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
        />
        <StatCard
          title="Recipient Students"
          value={`${recipients.length} Beneficiaries`}
          description="Enrolled in current academic session"
          icon={<Users className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Average Concession"
          value={formatMoney(avgDiscount)}
          description="Mean waiver per awarded candidate"
          icon={<Award className="w-5 h-5 text-teal-600" />}
        />
      </div>

      {/* Scheme Rules & Metadata Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
          Scheme Regulatory Framework
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-500">Scheme Code:</span>
            <p className="font-mono font-bold text-slate-900 dark:text-white mt-0.5">
              {scholarship.code}
            </p>
          </div>
          <div>
            <span className="text-slate-500">Assistance Category:</span>
            <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
              {scholarship.type}
            </p>
          </div>
          <div>
            <span className="text-slate-500">Benefit Rate:</span>
            <p className="font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
              {scholarship.discountType === "PERCENTAGE"
                ? `${scholarship.value}% Tuition Discount`
                : formatMoney(scholarship.value)}
            </p>
          </div>
          <div>
            <span className="text-slate-500">Maximum Ceiling:</span>
            <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
              {scholarship.maxDiscountAmount ? formatMoney(scholarship.maxDiscountAmount) : "Uncapped"}
            </p>
          </div>
          <div className="col-span-2">
            <span className="text-slate-500">Academic Year:</span>
            <p className="font-medium text-slate-900 dark:text-white mt-0.5">
              {scholarship.academicYear}
            </p>
          </div>
          <div className="col-span-2">
            <span className="text-slate-500">Eligibility Regulations:</span>
            <p className="font-medium text-slate-900 dark:text-white mt-0.5">
              {scholarship.eligibilityCriteria || "Satisfies institutional academic criteria"}
            </p>
          </div>
        </div>
      </div>

      {/* Recipient Students Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Awardee Students Ledger
            </h2>
            <p className="text-xs text-slate-500">
              Students granted financial assistance under {scholarship.name}.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 uppercase font-semibold text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Roll Number</th>
                <th className="px-4 py-3 text-right">Original Fee</th>
                <th className="px-4 py-3 text-right">Grant Discount</th>
                <th className="px-4 py-3 text-right">Adjusted Net Fee</th>
                <th className="px-4 py-3">Granted Date</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {recipients.length > 0 ? (
                recipients.map((rec) => (
                  <tr key={rec.id}>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {rec.studentName}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500">{rec.rollNumber}</td>
                    <td className="px-4 py-3 text-right text-slate-500">
                      {formatMoney(rec.originalFee)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                      -{formatMoney(rec.discountAmount)}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                      {formatMoney(rec.adjustedFee)}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{rec.grantedDate}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                        {rec.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    No students currently assigned to this scholarship scheme.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
