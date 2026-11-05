"use client";

import React from "react";
import { IssuedCertificate, IssuedCertificateStatus } from "@campusos/types";
import {
  Award,
  QrCode,
  ShieldCheck,
  Ban,
  Download,
  Printer,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface CertificatePreviewProps {
  certificate: IssuedCertificate;
  className?: string;
}

export function CertificatePreview({
  certificate,
  className = "",
}: CertificatePreviewProps) {
  const isRevoked = certificate.status === IssuedCertificateStatus.REVOKED;

  return (
    <div
      className={`flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-md ${className}`}
    >
      {/* Action Toolbar */}
      <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-yellow-600" />
          <span className="text-xs font-semibold text-slate-900">
            Official Institutional Credential
          </span>
          {isRevoked ? (
            <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
              REVOKED
            </span>
          ) : (
            <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              DIGITALLY ISSUED
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="text-xs h-7 gap-1"
            onClick={() =>
              alert(
                `Certificate ${certificate.certificateNumber} print layout initiated.`,
              )
            }
          >
            <Printer className="w-3.5 h-3.5" />
            Print
          </Button>
          <Button
            size="sm"
            className="text-xs h-7 gap-1 bg-yellow-400 hover:bg-yellow-500 text-slate-950 font-bold shadow-xs border-0"
            onClick={() =>
              alert(
                `Downloading signed credential ${certificate.certificateNumber}`,
              )
            }
          >
            <Download className="w-3.5 h-3.5" />
            Download PDF
          </Button>
        </div>
      </div>

      {/* Parchment Surface */}
      <div className="p-8 md:p-12 bg-slate-100 flex items-center justify-center">
        <div className="w-full max-w-2xl bg-white border-2 border-yellow-400 rounded-lg p-8 md:p-12 shadow-xl relative text-center">
          {/* Subtle Corner Accents */}
          <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-yellow-500" />
          <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-yellow-500" />
          <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-yellow-500" />
          <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-yellow-500" />

          {/* Revoked Watermark Overlay */}
          {isRevoked && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
              <div className="transform -rotate-12 border-4 border-rose-500/60 text-rose-500/70 font-black text-5xl tracking-widest px-8 py-3 uppercase rounded">
                REVOKED
              </div>
            </div>
          )}

          {/* Header */}
          <div className="space-y-1 mb-8">
            <div className="text-[11px] uppercase tracking-widest text-amber-800 font-mono font-bold">
              CampusOS University System • Institutional Repository
            </div>
            <h1 className="text-xl md:text-2xl font-serif font-bold text-slate-900 tracking-wide">
              CAMPUS INSTITUTE OF TECHNOLOGY
            </h1>
            <p className="text-xs text-slate-500">
              Autonomous Institution Accredited by NAAC with 'A++' Grade
            </p>
          </div>

          {/* Certificate Type */}
          <div className="my-6">
            <span className="text-xs uppercase tracking-widest text-slate-500 font-semibold block mb-2">
              This is to certify that
            </span>
            <div className="text-2xl md:text-3xl font-serif font-bold text-yellow-950 tracking-wide">
              {certificate.recipientName}
            </div>
            <div className="text-xs font-mono text-slate-600 mt-1">
              Roll / Register No: {certificate.recipientRollNumber}
            </div>
          </div>

          {/* Endorsement Body */}
          <p className="text-xs md:text-sm text-slate-700 max-w-lg mx-auto leading-relaxed my-6">
            is a bonafide student of this institution pursuing{" "}
            <span className="font-semibold text-slate-900">
              {certificate.recipientProgram}
            </span>{" "}
            in the Department of{" "}
            <span className="font-semibold text-slate-900">
              {certificate.recipientDepartment}
            </span>
            . This official credential has been authenticated and entered into
            the institutional registry under the seal of the issuing authority.
          </p>

          {/* Signatures & QR Code Section */}
          <div className="grid grid-cols-3 items-end pt-8 mt-6 border-t border-slate-200 text-xs">
            {/* Left: Issue Date & Cert Number */}
            <div className="text-left space-y-1">
              <div className="text-[10px] text-slate-500 uppercase font-mono">
                Certificate Number
              </div>
              <div className="font-mono text-xs font-semibold text-slate-900">
                {certificate.certificateNumber}
              </div>
              <div className="text-[10px] text-slate-500">
                Issue Date: {certificate.issueDate}
              </div>
            </div>

            {/* Center: QR Verification */}
            <div className="flex flex-col items-center justify-center">
              <div className="p-2 bg-white rounded border border-slate-200 shadow-sm">
                <QrCode className="w-12 h-12 text-slate-900" />
              </div>
              <span className="text-[9px] font-mono text-slate-500 mt-1">
                Scan to Verify
              </span>
            </div>

            {/* Right: Issuing Signatory */}
            <div className="text-right space-y-1">
              <div className="font-serif italic text-sm text-slate-800">
                Dr. Arvind Swaminathan
              </div>
              <div className="w-28 ml-auto border-b border-slate-300 my-1" />
              <div className="text-[11px] font-semibold text-slate-900">
                {certificate.issuingAuthority}
              </div>
              <div className="text-[10px] text-slate-500">
                Authorized Digital Signatory
              </div>
            </div>
          </div>

          {/* Digital Signature Hash */}
          <div className="mt-8 pt-4 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span className="flex items-center gap-1 text-emerald-700 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" /> Cryptographic Integrity
              Verified
            </span>
            <span className="truncate max-w-[280px]">
              HASH: {certificate.digitalSignatureHash}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
