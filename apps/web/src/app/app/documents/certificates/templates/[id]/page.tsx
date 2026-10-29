"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { certificateTemplatesService } from "@/services/certificate-templates.service";
import {
  CertificateTemplate,
  CertificateTemplateStatus,
} from "@campusos/types";
import { Button } from "@/components/ui/button";
import {
  Layers,
  ArrowLeft,
  FileText,
  Clock,
  History,
  TrendingUp,
  Plus,
  Users,
  CheckCircle2,
  Code,
  Tag,
} from "lucide-react";

export default function CertificateTemplateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [template, setTemplate] = useState<CertificateTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "fields" | "versions" | "usage" | "activity"
  >("overview");

  useEffect(() => {
    async function loadTemplate() {
      try {
        setLoading(true);
        const res = await certificateTemplatesService.getTemplateById(id);
        if (res.success && res.data) {
          setTemplate(res.data);
        } else {
          setTemplate(null);
        }
      } catch (err) {
        console.error("Failed to load certificate template:", err);
      } finally {
        setLoading(false);
      }
    }

    loadTemplate();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading certificate template...
      </div>
    );
  }

  if (!template) {
    notFound();
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/documents/certificates/templates"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Templates Directory
        </Link>
        <span className="font-mono text-xs text-amber-400 font-bold bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/20">
          TYPE: {template.certificateType}
        </span>
      </div>

      {/* Hero */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {template.status}
              </span>
              <span className="font-mono text-xs text-blue-400 font-semibold">
                Version {template.version}
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-100">
              {template.templateName}
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              {template.description}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="text-xs"
              onClick={() =>
                alert(`Previewing layout for ${template.templateName}`)
              }
            >
              Test Preview
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800 text-xs">
          {[
            { id: "overview", label: "Overview" },
            {
              id: "fields",
              label: `Template Fields (${template.fields.length})`,
            },
            {
              id: "versions",
              label: `Version History (${template.versionHistory.length})`,
            },
            { id: "usage", label: "Usage Statistics" },
            { id: "activity", label: "Activity Audit" },
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
            Template Profile & Audience Policy
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Certificate Type
              </span>
              <span className="font-semibold text-slate-200 text-sm mt-1 block">
                {template.certificateType}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Applicable Audience
              </span>
              <span className="font-semibold text-blue-400 text-sm mt-1 block">
                {template.applicableAudience.join(", ")}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Created Date
              </span>
              <span className="text-slate-200 text-sm mt-1 block">
                {template.createdDate}
              </span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                Last Revision Date
              </span>
              <span className="text-slate-200 text-sm mt-1 block">
                {template.lastUpdated}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TEMPLATE FIELDS */}
      {activeTab === "fields" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Dynamic Variable Mapping
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Fields mapped from CampusOS student registry or user input
                during generation.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="text-xs gap-1"
              onClick={() => alert("Add field dialog")}
            >
              <Plus className="w-3.5 h-3.5" />
              Add Field
            </Button>
          </div>

          <div className="space-y-2.5 pt-2">
            {template.fields.map((field) => (
              <div
                key={field.id}
                className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">
                      {field.label}
                    </span>
                    <span className="font-mono text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">
                      {field.name}
                    </span>
                    {field.required && (
                      <span className="text-[10px] text-amber-400 font-bold">
                        * Required
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    Type: {field.type}{" "}
                    {field.systemVariableMapping &&
                      `→ Source: ${field.systemVariableMapping}`}
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-slate-400 text-[11px]">
                    Default: {field.defaultValue || "Auto-bound"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: VERSIONS */}
      {activeTab === "versions" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            Template Revisions & Version Control
          </h3>

          <div className="space-y-3">
            {template.versionHistory.map((ver) => (
              <div
                key={ver.version}
                className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-blue-400 text-sm">
                    v{ver.version}
                  </span>
                  <span className="text-slate-500 font-mono text-[10px]">
                    {new Date(ver.publishedAt).toLocaleString()}
                  </span>
                </div>
                <div className="text-slate-400">
                  Published by {ver.publishedBy}
                </div>
                <div className="p-2.5 bg-slate-900 rounded text-slate-300 font-mono text-[11px]">
                  {ver.changelog}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: USAGE */}
      {activeTab === "usage" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Issuance & Lifecycle Utilization
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-3xl font-bold text-slate-100">
                {template.usageCount}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Total Certificates Generated
              </div>
            </div>
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-3xl font-bold text-emerald-400">100%</div>
              <div className="text-xs text-slate-400 mt-1">
                Template Validation Compliance
              </div>
            </div>
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-3xl font-bold text-blue-400">0.4s</div>
              <div className="text-xs text-slate-400 mt-1">
                Average Digital Generation Speed
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ACTIVITY */}
      {activeTab === "activity" && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" />
            Template Governance Ledger
          </h3>

          <div className="space-y-3">
            {template.activity.map((item) => (
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
                {item.notes && (
                  <div className="text-slate-300 italic pt-1">{item.notes}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
