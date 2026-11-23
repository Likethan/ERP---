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
  {
    label: "Dashboard",
    href: "/app/international",
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: "Partners",
    href: "/app/international/partners",
    icon: <Building2 className="h-4 w-4" />,
  },
  {
    label: "MoUs & Agreements",
    href: "/app/international/agreements",
    icon: <FileText className="h-4 w-4" />,
  },
  {
    label: "Programs",
    href: "/app/international/programs",
    icon: <Compass className="h-4 w-4" />,
  },
  {
    label: "Applications",
    href: "/app/international/applications",
    icon: <FileEdit className="h-4 w-4" />,
  },
  {
    label: "Reviews",
    href: "/app/international/applications/review",
    icon: <ShieldCheck className="h-4 w-4" />,
  },
  {
    label: "Nominations",
    href: "/app/international/nominations",
    icon: <CheckSquare className="h-4 w-4" />,
  },
  {
    label: "Inbound Scholars",
    href: "/app/international/inbound",
    icon: <DoorOpen className="h-4 w-4" />,
  },
  {
    label: "Outbound Mobility",
    href: "/app/international/outbound",
    icon: <MapPin className="h-4 w-4" />,
  },
  {
    label: "Faculty Exchange",
    href: "/app/international/faculty-exchange",
    icon: <UserCheck className="h-4 w-4" />,
  },
  {
    label: "Credit Transfer",
    href: "/app/international/credit-transfer",
    icon: <Scale className="h-4 w-4" />,
  },
  {
    label: "Documents",
    href: "/app/international/documents",
    icon: <FileCheck2 className="h-4 w-4" />,
  },
  {
    label: "Scholarships",
    href: "/app/international/scholarships",
    icon: <Award className="h-4 w-4" />,
  },
  {
    label: "Calendar",
    href: "/app/international/calendar",
    icon: <Calendar className="h-4 w-4" />,
  },
  {
    label: "Analytics",
    href: "/app/international/analytics",
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    label: "Policies & Config",
    href: "/app/international/config",
    icon: <Settings className="h-4 w-4" />,
  },
];

export function InternationalNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-20 shadow-2xs">
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-yellow-100 text-yellow-800 border border-yellow-300">
              <Globe className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
                International Relations & Global Mobility
                <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-900 border border-yellow-300 font-medium">
                  Step 60
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                CampusOS — One Campus. One System. One Source of Truth.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/international/programs"
            className="px-3 py-1.5 rounded-lg bg-yellow-400 hover:bg-yellow-500 text-slate-950 text-xs font-semibold transition-colors shadow-xs flex items-center gap-1.5"
          >
            <Compass className="h-3.5 w-3.5" />
            Explore Programs
          </Link>
          <Link
            href="/app/international/applications"
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium border border-slate-200 transition-colors flex items-center gap-1.5"
          >
            <FileEdit className="h-3.5 w-3.5" />
            Apply for Mobility
          </Link>
        </div>
      </div>

      {/* Horizontal Scrollable Tabs */}
      <div className="px-6 flex items-center gap-1 overflow-x-auto no-scrollbar border-t border-slate-200 pt-1 pb-0">
        {NAV_TABS.map((tab) => {
          const isActive =
            pathname === tab.href ||
            (tab.href !== "/app/international" &&
              pathname?.startsWith(tab.href));
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-all",
                isActive
                  ? "border-yellow-500 text-slate-950 bg-yellow-50 font-bold"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-yellow-50/40",
              )}
            >
              {tab.icon}
              {tab.label}
              {tab.badge && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-slate-100 text-slate-600 border border-slate-200">
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
