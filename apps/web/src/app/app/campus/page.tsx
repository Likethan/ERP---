"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  CampusEventItem,
  ClubItem,
  AnnouncementItem,
  NotificationItem,
  CampusDashboardSummary,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  CalendarDays,
  PartyPopper,
  Users,
  Bell,
  FileText,
  CheckSquare,
  Sparkles,
  ArrowRight,
  Plus,
  Clock,
  MapPin,
  TrendingUp,
  ShieldCheck,
  Building2,
  Calendar,
  Layers,
  ChevronRight,
} from "lucide-react";
import { CampusCalendarView } from "@/components/campus/campus-calendar";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function CampusOperationsDashboard() {
  const { user, hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<CampusDashboardSummary | null>(null);
  const [events, setEvents] = useState<CampusEventItem[]>([]);
  const [clubs, setClubs] = useState<ClubItem[]>([]);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "calendar" | "today">("overview");

  const canCreateEvent = hasPermission("campus.manage_events") || hasPermission("*");
  const canCreateClub = hasPermission("campus.manage_clubs") || hasPermission("*");
  const canCreateAnnouncement = hasPermission("campus.create_announcements") || hasPermission("*");

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [sumRes, evtsRes, clubsRes, ancRes, notifRes] = await Promise.all([
        campusService.getCampusSummary(),
        campusService.getEvents(),
        campusService.getClubs(),
        campusService.getAnnouncements(),
        campusService.getNotifications(),
      ]);

      if (sumRes.data) setSummary(sumRes.data);
      if (evtsRes.data) setEvents(evtsRes.data);
      if (clubsRes.data) setClubs(clubsRes.data);
      if (ancRes.data) setAnnouncements(ancRes.data);
      if (notifRes.data) setNotifications(notifRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const upcomingEvents = events.filter((e) => e.status !== "COMPLETED" && e.status !== "CANCELLED");

  // Today's Activity Filters (simulated date matching 16 Oct 2026 or active items)
  const todayEvents = events.filter(
    (e) => e.startDate === "2026-10-16" || e.status === "REGISTRATION_OPEN"
  ).slice(0, 3);

  const todayAnnouncements = announcements.slice(0, 3);
  const unreadNotifications = notifications.filter((n) => n.status === "UNREAD").slice(0, 4);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[11px] font-mono font-semibold uppercase text-indigo-300 border border-indigo-500/30">
              CampusOS Engagement Layer
            </span>
            <span className="text-slate-500">•</span>
            <span className="text-xs text-slate-400 font-medium">Academic Year 2026-27</span>
          </div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-black tracking-tight text-white">
            Campus Operations & Engagement Hub
          </h1>
          <p className="mt-1 text-sm text-slate-400 max-w-3xl">
            Single institutional operating plane for campus events, student organizations,
            event attendance registers, broadcasts, and notification dispatch.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {canCreateEvent && (
            <Link href="/app/campus/events/create">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Plus className="h-4 w-4" />}
                className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
              >
                Create Event
              </Button>
            </Link>
          )}
          {canCreateClub && (
            <Link href="/app/campus/clubs/create">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Building2 className="h-4 w-4" />}
                className="border-slate-700 bg-slate-900 hover:bg-slate-800"
              >
                New Club
              </Button>
            </Link>
          )}
          {canCreateAnnouncement && (
            <Link href="/app/campus/announcements">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<FileText className="h-4 w-4" />}
                className="border-slate-700 bg-slate-900 hover:bg-slate-800"
              >
                Post Notice
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* 8 Core Operational Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Events"
          value={summary?.activeEventsCount ?? 0}
          description="Open for registration or ongoing"
          icon={<PartyPopper className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Upcoming Events"
          value={summary?.upcomingEventsCount ?? 0}
          description="Scheduled across campus"
          icon={<CalendarDays className="h-5 w-5 text-purple-400" />}
        />
        <StatCard
          title="Active Clubs & Orgs"
          value={summary?.activeClubsCount ?? 0}
          description="Chartered student societies"
          icon={<Users className="h-5 w-5 text-cyan-400" />}
        />
        <StatCard
          title="Event Registrations"
          value={summary?.registeredParticipantsCount ?? 0}
          description="Total enrolled participants"
          icon={<CheckSquare className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Attendance Today"
          value={summary?.attendanceTodayCount ?? 0}
          description="Verified hall attendees"
          icon={<CheckSquare className="h-5 w-5 text-amber-400" />}
        />
        <StatCard
          title="Unread Notices"
          value={summary?.unreadAnnouncementsCount ?? 0}
          description="Active institutional circulars"
          icon={<FileText className="h-5 w-5 text-blue-400" />}
        />
        <StatCard
          title="Unread Alerts"
          value={summary?.unreadNotificationsCount ?? 0}
          description="Pending personal inbox dispatches"
          icon={<Bell className="h-5 w-5 text-rose-400" />}
        />
        <StatCard
          title="Overall Attendance Rate"
          value={`${summary?.overallAttendanceRate ?? 0}%`}
          description="Average event attendance yield"
          icon={<TrendingUp className="h-5 w-5 text-teal-400" />}
        />
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: "overview", label: "Operations Overview" },
          { id: "calendar", label: "Campus Unified Calendar" },
          { id: "today", label: "Today's Activity & Dispatch" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
              activeTab === tab.id
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "bg-slate-900/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-8">
          {/* Upcoming Events Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                  <PartyPopper className="h-4 w-4 text-indigo-400" />
                  Upcoming Campus Events & Activities
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Scheduled hackathons, symposiums, guest lectures, and cultural tournaments
                </p>
              </div>
              <Link
                href="/app/campus/events"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1 shrink-0"
              >
                View all events DataGrid <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {upcomingEvents.slice(0, 6).map((event) => (
                <div
                  key={event.id}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 flex flex-col justify-between hover:border-slate-700 transition-all hover:shadow-lg hover:shadow-indigo-500/5"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {event.category}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          event.status === "REGISTRATION_OPEN"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : event.status === "REGISTRATION_CLOSED"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {event.status.replace("_", " ")}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white line-clamp-2 leading-snug">
                      {event.title}
                    </h3>

                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {event.description}
                    </p>

                    <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                      <div className="flex items-center gap-2 truncate">
                        <Clock className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span>{event.startDate} • {event.startTime}</span>
                      </div>
                      <div className="flex items-center gap-2 truncate">
                        <MapPin className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span className="truncate">{event.venue}</span>
                      </div>
                      <div className="flex items-center gap-2 truncate">
                        <Users className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span className="text-slate-300 font-mono">
                          {event.registeredCount} / {event.capacity} registered
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] text-slate-500 truncate">
                      By {event.organizer}
                    </span>
                    <Link
                      href={`/app/campus/events/${event.id}`}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1"
                    >
                      Details <ChevronRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Engagement Summary & Operational Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Active Clubs Summary */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-cyan-400" />
                  Active Student Clubs ({clubs.length})
                </h3>
                <Link
                  href="/app/campus/clubs"
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Directory →
                </Link>
              </div>

              <div className="space-y-2.5">
                {clubs.slice(0, 4).map((c) => (
                  <Link
                    key={c.id}
                    href={`/app/campus/clubs/${c.id}`}
                    className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-colors"
                  >
                    <div>
                      <div className="text-xs font-semibold text-white">{c.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Lead: {c.studentLead} • Advisor: {c.facultyCoordinator}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-mono font-bold text-cyan-300">
                        {c.membersCount}
                      </span>
                      <span className="text-[10px] text-slate-500 block">members</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Recent Institutional Circulars */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-400" />
                  Recent Announcements
                </h3>
                <Link
                  href="/app/campus/announcements"
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  Notice Board →
                </Link>
              </div>

              <div className="space-y-2.5">
                {announcements.slice(0, 3).map((a) => (
                  <Link
                    key={a.id}
                    href={`/app/campus/announcements/${a.id}`}
                    className="block p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {a.category}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {a.publishDate.split(" ")[0]}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-white mt-1.5 truncate">
                      {a.title}
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1 mt-1">
                      {a.summary}
                    </p>
                  </Link>
                ))}
              </div>
            </div>

            {/* Quick Links & Engagement Health */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-400" />
                  Campus Quick Workflows
                </h3>
              </div>

              <div className="space-y-2">
                <Link
                  href="/app/campus/registrations"
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 hover:border-indigo-500/50 transition-colors"
                >
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-200">
                    <CheckSquare className="h-4 w-4 text-indigo-400" />
                    Manage Registrations
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </Link>

                <Link
                  href="/app/campus/attendance"
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 hover:border-indigo-500/50 transition-colors"
                >
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-200">
                    <Users className="h-4 w-4 text-purple-400" />
                    Event Attendance Marking
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </Link>

                <Link
                  href="/app/campus/notifications"
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 hover:border-indigo-500/50 transition-colors"
                >
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-200">
                    <Bell className="h-4 w-4 text-rose-400" />
                    Notification Inbox
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </Link>

                <Link
                  href="/app/campus/preferences"
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 hover:border-indigo-500/50 transition-colors"
                >
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-200">
                    <TrendingUp className="h-4 w-4 text-teal-400" />
                    Communication Preferences
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: UNIFIED CALENDAR */}
      {activeTab === "calendar" && (
        <CampusCalendarView events={events} announcements={announcements} />
      )}

      {/* TAB 3: TODAY'S ACTIVITY */}
      {activeTab === "today" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Events Today */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <PartyPopper className="h-4 w-4 text-indigo-400" />
                  Events In Progress / Today
                </h3>
              </div>
              <div className="space-y-3">
                {todayEvents.map((e) => (
                  <div key={e.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs font-bold text-white">{e.title}</div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {e.venue} • {e.startTime} - {e.endTime}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-indigo-400 font-mono">{e.registeredCount} attendees</span>
                      <Link href={`/app/campus/events/${e.id}`} className="text-slate-300 hover:text-white">
                        Open →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Club Meetings */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-cyan-400" />
                  Club Meetings Today
                </h3>
              </div>
              <div className="space-y-3">
                {clubs.slice(0, 3).map((c) => (
                  <div key={c.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs font-bold text-white">{c.name}</div>
                    <div className="text-[11px] text-slate-400 mt-1">{c.meetingSchedule}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Venue: {c.meetingVenue}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Attendance Activity */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <CheckSquare className="h-4 w-4 text-emerald-400" />
                  Live Attendance Check-Ins
                </h3>
              </div>
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300">
                  <div className="flex items-center justify-between font-semibold text-white">
                    <span>Cisco Pre-Placement Session</span>
                    <span className="text-emerald-400 font-mono">138 / 142 (97%)</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Hall attendance marked by Vikram Sen at Seminar Hall.
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300">
                  <div className="flex items-center justify-between font-semibold text-white">
                    <span>Production Rust Workshop</span>
                    <span className="text-emerald-400 font-mono">74 / 80 (92%)</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Lab registers verified by Dr. Rajesh Sharma.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
