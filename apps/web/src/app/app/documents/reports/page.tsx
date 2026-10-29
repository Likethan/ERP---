"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentReportsService } from "@/services/document-reports.service";
import { documentsService } from "@/services/documents.service";
import { DocumentsDashboardSummary, DocumentItem } from "@campusos/types";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  TrendingUp,
  Download,
  ShieldCheck,
  Clock,
  Calendar,
  AlertTriangle,
  Award,
  Layers,
  ArrowLeft,
  Building,
} from "lucide-react";

export default function DocumentReportsPage() {
  const [summary, setSummary] = useState<DocumentsDashboardSummary | null>(
    null,
  );
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        const [sumRes, docsRes] = await Promise.all([
          documentReportsService.getDashboardSummary(),
          documentsService.listDocuments(),
        ]);

        if (sumRes.success && sumRes.data) setSummary(sumRes.data);
        if (docsRes.success && docsRes.data) setDocuments(docsRes.data);
      } catch (err) {
        console.error("Failed to load reports:", err);
      } finally {
        setLoading(false);
      }
    }

    loadReports();
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <Link
              href="/app/documents"
              className="hover:underline flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Documents Center
            </Link>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Document Analytics & Compliance Reports
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Institutional verification SLAs, category completion rates, expiry
            radar audits, and certificate issuance trends.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            variant="outline"
            className="text-xs gap-1.5"
            onClick={() => alert("Downloading CSV Compliance Audit Report...")}
          >
            <Download className="w-4 h-4" />
            Export CSV Audit
          </Button>
          <Button
            size="sm"
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
            onClick={() =>
              alert("Generating Executive PDF Compliance Summary...")
            }
          >
            <Download className="w-4 h-4" />
            Executive PDF
          </Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Overall Verification Rate"
          value={loading ? "--" : `${summary?.verificationRate || 0}%`}
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
          subtitle="Processed submissions"
        />
        <StatCard
          title="Rejection Rate"
          value={loading ? "--" : `${summary?.rejectionRate || 0}%`}
          icon={<AlertTriangle className="w-5 h-5 text-rose-400" />}
          subtitle="Discrepancy / blur"
        />
        <StatCard
          title="Average Turnaround SLA"
          value={
            loading ? "--" : `${summary?.averageVerificationHours || 0} Hours`
          }
          icon={<Clock className="w-5 h-5 text-blue-400" />}
          subtitle="Target threshold: 24h"
        />
        <StatCard
          title="Certificates Issued"
          value={
            loading ? "--" : String(summary?.certificatesIssuedThisMonth || 0)
          }
          icon={<Award className="w-5 h-5 text-amber-400" />}
          subtitle="Current academic session"
        />
      </div>

      {/* Grid 1: Expiry Audit & Category Completion */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expiry Radar Audit */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-orange-400" />
                Document Expiry Radar Audit
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Breakdown of active credentials and validity horizon.
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-rose-400 font-medium">
                Expired Documents (Immediate Action)
              </span>
              <span className="font-mono font-bold text-rose-400 text-sm">
                {summary?.expiryBreakdown.expired || 0}
              </span>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-red-400 font-medium">
                Expiring within 7 Days
              </span>
              <span className="font-mono font-bold text-red-400 text-sm">
                {summary?.expiryBreakdown.expiring7Days || 0}
              </span>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-amber-400 font-medium">
                Expiring within 30 Days
              </span>
              <span className="font-mono font-bold text-amber-400 text-sm">
                {summary?.expiryBreakdown.expiring30Days || 0}
              </span>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-blue-400 font-medium">
                Expiring within 90 Days
              </span>
              <span className="font-mono font-bold text-blue-400 text-sm">
                {summary?.expiryBreakdown.expiring90Days || 0}
              </span>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-slate-300 font-medium">
                Permanent / Non-Expiring Records
              </span>
              <span className="font-mono font-bold text-slate-200 text-sm">
                {(summary?.expiryBreakdown.valid || 0) +
                  (summary?.expiryBreakdown.noExpiry || 0)}
              </span>
            </div>
          </div>
        </div>

        {/* Category Distribution Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              Taxonomy Category Breakdown
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Distribution of documents across institutional categories.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            {summary?.categoryDistribution.map((cat) => (
              <div key={cat.category} className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="font-medium">{cat.category}</span>
                  <span className="font-mono text-slate-400">
                    {cat.count} files ({cat.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, cat.percentage * 2)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Department Compliance Index Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Building className="w-4 h-4 text-emerald-400" />
          Departmental Document Compliance Index
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-semibold">
              <tr>
                <th className="py-3 px-4">Department / Unit</th>
                <th className="py-3 px-4">Enrolled Candidates</th>
                <th className="py-3 px-4">Mandatory Verified</th>
                <th className="py-3 px-4">Pending Review</th>
                <th className="py-3 px-4">Discrepancy / Backlog</th>
                <th className="py-3 px-4 text-right">Compliance Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {[
                {
                  dept: "Computer Science & Engineering",
                  enrolled: 420,
                  verified: 405,
                  pending: 12,
                  rejected: 3,
                  score: "96.4%",
                },
                {
                  dept: "Electronics & Communication Engineering",
                  enrolled: 360,
                  verified: 342,
                  pending: 15,
                  rejected: 3,
                  score: "95.0%",
                },
                {
                  dept: "Mechanical Engineering",
                  enrolled: 240,
                  verified: 224,
                  pending: 11,
                  rejected: 5,
                  score: "93.3%",
                },
                {
                  dept: "Management Studies (MBA)",
                  enrolled: 120,
                  verified: 118,
                  pending: 2,
                  rejected: 0,
                  score: "98.3%",
                },
              ].map((row) => (
                <tr key={row.dept} className="hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-semibold text-slate-100">
                    {row.dept}
                  </td>
                  <td className="py-3 px-4">{row.enrolled}</td>
                  <td className="py-3 px-4 text-emerald-400 font-medium">
                    {row.verified}
                  </td>
                  <td className="py-3 px-4 text-amber-400 font-medium">
                    {row.pending}
                  </td>
                  <td className="py-3 px-4 text-rose-400 font-medium">
                    {row.rejected}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-blue-400">
                    {row.score}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
