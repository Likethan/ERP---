"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Archive,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  History,
  Lock,
  Plus,
  RefreshCw,
  Search,
  Send,
  Shield,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Users,
  X,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { formatLegalDate } from "@/services/legal-calculator";

interface InstitutionalPolicyRecord {
  id: string;
  policy_code: string;
  title: string;
  category: string;
  status: "DRAFT" | "UNDER_REVIEW" | "APPROVED" | "PUBLISHED" | "SUPERSEDED" | "RETIRED";
  version: string;
  owner_department: string;
  responsible_official: string;
  effective_date: string;
  review_by_date: string;
  requires_acknowledgment: boolean;
  acknowledgment_count?: number;
  summary: string;
  scope: string;
}

const MOCK_POLICIES: InstitutionalPolicyRecord[] = [
  {
    id: "pol-01",
    policy_code: "POL-SEC-2026-001",
    title: "Institutional Generative AI & Data Confidentiality Framework",
    category: "INFORMATION_SECURITY",
    status: "PUBLISHED",
    version: "2.1",
    owner_department: "Information Technology & Cybersecurity",
    responsible_official: "Chief Information Security Officer",
    effective_date: "2026-01-15",
    review_by_date: "2027-01-15",
    requires_acknowledgment: true,
    acknowledgment_count: 1420,
    summary:
      "Defines acceptable institutional use of LLM tools, confidential student records protection under FERPA, and mandatory enterprise API boundaries.",
    scope: "All Faculty, Administrative Staff, Researchers, and Students",
  },
  {
    id: "pol-02",
    policy_code: "POL-ACAD-2025-004",
    title: "Academic Integrity, Plagiarism & AI-Assisted Research",
    category: "ACADEMIC",
    status: "PUBLISHED",
    version: "3.0",
    owner_department: "Office of the Provost & Academic Senate",
    responsible_official: "Dean of Academic Affairs",
    effective_date: "2025-08-01",
    review_by_date: "2026-08-01",
    requires_acknowledgment: true,
    acknowledgment_count: 3840,
    summary:
      "Standards for authentic scholarship, peer attribution, laboratory reproducibility, and disclosure protocols for generative tool usage in dissertations.",
    scope: "Undergraduate, Graduate Students, and Instructional Faculty",
  },
  {
    id: "pol-03",
    policy_code: "POL-FIN-2026-008",
    title: "Delegated Signature Authority & High-Value Procurement Thresholds",
    category: "FINANCIAL",
    status: "UNDER_REVIEW",
    version: "1.4",
    owner_department: "Finance & Institutional Procurement",
    responsible_official: "Chief Financial Officer",
    effective_date: "2026-04-01",
    review_by_date: "2026-10-01",
    requires_acknowledgment: false,
    summary:
      "Updated tiered expenditure authorization limits for Department Chairs ($50k), Deans ($100k), and Provost/VP ($500k+).",
    scope: "All Institutional Budget Heads and Procurement Officers",
  },
  {
    id: "pol-04",
    policy_code: "POL-RES-2026-012",
    title: "Institutional Review Board (IRB) Human Subjects Protection",
    category: "RESEARCH_ETHICS",
    status: "APPROVED",
    version: "4.0",
    owner_department: "Office of Sponsored Research",
    responsible_official: "IRB Chair & Compliance Director",
    effective_date: "2026-03-01",
    review_by_date: "2028-03-01",
    requires_acknowledgment: true,
    acknowledgment_count: 412,
    summary:
      "Procedures for expedited reviews, informed consent documentation, clinical trial oversight, and research data repository compliance.",
    scope: "Principal Investigators, Postdoctoral Fellows, and Clinical Staff",
  },
];

export default function PolicyGovernancePage() {
  const [policies, setPolicies] = useState<InstitutionalPolicyRecord[]>(MOCK_POLICIES);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");

  // Modals
  const [isDraftOpen, setIsDraftOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<InstitutionalPolicyRecord | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  // Draft form
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState("INFORMATION_SECURITY");
  const [newSummary, setNewSummary] = useState("");
  const [newDepartment, setNewDepartment] = useState("Legal & Institutional Affairs");
  const [newRequiresAck, setNewRequiresAck] = useState(true);

  // Review form
  const [reviewDecision, setReviewDecision] = useState<"PUBLISHED" | "APPROVED" | "SUPERSEDED">("PUBLISHED");
  const [reviewNotes, setReviewNotes] = useState("");

  function handleDraftSubmit(e: React.FormEvent) {
    e.preventDefault();
    const newRecord: InstitutionalPolicyRecord = {
      id: `pol-${Date.now()}`,
      policy_code: `POL-${newCategory.slice(0, 4)}-2026-${Math.floor(100 + Math.random() * 900)}`,
      title: newTitle,
      category: newCategory,
      status: "DRAFT",
      version: "1.0",
      owner_department: newDepartment,
      responsible_official: "Designated Policy Steward",
      effective_date: new Date().toISOString().split("T")[0],
      review_by_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
      requires_acknowledgment: newRequiresAck,
      summary: newSummary,
      scope: "Campus-wide Institutional Scope",
    };
    setPolicies([newRecord, ...policies]);
    setIsDraftOpen(false);
    setNewTitle("");
    setNewSummary("");
  }

  function handleReviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPolicy) return;
    setPolicies((prev) =>
      prev.map((p) =>
        p.id === selectedPolicy.id
          ? {
              ...p,
              status: reviewDecision,
              effective_date: new Date().toISOString().split("T")[0],
            }
          : p
      )
    );
    setIsReviewOpen(false);
  }

  const filteredPolicies = policies.filter((p) => {
    if (selectedCategory !== "ALL" && p.category !== selectedCategory) return false;
    if (selectedStatus !== "ALL" && p.status !== selectedStatus) return false;
    if (
      searchTerm &&
      !p.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !p.policy_code.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-indigo-600" /> Institutional Policy & Procedure Governance
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Controlled lifecycle management for university policies, senate reviews, mandatory faculty/staff attestations, and archival supersession.
            </p>
          </div>
          <button
            onClick={() => setIsDraftOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Propose Policy Draft
          </button>
        </div>

        {/* Filter and Search Bar */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search policy title, code, or department..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Categories</option>
                <option value="ACADEMIC">Academic Policies</option>
                <option value="INFORMATION_SECURITY">Information Security & Privacy</option>
                <option value="FINANCIAL">Finance & Procurement</option>
                <option value="RESEARCH_ETHICS">Research & Human Subjects</option>
                <option value="STUDENT_CONDUCT">Student Conduct & Grievances</option>
                <option value="CAMPUS_OPERATIONS">Campus Operations & Safety</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Statuses</option>
                <option value="PUBLISHED">Published (In Force)</option>
                <option value="APPROVED">Approved (Awaiting Rollout)</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="DRAFT">Draft</option>
                <option value="SUPERSEDED">Superseded</option>
                <option value="RETIRED">Retired</option>
              </select>
            </div>
          </div>
        </div>

        {/* Policy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredPolicies.map((policy) => (
            <div
              key={policy.id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between space-y-4 hover:border-slate-300 dark:hover:border-slate-700 transition-all"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {policy.policy_code} • v{policy.version}
                  </span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                      policy.status === "PUBLISHED"
                        ? "bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                        : policy.status === "APPROVED"
                        ? "bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                        : "bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                    }`}
                  >
                    {policy.status}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-slate-900 dark:text-white">{policy.title}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                  {policy.summary}
                </p>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                <div className="grid grid-cols-2 gap-2 text-slate-500">
                  <div>
                    <span className="block text-[10px] uppercase font-bold text-slate-400">Owner</span>
                    <strong className="text-slate-700 dark:text-slate-300 truncate block">
                      {policy.owner_department}
                    </strong>
                  </div>
                  <div>
                    <span className="block text-[10px] uppercase font-bold text-slate-400">Review Due</span>
                    <strong className="text-slate-700 dark:text-slate-300 block">
                      {formatLegalDate(policy.review_by_date)}
                    </strong>
                  </div>
                </div>

                {policy.requires_acknowledgment && (
                  <div className="p-2.5 rounded-lg bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-medium">
                      <UserCheck className="h-4 w-4" /> Mandatory Attestation Active
                    </span>
                    <span className="font-bold">{policy.acknowledgment_count} Signed</span>
                  </div>
                )}

                <div className="flex items-center justify-between pt-2">
                  <span className="text-[11px] text-slate-400">
                    Effective: {formatLegalDate(policy.effective_date)}
                  </span>
                  <button
                    onClick={() => {
                      setSelectedPolicy(policy);
                      setIsReviewOpen(true);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                  >
                    Review / Publish
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* MODAL 1: Propose Draft */}
      {isDraftOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-indigo-600" /> Propose New Institutional Policy Draft
              </h3>
              <button
                onClick={() => setIsDraftOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleDraftSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Policy Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Campus Drone & Unmanned Aerial Systems Policy"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="ACADEMIC">ACADEMIC</option>
                    <option value="INFORMATION_SECURITY">INFORMATION_SECURITY</option>
                    <option value="FINANCIAL">FINANCIAL</option>
                    <option value="RESEARCH_ETHICS">RESEARCH_ETHICS</option>
                    <option value="STUDENT_CONDUCT">STUDENT_CONDUCT</option>
                    <option value="CAMPUS_OPERATIONS">CAMPUS_OPERATIONS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Owner Department
                  </label>
                  <input
                    type="text"
                    value={newDepartment}
                    onChange={(e) => setNewDepartment(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Executive Summary & Scope
                </label>
                <textarea
                  rows={3}
                  placeholder="Summarize the core requirements, rationale, and affected campus constituencies..."
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="requiresAck"
                  checked={newRequiresAck}
                  onChange={(e) => setNewRequiresAck(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="requiresAck" className="text-xs text-slate-700 dark:text-slate-300">
                  Require annual digital acknowledgment from affected campus personnel
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsDraftOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  Create Policy Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Review / Publish */}
      {isReviewOpen && selectedPolicy && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-indigo-600" /> Policy Review & Publication Workflow
              </h3>
              <button
                onClick={() => setIsReviewOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Policy: <strong>{selectedPolicy.title}</strong> ({selectedPolicy.policy_code})
            </p>

            <form onSubmit={handleReviewSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Lifecycle Determination
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="PUBLISHED">PUBLISH (Enact as Official Institutional Policy)</option>
                  <option value="APPROVED">APPROVE (Awaiting Next Semester Rollout)</option>
                  <option value="SUPERSEDED">SUPERSEDE (Archive and Replace with New Edition)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Senate / Legal Review Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Record formal approval reference, committee vote, or legal review notes..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsReviewOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  Confirm Determination
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
