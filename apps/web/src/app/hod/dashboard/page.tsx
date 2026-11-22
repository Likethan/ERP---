"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { hodService, HodDashboardStats } from "@/services/hod.service";
import {
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from "lucide-react";

export default function HodDashboardPage() {
  const { user, activePersona } = useAuth();
  const [data, setData] = useState<HodDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const deptName =
    activePersona?.department || "Computer Science & Engineering";
  const userName = activePersona?.name || user?.name || "Dr. K. S. Anand";
  const userInitials =
    userName
      .split(" ")
      .map((n) => n[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() || "KA";

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const res = await hodService.getDashboardStats(deptName);
        if (res.success && res.data) {
          setData(res.data);
        } else {
          setError("Failed to load department statistics.");
        }
      } catch (err) {
        console.error("HOD Dashboard load error:", err);
        setError("Unable to connect to departmental services.");
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [deptName]);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-28 rounded-md bg-white border border-[#DCE3EB] p-4" />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-md bg-white border border-[#DCE3EB]"
            />
          ))}
        </div>
        <div className="h-10 rounded-md bg-white border border-[#DCE3EB]" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-8 h-96 rounded-md bg-white border border-[#DCE3EB]" />
          <div className="lg:col-span-4 h-96 rounded-md bg-white border border-[#DCE3EB]" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center rounded-md border border-red-200 bg-red-50 text-red-900">
        <AlertTriangle className="h-8 w-8 mx-auto text-red-500 mb-2" />
        <h2 className="text-base font-bold">Department Data Unavailable</h2>
        <p className="text-xs mt-1 text-red-700">
          {error || "Could not retrieve records."}
        </p>
        <button
          className="mt-3 px-3 py-1.5 text-xs font-semibold bg-white border border-red-300 rounded text-red-800 hover:bg-red-100"
          onClick={() => window.location.reload()}
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const stats = data.statistics;

  return (
    <div className="space-y-3.5 text-[#172338]">
      {/* 1. HERO IDENTITY CARD (Matching Top Reference Card) */}
      <div className="bg-white border border-[#DCE3EB] rounded-md p-4 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Avatar + Academic Title + Tags */}
        <div className="flex items-start sm:items-center gap-3.5">
          <div className="h-13 w-13 rounded bg-[#183153] text-white flex items-center justify-center font-black text-xl tracking-wider shrink-0 shadow-xs">
            {userInitials}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-base sm:text-lg font-black tracking-tight text-[#172338] uppercase">
                {userName}
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#DCE3EB] text-[#64748B] bg-slate-50 font-medium">
                2026-CSE-HOD
              </span>
              <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#16A34A]" />
                ACTIVE HOD
              </span>
            </div>
            <p className="text-xs text-[#64748B] mt-0.5 font-medium">
              Professor & Head of Department • {data.department.name} • Section
              A, B & C
            </p>
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#64748B] mt-1">
              <span>Department Office: Block C (Tech Tower) Room #204</span>
              <span>•</span>
              <span>Wednesday, Nov 18, 2026</span>
              <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-[#183153] text-white ml-1">
                Fall Term • Week 14
              </span>
            </div>
          </div>
        </div>

        {/* Right: Department Compliance Badge (Matching Green Right Box in Reference) */}
        <div className="bg-[#ECFDF5] border border-[#A7F3D0] rounded p-3 min-w-[270px] shrink-0 text-left md:text-right">
          <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#16A34A]">
            DEPARTMENT STATUS: HIGH COMPLIANCE
          </div>
          <div className="text-[10px] font-mono text-[#64748B] mt-0.5">
            TOKEN: HOD-CSE-2026
          </div>
          <div className="text-[11px] text-[#065F46] font-medium mt-1">
            All 6 Accreditation & Statutory Prerequisites Validated
          </div>
        </div>
      </div>

      {/* 2. STATISTIC METRIC CARDS ROW (6 Small Compact Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* Card 1: Aggregate Attendance */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Aggregate Attendance</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
              SAFE ZONE
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">
                {stats.averageStudentAttendance}%
              </span>
              <span className="text-[10px] text-[#64748B]">/ 75% req</span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              Attended: 246 hrs •{" "}
              <span className="text-[#16A34A] font-semibold">+1.2% wk</span>
            </div>
          </div>
        </div>

        {/* Card 2: Academic Standing */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Academic Standing</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
              TOP 2.5%
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">9.12</span>
              <span className="text-[10px] text-[#64748B]">
                Cumulative CGPA
              </span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              Rank #01/08 Depts •{" "}
              <span className="font-semibold text-[#172338]">0 Backlogs</span>
            </div>
          </div>
        </div>

        {/* Card 3: Faculty Workload & Cadre */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Faculty Compliance</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
              CLEARED
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">
                {stats.totalFaculty}/{stats.totalFaculty}
              </span>
              <span className="text-[10px] text-[#64748B]">Active Cadre</span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              Cadre 1:2:6 • Ph.D Ratio 64.3%
            </div>
          </div>
        </div>

        {/* Card 4: Career & Placements */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Career & Placements</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
              TIER-1 (AWS 24.5 LPA)
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">144</span>
              <span className="text-[10px] text-[#64748B]">Offers Secured</span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              87.8% Placed • Top: ₹24.5 LPA
            </div>
          </div>
        </div>

        {/* Card 5: Statutory Approvals */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Statutory Approvals</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA]">
              ACTION REQ
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">
                {stats.pendingApprovalRequests}
              </span>
              <span className="text-[10px] text-[#64748B]">Pending</span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              2 Faculty Leave • 2 Events • 1 OD
            </div>
          </div>
        </div>

        {/* Card 6: Budget & Grants */}
        <div className="bg-white border border-[#DCE3EB] rounded-md p-3 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
            <span>Budget & Grants</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
              CLEARED
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-black text-[#172338]">₹18.4L</span>
              <span className="text-[10px] text-[#64748B]">of ₹25.0L</span>
            </div>
            <div className="text-[10px] text-[#64748B] mt-1">
              Q4 Utilization: 73.6% • Clean Audit
            </div>
          </div>
        </div>
      </div>

      {/* 3. QUICK ACCESS BAR (Horizontal Pill Buttons) */}
      <div className="bg-white border border-[#DCE3EB] rounded-md px-3.5 py-2 flex items-center gap-2 overflow-x-auto shadow-2xs">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748B] shrink-0 mr-1">
          QUICK ACCESS:
        </span>
        <div className="flex items-center gap-2">
          <Link
            href="/hod/faculty"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Faculty Directory ({stats.totalFaculty})
          </Link>
          <Link
            href="/hod/students"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Student Registry ({stats.totalStudents})
          </Link>
          <Link
            href="/hod/attendance"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Attendance Shortage ({stats.studentsShortageCount})
          </Link>
          <Link
            href="/hod/timetable"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Master Timetable
          </Link>
          <Link
            href="/hod/curriculum"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Curriculum R-2026
          </Link>
          <Link
            href="/hod/approvals"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Approvals Hub ({stats.pendingApprovalRequests})
          </Link>
          <Link
            href="/hod/results"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Results & GPA (90.8%)
          </Link>
          <Link
            href="/hod/reports"
            className="px-2.5 py-1 text-[11px] font-semibold text-[#172338] bg-slate-50 hover:bg-slate-100 border border-[#DCE3EB] rounded transition-colors whitespace-nowrap"
          >
            Reports Engine
          </Link>
        </div>
      </div>

      {/* 4. MAIN TWO-COLUMN CONTENT AREA (Matches Left 70% and Right 30%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (8 cols): Today's Schedule + Registered Courses Table + Placement Telemetry */}
        <div className="lg:col-span-8 space-y-4">
          {/* A. TODAY'S CLASS / INSTRUCTIONAL SCHEDULE */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2.5 border-b border-[#DCE3EB]">
              <div className="flex items-center gap-2">
                <span className="bg-[#183153] text-white text-[10px] font-bold px-2 py-0.5 rounded">
                  DAY ORDER 3
                </span>
                <span className="text-xs font-black uppercase tracking-wider text-[#172338]">
                  TODAY&apos;S DEPARTMENT INSTRUCTIONAL SCHEDULE
                </span>
              </div>
              <span className="text-[11px] text-[#64748B] font-medium">
                4 Sessions Scheduled
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {/* Period 1 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 flex items-center justify-between bg-white hover:bg-slate-50/60 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="bg-[#183153] text-white text-[10px] font-mono font-bold px-2 py-1 rounded text-center min-w-[54px] shrink-0 leading-tight">
                    <div>P1</div>
                    <div className="text-[9px] opacity-80">08:45</div>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#172338]">
                        CS501 Distributed Systems
                      </span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                        ATTENDED
                      </span>
                    </div>
                    <div className="text-[11px] text-[#64748B] truncate mt-0.5">
                      Prof. S. Meenakshi • Lecture Hall LH-302
                    </div>
                  </div>
                </div>
                <div className="text-xs font-mono font-semibold text-[#172338] shrink-0 ml-2">
                  08:45 - 09:45 AM
                </div>
              </div>

              {/* Period 2 (IN SESSION - WARM GOLD HIGHLIGHT!) */}
              <div className="border border-[#F59E0B] rounded p-2.5 flex items-center justify-between bg-[#FEFCE8] ring-1 ring-[#F59E0B]/30 shadow-2xs">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="bg-[#D97706] text-white text-[10px] font-mono font-bold px-2 py-1 rounded text-center min-w-[54px] shrink-0 leading-tight shadow-xs">
                    <div>P2</div>
                    <div className="text-[9px] opacity-90">10:00</div>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#172338]">
                        CS502 Compiler Design
                      </span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A] animate-pulse">
                        IN SESSION
                      </span>
                    </div>
                    <div className="text-[11px] text-[#92400E] font-medium truncate mt-0.5">
                      Dr. K. Ramanathan (HOD CSE) • LH-302
                    </div>
                  </div>
                </div>
                <div className="text-xs font-mono font-bold text-[#92400E] shrink-0 ml-2">
                  10:00 - 11:00 AM
                </div>
              </div>

              {/* Period 3 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 flex items-center justify-between bg-white hover:bg-slate-50/60 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="bg-[#183153] text-white text-[10px] font-mono font-bold px-2 py-1 rounded text-center min-w-[54px] shrink-0 leading-tight">
                    <div>P3</div>
                    <div className="text-[9px] opacity-80">11:15</div>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#172338]">
                        CS503 Deep Learning Architectures
                      </span>
                    </div>
                    <div className="text-[11px] text-[#64748B] truncate mt-0.5">
                      Dr. P. Venkatesh • AI Lab 2
                    </div>
                  </div>
                </div>
                <div className="text-xs font-mono font-semibold text-[#172338] shrink-0 ml-2">
                  11:15 - 12:15 PM
                </div>
              </div>

              {/* Period 4 / Lab */}
              <div className="border border-[#DCE3EB] rounded p-2.5 flex items-center justify-between bg-white hover:bg-slate-50/60 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="bg-[#183153] text-white text-[10px] font-mono font-bold px-2 py-1 rounded text-center min-w-[54px] shrink-0 leading-tight">
                    <div>LAB</div>
                    <div className="text-[9px] opacity-80">01:15</div>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#172338]">
                        CS504 Cloud Computing & DevOps Lab
                      </span>
                    </div>
                    <div className="text-[11px] text-[#64748B] truncate mt-0.5">
                      Er. M. Divya & Team • Lab-4 (418)
                    </div>
                  </div>
                </div>
                <div className="text-xs font-mono font-semibold text-[#172338] shrink-0 ml-2">
                  01:15 - 04:15 PM
                </div>
              </div>
            </div>
          </div>

          {/* B. REGISTERED COURSES & ASSESSMENTS TABLE */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2.5 border-b border-[#DCE3EB]">
              <div>
                <h3 className="text-xs font-black uppercase tracking-wider text-[#172338]">
                  REGISTERED COURSES & ASSESSMENTS
                </h3>
                <p className="text-[10px] text-[#64748B]">
                  Semester 5 • 23 Total Academic Credits
                </p>
              </div>
              <span className="text-[11px] font-mono text-[#64748B]">
                Theory: 18 Cr | Lab: 5 Cr
              </span>
            </div>

            <div className="mt-2.5 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#DCE3EB] text-[10px] font-bold uppercase text-[#64748B] tracking-wider">
                    <th className="pb-2 font-bold">Course Code & Title</th>
                    <th className="pb-2 font-bold">Instructor</th>
                    <th className="pb-2 font-bold text-center">CR</th>
                    <th className="pb-2 font-bold">Attendance</th>
                    <th className="pb-2 font-bold text-center">CIA-1</th>
                    <th className="pb-2 font-bold text-center">CIA-2</th>
                    <th className="pb-2 font-bold text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F5F9]">
                  {/* Row 1 */}
                  <tr className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 pr-2">
                      <div className="font-bold text-[#172338]">
                        CS501 Distributed Systems
                      </div>
                      <div className="text-[10px] text-[#64748B]">
                        Core Engineering
                      </div>
                    </td>
                    <td className="py-2.5 text-[#172338] text-[11px]">
                      Prof. S. Meenakshi
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px]">
                      4.0
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-[#183153] rounded-full"
                            style={{ width: "91%" }}
                          />
                        </div>
                        <span className="text-[11px] font-bold text-[#172338] font-mono">
                          91%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      46/50
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      48/50
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                        Eligible (O)
                      </span>
                    </td>
                  </tr>

                  {/* Row 2 */}
                  <tr className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 pr-2">
                      <div className="font-bold text-[#172338]">
                        CS502 Compiler Design
                      </div>
                      <div className="text-[10px] text-[#64748B]">
                        Core Systems
                      </div>
                    </td>
                    <td className="py-2.5 text-[#172338] text-[11px]">
                      Dr. K. Ramanathan
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px]">
                      4.0
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-[#183153] rounded-full"
                            style={{ width: "86%" }}
                          />
                        </div>
                        <span className="text-[11px] font-bold text-[#172338] font-mono">
                          86%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      44/50
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      45/50
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                        Eligible (A+)
                      </span>
                    </td>
                  </tr>

                  {/* Row 3 */}
                  <tr className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 pr-2">
                      <div className="font-bold text-[#172338]">
                        CS503 Deep Learning
                      </div>
                      <div className="text-[10px] text-[#64748B]">
                        Professional Elective
                      </div>
                    </td>
                    <td className="py-2.5 text-[#172338] text-[11px]">
                      Dr. P. Venkatesh
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px]">
                      3.0
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-[#183153] rounded-full"
                            style={{ width: "94%" }}
                          />
                        </div>
                        <span className="text-[11px] font-bold text-[#172338] font-mono">
                          94%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      49/50
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      50/50
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                        Eligible (O)
                      </span>
                    </td>
                  </tr>

                  {/* Row 4 */}
                  <tr className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 pr-2">
                      <div className="font-bold text-[#172338]">
                        CS504 Cloud & DevOps Lab
                      </div>
                      <div className="text-[10px] text-[#64748B]">
                        Practical Course
                      </div>
                    </td>
                    <td className="py-2.5 text-[#172338] text-[11px]">
                      Er. M. Divya
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px]">
                      2.0
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-[#183153] rounded-full"
                            style={{ width: "92%" }}
                          />
                        </div>
                        <span className="text-[11px] font-bold text-[#172338] font-mono">
                          92%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      47/50
                    </td>
                    <td className="py-2.5 text-center font-mono text-[11px] text-[#64748B]">
                      48/50
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-[#64748B] border border-slate-200">
                        Completed
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* C. PLACEMENT TELEMETRY & DRIVES */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2.5 border-b border-[#DCE3EB]">
              <div>
                <h3 className="text-xs font-black uppercase tracking-wider text-[#172338]">
                  PLACEMENT TELEMETRY & DRIVES
                </h3>
                <p className="text-[10px] text-[#64748B]">
                  Campus Placement Cell • 2026 Batch Priority Track
                </p>
              </div>
              <Link
                href="/hod/placements"
                className="text-[11px] font-semibold text-[#183153] hover:underline flex items-center gap-1"
              >
                View All 14 Drives <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-2.5">
              {/* Ticker 1 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50 flex flex-col justify-between">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-bold text-[#B45309] bg-[#FEF3C7] px-1.5 py-0.2 rounded border border-[#FDE68A]">
                    SUPER DREAM
                  </span>
                  <span className="font-mono font-bold text-[#172338]">
                    ₹24.5 LPA
                  </span>
                </div>
                <div className="mt-1.5">
                  <div className="text-xs font-bold text-[#172338]">
                    Amazon SDE-1
                  </div>
                  <div className="text-[10px] text-[#64748B]">
                    AWS Cloud Infra
                  </div>
                </div>
                <div className="mt-2 text-right">
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                    OFFER ACCEPTED
                  </span>
                </div>
              </div>

              {/* Ticker 2 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50 flex flex-col justify-between">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-bold text-[#1D4ED8] bg-[#EFF6FF] px-1.5 py-0.2 rounded border border-[#DBEAFE]">
                    PRODUCT
                  </span>
                  <span className="font-mono font-bold text-[#172338]">
                    ₹15.0 LPA
                  </span>
                </div>
                <div className="mt-1.5">
                  <div className="text-xs font-bold text-[#172338]">
                    Cisco Systems
                  </div>
                  <div className="text-[10px] text-[#64748B]">
                    Software Engineer
                  </div>
                </div>
                <div className="mt-2 text-right">
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                    OFFER ACCEPTED
                  </span>
                </div>
              </div>

              {/* Ticker 3 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50 flex flex-col justify-between">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-bold text-[#6D28D9] bg-[#F5F3FF] px-1.5 py-0.2 rounded border border-[#EDE9FE]">
                    DIGITAL
                  </span>
                  <span className="font-mono font-bold text-[#172338]">
                    ₹7.5 LPA
                  </span>
                </div>
                <div className="mt-1.5">
                  <div className="text-xs font-bold text-[#172338]">
                    TCS Digital
                  </div>
                  <div className="text-[10px] text-[#64748B]">
                    Full Stack Engineer
                  </div>
                </div>
                <div className="mt-2 text-right">
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-slate-100 text-[#64748B] border border-slate-200">
                    ELIGIBLE (34)
                  </span>
                </div>
              </div>

              {/* Ticker 4 */}
              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50 flex flex-col justify-between">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-bold text-[#475569] bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                    ENTERPRISE
                  </span>
                  <span className="font-mono font-bold text-[#172338]">
                    ₹6.5 LPA
                  </span>
                </div>
                <div className="mt-1.5">
                  <div className="text-xs font-bold text-[#172338]">
                    Cognizant GenC
                  </div>
                  <div className="text-[10px] text-[#64748B]">
                    Developer Associate
                  </div>
                </div>
                <div className="mt-2 text-right">
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
                    IN PROGRESS
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Labs Logistics + Campus Circulars + Consultation / Approvals CTA */}
        <div className="lg:col-span-4 space-y-4">
          {/* 1. DEPARTMENT LABS & LOGISTICS */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#DCE3EB]">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#172338]">
                DEPARTMENT LABS & LOGISTICS
              </h3>
            </div>
            <div className="mt-2.5 space-y-2.5">
              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#172338]">
                    Turing Research & AI Center
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECFDF5] text-[#16A34A] border border-[#A7F3D0]">
                    ALLOCATED
                  </span>
                </div>
                <div className="text-[11px] text-[#64748B] mt-1">
                  Block D (Turing Towers) • Room 402 • 75 Workstations • Curfew
                  09:00 PM
                </div>
              </div>

              <div className="border border-[#DCE3EB] rounded p-2.5 bg-slate-50/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#172338]">
                    Transit Fleet & Campus HPC
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#183153] text-white">
                    ROUTE #16
                  </span>
                </div>
                <div className="text-[11px] text-[#64748B] mt-1">
                  Bus TN-47-E-9021 • Karur Central ↔ Campus • On-Time (Depot)
                </div>
              </div>
            </div>
          </div>

          {/* 2. CAMPUS CIRCULARS */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#DCE3EB]">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#172338]">
                CAMPUS CIRCULARS
              </h3>
              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
                3 NEW
              </span>
            </div>

            <div className="mt-2.5 space-y-3">
              <div className="border-b border-slate-100 pb-2">
                <div className="flex items-center justify-between text-[10px] text-[#64748B]">
                  <span className="font-bold text-[#183153] uppercase">
                    DEAN CELL
                  </span>
                  <span>Today • 08:15 AM</span>
                </div>
                <div className="text-xs font-bold text-[#172338] mt-0.5">
                  End-Semester Practical Exam Schedule Published
                </div>
                <div className="text-[11px] text-[#64748B] mt-0.5 leading-snug">
                  Office of CoE has released laboratory timetable for 5th
                  semester B.Tech CSE.
                </div>
              </div>

              <div className="border-b border-slate-100 pb-2">
                <div className="flex items-center justify-between text-[10px] text-[#64748B]">
                  <span className="font-bold text-[#183153] uppercase">
                    R&D CELL
                  </span>
                  <span>Yesterday</span>
                </div>
                <div className="text-xs font-bold text-[#172338] mt-0.5">
                  Smart India National Hackathon Registration
                </div>
                <div className="text-[11px] text-[#64748B] mt-0.5 leading-snug">
                  Internal team submissions close Nov 24. Screening
                  presentations next week.
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-[10px] text-[#64748B]">
                  <span className="font-bold text-[#183153] uppercase">
                    IEEE BRANCH
                  </span>
                  <span>Nov 16</span>
                </div>
                <div className="text-xs font-bold text-[#172338] mt-0.5">
                  Keynote: Generative AI on Edge Silicon
                </div>
                <div className="text-[11px] text-[#64748B] mt-0.5 leading-snug">
                  Speaker Dr. Aravind from IISc Bangalore. Main Auditorium at
                  10:30 AM.
                </div>
              </div>
            </div>
          </div>

          {/* 3. FACULTY MENTOR / HOD CONSULTATION & STATUTORY ACTION CTA */}
          <div className="bg-white border border-[#DCE3EB] rounded-md p-3.5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#DCE3EB]">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#172338]">
                DEPARTMENT FACULTY & STUDENTS CONSULTATION
              </h3>
            </div>
            <div>
              <div className="text-xs font-bold text-[#172338]">
                Dr. K. Ramanathan, Ph.D.
              </div>
              <div className="text-[11px] text-[#64748B]">
                Professor & Head, Dept of CSE • Room 204
              </div>
              <div className="text-[11px] font-medium text-[#D97706] mt-1">
                Next Slot: Tomorrow • 03:00 PM
              </div>
            </div>

            <Link
              href="/hod/approvals"
              className="block w-full py-2.5 px-3 bg-[#183153] hover:bg-[#1E3A5F] text-white text-xs font-bold uppercase tracking-wider rounded text-center transition-colors shadow-xs"
            >
              REVIEW PENDING STATUTORY APPROVALS (
              {stats.pendingApprovalRequests})
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
