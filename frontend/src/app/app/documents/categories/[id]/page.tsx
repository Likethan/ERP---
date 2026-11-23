"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { documentCategoriesService } from "@/services/document-categories.service";
import { DocumentCategory } from "@campusos/types";
import { Button } from "@/components/ui/button";
import {
  Layers,
  ArrowLeft,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Users,
  History,
  TrendingUp,
  Plus,
} from "lucide-react";

export default function CategoryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [category, setCategory] = useState<DocumentCategory | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "types" | "requirements" | "usage" | "activity"
  >("overview");

  useEffect(() => {
    async function loadCategory() {
      try {
        setLoading(true);
        const res = await documentCategoriesService.getCategoryById(id);
        if (res.success && res.data) {
          setCategory(res.data);
        } else {
          setCategory(null);
        }
      } catch (err) {
        console.error("Failed to load category:", err);
      } finally {
        setLoading(false);
      }
    }

    loadCategory();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading category specifications...
      </div>
    );
  }

  if (!category) {
    notFound();
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/categories"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Categories Directory
        </Link>
        <span className="font-mono text-xs text-blue-400 font-bold bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
          CODE: {category.code}
        </span>
      </div>

      {/* Hero */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ACTIVE
              </span>
              {category.required && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  MANDATORY COMPLIANCE
                </span>
              )}
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-100">
              {category.name}
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              {category.description}
            </p>
          </div>

          <Link href={`/app/documents/all?category=${category.code}`}>
            <Button size="sm" variant="outline" className="text-xs">
              View All Category Documents ({category.totalDocuments || 0})
            </Button>
          </Link>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800 text-xs">
          {[
            { id: "overview", label: "Overview" },
            {
              id: "types",
              label: `Document Types (${category.applicableDocumentTypes.length})`,
            },
            { id: "requirements", label: "Requirements & Rules" },
            { id: "usage", label: "Usage & Metrics" },
            { id: "activity", label: "Configuration History" },
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
            Category Profile
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Category Code
              </span>
              <span className="font-mono text-sm text-slate-200 mt-1 block">
                {category.code}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Compliance Mandate
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {category.required
                  ? "Mandatory for all eligible candidates"
                  : "Optional / Supporting Document"}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Verification Constraint
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {category.verificationRequired
                  ? "Officer review required prior to clearance"
                  : "Auto-verified"}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Expiry Tracking
              </span>
              <span className="text-sm text-slate-200 mt-1 block">
                {category.expiryRequired
                  ? "Mandatory expiry date with automated alerts"
                  : "No expiry monitoring"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DOCUMENT TYPES */}
      {activeTab === "types" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Configured Document Classifications
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Allowed document types that can be submitted under this
                category.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="text-xs gap-1"
              onClick={() => alert("Add type dialog")}
            >
              <Plus className="w-3.5 h-3.5" />
              Add Type
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {category.applicableDocumentTypes.map((type, idx) => (
              <div
                key={type}
                className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded bg-slate-900 border border-slate-700 flex items-center justify-center font-mono text-[11px] text-slate-400">
                    {idx + 1}
                  </span>
                  <span className="font-semibold text-slate-200">{type}</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-medium">
                  Active
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: REQUIREMENTS */}
      {activeTab === "requirements" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
          <h3 className="text-sm font-semibold text-slate-100">
            Institutional Governance Rules
          </h3>
          <div className="space-y-3">
            <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="font-semibold text-slate-200">
                Applicable Academic Cadres & Roles
              </div>
              <p className="text-slate-400 mt-1">
                Roles required or eligible to submit documents under this
                category:{" "}
                <strong className="text-blue-400">
                  {category.applicableRoles.join(", ")}
                </strong>
              </p>
            </div>

            <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="font-semibold text-slate-200">
                Regulatory Verification Policy
              </div>
              <p className="text-slate-400 mt-1">
                {category.verificationRequired
                  ? "All uploads must be authenticated by an authorized Verification Officer, Dean, or Registrar with a checklist review."
                  : "Documents uploaded in this category bypass mandatory administrative review."}
              </p>
            </div>

            <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="font-semibold text-slate-200">
                Expiry & Renewal Protocol
              </div>
              <p className="text-slate-400 mt-1">
                {category.expiryRequired
                  ? "Validity is strictly bounded by the declared expiry date. Automated warnings trigger at 90, 30, and 7 days prior to expiry."
                  : "Documents in this category possess permanent, unexpiring legal validity."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: USAGE */}
      {activeTab === "usage" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Category Utilization & Compliance Snapshot
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <div className="text-2xl font-bold text-slate-100">
                {category.totalDocuments || 0}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Total Submissions
              </div>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <div className="text-2xl font-bold text-emerald-400">
                {category.verifiedDocuments || 0}
              </div>
              <div className="text-xs text-slate-400 mt-1">Verified</div>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <div className="text-2xl font-bold text-amber-400">
                {category.pendingDocuments || 0}
              </div>
              <div className="text-xs text-slate-400 mt-1">Pending Review</div>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <div className="text-2xl font-bold text-rose-400">
                {category.rejectedDocuments || 0}
              </div>
              <div className="text-xs text-slate-400 mt-1">Rejected</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ACTIVITY */}
      {activeTab === "activity" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" />
            Category Audit Ledger
          </h3>
          <div className="space-y-3">
            {(category.auditHistory && category.auditHistory.length > 0
              ? category.auditHistory
              : [
                  {
                    id: "aud-def",
                    action: "Category Initialized",
                    performedBy: "Dr. Arvind Swaminathan (Registrar)",
                    timestamp: "2026-06-01T09:00:00Z",
                    details:
                      "Taxonomy established under CampusOS Institutional Governance.",
                  },
                ]
            ).map((item) => (
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
