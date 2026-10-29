"use client";

import React, { useState, useEffect } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import {
  UserCheck,
  Award,
  Shield,
  Search,
  Plus,
  Mail,
  Phone,
  Calendar,
  CheckCircle2,
  Filter,
} from "lucide-react";

interface CoachOfficialItem {
  id: string;
  name: string;
  role: "coach" | "assistant_coach" | "trainer" | "official" | "referee";
  sport: string;
  certification: string;
  license_number: string;
  assigned_team_or_event: string;
  email: string;
  phone: string;
  status: "active" | "on_leave" | "available";
}

const INITIAL_STAFF: CoachOfficialItem[] = [
  {
    id: "co-1",
    name: "Coach Rajesh Pillai",
    role: "coach",
    sport: "Cricket",
    certification: "BCCI Level 2 Certified Coach",
    license_number: "LIC-BCCI-8891",
    assigned_team_or_event: "Campus Titans (Cricket)",
    email: "rajesh.pillai@campus.edu",
    phone: "+91 98450 12345",
    status: "active",
  },
  {
    id: "co-2",
    name: "Coach Sneha Kulkarni",
    role: "coach",
    sport: "Football",
    certification: "AIFF D-License & AFC 'C' Diploma",
    license_number: "LIC-AIFF-4402",
    assigned_team_or_event: "Campus Falcons (Football Men)",
    email: "sneha.k@campus.edu",
    phone: "+91 98450 23456",
    status: "active",
  },
  {
    id: "co-3",
    name: "Dr. Vikram Seth",
    role: "trainer",
    sport: "General Conditioning",
    certification: "NSCA Certified Strength & Conditioning Specialist (CSCS)",
    license_number: "LIC-NSCA-1029",
    assigned_team_or_event: "Varsity High Performance Camp",
    email: "vikram.seth@campus.edu",
    phone: "+91 98450 34567",
    status: "active",
  },
  {
    id: "co-4",
    name: "Official Arvind Swamy",
    role: "referee",
    sport: "Basketball",
    certification: "FIBA National Grade 1 Referee",
    license_number: "LIC-FIBA-9912",
    assigned_team_or_event: "Inter-Campus Trophy 2026",
    email: "arvind.swamy@campus.edu",
    phone: "+91 98450 45678",
    status: "available",
  },
  {
    id: "co-5",
    name: "Official Manisha Roy",
    role: "referee",
    sport: "Badminton",
    certification: "BAI State Umpire Certification",
    license_number: "LIC-BAI-3310",
    assigned_team_or_event: "Chancellor Badminton Open",
    email: "manisha.roy@campus.edu",
    phone: "+91 98450 56789",
    status: "available",
  },
];

export default function CoachesPage() {
  const [staff, setStaff] = useState<CoachOfficialItem[]>(INITIAL_STAFF);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [sportFilter, setSportFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    role: "coach" as CoachOfficialItem["role"],
    sport: "Football",
    certification: "",
    license_number: "",
    assigned_team_or_event: "",
    email: "",
    phone: "",
  });

  const handleRegisterStaff = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim()) return;

    const newItem: CoachOfficialItem = {
      id: `co-${Date.now()}`,
      ...formData,
      status: "active",
    };

    setStaff((prev) => [newItem, ...prev]);
    setIsModalOpen(false);
    setToastMessage(`Staff profile for ${newItem.name} registered.`);
    setFormData({
      name: "",
      role: "coach",
      sport: "Football",
      certification: "",
      license_number: "",
      assigned_team_or_event: "",
      email: "",
      phone: "",
    });
  };

  const filteredStaff = staff.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.certification.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.assigned_team_or_event.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "all" || item.role === roleFilter;
    const matchesSport = sportFilter === "all" || item.sport.toLowerCase().includes(sportFilter.toLowerCase());
    return matchesSearch && matchesRole && matchesSport;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Coaches & Match Officials</h1>
          <p className="text-sm text-slate-500">
            Certified technical leaders, fitness conditioners, and accredited tournament referees.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Register Coach / Official
        </button>
      </div>

      {toastMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Head & Assistant Coaches</p>
            <p className="text-xl font-bold text-slate-900">
              {staff.filter((s) => s.role === "coach" || s.role === "assistant_coach").length} Staff
            </p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Accredited Officials & Umpires</p>
            <p className="text-xl font-bold text-slate-900">
              {staff.filter((s) => s.role === "referee" || s.role === "official").length} Referees
            </p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Compliance & Verification</p>
            <p className="text-xl font-bold text-slate-900">100% Certified</p>
          </div>
        </div>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by staff name, license, certification or assignment..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="all">All Roles</option>
            <option value="coach">Head Coach</option>
            <option value="assistant_coach">Assistant Coach</option>
            <option value="trainer">Fitness Trainer</option>
            <option value="referee">Referee / Umpire</option>
          </select>
          <select
            value={sportFilter}
            onChange={(e) => setSportFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="all">All Disciplines</option>
            <option value="Cricket">Cricket</option>
            <option value="Football">Football</option>
            <option value="Basketball">Basketball</option>
            <option value="Badminton">Badminton</option>
          </select>
        </div>
      </div>

      {/* Staff Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredStaff.map((person) => (
          <div
            key={person.id}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {person.sport}
                  </span>
                  <h3 className="font-semibold text-slate-900 mt-2 text-base">{person.name}</h3>
                  <p className="text-xs text-indigo-600 font-medium capitalize mt-0.5">
                    {person.role.replace("_", " ")}
                  </p>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                    person.status === "active"
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {person.status}
                </span>
              </div>

              <div className="mt-4 space-y-2 text-xs text-slate-600">
                <div className="flex items-center gap-2">
                  <Award className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  <span className="truncate">{person.certification}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="font-mono text-[11px] text-slate-500">{person.license_number}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span className="text-slate-800 font-medium truncate">{person.assigned_team_or_event}</span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3 text-slate-400" />
                {person.email}
              </span>
              <span className="flex items-center gap-1">
                <Phone className="w-3 h-3 text-slate-400" />
                {person.phone}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Modal: Register Staff */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Register Technical Staff / Official</h2>
            <form onSubmit={handleRegisterStaff} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Coach David Miller"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value as CoachOfficialItem["role"] })
                    }
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="coach">Head Coach</option>
                    <option value="assistant_coach">Assistant Coach</option>
                    <option value="trainer">Fitness Trainer / S&C</option>
                    <option value="referee">Referee / Umpire</option>
                    <option value="official">Technical Official</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Sport / Discipline</label>
                  <select
                    value={formData.sport}
                    onChange={(e) => setFormData({ ...formData, sport: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="Football">Football</option>
                    <option value="Cricket">Cricket</option>
                    <option value="Basketball">Basketball</option>
                    <option value="Badminton">Badminton</option>
                    <option value="Volleyball">Volleyball</option>
                    <option value="General Conditioning">General Conditioning</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Certification Body</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. AFC B Diploma, BCCI L1"
                    value={formData.certification}
                    onChange={(e) => setFormData({ ...formData, certification: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">License / Badge #</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. LIC-2026-901"
                    value={formData.license_number}
                    onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Primary Squad / Event</label>
                <input
                  type="text"
                  placeholder="e.g. Campus Falcons, Annual Sports Meet"
                  value={formData.assigned_team_or_event}
                  onChange={(e) => setFormData({ ...formData, assigned_team_or_event: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Campus Email</label>
                  <input
                    type="email"
                    required
                    placeholder="staff@campus.edu"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Phone</label>
                  <input
                    type="text"
                    placeholder="+91 98..."
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm Registration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
