import React from "react";
import {
  DocumentStatus,
  ConfidentialityLevel,
  VerificationPriority,
  DocumentExpiryStatus,
  CertificateRequestStatus,
  IssuedCertificateStatus,
  InstitutionalRecordStatus,
} from "@campusos/types";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  FileQuestion,
  Archive,
  Ban,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Lock,
} from "lucide-react";

export function DocumentStatusBadge({ status }: { status: DocumentStatus | string }) {
  switch (status) {
    case DocumentStatus.VERIFIED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Verified
        </span>
      );
    case DocumentStatus.UNDER_REVIEW:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Clock className="w-3.5 h-3.5 text-blue-400" />
          Under Review
        </span>
      );
    case DocumentStatus.UPLOADED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          Uploaded (Pending)
        </span>
      );
    case DocumentStatus.REJECTED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          Rejected
        </span>
      );
    case DocumentStatus.EXPIRED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20">
          <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
          Expired
        </span>
      );
    case DocumentStatus.REQUIRED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
          <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />
          Required
        </span>
      );
    case DocumentStatus.MISSING:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
          <FileQuestion className="w-3.5 h-3.5 text-red-400" />
          Missing
        </span>
      );
    case DocumentStatus.ARCHIVED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
          <Archive className="w-3.5 h-3.5 text-slate-400" />
          Archived
        </span>
      );
    case DocumentStatus.REVOKED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-600/10 text-rose-500 border border-rose-600/20">
          <Ban className="w-3.5 h-3.5 text-rose-500" />
          Revoked
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          {status}
        </span>
      );
  }
}

export function ConfidentialityBadge({ level }: { level: ConfidentialityLevel | string }) {
  switch (level) {
    case ConfidentialityLevel.PUBLIC:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/40 text-emerald-300 border border-emerald-800/40">
          <Shield className="w-3 h-3 text-emerald-400" />
          Public Record
        </span>
      );
    case ConfidentialityLevel.INTERNAL:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-blue-950/40 text-blue-300 border border-blue-800/40">
          <ShieldCheck className="w-3 h-3 text-blue-400" />
          Internal Use
        </span>
      );
    case ConfidentialityLevel.CONFIDENTIAL:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/40 text-amber-300 border border-amber-800/40">
          <Lock className="w-3 h-3 text-amber-400" />
          Confidential
        </span>
      );
    case ConfidentialityLevel.RESTRICTED:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-950/50 text-rose-300 border border-rose-800/50">
          <ShieldAlert className="w-3 h-3 text-rose-400" />
          Restricted Access
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
          {level}
        </span>
      );
  }
}

export function ExpiryStatusBadge({ status }: { status: DocumentExpiryStatus }) {
  switch (status) {
    case DocumentExpiryStatus.EXPIRED:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <AlertTriangle className="w-3 h-3 text-rose-400" />
          Expired
        </span>
      );
    case DocumentExpiryStatus.EXPIRING_7_DAYS:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
          <AlertTriangle className="w-3 h-3 text-red-400" />
          Expiring in ≤ 7 Days
        </span>
      );
    case DocumentExpiryStatus.EXPIRING_30_DAYS:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Clock className="w-3 h-3 text-amber-400" />
          Expiring in ≤ 30 Days
        </span>
      );
    case DocumentExpiryStatus.EXPIRING_90_DAYS:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Clock className="w-3 h-3 text-blue-400" />
          Expiring in ≤ 90 Days
        </span>
      );
    case DocumentExpiryStatus.VALID:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Valid
        </span>
      );
    case DocumentExpiryStatus.NO_EXPIRY:
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
          Permanent
        </span>
      );
  }
}

export function CertificateRequestStatusBadge({ status }: { status: CertificateRequestStatus | string }) {
  switch (status) {
    case CertificateRequestStatus.ISSUED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Issued
        </span>
      );
    case CertificateRequestStatus.APPROVED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
          Approved
        </span>
      );
    case CertificateRequestStatus.UNDER_REVIEW:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Clock className="w-3.5 h-3.5 text-blue-400" />
          In Review
        </span>
      );
    case CertificateRequestStatus.SUBMITTED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          Submitted
        </span>
      );
    case CertificateRequestStatus.REJECTED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          Rejected
        </span>
      );
    case CertificateRequestStatus.CANCELLED:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
          <Ban className="w-3.5 h-3.5 text-slate-400" />
          Cancelled
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
          {status}
        </span>
      );
  }
}
