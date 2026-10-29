"use client";

import React from "react";
import Link from "next/link";
import { DocumentItem } from "@campusos/types";
import {
  DocumentStatusBadge,
  ConfidentialityBadge,
} from "./document-status-badge";
import {
  FileText,
  Calendar,
  User,
  ShieldCheck,
  ChevronRight,
  Clock,
  AlertCircle,
} from "lucide-react";
import { getDocumentExpiryStatus } from "@/services/document-calculator";
import { ExpiryStatusBadge } from "./document-status-badge";

interface DocumentCardProps {
  document: DocumentItem;
  showActions?: boolean;
}

export function DocumentCard({
  document,
  showActions = true,
}: DocumentCardProps) {
  const expiryStatus = getDocumentExpiryStatus(document.expiryDate);

  return (
    <div className="bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition-all duration-200 shadow-sm hover:shadow-md flex flex-col justify-between">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <DocumentStatusBadge status={document.status} />
          <ConfidentialityBadge level={document.confidentiality} />
        </div>

        {/* Document Title & Category */}
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0 mt-0.5">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-semibold text-slate-100 line-clamp-1 hover:text-blue-400 transition">
              <Link href={`/app/documents/${document.id}`}>
                {document.name}
              </Link>
            </h4>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 font-medium">
              <span className="text-blue-400">{document.category}</span>
              <span>•</span>
              <span className="truncate">{document.documentType}</span>
            </div>
          </div>
        </div>

        {/* Metadata Details */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-500" />
              Owner
            </span>
            <span className="font-medium text-slate-200 truncate max-w-[160px]">
              {document.ownerName}
              {document.ownerRollNumber && ` (${document.ownerRollNumber})`}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              Uploaded
            </span>
            <span className="text-slate-300">
              {new Date(document.uploadedAt).toLocaleDateString()}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Expiry
            </span>
            <ExpiryStatusBadge status={expiryStatus} />
          </div>

          {document.verifiedBy && (
            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                Verified By
              </span>
              <span className="text-emerald-400 truncate max-w-[160px] font-medium">
                {document.verifiedBy.split(" ")[0]}{" "}
                {document.verifiedBy.split(" ")[1] || ""}
              </span>
            </div>
          )}

          {document.rejectionReason && (
            <div className="p-2 bg-rose-500/10 border border-rose-500/20 rounded text-[11px] text-rose-300 flex items-start gap-1.5 mt-2">
              <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
              <span className="line-clamp-2">{document.rejectionReason}</span>
            </div>
          )}
        </div>
      </div>

      {showActions && (
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-end">
          <Link
            href={`/app/documents/${document.id}`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300 transition"
          >
            View 360 Details
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
