"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { sportsService } from "@/services/sports.service";
import { SportsDashboardData, MatchFixtureItem, TrainingSessionItem } from "@/types/sports";
import { SportsNav } from "@/components/sports/sports-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Trophy,
  DoorOpen,
  Users,
  ShieldCheck,
  Dumbbell,
  Wrench,
  AlertTriangle,
  Calendar,
  Clock,
  MapPin,
  ChevronRight,
  PlusCircle,
  Activity,
  CheckCircle2,
  Timer,
  Building2,
} from "lucide-react";

export default function SportsDashboardPage() {
  const [data, setData] = useState<SportsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    const res = await sportsService.getSportsDashboard();
    if (res.success && res.data) {
      setData(res.data);
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Sports & Athletics", href: "/app/sports" },
        ]}
      />

      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Trophy className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Campus Sports & Athletics Management
                <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-mono font-bold uppercase text-indigo-300 border border-indigo-500/30">
                  Step 57
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400">
                Unified institutional sports administration, facility scheduling, varsity rosters & tournament engine.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/app/sports/calendar">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Calendar className="h-3.5 w-3.5 text-indigo-400" />
              Book Facility
            </Button>
          </Link>
          <Link href="/app/sports/participants">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Users className="h-3.5 w-3.5 text-emerald-400" />
              Register Athlete
            </Button>
          </Link>
          <Link href="/app/sports/competitions">
            <Button size="sm" className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500">
              <PlusCircle className="h-3.5 w-3.5" />
              New Tournament
            </Button>
          </Link>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <SportsNav />

      {/* Operational Alerts Banner */}
      {data && (data.equipmentOverdueCount > 0 || data.facilitiesMaintenance > 0) && (
        <div className="grid gap-3 sm:grid-cols-2">
          {data.facilitiesMaintenance > 0 && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5 text-amber-200">
              <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-semibold text-amber-300">
                  {data.facilitiesMaintenance} Facility Closed for Maintenance:
                </span>{" "}
                Outdoor Basketball Court B is undergoing surface crack resurfacing. No match or training bookings are permitted until inspection reopening.
                <div className="mt-1">
                  <Link href="/app/sports/facilities" className="underline font-medium hover:text-white">
                    View facility closures &rarr;
                  </Link>
                </div>
              </div>
            </div>
          )}

          {data.equipmentOverdueCount > 0 && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-950/20 p-3.5 text-rose-200">
              <Wrench className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-semibold text-rose-300">
                  {data.equipmentOverdueCount} Overdue Gear Loan(s) Detected:
                </span>{" "}
                Nightly sweep flagged items overdue for return. Condition inspection and replacement fee calculation required upon check-in.
                <div className="mt-1">
                  <Link href="/app/sports/equipment" className="underline font-medium hover:text-white">
                    Inspect equipment register &rarr;
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Key Metric Telemetry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          title="Student Athletes"
          value={data?.totalParticipants ?? 0}
          icon={<Users className="h-4 w-4 text-emerald-400" />}
          description="Registered participants"
        />
        <StatCard
          title="Clearance Compliance"
          value={`${data?.clearanceComplianceRate ?? 100}%`}
          icon={<ShieldCheck className="h-4 w-4 text-blue-400" />}
          description={`${data?.participantsCleared ?? 0} medically cleared`}
        />
        <StatCard
          title="Sports Facilities"
          value={`${data?.facilitiesAvailable ?? 0} / ${data?.totalFacilities ?? 0}`}
          icon={<DoorOpen className="h-4 w-4 text-purple-400" />}
          description="Operational venues"
        />
        <StatCard
          title="Varsity Teams"
          value={data?.totalTeams ?? 0}
          icon={<Trophy className="h-4 w-4 text-amber-400" />}
          description="Active competitive squads"
        />
        <StatCard
          title="Active Tournaments"
          value={data?.activeTournaments ?? 0}
          icon={<Activity className="h-4 w-4 text-rose-400" />}
          description="In-progress competitions"
        />
        <StatCard
          title="Equipment on Loan"
          value={data?.equipmentItemsCheckedOut ?? 0}
          icon={<Wrench className="h-4 w-4 text-indigo-400" />}
          description={`${data?.equipmentOverdueCount ?? 0} overdue returns`}
        />
      </div>

      {/* Operations Grid: Today's Fixtures & Training Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Fixtures */}
        <Card className="p-5 border-slate-800 bg-slate-900/40">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Timer className="h-4 w-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-white">Today's Scheduled Matches & Fixtures</h2>
            </div>
            <Link
              href="/app/sports/fixtures"
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              All Fixtures <ChevronRight className="h-3 w-3" />
            </Link>
          </div>

          {loading ? (
            <div className="h-40 flex items-center justify-center text-slate-500 text-xs">
              Loading fixtures...
            </div>
          ) : data?.todayFixtures && data.todayFixtures.length > 0 ? (
            <div className="space-y-3">
              {data.todayFixtures.map((fixture) => (
                <div
                  key={fixture.id}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3.5 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span className="font-mono text-indigo-400 font-semibold">{fixture.competitionName}</span>
                    <Badge variant={fixture.status === "COMPLETED" ? "success" : "default"}>
                      {fixture.status}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between my-2">
                    <div className="text-xs font-semibold text-white truncate max-w-[40%]">
                      {fixture.homeTeamName || fixture.homeParticipantName}
                    </div>
                    <div className="px-3 py-1 rounded bg-slate-900 border border-slate-800 font-mono text-sm font-bold text-amber-400">
                      {fixture.result ? `${fixture.result.homeScore} - ${fixture.result.awayScore}` : "VS"}
                    </div>
                    <div className="text-xs font-semibold text-white truncate max-w-[40%] text-right">
                      {fixture.awayTeamName || fixture.awayParticipantName}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3 text-slate-500" />
                      <span>{fixture.facilityName}</span>
                    </div>
                    <div className="flex items-center gap-1.5 font-mono text-slate-300">
                      <Clock className="h-3 w-3 text-slate-500" />
                      <span>{fixture.startTime} - {fixture.endTime}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-36 flex flex-col items-center justify-center text-slate-500 text-xs gap-1.5">
              <CheckCircle2 className="h-6 w-6 text-slate-600" />
              <span>No matches scheduled for today</span>
            </div>
          )}
        </Card>

        {/* Today's Training Sessions */}
        <Card className="p-5 border-slate-800 bg-slate-900/40">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Dumbbell className="h-4 w-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white">Upcoming Training & Conditioning</h2>
            </div>
            <Link
              href="/app/sports/training/schedule"
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              Session Schedule <ChevronRight className="h-3 w-3" />
            </Link>
          </div>

          {loading ? (
            <div className="h-40 flex items-center justify-center text-slate-500 text-xs">
              Loading sessions...
            </div>
          ) : data?.upcomingTrainingSessions && data.upcomingTrainingSessions.length > 0 ? (
            <div className="space-y-3">
              {data.upcomingTrainingSessions.map((session) => (
                <div
                  key={session.id}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3.5 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-white">{session.title}</span>
                    <Badge variant={session.status === "COMPLETED" ? "success" : "default"}>
                      {session.status}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-400 mb-2">
                    {session.programName} &bull; <span className="text-slate-300">{session.focusArea}</span>
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3 text-slate-500" />
                      <span>{session.facilityName}</span>
                    </div>
                    <div className="flex items-center gap-1.5 font-mono text-emerald-400 font-medium">
                      <Clock className="h-3 w-3 text-slate-500" />
                      <span>{session.startTime} - {session.endTime}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-36 flex flex-col items-center justify-center text-slate-500 text-xs gap-1.5">
              <CheckCircle2 className="h-6 w-6 text-slate-600" />
              <span>No training sessions scheduled today</span>
            </div>
          )}
        </Card>
      </div>

      {/* Module Navigation Grid: 16 Direct Portal Gateways */}
      <div className="pt-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
          Campus Sports & Athletics Administration Modules
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
          {[
            { title: "Departments", path: "/app/sports/departments", icon: <Building2 className="h-4 w-4 text-indigo-400" /> },
            { title: "Facilities", path: "/app/sports/facilities", icon: <DoorOpen className="h-4 w-4 text-blue-400" /> },
            { title: "Calendar", path: "/app/sports/calendar", icon: <Calendar className="h-4 w-4 text-emerald-400" /> },
            { title: "Athletes", path: "/app/sports/participants", icon: <Users className="h-4 w-4 text-amber-400" /> },
            { title: "Teams", path: "/app/sports/teams", icon: <ShieldCheck className="h-4 w-4 text-purple-400" /> },
            { title: "Coaches", path: "/app/sports/coaches", icon: <Trophy className="h-4 w-4 text-rose-400" /> },
            { title: "Programs", path: "/app/sports/training", icon: <Dumbbell className="h-4 w-4 text-emerald-400" /> },
            { title: "Attendance", path: "/app/sports/training/schedule", icon: <CheckCircle2 className="h-4 w-4 text-cyan-400" /> },
            { title: "Tournaments", path: "/app/sports/competitions", icon: <Trophy className="h-4 w-4 text-amber-400" /> },
            { title: "Fixtures", path: "/app/sports/fixtures", icon: <Timer className="h-4 w-4 text-blue-400" /> },
            { title: "Standings", path: "/app/sports/results", icon: <Activity className="h-4 w-4 text-emerald-400" /> },
            { title: "Achievements", path: "/app/sports/achievements", icon: <Trophy className="h-4 w-4 text-amber-400" /> },
            { title: "Equipment", path: "/app/sports/equipment", icon: <Wrench className="h-4 w-4 text-indigo-400" /> },
            { title: "Fees & Billing", path: "/app/sports/fees", icon: <Activity className="h-4 w-4 text-rose-400" /> },
            { title: "Analytics", path: "/app/sports/reports", icon: <Activity className="h-4 w-4 text-purple-400" /> },
            { title: "Policies", path: "/app/sports/config", icon: <ShieldCheck className="h-4 w-4 text-slate-400" /> },
          ].map((item) => (
            <Link
              key={item.path}
              href={item.path}
              className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-800 bg-slate-900/30 hover:bg-slate-800/60 hover:border-slate-700 transition-all text-center group"
            >
              <div className="mb-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80 group-hover:scale-105 transition-transform">
                {item.icon}
              </div>
              <span className="text-xs font-semibold text-slate-200 group-hover:text-white">
                {item.title}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
