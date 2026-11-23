"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentCategoriesService } from "@/services/document-categories.service";
import { DocumentCategory } from "@campusos/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Layers,
  Search,
  Plus,
  ShieldCheck,
  Clock,
  ArrowRight,
  CheckCircle2,
  Users,
  FileText,
} from "lucide-react";

export default function DocumentCategoriesPage() {
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function loadCategories() {
      try {
        setLoading(true);
        const res = await documentCategoriesService.listCategories();
        if (res.success && res.data) {
          setCategories(res.data);
        }
      } catch (err) {
        console.error("Failed to load categories:", err);
      } finally {
        setLoading(false);
      }
    }

    loadCategories();
  }, []);

  const filteredCategories = categories.filter((cat) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        cat.name.toLowerCase().includes(q) ||
        cat.code.toLowerCase().includes(q) ||
        cat.description.toLowerCase().includes(q)
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
            <Layers className="w-3.5 h-3.5" />
            <span>Document Taxonomy & Classification</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Document Categories
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Institutional categories, role applicability, mandatory verification
            constraints, and expiry rules.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
            onClick={() => alert("Category configuration modal")}
          >
            <Plus className="w-4 h-4" />
            Add Category
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by category name or code..."
          className="pl-9 bg-slate-900 border-slate-800 text-xs"
        />
      </div>

      {/* Grid of Categories */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500">
          Loading document categories...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCategories.map((cat) => (
            <div
              key={cat.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-mono text-[11px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                    {cat.code}
                  </span>
                  {cat.required ? (
                    <span className="text-[10px] font-bold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
                      Mandatory
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                      Optional
                    </span>
                  )}
                </div>

                <h3 className="text-base font-semibold text-slate-100 hover:text-blue-400 transition">
                  <Link href={`/app/documents/categories/${cat.id}`}>
                    {cat.name}
                  </Link>
                </h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  {cat.description}
                </p>

                {/* Applicable Roles */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                    <span>Applicable Roles:</span>
                    <span className="text-slate-200 font-medium">
                      {cat.applicableRoles.join(", ")}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 text-slate-400">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    <span>Types:</span>
                    <span className="text-slate-300 truncate">
                      {cat.applicableDocumentTypes.length} configured
                    </span>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      Verification:{" "}
                      {cat.verificationRequired ? "Required" : "Exempt"}
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                      Expiry: {cat.expiryRequired ? "Monitored" : "None"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  {cat.totalDocuments || 0} registered records
                </span>
                <Link
                  href={`/app/documents/categories/${cat.id}`}
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
