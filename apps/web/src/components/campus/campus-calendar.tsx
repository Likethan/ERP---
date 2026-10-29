"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { CampusEventItem, AnnouncementItem } from "@/types/campus";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CalendarEntry {
  id: string;
  title: string;
  date: string; // YYYY-MM-DD
  time: string;
  venue?: string;
  category: string;
  sourceType: "EVENT" | "CLUB" | "ACADEMIC" | "PLACEMENT" | "ANNOUNCEMENT";
  href: string;
  colorClass: string;
  badge: string;
}

interface CampusCalendarProps {
  events: CampusEventItem[];
  announcements: AnnouncementItem[];
}

export function CampusCalendarView({
  events,
  announcements,
}: CampusCalendarProps) {
  const [viewMode, setViewMode] = useState<"MONTH" | "WEEK" | "DAY" | "AGENDA">(
    "MONTH",
  );
  const [filterSource, setFilterSource] = useState<string>("ALL");
  const [currentDate, setCurrentDate] = useState<Date>(new Date(2026, 9, 15)); // October 2026

  // Transform events and announcements into unified calendar entries
  const calendarEntries = useMemo<CalendarEntry[]>(() => {
    const list: CalendarEntry[] = [];

    // Add Events
    events.forEach((e) => {
      let sourceType: CalendarEntry["sourceType"] = "EVENT";
      let colorClass = "bg-indigo-500/20 text-indigo-300 border-indigo-500/40";

      if (e.organizerType === "CLUB" || e.category === "Club Activity") {
        sourceType = "CLUB";
        colorClass = "bg-cyan-500/20 text-cyan-300 border-cyan-500/40";
      } else if (e.category === "Placement") {
        sourceType = "PLACEMENT";
        colorClass = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      } else if (e.category === "Academic" || e.category === "Symposium") {
        sourceType = "ACADEMIC";
        colorClass = "bg-amber-500/20 text-amber-300 border-amber-500/40";
      } else if (e.category === "Hackathon" || e.category === "Technical") {
        colorClass = "bg-purple-500/20 text-purple-300 border-purple-500/40";
      } else if (e.category === "Cultural") {
        colorClass = "bg-rose-500/20 text-rose-300 border-rose-500/40";
      }

      list.push({
        id: e.id,
        title: e.title,
        date: e.startDate,
        time: `${e.startTime} - ${e.endTime}`,
        venue: e.venue,
        category: e.category,
        sourceType,
        href: `/app/campus/events/${e.id}`,
        colorClass,
        badge: e.category,
      });
    });

    // Add Announcements
    announcements.forEach((a) => {
      const pubDate = a.publishDate.split(" ")[0] || "2026-10-01";
      list.push({
        id: a.id,
        title: a.title,
        date: pubDate.includes("-") ? pubDate : "2026-10-01",
        time: a.publishDate.split(" ").slice(1).join(" ") || "09:00 AM",
        category: a.category,
        sourceType: "ANNOUNCEMENT",
        href: `/app/campus/announcements/${a.id}`,
        colorClass: "bg-blue-500/20 text-blue-300 border-blue-500/40",
        badge: `Notice: ${a.priority}`,
      });
    });

    return list;
  }, [events, announcements]);

  const filteredEntries = useMemo(() => {
    if (filterSource === "ALL") return calendarEntries;
    return calendarEntries.filter((c) => c.sourceType === filterSource);
  }, [calendarEntries, filterSource]);

  // Calendar month rendering data
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-indexed, 9 = October
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay();

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-6">
      {/* Calendar Controls Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <CalendarIcon className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">
                {monthNames[month]} {year}
              </h2>
              <span className="text-[11px] rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-400 border border-slate-700">
                {filteredEntries.length} items
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Aggregated schedule across campus fests, academic seminars,
              placement drives & notices
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Source Filter */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-0.5">
            {[
              { id: "ALL", label: "All" },
              { id: "EVENT", label: "Events" },
              { id: "CLUB", label: "Clubs" },
              { id: "PLACEMENT", label: "Placement" },
              { id: "ANNOUNCEMENT", label: "Notices" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterSource(f.id)}
                className={cn(
                  "px-2.5 py-1 text-xs rounded-lg font-medium transition-colors cursor-pointer",
                  filterSource === f.id
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-slate-200",
                )}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-0.5">
            {(["MONTH", "WEEK", "DAY", "AGENDA"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  "px-2.5 py-1 text-xs rounded-lg font-medium transition-colors cursor-pointer",
                  viewMode === mode
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-slate-200",
                )}
              >
                {mode.charAt(0) + mode.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          {/* Month Navigation */}
          <div className="flex items-center gap-1 border border-slate-800 rounded-xl p-0.5 bg-slate-950">
            <button
              onClick={handlePrevMonth}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              aria-label="Previous month"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setCurrentDate(new Date(2026, 9, 15))}
              className="px-2 py-1 text-xs font-medium text-slate-300 hover:text-white"
            >
              Today
            </button>
            <button
              onClick={handleNextMonth}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              aria-label="Next month"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* MONTH VIEW */}
      {viewMode === "MONTH" && (
        <div className="space-y-2">
          {/* Day of week header */}
          <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold text-slate-400 py-1">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="py-1">
                {day}
              </div>
            ))}
          </div>

          {/* Month grid */}
          <div className="grid grid-cols-7 gap-2">
            {/* Empty prefix cells */}
            {Array.from({ length: firstDayIndex }).map((_, i) => (
              <div
                key={`empty-${i}`}
                className="min-h-[105px] rounded-xl border border-slate-800/40 bg-slate-950/20 p-2 opacity-30"
              />
            ))}

            {/* Days in Month */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const dayNum = i + 1;
              const dateString = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
              const dayEntries = filteredEntries.filter(
                (e) => e.date === dateString,
              );
              const isToday = dayNum === 15 && month === 9 && year === 2026;

              return (
                <div
                  key={dayNum}
                  className={cn(
                    "min-h-[110px] rounded-xl border p-2 flex flex-col transition-all",
                    isToday
                      ? "border-indigo-500/80 bg-indigo-950/20 shadow-md shadow-indigo-500/10"
                      : "border-slate-800 bg-slate-950/60 hover:border-slate-700",
                  )}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={cn(
                        "text-xs font-bold font-mono px-1.5 py-0.5 rounded",
                        isToday ? "bg-indigo-600 text-white" : "text-slate-400",
                      )}
                    >
                      {dayNum}
                    </span>
                    {dayEntries.length > 0 && (
                      <span className="text-[10px] font-mono text-slate-500">
                        {dayEntries.length}{" "}
                        {dayEntries.length === 1 ? "item" : "items"}
                      </span>
                    )}
                  </div>

                  <div className="flex-1 space-y-1 overflow-y-auto max-h-[90px] pr-0.5">
                    {dayEntries.map((entry) => (
                      <Link
                        key={entry.id}
                        href={entry.href}
                        className={cn(
                          "block rounded-lg px-2 py-1 text-[11px] font-medium border truncate transition-transform hover:scale-[1.02]",
                          entry.colorClass,
                        )}
                        title={`${entry.title} (${entry.time})`}
                      >
                        <div className="truncate font-semibold">
                          {entry.title}
                        </div>
                        <div className="text-[9px] opacity-80 truncate">
                          {entry.time}
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AGENDA / LIST VIEW */}
      {(viewMode === "AGENDA" || viewMode === "WEEK" || viewMode === "DAY") && (
        <div className="space-y-3">
          <div className="text-xs text-slate-400 font-medium pb-2 border-b border-slate-800">
            Displaying all {filteredEntries.length} scheduled institutional
            items in chronological sequence
          </div>
          <div className="space-y-2.5">
            {filteredEntries.map((item) => (
              <div
                key={item.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 border border-slate-700/60 shrink-0 font-mono text-xs font-bold text-slate-300">
                    {item.date.split("-")[2] || "15"}
                  </div>
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-white">
                        {item.title}
                      </span>
                      <span
                        className={cn(
                          "text-[10px] font-mono px-2 py-0.5 rounded-full border",
                          item.colorClass,
                        )}
                      >
                        {item.badge}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-slate-500" />
                        {item.time}
                      </span>
                      {item.venue && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-slate-500" />
                          {item.venue}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <Link
                  href={item.href}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors shrink-0 self-start sm:self-auto"
                >
                  Inspect <ExternalLink className="h-3 w-3" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
