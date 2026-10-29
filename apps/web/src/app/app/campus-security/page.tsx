"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  DoorOpen,
  Flame,
  Footprints,
  KeyRound,
  Layers,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import {
  CampusSecurityIncident,
  EmergencyEvent,
  SecurityCheckpoint,
  SecurityOperationsOverview,
  VisitorPass,
} from "@/types/campus-security";

export default function CampusSecurityDashboardPage() {
  const [overview, setOverview] = useState<SecurityOperationsOverview | null>(null);
  const [recentPasses, setRecentPasses] = useState<VisitorPass[]>([]);
  const [recentIncidents, setRecentIncidents] = useState<CampusSecurityIncident[]>([]);
  const [emergencies, setEmergencies] = useState<EmergencyEvent[]>([]);
  const [checkpoints, setCheckpoints] = useState<SecurityCheckpoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ov, passes, incs, emgs, chkpts] = await Promise.all([
          CampusSecurityService.getOverview(),
          CampusSecurityService.listPasses(),
          CampusSecurityService.listIncidents(),
          CampusSecurityService.listEmergencyEvents(),
          CampusSecurityService.listCheckpoints(),
        ]);
        setOverview(ov);
        setRecentPasses(passes);
        setRecentIncidents(incs);
        setEmergencies(emgs);
        setCheckpoints(chkpts);
      } catch (err) {
        console.error("Failed to load security dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <SecurityNav />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex justify-center items-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-16">
      <SecurityNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top Header & Readiness Indicator */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-card/60 border border-border p-6 rounded-2xl backdrop-blur-md shadow-sm">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                DEFCON 5 — NORMAL CAMPUS OPERATIONS
              </span>
              <span className="text-xs text-muted-foreground">• Server-Signed Access Security</span>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight mt-1">
              Campus Security Command & Gate Intelligence
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Real-time gate telemetry, visitor credentials, physical access authorization, and emergency response.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-muted/40 p-4 rounded-xl border border-border/80">
            <div className="text-right">
              <div className="text-xs font-medium text-muted-foreground">Composite Readiness Score</div>
              <div className="text-3xl font-black text-primary">
                {overview?.security_readiness_score.toFixed(1)}
                <span className="text-sm font-normal text-muted-foreground">/100</span>
              </div>
            </div>
            <div className="h-12 w-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <ShieldCheck className="h-7 w-7 text-primary" />
            </div>
          </div>
        </div>

        {/* 6 Key Telemetry Scorecards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">On-Campus Guests</span>
              <Users className="h-4 w-4 text-primary" />
            </div>
            <div className="text-2xl font-bold mt-2">
              {overview?.visitors_currently_on_campus}
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              Verified active passes
            </div>
          </div>

          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Expected Today</span>
              <Clock className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold mt-2">
              {overview?.expected_arrivals_today}
            </div>
            <div className="text-[11px] text-cyan-500 font-medium mt-0.5">
              Pre-registered visits
            </div>
          </div>

          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Pending Approvals</span>
              <CheckCircle2 className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold mt-2 text-amber-500">
              {overview?.pending_visitor_approvals}
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              Awaiting host sign-off
            </div>
          </div>

          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Active Contractors</span>
              <UserCheck className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold mt-2">
              {overview?.active_contractors_on_site}
            </div>
            <div className="text-[11px] text-indigo-400 font-medium mt-0.5">
              Induction-verified
            </div>
          </div>

          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Active Incidents</span>
              <AlertTriangle className="h-4 w-4 text-rose-500" />
            </div>
            <div className="text-2xl font-bold mt-2 text-rose-500">
              {overview?.open_security_incidents}
            </div>
            <div className="text-[11px] text-rose-400 font-medium mt-0.5">
              {overview?.critical_incidents_count} Critical alarms
            </div>
          </div>

          <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Patrol Rounds</span>
              <Footprints className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold mt-2 text-emerald-500">
              {overview?.patrol_completion_rate_pct}%
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              Verified checkpoint completion
            </div>
          </div>
        </div>

        {/* Quick Launchpad & Gate Action Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link
            href="/app/campus-security/gate-operations"
            className="group p-5 bg-card hover:bg-muted/40 border border-border rounded-xl transition-all shadow-xs flex items-center space-x-4"
          >
            <div className="p-3 rounded-xl bg-primary/10 text-primary group-hover:scale-105 transition-transform">
              <DoorOpen className="h-6 w-6" />
            </div>
            <div>
              <div className="font-semibold text-sm">Gate Check-in Desk</div>
              <div className="text-xs text-muted-foreground">Verify QR pass & issue badges</div>
            </div>
          </Link>

          <Link
            href="/app/campus-security/visitors"
            className="group p-5 bg-card hover:bg-muted/40 border border-border rounded-xl transition-all shadow-xs flex items-center space-x-4"
          >
            <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 group-hover:scale-105 transition-transform">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <div className="font-semibold text-sm">Pre-Register Guest</div>
              <div className="text-xs text-muted-foreground">Host invitation & approvals</div>
            </div>
          </Link>

          <Link
            href="/app/campus-security/incidents"
            className="group p-5 bg-card hover:bg-muted/40 border border-border rounded-xl transition-all shadow-xs flex items-center space-x-4"
          >
            <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 group-hover:scale-105 transition-transform">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <div className="font-semibold text-sm">Report Security Concern</div>
              <div className="text-xs text-muted-foreground">Perimeter breach or safety hazard</div>
            </div>
          </Link>

          <Link
            href="/app/campus-security/emergency"
            className="group p-5 bg-card hover:bg-muted/40 border border-border rounded-xl transition-all shadow-xs flex items-center space-x-4"
          >
            <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 group-hover:scale-105 transition-transform">
              <Flame className="h-6 w-6" />
            </div>
            <div>
              <div className="font-semibold text-sm">Emergency Workspace</div>
              <div className="text-xs text-muted-foreground">Evacuation & incident response</div>
            </div>
          </Link>
        </div>

        {/* Active Emergency Advisory Banner (if active) */}
        {emergencies.some((e) => e.status === "ACTIVE") && (
          <div className="bg-destructive/15 border-2 border-destructive p-5 rounded-xl flex items-start space-x-4 animate-pulse">
            <Flame className="h-6 w-6 text-destructive shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-bold text-destructive text-base">
                ACTIVE CAMPUS EMERGENCY IN PROGRESS
              </div>
              <div className="text-sm font-medium mt-1">
                {emergencies.find((e) => e.status === "ACTIVE")?.title} — Affected:{" "}
                {emergencies.find((e) => e.status === "ACTIVE")?.affected_campus_areas}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {emergencies.find((e) => e.status === "ACTIVE")?.emergency_broadcast_message}
              </div>
            </div>
            <Link
              href="/app/campus-security/emergency"
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg text-xs font-semibold shadow-xs"
            >
              Open Incident Command
            </Link>
          </div>
        )}

        {/* Two-Column Operations Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left 2 Cols: Active Checked-In Visitors & Gate Passes */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div>
                  <h2 className="text-lg font-bold">Active Visitor Gate Sessions</h2>
                  <p className="text-xs text-muted-foreground">
                    Currently verified guests and visitors inside physical campus perimeter
                  </p>
                </div>
                <Link
                  href="/app/campus-security/gate-operations"
                  className="text-xs text-primary font-semibold hover:underline"
                >
                  View All Passes →
                </Link>
              </div>

              <div className="divide-y divide-border/60 mt-2">
                {recentPasses.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    No active visitor passes found.
                  </div>
                ) : (
                  recentPasses.map((pass) => (
                    <div key={pass.id} className="py-3.5 flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-sm">{pass.visitor_name}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-muted text-muted-foreground">
                            {pass.pass_number}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-primary/10 text-primary border border-primary/20">
                            {pass.visitor_category}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Host: <span className="text-foreground">{pass.host_name}</span> • Dest:{" "}
                          <span className="text-foreground">{pass.destination}</span>
                        </div>
                      </div>

                      <div className="text-right">
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                            pass.status === "CHECKED_IN"
                              ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                              : pass.status === "OVERDUE"
                              ? "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {pass.status}
                        </span>
                        <div className="text-[11px] text-muted-foreground mt-1">
                          Valid until {new Date(pass.valid_until).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Security Zones & Restricted Areas */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div>
                  <h2 className="text-lg font-bold">Physical Security Zones & Clearances</h2>
                  <p className="text-xs text-muted-foreground">
                    Campus perimeter, labs, server rooms, and restricted research facilities
                  </p>
                </div>
                <Link
                  href="/app/campus-security/zones"
                  className="text-xs text-primary font-semibold hover:underline"
                >
                  Configure Zones →
                </Link>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-primary">ZONE-SERVER-DC</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      HIGH_SECURITY
                    </span>
                  </div>
                  <div className="font-semibold text-sm mt-1.5">
                    Institutional Data Center & Fiber NOC
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Turing Tower, Floor 1 • Escort Required
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-primary">ZONE-RESEARCH-BIOCHEM</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      RESTRICTED
                    </span>
                  </div>
                  <div className="font-semibold text-sm mt-1.5">
                    Biochemical Research Labs
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Franklin Science Wing, Floor 3
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Col: Recent Incidents & Checkpoint Readiness */}
          <div className="space-y-6">
            {/* Live Security Incident Stream */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-rose-500" />
                  <h2 className="text-lg font-bold">Active Incidents</h2>
                </div>
                <Link
                  href="/app/campus-security/incidents"
                  className="text-xs text-primary font-semibold hover:underline"
                >
                  Manage →
                </Link>
              </div>

              <div className="divide-y divide-border/60 mt-2">
                {recentIncidents.length === 0 ? (
                  <div className="py-6 text-center text-sm text-muted-foreground">
                    No active incidents reported.
                  </div>
                ) : (
                  recentIncidents.map((inc) => (
                    <div key={inc.id} className="py-3.5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-primary">
                          {inc.incident_number}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            inc.severity === "CRITICAL"
                              ? "bg-rose-500/20 text-rose-400"
                              : inc.severity === "HIGH"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-blue-500/20 text-blue-400"
                          }`}
                        >
                          {inc.severity}
                        </span>
                      </div>
                      <div className="font-semibold text-sm">{inc.title}</div>
                      <div className="text-xs text-muted-foreground">
                        Location: <span className="text-foreground">{inc.reported_location}</span>
                      </div>
                      <div className="flex items-center justify-between pt-1 text-[11px] text-muted-foreground">
                        <span>Team: {inc.assigned_team || "Unassigned"}</span>
                        <span className="font-medium text-foreground">{inc.status}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Checkpoint Status */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center space-x-2">
                  <DoorOpen className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-bold">Manned Gates & Barriers</h2>
                </div>
                <span className="text-xs font-semibold text-emerald-500">
                  {checkpoints.filter((c) => c.is_manned).length} Active
                </span>
              </div>

              <div className="space-y-3 mt-3">
                {checkpoints.map((chkpt) => (
                  <div
                    key={chkpt.id}
                    className="p-3 rounded-xl border border-border/80 bg-muted/20 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-xs">{chkpt.name}</div>
                      <div className="text-[11px] text-muted-foreground font-mono">
                        {chkpt.code} • {chkpt.checkpoint_type}
                      </div>
                    </div>
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-500/20" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

