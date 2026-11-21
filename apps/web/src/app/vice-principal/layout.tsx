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
  Building2,
  Calendar,
  Users,
  GraduationCap,
  ShieldCheck,
  ClipboardCheck,
  FileSpreadsheet,
  Bell,
  ShieldAlert,
  Menu,
  X,
  Shield,
  LogOut,
  ChevronRight,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface VicePrincipalNavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  badgeVariant?: "default" | "alert" | "warning";
}

const VP_NAV_ITEMS: VicePrincipalNavItem[] = [
  {
    label: "Executive Dashboard",
    href: "/vice-principal/dashboard",
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: "Department Monitoring",
    href: "/vice-principal/departments",
    icon: <Building2 className="h-4 w-4" />,
    badge: "5 Depts",
  },
  {
    label: "Academic Monitoring",
    href: "/vice-principal/academics",
    icon: <Calendar className="h-4 w-4" />,
    badge: "Milestones",
  },
  {
    label: "Faculty Supervision",
    href: "/vice-principal/faculty",
    icon: <Users className="h-4 w-4" />,
    badge: "Workload",
  },
  {
    label: "Student Monitoring",
    href: "/vice-principal/students",
    icon: <GraduationCap className="h-4 w-4" />,
    badge: "<75% Radar",
    badgeVariant: "alert",
  },
  {
    label: "Approval Center",
    href: "/vice-principal/approvals",
    icon: <ShieldCheck className="h-4 w-4" />,
    badge: "4 Pending",
    badgeVariant: "warning",
  },
  {
    label: "Examinations & CIA",
    href: "/vice-principal/examinations",
    icon: <ClipboardCheck className="h-4 w-4" />,
  },
  {
    label: "Reports & Analytics",
    href: "/vice-principal/reports",
    icon: <FileSpreadsheet className="h-4 w-4" />,
  },
  {
    label: "Institutional Circulars",
    href: "/vice-principal/announcements",
    icon: <Bell className="h-4 w-4" />,
  },
  {
    label: "Audit Trail",
    href: "/vice-principal/audit",
    icon: <ShieldAlert className="h-4 w-4" />,
    badge: "Read-Only",
  },
];

export default function VicePrincipalPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, activePersona, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  // Authentication & Role Gate
  React.useEffect(() => {
    if (!user) {
      router.push("/login?role=vice_principal");
      return;
    }
    const role = user.role?.toUpperCase();
    const allowed = ["PRINCIPAL", "VICE_PRINCIPAL", "SUPER_ADMIN", "ADMIN"];
    if (!allowed.includes(role || "")) {
      router.push("/app/dashboard");
    }
  }, [user, router]);

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200 text-slate-800">
      {/* Brand & Executive Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200">
        <Link
          href="/vice-principal/dashboard"
          className="flex items-center gap-2.5 min-w-0"
        >
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
              <span className="rounded bg-indigo-100 px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase text-indigo-900 border border-indigo-300 shrink-0">
                VICE PRINCIPAL
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
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100"
            aria-label="Close mobile menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Role Context Card */}
      <div className="p-3 bg-indigo-50/60 border-b border-indigo-200/70">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 font-bold text-xs shadow-xs">
            <Shield className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-900">
              Executive Office
            </div>
            <div
              className="text-xs font-bold text-slate-900 truncate"
              title="Academic Supervision & Statutory Approvals"
            >
              Academic & Institutional Operations
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
          Executive Modules
        </div>
        {VP_NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/vice-principal/dashboard" &&
              pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-all group",
                isActive
                  ? "bg-indigo-600 text-white shadow-xs font-bold border border-indigo-700"
                  : "text-slate-600 hover:bg-indigo-50 hover:text-indigo-950",
              )}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={cn(
                    "transition-colors",
                    isActive
                      ? "text-white"
                      : "text-slate-400 group-hover:text-indigo-600",
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
                      ? "bg-white/20 text-white font-bold"
                      : item.badgeVariant === "alert"
                        ? "bg-rose-100 text-rose-700 font-bold border border-rose-200"
                        : item.badgeVariant === "warning"
                          ? "bg-amber-100 text-amber-800 font-bold border border-amber-200"
                          : "bg-slate-100 text-slate-600 border border-slate-200",
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <div className="pt-4 mt-4 border-t border-slate-200">
          <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Institutional Gateway
          </div>
          <Link
            href="/app/dashboard"
            className="flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <ExternalLink className="h-4 w-4 text-slate-400" />
              <span>Institutional Overview</span>
            </div>
            <ChevronRight className="h-3 w-3 text-slate-400" />
          </Link>
        </div>
      </nav>

      {/* User Footer with Switcher */}
      <div className="p-3 border-t border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-8 w-8 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
              {(user?.first_name
                ? `${user.first_name[0]}${user.last_name ? user.last_name[0] : ""}`
                : activePersona?.avatarInitials) || "VP"}
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-slate-900 truncate">
                {user?.first_name
                  ? `${user.first_name} ${user.last_name || ""}`.trim()
                  : activePersona?.name || "Vice Principal"}
              </div>
              <div className="text-[10px] text-slate-500 truncate">
                {activePersona?.roleTitle ||
                  user?.roles?.[0]?.display_name ||
                  "Vice Principal"}
              </div>
            </div>
          </div>
          <button
            onClick={() => logout()}
            title="Sign Out"
            className="rounded p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <ToastProvider>
      <div className="flex h-screen overflow-hidden bg-slate-50">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:flex w-64 shrink-0 flex-col shadow-xs z-30">
          {sidebarContent}
        </aside>

        {/* Mobile Sidebar Backdrop */}
        {mobileOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-xs lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Mobile Drawer */}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 w-72 bg-white transition-transform duration-300 ease-in-out lg:hidden",
            mobileOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          {sidebarContent}
        </aside>

        {/* Main Content Area */}
        <div className="flex flex-1 flex-col overflow-hidden min-w-0">
          {/* Executive Top Bar */}
          <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="lg:hidden rounded-lg p-2 text-slate-600 hover:bg-slate-100"
                aria-label="Open mobile menu"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="hidden sm:flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                  CampusOS Executive
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-xs text-slate-600 font-medium">
                  Academic Governance & Statutory Supervision
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full font-semibold">
                <Sparkles className="h-3 w-3" />
                <span>Statutory Authority Active</span>
              </div>

              {/* Role Switcher */}
              <RoleSwitcher />
            </div>
          </header>

          {/* Page Content Body */}
          <main className="flex-1 overflow-y-auto bg-slate-50 p-4 lg:p-8">
            <div className="mx-auto max-w-7xl">{children}</div>
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
