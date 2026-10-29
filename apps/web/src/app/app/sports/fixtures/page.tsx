"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import { MatchFixtureItem, SportsCompetitionItem } from "@/types/sports";
import {
  Calendar,
  Clock,
  MapPin,
  Trophy,
  Shield,
  Edit2,
  AlertTriangle,
  CheckCircle2,
  Filter,
} from "lucide-react";

export default function FixturesPage() {
  const [fixtures, setFixtures] = useState<MatchFixtureItem[]>([]);
  const [competitions, setCompetitions] = useState<SportsCompetitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompId, setSelectedCompId] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");

  // Reschedule dialog
  const [rescheduleFixture, setRescheduleFixture] = useState<MatchFixtureItem | null>(null);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [cRes, fRes] = await Promise.all([
      sportsService.listCompetitions(),
      sportsService.listFixtures(),
    ]);

    if (cRes.success && cRes.data) {
      setCompetitions(cRes.data);
    }
    if (fRes.success && fRes.data) {
      setFixtures(fRes.data);
    }
    setLoading(false);
  };

  const handleReschedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rescheduleFixture || !newDate || !newTime) return;

    const res = await sportsService.rescheduleFixture(
      rescheduleFixture.id,
      newDate,
      newTime,
      rescheduleFixture.facilityName
    );

    if (res.success && res.data) {
      setActionSuccess(`Match #${rescheduleFixture.matchNumber} rescheduled to ${newDate} at ${newTime}.`);
      setRescheduleFixture(null);
      loadData();
    }
  };

  const filteredFixtures = fixtures.filter((f) => {
    const matchesComp = selectedCompId === "all" || f.competitionId === selectedCompId;
    const matchesStatus = selectedStatus === "all" || f.status === selectedStatus;
    return matchesComp && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Fixtures & Match Schedule
          </h1>
          <p className="text-sm text-slate-500">
            Tournament brackets, scheduled match clashes, and verified venue slot assignments.
          </p>
        </div>
        <Link
          href="/app/sports/results"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Trophy className="w-4 h-4" />
          Enter / View Scores & Standings
        </Link>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Tournament:</span>
          <select
            value={selectedCompId}
            onChange={(e) => setSelectedCompId(e.target.value)}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="all">All Competitions</option>
            {competitions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.sport})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">Status:</span>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="all">All Statuses</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="LIVE">Live Now</option>
            <option value="COMPLETED">Completed</option>
            <option value="POSTPONED">Postponed</option>
          </select>
        </div>
      </div>

      {/* Fixtures List */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
          <p className="mt-2 text-sm text-slate-500">Loading match schedule...</p>
        </div>
      ) : filteredFixtures.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <Calendar className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="mt-2 text-sm font-medium text-slate-700">No match fixtures found</p>
          <p className="text-xs text-slate-500">Select a tournament or generate fixtures.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredFixtures.map((fixture) => {
            const isCompleted = fixture.status === "COMPLETED";
            return (
              <div
                key={fixture.id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow transition-all space-y-4"
              >
                {/* Top bar: Round, Match #, Status */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                      Match #{fixture.matchNumber}
                    </span>
                    <span className="text-slate-500">Round {fixture.roundNumber}</span>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full font-semibold uppercase text-[10px] ${
                      isCompleted
                        ? "bg-emerald-100 text-emerald-800"
                        : fixture.status === "POSTPONED"
                        ? "bg-amber-100 text-amber-800"
                        : fixture.status === "LIVE"
                        ? "bg-red-100 text-red-800 animate-pulse"
                        : "bg-blue-100 text-blue-800"
                    }`}
                  >
                    {fixture.status}
                  </span>
                </div>

                {/* Clash Card: Team A vs Team B */}
                <div className="flex items-center justify-between bg-slate-50 p-4 rounded-lg border border-slate-100">
                  <div className="flex-1 text-center pr-2">
                    <p className="font-bold text-sm text-slate-900">{fixture.homeTeamName || "Home Team"}</p>
                    <span className="text-[10px] text-slate-400 font-medium">Home Squad</span>
                  </div>

                  <div className="px-3 text-center">
                    {isCompleted && fixture.result ? (
                      <div className="flex items-center gap-2 font-mono text-xl font-extrabold text-slate-900 bg-white px-3 py-1 rounded border border-slate-200 shadow-inner">
                        <span>{fixture.result.homeScore}</span>
                        <span className="text-slate-300">-</span>
                        <span>{fixture.result.awayScore}</span>
                      </div>
                    ) : (
                      <span className="text-xs font-bold text-slate-400 bg-white px-2 py-1 rounded border border-slate-200">
                        VS
                      </span>
                    )}
                  </div>

                  <div className="flex-1 text-center pl-2">
                    <p className="font-bold text-sm text-slate-900">{fixture.awayTeamName || "Away Team"}</p>
                    <span className="text-[10px] text-slate-400 font-medium">Away Squad</span>
                  </div>
                </div>

                {/* Details: Date, Time, Venue, Official */}
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{fixture.matchDate}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {fixture.startTime} - {fixture.endTime}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 col-span-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{fixture.facilityName || "Main Arena"}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <button
                    onClick={() => {
                      setRescheduleFixture(fixture);
                      setNewDate(fixture.matchDate);
                      setNewTime(fixture.startTime);
                    }}
                    className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-indigo-600 font-medium"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    Reschedule
                  </button>

                  <Link
                    href={`/app/sports/results?match=${fixture.id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    {isCompleted ? "View Result Audit" : "Enter Match Score"}
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Reschedule Match */}
      {rescheduleFixture && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Reschedule Match Fixture</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Match #{rescheduleFixture.matchNumber}: {rescheduleFixture.homeTeamName} vs{" "}
                {rescheduleFixture.awayTeamName}
              </p>
            </div>

            <form onSubmit={handleReschedule} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Date</label>
                <input
                  type="date"
                  required
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Kick-off / Start Time</label>
                <input
                  type="time"
                  required
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-800 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  Rescheduling will verify against existing timetable slots and facility bookings to prevent court
                  overlaps.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setRescheduleFixture(null)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm & Synchronize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
