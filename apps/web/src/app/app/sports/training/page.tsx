"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import { TrainingProgramItem } from "@/types/sports";
import {
  Dumbbell,
  Plus,
  Search,
  Calendar,
  Users,
  Clock,
  ArrowRight,
  CheckCircle2,
  FileCheck,
} from "lucide-react";

export default function TrainingProgramsPage() {
  const [programs, setPrograms] = useState<TrainingProgramItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    sport: "General Conditioning",
    programType: "CAMP",
    leadCoachName: "Coach Sneha Kulkarni",
    facilityName: "Varsity Gymnasium",
    startDate: "2026-11-01",
    endDate: "2026-12-15",
    capacity: 25,
    feeAmount: 0,
    status: "ACTIVE",
  });

  useEffect(() => {
    loadPrograms();
  }, []);

  const loadPrograms = async () => {
    setLoading(true);
    const res = await sportsService.listTrainingPrograms();
    if (res.success && res.data) {
      setPrograms(res.data);
    }
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await sportsService.createTrainingProgram({
      name: formData.name,
      sport: formData.sport,
      programType: formData.programType,
      leadCoachName: formData.leadCoachName,
      facilityName: formData.facilityName,
      startDate: formData.startDate,
      endDate: formData.endDate,
      capacity: Number(formData.capacity),
      feeAmount: Number(formData.feeAmount),
      status: formData.status,
    });

    if (res.success && res.data) {
      setToastMessage(`Training program "${res.data.name}" created successfully.`);
      setIsModalOpen(false);
      loadPrograms();
    }
  };

  const filteredPrograms = programs.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.leadCoachName || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.facilityName || "").toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      categoryFilter === "all" || p.sport.toLowerCase() === categoryFilter.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Training Camps & Fitness Programs
          </h1>
          <p className="text-sm text-slate-500">
            High-performance development academies, conditioning drills, and recreational fitness clinics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/app/sports/training/schedule"
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-sm font-medium shadow-sm transition-colors"
          >
            <Calendar className="w-4 h-4 text-indigo-600" />
            Session Attendance Sheets
          </Link>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Program
          </button>
        </div>
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

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search programs by title, coach, or venue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
        >
          <option value="all">All Categories</option>
          <option value="Football">Football</option>
          <option value="Badminton">Badminton</option>
          <option value="General Conditioning">General Conditioning</option>
          <option value="Swimming">Swimming</option>
        </select>
      </div>

      {/* Program Cards Grid */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
          <p className="mt-2 text-sm text-slate-500">Loading training programs...</p>
        </div>
      ) : filteredPrograms.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <Dumbbell className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="mt-2 text-sm font-medium text-slate-700">No training programs found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPrograms.map((prog) => {
            const enrolled = prog.enrolledCount || 0;
            const enrollPct = Math.round((enrolled / prog.capacity) * 100);
            return (
              <div
                key={prog.id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {prog.sport}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-800 capitalize">
                      {prog.status.toLowerCase()}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 mt-2 text-base">{prog.name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Lead Instructor: {prog.leadCoachName || "Staff Coach"}
                  </p>

                  <div className="mt-4 space-y-2 text-xs text-slate-600">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        {prog.startDate} to {prog.endDate}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>Venue: {prog.facilityName || "Campus Facility"}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FileCheck className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Fee:{" "}
                        {prog.feeAmount && prog.feeAmount > 0
                          ? `₹${prog.feeAmount.toLocaleString()} (Billable)`
                          : "Free / Institution-Funded"}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                      <span className="flex items-center gap-1 font-medium">
                        <Users className="w-3.5 h-3.5" />
                        Enrolled Athletes
                      </span>
                      <span className="font-semibold text-slate-700">
                        {enrolled} / {prog.capacity} ({enrollPct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          enrollPct >= 90 ? "bg-amber-500" : "bg-indigo-600"
                        }`}
                        style={{ width: `${enrollPct}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs text-slate-400 capitalize">
                    {prog.programType.toLowerCase()} Program
                  </span>
                  <Link
                    href={`/app/sports/training/schedule?program=${prog.id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    View Schedule & Roll Call
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: New Program */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Create Sports Training Program</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Program Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Pre-Season Football Sprint & Stamina Camp"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Sport Category</label>
                  <select
                    value={formData.sport}
                    onChange={(e) => setFormData({ ...formData, sport: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="Football">Football</option>
                    <option value="Cricket">Cricket</option>
                    <option value="Basketball">Basketball</option>
                    <option value="Badminton">Badminton</option>
                    <option value="Swimming">Swimming</option>
                    <option value="General Conditioning">General Conditioning</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Program Type</label>
                  <select
                    value={formData.programType}
                    onChange={(e) => setFormData({ ...formData, programType: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                  >
                    <option value="CAMP">Intensive Camp</option>
                    <option value="DEVELOPMENT">Weekly Development</option>
                    <option value="RECREATIONAL">Recreational Clinic</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Lead Coach</label>
                  <input
                    type="text"
                    required
                    value={formData.leadCoachName}
                    onChange={(e) => setFormData({ ...formData, leadCoachName: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Facility / Court</label>
                  <input
                    type="text"
                    required
                    value={formData.facilityName}
                    onChange={(e) => setFormData({ ...formData, facilityName: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={formData.startDate}
                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    required
                    value={formData.endDate}
                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Max Capacity</label>
                  <input
                    type="number"
                    min={5}
                    max={100}
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Fee (₹, 0 if free)</label>
                  <input
                    type="number"
                    min={0}
                    value={formData.feeAmount}
                    onChange={(e) => setFormData({ ...formData, feeAmount: Number(e.target.value) })}
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
                  Create Program
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
