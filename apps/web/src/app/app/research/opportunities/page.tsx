"use client";

import React, { useEffect, useState } from "react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { ResearchFundingOpportunity } from "@/types/research";
import {
  Sparkles,
  Search,
  Bookmark,
  BookmarkCheck,
  Send,
  Plus,
  RefreshCw,
  ExternalLink,
  Calendar,
  DollarSign,
  Building,
  Tag,
  Clock,
  CheckCircle2,
} from "lucide-react";

export default function GrantOpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<ResearchFundingOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // EOI Modal state
  const [isEoiModalOpen, setIsEoiModalOpen] = useState(false);
  const [selectedOpp, setSelectedOpp] = useState<ResearchFundingOpportunity | null>(null);
  const [eoiForm, setEoiForm] = useState({
    prospective_project_title: "",
    notes: "",
    estimated_budget: 150000,
  });

  // New Opportunity Modal
  const [isNewOppModalOpen, setIsNewOppModalOpen] = useState(false);
  const [newOppForm, setNewOppForm] = useState({
    code: `OPP-NSF-${Math.floor(1000 + Math.random() * 9000)}`,
    title: "",
    description: "",
    funding_agency_name: "National Science Foundation",
    category: "GOVERNMENT_GRANT",
    research_domains: ["Renewable Energy", "Smart Grids"],
    eligibility_criteria: "Higher Education Institutions and Research Consortia",
    opening_date: new Date().toISOString().split("T")[0],
    closing_date: new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0],
    min_funding_amount: 100000,
    max_funding_amount: 500000,
    currency: "USD",
  });

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const data = await ResearchService.getFundingOpportunities({
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
      });
      setOpportunities(data);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to load opportunities." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [categoryFilter]);

  const handleToggleSave = async (opp: ResearchFundingOpportunity) => {
    const nextSaved = !opp.is_saved;
    try {
      await ResearchService.saveOpportunity(opp.id, nextSaved);
      setOpportunities((prev) =>
        prev.map((o) => (o.id === opp.id ? { ...o, is_saved: nextSaved } : o))
      );
      setFeedback({
        type: "success",
        message: nextSaved ? "Opportunity saved to bookmarks." : "Opportunity removed from bookmarks.",
      });
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to update bookmark." });
    }
  };

  const handleOpenEoi = (opp: ResearchFundingOpportunity) => {
    setSelectedOpp(opp);
    setEoiForm({
      prospective_project_title: `Proposal for ${opp.title}`,
      notes: "Departmental team assembled. Preparing multi-institution collaborative draft.",
      estimated_budget: opp.max_funding_amount || 200000,
    });
    setIsEoiModalOpen(true);
  };

  const handleSubmitEoi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOpp) return;
    try {
      await ResearchService.recordOpportunityEOI(selectedOpp.id, {
        prospective_project_title: eoiForm.prospective_project_title,
        principal_investigator_id: "00000000-0000-0000-0000-000000000000",
        notes: eoiForm.notes,
        estimated_budget: Number(eoiForm.estimated_budget),
      });
      setFeedback({
        type: "success",
        message: `Expression of Interest recorded for '${selectedOpp.title}'.`,
      });
      setIsEoiModalOpen(false);
      loadOpportunities();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to record Expression of Interest." });
    }
  };

  const handleCreateOpp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await ResearchService.createFundingOpportunity(newOppForm as any);
      setFeedback({ type: "success", message: `Opportunity '${newOppForm.title}' registered in registry.` });
      setIsNewOppModalOpen(false);
      loadOpportunities();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to catalog opportunity." });
    }
  };

  const filteredOpps = opportunities.filter((o) => {
    const q = search.toLowerCase();
    return (
      o.title.toLowerCase().includes(q) ||
      o.funding_agency_name.toLowerCase().includes(q) ||
      o.code.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Page Title & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-amber-400" />
              Grant Discovery & Funding Opportunity Registry
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Curated opportunities from research councils, government agencies, foundations, and industry sponsors.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsNewOppModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all"
            >
              <Plus className="h-4 w-4" />
              Catalog Funding Call
            </button>
            <button
              onClick={loadOpportunities}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
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

        {/* Search & Filters */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by scheme title, agency, or code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-xs text-slate-400 font-medium">Sponsor Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="ALL">All Categories</option>
              <option value="GOVERNMENT_GRANT">Government Grants</option>
              <option value="INDUSTRY_SPONSORED">Industry Sponsored</option>
              <option value="FOUNDATION_PHILANTHROPY">Foundations</option>
              <option value="INTERNATIONAL_CONSORTIUM">International Consortia</option>
            </select>
          </div>
        </div>

        {/* Opportunity Cards */}
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="h-8 w-8 animate-spin text-emerald-400 mx-auto" />
            <p className="text-sm text-slate-400">Loading funding schemes...</p>
          </div>
        ) : filteredOpps.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 space-y-4">
            <Sparkles className="h-12 w-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-semibold text-white">No funding opportunities found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Clear your search or catalog verified funding schemes from government agencies or sponsors.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredOpps.map((opp) => (
              <div
                key={opp.id}
                className="flex flex-col justify-between rounded-xl bg-slate-900/60 border border-slate-800 p-5 hover:border-slate-700 transition-all hover:shadow-xl hover:shadow-emerald-950/20 group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                      {opp.code}
                    </span>
                    <button
                      onClick={() => handleToggleSave(opp)}
                      className={`p-1.5 rounded-lg border transition-colors ${
                        opp.is_saved
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          : "bg-slate-800/80 text-slate-400 border-slate-700 hover:text-white"
                      }`}
                      title={opp.is_saved ? "Bookmarked" : "Save opportunity"}
                    >
                      {opp.is_saved ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
                    </button>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white group-hover:text-emerald-400 transition-colors line-clamp-2">
                      {opp.title}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">{opp.description}</p>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                    <div className="flex items-center gap-2">
                      <Building className="h-3.5 w-3.5 text-slate-500" />
                      <span className="text-slate-300">{opp.funding_agency_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-3.5 w-3.5 text-emerald-400" />
                      <span className="text-emerald-400 font-mono font-semibold">
                        {opp.currency} {Number(opp.min_funding_amount || 0).toLocaleString()} →{" "}
                        {Number(opp.max_funding_amount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-3.5 w-3.5 text-amber-400" />
                      <span className="text-slate-300">
                        Deadline: <strong className="font-mono text-amber-400">{opp.closing_date}</strong>
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between gap-2">
                  <span className="text-[11px] text-slate-500">
                    {opp.metadata_json?.expressions_of_interest?.length || 0} EOI(s) Logged
                  </span>
                  <button
                    onClick={() => handleOpenEoi(opp)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
                  >
                    <Send className="h-3.5 w-3.5" />
                    Express Interest
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Expression of Interest Modal */}
      {isEoiModalOpen && selectedOpp && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Send className="h-5 w-5 text-emerald-400" />
              Record Institutional Expression of Interest
            </h3>
            <p className="text-xs text-slate-400">
              For call: <strong className="text-white">{selectedOpp.title}</strong> ({selectedOpp.funding_agency_name})
            </p>

            <form onSubmit={handleSubmitEoi} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Prospective Project Title</label>
                <input
                  type="text"
                  value={eoiForm.prospective_project_title}
                  onChange={(e) => setEoiForm({ ...eoiForm, prospective_project_title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Estimated Budget Request</label>
                <input
                  type="number"
                  value={eoiForm.estimated_budget}
                  onChange={(e) => setEoiForm({ ...eoiForm, estimated_budget: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Proposal Concept & Teaming Notes</label>
                <textarea
                  rows={3}
                  value={eoiForm.notes}
                  onChange={(e) => setEoiForm({ ...eoiForm, notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEoiModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-sm"
                >
                  Submit Expression of Interest
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Catalog New Funding Call Modal */}
      {isNewOppModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus className="h-5 w-5 text-emerald-400" />
              Catalog Funding Scheme in Registry
            </h3>

            <form onSubmit={handleCreateOpp} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Opportunity Code</label>
                <input
                  type="text"
                  value={newOppForm.code}
                  onChange={(e) => setNewOppForm({ ...newOppForm, code: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Scheme / Program Title</label>
                <input
                  type="text"
                  value={newOppForm.title}
                  onChange={(e) => setNewOppForm({ ...newOppForm, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Sponsoring Agency</label>
                <input
                  type="text"
                  value={newOppForm.funding_agency_name}
                  onChange={(e) => setNewOppForm({ ...newOppForm, funding_agency_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Min Funding Amount</label>
                  <input
                    type="number"
                    value={newOppForm.min_funding_amount}
                    onChange={(e) => setNewOppForm({ ...newOppForm, min_funding_amount: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Max Funding Amount</label>
                  <input
                    type="number"
                    value={newOppForm.max_funding_amount}
                    onChange={(e) => setNewOppForm({ ...newOppForm, max_funding_amount: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Submission Deadline</label>
                <input
                  type="date"
                  value={newOppForm.closing_date}
                  onChange={(e) => setNewOppForm({ ...newOppForm, closing_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewOppModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-sm"
                >
                  Save Call
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
