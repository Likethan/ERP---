"use client";

import React, { useState } from "react";
import { DocumentItem } from "@campusos/types";
import {
  DocumentStatusBadge,
  ConfidentialityBadge,
} from "./document-status-badge";
import {
  FileText,
  Download,
  Printer,
  Maximize2,
  Minimize2,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Building,
  Calendar,
  Hash,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentPreviewProps {
  document: DocumentItem;
  className?: string;
  showToolbar?: boolean;
}

export function DocumentPreview({
  document,
  className = "",
  showToolbar = true,
}: DocumentPreviewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div
      className={`flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl transition-all ${
        isFullscreen
          ? "fixed inset-4 z-50 bg-slate-950/95 backdrop-blur-xl border-slate-700"
          : className
      }`}
    >
      {/* Top Preview Control Header */}
      {showToolbar && (
        <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-1.5 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h4 className="text-xs font-semibold text-slate-200 truncate">
                {document.name}
              </h4>
              <p className="text-[10px] text-slate-400">
                {document.fileType} • {document.fileSize} • Uploaded{" "}
                {new Date(document.uploadedAt).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <span className="hidden sm:inline-block">
              <ConfidentialityBadge level={document.confidentiality} />
            </span>
            <button
              onClick={() => setZoomLevel((z) => Math.max(75, z - 15))}
              className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title="Zoom Out"
            >
              -
            </button>
            <span className="text-[11px] font-mono text-slate-400 px-1">
              {zoomLevel}%
            </span>
            <button
              onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
              className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title="Zoom In"
            >
              +
            </button>

            <button
              onClick={toggleFullscreen}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
            <a
              href="#mock-download"
              onClick={(e) => {
                e.preventDefault();
                alert(`Mock Download: ${document.name} (${document.fileSize})`);
              }}
              className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded transition"
              title="Download File"
            >
              <Download className="w-4 h-4" />
            </a>
          </div>
        </div>
      )}

      {/* Realistic Document Render Surface */}
      <div className="relative flex-1 p-6 md:p-8 bg-slate-950/50 flex items-center justify-center overflow-auto min-h-[460px]">
        {/* Document Sheet Simulation */}
        <div
          style={{
            transform: `scale(${zoomLevel / 100})`,
            transformOrigin: "top center",
          }}
          className="w-full max-w-[580px] bg-slate-900 border border-slate-700/60 rounded-lg p-8 shadow-2xl relative transition-transform duration-150 select-none text-slate-100"
        >
          {/* Mock Institutional Seal / Watermark Background */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-5">
            <Building className="w-80 h-80 text-white" />
          </div>

          {/* Institutional Header */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-5 mb-6">
            <div>
              <div className="text-[10px] uppercase font-bold tracking-widest text-blue-400 mb-0.5">
                CampusOS Digital Document Repository
              </div>
              <h2 className="text-base font-bold text-slate-100">
                {document.issuingAuthority ||
                  "Academic & Institutional Registry"}
              </h2>
              <p className="text-xs text-slate-400">
                Official Authenticated Record
              </p>
            </div>
            <div className="text-right">
              <DocumentStatusBadge status={document.status} />
              <div className="text-[10px] font-mono text-slate-500 mt-1.5">
                DOC ID: {document.id}
              </div>
            </div>
          </div>

          {/* Document Core Content Representation */}
          <div className="space-y-4 my-6">
            <div className="p-4 bg-slate-950/70 border border-slate-800/80 rounded-lg">
              <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-1">
                Document Title
              </div>
              <div className="text-sm font-semibold text-slate-100">
                {document.name}
              </div>
              <div className="text-xs text-blue-400 mt-1 font-mono">
                Category: {document.category} • Classification:{" "}
                {document.documentType}
              </div>
            </div>

            {/* Grid of Verified Fields */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Legal Owner
                </span>
                <span className="font-medium text-slate-200 mt-0.5 block">
                  {document.ownerName}
                </span>
                {document.ownerRollNumber && (
                  <span className="text-[11px] text-slate-400 font-mono">
                    ID: {document.ownerRollNumber}
                  </span>
                )}
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Department / Cadre
                </span>
                <span className="font-medium text-slate-200 mt-0.5 block">
                  {document.ownerDepartment || "General"}
                </span>
                <span className="text-[11px] text-slate-400">
                  {document.ownerType}
                </span>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Document Number
                </span>
                <span className="font-medium text-slate-200 mt-0.5 block font-mono">
                  {document.documentNumber ||
                    "CAMPUS-REC-00" + document.id.slice(-4)}
                </span>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Issue Date
                </span>
                <span className="font-medium text-slate-200 mt-0.5 block">
                  {document.issueDate || "N/A"}
                </span>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Expiry Date
                </span>
                <span className="font-medium text-slate-200 mt-0.5 block">
                  {document.expiryDate ? (
                    <span className="text-amber-400">
                      {document.expiryDate}
                    </span>
                  ) : (
                    <span className="text-slate-400">Permanent Validity</span>
                  )}
                </span>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded">
                <span className="text-slate-400 block text-[10px] uppercase">
                  Verification Status
                </span>
                <span className="font-medium mt-0.5 block text-slate-300">
                  {document.verifiedBy ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Verified
                    </span>
                  ) : (
                    <span className="text-amber-400">
                      Awaiting Verification
                    </span>
                  )}
                </span>
              </div>
            </div>

            {/* Checklist summary if available */}
            {document.verificationChecklist &&
              document.verificationChecklist.length > 0 && (
                <div className="mt-3 p-3 bg-slate-950/40 border border-slate-800/60 rounded text-xs space-y-1.5">
                  <div className="text-[10px] uppercase font-semibold text-slate-400 mb-1">
                    Verification Checklist Snapshot
                  </div>
                  {document.verificationChecklist.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center gap-2 text-slate-300 text-[11px]"
                    >
                      {item.checked ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-slate-600 shrink-0" />
                      )}
                      <span className="truncate">{item.label}</span>
                    </div>
                  ))}
                </div>
              )}
          </div>

          {/* Security & Verification Footer */}
          <div className="border-t border-slate-800/80 pt-4 mt-6 flex items-center justify-between text-[10px] text-slate-400">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>CampusOS Institutional Digital Vault</span>
            </div>
            <div className="font-mono text-slate-400">
              HASH: 0x{document.id.padEnd(16, "f0a1")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
