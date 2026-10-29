"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { ClubItem, ClubStatus } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  Building2,
  Users,
  Calendar,
  Plus,
  Search,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  MapPin,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

export default function CampusClubsDirectoryPage() {
  const { user, hasPermission } = useAuth();
  const [clubs, setClubs] = useState<ClubItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Join Club Modal State
  const [joinClubTarget, setJoinClubTarget] = useState<ClubItem | null>(null);
  const [joinLoading, setJoinLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const canCreate = hasPermission("campus.manage_clubs") || hasPermission("*");

  const loadClubs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getClubs();
      if (res.success && res.data) {
        setClubs(res.data);
      } else {
        setError(res.error || "Failed to load clubs");
      }
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClubs();
  }, []);

  const handleRequestMembership = async () => {
    if (!joinClubTarget || !user) return;
    try {
      setJoinLoading(true);
      const res = await campusService.requestMembership(joinClubTarget.id, {
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
        rollNumber: "CS23B101",
        email: user.email,
        department: "Computer Science & Engineering",
        program: "B.Tech Computer Science",
        semester: 5,
      });

      if (res.success) {
        setFeedback(
          `Membership request for ${joinClubTarget.name} has been submitted! Status: PENDING coordinator review.`,
        );
        setJoinClubTarget(null);
        loadClubs();
      } else {
        alert(res.error || "Could not submit join request.");
      }
    } finally {
      setJoinLoading(false);
    }
  };

  const filteredClubs = useMemo(() => {
    return clubs.filter((c) => {
      const matchCat =
        selectedCategory === "ALL" || c.category === selectedCategory;
      const matchQuery =
        searchQuery === "" ||
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.studentLead.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.facultyCoordinator.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchQuery;
    });
  }, [clubs, selectedCategory, searchQuery]);

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/campus"
              className="text-xs text-slate-400 hover:text-indigo-400"
            >
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">
              Clubs & Societies
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <Building2 className="h-6 w-6 text-cyan-400" />
            Clubs & Student Organizations Directory
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Explore active guilds, technical teams, cultural societies, and
            community leadership councils.
          </p>
        </div>

        {canCreate && (
          <Link href="/app/campus/clubs/create">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
            >
              Charter New Club
            </Button>
          </Link>
        )}
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button
            onClick={() => setFeedback(null)}
            className="text-emerald-400 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            "ALL",
            "TECHNICAL",
            "CULTURAL",
            "LITERARY",
            "SPORTS",
            "ENTREPRENEURSHIP",
          ].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                selectedCategory === cat
                  ? "bg-cyan-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {cat === "ALL" ? "All Guilds" : cat}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search club name, code, or lead..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Clubs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredClubs.map((club) => (
          <div
            key={club.id}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col justify-between hover:border-slate-700 hover:shadow-xl transition-all"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {club.code}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    club.status === "ACTIVE"
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                      : "bg-slate-800 text-slate-400 border-slate-700"
                  }`}
                >
                  {club.status}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-white tracking-tight">
                  {club.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1.5 line-clamp-3 leading-relaxed">
                  {club.description}
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800 text-xs text-slate-300">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Student Lead:</span>
                  <span className="font-semibold text-white">
                    {club.studentLead}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Faculty Advisor:</span>
                  <span className="font-medium text-slate-300">
                    {club.facultyCoordinator}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Active Roster:</span>
                  <span className="font-mono font-bold text-cyan-400">
                    {club.membersCount} members
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Established:</span>
                  <span className="font-mono text-slate-400">
                    {club.establishedYear}
                  </span>
                </div>
              </div>

              {club.upcomingEventTitles &&
                club.upcomingEventTitles.length > 0 && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block">
                      Upcoming Activity:
                    </span>
                    <div className="text-[11px] font-semibold text-indigo-300 line-clamp-1">
                      {club.upcomingEventTitles[0]}
                    </div>
                  </div>
                )}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between gap-2">
              <Link
                href={`/app/campus/clubs/${club.id}`}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1"
              >
                Inspect Portal <ChevronRight className="h-3.5 w-3.5" />
              </Link>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setJoinClubTarget(club)}
                className="border-cyan-500/40 text-cyan-300 hover:bg-cyan-950/40 text-xs"
              >
                Request to Join
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Join Club Modal Dialog */}
      <Dialog
        open={Boolean(joinClubTarget)}
        onClose={() => setJoinClubTarget(null)}
        title="Submit Club Membership Request"
      >
        {joinClubTarget && (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
              <div className="font-bold text-white text-sm">
                {joinClubTarget.name}
              </div>
              <div className="text-slate-400">
                Faculty Advisor: {joinClubTarget.facultyCoordinator}
              </div>
              <div className="text-slate-400">
                Meeting Schedule: {joinClubTarget.meetingSchedule}
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              You are requesting to join as{" "}
              <strong>
                {user?.first_name} {user?.last_name}
              </strong>
              . Your application will be forwarded to the Club President and
              Faculty Advisor for verification.
            </p>

            <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-[11px] text-indigo-300">
              Note: Membership requests require faculty coordinator approval.
              Students cannot approve their own membership.
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setJoinClubTarget(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={joinLoading}
                onClick={handleRequestMembership}
                className="bg-cyan-600 hover:bg-cyan-500"
              >
                Submit Request
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
