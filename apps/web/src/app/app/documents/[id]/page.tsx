"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { documentsService } from "@/services/documents.service";
import { DocumentItem } from "@campusos/types";
import { DocumentStatusBadge, ConfidentialityBadge, ExpiryStatusBadge } from "@/components/documents/document-status-badge";
import { DocumentPreview } from "@/components/documents/document-preview";
import { getDocumentExpiryStatus } from "@/services/document-calculator";
import { Button } from "@/components/ui/button";
import {
  FileText,
  User,
  ShieldCheck,
  Calendar,
  Clock,
  Download,
  Share2,
  ArrowLeft,
  Building,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  History,
  Layers,
  Edit,
  Tag,
} from "lucide-react";

export default function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "verification" | "metadata" | "related" | "activity">("overview");

  useEffect(() => {
    async function loadDoc() {
      try {
        setLoading(true);
        const res = await documentsService.getDocumentById(id);
        if (res.success && res.data) {
          setDocument(res.data);
        } else {
          setDocument(null);
        }
      } catch (err) {
        console.error("Failed to load document:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDoc();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading document details...
      </div>
    );
  }

  if (!document) {
    notFound();
  }

  const expiryStatus = getDocumentExpiryStatus(document.expiryDate);

  return (
    <div className="space-y-6 pb-16">
      {/* Back Navigation Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/all"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Documents Directory
        </Link>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="text-xs h-7 gap-1"
            onClick={() => alert(`Document metadata download started for ${document.id}`)}
          >
            <Download className="w-3.5 h-3.5" />
            Download File
          </Button>
          <Link href={`/app/documents/verification/${document.id}`}>
            <Button size="sm" className="text-xs h-7 gap-1 bg-blue-600 hover:bg-blue-700">
              <ShieldCheck className="w-3.5 h-3.5" />
              Verification Desk
            </Button>
          </Link>
        </div>
      </div>

      {/* Hero 360 Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-xl shrink-0 mt-1">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <DocumentStatusBadge status={document.status} />
                <ConfidentialityBadge level={document.confidentiality} />
                <span className="text-xs font-mono text-slate-500">ID: {document.id}</span>
              </div>
              <h1 className="text-xl md:text-2xl font-bold text-slate-100">{document.name}</h1>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-2 font-medium">
                <span className="text-blue-400">{document.category}</span>
                <span>•</span>
                <span>{document.documentType}</span>
                <span>•</span>
                <span>{document.fileSize} ({document.fileType})</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-start md:items-end justify-between self-stretch">
            <div className="text-xs text-slate-400">
              Uploaded <strong className="text-slate-200">{new Date(document.uploadedAt).toLocaleDateString()}</strong>
            </div>
            <div className="mt-2">
              <ExpiryStatusBadge status={expiryStatus} />
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800 text-xs">
          {[
            { id: "overview", label: "Overview & Preview" },
            { id: "verification", label: "Verification Status" },
            { id: "metadata", label: "Metadata & Details" },
            { id: "related", label: "Related Records" },
            { id: "activity", label: `Activity History (${document.activityTimeline.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* TAB 1: OVERVIEW & DOCUMENT PREVIEW */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <DocumentPreview document={document} />
          </div>

          <div className="space-y-6">
            {/* Quick Owner Profile Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-blue-400" />
                Document Owner
              </h3>
              <div className="space-y-2 text-xs">
                <div className="font-semibold text-slate-200 text-sm">{document.ownerName}</div>
                {document.ownerRollNumber && (
                  <div className="font-mono text-slate-400">ID / Roll No: {document.ownerRollNumber}</div>
                )}
                <div className="text-slate-400">Cadre: {document.ownerType}</div>
                {document.ownerDepartment && (
                  <div className="text-slate-400">Department: {document.ownerDepartment}</div>
                )}
                {document.program && (
                  <div className="text-slate-400">Program: {document.program}</div>
                )}
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-2">
                Document Governance
              </h3>
              <Link href={`/app/documents/verification/${document.id}`} className="block">
                <Button className="w-full text-xs bg-blue-600 hover:bg-blue-700 gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  Perform Verification
                </Button>
              </Link>
              <Button
                variant="outline"
                className="w-full text-xs gap-1.5"
                onClick={() => alert(`Simulated document re-upload request dispatched to ${document.ownerName}.`)}
              >
                <AlertCircle className="w-4 h-4 text-amber-400" />
                Request Replacement Scan
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: VERIFICATION */}
      {activeTab === "verification" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Institutional Verification Standing
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Compliance checks, reviewer endorsements, and state verification status.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">Status</span>
              <div className="mt-1">
                <DocumentStatusBadge status={document.status} />
              </div>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">Verified By</span>
              <span className="font-semibold text-slate-200 text-xs mt-1 block">
                {document.verifiedBy || "Not yet verified"}
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">Verified Timestamp</span>
              <span className="text-slate-300 text-xs mt-1 block">
                {document.verifiedAt ? new Date(document.verifiedAt).toLocaleString() : "Pending review"}
              </span>
            </div>
          </div>

          {document.rejectionReason && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs space-y-1">
              <div className="font-bold text-rose-400 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" />
                Official Rejection Reason
              </div>
              <p className="text-rose-300">{document.rejectionReason}</p>
            </div>
          )}

          {/* Verification Checklist */}
          {document.verificationChecklist && (
            <div className="space-y-3 pt-4 border-t border-slate-800">
              <h4 className="text-xs uppercase font-bold tracking-wider text-slate-300">
                Institutional Verification Checklist
              </h4>
              <div className="space-y-2">
                {document.verificationChecklist.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2.5">
                      {item.checked ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />
                      )}
                      <span className="text-slate-200">{item.label}</span>
                    </div>
                    <span className="text-[10px] font-bold uppercase text-slate-500">
                      {item.required ? "Mandatory" : "Optional"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: METADATA */}
      {activeTab === "metadata" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Tag className="w-5 h-5 text-blue-400" />
            Document Metadata & Issuing Details
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">Official Document Number</span>
              <span className="font-mono font-semibold text-slate-200 text-sm mt-1 block">
                {document.documentNumber || "Not Specified"}
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">Issuing Authority</span>
              <span className="font-semibold text-slate-200 text-sm mt-1 block">
                {document.issuingAuthority || "Not Specified"}
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">Issue Date</span>
              <span className="text-slate-200 text-sm mt-1 block">{document.issueDate || "N/A"}</span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">Expiry Date</span>
              <span className="text-slate-200 text-sm mt-1 block">
                {document.expiryDate || "Permanent / No Expiry"}
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">File Type & Size</span>
              <span className="text-slate-200 text-sm mt-1 block">
                {document.fileType} ({document.fileSize})
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block text-[10px] uppercase">Storage Location (Mock)</span>
              <span className="font-mono text-slate-400 text-xs mt-1 block truncate">
                /vault/secure/{document.ownerId}/{document.id}.pdf
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: RELATED RECORDS */}
      {activeTab === "related" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Building className="w-5 h-5 text-indigo-400" />
            Cross-Module Related Institutional Entities
          </h3>
          <p className="text-xs text-slate-400">
            Linked entities across Student 360, Academics, Placement, Finance, Hostel, and Transport.
          </p>

          {document.relatedRecord ? (
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400">
                  {document.relatedRecord.entityType} LINK
                </span>
                <div className="font-semibold text-slate-200 text-sm mt-0.5">
                  {document.relatedRecord.label}
                </div>
                <div className="text-xs font-mono text-slate-500 mt-0.5">
                  Entity ID: {document.relatedRecord.entityId}
                </div>
              </div>

              <Link
                href={
                  document.relatedRecord.entityType === "STUDENT"
                    ? `/app/students/${document.relatedRecord.entityId}`
                    : document.relatedRecord.entityType === "PLACEMENT"
                    ? `/app/placement`
                    : document.relatedRecord.entityType === "FINANCE"
                    ? `/app/finance`
                    : document.relatedRecord.entityType === "HOSTEL"
                    ? `/app/infrastructure/hostel`
                    : document.relatedRecord.entityType === "TRANSPORT"
                    ? `/app/infrastructure/transport`
                    : `/app/dashboard`
                }
              >
                <Button size="sm" variant="outline" className="text-xs gap-1.5">
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open Entity 360
                </Button>
              </Link>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No direct external module relationships configured for this file.
            </div>
          )}
        </div>
      )}

      {/* TAB 5: ACTIVITY TIMELINE */}
      {activeTab === "activity" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <History className="w-5 h-5 text-amber-400" />
            Document Lifecycle & Audit Timeline
          </h3>
          <p className="text-xs text-slate-400">
            Immutable governance ledger tracking submissions, verification states, and reviewer actions.
          </p>

          <div className="relative border-l-2 border-slate-800 ml-4 space-y-6 pt-2">
            {document.activityTimeline.map((item, idx) => (
              <div key={item.id} className="relative pl-6">
                {/* Dot */}
                <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center" />

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-200">{item.action}</span>
                    <span className="text-slate-500 font-mono text-[10px]">
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">{item.description}</p>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-2 font-medium">
                    <span>By: {item.performedBy}</span>
                    {item.role && (
                      <>
                        <span>•</span>
                        <span className="text-blue-400">{item.role}</span>
                      </>
                    )}
                  </div>
                  {item.notes && (
                    <div className="mt-2 p-2 bg-slate-900 rounded text-[11px] text-slate-300 italic border border-slate-800">
                      "{item.notes}"
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
