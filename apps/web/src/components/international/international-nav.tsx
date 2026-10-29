"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  BarChart3,
  BookOpen,
  Building2,
  Calendar,
  CheckSquare,
  Compass,
  DoorOpen,
  FileCheck2,
  FileEdit,
  FileText,
  Globe,
  LayoutDashboard,
  MapPin,
  Scale,
  Settings,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavTab {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const NAV_TABS: NavTab[] = [
  { label: "Dashboard", href: "/app/international", icon: <LayoutDashboard className="h-4 w-4" /> },
  { label: "Partners", href: "/app/international/partners", icon: <Building2 className="h-4 w-4" /> },
  { label: "MoUs & Agreements", href: "/app/international/agreements", icon: <FileText className="h-4 w-4" /> },
  { label: "Programs", href: "/app/international/programs", icon: <Compass className="h-4 w-4" /> },
  { label: "Applications", href: "/app/international/applications", icon: <FileEdit className="h-4 w-4" /> },
  { label: "Reviews", href: "/app/international/applications/review", icon: <ShieldCheck className="h-4 w-4" /> },
  { label: "Nominations", href: "/app/international/nominations", icon: <CheckSquare className="h-4 w-4" /> },
  { label: "Inbound Scholars", href: "/app/international/inbound", icon: <DoorOpen className="h-4 w-4" /> },
  { label: "Outbound Mobility", href: "/app/international/outbound", icon: <MapPin className="h-4 w-4" /> },
  { label: "Faculty Exchange", href: "/app/international/faculty-exchange", icon: <UserCheck className="h-4 w-4" /> },
  { label: "Credit Transfer", href: "/app/international/credit-transfer", icon: <Scale className="h-4 w-4" /> },
  { label: "Documents", href: "/app/international/documents", icon: <FileCheck2 className="h-4 w-4" /> },
  { label: "Scholarships", href: "/app/international/scholarships", icon: <Award className="h-4 w-4" /> },
  { label: "Calendar", href: "/app/international/calendar", icon: <Calendar className="h-4 w-4" /> },
  { label: "Analytics", href: "/app/international/analytics", icon: <BarChart3 className="h-4 w-4" /> },
  { label: "Policies & Config", href: "/app/international/config", icon: <Settings className="h-4 w-4" /> },
];

export function InternationalNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Globe className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                International Relations & Global Mobility
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-medium">
                  Step 60
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                CampusOS — One Campus. One System. One Source of Truth.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/international/programs"
            className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition-colors shadow-sm shadow-cyan-900/40 flex items-center gap-1.5"
          >
            <Compass className="h-3.5 w-3.5" />
            Explore Programs
          </Link>
          <Link
            href="/app/international/applications"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <FileEdit className="h-3.5 w-3.5" />
            Apply for Mobility
          </Link>
        </div>
      </div>

      {/* Horizontal Scrollable Tabs */}
      <div className="px-6 flex items-center gap-1 overflow-x-auto no-scrollbar pb-0">
        {NAV_TABS.map((tab) => {
          const isActive = pathname === tab.href || (tab.href !== "/app/international" && pathname?.startsWith(tab.href));
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-all",
                isActive
                  ? "border-cyan-500 text-cyan-400 bg-cyan-500/5 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              )}
            >
              {tab.icon}
              {tab.label}
              {tab.badge && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300">
                  {tab.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
