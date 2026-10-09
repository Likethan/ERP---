"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound, useRouter } from "next/navigation";
import { documentsService } from "@/services/documents.service";
import { documentVerificationService } from "@/services/document-verification.service";
import { DocumentItem, DocumentStatus } from "@campusos/types";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { DocumentPreview } from "@/components/documents/document-preview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Clock,
  User,
  Building,
  RotateCcw,
  Check,
  AlertCircle,
  FileText,
} from "lucide-react";

export default function VerificationWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const router = useRouter();

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [checklist, setChecklist] = useState<
    { id: string; label: string; checked: boolean; required: boolean }[]
  >([
    { id: "c1", label: "Document classification matches stated requirement", checked: true, required: true },
    { id: "c2", label: "Legal candidate name & registration number authenticated", checked: true, required: true },
    { id: "c3", label: "Official issuing authority seal / digital stamp legible", checked: false, required: true },
    { id: "c4", label: "Issue and validity dates compliant with semester regulations", checked: false, required: true },
    { id: "c5", label: "Zero indications of tampering, cropping, or resolution blur", checked: true, required: true },
  ]);

  // Reject Modal State
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const [reuploadModalOpen, setReuploadModalOpen] = useState(false);
  const [reuploadInstruction, setReuploadInstruction] = useState("");
  const [actionProcessing, setActionProcessing] = useState(false);

  useEffect(() => {
    async function loadDoc() {
      try {
        setLoading(true);
        const res = await documentsService.getDocumentById(id);
        if (res.success && res.data) {
          setDocument(res.data);
          if (res.data.verificationChecklist && res.data.verificationChecklist.length > 0) {
            setChecklist(res.data.verificationChecklist);
          }
        } else {
          setDocument(null);
        }
      } catch (err) {
        console.error("Failed to load document for verification:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDoc();
  }, [id]);

  if (loading) {
    return <div className="py-24 text-center text-xs text-slate-500">Opening verification workspace...</div>;
  }

  if (!document) {
    notFound();
  }

  const toggleChecklist = (itemIndex: number) => {
    setChecklist((prev) =>
      prev.map((item, idx) => (idx === itemIndex ? { ...item, checked: !item.checked } : item))
    );
  };

  const allMandatoryChecked = checklist.filter((c) => c.required).every((c) => c.checked);

  const handleStartReview = async () => {
    try {
      setActionProcessing(true);
      const res = await documentVerificationService.startVerification(
        document.id,
        "user-super-admin-01",
        "Dr. Arvind Swaminathan (Registrar)"
      );
      if (res.success && res.data) {
        setDocument({ ...res.data });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  const handleVerify = async () => {
    try {
      setActionProcessing(true);
      const res = await documentVerificationService.verifyDocument(
        document.id,
        "Dr. Arvind Swaminathan (Registrar)",
        "Verified all statutory checklist requirements."
      );
      if (res.success && res.data) {
        setDocument({ ...res.data });
        alert(`Document "${document.name}" has been successfully verified!`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      alert("A specific rejection reason is mandatory.");
      return;
    }

    try {
      setActionProcessing(true);
      const res = await documentVerificationService.rejectDocument(
        document.id,
        rejectionReason,
        "Dr. Arvind Swaminathan (Registrar)"
      );
      if (res.success && res.data) {
        setDocument({ ...res.data });
        setRejectModalOpen(false);
        alert("Document rejected. Official reason logged and notice dispatched to candidate.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  const handleRequestReupload = async () => {
    if (!reuploadInstruction.trim()) {
      alert("Instructions for the candidate are required.");
      return;
    }

    try {
      setActionProcessing(true);
      const res = await documentVerificationService.requestReupload(
        document.id,
        reuploadInstruction,
        "Dr. Arvind Swaminathan (Registrar)"
      );
      if (res.success && res.data) {
        setDocument({ ...res.data });
        setReuploadModalOpen(false);
        alert("Re-upload request recorded and sent to student.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionProcessing(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/verification"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Verification Queue
        </Link>
        <div className="flex items-center gap-2">
          <DocumentStatusBadge status={document.status} />
          <span className="text-xs text-slate-500 font-mono">DOC ID: {document.id}</span>
        </div>
      </div>

      {/* Workspace Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            Verification Workspace
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">{document.name}</h1>
          <p className="text-xs text-slate-400 mt-1">
            Candidate: <strong className="text-slate-200">{document.ownerName}</strong> ({document.ownerRollNumber || document.ownerType}) • Category: {document.category}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {document.status === DocumentStatus.UPLOADED && (
            <Button
              size="sm"
              onClick={handleStartReview}
              disabled={actionProcessing}
              className="text-xs bg-blue-600 hover:bg-blue-700"
            >
              Start Active Review
            </Button>
          )}

          {document.status !== DocumentStatus.VERIFIED && (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setReuploadModalOpen(true)}
                disabled={actionProcessing}
                className="text-xs gap-1 border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Request Re-upload
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setRejectModalOpen(true)}
                disabled={actionProcessing}
                className="text-xs gap-1 border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </Button>
              <Button
                size="sm"
                onClick={handleVerify}
                disabled={!allMandatoryChecked || actionProcessing}
                className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 font-semibold disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                Endorse & Verify Document
              </Button>
            </>
          )}

          {document.status === DocumentStatus.VERIFIED && (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
              Verified by {document.verifiedBy || "Registrar"}
            </div>
          )}
        </div>
      </div>

      {/* Split Workspace Layout: Document Preview (Left) vs Checklist & Details (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Full Document Preview (7 cols) */}
        <div className="lg:col-span-7">
          <DocumentPreview document={document} />
        </div>

        {/* Right Column: Verification Checklist & Meta (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Interactive Checklist Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
                <Check className="w-4 h-4 text-emerald-400" />
                Verification Checklist
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                {checklist.filter((c) => c.checked).length} / {checklist.length} satisfied
              </span>
            </div>

            <div className="space-y-2.5">
              {checklist.map((item, idx) => (
                <div
                  key={item.id}
                  onClick={() => toggleChecklist(idx)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-start gap-2.5 ${
                    item.checked
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-200"
                      : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded mt-0.5 flex items-center justify-center shrink-0 border ${
                      item.checked
                        ? "bg-emerald-500 border-emerald-400 text-slate-950"
                        : "border-slate-600"
                    }`}
                  >
                    {item.checked && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <span className="block font-medium">{item.label}</span>
                    {item.required && (
                      <span className="text-[10px] text-amber-400/80 font-mono mt-0.5 block">
                        * Mandatory requirement
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {!allMandatoryChecked && document.status !== DocumentStatus.VERIFIED && (
              <p className="text-[11px] text-amber-400/80 mt-3 italic flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                All mandatory checks must be validated before endorsing.
              </p>
            )}
          </div>

          {/* Document Key Particulars */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 text-xs">
            <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-2">
              Declared Metadata
            </h3>
            <div className="grid grid-cols-2 gap-2 text-slate-300">
              <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] text-slate-500 block">DOCUMENT NUMBER</span>
                <span className="font-mono text-slate-200 mt-0.5 block">
                  {document.documentNumber || "Not recorded"}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] text-slate-500 block">ISSUING AUTHORITY</span>
                <span className="text-slate-200 mt-0.5 block truncate">
                  {document.issuingAuthority || "Not recorded"}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] text-slate-500 block">ISSUE DATE</span>
                <span className="text-slate-200 mt-0.5 block">{document.issueDate || "N/A"}</span>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                <span className="text-[10px] text-slate-500 block">EXPIRY DATE</span>
                <span className="text-slate-200 mt-0.5 block">{document.expiryDate || "Permanent"}</span>
              </div>
            </div>
          </div>

          {/* Rejection Notice if currently rejected */}
          {document.rejectionReason && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-xs space-y-1">
              <span className="font-bold text-rose-400 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" />
                Active Rejection Record
              </span>
              <p className="text-rose-300">{document.rejectionReason}</p>
            </div>
          )}
        </div>
      </div>

      {/* REJECT MODAL */}
      <Dialog
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="Reject Document Submission"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            Please enter an official reason for rejection. This notice will be immediately recorded in the document audit trail and communicated to the candidate.
          </p>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Rejection Reason <span className="text-rose-400">*</span>
            </label>
            <Textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Scanned copy is illegible; revenue taluk seal is unreadable; please upload original color scan."
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
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

      {/* REQUEST RE-UPLOAD MODAL */}
      <Dialog
        isOpen={reuploadModalOpen}
        onClose={() => setReuploadModalOpen(false)}
        title="Request Document Re-upload"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            Notify the candidate to supply a replacement document with corrective guidance.
          </p>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Instructions for Student / Staff <span className="text-amber-400">*</span>
            </label>
            <Textarea
              rows={3}
              value={reuploadInstruction}
              onChange={(e) => setReuploadInstruction(e.target.value)}
              placeholder="e.g. Please upload the front and reverse side of the 10+2 marksheet in high resolution (minimum 300 DPI)."
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setReuploadModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={handleRequestReupload}
              disabled={actionProcessing}
              className="text-xs bg-amber-600 hover:bg-amber-700"
            >
              Dispatch Notice
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
