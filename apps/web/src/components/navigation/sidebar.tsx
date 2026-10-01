"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  UserCheck,
  BookOpen,
  CalendarDays,
  Calendar,
  CheckSquare,
  FileSpreadsheet,
  FileCheck2,
  DollarSign,
  Receipt,
  Briefcase,
  Building2,
  PartyPopper,
  Sparkles,
  BedDouble,
  Bus,
  FileText,
  ShieldCheck,
  Building,
  Layers,
  ChevronDown,
  X,
  CreditCard,
  Gift,
  RotateCcw,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavLinkItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  roles?: string[];
}

interface NavSection {
  title: string;
  items: NavLinkItem[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const { user, activePersona } = useAuth();

  const NAV_SECTIONS: NavSection[] = [
    {
      title: "OVERVIEW",
      items: [
        {
          label: "Dashboard",
          href: "/app/dashboard",
          icon: <LayoutDashboard className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "PEOPLE",
      items: [
        {
          label: "Students",
          href: "/app/students",
          icon: <GraduationCap className="h-4 w-4" />,
        },
        {
          label: "Faculty",
          href: "/app/faculty",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Staff",
          href: "/app/staff",
          icon: <Users className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "ACADEMICS",
      items: [
        {
          label: "Programs",
          href: "/app/programs",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Academic Structure",
          href: "/app/academic-structure",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Subjects",
          href: "/app/academics/subjects",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Curricula",
          href: "/app/academics/curricula",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Course Offerings",
          href: "/app/academics/course-offerings",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Timetable",
          href: "/app/academics/timetable",
          icon: <Calendar className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "ATTENDANCE",
      items: [
        {
          label: "Attendance Overview",
          href: "/app/attendance",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Sessions",
          href: "/app/attendance/sessions",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Leave Requests",
          href: "/app/attendance/leaves",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Corrections",
          href: "/app/attendance/corrections",
          icon: <RotateCcw className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "EXAMINATIONS",
      items: [
        {
          label: "Assessments",
          href: "/app/examinations/assessments",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Exam Schedules",
          href: "/app/examinations/schedules",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Marks Entry",
          href: "/app/examinations/marks",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Results & GPA",
          href: "/app/examinations/results",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "FINANCE",
      items: [
        {
          label: "Finance Dashboard",
          href: "/app/finance",
          icon: <DollarSign className="h-4 w-4" />,
        },
        {
          label: "Fee Structures",
          href: "/app/finance/fee-structures",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Invoices",
          href: "/app/finance/invoices",
          icon: <CreditCard className="h-4 w-4" />,
        },
        {
          label: "Payments",
          href: "/app/finance/payments",
          icon: <DollarSign className="h-4 w-4" />,
        },
        {
          label: "Receipts",
          href: "/app/finance/receipts",
          icon: <Receipt className="h-4 w-4" />,
        },
        {
          label: "Scholarships",
          href: "/app/finance/scholarships",
          icon: <Gift className="h-4 w-4" />,
        },
        {
          label: "Refunds",
          href: "/app/finance/refunds",
          icon: <RotateCcw className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "CAREER & PLACEMENT",
      items: [
        {
          label: "Placement Hub",
          href: "/app/placement",
          icon: <Briefcase className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "CAMPUS ENGAGEMENT",
      items: [
        {
          label: "Events",
          href: "/app/events",
          icon: <PartyPopper className="h-4 w-4" />,
        },
        {
          label: "Clubs & Orgs",
          href: "/app/clubs",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Announcements",
          href: "/app/announcements",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Notifications",
          href: "/app/notifications",
          icon: <Calendar className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "INFRASTRUCTURE",
      items: [
        {
          label: "Residential Hostel",
          href: "/app/hostel",
          icon: <BedDouble className="h-4 w-4" />,
        },
        {
          label: "Campus Transport",
          href: "/app/transport",
          icon: <Bus className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "DOCUMENTS",
      items: [
        {
          label: "Document Vault",
          href: "/app/documents",
          icon: <FileText className="h-4 w-4" />,
        },
      ],
    },
    {
      title: "INTELLIGENCE",
      items: [
        {
          label: "Campus Intelligence",
          href: "/app/intelligence",
          icon: <Sparkles className="h-4 w-4 text-yellow-400" />,
        },
        {
          label: "AI Assistant",
          href: "/app/ai",
          icon: <Bot className="h-4 w-4 text-indigo-400" />,
        },
      ],
    },
    {
      title: "SYSTEM GOVERNANCE",
      items: [
        {
          label: "Institution",
          href: "/app/institution",
          icon: <Building className="h-4 w-4" />,
        },
        {
          label: "Campuses",
          href: "/app/campuses",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Departments",
          href: "/app/departments",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Security & IAM",
          href: "/app/security",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
      ],
    },
  ];

  const sidebarContent = (
    <div className="flex h-full flex-col bg-slate-950 border-r border-slate-800 text-slate-200">
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800">
        <Link href="/app/dashboard" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white font-black text-sm shadow-md shadow-indigo-600/30">
            C
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-white">
                CampusOS
              </span>
              <span className="rounded bg-indigo-500/20 px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase text-indigo-300 border border-indigo-500/30">
                ERP
              </span>
            </div>
            <div className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">
              Operating System
            </div>
          </div>
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
              {section.title}
            </div>
            {section.items.map((item) => {
              const isActive =
                item.href === "/app/dashboard"
                  ? pathname === "/app/dashboard"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-indigo-600 text-white shadow-sm font-semibold"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={cn(
                        "transition-colors",
                        isActive
                          ? "text-white"
                          : "text-slate-500 group-hover:text-slate-300"
                      )}
                    >
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[9px] font-mono text-slate-400">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Tenant Context Footer */}
      <div className="p-3.5 border-t border-slate-800 bg-slate-950/80">
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>Tenant Scope</span>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </div>
          <div className="text-xs font-semibold text-white truncate">
            {user?.tenant?.name || "Vidyasagar State University"}
          </div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
            CODE: {user?.tenant?.code || "VSB-CAMPUS"}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 h-screen sticky top-0 overflow-hidden z-20">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in"
            onClick={onCloseMobile}
          />
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl animate-slide-right z-10">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
