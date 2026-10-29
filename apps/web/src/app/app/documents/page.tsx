"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  documentReportsService,
  documentsService,
  certificateRequestsService,
  institutionalRecordsService,
} from "@/services";
import {
  DocumentsDashboardSummary,
  DocumentItem,
  CertificateRequest,
  InstitutionalRecord,
  DocumentStatus,
} from "@campusos/types";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import {
  DocumentStatusBadge,
  ConfidentialityBadge,
} from "@/components/documents/document-status-badge";
import {
  FileText,
  ShieldCheck,
  Clock,
  XCircle,
  AlertTriangle,
  Award,
  Upload,
  ArrowRight,
  TrendingUp,
  Building,
  CheckCircle2,
  Calendar,
  Layers,
  ChevronRight,
  ExternalLink,
  Search,
  FileCheck,
} from "lucide-react";

export default function DocumentsDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DocumentsDashboardSummary | null>(
    null,
  );
  const [pendingQueue, setPendingQueue] = useState<DocumentItem[]>([]);
  const [recentRequests, setRecentRequests] = useState<CertificateRequest[]>(
    [],
  );
  const [recentRecords, setRecentRecords] = useState<InstitutionalRecord[]>([]);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        const [sumRes, docsRes, reqsRes, recsRes] = await Promise.all([
          documentReportsService.getDashboardSummary(),
          documentsService.listDocuments({ status: "ALL" }),
          certificateRequestsService.listRequests(),
          institutionalRecordsService.listRecords(),
        ]);

        if (sumRes.success && sumRes.data) setSummary(sumRes.data);

        if (docsRes.success && docsRes.data) {
          const queue = docsRes.data.filter(
            (d) =>
              d.status === DocumentStatus.UPLOADED ||
              d.status === DocumentStatus.UNDER_REVIEW,
          );
          setPendingQueue(queue.slice(0, 5));
        }

        if (reqsRes.success && reqsRes.data) {
          setRecentRequests(reqsRes.data.slice(0, 4));
        }

        if (recsRes.success && recsRes.data) {
          setRecentRecords(recsRes.data.slice(0, 3));
        }
      } catch (err) {
        console.error("Failed to load documents dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <FileText className="w-3.5 h-3.5" />
            <span>Digital Vault & Institutional Records</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Document Operations Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Centralized document verification desk, digital certificates
            pipeline, and regulatory institutional repository.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link href="/app/documents/my-documents">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              My Documents
            </Button>
          </Link>
          <Link href="/app/documents/verification">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              Verification Queue
              {summary && summary.pendingVerification > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                  {summary.pendingVerification}
                </span>
              )}
            </Button>
          </Link>
          <Link href="/app/documents/upload">
            <Button
              size="sm"
              className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-700"
            >
              <Upload className="w-4 h-4" />
              Upload Document
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards Row 1: Document Volumes */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Documents"
          value={loading ? "--" : String(summary?.totalDocuments || 0)}
          icon={<FileText className="w-5 h-5 text-blue-400" />}
          subtitle="Registered in Vault"
        />
        <StatCard
          title="Verified Documents"
          value={loading ? "--" : String(summary?.verifiedDocuments || 0)}
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
          subtitle={`${summary?.verificationRate || 0}% completion`}
        />
        <StatCard
          title="Pending Verification"
          value={loading ? "--" : String(summary?.pendingVerification || 0)}
          icon={<Clock className="w-5 h-5 text-amber-400" />}
          subtitle="Needs review action"
        />
        <StatCard
          title="Rejected Documents"
          value={loading ? "--" : String(summary?.rejectedDocuments || 0)}
          icon={<XCircle className="w-5 h-5 text-rose-400" />}
          subtitle="Awaiting re-upload"
        />
      </div>

      {/* KPI Cards Row 2: Lifecycle & Certificates */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Missing Required"
          value={loading ? "--" : String(summary?.missingDocuments || 0)}
          icon={<AlertTriangle className="w-5 h-5 text-purple-400" />}
          subtitle="Admission compliance"
        />
        <StatCard
          title="Expiring Soon"
          value={loading ? "--" : String(summary?.expiringDocuments || 0)}
          icon={<Calendar className="w-5 h-5 text-orange-400" />}
          subtitle="Within 30 calendar days"
        />
        <StatCard
          title="Certificate Requests"
          value={loading ? "--" : String(summary?.certificateRequests || 0)}
          icon={<Award className="w-5 h-5 text-indigo-400" />}
          subtitle="Student applications"
        />
        <StatCard
          title="Pending Requests"
          value={
            loading ? "--" : String(summary?.pendingCertificateRequests || 0)
          }
          icon={<Clock className="w-5 h-5 text-yellow-400" />}
          subtitle="Awaiting issuance approval"
        />
      </div>

      {/* Operational Efficiency Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-blue-950/40 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <span>Operational Turnaround & SLA Metrics</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center md:text-left divide-y md:divide-y-0 md:divide-x divide-slate-800">
          <div>
            <div className="text-2xl font-bold text-emerald-400">
              {summary ? `${summary.verificationRate}%` : "--%"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Verification Rate
            </div>
          </div>
          <div className="md:pl-6 pt-3 md:pt-0">
            <div className="text-2xl font-bold text-rose-400">
              {summary ? `${summary.rejectionRate}%` : "--%"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Rejection Rate</div>
          </div>
          <div className="md:pl-6 pt-3 md:pt-0">
            <div className="text-2xl font-bold text-blue-400">
              {summary ? `${summary.averageVerificationHours}h` : "--"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Avg Verification SLA
            </div>
          </div>
          <div className="md:pl-6 pt-3 md:pt-0">
            <div className="text-2xl font-bold text-slate-200">
              {summary ? summary.documentsUploadedThisMonth : "--"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Uploaded This Month
            </div>
          </div>
          <div className="md:pl-6 pt-3 md:pt-0">
            <div className="text-2xl font-bold text-amber-300">
              {summary ? summary.certificatesIssuedThisMonth : "--"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Certificates Issued
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Pending Queue & Categories / Expiry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Pending Verification Queue */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-amber-400" />
                  Urgent Verification Queue
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Submissions requiring compliance review and endorsement.
                </p>
              </div>
              <Link
                href="/app/documents/verification"
                className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition"
              >
                View Full Queue ({summary?.pendingVerification || 0})
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {loading ? (
              <div className="py-12 text-center text-xs text-slate-500">
                Loading queue items...
              </div>
            ) : pendingQueue.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">
                All document submissions are verified and up-to-date!
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {pendingQueue.map((doc) => (
                  <div
                    key={doc.id}
                    className="py-3.5 flex items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0 mt-0.5">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <Link
                          href={`/app/documents/verification/${doc.id}`}
                          className="text-sm font-semibold text-slate-200 hover:text-blue-400 transition truncate block"
                        >
                          {doc.name}
                        </Link>
                        <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5 font-medium">
                          <span>{doc.ownerName}</span>
                          {doc.ownerRollNumber && (
                            <>
                              <span>•</span>
                              <span className="font-mono text-slate-500">
                                {doc.ownerRollNumber}
                              </span>
                            </>
                          )}
                          <span>•</span>
                          <span className="text-blue-400">{doc.category}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <DocumentStatusBadge status={doc.status} />
                      <Link href={`/app/documents/verification/${doc.id}`}>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs h-7"
                        >
                          Review
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>Standard SLA turnaround threshold: 24 hours</span>
            <Link
              href="/app/documents/all"
              className="text-blue-400 hover:underline"
            >
              Explore All Documents Master Directory →
            </Link>
          </div>
        </div>

        {/* Right Column (1 col): Expiry Radar & Category Breakdown */}
        <div className="space-y-6">
          {/* Expiry Radar Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-400" />
                Document Expiry Radar
              </h3>
              <Link
                href="/app/documents/reports"
                className="text-xs text-blue-400 hover:underline"
              >
                Audit
              </Link>
            </div>

            <div className="space-y-2.5 text-xs">
              <Link
                href="/app/documents/all?status=EXPIRED"
                className="flex items-center justify-between p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/15 transition"
              >
                <span className="text-rose-300 font-medium">
                  Lapsed / Expired Documents
                </span>
                <span className="font-mono font-bold text-rose-400">
                  {summary?.expiryBreakdown.expired || 0}
                </span>
              </Link>

              <Link
                href="/app/documents/all?expiryStatus=EXPIRING_7_DAYS"
                className="flex items-center justify-between p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/15 transition"
              >
                <span className="text-amber-300 font-medium">
                  Expiring within 7 Days
                </span>
                <span className="font-mono font-bold text-amber-400">
                  {summary?.expiryBreakdown.expiring7Days || 0}
                </span>
              </Link>

              <Link
                href="/app/documents/all?expiryStatus=EXPIRING_30_DAYS"
                className="flex items-center justify-between p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/15 transition"
              >
                <span className="text-blue-300 font-medium">
                  Expiring within 30 Days
                </span>
                <span className="font-mono font-bold text-blue-400">
                  {summary?.expiryBreakdown.expiring30Days || 0}
                </span>
              </Link>

              <div className="flex items-center justify-between p-2 text-slate-400">
                <span>Valid / Permanent Records</span>
                <span className="font-mono text-slate-300">
                  {(summary?.expiryBreakdown.valid || 0) +
                    (summary?.expiryBreakdown.noExpiry || 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Categories Catalog */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                Category Distribution
              </h3>
              <Link
                href="/app/documents/categories"
                className="text-xs text-blue-400 hover:underline"
              >
                Manage
              </Link>
            </div>

            <div className="space-y-2">
              {summary?.categoryDistribution.slice(0, 5).map((cat) => (
                <div key={cat.category} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-slate-300">
                    <span>{cat.category}</span>
                    <span className="font-mono text-slate-400">
                      {cat.count} ({cat.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, cat.percentage * 2)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Lower Section: Certificates & Institutional Records Split */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Certificate Pipeline Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Award className="w-4 h-4 text-indigo-400" />
                Recent Certificate Requests
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Bonafide, NOCs, and transcripts submitted by students.
              </p>
            </div>
            <Link
              href="/app/documents/certificates/requests"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              View All
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {recentRequests.map((req) => (
              <div
                key={req.id}
                className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    <Link
                      href={`/app/documents/certificates/requests/${req.id}`}
                      className="hover:text-blue-400 transition"
                    >
                      {req.templateName}
                    </Link>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {req.studentName} ({req.rollNumber}) • {req.requestId}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {req.status}
                  </span>
                  <Link href={`/app/documents/certificates/requests/${req.id}`}>
                    <ChevronRight className="w-4 h-4 text-slate-500 hover:text-slate-300" />
                  </Link>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <Link
              href="/app/documents/certificates/templates"
              className="text-slate-400 hover:text-slate-200"
            >
              Manage Templates ({MOCK_CERTIFICATE_TEMPLATES_COUNT || 5})
            </Link>
            <Link
              href="/app/documents/certificates"
              className="text-blue-400 hover:underline"
            >
              Certificate Center →
            </Link>
          </div>
        </div>

        {/* Institutional Records Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Building className="w-4 h-4 text-emerald-400" />
                Institutional & Regulatory Records
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Accreditation, statutory approvals, and institutional policies.
              </p>
            </div>
            <Link
              href="/app/documents/institutional-records"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              Browse Register
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {recentRecords.map((rec) => (
              <div
                key={rec.id}
                className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-center justify-between"
              >
                <div className="min-w-0 pr-2">
                  <div className="text-xs font-semibold text-slate-200 truncate">
                    <Link
                      href={`/app/documents/institutional-records/${rec.id}`}
                      className="hover:text-blue-400 transition"
                    >
                      {rec.recordName}
                    </Link>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2">
                    <span className="text-blue-400 font-mono">{rec.code}</span>
                    <span>•</span>
                    <span className="truncate">{rec.ownerDepartment}</span>
                  </div>
                </div>
                <div className="shrink-0">
                  <ConfidentialityBadge level={rec.confidentiality} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-500">
              Autonomous governance compliance
            </span>
            <Link
              href="/app/documents/institutional-records"
              className="text-blue-400 hover:underline"
            >
              View Institutional Repository →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

const MOCK_CERTIFICATE_TEMPLATES_COUNT = 5;
