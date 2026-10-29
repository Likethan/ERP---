"use client";

import React, { useState, useEffect } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import {
  SportsCompetitionItem,
  MatchFixtureItem,
  CompetitionStandingItem,
} from "@/types/sports";
import {
  Trophy,
  CheckCircle2,
  ShieldCheck,
  Edit3,
  History,
} from "lucide-react";

export default function ResultsPage() {
  const [competitions, setCompetitions] = useState<SportsCompetitionItem[]>([]);
  const [selectedCompId, setSelectedCompId] = useState("");
  const [standings, setStandings] = useState<CompetitionStandingItem[]>([]);
  const [fixtures, setFixtures] = useState<MatchFixtureItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Score Entry Modal
  const [scoreModalFixture, setScoreModalFixture] = useState<MatchFixtureItem | null>(null);
  const [homeScore, setHomeScore] = useState(0);
  const [awayScore, setAwayScore] = useState(0);
  const [verificationNotes, setVerificationNotes] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    setLoading(true);
    const res = await sportsService.listCompetitions();
    if (res.success && res.data && res.data.length > 0) {
      setCompetitions(res.data);
      const first = res.data[0];
      setSelectedCompId(first.id);
      loadCompetitionData(first.id);
    } else {
      setLoading(false);
    }
  };

  const loadCompetitionData = async (compId: string) => {
    const [sRes, fRes] = await Promise.all([
      sportsService.getCompetitionStandings(compId),
      sportsService.listFixtures(compId),
    ]);
    if (sRes.success && sRes.data) {
      setStandings(sRes.data);
    }
    if (fRes.success && fRes.data) {
      setFixtures(fRes.data);
    }
    setLoading(false);
  };

  const handleOpenScoreModal = (fixture: MatchFixtureItem) => {
    setScoreModalFixture(fixture);
    setHomeScore(fixture.result?.homeScore ?? 0);
    setAwayScore(fixture.result?.awayScore ?? 0);
    setVerificationNotes("");
  };

  const handleSubmitScore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scoreModalFixture) return;

    const res = await sportsService.recordMatchResult(
      scoreModalFixture.id,
      homeScore,
      awayScore,
      verificationNotes || "Official score recorded by Chief Referee"
    );

    if (res.success && res.data) {
      setActionSuccess(
        `Score recorded: ${scoreModalFixture.homeTeamName || "Home"} ${homeScore} - ${awayScore} ${
          scoreModalFixture.awayTeamName || "Away"
        }. Standings recomputed.`
      );
      setScoreModalFixture(null);
      if (selectedCompId) {
        loadCompetitionData(selectedCompId);
      }
    }
  };

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Results, Score Verification & Standings
          </h1>
          <p className="text-sm text-slate-500">
            Auditable score entry, referee verification trails, and real-time tournament league tables.
          </p>
        </div>
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

      {/* Competition Selector */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Tournament Table:</label>
          <select
            value={selectedCompId}
            onChange={(e) => {
              setSelectedCompId(e.target.value);
              loadCompetitionData(e.target.value);
            }}
            className="text-sm font-semibold border border-slate-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            {competitions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.sport} - {c.tournamentFormat.replace("_", " ").toLowerCase()})
              </option>
            ))}
          </select>
        </div>

        <div className="text-xs text-slate-500 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Tiebreaker: Points &gt; Score Difference &gt; Points For</span>
        </div>
      </div>

      {/* Standings League Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-amber-500" />
            <h2 className="text-sm font-bold text-slate-900">Official Competition Standings</h2>
          </div>
          <span className="text-xs font-medium text-slate-500">Live Seedings</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3 text-center">Pos</th>
                <th className="py-2.5 px-3">Squad / Team</th>
                <th className="py-2.5 px-2 text-center">P</th>
                <th className="py-2.5 px-2 text-center">W</th>
                <th className="py-2.5 px-2 text-center">D</th>
                <th className="py-2.5 px-2 text-center">L</th>
                <th className="py-2.5 px-2 text-center">GF</th>
                <th className="py-2.5 px-2 text-center">GA</th>
                <th className="py-2.5 px-2 text-center font-bold">GD</th>
                <th className="py-2.5 px-3 text-center font-bold text-indigo-700">PTS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {standings.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-400">
                    No standings generated yet.
                  </td>
                </tr>
              ) : (
                standings.map((team, idx) => {
                  const isTop = idx === 0;
                  return (
                    <tr key={team.id} className={isTop ? "bg-amber-50/40 font-medium" : "hover:bg-slate-50/60"}>
                      <td className="py-2.5 px-3 text-center font-bold text-slate-900">
                        {isTop ? (
                          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-400 text-slate-900 text-xs">
                            1
                          </span>
                        ) : (
                          team.rank
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">
                        {team.teamName || team.participantName || "Team"}
                      </td>
                      <td className="py-2.5 px-2 text-center">{team.played}</td>
                      <td className="py-2.5 px-2 text-center text-emerald-700 font-semibold">{team.won}</td>
                      <td className="py-2.5 px-2 text-center text-slate-500">{team.drawn}</td>
                      <td className="py-2.5 px-2 text-center text-red-600">{team.lost}</td>
                      <td className="py-2.5 px-2 text-center">{team.pointsFor}</td>
                      <td className="py-2.5 px-2 text-center">{team.pointsAgainst}</td>
                      <td className="py-2.5 px-2 text-center font-bold">
                        {team.pointDifference > 0 ? `+${team.pointDifference}` : team.pointDifference}
                      </td>
                      <td className="py-2.5 px-3 text-center font-extrabold text-indigo-700 text-sm">
                        {team.points}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Match Fixture Scorecards */}
      <div>
        <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-600" />
          Match Fixtures & Scorecard Verification
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fixtures.map((f) => {
            const isCompleted = f.status === "COMPLETED";
            return (
              <div
                key={f.id}
                className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Match #{f.matchNumber}</span>
                    <span
                      className={`text-[10px] px-2 py-0.2 rounded font-semibold uppercase ${
                        isCompleted ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {f.status}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {f.homeTeamName || "Home"}{" "}
                    {isCompleted && f.result ? (
                      <span className="text-indigo-600">
                        {f.result.homeScore} - {f.result.awayScore}
                      </span>
                    ) : (
                      "vs"
                    )}{" "}
                    {f.awayTeamName || "Away"}
                  </div>
                  <p className="text-xs text-slate-500">
                    {f.matchDate} • {f.facilityName || "Court Arena"}
                  </p>
                </div>

                <button
                  onClick={() => handleOpenScoreModal(f)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 rounded-lg text-xs font-semibold text-slate-700 transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  {isCompleted ? "Correct Score" : "Record Score"}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal: Score Entry & Referee Audit */}
      {scoreModalFixture && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Official Match Score Verification</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Match #{scoreModalFixture.matchNumber} • {scoreModalFixture.facilityName || "Venue"}
              </p>
            </div>

            <form onSubmit={handleSubmitScore} className="space-y-4">
              <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div className="text-center">
                  <label className="block text-xs font-bold text-slate-700 mb-1 truncate">
                    {scoreModalFixture.homeTeamName || "Home Team"}
                  </label>
                  <input
                    type="number"
                    min={0}
                    required
                    value={homeScore}
                    onChange={(e) => setHomeScore(Number(e.target.value))}
                    className="w-20 mx-auto text-center text-xl font-mono font-bold border border-slate-300 rounded-lg py-1.5 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="text-center">
                  <label className="block text-xs font-bold text-slate-700 mb-1 truncate">
                    {scoreModalFixture.awayTeamName || "Away Team"}
                  </label>
                  <input
                    type="number"
                    min={0}
                    required
                    value={awayScore}
                    onChange={(e) => setAwayScore(Number(e.target.value))}
                    className="w-20 mx-auto text-center text-xl font-mono font-bold border border-slate-300 rounded-lg py-1.5 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Referee / Scorer Audit Notes
                </label>
                <textarea
                  rows={2}
                  required
                  placeholder="Record referee confirmation, score validation notes, or reason for correction..."
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setScoreModalFixture(null)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Verify & Lock Result
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
