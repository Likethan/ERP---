"use client";

import React, { useEffect, useState, useMemo } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  KnowledgeCategoryModel,
  KnowledgeItemModel,
  KnowledgeItemVersionDetailModel,
  KnowledgeGovernanceSummaryModel,
  KnowledgeSearchResultItemModel,
  KnowledgeAttestationComplianceReportModel,
  KnowledgeDraftValidationResultModel,
} from "@campusos/types";
import {
  KnowledgeItemStatus,
  KnowledgeScopeType,
  KnowledgeConfidentiality,
  KnowledgeRelationshipType,
} from "@campusos/types";

export default function KnowledgeBasePolicyPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "library" | "editor" | "review" | "attestations" | "governance"
  >("library");

  // Summary KPIs & Categories
  const [summary, setSummary] = useState<KnowledgeGovernanceSummaryModel | null>(null);
  const [categories, setCategories] = useState<KnowledgeCategoryModel[]>([]);
  const [items, setItems] = useState<KnowledgeItemModel[]>([]);
  const [complianceReports, setComplianceReports] = useState<KnowledgeAttestationComplianceReportModel[]>([]);
  const [scheduledReviews, setScheduledReviews] = useState<any[]>([]);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedScope, setSelectedScope] = useState<string>("ALL");
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResultItemModel[] | null>(null);

  // Active / Selected Item & Version Snapshot Modal
  const [selectedItem, setSelectedItem] = useState<KnowledgeItemModel | null>(null);
  const [selectedVersionDetail, setSelectedVersionDetail] = useState<KnowledgeItemVersionDetailModel | null>(null);
  const [isSnapshotModalOpen, setIsSnapshotModalOpen] = useState(false);

  // Editor State
  const [editorItemId, setEditorItemId] = useState<string | null>(null);
  const [editorItemCode, setEditorItemCode] = useState("");
  const [editorTitle, setEditorTitle] = useState("");
  const [editorSummary, setEditorSummary] = useState("");
  const [editorCategoryCode, setEditorCategoryCode] = useState("ACADEMIC_REGULATION");
  const [editorScope, setEditorScope] = useState<KnowledgeScopeType>(KnowledgeScopeType.INSTITUTION);
  const [editorConfidentiality, setEditorConfidentiality] = useState<KnowledgeConfidentiality>(KnowledgeConfidentiality.PUBLIC_INSTITUTION);
  const [editorVisibilityRole, setEditorVisibilityRole] = useState("");
  const [editorContentMarkdown, setEditorContentMarkdown] = useState("");
  const [editorTags, setEditorTags] = useState("");
  const [editorLockVersion, setEditorLockVersion] = useState(1);
  const [editorEffectiveFrom, setEditorEffectiveFrom] = useState("");
  const [editorReviewByDate, setEditorReviewByDate] = useState("");
  const [editorRequiresAcknowledgement, setEditorRequiresAcknowledgement] = useState(false);
  const [editorChangeSummary, setEditorChangeSummary] = useState("");
  const [draftValidation, setDraftValidation] = useState<KnowledgeDraftValidationResultModel | null>(null);

  // Review & Publishing Action Modals
  const [reviewActionItem, setReviewActionItem] = useState<KnowledgeItemModel | null>(null);
  const [reviewDecision, setReviewDecision] = useState<"APPROVED" | "CHANGES_REQUESTED" | "REJECTED">("APPROVED");
  const [reviewComments, setReviewComments] = useState("");
  const [publishActionItem, setPublishActionItem] = useState<KnowledgeItemModel | null>(null);
  const [publishBumpType, setPublishBumpType] = useState<"PATCH" | "MINOR" | "MAJOR">("PATCH");
  const [publishChangeSummary, setPublishChangeSummary] = useState("");

  // Attestation Action Modal
  const [attestModalItem, setAttestModalItem] = useState<KnowledgeItemModel | null>(null);
  const [attestConfirmed, setAttestConfirmed] = useState(false);

  // Relationship Modal
  const [isRelModalOpen, setIsRelModalOpen] = useState(false);
  const [relSourceItemId, setRelSourceItemId] = useState("");
  const [relTargetItemId, setRelTargetItemId] = useState("");
  const [relType, setRelType] = useState<KnowledgeRelationshipType>(KnowledgeRelationshipType.SUPERSEDES);
  const [relDescription, setRelDescription] = useState("");

  // Feedback & Loading States
  const [loading, setLoading] = useState(true);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 1. Load Data
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryRes, catsRes, itemsRes, complianceRes, reviewsRes] = await Promise.all([
        apiFetch<KnowledgeGovernanceSummaryModel>("/api/v1/knowledge/dashboard/summary").catch(() => ({ data: null })),
        apiFetch<KnowledgeCategoryModel[]>("/api/v1/knowledge/categories").catch(() => ({ data: [] })),
        apiFetch<KnowledgeItemModel[]>("/api/v1/knowledge/items?limit=100").catch(() => ({ data: [] })),
        apiFetch<KnowledgeAttestationComplianceReportModel[]>("/api/v1/knowledge/attestations/compliance").catch(() => ({ data: [] })),
        apiFetch<any[]>("/api/v1/knowledge/scheduler/reviews").catch(() => ({ data: [] })),
      ]);

      setSummary(summaryRes.data);
      setCategories(catsRes.data || []);
      setItems(itemsRes.data || []);
      setComplianceReports(complianceRes.data || []);
      setScheduledReviews(reviewsRes.data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load institutional knowledge base data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered Items (Client-side fast filter)
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (selectedCategory !== "ALL" && item.category_code !== selectedCategory) return false;
      if (selectedStatus !== "ALL" && item.status !== selectedStatus) return false;
      if (selectedScope !== "ALL" && item.scope_type !== selectedScope) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesCode = item.item_code?.toLowerCase().includes(q);
        const matchesTitle = item.title?.toLowerCase().includes(q);
        const matchesSummary = item.summary?.toLowerCase().includes(q);
        const matchesTags = item.tags?.some((t) => t.toLowerCase().includes(q));
        if (!matchesCode && !matchesTitle && !matchesSummary && !matchesTags) return false;
      }
      return true;
    });
  }, [items, selectedCategory, selectedStatus, selectedScope, searchQuery]);

  // Review Queue Items (SUBMITTED or IN_REVIEW)
  const reviewQueueItems = useMemo(() => {
    return items.filter((item) => item.status === "SUBMITTED" || item.status === "IN_REVIEW");
  }, [items]);

  // 2. Search API Handler
  const handleServerSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      setLoading(true);
      const res = await apiFetch<any>(`/api/v1/knowledge/search?query=${encodeURIComponent(searchQuery.trim())}`);
      setSearchResults(res.data?.items || []);
    } catch (err: any) {
      setError(err?.message || "Knowledge search query failed.");
    } finally {
      setLoading(false);
    }
  };

  // 3. Clear & Reset Editor Form
  const resetEditor = () => {
    setEditorItemId(null);
    setEditorItemCode(`POL-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`);
    setEditorTitle("");
    setEditorSummary("");
    setEditorCategoryCode(categories[0]?.code || "ACADEMIC_REGULATION");
    setEditorScope(KnowledgeScopeType.INSTITUTION);
    setEditorConfidentiality(KnowledgeConfidentiality.PUBLIC_INSTITUTION);
    setEditorVisibilityRole("");
    setEditorContentMarkdown("# Institutional Policy Specification\n\n## 1. Purpose\nState policy rationale and scope.\n\n## 2. Applicability\nIdentify applicable institutional units and roles.\n\n## 3. Statutory Authority\nReferences to university senate, governing council, or regulatory decrees.");
    setEditorTags("policy, governance, campus");
    setEditorLockVersion(1);
    setEditorEffectiveFrom(new Date().toISOString().split("T")[0]);
    setEditorReviewByDate("");
    setEditorRequiresAcknowledgement(false);
    setEditorChangeSummary("Initial drafting of institutional policy.");
    setDraftValidation(null);
  };

  // 4. Load item into Editor
  const handleLoadItemIntoEditor = (item: KnowledgeItemModel) => {
    setEditorItemId(item.id);
    setEditorItemCode(item.item_code);
    setEditorTitle(item.title);
    setEditorSummary(item.summary || "");
    setEditorCategoryCode(item.category_code);
    setEditorScope(item.scope_type as KnowledgeScopeType);
    setEditorConfidentiality(item.confidentiality as KnowledgeConfidentiality);
    setEditorVisibilityRole(item.visibility_role || "");
    setEditorContentMarkdown(item.draft_content_markdown || "");
    setEditorTags(item.tags?.join(", ") || "");
    setEditorLockVersion(item.lock_version || 1);
    setEditorEffectiveFrom(item.effective_from ? item.effective_from.split("T")[0] : "");
    setEditorReviewByDate(item.review_by_date ? item.review_by_date.split("T")[0] : "");
    setEditorRequiresAcknowledgement(Boolean(item.requires_acknowledgement));
    setEditorChangeSummary("");
    setDraftValidation(null);
    setActiveTab("editor");
  };

  // 5. Validate Draft Content
  const handleValidateDraft = async () => {
    try {
      setError(null);
      const res = await apiFetch<KnowledgeDraftValidationResultModel>("/api/v1/knowledge/items/validate-draft", {
        method: "POST",
        body: JSON.stringify({
          title: editorTitle,
          summary: editorSummary,
          content_markdown: editorContentMarkdown,
        }),
      });
      setDraftValidation(res.data);
      setActionNotice("Draft validated successfully.");
    } catch (err: any) {
      setError(err?.message || "Failed to validate draft.");
    }
  };

  // 6. Save or Update Draft (with optimistic lock protection)
  const handleSaveDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editorTitle.trim() || !editorItemCode.trim()) {
      setError("Please specify item code and title.");
      return;
    }

    try {
      setError(null);
      const parsedTags = editorTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      if (!editorItemId) {
        // Create new Knowledge Item
        const res = await apiFetch<KnowledgeItemModel>("/api/v1/knowledge/items", {
          method: "POST",
          body: JSON.stringify({
            item_code: editorItemCode.trim().toUpperCase(),
            title: editorTitle.trim(),
            summary: editorSummary.trim(),
            category_code: editorCategoryCode,
            scope_type: editorScope,
            visibility_role: editorVisibilityRole ? editorVisibilityRole.trim() : null,
            confidentiality: editorConfidentiality,
            draft_content_markdown: editorContentMarkdown,
            tags: parsedTags,
            effective_from: editorEffectiveFrom ? new Date(editorEffectiveFrom).toISOString() : null,
            review_by_date: editorReviewByDate ? new Date(editorReviewByDate).toISOString() : null,
            requires_acknowledgement: editorRequiresAcknowledgement,
            change_summary: editorChangeSummary || "Initial creation",
          }),
        });

        setActionNotice(`Knowledge item '${res.data?.item_code}' created successfully.`);
        setEditorItemId(res.data?.id || null);
        setEditorLockVersion(res.data?.lock_version || 1);
      } else {
        // Update existing Draft with optimistic lock version
        const res = await apiFetch<KnowledgeItemModel>(`/api/v1/knowledge/items/${editorItemId}/draft`, {
          method: "PUT",
          body: JSON.stringify({
            title: editorTitle.trim(),
            summary: editorSummary.trim(),
            draft_content_markdown: editorContentMarkdown,
            tags: parsedTags,
            lock_version: editorLockVersion,
            change_summary: editorChangeSummary || "Draft content modified",
          }),
        });

        setActionNotice(`Draft '${res.data?.item_code}' updated successfully. (New lock version: ${res.data?.lock_version})`);
        setEditorLockVersion(res.data?.lock_version || editorLockVersion + 1);
      }
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to save draft.");
    }
  };

  // 7. Submit Item for Multi-Stage Review
  const handleSubmitForReview = async (itemId: string) => {
    try {
      setError(null);
      await apiFetch(`/api/v1/knowledge/items/${itemId}/submit-review`, {
        method: "POST",
        body: JSON.stringify({
          submission_notes: "Submitted for formal editorial review and academic governance clearance.",
        }),
      });
      setActionNotice("Item submitted into institutional review workflow.");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to submit item for review.");
    }
  };

  // 8. Submit Review Decision
  const handleReviewDecision = async () => {
    if (!reviewActionItem) return;
    try {
      setError(null);
      await apiFetch(`/api/v1/knowledge/items/${reviewActionItem.id}/review-stage`, {
        method: "POST",
        body: JSON.stringify({
          decision: reviewDecision,
          comments: reviewComments || "Reviewed against university policy governance requirements.",
        }),
      });

      setActionNotice(`Editorial review decision recorded: ${reviewDecision}.`);
      setReviewActionItem(null);
      setReviewComments("");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to submit review decision.");
    }
  };

  // 9. Publish Approved Item
  const handlePublishItem = async () => {
    if (!publishActionItem) return;
    try {
      setError(null);
      const res = await apiFetch<{ version: { version_number: number } }>(
        `/api/v1/knowledge/items/${publishActionItem.id}/publish`,
        {
          method: "POST",
          body: JSON.stringify({
            bump_type: publishBumpType,
            change_summary: publishChangeSummary || "Formally approved and published to university knowledge repository.",
          }),
        }
      );

      setActionNotice(
        `Item published as immutable version snapshot v${res.data?.version?.version_number}.`
      );
      setPublishActionItem(null);
      setPublishChangeSummary("");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to publish item.");
    }
  };

  // 10. Record User Attestation
  const handleRecordAttestation = async () => {
    if (!attestModalItem) return;
    try {
      setError(null);
      await apiFetch(`/api/v1/knowledge/items/${attestModalItem.id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({
          version_number: attestModalItem.current_version_number,
          statement_confirmed: "I confirm that I have read, understood, and agree to abide by the provisions of this institutional document.",
        }),
      });

      setActionNotice(`Attestation recorded for ${attestModalItem.item_code} v${attestModalItem.current_version_number}.`);
      setAttestModalItem(null);
      setAttestConfirmed(false);
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to record attestation.");
    }
  };

  // 11. Create Directed Relationship
  const handleCreateRelationship = async () => {
    if (!relSourceItemId || !relTargetItemId) {
      setError("Please select both source and target knowledge items.");
      return;
    }
    try {
      setError(null);
      await apiFetch("/api/v1/knowledge/relationships", {
        method: "POST",
        body: JSON.stringify({
          source_item_id: relSourceItemId,
          target_item_id: relTargetItemId,
          relationship_type: relType,
          description: relDescription || "Statutory institutional cross-reference",
        }),
      });

      setActionNotice("Directed relationship established with cycle validation check.");
      setIsRelModalOpen(false);
      setRelDescription("");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to establish relationship.");
    }
  };

  // 12. Trigger Background Sweep
  const handleTriggerSweep = async () => {
    try {
      setError(null);
      const res = await apiFetch<any>("/api/v1/knowledge/scheduler/sweep", {
        method: "POST",
        body: JSON.stringify({ run_type: "MANUAL_SWEEP" }),
      });
      setActionNotice(
        `Scheduled review sweep executed. Scanned ${res.data?.items_scanned || 0} items. Overdue flagged: ${res.data?.overdue_flagged || 0}.`
      );
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to trigger scheduled review sweep.");
    }
  };

  // 13. View Immutable Version Detail
  const handleViewVersionSnapshot = async (item: KnowledgeItemModel, versionNum: number) => {
    try {
      setSelectedItem(item);
      const res = await apiFetch<KnowledgeItemVersionDetailModel>(
        `/api/v1/knowledge/items/${item.id}/versions/${versionNum}`
      );
      setSelectedVersionDetail(res.data);
      setIsSnapshotModalOpen(true);
    } catch (err: any) {
      setError(err?.message || "Failed to load version snapshot.");
    }
  };

  // Helper Badge Color
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "PUBLISHED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "APPROVED":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
      case "IN_REVIEW":
      case "SUBMITTED":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "DRAFT":
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
      case "SUPERSEDED":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      case "RETIRED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Institutional Knowledge Base & Policy Library
            </h1>
            <span className="rounded-md bg-indigo-500/20 px-2 py-0.5 text-xs font-mono font-semibold text-indigo-400 border border-indigo-500/30">
              STEP 42
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Enterprise policy governance, multi-stage approval workflows, immutable version snapshots, and compliance attestations.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => {
              resetEditor();
              setActiveTab("editor");
            }}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            <span>+ Author Policy / SOP</span>
          </button>
          <button
            onClick={handleTriggerSweep}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors"
          >
            Trigger Review Sweep
          </button>
          <button
            onClick={loadData}
            className="px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg transition-colors"
            title="Refresh Data"
          >
            ↻
          </button>
        </div>
      </div>

      {/* 2. Global Feedback Notices */}
      {actionNotice && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-sm rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-emerald-400 font-bold hover:text-emerald-200">
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/40 text-rose-300 text-sm rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 font-bold hover:text-rose-200">
            ✕
          </button>
        </div>
      )}

      {/* 3. Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Items</span>
            <p className="text-2xl font-bold text-white mt-1">{summary.total_items}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Published</span>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{summary.published_count}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">In Review</span>
            <p className="text-2xl font-bold text-amber-400 mt-1">{summary.in_review_count}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Drafts</span>
            <p className="text-2xl font-bold text-slate-300 mt-1">{summary.draft_count}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider">Superseded</span>
            <p className="text-2xl font-bold text-purple-400 mt-1">{summary.superseded_count}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Overdue Reviews</span>
            <p className="text-2xl font-bold text-rose-400 mt-1">{summary.overdue_reviews_count}</p>
          </div>
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
            <span className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">Mandatory Read</span>
            <p className="text-2xl font-bold text-cyan-400 mt-1">{summary.mandatory_attestation_items_count}</p>
          </div>
        </div>
      )}

      {/* 4. Tab Navigation Header */}
      <div className="border-b border-slate-800 flex gap-6 overflow-x-auto text-sm font-medium">
        <button
          onClick={() => setActiveTab("library")}
          className={`pb-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "library"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Knowledge Library & Search ({items.length})
        </button>
        <button
          onClick={() => setActiveTab("editor")}
          className={`pb-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "editor"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Policy & SOP Editor {editorItemId && `(Editing: ${editorItemCode})`}
        </button>
        <button
          onClick={() => setActiveTab("review")}
          className={`pb-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "review"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>Review & Approval Queue</span>
          {reviewQueueItems.length > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30">
              {reviewQueueItems.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("attestations")}
          className={`pb-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "attestations"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Mandatory Attestations & Compliance
        </button>
        <button
          onClick={() => setActiveTab("governance")}
          className={`pb-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "governance"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Governance & Relationships
        </button>
      </div>

      {/* =========================================================================
          TAB 1: KNOWLEDGE LIBRARY & SEARCH
         ========================================================================= */}
      {activeTab === "library" && (
        <div className="space-y-6">
          {/* Search & Filter Toolbar */}
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleServerSearch()}
                  placeholder="Search policies, SOPs, academic regulations, guidelines, circulars..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                onClick={handleServerSearch}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                Search
              </button>
              {searchResults && (
                <button
                  onClick={() => setSearchResults(null)}
                  className="px-3 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg"
                >
                  Clear Results
                </button>
              )}
            </div>

            {/* Filter Chips */}
            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500 font-semibold uppercase">Category:</span>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-300 focus:outline-none"
                >
                  <option value="ALL">All Categories</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.code}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-slate-500 font-semibold uppercase">Status:</span>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-300 focus:outline-none"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="PUBLISHED">Published</option>
                  <option value="DRAFT">Draft</option>
                  <option value="SUBMITTED">Submitted</option>
                  <option value="IN_REVIEW">In Review</option>
                  <option value="APPROVED">Approved</option>
                  <option value="SUPERSEDED">Superseded</option>
                  <option value="RETIRED">Retired</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-slate-500 font-semibold uppercase">Scope:</span>
                <select
                  value={selectedScope}
                  onChange={(e) => setSelectedScope(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-300 focus:outline-none"
                >
                  <option value="ALL">All Scopes</option>
                  <option value="INSTITUTION">Institution-Wide</option>
                  <option value="CAMPUS">Campus-Specific</option>
                  <option value="DEPARTMENT">Departmental</option>
                  <option value="ROLE">Role-Restricted</option>
                  <option value="RESTRICTED">Restricted</option>
                </select>
              </div>
            </div>
          </div>

          {/* Search Result Snippets if Server Search was Run */}
          {searchResults && (
            <div className="p-4 bg-indigo-950/30 border border-indigo-500/30 rounded-xl space-y-3">
              <h3 className="text-sm font-semibold text-indigo-300 flex items-center justify-between">
                <span>Search Index Results ({searchResults.length} matches)</span>
                <span className="text-xs text-slate-400">Weighted relevance ranking</span>
              </h3>
              <div className="divide-y divide-slate-800">
                {searchResults.map((sr) => (
                  <div key={sr.id} className="py-2.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-indigo-400">{sr.item_code}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded border ${getStatusBadgeClass(sr.status)}`}>
                        {sr.status}
                      </span>
                    </div>
                    <div className="text-sm font-medium text-white mt-0.5">{sr.title}</div>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">{sr.snippet || sr.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Items Card Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="p-5 bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-xl space-y-3 transition-colors flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {item.item_code}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getStatusBadgeClass(
                        item.status
                      )}`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <h3 className="text-base font-semibold text-white line-clamp-1">{item.title}</h3>
                  <p className="text-xs text-slate-400 line-clamp-2">{item.summary || "No summary provided."}</p>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                      {item.category_code}
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                      Scope: {item.scope_type}
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                      v{item.current_version_number || 1}.0
                    </span>
                    {item.requires_acknowledgement && (
                      <span className="text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded">
                        Attestation Required
                      </span>
                    )}
                  </div>

                  {item.review_by_date && (
                    <div className="text-[11px] text-slate-500 pt-1">
                      Review due: {new Date(item.review_by_date).toLocaleDateString()}
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {item.status === "PUBLISHED" && (
                      <button
                        onClick={() => handleViewVersionSnapshot(item, item.current_version_number)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        View Snapshot
                      </button>
                    )}
                    <button
                      onClick={() => handleLoadItemIntoEditor(item)}
                      className="text-xs text-slate-300 hover:text-white font-medium"
                    >
                      Edit
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    {item.status === "DRAFT" && (
                      <button
                        onClick={() => handleSubmitForReview(item.id)}
                        className="px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs rounded transition-colors"
                      >
                        Submit
                      </button>
                    )}
                    {item.requires_acknowledgement && item.status === "PUBLISHED" && (
                      <button
                        onClick={() => {
                          setAttestModalItem(item);
                          setAttestConfirmed(false);
                        }}
                        className="px-2 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs rounded transition-colors"
                      >
                        Attest
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredItems.length === 0 && (
            <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500">
              No institutional knowledge items found matching the selected filters.
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: POLICY & SOP EDITOR
         ========================================================================= */}
      {activeTab === "editor" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Editing Column */}
          <div className="lg:col-span-2 space-y-5">
            <form onSubmit={handleSaveDraft} className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {editorItemId ? `Edit Draft Policy / SOP` : "Author New Institutional Policy"}
                  </h2>
                  <p className="text-xs text-slate-400">
                    Concurrency protected with optimistic locking (Lock Version: {editorLockVersion}).
                  </p>
                </div>
                {editorItemId && (
                  <button
                    type="button"
                    onClick={resetEditor}
                    className="text-xs text-slate-400 hover:text-slate-200 underline"
                  >
                    Start New Policy Instead
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Document Code *
                  </label>
                  <input
                    type="text"
                    value={editorItemCode}
                    onChange={(e) => setEditorItemCode(e.target.value)}
                    required
                    disabled={Boolean(editorItemId)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Classification Category *
                  </label>
                  <select
                    value={editorCategoryCode}
                    onChange={(e) => setEditorCategoryCode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.code}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  value={editorTitle}
                  onChange={(e) => setEditorTitle(e.target.value)}
                  placeholder="e.g., University Policy on Student Academic Integrity and Anti-Plagiarism"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Executive Summary / Abstract
                </label>
                <textarea
                  rows={2}
                  value={editorSummary}
                  onChange={(e) => setEditorSummary(e.target.value)}
                  placeholder="Concise high-level abstract of policy mandate and operational directives..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Visibility Scope
                  </label>
                  <select
                    value={editorScope}
                    onChange={(e) => setEditorScope(e.target.value as KnowledgeScopeType)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="INSTITUTION">INSTITUTION (All Campuses)</option>
                    <option value="CAMPUS">CAMPUS (Selected Campus)</option>
                    <option value="DEPARTMENT">DEPARTMENT (Specific Dept)</option>
                    <option value="ROLE">ROLE (Role-Based Restriction)</option>
                    <option value="RESTRICTED">RESTRICTED (Officer Access)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Confidentiality Tier
                  </label>
                  <select
                    value={editorConfidentiality}
                    onChange={(e) => setEditorConfidentiality(e.target.value as KnowledgeConfidentiality)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="PUBLIC_INSTITUTION">PUBLIC_INSTITUTION (Public)</option>
                    <option value="INTERNAL_ONLY">INTERNAL_ONLY (Staff/Students)</option>
                    <option value="CONFIDENTIAL_ADMIN">CONFIDENTIAL_ADMIN (Deans/HODs)</option>
                    <option value="RESTRICTED">RESTRICTED (Legal/Secretariat)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Target Role (If Scope = ROLE)
                  </label>
                  <input
                    type="text"
                    value={editorVisibilityRole}
                    onChange={(e) => setEditorVisibilityRole(e.target.value)}
                    placeholder="e.g. FACULTY, STUDENT"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1 flex items-center justify-between">
                  <span>Markdown Document Body</span>
                  <span className="text-[11px] text-slate-500 font-normal">Supports GitHub Flavored Markdown</span>
                </label>
                <textarea
                  rows={14}
                  value={editorContentMarkdown}
                  onChange={(e) => setEditorContentMarkdown(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Tags (Comma Separated)
                  </label>
                  <input
                    type="text"
                    value={editorTags}
                    onChange={(e) => setEditorTags(e.target.value)}
                    placeholder="exam, grading, ugc, academic"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Editorial Change Summary *
                  </label>
                  <input
                    type="text"
                    value={editorChangeSummary}
                    onChange={(e) => setEditorChangeSummary(e.target.value)}
                    placeholder="e.g., Added section 4 on remote viva-voce guidelines."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800">
                <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editorRequiresAcknowledgement}
                    onChange={(e) => setEditorRequiresAcknowledgement(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
                  />
                  <span>Enforce Mandatory User Attestation / Acknowledgement</span>
                </label>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleValidateDraft}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors"
                  >
                    Validate & Preview
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                  >
                    {editorItemId ? "Update Draft (Save)" : "Create Knowledge Item"}
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Validation & Live Preview Sidebar */}
          <div className="space-y-4">
            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
              <h3 className="text-sm font-semibold text-white">Draft Quality & Sanitization</h3>
              {draftValidation ? (
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400">Status</span>
                    <span
                      className={`font-bold ${
                        draftValidation.is_valid ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {draftValidation.is_valid ? "VALID" : "INVALID"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400">Word Count</span>
                    <span className="font-semibold text-white">{draftValidation.word_count} words</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400">Structured Sections</span>
                    <span className="font-semibold text-white">{draftValidation.sections_count} detected</span>
                  </div>

                  {draftValidation.errors.length > 0 && (
                    <div className="p-3 bg-rose-950/40 border border-rose-500/30 text-rose-300 rounded space-y-1">
                      <span className="font-bold">Errors:</span>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {draftValidation.errors.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {draftValidation.warnings.length > 0 && (
                    <div className="p-3 bg-amber-950/40 border border-amber-500/30 text-amber-300 rounded space-y-1">
                      <span className="font-bold">Recommendations:</span>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {draftValidation.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500">
                  Click &apos;Validate &amp; Preview&apos; to run safe AST HTML sanitization and quality checks against the drafted policy text.
                </p>
              )}
            </div>

            {/* Sanitized HTML Preview Pane */}
            {draftValidation?.sanitized_preview_html && (
              <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
                <h3 className="text-sm font-semibold text-white">Sanitized Render Preview</h3>
                <div
                  className="prose prose-invert prose-sm max-h-96 overflow-y-auto p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs"
                  dangerouslySetInnerHTML={{ __html: draftValidation.sanitized_preview_html }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: REVIEW & APPROVAL QUEUE (SEPARATION OF DUTIES)
         ========================================================================= */}
      {activeTab === "review" && (
        <div className="space-y-6">
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
            <h2 className="text-base font-semibold text-white mb-1">Institutional Editorial Review Queue</h2>
            <p className="text-xs text-slate-400">
              Per strict separation of duties, the primary author or last editor cannot approve their own submissions. An independent reviewer or authorized compliance officer must conduct formal review.
            </p>
          </div>

          <div className="space-y-4">
            {reviewQueueItems.map((item) => {
              const isAuthor = user?.id && item.owner_user_id === user.id;

              return (
                <div
                  key={item.id}
                  className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 max-w-2xl">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {item.item_code}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded border ${getStatusBadgeClass(item.status)}`}>
                        {item.status}
                      </span>
                      <span className="text-xs text-slate-400">Category: {item.category_code}</span>
                    </div>

                    <h3 className="text-base font-bold text-white">{item.title}</h3>
                    <p className="text-xs text-slate-400 line-clamp-2">{item.summary}</p>

                    {item.change_summary && (
                      <div className="text-xs text-indigo-300 font-mono bg-indigo-950/30 p-2 rounded border border-indigo-500/20">
                        Change note: {item.change_summary}
                      </div>
                    )}

                    {isAuthor && (
                      <div className="text-xs text-amber-400 font-medium flex items-center gap-1.5 pt-1">
                        <span>⚠️ Separation of Duties Guard:</span>
                        <span>You are registered as the author of this item. Approval must be performed by another authorized officer.</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-2.5">
                    <button
                      onClick={() => handleLoadItemIntoEditor(item)}
                      className="w-full sm:w-auto px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
                    >
                      Inspect Draft
                    </button>

                    <button
                      onClick={() => {
                        setReviewActionItem(item);
                        setReviewDecision("APPROVED");
                        setReviewComments("");
                      }}
                      className="w-full sm:w-auto px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                    >
                      Conduct Review
                    </button>
                  </div>
                </div>
              );
            })}

            {reviewQueueItems.length === 0 && (
              <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500">
                No policy items currently awaiting editorial review or approval.
              </div>
            )}
          </div>

          {/* Approved Items Ready for Release Publication */}
          <div className="pt-6">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Approved Items Ready for Formal Publication
            </h3>
            <div className="space-y-3">
              {items
                .filter((item) => item.status === "APPROVED")
                .map((item) => (
                  <div
                    key={item.id}
                    className="p-4 bg-slate-900/40 border border-cyan-500/30 rounded-xl flex items-center justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-cyan-400">{item.item_code}</span>
                        <span className="text-xs text-slate-300 font-medium">{item.title}</span>
                      </div>
                      <span className="text-xs text-slate-400 mt-1 block">
                        Approved by independent reviewer. Awaiting publication snapshot generation.
                      </span>
                    </div>

                    <button
                      onClick={() => {
                        setPublishActionItem(item);
                        setPublishBumpType("PATCH");
                        setPublishChangeSummary("");
                      }}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                    >
                      Publish Snapshot
                    </button>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: MANDATORY ATTESTATIONS & COMPLIANCE REPORTING
         ========================================================================= */}
      {activeTab === "attestations" && (
        <div className="space-y-6">
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
            <h2 className="text-base font-semibold text-white mb-1">Mandatory Policy Attestations & Compliance</h2>
            <p className="text-xs text-slate-400">
              Exact-version compliance tracking for statutory regulatory directives, codes of conduct, and academic integrity policies.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {complianceReports.map((report) => (
              <div
                key={report.item_id}
                className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      {report.item_code}
                    </span>
                    <span className="text-xs text-slate-400">v{report.version_number}.0</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white line-clamp-2">{report.item_title}</h3>

                  <div className="pt-2">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">Compliance Rate</span>
                      <span className="font-bold text-white">{report.compliance_percentage}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full transition-all"
                        style={{ width: `${Math.min(report.compliance_percentage, 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 block">Required</span>
                      <span className="font-bold text-white">{report.total_required}</span>
                    </div>
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 block">Attested</span>
                      <span className="font-bold text-emerald-400">{report.total_acknowledged}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800">
                  <span className="text-[11px] text-slate-500 block mb-2">
                    Deadline: {report.deadline_days} days from publication
                  </span>
                  <button
                    onClick={() => {
                      const itm = items.find((i) => i.id === report.item_id);
                      if (itm) {
                        setAttestModalItem(itm);
                        setAttestConfirmed(false);
                      }
                    }}
                    className="w-full py-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold rounded-lg transition-colors"
                  >
                    Attest to This Policy
                  </button>
                </div>
              </div>
            ))}

            {complianceReports.length === 0 && (
              <div className="col-span-full p-12 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500">
                No policy items currently configured with mandatory attestation requirements.
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 5: GOVERNANCE & RELATIONSHIPS
         ========================================================================= */}
      {activeTab === "governance" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
            <div>
              <h2 className="text-base font-semibold text-white">Directed Policy Cross-References & Supersessions</h2>
              <p className="text-xs text-slate-400">
                Directed relationships between institutional policies with cycle-prevention graph validation.
              </p>
            </div>
            <button
              onClick={() => setIsRelModalOpen(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              + Link Knowledge Items
            </button>
          </div>

          {/* Scheduled Reviews Calendar / Table */}
          <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Scheduled Statutory Review Calendar</h3>
              <span className="text-xs text-slate-400">{scheduledReviews.length} automated review schedules</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-3">Review Type</th>
                    <th className="py-2.5 px-3">Scheduled Date</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Last Notified</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {scheduledReviews.map((rev) => (
                    <tr key={rev.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-semibold text-white">{rev.schedule_type}</td>
                      <td className="py-2.5 px-3 font-mono">
                        {rev.scheduled_date ? new Date(rev.scheduled_date).toLocaleDateString() : "-"}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            rev.status === "OVERDUE"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {rev.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {rev.notified_at ? new Date(rev.notified_at).toLocaleString() : "Pending"}
                      </td>
                    </tr>
                  ))}
                  {scheduledReviews.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-500">
                        Zero scheduled review alerts. Run a review sweep to generate reminders.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: VIEW IMMUTABLE VERSION SNAPSHOT
         ========================================================================= */}
      {isSnapshotModalOpen && selectedVersionDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    Version v{selectedVersionDetail.version_number}.0
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                    IMMUTABLE SNAPSHOT
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">{selectedVersionDetail.title}</h2>
              </div>
              <button
                onClick={() => setIsSnapshotModalOpen(false)}
                className="text-slate-400 hover:text-white font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <div>
                  <span className="text-slate-500 block">Published At</span>
                  <span className="text-slate-300 font-mono">
                    {new Date(selectedVersionDetail.published_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Effective From</span>
                  <span className="text-slate-300 font-mono">
                    {new Date(selectedVersionDetail.effective_from).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Decision</span>
                  <span className="text-emerald-400 font-semibold">{selectedVersionDetail.approval_decision}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Change Summary</span>
                  <span className="text-slate-300">{selectedVersionDetail.change_summary || "Release"}</span>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Published Document Text
                </h3>
                <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {selectedVersionDetail.content_markdown}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setIsSnapshotModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: CONDUCT EDITORIAL REVIEW
         ========================================================================= */}
      {reviewActionItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-white">Editorial Review Decision</h2>
            <p className="text-xs text-slate-400">
              Evaluating: <span className="text-indigo-400 font-mono">{reviewActionItem.item_code}</span> — {reviewActionItem.title}
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Decision
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
                >
                  <option value="APPROVED">APPROVED — Clear for Publication</option>
                  <option value="CHANGES_REQUESTED">CHANGES_REQUESTED — Return to Author</option>
                  <option value="REJECTED">REJECTED — Not Aligned with Institutional Policy</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Editorial Comments / Feedback *
                </label>
                <textarea
                  rows={3}
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  placeholder="Record formal statutory rationale and compliance feedback..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setReviewActionItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleReviewDecision}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg"
              >
                Confirm Decision
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: PUBLISH IMMUTABLE SNAPSHOT
         ========================================================================= */}
      {publishActionItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-white">Publish Approved Policy Snapshot</h2>
            <p className="text-xs text-slate-400">
              Formally publish <span className="text-cyan-400 font-mono">{publishActionItem.item_code}</span> into the repository. An immutable snapshot will be created.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  SemVer Version Bump Type
                </label>
                <select
                  value={publishBumpType}
                  onChange={(e) => setPublishBumpType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
                >
                  <option value="PATCH">PATCH (e.g. Minor wording / clarification bump)</option>
                  <option value="MINOR">MINOR (e.g. Section update, new guidance)</option>
                  <option value="MAJOR">MAJOR (e.g. Complete policy overhaul)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Official Release Notes
                </label>
                <textarea
                  rows={3}
                  value={publishChangeSummary}
                  onChange={(e) => setPublishChangeSummary(e.target.value)}
                  placeholder="Record formal release notes for university records..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setPublishActionItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handlePublishItem}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg"
              >
                Publish Snapshot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: USER ATTESTATION / ACKNOWLEDGEMENT
         ========================================================================= */}
      {attestModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-white">Institutional Document Attestation</h2>
            <p className="text-xs text-slate-400">
              Mandatory confirmation of reading and compliance with:
            </p>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1">
              <div className="font-mono text-cyan-400 font-bold">{attestModalItem.item_code} (Version v{attestModalItem.current_version_number}.0)</div>
              <div className="text-white font-semibold">{attestModalItem.title}</div>
            </div>

            <div className="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl space-y-3">
              <label className="flex items-start gap-2.5 text-xs text-indigo-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={attestConfirmed}
                  onChange={(e) => setAttestConfirmed(e.target.checked)}
                  className="mt-0.5 rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
                />
                <span>
                  &ldquo;I hereby confirm that I have accessed, thoroughly read, understood, and agreed to adhere to all terms, guidelines, and directives outlined in this institutional document.&rdquo;
                </span>
              </label>
              <div className="text-[11px] text-slate-400">
                Timestamp, verified user ID ({user?.email || "Current Officer"}), and client IP will be cryptographically registered in the compliance registry.
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setAttestModalItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg"
              >
                Cancel
              </button>
              <button
                disabled={!attestConfirmed}
                onClick={handleRecordAttestation}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg"
              >
                Submit Attestation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: CREATE DIRECTED RELATIONSHIP
         ========================================================================= */}
      {isRelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-white">Create Directed Relationship</h2>
            <p className="text-xs text-slate-400">
              Link two policies or SOPs with graph cycle prevention.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Source Document (Origin) *
                </label>
                <select
                  value={relSourceItemId}
                  onChange={(e) => setRelSourceItemId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="">Select source item...</option>
                  {items.map((it) => (
                    <option key={it.id} value={it.id}>
                      {it.item_code} — {it.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Relationship Type *
                </label>
                <select
                  value={relType}
                  onChange={(e) => setRelType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="SUPERSEDES">SUPERSEDES (Source supersedes Target)</option>
                  <option value="IMPLEMENTS">IMPLEMENTS (Source SOP implements Target Policy)</option>
                  <option value="REFERENCES">REFERENCES (Source references Target)</option>
                  <option value="DEPENDS_ON">DEPENDS_ON (Source depends on Target)</option>
                  <option value="ANNOUNCES">ANNOUNCES (Circular announces Policy)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Target Document (Destination) *
                </label>
                <select
                  value={relTargetItemId}
                  onChange={(e) => setRelTargetItemId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="">Select target item...</option>
                  {items.map((it) => (
                    <option key={it.id} value={it.id}>
                      {it.item_code} — {it.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Description / Justification
                </label>
                <input
                  type="text"
                  value={relDescription}
                  onChange={(e) => setRelDescription(e.target.value)}
                  placeholder="e.g. Senate Decree 2026/04 resolution"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsRelModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRelationship}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
              >
                Establish Link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
