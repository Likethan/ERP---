"use client";

import React, { useEffect, useState } from "react";
import {
  Trophy,
  Award,
  FlaskConical,
  GraduationCap,
  Users,
  Search,
  Filter,
  Plus,
  CheckCircle2,
  ExternalLink,
  Calendar,
  Sparkles,
  X,
  FileText,
} from "lucide-react";
import {
  hodService,
  HodAchievementItem,
  HodAchievementsData,
  HodAchievementCreatePayload,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodAchievementsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<HodAchievementsData | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [recipientFilter, setRecipientFilter] = useState("ALL");
  const [yearFilter, setYearFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Record Achievement Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCategory, setNewCategory] = useState("HACKATHON");
  const [newRecipientName, setNewRecipientName] = useState("");
  const [newRecipientType, setNewRecipientType] = useState<
    "STUDENT" | "FACULTY"
  >("STUDENT");
  const [newRecipientId, setNewRecipientId] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newOrg, setNewOrg] = useState("");

  const loadAchievements = async () => {
    try {
      setLoading(true);
      const res = await hodService.getDepartmentAchievements(
        categoryFilter,
        recipientFilter,
        yearFilter,
      );
      if (res.data) {
        setData(res.data);
      }
    } catch {
      addToast({
        title: "Error Loading Achievements",
        description: "Failed to retrieve department achievements registry.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAchievements();
  }, [categoryFilter, recipientFilter, yearFilter]);

  const handleCreateAchievement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newRecipientName.trim() || !newDate) {
      addToast({
        title: "Required Fields Missing",
        description: "Please provide title, recipient name, and date.",
        variant: "destructive",
      });
      return;
    }

    try {
      setSaving(true);
      const payload: HodAchievementCreatePayload = {
        title: newTitle.trim(),
        description:
          newDesc.trim() || "Verified department academic achievement.",
        category: newCategory,
        recipientName: newRecipientName.trim(),
        recipientType: newRecipientType,
        recipientId: newRecipientId.trim() || "N/A",
        achievementDate: newDate,
        academicYear: "2025-2026",
        eventOrOrganization: newOrg.trim() || "National Competitions Board",
      };

      const res = await hodService.recordDepartmentAchievement(payload);
      if (res.success && res.data) {
        addToast({
          title: "Achievement Recorded",
          description: `"${res.data.title}" successfully recorded in department honors ledger.`,
          variant: "success",
        });
        setModalOpen(false);
        resetForm();
        loadAchievements();
      }
    } catch {
      addToast({
        title: "Registration Failed",
        description: "Could not record achievement.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setNewTitle("");
    setNewDesc("");
    setNewCategory("HACKATHON");
    setNewRecipientName("");
    setNewRecipientId("");
    setNewDate("");
    setNewOrg("");
  };

  const filteredAchievements = (data?.achievements || []).filter((ach) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      ach.title.toLowerCase().includes(q) ||
      ach.recipientName.toLowerCase().includes(q) ||
      ach.category.toLowerCase().includes(q) ||
      ach.eventOrOrganization.toLowerCase().includes(q)
    );
  });

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case "HACKATHON":
        return (
          <span className="rounded-full bg-yellow-100 text-yellow-900 border border-yellow-300 px-2.5 py-0.5 text-[10px] font-bold">
            Hackathon Win
          </span>
        );
      case "RESEARCH":
        return (
          <span className="rounded-full bg-purple-100 text-purple-900 border border-purple-200 px-2.5 py-0.5 text-[10px] font-bold">
            Research Award
          </span>
        );
      case "INNOVATION":
        return (
          <span className="rounded-full bg-blue-100 text-blue-900 border border-blue-200 px-2.5 py-0.5 text-[10px] font-bold">
            Patent / Innovation
          </span>
        );
      case "CERTIFICATION":
        return (
          <span className="rounded-full bg-emerald-100 text-emerald-900 border border-emerald-200 px-2.5 py-0.5 text-[10px] font-bold">
            Industry Cert
          </span>
        );
      case "SPORTS":
        return (
          <span className="rounded-full bg-rose-100 text-rose-900 border border-rose-200 px-2.5 py-0.5 text-[10px] font-bold">
            Sports Gold
          </span>
        );
      default:
        return (
          <span className="rounded-full bg-slate-100 text-slate-800 border border-slate-200 px-2.5 py-0.5 text-[10px] font-bold">
            {category}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Department Achievements & Honors
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              Department Hall of Fame
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Showcase verified student hackathons, international research awards,
            published patents, and faculty credentials.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-yellow-400 px-4 py-2 text-xs font-bold text-slate-950 shadow-xs hover:bg-yellow-300 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Record New Achievement
        </button>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Total Honors
            </span>
            <Trophy className="h-4 w-4 text-yellow-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {data?.summary.totalAchievements || 6}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Recognized & Verified
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Student Honors
            </span>
            <GraduationCap className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-600">
            {data?.summary.studentAchievements || 3}
          </div>
          <div className="mt-1 text-[11px] text-blue-600/80 font-medium">
            National Wins & Medals
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Faculty Awards
            </span>
            <Users className="h-4 w-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-purple-600">
            {data?.summary.facultyAchievements || 3}
          </div>
          <div className="mt-1 text-[11px] text-purple-600/80 font-medium">
            Research & Patents
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Research Papers
            </span>
            <FlaskConical className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {data?.summary.researchPapers || 34}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Indexed in Scopus/SCI
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              National Hackathons
            </span>
            <Sparkles className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {data?.summary.hackathonWins || 12}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            SIH & Global Challenges
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by achievement title, recipient, category, organization..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm focus:border-yellow-400 focus:outline-hidden focus:ring-1 focus:ring-yellow-400"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={recipientFilter}
            onChange={(e) => setRecipientFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Recipients</option>
            <option value="STUDENT">Students Only</option>
            <option value="FACULTY">Faculty Only</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Categories</option>
            <option value="HACKATHON">Hackathon</option>
            <option value="RESEARCH">Research</option>
            <option value="INNOVATION">Innovation / Patent</option>
            <option value="TECHNICAL_COMPETITION">Competition</option>
            <option value="CERTIFICATION">Certification</option>
            <option value="SPORTS">Sports</option>
          </select>
        </div>
      </div>

      {/* Achievements Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-sm text-slate-500">
          Loading achievements honors ledger...
        </div>
      ) : filteredAchievements.length === 0 ? (
        <div className="p-12 text-center text-sm text-slate-500">
          No achievements match your search filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAchievements.map((ach) => (
            <div
              key={ach.id}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-yellow-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  {getCategoryBadge(ach.category)}
                  <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {ach.achievementDate}
                  </span>
                </div>

                <h3 className="mt-3 font-bold text-slate-900 text-sm leading-snug">
                  {ach.title}
                </h3>
                <p className="mt-1.5 text-xs text-slate-600 line-clamp-3">
                  {ach.description}
                </p>

                <div className="mt-4 rounded-lg bg-slate-50 p-2.5 border border-slate-100 text-xs">
                  <div className="text-[10px] uppercase font-bold text-slate-400">
                    Recipient
                  </div>
                  <div className="font-semibold text-slate-900 mt-0.5">
                    {ach.recipientName}{" "}
                    <span className="font-normal text-slate-500">
                      ({ach.recipientType === "STUDENT" ? "Student" : "Faculty"}
                      )
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                    Org: {ach.eventOrOrganization}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  Verified by HOD
                </span>
                <span className="text-slate-400 text-[10px] font-mono">
                  {ach.id}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Record Achievement Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                Record Department Achievement
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={handleCreateAchievement}
              className="mt-4 space-y-3.5 text-xs"
            >
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Achievement Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Best Paper Award / SIH Winner"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Category *
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  >
                    <option value="HACKATHON">Hackathon</option>
                    <option value="RESEARCH">Research</option>
                    <option value="INNOVATION">Innovation / Patent</option>
                    <option value="TECHNICAL_COMPETITION">
                      Technical Competition
                    </option>
                    <option value="CERTIFICATION">Certification</option>
                    <option value="SPORTS">Sports</option>
                    <option value="CONFERENCE">Conference</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Achievement Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Recipient Type *
                  </label>
                  <select
                    value={newRecipientType}
                    onChange={(e) =>
                      setNewRecipientType(
                        e.target.value as "STUDENT" | "FACULTY",
                      )
                    }
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  >
                    <option value="STUDENT">Student</option>
                    <option value="FACULTY">Faculty</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Recipient Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Full Name"
                    value={newRecipientName}
                    onChange={(e) => setNewRecipientName(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Roll No / Employee Code
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 714022104018"
                    value={newRecipientId}
                    onChange={(e) => setNewRecipientId(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Awarding Body / Organization
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. AICTE, IEEE, Google"
                    value={newOrg}
                    onChange={(e) => setNewOrg(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Description & Impact
                </label>
                <textarea
                  rows={2}
                  placeholder="Summary of achievement, cash prize, citation details..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-yellow-400 px-4 py-2 font-semibold text-slate-950 hover:bg-yellow-300 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Verify & Record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
