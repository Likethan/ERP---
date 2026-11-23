"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ToastProvider } from "@/components/ui/toast";
import { RoleSwitcher } from "@/components/navigation/role-switcher";
import {
  Menu,
  X,
  Search,
  LogOut,
  ChevronDown,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface HodNavItem {
  label: string;
  href: string;
  badge?: string;
}

interface HodNavSection {
  title: string;
  items: HodNavItem[];
}

const HOD_NAV_SECTIONS: HodNavSection[] = [
  {
    title: "OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/hod/dashboard",
      },
    ],
  },
  {
    title: "MY ACADEMICS",
    items: [
      {
        label: "Faculty Directory",
        href: "/hod/faculty",
        badge: "28",
      },
      {
        label: "Student Directory",
        href: "/hod/students",
        badge: "720",
      },
      {
        label: "Class Timetable",
        href: "/hod/timetable",
      },
      {
        label: "Curriculum & Syllabi",
        href: "/hod/curriculum",
        badge: "R-2026",
      },
      {
        label: "Lesson Plan Tracker",
        href: "/hod/lesson-plans",
        badge: "82.8%",
      },
    ],
  },
  {
    title: "MY ATTENDANCE",
    items: [
      {
        label: "Attendance Records",
        href: "/hod/attendance",
        badge: "88.5%",
      },
    ],
  },
  {
    title: "MY EXAMINATIONS",
    items: [
      {
        label: "Exam Schedules",
        href: "/hod/examinations",
      },
      {
        label: "Internal Marks Audit",
        href: "/hod/internal-marks",
      },
      {
        label: "Results & GPA Card",
        href: "/hod/results",
        badge: "90.8%",
      },
    ],
  },
  {
    title: "OPERATIONS & APPROVALS",
    items: [
      {
        label: "Leave & Approvals",
        href: "/hod/approvals",
        badge: "5",
      },
      {
        label: "Department Events",
        href: "/hod/events",
        badge: "5 Active",
      },
      {
        label: "Placement Telemetry",
        href: "/hod/placements",
        badge: "87.8%",
      },
      {
        label: "Faculty Achievements",
        href: "/hod/achievements",
        badge: "6 Awards",
      },
    ],
  },
  {
    title: "REPORTS & QUALITY",
    items: [
      {
        label: "Reports Engine",
        href: "/hod/reports",
      },
      {
        label: "Live KPIs & Telemetry",
        href: "/hod/analytics",
      },
      {
        label: "Accreditation & NBA",
        href: "/hod/accreditation",
        badge: "93.0%",
      },
    ],
  },
];

export default function HodPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, activePersona, logout, isLoading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Authentication & Role Gate
  React.useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.replace("/login?role=hod");
      return;
    }
    const role = (
      user.roles?.[0]?.name ||
      (user as any).role ||
      ""
    ).toUpperCase();
    const allowed = ["HOD", "SUPER_ADMIN", "ADMIN"];
    if (!allowed.includes(role)) {
      router.replace("/app/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F6F9]">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-[#183153]" />
          <span className="text-sm font-medium">
            Resolving CampusOS HOD Workspace...
          </span>
        </div>
      </div>
    );
  }

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

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-[#DCE3EB] text-[#172338]">
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-[#DCE3EB]">
        <Link
          href="/hod/dashboard"
          className="flex items-center gap-2.5 min-w-0"
        >
          <div className="h-8 w-8 rounded bg-[#183153] flex items-center justify-center text-white font-black text-xs tracking-wider shrink-0 shadow-xs">
            VSB
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 leading-none">
              <span className="text-[13px] font-extrabold tracking-tight text-[#172338]">
                CAMPUSOS
              </span>
              <span className="text-[10px] font-mono text-[#64748B]">v2.4</span>
            </div>
            <div className="text-[10px] text-[#64748B] font-medium tracking-wide truncate mt-0.5">
              V.S.B. Eng. College
            </div>
          </div>
        </Link>
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden rounded p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100"
            aria-label="Close mobile menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4">
        {HOD_NAV_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-0.5">
            <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-[#94A3B8] mb-1">
              {section.title}
            </div>
            {section.items.map((item) => {
              const isActive =
                item.href === "/hod/dashboard"
                  ? pathname === "/hod/dashboard" || pathname === "/hod"
                  : pathname === item.href ||
                    pathname?.startsWith(item.href + "/");

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center justify-between px-2.5 py-1.5 rounded text-[12px] transition-colors font-medium",
                    isActive
                      ? "bg-[#183153] text-white shadow-xs font-semibold"
                      : "text-[#64748B] hover:text-[#172338] hover:bg-[#F1F5F9]",
                  )}
                >
                  <div className="flex items-center min-w-0 gap-1.5">
                    <span
                      className={cn(
                        "text-[14px] leading-none shrink-0",
                        isActive ? "text-[#C99A2E]" : "text-[#94A3B8]",
                      )}
                    >
                      •
                    </span>
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={cn(
                        "text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold shrink-0 ml-1.5",
                        isActive
                          ? "bg-[#1E3A5F] text-[#F8F1DF] border border-[#2D5382]"
                          : "bg-slate-100 text-[#64748B] border border-slate-200",
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Profile / Switcher */}
      <div className="p-3 border-t border-[#DCE3EB] bg-[#F8FAFC]">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-7 w-7 rounded bg-[#183153] text-white flex items-center justify-center font-bold text-[11px] shrink-0">
              {userInitials}
            </div>
            <div className="min-w-0">
              <div className="text-[11px] font-bold text-[#172338] truncate">
                {userName}
              </div>
              <div className="text-[10px] text-[#64748B] truncate">
                {activePersona.role} • {activePersona.department ? "HOD" : ""}
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            title="Log Out"
            className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-slate-100 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <ToastProvider>
      <div className="min-h-screen bg-[#F4F6F9] text-[#172338] font-sans">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:flex lg:w-56 lg:flex-col shadow-xs">
          {sidebarContent}
        </aside>

        {/* Mobile Sidebar Overlay */}
        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
              onClick={() => setMobileOpen(false)}
            />
            <div className="fixed inset-y-0 left-0 w-64 shadow-xl">
              {sidebarContent}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="lg:pl-56 flex flex-col min-h-screen">
          {/* Top Bar matching reference */}
          <header className="sticky top-0 z-30 h-12 bg-white border-b border-[#DCE3EB] px-4 flex items-center justify-between gap-3 shadow-2xs">
            {/* Left: Mobile trigger & Global Search */}
            <div className="flex items-center gap-3 flex-1 max-w-xl">
              <button
                onClick={() => setMobileOpen(true)}
                className="lg:hidden p-1.5 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100"
                aria-label="Open mobile menu"
              >
                <Menu className="h-5 w-5" />
              </button>

              <div className="relative w-full max-w-md hidden sm:block">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search courses, exams, dues services..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-8 pl-8 pr-14 text-xs bg-white border border-[#DCE3EB] rounded placeholder:text-slate-400 text-[#172338] focus:outline-none focus:border-[#1E3A5F] focus:ring-1 focus:ring-[#1E3A5F] transition-all"
                />
                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-mono text-slate-400 border border-slate-200 rounded px-1.5 py-0.5 bg-slate-50">
                  CTRL+K
                </span>
              </div>
            </div>

            {/* Right: Theme label, Term Pill, User details */}
            <div className="flex items-center gap-3 shrink-0">
              {/* Theme identifier from reference */}
              <div className="hidden xl:flex items-center text-[11px] font-semibold text-[#C99A2E]">
                Theme 01: Oxford Navy & Warm Gold
              </div>

              {/* Term badge */}
              <div className="hidden md:inline-flex items-center text-[11px] font-medium text-[#172338] bg-slate-50 border border-[#DCE3EB] px-2.5 py-0.5 rounded-full">
                Fall 2026 • Sem 5
              </div>

              {/* Role Switcher */}
              <div className="hidden sm:block">
                <RoleSwitcher />
              </div>

              {/* User Identity & Avatar */}
              <div className="flex items-center gap-2 pl-2 border-l border-[#DCE3EB]">
                <div className="hidden sm:block text-right">
                  <div className="text-[11px] font-bold text-[#172338] leading-tight">
                    {userName}
                  </div>
                  <div className="text-[9px] font-mono text-[#64748B] leading-tight">
                    2026-CSE-HOD • B.Tech CSE (HOD)
                  </div>
                </div>
                <div
                  className="h-7 w-7 rounded bg-[#183153] text-white flex items-center justify-center font-bold text-[11px] tracking-wider shrink-0 cursor-pointer shadow-2xs"
                  title={`${userName} (${activePersona.role})`}
                >
                  {userInitials}
                </div>
              </div>
            </div>
          </header>

          {/* Page Body */}
          <main className="flex-1 p-3 sm:p-4 max-w-[1700px] w-full mx-auto">
            {children}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
