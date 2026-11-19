"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ToastProvider } from "@/components/ui/toast";
import { RoleSwitcher } from "@/components/navigation/role-switcher";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  CalendarCheck,
  Calendar,
  Menu,
  X,
  Building,
  Shield,
  LogOut,
  ChevronRight,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface HodNavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const HOD_NAV_ITEMS: HodNavItem[] = [
  {
    label: "Dashboard",
    href: "/hod/dashboard",
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: "Faculty Management",
    href: "/hod/faculty",
    icon: <Users className="h-4 w-4" />,
    badge: "28 Faculty",
  },
  {
    label: "Student Management",
    href: "/hod/students",
    icon: <GraduationCap className="h-4 w-4" />,
    badge: "720 Enrolled",
  },
  {
    label: "Attendance Management",
    href: "/hod/attendance",
    icon: <CalendarCheck className="h-4 w-4" />,
  },
  {
    label: "Timetable Management",
    href: "/hod/timetable",
    icon: <Calendar className="h-4 w-4" />,
  },
];

export default function HodPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, activePersona, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const deptName = activePersona.department || "Computer Science & Engineering";

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200 text-slate-800">
      {/* Brand & Department Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200">
        <Link href="/hod/dashboard" className="flex items-center gap-2.5 min-w-0">
          <div className="relative h-10 w-10 shrink-0">
            <Image
              src="/college-logo.jpg"
              alt="V.S.B. Engineering College"
              fill
              className="object-contain rounded-md"
              priority
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-slate-900 truncate">
                CampusOS
              </span>
              <span className="rounded bg-yellow-100 px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase text-yellow-950 border border-yellow-300 shrink-0">
                HOD
              </span>
            </div>
            <div className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold truncate">
              V.S.B. Engineering College
            </div>
          </div>
        </Link>
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-slate-800 hover:bg-yellow-50"
            aria-label="Close mobile menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Department Context Badge */}
      <div className="p-3 bg-yellow-50/50 border-b border-yellow-200/60">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-yellow-400 flex items-center justify-center text-slate-950 shrink-0 font-bold text-xs shadow-xs border border-yellow-500">
            <Building className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-yellow-800">
              Department Portal
            </div>
            <div className="text-xs font-bold text-slate-900 truncate" title={deptName}>
              {deptName}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
        <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
          HOD Navigation
        </div>
        {HOD_NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/hod/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center justify-between rounded-lg px-3 py-2.5 text-xs font-medium transition-all group",
                isActive
                  ? "bg-yellow-400 text-slate-950 shadow-xs font-bold border border-yellow-500/50"
                  : "text-slate-600 hover:bg-yellow-50 hover:text-slate-950",
              )}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={cn(
                    "transition-colors",
                    isActive
                      ? "text-slate-950"
                      : "text-slate-400 group-hover:text-slate-800",
                  )}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[9px] font-mono",
                    isActive
                      ? "bg-yellow-500/40 text-slate-950 font-bold"
                      : "bg-slate-100 text-slate-600 border border-slate-200",
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <div className="pt-4 mt-4 border-t border-slate-100">
          <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Institutional Hub
          </div>
          <Link
            href="/app/dashboard"
            className="flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          >
            <span className="flex items-center gap-2">
              <ExternalLink className="h-3.5 w-3.5" />
              Full CampusOS Workspace
            </span>
            <ChevronRight className="h-3 w-3 text-slate-400" />
          </Link>
        </div>
      </nav>

      {/* HOD Profile Footer */}
      <div className="p-3 border-t border-slate-200 bg-yellow-50/40">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-yellow-400 text-slate-950 font-bold text-xs border border-yellow-500">
              {activePersona.avatarInitials || "KA"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-slate-900 truncate">
                {activePersona.name || "Dr. K. S. Anand"}
              </div>
              <div className="text-[10px] text-slate-500 truncate">
                Head of Department
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-yellow-50/25 antialiased font-sans text-slate-800">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-64 shrink-0 h-screen sticky top-0 overflow-hidden z-20">
          {sidebarContent}
        </aside>

        {/* Mobile Drawer */}
        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs animate-fade-in"
              onClick={() => setMobileOpen(false)}
            />
            <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl z-10 animate-slide-right">
              {sidebarContent}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Topbar */}
          <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-4 sm:px-6 backdrop-blur-md">
            {/* Left: Mobile Toggle & Scope Title */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="lg:hidden rounded-lg p-2 text-slate-600 hover:bg-yellow-50 hover:text-slate-900 transition-colors"
                aria-label="Toggle navigation"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="hidden sm:flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-semibold text-slate-600">
                  {deptName}
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-mono font-medium text-slate-500">
                  VSB-CAMPUS
                </span>
              </div>
            </div>

            {/* Right: Role Switcher & User Menu */}
            <div className="flex items-center gap-2.5 sm:gap-3">
              <RoleSwitcher />

              {/* User Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2 rounded-lg p-1 text-slate-700 hover:bg-yellow-50 transition-colors"
                  aria-label="User menu"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-yellow-400 text-slate-950 border border-yellow-500 text-xs font-bold font-mono shadow-xs">
                    {activePersona.avatarInitials || "KA"}
                  </div>
                </button>

                {userDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserDropdownOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-xl z-50 animate-scale-in">
                      <div className="px-3 py-2.5 border-b border-slate-100 mb-1">
                        <div className="text-xs font-semibold text-slate-900 truncate">
                          {activePersona.name}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono truncate mt-0.5">
                          {activePersona.email}
                        </div>
                        <div className="mt-2 inline-flex items-center gap-1 rounded bg-yellow-100 px-2 py-0.5 text-[10px] font-mono text-yellow-950 border border-yellow-300 font-semibold">
                          <Shield className="h-3 w-3 text-yellow-700" />
                          HOD • {deptName}
                        </div>
                      </div>

                      <div className="space-y-0.5 text-xs">
                        <Link
                          href="/app/dashboard"
                          className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-50 transition-colors"
                          onClick={() => setUserDropdownOpen(false)}
                        >
                          <ExternalLink className="h-4 w-4 text-slate-400" />
                          <span>Switch to Full ERP View</span>
                        </Link>
                        <button
                          onClick={() => {
                            setUserDropdownOpen(false);
                            logout();
                            router.push("/login");
                          }}
                          className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                        >
                          <LogOut className="h-4 w-4" />
                          <span>Sign Out</span>
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
            {children}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
