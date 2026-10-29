"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { calculateProjectHealth } from "@/services/research-calculator";
import { ResearchProject, ResearchProjectCategory, ResearchProjectStatus } from "@/types/research";
import {
  FolderKanban,
  Search,
  Filter,
  Plus,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Users,
  DollarSign,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export default function ProjectsPortfolioPage() {
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Form State
  const [form, setForm] = useState({
    project_code: `RES-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    title: "",
    abstract: "",
    research_domain: "Computer Science & AI",
    research_category: "APPLIED_INNOVATION",
    proposed_budget: 100000,
    currency: "USD",
    requires_ethics_approval: false,
    start_date: new Date().toISOString().split("T")[0],
    planned_end_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
  });

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await ResearchService.getProjects({
        search: search || undefined,
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setProjects(data);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to load projects." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [categoryFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadProjects();
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.abstract.trim()) {
      setFeedback({ type: "error", message: "Please enter project title and abstract." });
      return;
    }
    try {
      const created = await ResearchService.createProject(form as any);
      setFeedback({ type: "success", message: `Project ${created.project_code} registered in portfolio.` });
      setIsNewProjectModalOpen(false);
      loadProjects();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to register project." });
    }
  };

  const statusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === "ACTIVE") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (s === "APPROVED") return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    if (s === "UNDER_REVIEW") return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    if (s === "COMPLETED") return "bg-purple-500/10 text-purple-400 border-purple-500/20";
    if (s === "CLOSED") return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    return "bg-slate-800 text-slate-400 border-slate-700";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Page Title & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FolderKanban className="h-6 w-6 text-emerald-400" />
              Institutional Project Portfolio
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Unified operational portfolio covering faculty, student, sponsored, and international research.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsNewProjectModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all"
            >
              <Plus className="h-4 w-4" />
              New Research Project
            </button>
            <button
              onClick={loadProjects}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              title="Refresh Portfolio"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-4 rounded-xl border text-sm flex items-center justify-between ${
              feedback.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="text-xs underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Search & Filter Bar */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by title, code, domain, or PI..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all"
            />
          </form>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Categories</option>
                <option value="FACULTY_LED">Faculty-Led</option>
                <option value="GOVERNMENT_FUNDED">Government-Funded</option>
                <option value="INDUSTRY_SPONSORED">Industry-Sponsored</option>
                <option value="APPLIED_INNOVATION">Applied Innovation</option>
                <option value="INTERNATIONAL_COLLABORATION">International</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="PROPOSAL">Proposal</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="APPROVED">Approved</option>
                <option value="ACTIVE">Active</option>
                <option value="ON_HOLD">On Hold</option>
                <option value="COMPLETED">Completed</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Project Grid / Cards */}
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="h-8 w-8 animate-spin text-emerald-400 mx-auto" />
            <p className="text-sm text-slate-400">Loading project records from institutional repository...</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 space-y-4">
            <FolderKanban className="h-12 w-12 text-slate-600 mx-auto" />
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-white">No research projects match your criteria</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Try clearing active filters or register a new research project in the institutional portfolio.
              </p>
            </div>
            <button
              onClick={() => setIsNewProjectModalOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Register New Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="flex flex-col justify-between rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 hover:border-slate-700 transition-all hover:shadow-xl hover:shadow-emerald-950/20 group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                      {proj.project_code}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${statusBadge(
                        proj.status
                      )}`}
                    >
                      {proj.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-semibold text-white group-hover:text-emerald-400 transition-colors line-clamp-2">
                      {proj.title}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">{proj.abstract}</p>
                  </div>

                  <div className="space-y-1 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Domain:</span>
                      <span className="text-slate-300 font-medium">{proj.research_domain}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Allocation:</span>
                      <span className="text-emerald-400 font-semibold font-mono">
                        {proj.currency} {Number(proj.total_budget_allocated).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Timeline:</span>
                      <span className="text-slate-300 font-mono text-[11px]">
                        {proj.start_date} → {proj.planned_end_date}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  {proj.requires_ethics_approval ? (
                    <span className="flex items-center gap-1 text-[11px] text-amber-400">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Ethics Required
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500">Standard Protocol</span>
                  )}

                  <Link
                    href={`/app/research/projects/${proj.id}`}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 hover:text-emerald-300 group-hover:translate-x-0.5 transition-transform"
                  >
                    Workspace
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* New Project Registration Modal */}
      {isNewProjectModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-emerald-400" />
                Register New Institutional Research Project
              </h3>
              <button
                onClick={() => setIsNewProjectModalOpen(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Project Code</label>
                  <input
                    type="text"
                    value={form.project_code}
                    onChange={(e) => setForm({ ...form, project_code: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Research Domain</label>
                  <input
                    type="text"
                    value={form.research_domain}
                    onChange={(e) => setForm({ ...form, research_domain: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Project Title</label>
                <input
                  type="text"
                  placeholder="e.g., Deep Learning Architectures for Autonomous Electric Grid Management"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Abstract & Scope</label>
                <textarea
                  rows={3}
                  placeholder="Detail problem statement, scientific methodology, and target institutional deliverables..."
                  value={form.abstract}
                  onChange={(e) => setForm({ ...form, abstract: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Category</label>
                  <select
                    value={form.research_category}
                    onChange={(e) => setForm({ ...form, research_category: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="FACULTY_LED">Faculty-Led</option>
                    <option value="APPLIED_INNOVATION">Applied Innovation</option>
                    <option value="GOVERNMENT_FUNDED">Government-Funded</option>
                    <option value="INDUSTRY_SPONSORED">Industry-Sponsored</option>
                    <option value="STUDENT_RESEARCH">Student Research</option>
                    <option value="INTERNATIONAL_COLLABORATION">International Collaboration</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">Proposed Budget</label>
                  <input
                    type="number"
                    value={form.proposed_budget}
                    onChange={(e) => setForm({ ...form, proposed_budget: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">Currency</label>
                  <input
                    type="text"
                    value={form.currency}
                    onChange={(e) => setForm({ ...form, currency: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Start Date</label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Planned End Date</label>
                  <input
                    type="date"
                    value={form.planned_end_date}
                    onChange={(e) => setForm({ ...form, planned_end_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="ethics_checkbox"
                  checked={form.requires_ethics_approval}
                  onChange={(e) => setForm({ ...form, requires_ethics_approval: e.target.checked })}
                  className="rounded bg-slate-950 border-slate-800 text-emerald-600 focus:ring-0"
                />
                <label htmlFor="ethics_checkbox" className="text-slate-300">
                  Project involves human subjects, animal assays, or biohazardous materials (Requires institutional ethics review)
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewProjectModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-md shadow-emerald-600/20"
                >
                  Save Project to Portfolio
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
