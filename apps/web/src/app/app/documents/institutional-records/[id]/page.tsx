"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { institutionalRecordsService } from "@/services/institutional-records.service";
import {
  InstitutionalRecord,
  InstitutionalRecordStatus,
} from "@campusos/types";
import { ConfidentialityBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import {
  Building,
  ArrowLeft,
  FileText,
  Clock,
  History,
  Download,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Lock,
  ExternalLink,
} from "lucide-react";

export default function InstitutionalRecordDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [record, setRecord] = useState<InstitutionalRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "metadata"
    | "department"
    | "validity"
    | "documents"
    | "activity"
  >("overview");

  useEffect(() => {
    async function loadRecord() {
      try {
        setLoading(true);
        const res = await institutionalRecordsService.getRecordById(id);
        if (res.success && res.data) {
          setRecord(res.data);
        } else {
          setRecord(null);
        }
      } catch (err) {
        console.error("Failed to load institutional record:", err);
      } finally {
        setLoading(false);
      }
    }

    loadRecord();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading institutional record...
      </div>
    );
  }

  if (!record) {
    notFound();
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/institutional-records"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Institutional Register
        </Link>
        <span className="font-mono text-xs text-blue-400 font-bold bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
          CODE: {record.code}
        </span>
      </div>

      {/* Hero */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {record.status}
              </span>
              <ConfidentialityBadge level={record.confidentiality} />
              <span className="text-xs text-slate-400">
                • {record.category}
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-100">
              {record.recordName}
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              {record.description}
            </p>
          </div>

          <Button
            size="sm"
            variant="outline"
            className="text-xs gap-1"
            onClick={() =>
              alert(`Downloading gazette copy of ${record.recordName}`)
            }
          >
            <Download className="w-3.5 h-3.5" />
            Download Gazette PDF
          </Button>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800 text-xs">
          {[
            { id: "overview", label: "Overview" },
            { id: "metadata", label: "Statutory Metadata" },
            { id: "department", label: "Department Ownership" },
            { id: "validity", label: "Validity & Compliance" },
            {
              id: "documents",
              label: `Related Files (${record.relatedDocuments?.length || 0})`,
            },
            { id: "activity", label: "Gazette Timeline" },
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

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100">
            Executive Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Record Code
              </span>
              <span className="font-mono text-sm text-slate-200 mt-1 block">
                {record.code}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Regulatory Category
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {record.category}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Custodial Department
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {record.ownerDepartment}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Legal Status
              </span>
              <span className="text-sm text-emerald-400 font-semibold mt-1 block">
                {record.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: METADATA */}
      {activeTab === "metadata" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
          <h3 className="text-sm font-semibold text-slate-100">
            Statutory & Regulatory Particulars
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Issuing Authority
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {record.issuingAuthority || "N/A"}
              </span>
            </div>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Official Reference Number
              </span>
              <span className="font-mono text-sm text-blue-400 mt-1 block">
                {record.referenceNumber || "N/A"}
              </span>
            </div>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Promulgation Date
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {record.createdDate}
              </span>
            </div>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Statutory Validity
              </span>
              <span className="text-sm text-amber-400 mt-1 block">
                {record.validUntil
                  ? `Valid through ${record.validUntil}`
                  : "Permanent Institutional Policy"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DEPARTMENT */}
      {activeTab === "department" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
          <h3 className="text-sm font-semibold text-slate-100">
            Institutional Custody
          </h3>
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <div>
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Primary Department
              </span>
              <div className="font-semibold text-sm text-slate-200 mt-0.5">
                {record.ownerDepartment}
              </div>
            </div>
            <p className="text-slate-400">
              Responsible for compliance enforcement, audit representation,
              periodic re-accreditation filings, and council updates.
            </p>
          </div>
        </div>
      )}

      {/* TAB 4: VALIDITY */}
      {activeTab === "validity" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
          <h3 className="text-sm font-semibold text-slate-100">
            Validity & Audit Radar
          </h3>
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <span className="font-semibold text-slate-200 text-sm">
                  Active Statutory Compliance Confirmed
                </span>
                <div className="text-slate-400 mt-0.5">
                  Effective from {record.createdDate}{" "}
                  {record.validUntil && `until ${record.validUntil}`}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: RELATED DOCUMENTS */}
      {activeTab === "documents" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100">
            Associated Official Documents & Attachments
          </h3>
          {record.relatedDocuments && record.relatedDocuments.length > 0 ? (
            <div className="space-y-2.5">
              {record.relatedDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-blue-400" />
                    <div>
                      <span className="font-semibold text-slate-200">
                        {doc.name}
                      </span>
                      <span className="text-[11px] text-slate-500 ml-2">
                        {doc.fileType} • {doc.fileSize}
                      </span>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs h-7 gap-1"
                    onClick={() => alert(`Downloading attachment ${doc.name}`)}
                  >
                    <Download className="w-3 h-3" />
                    Download
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No supplementary attachments filed with this gazette.
            </div>
          )}
        </div>
      )}

      {/* TAB 6: ACTIVITY */}
      {activeTab === "activity" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" />
            Institutional Gazette Ledger
          </h3>

          <div className="space-y-3">
            {record.activity.map((item) => (
              <div
                key={item.id}
                className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">
                    {item.action}
                  </span>
                  <span className="text-slate-500 font-mono text-[10px]">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="text-slate-400">By {item.performedBy}</div>
                {item.details && (
                  <div className="text-slate-300 italic pt-1">
                    {item.details}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
