"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  ClubItem,
  ClubMemberItem,
  CampusEventItem,
  AnnouncementItem,
  ClubRole,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  Building2,
  Users,
  Calendar,
  Clock,
  MapPin,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  UserCheck,
  ShieldCheck,
  ChevronRight,
  History,
  Award,
  Crown,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

interface ClubDetailPageProps {
  params: Promise<{ id: string }>;
}

const ALL_ROLES: ClubRole[] = [
  "CLUB_PRESIDENT",
  "VICE_PRESIDENT",
  "SECRETARY",
  "TREASURER",
  "EVENT_COORDINATOR",
  "MEMBER",
];

export default function ClubDetailPage({ params }: ClubDetailPageProps) {
  const resolvedParams = use(params);
  const clubId = resolvedParams.id;
  const { user, hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [club, setClub] = useState<ClubItem | null>(null);
  const [members, setMembers] = useState<ClubMemberItem[]>([]);
  const [events, setEvents] = useState<CampusEventItem[]>([]);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);

  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "members"
    | "events"
    | "announcements"
    | "leadership"
    | "history"
  >("overview");

  // Actions
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Role Elevation Dialog
  const [roleMember, setRoleMember] = useState<ClubMemberItem | null>(null);
  const [selectedRole, setSelectedRole] = useState<ClubRole>("MEMBER");

  // Rejection Dialog
  const [rejectMember, setRejectMember] = useState<ClubMemberItem | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const canManageMembers =
    hasPermission("campus.manage_memberships") ||
    hasPermission("campus.manage_clubs") ||
    hasPermission("*");

  const loadClubData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getClubById(clubId);
      if (res.success && res.data) {
        setClub(res.data.club);
        setMembers(res.data.members);
        setEvents(res.data.events);
        setAnnouncements(res.data.announcements);
      } else {
        setError(res.error || "Club not found");
      }
    } catch (e: any) {
      setError(e.message || "Failed to load club details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClubData();
  }, [clubId]);

  const handleApprove = async (memberId: string) => {
    try {
      setActionLoading(true);
      await campusService.approveMembership(
        clubId,
        memberId,
        user?.first_name || "Coordinator",
      );
      setActionMessage("Member approved and added to active roster!");
      loadClubData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectMember) return;
    try {
      setActionLoading(true);
      await campusService.rejectMembership(
        clubId,
        rejectMember.id,
        rejectReason || "Does not meet cohort criteria",
        user?.first_name || "Coordinator",
      );
      setRejectMember(null);
      setRejectReason("");
      setActionMessage("Membership request rejected.");
      loadClubData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleElevateRole = async () => {
    if (!roleMember) return;
    try {
      setActionLoading(true);
      await campusService.updateMemberRole(
        clubId,
        roleMember.id,
        selectedRole,
        user?.first_name || "Coordinator",
      );
      setRoleMember(null);
      setActionMessage(`Member role updated to ${selectedRole}!`);
      loadClubData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleStudentJoin = async () => {
    if (!user) return;
    try {
      setActionLoading(true);
      const res = await campusService.requestMembership(clubId, {
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
        rollNumber: "CS23B101",
        email: user.email,
        department: "Computer Science & Engineering",
        program: "B.Tech Computer Science",
        semester: 5,
      });

      if (res.success) {
        setActionMessage(
          "Join request submitted. Pending coordinator verification.",
        );
        loadClubData();
      } else {
        alert(res.error || "Could not submit request.");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleStudentLeave = async () => {
    const myMembership = members.find(
      (m) => m.studentId === user?.id && m.status === "ACTIVE",
    );
    if (!myMembership) return;
    if (
      !confirm("Are you sure you want to resign your membership in this club?")
    )
      return;

    try {
      setActionLoading(true);
      await campusService.leaveClub(
        clubId,
        myMembership.id,
        user?.first_name || "Student",
      );
      setActionMessage("You have resigned from this club.");
      loadClubData();
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
          <span className="text-xs">Loading guild operations...</span>
        </div>
      </div>
    );
  }

  if (error || !club) {
    return (
      <div className="p-8 text-center space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 max-w-xl mx-auto my-12">
        <AlertTriangle className="h-10 w-10 text-rose-400 mx-auto" />
        <h2 className="text-base font-bold text-white">Club Not Found</h2>
        <p className="text-xs text-slate-400">
          {error || "Requested club does not exist."}
        </p>
        <Link href="/app/campus/clubs">
          <Button variant="outline" size="sm">
            Back to Clubs Directory
          </Button>
        </Link>
      </div>
    );
  }

  const myMembership = members.find((m) => m.studentId === user?.id);
  const activeMembers = members.filter((m) => m.status === "ACTIVE");
  const pendingMembers = members.filter((m) => m.status === "PENDING");

  const leadershipRoles: ClubRole[] = [
    "FACULTY_COORDINATOR",
    "CLUB_PRESIDENT",
    "VICE_PRESIDENT",
    "SECRETARY",
    "TREASURER",
    "EVENT_COORDINATOR",
  ];

  const leaders = members.filter(
    (m) => leadershipRoles.includes(m.role) && m.status === "ACTIVE",
  );

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <Link
          href="/app/campus/clubs"
          className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Clubs Directory
        </Link>

        <div className="flex items-center gap-2">
          {!myMembership && (
            <Button
              variant="primary"
              size="sm"
              isLoading={actionLoading}
              onClick={handleStudentJoin}
              className="bg-cyan-600 hover:bg-cyan-500 shadow-md shadow-cyan-600/30"
            >
              Request Membership
            </Button>
          )}

          {myMembership?.status === "PENDING" && (
            <span className="text-xs font-semibold px-3 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Application Pending Approval
            </span>
          )}

          {myMembership?.status === "ACTIVE" && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" /> Member (
                {myMembership.role})
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleStudentLeave}
                className="border-slate-800 text-slate-400 hover:text-rose-400 text-xs"
              >
                Leave Club
              </Button>
            </div>
          )}
        </div>
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-emerald-400 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Polish Club Banner Header */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded bg-cyan-500/20 px-2.5 py-0.5 text-xs font-mono font-bold text-cyan-300 border border-cyan-500/30">
            {club.code}
          </span>
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            {club.category}
          </span>
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
              club.status === "ACTIVE"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                : "bg-slate-800 text-slate-400"
            }`}
          >
            {club.status}
          </span>
        </div>

        <h1 className="text-2xl font-black text-white tracking-tight">
          {club.name}
        </h1>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          {club.description}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">
              Faculty Coordinator
            </span>
            <span className="font-semibold text-white mt-0.5 block">
              {club.facultyCoordinator}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {club.facultyCoordinatorEmail}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">
              Student Lead
            </span>
            <span className="font-semibold text-white mt-0.5 block">
              {club.studentLead}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {club.studentLeadRollNo}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">
              Meeting Schedule
            </span>
            <span className="font-medium text-slate-300 mt-0.5 block">
              {club.meetingSchedule}
            </span>
            <span className="text-[10px] text-slate-500">
              Venue: {club.meetingVenue}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">
              Charter History
            </span>
            <span className="font-mono text-cyan-400 mt-0.5 block font-bold">
              Est. {club.establishedYear}
            </span>
            <span className="text-[10px] text-slate-500">
              {activeMembers.length} active members
            </span>
          </div>
        </div>
      </div>

      {/* 6 Tabs Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: "overview", label: "Overview" },
          { id: "members", label: `Members (${activeMembers.length})` },
          { id: "events", label: `Club Events (${events.length})` },
          {
            id: "announcements",
            label: `Announcements (${announcements.length})`,
          },
          { id: "leadership", label: `Leadership (${leaders.length})` },
          { id: "history", label: "History & Charter" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
              activeTab === tab.id
                ? "bg-cyan-600 text-white shadow-sm shadow-cyan-600/30"
                : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
              <h3 className="text-sm font-bold text-white">
                Guild Charter & Mission
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {club.description}
              </p>
            </div>

            {/* Referenced Events */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white">
                  Organized Campus Events
                </h3>
                <span className="text-xs text-slate-400">
                  {events.length} events scheduled
                </span>
              </div>

              <div className="space-y-3">
                {events.map((e) => (
                  <Link
                    key={e.id}
                    href={`/app/campus/events/${e.id}`}
                    className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 flex items-center justify-between transition-colors block"
                  >
                    <div>
                      <div className="text-xs font-bold text-white">
                        {e.title}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        {e.startDate} • {e.venue} • {e.registeredCount} /{" "}
                        {e.capacity} participants
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-500" />
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Quick Metrics */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">
                Membership Snapshot
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Active Members:</span>
                  <span className="font-mono font-bold text-cyan-400">
                    {activeMembers.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Pending Requests:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {pendingMembers.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Charter Size:</span>
                  <span className="font-mono font-bold text-white">
                    {members.length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB: MEMBERS */}
      {activeTab === "members" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-sm font-bold text-white">
                Official Membership Roster
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Role designations and membership authorization states
              </p>
            </div>
          </div>

          {/* Pending Applications Section for Coordinators */}
          {canManageMembers && pendingMembers.length > 0 && (
            <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/20 space-y-3">
              <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                Pending Join Requests ({pendingMembers.length})
              </h4>
              <div className="divide-y divide-amber-900/40">
                {pendingMembers.map((m) => (
                  <div
                    key={m.id}
                    className="py-2.5 flex items-center justify-between gap-4 text-xs"
                  >
                    <div>
                      <span className="font-bold text-white">
                        {m.studentName}
                      </span>
                      <span className="text-slate-400 font-mono ml-2">
                        {m.rollNumber} • {m.department}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="primary"
                        isLoading={actionLoading}
                        onClick={() => handleApprove(m.id)}
                        className="bg-emerald-600 hover:bg-emerald-500 text-xs py-1"
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setRejectMember(m)}
                        className="border-rose-900 text-rose-400 hover:bg-rose-950 text-xs py-1"
                      >
                        Reject
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Members Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Student</th>
                  <th className="p-3">Roll Number</th>
                  <th className="p-3">Department</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Joined Date</th>
                  <th className="p-3">Status</th>
                  {canManageMembers && (
                    <th className="p-3 text-right">Actions</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {activeMembers.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30">
                    <td className="p-3 font-semibold text-white">
                      {m.studentName}
                    </td>
                    <td className="p-3 font-mono text-slate-300">
                      {m.rollNumber}
                    </td>
                    <td className="p-3 text-slate-400">{m.department}</td>
                    <td className="p-3">
                      <span className="font-bold text-cyan-300">
                        {m.role.replace("_", " ")}
                      </span>
                    </td>
                    <td className="p-3 text-slate-500 font-mono">
                      {m.joinedDate}
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">
                        {m.status}
                      </span>
                    </td>
                    {canManageMembers && (
                      <td className="p-3 text-right">
                        <button
                          onClick={() => {
                            setRoleMember(m);
                            setSelectedRole(m.role);
                          }}
                          className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                        >
                          Change Role
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: EVENTS */}
      {activeTab === "events" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white">
              Club Calendar & Competitions
            </h3>
            <Link
              href="/app/campus/events/create"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
            >
              + Create Event Under This Club
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {events.map((e) => (
              <div
                key={e.id}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                      {e.category}
                    </span>
                    <span className="text-[10px] font-bold text-emerald-400">
                      {e.status}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-1.5">
                    {e.title}
                  </h4>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                    {e.description}
                  </p>
                </div>
                <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span>
                    {e.startDate} • {e.venue}
                  </span>
                  <Link
                    href={`/app/campus/events/${e.id}`}
                    className="text-indigo-400 hover:text-indigo-300 font-semibold"
                  >
                    Inspect →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB: LEADERSHIP */}
      {activeTab === "leadership" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Crown className="h-4 w-4 text-amber-400" />
            Executive Leadership & Advisory Council
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Faculty Advisor Card */}
            <div className="p-4 rounded-xl border border-indigo-500/40 bg-indigo-950/20 space-y-2">
              <span className="text-[10px] font-mono font-bold text-indigo-300 uppercase">
                Faculty Coordinator
              </span>
              <div className="text-sm font-bold text-white">
                {club.facultyCoordinator}
              </div>
              <div className="text-xs text-slate-400">
                {club.facultyCoordinatorEmail}
              </div>
              <div className="text-[10px] text-indigo-400 pt-2 border-t border-indigo-900/40">
                Institutional Oversight & Approval Authority
              </div>
            </div>

            {/* Student Executive Cards */}
            {leaders.map((leader) => (
              <div
                key={leader.id}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-cyan-300 uppercase">
                    {leader.role.replace("_", " ")}
                  </span>
                  <Award className="h-4 w-4 text-cyan-400" />
                </div>
                <div className="text-sm font-bold text-white">
                  {leader.studentName}
                </div>
                <div className="text-xs text-slate-400">
                  {leader.rollNumber} • {leader.department}
                </div>
                <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-800">
                  Tenure: Since {leader.joinedDate}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB: ANNOUNCEMENTS */}
      {activeTab === "announcements" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">
            Club Announcements & Dispatches
          </h3>
          <div className="space-y-3">
            {announcements.length > 0 ? (
              announcements.map((a) => (
                <div
                  key={a.id}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-950 space-y-1 text-xs"
                >
                  <div className="font-bold text-white">{a.title}</div>
                  <p className="text-slate-400">{a.content}</p>
                  <div className="text-[10px] text-slate-500 font-mono pt-1">
                    Published: {a.publishDate}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">
                No club-specific circulars published yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB: HISTORY */}
      {activeTab === "history" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="h-4 w-4 text-cyan-400" />
            Charter Audit & Membership Log
          </h3>

          <div className="space-y-4 border-l border-slate-800 ml-3 pl-4">
            {club.timeline.map((entry) => (
              <div key={entry.id} className="relative space-y-1 text-xs">
                <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-cyan-500 ring-4 ring-slate-950" />
                <div className="font-bold text-white">{entry.action}</div>
                <div className="text-slate-400">Actor: {entry.actor}</div>
                <div className="text-[10px] text-slate-500 font-mono">
                  {entry.timestamp}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Role Assignment Modal */}
      <Dialog
        open={Boolean(roleMember)}
        onClose={() => setRoleMember(null)}
        title="Elevate or Reassign Member Role"
      >
        {roleMember && (
          <div className="space-y-4">
            <p className="text-xs text-slate-300">
              Assign a new leadership or organizational role to{" "}
              <strong>{roleMember.studentName}</strong>:
            </p>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as ClubRole)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
            >
              {ALL_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRoleMember(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={actionLoading}
                onClick={handleElevateRole}
                className="bg-cyan-600 hover:bg-cyan-500"
              >
                Confirm Role Assignment
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {/* Rejection Modal */}
      <Dialog
        open={Boolean(rejectMember)}
        onClose={() => setRejectMember(null)}
        title="Reject Membership Request"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            Provide a reason for rejecting this student's join application:
          </p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            placeholder="e.g. Club capacity reached for current semester..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRejectMember(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              isLoading={actionLoading}
              onClick={handleReject}
            >
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
