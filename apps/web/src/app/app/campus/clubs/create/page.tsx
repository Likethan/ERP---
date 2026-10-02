"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { useAuth } from "@/lib/auth-context";
import {
  Building2,
  ArrowLeft,
  Save,
  AlertTriangle,
  Info,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CreateClubPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [category, setCategory] = useState<"TECHNICAL" | "CULTURAL" | "LITERARY" | "SPORTS" | "ENTREPRENEURSHIP">("TECHNICAL");
  const [description, setDescription] = useState("");
  const [facultyCoordinator, setFacultyCoordinator] = useState("");
  const [facultyCoordinatorEmail, setFacultyCoordinatorEmail] = useState("");
  const [studentLead, setStudentLead] = useState("");
  const [studentLeadRollNo, setStudentLeadRollNo] = useState("");
  const [meetingSchedule, setMeetingSchedule] = useState("Every Wednesday at 04:30 PM");
  const [meetingVenue, setMeetingVenue] = useState("CS-LAB-3");
  const [establishedYear, setEstablishedYear] = useState(2026);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !code.trim() || !description.trim()) {
      setError("Please complete all required fields.");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const res = await campusService.createClub({
        name,
        code: code.toUpperCase(),
        category,
        description,
        facultyCoordinator: facultyCoordinator || "Prof. Coordinator",
        facultyCoordinatorEmail: facultyCoordinatorEmail || "coordinator@campusos.edu",
        studentLead: studentLead || "Student Lead",
        studentLeadRollNo: studentLeadRollNo || "CS23B001",
        meetingSchedule,
        meetingVenue,
        establishedYear,
        status: "ACTIVE",
      }, user?.first_name || "Administrator");

      if (res.success && res.data) {
        router.push(`/app/campus/clubs/${res.data.id}`);
      } else {
        setError(res.error || "Failed to charter club");
      }
    } catch (err: any) {
      setError(err.message || "Failed to save club");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto pb-16">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <Link
          href="/app/campus/clubs"
          className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1.5 transition-colors mb-2"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Clubs Directory
        </Link>
        <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
          <Building2 className="h-6 w-6 text-cyan-400" />
          Charter a New Student Club or Society
        </h1>
        <p className="mt-1 text-xs text-slate-400">
          Submit official guild charter, governance structure, advisor assignment, and meeting schedules.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Club Full Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Autonomous Drone Systems Society"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Short Code <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. DRONE"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white font-mono uppercase focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Guild Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="TECHNICAL">TECHNICAL</option>
              <option value="CULTURAL">CULTURAL</option>
              <option value="LITERARY">LITERARY</option>
              <option value="SPORTS">SPORTS</option>
              <option value="ENTREPRENEURSHIP">ENTREPRENEURSHIP</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Established Year</label>
            <input
              type="number"
              value={establishedYear}
              onChange={(e) => setEstablishedYear(parseInt(e.target.value, 10))}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white font-mono"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-300 block mb-1">
            Charter Description & Mission Statement <span className="text-rose-400">*</span>
          </label>
          <textarea
            required
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Outline club objectives, projects, workshops, and student cohort participation..."
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Faculty Coordinator Name</label>
            <input
              type="text"
              value={facultyCoordinator}
              onChange={(e) => setFacultyCoordinator(e.target.value)}
              placeholder="e.g. Dr. Rajesh Sharma"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Faculty Coordinator Email</label>
            <input
              type="email"
              value={facultyCoordinatorEmail}
              onChange={(e) => setFacultyCoordinatorEmail(e.target.value)}
              placeholder="e.g. rajesh.sharma@campusos.edu"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Founding Student Lead Name</label>
            <input
              type="text"
              value={studentLead}
              onChange={(e) => setStudentLead(e.target.value)}
              placeholder="e.g. Aarav Patel"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Student Lead Roll Number</label>
            <input
              type="text"
              value={studentLeadRollNo}
              onChange={(e) => setStudentLeadRollNo(e.target.value)}
              placeholder="e.g. CS23B101"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white font-mono"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Regular Meeting Schedule</label>
            <input
              type="text"
              value={meetingSchedule}
              onChange={(e) => setMeetingSchedule(e.target.value)}
              placeholder="e.g. Every Thursday at 05:00 PM"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Regular Meeting Venue</label>
            <input
              type="text"
              value={meetingVenue}
              onChange={(e) => setMeetingVenue(e.target.value)}
              placeholder="e.g. Turing Lab / Room CS-104"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Link href="/app/campus/clubs">
            <Button variant="ghost" size="sm">
              Cancel
            </Button>
          </Link>

          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={saving}
            leftIcon={<Save className="h-4 w-4" />}
            className="bg-cyan-600 hover:bg-cyan-500 shadow-md shadow-cyan-600/30"
          >
            Charter Club
          </Button>
        </div>
      </form>
    </div>
  );
}
