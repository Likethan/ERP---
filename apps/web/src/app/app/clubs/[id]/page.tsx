"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Club, ClubMembership, CampusEvent } from "@campusos/types";

export default function ClubDetailPage() {
  const params = useParams();
  const router = useRouter();
  const clubId = params.id as string;
  const { hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [club, setClub] = useState<Club | null>(null);
  const [members, setMembers] = useState<ClubMembership[]>([]);
  const [clubEvents, setClubEvents] = useState<CampusEvent[]>([]);

  // Actions
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Membership request role selection
  const [requestedRole, setRequestedRole] = useState("MEMBER");

  const canApproveClub = hasPermission("clubs:approve");
  const canManageMemberships = hasPermission("clubs:manage_memberships");

  const loadClubData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [clubRes, membersRes, eventsRes] = await Promise.all([
        apiFetch<Club>(`/api/v1/clubs/${clubId}`),
        apiFetch<{ items: ClubMembership[] }>(`/api/v1/clubs/${clubId}/members`).catch(() => ({ data: { items: [] } })),
        apiFetch<{ items: CampusEvent[] }>(`/api/v1/events?club_id=${clubId}`).catch(() => ({ data: { items: [] } })),
      ]);

      setClub(clubRes.data);
      setMembers(membersRes.data.items || []);
      setClubEvents(eventsRes.data?.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load club details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (clubId) {
      loadClubData();
    }
  }, [clubId]);

  const handleRequestMembership = async () => {
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/clubs/${clubId}/membership`, {
        method: "POST",
        body: JSON.stringify({ role: requestedRole }),
      });
      setActionSuccess("Membership request submitted! Waiting for chapter leadership approval.");
      loadClubData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to request membership.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleLeaveClub = async () => {
    if (!confirm("Are you sure you want to resign your membership in this organization?")) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/clubs/${clubId}/membership`, { method: "DELETE" });
      setActionSuccess("You have left the organization.");
      loadClubData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to leave club.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReviewMembership = async (membershipId: string, status: "ACTIVE" | "REJECTED") => {
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/clubs/${clubId}/members/${membershipId}/review`, {
        method: "POST",
        body: JSON.stringify({ status }),
      });
      setActionSuccess(`Membership request ${status.toLowerCase()}!`);
      loadClubData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to review membership.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleApproveClub = async () => {
    if (!confirm("Approve this club charter and make it active across the campus?")) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/clubs/${clubId}/approve`, { method: "POST" });
      setActionSuccess("Club charter approved and activated!");
      loadClubData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to approve club.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 text-sm">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
        <p>Loading club charter and roster...</p>
      </div>
    );
  }

  if (error || !club) {
    return (
      <div className="space-y-4">
        <Link href="/app/clubs" className="text-xs text-indigo-400 hover:text-indigo-300">
          ← Back to Clubs
        </Link>
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error || "Club not found"}
        </div>
      </div>
    );
  }

  const isPendingReview = club.status === "PENDING_APPROVAL";
  const userStanding = club.user_membership_status;
  const isMember = userStanding === "ACTIVE";
  const isPendingMember = userStanding === "PENDING";

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/app/clubs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Clubs Directory
        </Link>

        {canApproveClub && isPendingReview && (
          <button
            onClick={handleApproveClub}
            disabled={actionLoading}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-sm transition-colors"
          >
            Approve Club Charter
          </button>
        )}
      </div>

      {actionError && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {actionError}
        </div>
      )}
      {actionSuccess && (
        <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/60 text-xs text-emerald-300">
          {actionSuccess}
        </div>
      )}

      {/* Main Dossier */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {club.category}
              </span>
              <span className="text-xs font-mono font-semibold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900/50">
                {club.code}
              </span>
              <span
                className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${
                  club.status === "ACTIVE"
                    ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                    : "bg-amber-950/70 text-amber-400 border border-amber-800/60"
                }`}
              >
                {club.status.replace("_", " ")}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-white">{club.name}</h1>
            {club.description && (
              <p className="text-sm text-slate-300 whitespace-pre-line pt-1">
                {club.description}
              </p>
            )}
          </div>

          {/* Membership Actions Box */}
          <div className="w-full md:w-72 rounded-xl border border-slate-800 bg-slate-950 p-5 flex flex-col justify-between">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Your Affiliation
              </div>
              <div className="mt-2 text-sm font-semibold text-white">
                {isMember ? (
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    Active Member ({club.user_membership_role || "MEMBER"})
                  </span>
                ) : isPendingMember ? (
                  <span className="text-amber-400 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-amber-400" />
                    Pending Approval
                  </span>
                ) : (
                  <span className="text-slate-500">Not affiliated</span>
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800">
              {isMember ? (
                <button
                  onClick={handleLeaveClub}
                  disabled={actionLoading}
                  className="w-full py-2 rounded-lg border border-slate-800 bg-slate-900 hover:bg-rose-950 hover:border-rose-900 hover:text-rose-300 text-xs font-semibold text-slate-400 transition-colors"
                >
                  Leave Organization
                </button>
              ) : isPendingMember ? (
                <button
                  disabled
                  className="w-full py-2 rounded-lg bg-slate-900 text-xs font-semibold text-slate-500 cursor-not-allowed"
                >
                  Request Awaiting Review
                </button>
              ) : club.status === "ACTIVE" ? (
                <div className="space-y-3">
                  <select
                    value={requestedRole}
                    onChange={(e) => setRequestedRole(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200"
                  >
                    <option value="MEMBER">Join as Member</option>
                    <option value="EVENT_COORDINATOR">Event Coordinator</option>
                    <option value="SECRETARY">Secretary</option>
                  </select>
                  <button
                    onClick={handleRequestMembership}
                    disabled={actionLoading}
                    className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition-colors"
                  >
                    Request Membership
                  </button>
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center">
                  Membership closed (Club is {club.status.toLowerCase()}).
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Club Meta Metrics */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t border-slate-800/80 text-xs text-slate-300">
          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Leadership Roster</span>
            <p className="text-sm font-semibold text-white mt-1">
              {club.student_lead_name || "Elections Pending"}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">Student Chapter Lead</p>
          </div>

          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Faculty Mentor</span>
            <p className="text-sm font-semibold text-white mt-1">
              {club.faculty_advisor_name || "Faculty Body"}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">Charter Faculty Advisor</p>
          </div>

          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Society Statistics</span>
            <p className="text-sm font-semibold text-white mt-1">
              {club.members_count} Members • {club.events_count} Events
            </p>
            <p className="text-xs text-slate-400 mt-0.5">Chartered since {new Date(club.created_at).getFullYear()}</p>
          </div>
        </div>
      </div>

      {/* Chapter Members Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-white">Membership Roster ({members.length})</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Active student members, elected leaders, and pending applicants.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Student</th>
                <th className="py-2.5 px-4">Roll Number</th>
                <th className="py-2.5 px-4">Role</th>
                <th className="py-2.5 px-4">Standing</th>
                <th className="py-2.5 px-4">Joined</th>
                {canManageMemberships && <th className="py-2.5 px-4 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/20 text-slate-300">
              {members.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No members recorded yet.
                  </td>
                </tr>
              ) : (
                members.map((mem) => {
                  const isPending = mem.status === "PENDING";
                  return (
                    <tr key={mem.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-medium text-white">
                        {mem.student_name || "Student"}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-400">
                        {mem.student_roll_number || "—"}
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-indigo-400">
                        {mem.role}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            mem.status === "ACTIVE"
                              ? "bg-emerald-950 text-emerald-400"
                              : mem.status === "PENDING"
                              ? "bg-amber-950 text-amber-400"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {mem.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-400">
                        {mem.joined_at ? new Date(mem.joined_at).toLocaleDateString() : "—"}
                      </td>
                      {canManageMemberships && (
                        <td className="py-2.5 px-4 text-right">
                          {isPending ? (
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleReviewMembership(mem.id, "ACTIVE")}
                                className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[11px]"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleReviewMembership(mem.id, "REJECTED")}
                                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-rose-950 hover:text-rose-300 text-slate-300 text-[11px]"
                              >
                                Decline
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-500 text-[11px]">Approved</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
