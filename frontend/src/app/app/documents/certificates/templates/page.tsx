"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { certificateTemplatesService } from "@/services/certificate-templates.service";
import {
  CertificateTemplate,
  CertificateType,
  CertificateTemplateStatus,
} from "@campusos/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Layers,
  Search,
  Plus,
  ArrowLeft,
  ArrowRight,
  FileText,
  Clock,
  CheckCircle2,
  Users,
} from "lucide-react";

export default function CertificateTemplatesPage() {
  const [templates, setTemplates] = useState<CertificateTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  useEffect(() => {
    async function loadTemplates() {
      try {
        setLoading(true);
        const res = await certificateTemplatesService.listTemplates();
        if (res.success && res.data) {
          setTemplates(res.data);
        }
      } catch (err) {
        console.error("Failed to load templates:", err);
      } finally {
        setLoading(false);
      }
    }

    loadTemplates();
  }, []);

  const filteredTemplates = templates.filter((tmpl) => {
    if (typeFilter !== "ALL" && tmpl.certificateType !== typeFilter)
      return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        tmpl.templateName.toLowerCase().includes(q) ||
        tmpl.certificateType.toLowerCase().includes(q) ||
        tmpl.description.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <Link
              href="/app/documents/certificates"
              className="hover:underline flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Certificate Center
            </Link>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Certificate Templates
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Standardized institutional certificate formats, custom fields,
            version control, and audience policies.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
            onClick={() => alert("Create template configuration dialog")}
          >
            <Plus className="w-4 h-4" />
            Create Template
          </Button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates by name, type, or description..."
            className="pl-9 bg-slate-900 border-slate-800 text-xs"
          />
        </div>

        <div>
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-900 border-slate-800 text-xs"
          >
            <option value="ALL">All Certificate Types</option>
            {Object.values(CertificateType).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Grid of Templates */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500">
          Loading templates catalog...
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="py-16 text-center text-xs text-slate-500">
          No templates found matching your criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTemplates.map((tmpl) => (
            <div
              key={tmpl.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-mono text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {tmpl.certificateType}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      tmpl.status === CertificateTemplateStatus.ACTIVE
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {tmpl.status}
                  </span>
                </div>

                <h3 className="text-base font-semibold text-slate-100 hover:text-blue-400 transition">
                  <Link
                    href={`/app/documents/certificates/templates/${tmpl.id}`}
                  >
                    {tmpl.templateName}
                  </Link>
                </h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  {tmpl.description}
                </p>

                <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-slate-500" />
                      Target Audience
                    </span>
                    <span className="text-slate-200 font-medium">
                      {tmpl.applicableAudience.join(", ")}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-slate-500" />
                      Fields
                    </span>
                    <span className="font-mono text-slate-300">
                      {tmpl.fields.length} dynamic variables
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      Version
                    </span>
                    <span className="font-mono text-blue-400 font-semibold">
                      v{tmpl.version}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  {tmpl.usageCount} issuances
                </span>
                <Link
                  href={`/app/documents/certificates/templates/${tmpl.id}`}
                  className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 font-semibold"
                >
                  Configure
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
