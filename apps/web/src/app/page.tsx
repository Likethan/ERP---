"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileCode2,
  ArrowRight,
  GraduationCap,
  Building,
  UserCheck,
  Users,
  Landmark,
  Briefcase,
  Calendar,
  CheckSquare,
  FileSpreadsheet,
  Bot,
  Sparkles,
  Home,
  FileText,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";

interface ApiHealthState {
  status: "checking" | "connected" | "unreachable";
  service?: string;
  version?: string;
}

export default function CampusOSPortalPage() {
  const router = useRouter();
  const { switchPersona } = useAuth();
  const [apiHealth, setApiHealth] = useState<ApiHealthState>({
    status: "checking",
  });

  useEffect(() => {
    async function checkApi() {
      try {
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/health`, {
          cache: "no-store",
        });
        if (res.ok) {
          const data = await res.json();
          setApiHealth({
            status: "connected",
            service: data.data?.service || "CampusOS API",
            version: data.data?.version || "0.1.0",
          });
        } else {
          setApiHealth({ status: "unreachable" });
        }
      } catch {
        setApiHealth({ status: "unreachable" });
      }
    }
    checkApi();
  }, []);

  const handleLaunchPersona = (role: string) => {
    switchPersona(role);
    router.push("/app/dashboard");
  };

  const domainModules = [
    {
      id: "people",
      name: "People & Directory",
      desc: "Unified student profiles, faculty credentials, administrative staff, and guardians with role governance.",
      href: "/app/students",
      badge: "6 Sub-routes",
      icon: <Users className="h-5 w-5 text-blue-600" />,
      sublinks: [
        { label: "Students", href: "/app/students" },
        { label: "Faculty", href: "/app/faculty" },
        { label: "Staff", href: "/app/staff" },
      ],
    },
    {
      id: "academics",
      name: "Academics & Curricula",
      desc: "Academic calendar schemes, department syllabus units, course offerings, and conflict-free timetables.",
      href: "/app/academics",
      badge: "7 Sub-routes",
      icon: <FileSpreadsheet className="h-5 w-5 text-indigo-600" />,
      sublinks: [
        { label: "Curricula", href: "/app/academics/curricula" },
        { label: "Subjects", href: "/app/academics/subjects" },
        { label: "Offerings", href: "/app/academics/course-offerings" },
        { label: "Timetable", href: "/app/academics/timetable" },
      ],
    },
    {
      id: "attendance",
      name: "Attendance Engine",
      desc: "Session registries, biometric check-ins, medical leave applications, and immutable lock validation.",
      href: "/app/attendance",
      badge: "8 Sub-routes",
      icon: <CheckSquare className="h-5 w-5 text-emerald-600" />,
      sublinks: [
        { label: "Sessions", href: "/app/attendance/sessions" },
        { label: "Student Roster", href: "/app/attendance/students" },
        { label: "Leaves", href: "/app/attendance/leaves" },
        { label: "Policies", href: "/app/attendance/policies" },
      ],
    },
    {
      id: "examinations",
      name: "Examinations & Grading",
      desc: "Continuous internal assessments, university semester schedules, marks entry, and GPA computation.",
      href: "/app/examinations",
      badge: "5 Sub-routes",
      icon: <GraduationCap className="h-5 w-5 text-amber-600" />,
      sublinks: [
        { label: "Assessments", href: "/app/examinations/assessments" },
        { label: "Schedules", href: "/app/examinations/schedules" },
        { label: "Marks Entry", href: "/app/examinations/marks" },
        { label: "Results", href: "/app/examinations/results" },
      ],
    },
    {
      id: "finance",
      name: "Finance & Fee Ledger",
      desc: "Institutional fee catalogs, automated billing invoices, payment processing, receipts, and refund requests.",
      href: "/app/finance",
      badge: "7 Sub-routes",
      icon: <Landmark className="h-5 w-5 text-teal-600" />,
      sublinks: [
        { label: "Structures", href: "/app/finance/fee-structures" },
        { label: "Invoices", href: "/app/finance/invoices" },
        { label: "Payments", href: "/app/finance/payments" },
        { label: "Scholarships", href: "/app/finance/scholarships" },
      ],
    },
    {
      id: "placement",
      name: "Placement & Corporate",
      desc: "Corporate directory, recruitment drives, automated eligibility filtering (CGPA, backlogs), and offer tracking.",
      href: "/app/placement",
      badge: "6 Tabs",
      icon: <Briefcase className="h-5 w-5 text-purple-600" />,
      sublinks: [
        { label: "Companies", href: "/app/placement" },
        { label: "Job Drives", href: "/app/placement" },
        { label: "Eligibility", href: "/app/placement" },
        { label: "Offers", href: "/app/placement" },
      ],
    },
    {
      id: "campus",
      name: "Campus Life & Events",
      desc: "Student clubs, executive council approvals, campus festival events, and cross-institution broadcasts.",
      href: "/app/events",
      badge: "8 Sub-routes",
      icon: <Calendar className="h-5 w-5 text-rose-600" />,
      sublinks: [
        { label: "Events", href: "/app/events" },
        { label: "Clubs", href: "/app/clubs" },
        { label: "Announcements", href: "/app/announcements" },
        { label: "Notifications", href: "/app/notifications" },
      ],
    },
    {
      id: "infrastructure",
      name: "Hostel & Transport Fleet",
      desc: "Residential block allocations, room inventories, warden logs, vehicle fleet GPS routes, and pick-up stops.",
      href: "/app/hostel",
      badge: "Residential & Fleet",
      icon: <Home className="h-5 w-5 text-sky-600" />,
      sublinks: [
        { label: "Hostel Blocks", href: "/app/hostel" },
        { label: "Transport Fleet", href: "/app/transport" },
      ],
    },
    {
      id: "documents",
      name: "Documents Vault",
      desc: "Secure document repository, bonafide & transcript requests, cryptographic verification, and templating.",
      href: "/app/documents",
      badge: "Audit Ready",
      icon: <FileText className="h-5 w-5 text-slate-700" />,
      sublinks: [
        { label: "Repository", href: "/app/documents" },
        { label: "Certificates", href: "/app/documents" },
        { label: "Verification", href: "/app/documents" },
      ],
    },
    {
      id: "intelligence",
      name: "Executive Intelligence & AI",
      desc: "Strategic leadership dashboards, real-time KPI metrics, and permission-guarded conversational AI assistant.",
      href: "/app/intelligence",
      badge: "AI Powered",
      icon: <Bot className="h-5 w-5 text-indigo-600" />,
      sublinks: [
        { label: "KPI Intelligence", href: "/app/intelligence" },
        { label: "AI Campus Assistant", href: "/app/ai" },
      ],
    },
    {
      id: "academic-structure",
      name: "Core Institutional Structure",
      desc: "Multi-campus hierarchy, institutions, academic faculties, degree programs, and semester batches.",
      href: "/app/academic-structure",
      badge: "Foundational",
      icon: <Building className="h-5 w-5 text-violet-600" />,
      sublinks: [
        { label: "Campuses", href: "/app/campuses" },
        { label: "Institution", href: "/app/institution" },
        { label: "Departments", href: "/app/departments" },
        { label: "Programs", href: "/app/programs" },
      ],
    },
    {
      id: "security",
      name: "Security & Access Governance",
      desc: "Stateless session controls, RBAC & PBAC policies, tenant isolation verification, and immutable audit trails.",
      href: "/app/security",
      badge: "Zero-Trust",
      icon: <ShieldCheck className="h-5 w-5 text-emerald-600" />,
      sublinks: [
        { label: "Role Permissions", href: "/app/security" },
        { label: "Audit Logs", href: "/app/security" },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-between">
      {/* Top Enterprise Navigation */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm tracking-wider shadow-sm">
              COS
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900">
                  CampusOS
                </span>
                <span className="text-xs px-2 py-0.5 font-medium bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                  Enterprise v1.0
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                One Campus. One System. One Source of Truth.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 sm:space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-full border border-slate-200 bg-slate-50">
              <span className="text-slate-500 hidden md:inline">
                API Gateway:
              </span>
              {apiHealth.status === "checking" && (
                <span className="flex items-center text-slate-500">
                  <span className="h-2 w-2 rounded-full bg-slate-400 animate-pulse mr-1.5" />
                  Checking...
                </span>
              )}
              {apiHealth.status === "connected" && (
                <span className="flex items-center text-emerald-700 font-semibold">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 mr-1" />
                  Online ({apiHealth.version})
                </span>
              )}
              {apiHealth.status === "unreachable" && (
                <span
                  className="flex items-center text-amber-700"
                  title="Mock Service Fallback Active"
                >
                  <AlertCircle className="h-3.5 w-3.5 text-amber-600 mr-1" />
                  Mock Services Active
                </span>
              )}
            </div>

            <Link
              href="/login"
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 px-3 py-2 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors"
            >
              Sign In
            </Link>

            <Link
              href="/app/dashboard"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 px-4 py-2 rounded-lg shadow-sm transition-colors"
            >
              <span>Launch Platform</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12 flex-1">
        {/* Hero Section */}
        <section className="bg-white border border-slate-200 rounded-2xl p-8 sm:p-10 shadow-sm relative overflow-hidden">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-800 text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              <span>Full Operational Product Suite Ready</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-950 tracking-tight leading-tight">
              Enterprise Digital Operating System for Modern Colleges
            </h1>
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
              CampusOS unifies academic operations, student governance,
              attendance tracking, examination workflows, fee ledgers,
              placements, residential infrastructure, and executive intelligence
              into a single high-performance enterprise interface.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href="/app/dashboard"
                className="inline-flex items-center gap-2 text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 px-5 py-2.5 rounded-lg shadow-sm transition-all"
              >
                <span>Enter CampusOS Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 text-sm font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 px-5 py-2.5 rounded-lg transition-all border border-slate-200"
              >
                <span>Persona Login & Switcher</span>
              </Link>
              <Link
                href="/app/ai"
                className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-5 py-2.5 rounded-lg transition-all border border-indigo-200"
              >
                <Bot className="h-4 w-4 text-indigo-600" />
                <span>Launch AI Assistant</span>
              </Link>
            </div>
          </div>

          {/* Key Metrics Bar */}
          <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8 border-t border-slate-100">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Total Routes
              </span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                51 Pages
              </span>
              <span className="text-xs text-emerald-700 font-medium mt-0.5 block">
                100% Typed & Linked
              </span>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Domain Modules
              </span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                12 Engines
              </span>
              <span className="text-xs text-indigo-700 font-medium mt-0.5 block">
                Zero Data Duplication
              </span>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Role Personas
              </span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                6 Experiences
              </span>
              <span className="text-xs text-purple-700 font-medium mt-0.5 block">
                Dedicated Dashboards
              </span>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Service Layer
              </span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                Typed Contracts
              </span>
              <span className="text-xs text-sky-700 font-medium mt-0.5 block">
                FastAPI Drop-in Ready
              </span>
            </div>
          </div>
        </section>

        {/* 1-Click Role Switcher Quick Access */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                1-Click Role Experience Launchpad
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Jump directly into CampusOS with tailored views and role
                permissions.
              </p>
            </div>
            <Link
              href="/login"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 self-start sm:self-auto"
            >
              <span>Explore Authentication & Personas</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {DEMO_PERSONAS.map((persona) => (
              <button
                key={persona.role}
                onClick={() => handleLaunchPersona(persona.role)}
                className="flex items-start gap-4 p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-400 hover:shadow-md transition-all text-left group"
              >
                <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors shrink-0">
                  {persona.role === "SUPER_ADMIN" && (
                    <ShieldCheck className="h-5 w-5" />
                  )}
                  {persona.role === "HOD" && <Building className="h-5 w-5" />}
                  {persona.role === "FACULTY" && (
                    <UserCheck className="h-5 w-5" />
                  )}
                  {persona.role === "STUDENT" && (
                    <GraduationCap className="h-5 w-5" />
                  )}
                  {persona.role === "ACCOUNTS" && (
                    <Landmark className="h-5 w-5" />
                  )}
                  {persona.role === "PLACEMENT_OFFICER" && (
                    <Briefcase className="h-5 w-5" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 group-hover:text-indigo-600 transition-colors">
                      {persona.name}
                    </span>
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {persona.role}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {persona.description}
                  </p>
                  <div className="mt-2 text-xs font-semibold text-indigo-600 group-hover:underline flex items-center gap-1">
                    <span>Open Dashboard</span>
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* 12 Operational Domain Catalog */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                12 Enterprise Domain Modules
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Every operational domain is built with interactive tables,
                forms, filters, drawers, and mock services.
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-200 text-slate-800 rounded-md self-start sm:self-auto">
              51 Prerendered Pages
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {domainModules.map((d) => (
              <div
                key={d.id}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-slate-300 hover:shadow transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="h-9 w-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center">
                      {d.icon}
                    </div>
                    <span className="text-xs font-medium px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                      {d.badge}
                    </span>
                  </div>
                  <div>
                    <Link
                      href={d.href}
                      className="font-bold text-base text-slate-900 hover:text-indigo-600 transition-colors flex items-center gap-1"
                    >
                      <span>{d.name}</span>
                      <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                    </Link>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {d.desc}
                    </p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-1.5">
                  {d.sublinks.map((sub, idx) => (
                    <Link
                      key={idx}
                      href={sub.href}
                      className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
                    >
                      {sub.label}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Architectural Baseline Card */}
        <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
          <div className="flex items-center space-x-2 text-slate-900 mb-3">
            <FileCode2 className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-bold">
              Engineering Architecture & Backend Compatibility
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-600 mb-6 leading-relaxed">
            The frontend application is structured with a decoupled service
            adapter layer (`apps/web/src/services`), typed data models from
            `@campusos/types`, and unified canonical entities. When the backend
            FastAPI & PostgreSQL engines are connected, services swap cleanly to
            HTTP calls without UI rewrites.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-900 block">
                Single Truth Entity Model
              </span>
              <span className="text-slate-500 mt-1 block">
                Student, Faculty, Course records never duplicate across modules.
              </span>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-900 block">
                Role-Aware Authorization
              </span>
              <span className="text-slate-500 mt-1 block">
                Client auth context mirrors backend RBAC/PBAC scopes.
              </span>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-900 block">
                Strict Typing & Linting
              </span>
              <span className="text-slate-500 mt-1 block">
                Next.js 15.1 + React 19 + TypeScript 5.7 zero error build.
              </span>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
              <span className="font-bold text-slate-900 block">
                AI & Intelligence Layer
              </span>
              <span className="text-slate-500 mt-1 block">
                Deterministic tool-invoking assistant bounded by permissions.
              </span>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            CampusOS • College Operating System • Built for Institutional Scale
          </div>
          <div className="flex items-center space-x-6">
            <Link href="/app/dashboard" className="hover:text-slate-900">
              Dashboard
            </Link>
            <Link href="/login" className="hover:text-slate-900">
              Sign In
            </Link>
            <Link href="/app/security" className="hover:text-slate-900">
              Security & Audit
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
