"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  BarChart3,
  BookOpen,
  DollarSign,
  FileCheck2,
  FileEdit,
  FileText,
  FlaskConical,
  FolderKanban,
  LayoutDashboard,
  Lightbulb,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
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
    href: "/app/research",
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: "Projects",
    href: "/app/research/projects",
    icon: <FolderKanban className="h-4 w-4" />,
  },
  {
    label: "Opportunities",
    href: "/app/research/opportunities",
    icon: <Sparkles className="h-4 w-4" />,
  },
  {
    label: "Proposals",
    href: "/app/research/proposals",
    icon: <FileEdit className="h-4 w-4" />,
  },
  {
    label: "Agreements & Awards",
    href: "/app/research/agreements",
    icon: <Award className="h-4 w-4" />,
  },
  {
    label: "Budgets & Ledger",
    href: "/app/research/budgets",
    icon: <DollarSign className="h-4 w-4" />,
  },
  {
    label: "Milestones",
    href: "/app/research/milestones",
    icon: <FileCheck2 className="h-4 w-4" />,
  },
  {
    label: "Ethics & Compliance",
    href: "/app/research/ethics",
    icon: <ShieldCheck className="h-4 w-4" />,
  },
  {
    label: "Outputs & IP",
    href: "/app/research/outputs",
    icon: <Lightbulb className="h-4 w-4" />,
  },
  {
    label: "Analytics",
    href: "/app/research/analytics",
    icon: <BarChart3 className="h-4 w-4" />,
  },
];

export function ResearchNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-20 shadow-2xs">
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-yellow-100 text-yellow-800 border border-yellow-300">
              <FlaskConical className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              Research & Sponsored Programs
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-900 border border-yellow-300 font-medium">
              Step 61 Enterprise
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            CampusOS — One Campus. One System. One Source of Truth.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/research/projects"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-yellow-400 hover:bg-yellow-500 text-slate-950 transition-colors shadow-xs"
          >
            <FolderKanban className="h-3.5 w-3.5" />
            View Portfolio
          </Link>
          <Link
            href="/app/research/opportunities"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            Grant Discovery
          </Link>
        </div>
      </div>

      <div className="px-6 flex items-center gap-1 overflow-x-auto no-scrollbar border-t border-slate-200 pt-1">
        {NAV_TABS.map((tab) => {
          const isActive =
            tab.href === "/app/research"
              ? pathname === "/app/research"
              : pathname.startsWith(tab.href);

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-t-lg transition-all border-b-2 whitespace-nowrap",
                isActive
                  ? "border-yellow-500 text-slate-950 bg-yellow-50 font-bold"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-yellow-50/40",
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
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
