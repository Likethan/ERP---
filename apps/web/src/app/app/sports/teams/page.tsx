"use client";

import React, { useState, useEffect } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import {
  SportsTeamItem,
  TeamRosterMemberItem,
  SportsParticipantItem,
} from "@/types/sports";
import {
  Users,
  Plus,
  Search,
  Filter,
  Shield,
  Award,
  Trash2,
  AlertTriangle,
  ChevronRight,
  CheckCircle2,
} from "lucide-react";

export default function TeamsPage() {
  const [teams, setTeams] = useState<SportsTeamItem[]>([]);
  const [participants, setParticipants] = useState<SportsParticipantItem[]>([]);
  const [roster, setRoster] = useState<TeamRosterMemberItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<SportsTeamItem | null>(null);

  // Modals
  const [isAddTeamModalOpen, setIsAddTeamModalOpen] = useState(false);
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);

  // New team form state
  const [newTeam, setNewTeam] = useState({
    name: "",
    sport: "Football",
    category: "VARSITY",
    genderCategory: "MEN",
    maxRosterSize: 18,
    headCoachName: "Coach Rajesh Pillai",
  });

  // New member form state
  const [selectedParticipantId, setSelectedParticipantId] = useState("");
  const [memberRole, setMemberRole] = useState("PLAYER");
  const [jerseyNumber, setJerseyNumber] = useState("");
  const [position, setPosition] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [tRes, pRes] = await Promise.all([
      sportsService.listTeams(),
      sportsService.listParticipants(),
    ]);
    if (tRes.success && tRes.data) {
      setTeams(tRes.data);
      if (tRes.data.length > 0 && !selectedTeam) {
        setSelectedTeam(tRes.data[0]);
        loadRoster(tRes.data[0].id);
      }
    }
    if (pRes.success && pRes.data) {
      setParticipants(pRes.data);
    }
    setLoading(false);
  };

  const loadRoster = async (teamId: string) => {
    const res = await sportsService.getTeamRoster(teamId);
    if (res.success && res.data) {
      setRoster(res.data);
    }
  };

  const handleSelectTeam = (team: SportsTeamItem) => {
    setSelectedTeam(team);
    loadRoster(team.id);
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!newTeam.name.trim()) {
      setFormError("Team name is required");
      return;
    }
    const res = await sportsService.createTeam({
      name: newTeam.name,
      sport: newTeam.sport,
      category: newTeam.category,
      genderCategory: newTeam.genderCategory,
      maxRosterSize: Number(newTeam.maxRosterSize),
      headCoachName: newTeam.headCoachName,
    });
    if (res.success && res.data) {
      setActionSuccess(`Team "${res.data.name}" created successfully`);
      setIsAddTeamModalOpen(false);
      setNewTeam({
        name: "",
        sport: "Football",
        category: "VARSITY",
        genderCategory: "MEN",
        maxRosterSize: 18,
        headCoachName: "Coach Rajesh Pillai",
      });
      loadData();
    } else {
      setFormError(typeof res.error === "string" ? res.error : "Failed to create team");
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!selectedTeam) return;

    if (!selectedParticipantId) {
      setFormError("Please select an athlete from the participant directory");
      return;
    }

    const participant = participants.find((p) => p.id === selectedParticipantId);
    if (!participant) {
      setFormError("Selected participant was not found");
      return;
    }

    if (participant.clearanceStatus !== "CLEARED") {
      setFormError(
        `Athlete ${participant.userName} has status "${participant.clearanceStatus}". Institutional policy requires "CLEARED" medical certification.`
      );
      return;
    }

    const activeCount = roster.filter((m) => m.status === "ACTIVE").length;
    if (activeCount >= selectedTeam.maxRosterSize) {
      setFormError(`Cannot exceed team maximum roster capacity of ${selectedTeam.maxRosterSize}`);
      return;
    }

    const res = await sportsService.addTeamMember(selectedTeam.id, {
      participantId: participant.id,
      participantName: participant.userName,
      role: memberRole,
      jerseyNumber: jerseyNumber ? Number(jerseyNumber) : undefined,
      position: position || undefined,
    });

    if (res.success) {
      setActionSuccess(`Added ${participant.userName} to roster.`);
      setIsAddMemberModalOpen(false);
      setSelectedParticipantId("");
      setJerseyNumber("");
      setPosition("");
      loadRoster(selectedTeam.id);
      // Refresh teams to update activeRosterCount
      const tRes = await sportsService.listTeams();
      if (tRes.data) setTeams(tRes.data);
    } else {
      setFormError(typeof res.error === "string" ? res.error : "Failed to add member");
    }
  };

  const handleRemoveMember = async (teamId: string, memberId: string) => {
    if (!confirm("Are you sure you want to remove this athlete from the active roster?")) return;
    setRoster((prev) => prev.filter((m) => m.id !== memberId));
    setActionSuccess("Roster membership updated.");
  };

  const filteredTeams = teams.filter((t) => {
    const matchesSport = selectedSport === "all" || t.sport.toLowerCase() === selectedSport.toLowerCase();
    const matchesQuery =
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.sport.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.headCoachName || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSport && matchesQuery;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Teams & Rosters</h1>
          <p className="text-sm text-slate-500">
            Manage varsity, collegiate, and intramural squads, player positions, and coaching staff.
          </p>
        </div>
        <button
          onClick={() => {
            setFormError(null);
            setIsAddTeamModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Team
        </button>
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
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search teams by name, sport, or coach..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedSport}
            onChange={(e) => setSelectedSport(e.target.value)}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="all">All Sports</option>
            <option value="Cricket">Cricket</option>
            <option value="Football">Football</option>
            <option value="Basketball">Basketball</option>
            <option value="Badminton">Badminton</option>
            <option value="Volleyball">Volleyball</option>
            <option value="Athletics">Athletics</option>
          </select>
        </div>
      </div>

      {/* Grid: Left teams list, Right selected team roster */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Teams List */}
        <div className="lg:col-span-5 space-y-3">
          {loading ? (
            <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
              <p className="mt-2 text-sm text-slate-500">Loading campus teams...</p>
            </div>
          ) : filteredTeams.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
              <Users className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="mt-2 text-sm font-medium text-slate-700">No teams found</p>
              <p className="text-xs text-slate-500">Try adjusting your search or filters.</p>
            </div>
          ) : (
            filteredTeams.map((team) => {
              const activeCount = team.activeRosterCount || 0;
              const isSelected = selectedTeam?.id === team.id;
              const capacityPct = Math.min(100, Math.round((activeCount / team.maxRosterSize) * 100));

              return (
                <div
                  key={team.id}
                  onClick={() => handleSelectTeam(team)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-indigo-50/60 border-indigo-300 ring-1 ring-indigo-400 shadow-sm"
                      : "bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {team.sport}
                        </span>
                        <span className="text-xs capitalize text-slate-500">
                          {team.genderCategory.toLowerCase()}&apos;s Squad
                        </span>
                      </div>
                      <h3 className="font-semibold text-slate-900 mt-1 text-base">{team.name}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Head Coach: {team.headCoachName || "Staff Coach"}
                      </p>
                    </div>
                    <ChevronRight className={`w-5 h-5 ${isSelected ? "text-indigo-600" : "text-slate-300"}`} />
                  </div>

                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>Roster Capacity</span>
                      <span className="font-medium text-slate-700">
                        {activeCount} / {team.maxRosterSize} athletes
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          capacityPct >= 90 ? "bg-amber-500" : "bg-indigo-600"
                        }`}
                        style={{ width: `${capacityPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Selected Team Detail & Roster */}
        <div className="lg:col-span-7">
          {selectedTeam ? (
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-slate-900">{selectedTeam.name}</h2>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-800">
                      Active Squad
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Sport: {selectedTeam.sport} • Coach: {selectedTeam.headCoachName || "Head Coach"} • Roster Cap:{" "}
                    {selectedTeam.maxRosterSize}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setFormError(null);
                    setIsAddMemberModalOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Athlete to Roster
                </button>
              </div>

              {/* Roster Table */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-indigo-600" />
                  Official Roster ({roster.filter((m) => m.status === "ACTIVE").length} Athletes)
                </h3>

                {roster.length === 0 ? (
                  <div className="text-center py-8 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                    <Users className="w-6 h-6 text-slate-400 mx-auto" />
                    <p className="text-sm text-slate-600 mt-2 font-medium">No athletes assigned yet</p>
                    <p className="text-xs text-slate-400">Click &quot;Add Athlete to Roster&quot; to assign eligible participants.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-lg border border-slate-200">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                        <tr>
                          <th className="py-2.5 px-3 font-semibold">Jersey</th>
                          <th className="py-2.5 px-3 font-semibold">Athlete Name</th>
                          <th className="py-2.5 px-3 font-semibold">Position</th>
                          <th className="py-2.5 px-3 font-semibold">Role</th>
                          <th className="py-2.5 px-3 font-semibold">Status</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {roster.map((member) => (
                          <tr key={member.id} className="hover:bg-slate-50/60">
                            <td className="py-2.5 px-3 font-bold text-slate-900">
                              {member.jerseyNumber !== undefined && member.jerseyNumber !== null
                                ? `#${member.jerseyNumber}`
                                : "-"}
                            </td>
                            <td className="py-2.5 px-3 font-medium text-slate-900">
                              {member.participantName}
                            </td>
                            <td className="py-2.5 px-3 text-slate-600">{member.position || "General"}</td>
                            <td className="py-2.5 px-3">
                              {member.role === "CAPTAIN" ? (
                                <span className="inline-flex items-center gap-1 font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                                  <Award className="w-3 h-3 text-amber-600" />
                                  Captain
                                </span>
                              ) : member.role === "VICE_CAPTAIN" ? (
                                <span className="inline-flex items-center gap-1 font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                                  Vice Capt.
                                </span>
                              ) : (
                                <span className="text-slate-500 capitalize">{member.role.toLowerCase()}</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                                  member.status === "ACTIVE"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {member.status}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <button
                                onClick={() => handleRemoveMember(selectedTeam.id, member.id)}
                                title="Remove from Roster"
                                className="text-slate-400 hover:text-red-600 p-1 rounded transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
              <Shield className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="mt-3 text-sm font-medium">Select a team from the left to view and manage its roster.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal: Create Team */}
      {isAddTeamModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Create Campus Sports Team</h2>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateTeam} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Team Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Campus Titans, Falcons XI"
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Sport Category</label>
                  <select
                    value={newTeam.sport}
                    onChange={(e) => setNewTeam({ ...newTeam, sport: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="Cricket">Cricket</option>
                    <option value="Football">Football</option>
                    <option value="Basketball">Basketball</option>
                    <option value="Badminton">Badminton</option>
                    <option value="Volleyball">Volleyball</option>
                    <option value="Tennis">Tennis</option>
                    <option value="Athletics">Athletics</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Gender Division</label>
                  <select
                    value={newTeam.genderCategory}
                    onChange={(e) => setNewTeam({ ...newTeam, genderCategory: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="MEN">Men</option>
                    <option value="WOMEN">Women</option>
                    <option value="COED">Co-ed / Mixed</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Roster Limit</label>
                  <input
                    type="number"
                    min={5}
                    max={50}
                    value={newTeam.maxRosterSize}
                    onChange={(e) => setNewTeam({ ...newTeam, maxRosterSize: Number(e.target.value) })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Head Coach</label>
                  <input
                    type="text"
                    value={newTeam.headCoachName}
                    onChange={(e) => setNewTeam({ ...newTeam, headCoachName: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddTeamModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm & Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Athlete to Roster */}
      {isAddMemberModalOpen && selectedTeam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Add Athlete to Roster</h2>
              <p className="text-xs text-slate-500 mt-0.5">Team: {selectedTeam.name}</p>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleAddMember} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select Registered Athlete (Must have Medical Clearance)
                </label>
                <select
                  required
                  value={selectedParticipantId}
                  onChange={(e) => setSelectedParticipantId(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                >
                  <option value="">-- Choose Athlete --</option>
                  {participants.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.userName} ({p.primarySport}) - [{p.clearanceStatus}]
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Roster Role</label>
                  <select
                    value={memberRole}
                    onChange={(e) => setMemberRole(e.target.value)}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="PLAYER">Player</option>
                    <option value="CAPTAIN">Captain</option>
                    <option value="VICE_CAPTAIN">Vice Captain</option>
                    <option value="RESERVE">Reserve</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Jersey #</label>
                  <input
                    type="number"
                    min={1}
                    max={99}
                    placeholder="e.g. 10"
                    value={jerseyNumber}
                    onChange={(e) => setJerseyNumber(e.target.value)}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Position</label>
                  <input
                    type="text"
                    placeholder="e.g. Striker"
                    value={position}
                    onChange={(e) => setPosition(e.target.value)}
                    className="w-full text-xs border border-slate-300 rounded px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddMemberModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm Roster Addition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
