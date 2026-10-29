"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import { SportsCompetitionItem } from "@/types/sports";
import {
  Trophy,
  Plus,
  Search,
  Calendar,
  Users,
  ArrowRight,
  Shield,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

export default function CompetitionsPage() {
  const router = useRouter();
  const [competitions, setCompetitions] = useState<SportsCompetitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [sportFilter, setSportFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    sport: "Football",
    tournamentFormat: "ROUND_ROBIN",
    startDate: "2026-11-10",
    endDate: "2026-11-25",
    maxParticipants: 8,
    pointsForWin: 3,
    pointsForDraw: 1,
    pointsForLoss: 0,
  });

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    setLoading(true);
    const res = await sportsService.listCompetitions();
    if (res.success && res.data) {
      setCompetitions(res.data);
    }
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await sportsService.createCompetition({
      name: formData.name,
      sport: formData.sport,
      tournamentFormat: formData.tournamentFormat as any,
      startDate: formData.startDate,
      endDate: formData.endDate,
      maxParticipants: Number(formData.maxParticipants),
      pointsForWin: Number(formData.pointsForWin),
      pointsForDraw: Number(formData.pointsForDraw),
      pointsForLoss: Number(formData.pointsForLoss),
    });

    if (res.success && res.data) {
      setActionMessage(`Competition "${res.data.name}" created successfully.`);
      setIsModalOpen(false);
      loadCompetitions();
    }
  };

  const handleGenerateFixtures = async (compId: string, compName: string) => {
    if (
      !confirm(
        `Generate official match fixtures for "${compName}"? This will compute tournament pairings and prevent conflicting venue bookings.`
      )
    ) {
      return;
    }

    const res = await sportsService.generateFixtures(compId);
    if (res.success && res.data) {
      setActionMessage(`Generated ${res.data.length} match fixtures for "${compName}".`);
      loadCompetitions();
      router.push(`/app/sports/fixtures?competition=${compId}`);
    }
  };

  const filtered = competitions.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSport = sportFilter === "all" || c.sport.toLowerCase() === sportFilter.toLowerCase();
    return matchesSearch && matchesSport;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Tournaments & Competitions Engine
          </h1>
          <p className="text-sm text-slate-500">
            Internal collegiate leagues, inter-university championships, and automated fixture generators.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/app/sports/fixtures"
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-sm font-medium shadow-sm transition-colors"
          >
            <Calendar className="w-4 h-4 text-indigo-600" />
            Match Fixtures & Calendar
          </Link>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Tournament
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Search and Sport Filter */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search competitions by name, tournament type or venue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={sportFilter}
          onChange={(e) => setSportFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
        >
          <option value="all">All Sports</option>
          <option value="Cricket">Cricket</option>
          <option value="Football">Football</option>
          <option value="Badminton">Badminton</option>
          <option value="Basketball">Basketball</option>
        </select>
      </div>

      {/* Competitions Grid */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
          <p className="mt-2 text-sm text-slate-500">Loading tournaments...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <Trophy className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="mt-2 text-sm font-medium text-slate-700">No competitions found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((comp) => {
            return (
              <div
                key={comp.id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {comp.sport}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-semibold capitalize ${
                        comp.status === "IN_PROGRESS"
                          ? "bg-amber-100 text-amber-800"
                          : comp.status === "REGISTRATION_OPEN"
                          ? "bg-blue-100 text-blue-800"
                          : comp.status === "COMPLETED"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {comp.status.replace("_", " ").toLowerCase()}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 mt-2 text-base">{comp.name}</h3>

                  <div className="mt-3 inline-block">
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 capitalize">
                      Format: {comp.tournamentFormat.replace("_", " ").toLowerCase()}
                    </span>
                  </div>

                  <div className="mt-4 space-y-2 text-xs text-slate-600">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        {comp.startDate} to {comp.endDate}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Shield className="w-3.5 h-3.5 text-slate-400" />
                      <span>Code: {comp.code}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Capacity: {comp.registeredCount || 4} / {comp.maxParticipants} Registered Squads
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 pt-1">
                      Scoring Rules: Win = {comp.pointsForWin} pts | Draw = {comp.pointsForDraw} pts | Loss ={" "}
                      {comp.pointsForLoss} pts
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 space-y-2">
                  <button
                    onClick={() => handleGenerateFixtures(comp.id, comp.name)}
                    className="w-full inline-flex items-center justify-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                    Auto-Generate Fixtures
                  </button>

                  <div className="flex items-center justify-between text-xs pt-1">
                    <Link
                      href={`/app/sports/fixtures?competition=${comp.id}`}
                      className="font-medium text-slate-600 hover:text-indigo-600"
                    >
                      View Fixtures
                    </Link>
                    <Link
                      href={`/app/sports/results?competition=${comp.id}`}
                      className="font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                    >
                      Standings & Scores
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Create Competition */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Create Campus Tournament</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tournament Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Inter-Departmental Spring Championship"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
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
                    <option value="Volleyball">Volleyball</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Tournament Format</label>
                  <select
                    value={formData.tournamentFormat}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        tournamentFormat: e.target.value,
                      })
                    }
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="ROUND_ROBIN">Round Robin League</option>
                    <option value="KNOCKOUT">Single Elimination Knockout</option>
                    <option value="LEAGUE_PLUS_PLAYOFFS">League + Playoffs</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={formData.startDate}
                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    required
                    value={formData.endDate}
                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Max Teams</label>
                <input
                  type="number"
                  min={2}
                  max={32}
                  value={formData.maxParticipants}
                  onChange={(e) => setFormData({ ...formData, maxParticipants: Number(e.target.value) })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Win Points</label>
                  <input
                    type="number"
                    value={formData.pointsForWin}
                    onChange={(e) => setFormData({ ...formData, pointsForWin: Number(e.target.value) })}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Draw Points</label>
                  <input
                    type="number"
                    value={formData.pointsForDraw}
                    onChange={(e) => setFormData({ ...formData, pointsForDraw: Number(e.target.value) })}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Loss Points</label>
                  <input
                    type="number"
                    value={formData.pointsForLoss}
                    onChange={(e) => setFormData({ ...formData, pointsForLoss: Number(e.target.value) })}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1"
                  />
                </div>
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
                  Initialize Competition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
