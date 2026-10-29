"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Award,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  Globe2,
  HandHeart,
  PlusCircle,
  ShieldCheck,
  TrendingUp,
  Users2,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  CommunityPartner,
  EngagementAnalyticsSummary,
  EngagementProgram,
  ServiceHourEntry,
} from "@/types/engagement";

const SDG_NAMES: Record<number, string> = {
  1: "No Poverty",
  2: "Zero Hunger",
  3: "Good Health & Well-being",
  4: "Quality Education",
  5: "Gender Equality",
  6: "Clean Water & Sanitation",
  7: "Affordable & Clean Energy",
  8: "Decent Work & Economic Growth",
  9: "Industry, Innovation & Infrastructure",
  10: "Reduced Inequalities",
  11: "Sustainable Cities & Communities",
  12: "Responsible Consumption & Production",
  13: "Climate Action",
  14: "Life Below Water",
  15: "Life on Land",
  16: "Peace, Justice & Strong Institutions",
  17: "Partnerships for the Goals",
};

export default function EngagementDashboardPage() {
  const [analytics, setAnalytics] = useState<EngagementAnalyticsSummary | null>(null);
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [partners, setPartners] = useState<CommunityPartner[]>([]);
  const [recentHours, setRecentHours] = useState<ServiceHourEntry[]>([]);
  const [activeRole, setActiveRole] = useState<"STUDENT" | "COORDINATOR" | "HOD" | "ADMIN">("COORDINATOR");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [a, p, part, h] = await Promise.all([
          EngagementService.getAnalytics(),
          EngagementService.listPrograms(),
          EngagementService.listPartners(),
          EngagementService.listServiceHours(),
        ]);
        setAnalytics(a);
        setPrograms(p);
        setPartners(part);
        setRecentHours(h);
      } catch (e) {
        console.error("Failed to load engagement dashboard data", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header with Title and Role Simulator */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                Step 65 — Civic Impact OS
              </span>
              <span className="text-xs text-muted-foreground">
                One Campus. One System. One Source of Truth.
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
              Student Engagement & Civic Impact Management
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Enterprise community service, partner collaborations, verified service hours, and verifiable credentials.
            </p>
          </div>

          {/* Role Experience Switcher */}
          <div className="flex items-center bg-muted/60 p-1 rounded-xl border border-border text-xs">
            <span className="px-2 py-1 text-muted-foreground font-medium">Viewing as:</span>
            {(["STUDENT", "COORDINATOR", "HOD", "ADMIN"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setActiveRole(r)}
                className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                  activeRole === r
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {r.charAt(0) + r.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Executive Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium uppercase tracking-wider">Active Programs</span>
              <HandHeart className="h-5 w-5 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              {analytics?.active_programs ?? 12}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <span className="text-emerald-500 font-semibold flex items-center">
                <TrendingUp className="h-3 w-3 mr-0.5" /> 100%
              </span>
              institutional clearance
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium uppercase tracking-wider">Community Partners</span>
              <Users2 className="h-5 w-5 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              {analytics?.total_partners ?? 18}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              Active MoUs with registered NGOs & trusts
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium uppercase tracking-wider">Verified Hours</span>
              <Clock className="h-5 w-5 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              {analytics?.total_verified_hours ? Number(analytics.total_verified_hours).toLocaleString() : "3,840.5"}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <span className="text-amber-500 font-semibold">
                {analytics?.hours_pending_verification ?? 145} hrs
              </span>
              pending verification
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium uppercase tracking-wider">Certificates Issued</span>
              <Award className="h-5 w-5 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              {analytics?.certificates_issued ?? 312}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5 text-purple-500" />
              Cryptographically verifiable credentials
            </div>
          </div>
        </div>

        {/* Quick Action Bar for Coordinators & Admins */}
        <div className="bg-card/40 border border-border rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase text-muted-foreground tracking-wider">
              Fast Operations:
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/app/engagement/programs"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium shadow-sm hover:opacity-90"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              <span>Create Program</span>
            </Link>
            <Link
              href="/app/engagement/opportunities"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-secondary text-secondary-foreground text-xs font-medium hover:bg-secondary/80"
            >
              <Compass className="h-3.5 w-3.5" />
              <span>Publish Opportunity</span>
            </Link>
            <Link
              href="/app/engagement/partners"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-border text-foreground text-xs font-medium hover:bg-accent"
            >
              <Users2 className="h-3.5 w-3.5" />
              <span>Register Partner</span>
            </Link>
            <Link
              href="/app/engagement/service-hours"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-border text-foreground text-xs font-medium hover:bg-accent"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span>Verify Logged Hours</span>
            </Link>
          </div>
        </div>

        {/* Two-Column Grid: UN SDG Impact & Recent Programs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* SDG Alignment & Civic Impact Distribution */}
          <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                  <Globe2 className="h-5 w-5 text-emerald-500" />
                  UN Sustainable Development Goals (SDG) Alignment
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Audited hours contributed across institutional civic missions
                </p>
              </div>
              <Link
                href="/app/engagement/analytics"
                className="text-xs text-primary hover:underline font-medium"
              >
                View Full Analytics →
              </Link>
            </div>

            <div className="space-y-3">
              {analytics &&
                Object.entries(analytics.hours_by_sdg).map(([sdg, hours]) => {
                  const numSdg = Number(sdg);
                  const name = SDG_NAMES[numSdg] || `SDG ${numSdg}`;
                  const percentage = Math.min(100, Math.round((hours / 1200) * 100));

                  return (
                    <div key={sdg} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-foreground">
                          Goal {numSdg}: {name}
                        </span>
                        <span className="text-muted-foreground font-semibold">{hours} hrs</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Partner Spotlight & Key Collaborations */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                <Users2 className="h-5 w-5 text-blue-500" />
                Key Community Partners
              </h2>
              <Link
                href="/app/engagement/partners"
                className="text-xs text-primary hover:underline font-medium"
              >
                All Partners →
              </Link>
            </div>

            <div className="divide-y divide-border">
              {partners.slice(0, 3).map((partner) => (
                <div key={partner.id} className="py-3 first:pt-0 last:pb-0 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-foreground line-clamp-1">
                      {partner.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 font-medium">
                      {partner.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2">
                    {partner.purpose_statement}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                    <span>{partner.total_volunteers_engaged} volunteers</span>
                    <span className="font-medium text-foreground">
                      {partner.verified_hours_contributed} verified hrs
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Active Programs Directory Preview */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                <HandHeart className="h-5 w-5 text-emerald-500" />
                Featured Civic Engagement Programs
              </h2>
              <p className="text-xs text-muted-foreground">
                Approved institutional programs actively registering or in progress
              </p>
            </div>
            <Link
              href="/app/engagement/programs"
              className="text-xs text-primary hover:underline font-medium"
            >
              Browse All Programs ({programs.length}) →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {programs.slice(0, 3).map((prog) => (
              <div
                key={prog.id}
                className="border border-border/80 rounded-xl p-4 bg-muted/20 space-y-3 hover:border-primary/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                    {prog.code}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-medium uppercase">
                    {prog.status.replace("_", " ")}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-foreground line-clamp-1">
                    {prog.name}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {prog.description}
                  </p>
                </div>

                <div className="space-y-1 text-xs text-muted-foreground border-t border-border pt-2">
                  <div className="flex items-center justify-between">
                    <span>Capacity:</span>
                    <span className="font-medium text-foreground">
                      {prog.current_enrolled_count} / {prog.max_participants || "Open"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Target Hours:</span>
                    <span className="font-medium text-foreground">{prog.target_service_hours} hrs</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link
                    href={`/app/engagement/programs`}
                    className="block text-center text-xs font-medium py-1.5 rounded-lg bg-card border border-border text-foreground hover:bg-accent"
                  >
                    View Details & Roster
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Service-Hour Submissions & Approvals */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                <Clock className="h-5 w-5 text-amber-500" />
                Recent Service-Hour Activity
              </h2>
              <p className="text-xs text-muted-foreground">
                Participant check-in records, hour submissions, and supervisor verification audit
              </p>
            </div>
            <Link
              href="/app/engagement/service-hours"
              className="text-xs text-primary hover:underline font-medium"
            >
              Manage All Hours →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase font-semibold">
                <tr>
                  <th className="px-4 py-2.5">Student</th>
                  <th className="px-4 py-2.5">Date</th>
                  <th className="px-4 py-2.5">Duration</th>
                  <th className="px-4 py-2.5">Description</th>
                  <th className="px-4 py-2.5">Supervisor</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recentHours.slice(0, 5).map((hour) => (
                  <tr key={hour.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium text-foreground">
                      {hour.student_name || "Enrolled Student"}
                      <div className="text-[10px] text-muted-foreground">
                        {hour.student_roll_number || "Verified"}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{hour.activity_date}</td>
                    <td className="px-4 py-3 font-semibold text-foreground">{hour.duration_hours} hrs</td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">
                      {hour.activity_description}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {hour.supervisor_name || "Community Partner"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          hour.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                            : hour.status === "PENDING"
                            ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                            : "bg-red-500/10 text-red-500 border border-red-500/20"
                        }`}
                      >
                        {hour.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

