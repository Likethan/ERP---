"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Club } from "@campusos/types";

const CLUB_CATEGORIES = [
  "ALL",
  "TECHNICAL",
  "CULTURAL",
  "SPORTS",
  "SOCIAL",
  "ACADEMIC",
  "ENTREPRENEURSHIP",
  "LITERARY",
  "OTHER",
];

export default function ClubsCatalogPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clubs, setClubs] = useState<Club[]>([]);

  // Filters
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Propose Club Modal
  const [showProposeModal, setShowProposeModal] = useState(false);
  const [proposing, setProposing] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    category: "TECHNICAL",
    description: "",
  });

  const loadClubs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (category !== "ALL") params.append("category", category);
      if (statusFilter !== "ALL") params.append("status", statusFilter);

      const res = await apiFetch<{ items: Club[]; total: number }>(`/api/v1/clubs?${params.toString()}`);
      setClubs(res.data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load clubs catalog.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClubs();
  }, [category, statusFilter]);

  const handleProposeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProposing(true);
    setFormError(null);

    try {
      await apiFetch("/api/v1/clubs", {
        method: "POST",
        body: JSON.stringify({
          code: formData.code.toUpperCase().trim(),
          name: formData.name.trim(),
          category: formData.category,
          description: formData.description.trim() || null,
        }),
      });

      setShowProposeModal(false);
      setFormData({ code: "", name: "", category: "TECHNICAL", description: "" });
      loadClubs();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to submit club proposal.");
    } finally {
      setProposing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-950/80 text-indigo-400 border border-indigo-800/60">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-400">Step 10 Active</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            Clubs & Student Societies
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Student governance, technical chapters, cultural societies, and active memberships.
          </p>
        </div>

        <div>
          <button
            onClick={() => setShowProposeModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Found New Club
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadClubs()}
            placeholder="Search clubs by name, code, or domain..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          {CLUB_CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {cat.replace("_", " ")}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="ACTIVE">Active Clubs</option>
          <option value="PENDING_APPROVAL">Pending Review</option>
          <option value="DRAFT">Draft</option>
        </select>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-sm">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
          <p>Loading collegiate clubs directory...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error}
        </div>
      ) : clubs.length === 0 ? (
        <div className="py-20 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
          <svg className="mx-auto h-12 w-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" strokeWidth="1" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
          </svg>
          <p className="text-base font-medium text-slate-300">No organizations found</p>
          <p className="text-xs text-slate-500 mt-1">Be the first to propose a new student chapter or society.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {clubs.map((club) => {
            const isActive = club.status === "ACTIVE";

            return (
              <div
                key={club.id}
                className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-slate-700 transition-all hover:shadow-lg"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {club.category}
                    </span>
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                        isActive
                          ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                          : "bg-amber-950/70 text-amber-400 border border-amber-800/60"
                      }`}
                    >
                      {club.status.replace("_", " ")}
                    </span>
                  </div>

                  <h3 className="text-base font-semibold text-white">
                    {club.name}
                  </h3>
                  <span className="text-xs font-mono text-indigo-400">{club.code}</span>

                  {club.description && (
                    <p className="text-xs text-slate-400 line-clamp-2 mt-2">
                      {club.description}
                    </p>
                  )}

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                    <span>
                      <strong className="text-white font-semibold">{club.members_count}</strong> Active Members
                    </span>
                    <span>
                      <strong className="text-white font-semibold">{club.events_count}</strong> Events Hosted
                    </span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    {club.faculty_advisor_name ? `Advisor: ${club.faculty_advisor_name}` : "Student Body"}
                  </span>
                  <Link
                    href={`/app/clubs/${club.id}`}
                    className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    View & Join →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Propose Club Modal */}
      {showProposeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 className="text-lg font-bold text-white">Found New Student Organization</h2>
              <button
                onClick={() => setShowProposeModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleProposeSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Club Code *
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="e.g. AI-RESEARCH-CLUB"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Club Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Artificial Intelligence & Robotics Society"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  {CLUB_CATEGORIES.filter((c) => c !== "ALL").map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Mission & Description
                </label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Goals, activities, target members..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowProposeModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-xs font-medium text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={proposing}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {proposing ? "Submitting Proposal..." : "Submit Proposal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
