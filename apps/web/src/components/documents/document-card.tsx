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
    <div className="bg-white border border-slate-200 hover:border-yellow-400 rounded-xl p-4 transition-all duration-200 shadow-xs hover:shadow-md flex flex-col justify-between">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <DocumentStatusBadge status={document.status} />
          <ConfidentialityBadge level={document.confidentiality} />
        </div>

        {/* Document Title & Category */}
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 shrink-0 mt-0.5">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-semibold text-slate-900 line-clamp-1 hover:text-yellow-700 transition">
              <Link href={`/app/documents/${document.id}`}>
                {document.name}
              </Link>
            </h4>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 font-medium">
              <span className="text-yellow-700 font-semibold">{document.category}</span>
              <span>•</span>
              <span className="truncate">{document.documentType}</span>
            </div>
          </div>
        </div>

        {/* Metadata Details */}
        <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-500" />
              Owner
            </span>
            <span className="font-semibold text-slate-800 truncate max-w-[160px]">
              {document.ownerName}
              {document.ownerRollNumber && ` (${document.ownerRollNumber})`}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-500">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              Uploaded
            </span>
            <span className="text-slate-700">
              {new Date(document.uploadedAt).toLocaleDateString()}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-500">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Expiry
            </span>
            <ExpiryStatusBadge status={expiryStatus} />
          </div>

          {document.verifiedBy && (
            <div className="flex items-center justify-between text-slate-500">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                Verified By
              </span>
              <span className="text-emerald-700 truncate max-w-[160px] font-semibold">
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
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end">
          <Link
            href={`/app/documents/${document.id}`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-yellow-800 hover:text-yellow-950 transition"
          >
            View 360 Details
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
