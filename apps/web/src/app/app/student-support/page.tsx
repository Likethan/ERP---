"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import {
  SupportTelemetryMetrics,
  MentoringSessionItem,
  SupportFollowUpItem,
  SupportReferralItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Heart,
  Users,
  UserCheck,
  Calendar,
  Sparkles,
  ArrowRightLeft,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ShieldCheck,
  GraduationCap,
  Target,
  Search,
} from "lucide-react";

export default function StudentSupportDashboardPage() {
  const [metrics, setMetrics] = useState<SupportTelemetryMetrics | null>(null);
  const [recentSessions, setRecentSessions] = useState<MentoringSessionItem[]>([]);
  const [urgentFollowUps, setUrgentFollowUps] = useState<SupportFollowUpItem[]>([]);
  const [activeReferrals, setActiveReferrals] = useState<SupportReferralItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);
    try {
      const [m, sessions, followUps, referrals] = await Promise.all([
        StudentSupportService.getTelemetryMetrics(),
        StudentSupportService.getMentoringSessions(),
        StudentSupportService.getFollowUps({ status: "PENDING" }),
        StudentSupportService.getReferrals(),
      ]);
      setMetrics(m);
      setRecentSessions(sessions.slice(0, 5));
      setUrgentFollowUps(followUps.slice(0, 5));
      setActiveReferrals(referrals.slice(0, 5));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError("Unable to load student support dashboard. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Breadcrumbs */}
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Counselling & Mentoring", href: "/app/student-support" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-indigo-400" />
              Student Support, Mentoring & Personal Development
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              One Campus. One System. One Source of Truth. Coordinated faculty mentoring, counselling, and individual student growth.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/app/student-support/mentor">
              <Button variant="outline" className="border-slate-700 hover:bg-slate-800 text-xs">
                <UserCheck className="mr-1.5 h-3.5 w-3.5 text-indigo-400" />
                My Mentor
              </Button>
            </Link>
            <Link href="/app/student-support/counselling">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white">
                <Heart className="mr-1.5 h-3.5 w-3.5" />
                Book Counselling
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <StudentSupportNav />

      {/* Strict Confidentiality Banner */}
      <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-4 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-300">
            <span className="font-semibold text-white">CampusOS Privacy Boundary:</span> Mentoring summaries and student development plans are accessible to authorized faculty mentors and students. Clinical counselling records are stored separately under dedicated end-to-end access control and are restricted exclusively to licensed counselling professionals.
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-800/50 bg-red-950/30 p-4 text-xs text-red-300 flex items-center justify-between">
          <span>{error}</span>
          <Button size="sm" variant="outline" onClick={loadDashboardData} className="text-xs">
            Retry
          </Button>
        </div>
      )}

      {/* Telemetry KPI Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Mentorships"
          value={loading ? "..." : (metrics?.active_mentor_assignments ?? 0).toLocaleString()}
          icon={<Users className="h-5 w-5 text-indigo-400" />}
          description="Assigned faculty-student connections"
        />
        <StatCard
          title="Unassigned Students"
          value={loading ? "..." : (metrics?.unassigned_students_count ?? 0).toLocaleString()}
          icon={<AlertTriangle className="h-5 w-5 text-amber-400" />}
          description="Awaiting faculty mentor allocation"
        />
        <StatCard
          title="Sessions Completed"
          value={loading ? "..." : (metrics?.mentoring_sessions_completed ?? 0).toLocaleString()}
          icon={<Calendar className="h-5 w-5 text-emerald-400" />}
          description="Recorded mentorship interactions"
        />
        <StatCard
          title="Counselling Utilization"
          value={loading ? "..." : `${metrics?.appointment_utilization_rate_pct ?? 0}%`}
          icon={<Heart className="h-5 w-5 text-rose-400" />}
          description="Service capacity booking index"
        />
        <StatCard
          title="Pending Referrals"
          value={loading ? "..." : (metrics?.pending_support_referrals ?? 0).toLocaleString()}
          icon={<ArrowRightLeft className="h-5 w-5 text-cyan-400" />}
          description="Inter-service student referrals"
        />
        <StatCard
          title="Overdue Follow-ups"
          value={loading ? "..." : (metrics?.overdue_follow_up_actions ?? 0).toLocaleString()}
          icon={<Clock className="h-5 w-5 text-orange-400" />}
          description="Pending action items requiring check-in"
        />
        <StatCard
          title="Goals Completed"
          value={loading ? "..." : (metrics?.development_goals_completed ?? 0).toLocaleString()}
          icon={<CheckCircle2 className="h-5 w-5 text-teal-400" />}
          description="Student milestone achievements"
        />
        <StatCard
          title="Avg IDP Progress"
          value={loading ? "..." : `${metrics?.average_development_progress_pct ?? 0}%`}
          icon={<Target className="h-5 w-5 text-purple-400" />}
          description="Institutional growth plan metric"
        />
      </div>

      {/* Main Two-Column Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left 2 Columns: Recent Mentoring Sessions */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-indigo-400" />
                  Recent Mentoring Sessions
                </h2>
                <p className="text-xs text-slate-400">Structured faculty mentoring and progress reviews</p>
              </div>
              <Link href="/app/student-support/sessions">
                <Button variant="ghost" size="sm" className="text-xs text-indigo-400 hover:text-indigo-300">
                  View All <ChevronRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>

            {loading ? (
              <div className="py-8 text-center text-xs text-slate-500">Loading session schedule...</div>
            ) : recentSessions.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">No recent mentoring sessions recorded.</div>
            ) : (
              <div className="divide-y divide-slate-800">
                {recentSessions.map((session) => (
                  <div key={session.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-slate-200">{session.title}</span>
                        <Badge
                          variant="outline"
                          className={
                            session.status === "COMPLETED"
                              ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                              : session.status === "SCHEDULED"
                              ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                              : "border-slate-700 text-slate-400 text-[10px]"
                          }
                        >
                          {session.status}
                        </Badge>
                        <span className="text-[11px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                          {session.session_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-3">
                        <span>Mentor: {session.mentor_name ?? "Assigned Faculty"}</span>
                        <span>•</span>
                        <span>{new Date(session.scheduled_start || session.sessionDate || "").toLocaleDateString()} at {new Date(session.scheduled_start || session.sessionDate || "").toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <span>•</span>
                        <span>{session.location || session.locationOrLink || "Online"}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {(session.action_items_count ?? 0) > 0 && (
                        <span className="text-[11px] text-indigo-300 bg-indigo-950/60 px-2 py-1 rounded border border-indigo-800/40">
                          {session.action_items_count} Action {session.action_items_count === 1 ? 'Item' : 'Items'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Active Support Referrals Queue */}
          <Card className="border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
                  Active Support Referrals
                </h2>
                <p className="text-xs text-slate-400">Coordinated cross-department student referrals</p>
              </div>
              <Link href="/app/student-support/referrals">
                <Button variant="ghost" size="sm" className="text-xs text-cyan-400 hover:text-cyan-300">
                  Manage Referrals <ChevronRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>

            {loading ? (
              <div className="py-8 text-center text-xs text-slate-500">Loading referrals...</div>
            ) : activeReferrals.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">No active support referrals.</div>
            ) : (
              <div className="divide-y divide-slate-800">
                {activeReferrals.map((ref) => (
                  <div key={ref.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-slate-200">{ref.student_name}</span>
                        <span className="text-xs text-slate-400">({ref.student_reg_no})</span>
                        <Badge
                          variant="outline"
                          className={
                            ref.status === "PENDING"
                              ? "border-amber-500/30 text-amber-400 bg-amber-500/10 text-[10px]"
                              : ref.status === "IN_PROGRESS"
                              ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                              : "border-slate-700 text-slate-400 text-[10px]"
                          }
                        >
                          {ref.status}
                        </Badge>
                        {ref.student_consent_obtained && (
                          <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40">
                            Consent Verified
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2">
                        <span>Service: <strong className="text-slate-300">{ref.target_service}</strong></span>
                        <span>•</span>
                        <span>Category: {ref.reason_category || ref.reasonCategory}</span>
                        <span>•</span>
                        <span>Referred by: {ref.referrer_role || ref.referring_role || ref.referringRole || "Faculty"}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right 1 Column: Quick Action Hub & Urgent Follow-Ups */}
        <div className="space-y-6">
          {/* Quick Support Actions */}
          <Card className="border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Quick Workflows</h2>
            <div className="space-y-2">
              <Link href="/app/student-support/mentor" className="block">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800/80 hover:border-slate-700 transition flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <UserCheck className="h-4 w-4 text-indigo-400" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">My Mentor Portal</div>
                      <div className="text-[11px] text-slate-400">View faculty mentor & contact</div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              </Link>

              <Link href="/app/student-support/counselling" className="block">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800/80 hover:border-slate-700 transition flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Heart className="h-4 w-4 text-rose-400" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">Book Counselling</div>
                      <div className="text-[11px] text-slate-400">Confidential appointment booking</div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              </Link>

              <Link href="/app/student-support/development-plans" className="block">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800/80 hover:border-slate-700 transition flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Sparkles className="h-4 w-4 text-purple-400" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">Student Development Plans</div>
                      <div className="text-[11px] text-slate-400">IDP milestones & academic goals</div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              </Link>

              <Link href="/app/student-support/referrals" className="block">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-800/40 hover:bg-slate-800/80 hover:border-slate-700 transition flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">Support Referral</div>
                      <div className="text-[11px] text-slate-400">Career, academic & wellbeing links</div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              </Link>

              <Link href="/app/student-support/counselling/workspace" className="block">
                <div className="p-3 rounded-lg border border-amber-900/40 bg-amber-950/20 hover:bg-amber-950/40 transition flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="h-4 w-4 text-amber-400" />
                    <div>
                      <div className="text-xs font-medium text-amber-300">Counsellor Workspace</div>
                      <div className="text-[11px] text-amber-400/80">Authorized licensed staff only</div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-amber-500" />
                </div>
              </Link>
            </div>
          </Card>

          {/* Pending Follow-up Action Items */}
          <Card className="border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-400" />
                Urgent Follow-Ups
              </h2>
              <Link href="/app/student-support/follow-ups">
                <span className="text-[11px] text-orange-400 hover:underline">All Tasks</span>
              </Link>
            </div>

            {loading ? (
              <div className="py-4 text-center text-xs text-slate-500">Loading follow-ups...</div>
            ) : urgentFollowUps.length === 0 ? (
              <div className="py-4 text-center text-xs text-slate-500">No overdue follow-up tasks.</div>
            ) : (
              <div className="space-y-2">
                {urgentFollowUps.map((fu) => (
                  <div key={fu.id} className="p-2.5 rounded border border-slate-800 bg-slate-950/40 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-200">{fu.title}</span>
                      <Badge
                        variant="outline"
                        className={
                          fu.priority === "URGENT" || fu.priority === "HIGH"
                            ? "border-rose-500/30 text-rose-400 text-[9px]"
                            : "border-slate-700 text-slate-400 text-[9px]"
                        }
                      >
                        {fu.priority}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Due: {new Date(fu.due_date || fu.dueDate || "").toLocaleDateString()}</span>
                      <span className="text-slate-500">Assigned: {fu.assigned_to_name ?? fu.assignedUserName ?? "Staff"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
