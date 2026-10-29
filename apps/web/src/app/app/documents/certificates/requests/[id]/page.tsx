"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { certificateRequestsService } from "@/services/certificate-requests.service";
import { CertificateRequest, CertificateRequestStatus } from "@campusos/types";
import { CertificateRequestStatusBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Award,
  ArrowLeft,
  User,
  CheckCircle2,
  XCircle,
  Clock,
  History,
  Building,
  Calendar,
  AlertCircle,
  Check,
  Printer,
  Download,
} from "lucide-react";

export default function CertificateRequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [request, setRequest] = useState<CertificateRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionProcessing, setActionProcessing] = useState(false);

  // Reject Dialog
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  useEffect(() => {
    async function loadRequest() {
      try {
        setLoading(true);
        const res = await certificateRequestsService.getRequestById(id);
        if (res.success && res.data) {
          setRequest(res.data);
        } else {
          setRequest(null);
        }
      } catch (err) {
        console.error("Failed to load request detail:", err);
      } finally {
        setLoading(false);
      }
    }

    loadRequest();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading certificate request...
      </div>
    );
  }

  if (!request) {
    notFound();
  }

  const handleApprove = async () => {
    try {
      setActionProcessing(true);
      const res = await certificateRequestsService.approveRequest(
        request.id,
        "user-super-admin-01",
        "Dr. Arvind Swaminathan (Registrar)",
        "Student eligibility and fee ledger verified.",
      );
      if (res.success && res.data) {
        setRequest({ ...res.data });
        alert(
          "Certificate request approved! Now eligible for digital certificate generation.",
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      alert("A rejection reason is mandatory.");
      return;
    }

    try {
      setActionProcessing(true);
      const res = await certificateRequestsService.rejectRequest(
        request.id,
        rejectionReason,
        "user-super-admin-01",
        "Dr. Arvind Swaminathan (Registrar)",
      );
      if (res.success && res.data) {
        setRequest({ ...res.data });
        setRejectModalOpen(false);
        alert("Request rejected and reason dispatched to student.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  const handleIssueCertificate = async () => {
    try {
      setActionProcessing(true);
      const res = await certificateRequestsService.issueCertificateForRequest(
        request.id,
        "Office of the Registrar",
      );
      if (res.success && res.data) {
        // Reload fresh state
        const refreshed = await certificateRequestsService.getRequestById(
          request.id,
        );
        if (refreshed.data) setRequest(refreshed.data);
        alert(
          `Certificate issued! Serial Number: ${res.data.certificateNumber}`,
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/certificates/requests"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Certificate Pipeline
        </Link>
        <span className="font-mono text-xs text-blue-400 font-bold bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
          {request.requestId}
        </span>
      </div>

      {/* Hero Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <CertificateRequestStatusBadge status={request.status} />
            <span className="font-mono text-xs text-amber-400 font-bold">
              {request.certificateType}
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">
            {request.templateName}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Requested on {new Date(request.requestedDate).toLocaleDateString()}{" "}
            by <strong className="text-slate-200">{request.studentName}</strong>{" "}
            ({request.rollNumber})
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {request.status === CertificateRequestStatus.SUBMITTED && (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setRejectModalOpen(true)}
                disabled={actionProcessing}
                className="text-xs border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </Button>
              <Button
                size="sm"
                onClick={handleApprove}
                disabled={actionProcessing}
                className="text-xs bg-indigo-600 hover:bg-indigo-700 font-semibold"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Approve Request
              </Button>
            </>
          )}

          {request.status === CertificateRequestStatus.APPROVED && (
            <Button
              size="sm"
              onClick={handleIssueCertificate}
              disabled={actionProcessing}
              className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 font-semibold shadow-sm"
            >
              <Award className="w-4 h-4" />
              Generate & Issue Certificate
            </Button>
          )}

          {request.status === CertificateRequestStatus.ISSUED && (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
              Digitally Issued
            </div>
          )}
        </div>
      </div>

      {/* Main Grid: Details & Validation (Left 7 cols) vs Timeline (Right 5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-6">
          {/* Requester Profile */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-blue-400" />
              Applicant Profile
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block">
                  Student Name
                </span>
                <span className="font-semibold text-slate-200 mt-0.5 block">
                  {request.studentName}
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block">
                  Register Number
                </span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5 block">
                  {request.rollNumber}
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block">
                  Program
                </span>
                <span className="text-slate-200 mt-0.5 block">
                  {request.program}
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] uppercase text-slate-500 block">
                  Department
                </span>
                <span className="text-slate-200 mt-0.5 block">
                  {request.department}
                </span>
              </div>
            </div>
          </div>

          {/* Certificate Specifications */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 text-xs">
            <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-amber-400" />
              Certificate Request Specifications
            </h3>
            <div className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-2">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-semibold">
                  Statement of Purpose
                </span>
                <p className="text-slate-200 mt-0.5">{request.purpose}</p>
              </div>
              {request.requiredByDate && (
                <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                  Required By Deadline:{" "}
                  <strong className="text-amber-400">
                    {request.requiredByDate}
                  </strong>
                </div>
              )}
            </div>
          </div>

          {/* Validation Checks */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              Institutional Eligibility Checks
            </h3>
            <div className="space-y-2 text-xs">
              {request.validationChecks.map((chk) => (
                <div
                  key={chk.id}
                  className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    {chk.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <div className="font-semibold text-slate-200">
                        {chk.title}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {chk.details}
                      </div>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      chk.passed
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    }`}
                  >
                    {chk.passed ? "PASSED" : "FAILED"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Rejection notice if present */}
          {request.rejectionReason && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs space-y-1">
              <span className="font-bold text-rose-400 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" />
                Reason for Rejection
              </span>
              <p className="text-rose-300">{request.rejectionReason}</p>
            </div>
          )}
        </div>

        {/* Right Column: Governance Timeline (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-blue-400" />
            Issuance Governance Timeline
          </h3>

          <div className="relative border-l-2 border-slate-800 ml-3 space-y-5 pt-1 text-xs">
            {request.timeline.map((entry) => (
              <div key={entry.id} className="relative pl-5">
                <div className="absolute -left-[7px] top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-blue-500" />
                <div className="bg-slate-950 p-3 rounded border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">
                      {entry.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {new Date(entry.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    By {entry.performedBy}
                  </div>
                  {entry.notes && (
                    <div className="mt-1.5 p-1.5 bg-slate-900 rounded text-[11px] text-slate-300 italic border border-slate-800/80">
                      {entry.notes}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* REJECT MODAL */}
      <Dialog
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="Reject Certificate Request"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            Please provide the reason this certificate request cannot be
            fulfilled at this time.
          </p>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Rejection Reason <span className="text-rose-400">*</span>
            </label>
            <Textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Student has active semester backlogs; course completion cannot be issued until all credits are cleared."
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setRejectModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={handleReject}
              disabled={actionProcessing}
              className="text-xs bg-rose-600 hover:bg-rose-700"
            >
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
