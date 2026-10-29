"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import { MenteeItem } from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  GraduationCap,
  Search,
  Calendar,
  Sparkles,
  ArrowRightLeft,
  Clock,
  UserCheck,
  ChevronRight,
  PlusCircle,
  FileText,
} from "lucide-react";

export default function MenteeDirectoryPage() {
  const [mentees, setMentees] = useState<MenteeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [yearFilter, setYearFilter] = useState("ALL");

  useEffect(() => {
    loadMentees();
  }, []);

  async function loadMentees() {
    setLoading(true);
    try {
      const data = await StudentSupportService.getAssignedMentees();
      setMentees(data);
    } catch (err) {
      console.error("Failed to load mentees:", err);
    } finally {
      setLoading(false);
    }
  }

  const filteredMentees = mentees.filter((m) => {
    const sName = m.student_name || m.studentName || "";
    const sReg = m.student_reg_no || m.rollNumber || "";
    const pName = m.program_name || m.programName || "";
    const ySem = m.current_year_semester || m.academicYear || "";
    const matchesSearch =
      sName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sReg.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesYear = yearFilter === "ALL" || ySem.includes(yearFilter);
    return matchesSearch && matchesYear;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Mentee Directory", href: "/app/student-support/mentees" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <GraduationCap className="h-6 w-6 text-indigo-400" />
              Faculty Mentee Directory
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Track student progress, schedule mentoring touchpoints, and review individual growth milestones.
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/app/student-support/sessions">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white">
                <Calendar className="mr-1.5 h-3.5 w-3.5" />
                Schedule Session
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <StudentSupportNav />

      {/* KPI Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Assigned Mentees"
          value={loading ? "..." : mentees.length.toString()}
          icon={<GraduationCap className="h-5 w-5 text-indigo-400" />}
          description="Assigned student cohort"
        />
        <StatCard
          title="Active Development Plans"
          value={loading ? "..." : mentees.filter((m) => m.has_active_development_plan).length.toString()}
          icon={<Sparkles className="h-5 w-5 text-purple-400" />}
          description="With published IDP goals"
        />
        <StatCard
          title="Pending Tasks"
          value={loading ? "..." : mentees.reduce((acc, m) => acc + (m.pending_action_items_count ?? 0), 0).toString()}
          icon={<Clock className="h-5 w-5 text-orange-400" />}
          description="Open mentee action items"
        />
        <StatCard
          title="Avg Cohort Progress"
          value={loading ? "..." : "72%"}
          icon={<UserCheck className="h-5 w-5 text-emerald-400" />}
          description="Milestone completion rate"
        />
      </div>

      {/* Filter and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search assigned mentees by name, register number, or program..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Semesters</option>
            <option value="Sem 3">Semester 3</option>
            <option value="Sem 5">Semester 5</option>
            <option value="Sem 7">Semester 7</option>
          </select>
        </div>
      </Card>

      {/* Mentees Grid / List */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading assigned mentees...</div>
      ) : filteredMentees.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No assigned mentees found matching your search.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMentees.map((mentee) => (
            <Card
              key={mentee.student_id || mentee.studentId || mentee.assignmentId}
              className="border-slate-800 bg-slate-900/60 p-5 space-y-4 hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-white text-sm">{mentee.student_name || mentee.studentName}</h3>
                  <div className="text-xs text-slate-400">{mentee.student_reg_no || mentee.rollNumber}</div>
                  <div className="text-[11px] text-indigo-400 mt-0.5">
                    {mentee.program_name || mentee.programName} • {mentee.current_year_semester || mentee.academicYear}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-semibold text-emerald-400">
                    CGPA: {mentee.cgpa?.toFixed(2) ?? "N/A"}
                  </div>
                  <Badge variant="outline" className="mt-1 border-slate-700 text-slate-400 text-[10px]">
                    {mentee.academic_status ?? "Good Standing"}
                  </Badge>
                </div>
              </div>

              {/* IDP Progress Bar */}
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">IDP Progress:</span>
                  <span className="text-indigo-400 font-medium">
                    {mentee.development_progress_pct ?? 0}%
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${mentee.development_progress_pct ?? 0}%` }}
                  />
                </div>
              </div>

              {/* Mentoring Touchpoint Info */}
              <div className="text-xs text-slate-400 space-y-1 border-t border-slate-800/80 pt-3">
                <div className="flex items-center justify-between">
                  <span>Last Session:</span>
                  <span className="text-slate-200">
                    {mentee.last_mentoring_date
                      ? new Date(mentee.last_mentoring_date).toLocaleDateString()
                      : "No prior sessions"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Pending Action Items:</span>
                  <span
                    className={
                      (mentee.pending_action_items_count ?? 0) > 0
                        ? "text-orange-400 font-medium"
                        : "text-slate-400"
                    }
                  >
                    {mentee.pending_action_items_count ?? 0}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-between gap-2">
                <Link href={`/app/student-support/development-plans?student_id=${mentee.student_id || mentee.studentId}`} className="flex-1">
                  <Button variant="outline" size="sm" className="w-full text-xs border-slate-700 hover:bg-slate-800">
                    <Sparkles className="mr-1.5 h-3.5 w-3.5 text-purple-400" />
                    IDP Goals
                  </Button>
                </Link>
                <Link href={`/app/student-support/sessions?student_id=${mentee.student_id || mentee.studentId}`} className="flex-1">
                  <Button size="sm" className="w-full text-xs bg-indigo-600 hover:bg-indigo-700 text-white">
                    <Calendar className="mr-1.5 h-3.5 w-3.5" />
                    Session
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
