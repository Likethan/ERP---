"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  certificateTemplatesService,
  certificateRequestsService,
  certificatesService,
} from "@/services";
import {
  CertificateTemplate,
  CertificateRequest,
  IssuedCertificate,
  IssuedCertificateStatus,
} from "@campusos/types";
import { CertificateRequestStatusBadge } from "@/components/documents/document-status-badge";
import { CertificatePreview } from "@/components/documents/certificate-preview";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Award,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Ban,
  Search,
  Plus,
  ArrowRight,
  ShieldCheck,
  QrCode,
  Layers,
  ChevronRight,
} from "lucide-react";

export default function CertificateCenterPage() {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<CertificateTemplate[]>([]);
  const [requests, setRequests] = useState<CertificateRequest[]>([]);
  const [issuedCerts, setIssuedCerts] = useState<IssuedCertificate[]>([]);

  // Verification Search Tool State
  const [verifyCode, setVerifyCode] = useState("");
  const [verifiedResult, setVerifiedResult] =
    useState<IssuedCertificate | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [tmplsRes, reqsRes, certsRes] = await Promise.all([
          certificateTemplatesService.listTemplates(),
          certificateRequestsService.listRequests(),
          certificatesService.listIssuedCertificates(),
        ]);

        if (tmplsRes.success && tmplsRes.data) setTemplates(tmplsRes.data);
        if (reqsRes.success && reqsRes.data) setRequests(reqsRes.data);
        if (certsRes.success && certsRes.data) setIssuedCerts(certsRes.data);
      } catch (err) {
        console.error("Failed to load certificate center data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleVerifyLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyCode.trim()) return;

    try {
      setVerifying(true);
      setHasSearched(true);
      const res = await certificatesService.verifyCertificate(verifyCode);
      setVerifiedResult(res.data);
    } catch (err) {
      console.error(err);
      setVerifiedResult(null);
    } finally {
      setVerifying(false);
    }
  };

  const pendingRequests = requests.filter(
    (r) => r.status === "SUBMITTED" || r.status === "UNDER_REVIEW",
  );
  const revokedCerts = issuedCerts.filter(
    (c) => c.status === IssuedCertificateStatus.REVOKED,
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1">
            <Award className="w-3.5 h-3.5" />
            <span>Digital Credential Engine</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Certificate Management Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage institutional certificate templates, process student
            requests, issue verifiable credentials, and revoke certifications.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link href="/app/documents/certificates/templates">
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
              <Layers className="w-4 h-4 text-blue-400" />
              Templates ({templates.length})
            </Button>
          </Link>
          <Link href="/app/documents/certificates/requests">
            <Button
              size="sm"
              className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
            >
              <Clock className="w-4 h-4" />
              Request Pipeline ({requests.length})
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          title="Active Templates"
          value={loading ? "--" : String(templates.length)}
          icon={<Layers className="w-5 h-5 text-blue-400" />}
          subtitle="Bonafide, NOC, etc."
        />
        <StatCard
          title="Total Requests"
          value={loading ? "--" : String(requests.length)}
          icon={<FileText className="w-5 h-5 text-indigo-400" />}
          subtitle="Lifetime volume"
        />
        <StatCard
          title="Pending Approval"
          value={loading ? "--" : String(pendingRequests.length)}
          icon={<Clock className="w-5 h-5 text-amber-400" />}
          subtitle="Action required"
        />
        <StatCard
          title="Issued Certificates"
          value={loading ? "--" : String(issuedCerts.length)}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          subtitle="Valid credentials"
        />
        <StatCard
          title="Revoked Credentials"
          value={loading ? "--" : String(revokedCerts.length)}
          icon={<Ban className="w-5 h-5 text-rose-400" />}
          subtitle="Flagged / Voided"
        />
      </div>

      {/* Public Digital Verification Lookup Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="max-w-2xl mx-auto space-y-3 text-center">
          <div className="inline-flex p-2.5 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20 mb-1">
            <QrCode className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-100">
            Certificate & Credential Authentication Tool
          </h2>
          <p className="text-xs text-slate-400">
            Verify the authenticity of any institutional certificate using its
            serial number or digital verification hash.
          </p>

          <form
            onSubmit={handleVerifyLookup}
            className="flex gap-2 max-w-lg mx-auto pt-2"
          >
            <Input
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value)}
              placeholder="e.g. CAMPUSOS/CERT/2026/0041"
              className="bg-slate-950 border-slate-700 text-xs font-mono"
            />
            <Button
              type="submit"
              disabled={verifying}
              className="text-xs bg-amber-600 hover:bg-amber-700 font-semibold shrink-0"
            >
              {verifying ? "Verifying..." : "Verify Certificate"}
            </Button>
          </form>

          {/* Verification Result Output */}
          {hasSearched && (
            <div className="pt-4 text-left">
              {verifiedResult ? (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                    AUTHENTIC INSTITUTIONAL CREDENTIAL CONFIRMED
                  </div>
                  <div className="text-xs text-slate-300">
                    Recipient:{" "}
                    <strong className="text-slate-100">
                      {verifiedResult.recipientName}
                    </strong>{" "}
                    ({verifiedResult.recipientRollNumber}) • Program:{" "}
                    {verifiedResult.recipientProgram}
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Certificate No: {verifiedResult.certificateNumber} • Issued:{" "}
                    {verifiedResult.issueDate} • Status:{" "}
                    <strong
                      className={
                        verifiedResult.status === "ISSUED"
                          ? "text-emerald-400"
                          : "text-rose-400"
                      }
                    >
                      {verifiedResult.status}
                    </strong>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-center text-xs text-rose-300">
                  <XCircle className="w-5 h-5 text-rose-400 mx-auto mb-1" />
                  No authentic credential matching{" "}
                  <strong>"{verifyCode}"</strong> was found in the institutional
                  registry.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Two Column Split: Recent Requests & Issued Certificates */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Certificate Requests Pipeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400" />
                  Recent Certificate Requests
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Live student requests under validation and review.
                </p>
              </div>
              <Link
                href="/app/documents/certificates/requests"
                className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                View Pipeline ({requests.length})
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {requests.slice(0, 4).map((req) => (
                <div
                  key={req.id}
                  className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                >
                  <div>
                    <Link
                      href={`/app/documents/certificates/requests/${req.id}`}
                      className="font-semibold text-slate-200 hover:text-blue-400 transition"
                    >
                      {req.templateName}
                    </Link>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {req.studentName} ({req.rollNumber}) • {req.requestId}
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <CertificateRequestStatusBadge status={req.status} />
                    <Link
                      href={`/app/documents/certificates/requests/${req.id}`}
                    >
                      <ChevronRight className="w-4 h-4 text-slate-500 hover:text-slate-300" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 mt-4 flex items-center justify-end">
            <Link
              href="/app/documents/certificates/requests"
              className="text-xs text-blue-400 hover:underline"
            >
              Open Full Certificate Pipeline →
            </Link>
          </div>
        </div>

        {/* Right Column: Issued Certificates Directory */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <Award className="w-4 h-4 text-emerald-400" />
                  Issued Digital Credentials
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Digitally sealed certificates with cryptographic verification.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {issuedCerts.map((cert) => (
                <div
                  key={cert.id}
                  className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-semibold text-slate-200">
                      {cert.certificateType} Certificate
                    </span>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {cert.recipientName} ({cert.recipientRollNumber})
                    </div>
                    <div className="font-mono text-[10px] text-blue-400 mt-0.5">
                      {cert.certificateNumber}
                    </div>
                  </div>

                  <div className="text-right">
                    {cert.status === IssuedCertificateStatus.REVOKED ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                        REVOKED
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        VALID
                      </span>
                    )}
                    <div className="text-[10px] text-slate-500 mt-1">
                      {cert.issueDate}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 mt-4 flex items-center justify-between text-xs text-slate-500">
            <span>Sealed with institutional SHA256 signature</span>
            <Link
              href="/app/documents/certificates/templates"
              className="text-blue-400 hover:underline"
            >
              Configure Templates →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
