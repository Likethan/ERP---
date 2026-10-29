"use client";

import React, { useState, useEffect } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import { SportsAchievementItem } from "@/types/sports";
import {
  Award,
  Medal,
  Plus,
  Search,
  Star,
  CheckCircle2,
  Calendar,
} from "lucide-react";

export default function AchievementsPage() {
  const [achievements, setAchievements] = useState<SportsAchievementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [awardFilter, setAwardFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    participantName: "",
    competitionName: "South Zone Inter-University Tournament",
    sport: "Football",
    title: "Gold Medal & Best Defender of the Tournament",
    medal: "GOLD",
    level: "ZONE",
    awardDate: "2026-10-18",
    certificateNumber: "CERT-SZ-2026-091",
    citation: "Demonstrated exceptional backline leadership and conceded zero open-play goals.",
  });

  useEffect(() => {
    loadAchievements();
  }, []);

  const loadAchievements = async () => {
    setLoading(true);
    const res = await sportsService.listAchievements();
    if (res.success && res.data) {
      setAchievements(res.data);
    }
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.participantName.trim()) return;

    const res = await sportsService.createAchievement({
      recipientType: "PARTICIPANT",
      participantId: `part-${Date.now()}`,
      participantName: formData.participantName,
      competitionName: formData.competitionName,
      sport: formData.sport,
      title: formData.title,
      medal: formData.medal,
      level: formData.level,
      awardDate: formData.awardDate,
      certificateNumber: formData.certificateNumber,
      citation: formData.citation,
    });

    if (res.success && res.data) {
      setToastMessage(`Achievement for ${res.data.participantName} archived into university hall of fame.`);
      setIsModalOpen(false);
      loadAchievements();
    }
  };

  const filtered = achievements.filter((a) => {
    const matchesSearch =
      (a.participantName || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (a.competitionName || "").toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = awardFilter === "all" || (a.medal && a.medal.toLowerCase() === awardFilter.toLowerCase());
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Athletic Honors & Hall of Fame
          </h1>
          <p className="text-sm text-slate-500">
            Recognized university records, championship medals, and verified state/national citations.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Record Achievement
        </button>
      </div>

      {toastMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-lg">
            <Medal className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Gold Medals</p>
            <p className="text-xl font-bold text-slate-900">
              {achievements.filter((a) => a.medal === "GOLD").length} Laurels
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-slate-100 text-slate-600 rounded-lg">
            <Medal className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Silver Medals</p>
            <p className="text-xl font-bold text-slate-900">
              {achievements.filter((a) => a.medal === "SILVER").length} Laurels
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-orange-50 text-orange-600 rounded-lg">
            <Medal className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Bronze Medals</p>
            <p className="text-xl font-bold text-slate-900">
              {achievements.filter((a) => a.medal === "BRONZE").length} Laurels
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg">
            <Star className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">State / University Honors</p>
            <p className="text-xl font-bold text-slate-900">
              {achievements.filter((a) => a.level === "STATE" || a.level === "NATIONAL").length} Citations
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search honors by athlete name, citation, or tournament..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={awardFilter}
          onChange={(e) => setAwardFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
        >
          <option value="all">All Award Types</option>
          <option value="gold">Gold Medal</option>
          <option value="silver">Silver Medal</option>
          <option value="bronze">Bronze Medal</option>
        </select>
      </div>

      {/* Achievements List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((item) => {
          return (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {item.sport}
                  </span>
                  <span
                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wide ${
                      item.medal === "GOLD"
                        ? "bg-amber-100 text-amber-900 border border-amber-300"
                        : item.medal === "SILVER"
                        ? "bg-slate-200 text-slate-800"
                        : "bg-orange-100 text-orange-900"
                    }`}
                  >
                    {item.medal || item.level}
                  </span>
                </div>

                <h3 className="font-bold text-slate-900 mt-3 text-base">{item.title}</h3>
                <p className="text-xs text-indigo-600 font-semibold mt-0.5">{item.participantName}</p>

                <div className="mt-3 text-xs text-slate-600 space-y-1.5">
                  <p className="text-slate-500 font-medium">{item.competitionName}</p>
                  {item.citation && (
                    <blockquote className="italic border-l-2 border-indigo-400 pl-2 text-slate-600 text-[11px] my-2">
                      &quot;{item.citation}&quot;
                    </blockquote>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span className="flex items-center gap-1 font-mono">
                  <Award className="w-3.5 h-3.5 text-slate-400" />
                  {item.certificateNumber || "N/A"}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  {item.awardDate}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Record Achievement */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Record Athletic Honor / Laurels</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Athlete Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rohan Sharma"
                  value={formData.participantName}
                  onChange={(e) => setFormData({ ...formData, participantName: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Medal</label>
                  <select
                    value={formData.medal}
                    onChange={(e) => setFormData({ ...formData, medal: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="GOLD">Gold Medal</option>
                    <option value="SILVER">Silver Medal</option>
                    <option value="BRONZE">Bronze Medal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Sport Category</label>
                  <select
                    value={formData.sport}
                    onChange={(e) => setFormData({ ...formData, sport: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="Football">Football</option>
                    <option value="Cricket">Cricket</option>
                    <option value="Basketball">Basketball</option>
                    <option value="Badminton">Badminton</option>
                    <option value="Athletics">Athletics</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Award Title</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Competition / Meet</label>
                <input
                  type="text"
                  required
                  value={formData.competitionName}
                  onChange={(e) => setFormData({ ...formData, competitionName: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Award Date</label>
                  <input
                    type="date"
                    required
                    value={formData.awardDate}
                    onChange={(e) => setFormData({ ...formData, awardDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Certificate Number</label>
                  <input
                    type="text"
                    required
                    value={formData.certificateNumber}
                    onChange={(e) => setFormData({ ...formData, certificateNumber: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Citation / Remarks</label>
                <textarea
                  rows={2}
                  value={formData.citation}
                  onChange={(e) => setFormData({ ...formData, citation: e.target.value })}
                  className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Save Citation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
