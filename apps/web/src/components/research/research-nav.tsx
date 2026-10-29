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
  { label: "Dashboard", href: "/app/research", icon: <LayoutDashboard className="h-4 w-4" /> },
  { label: "Projects", href: "/app/research/projects", icon: <FolderKanban className="h-4 w-4" /> },
  { label: "Opportunities", href: "/app/research/opportunities", icon: <Sparkles className="h-4 w-4" /> },
  { label: "Proposals", href: "/app/research/proposals", icon: <FileEdit className="h-4 w-4" /> },
  { label: "Agreements & Awards", href: "/app/research/agreements", icon: <Award className="h-4 w-4" /> },
  { label: "Budgets & Ledger", href: "/app/research/budgets", icon: <DollarSign className="h-4 w-4" /> },
  { label: "Milestones", href: "/app/research/milestones", icon: <FileCheck2 className="h-4 w-4" /> },
  { label: "Ethics & Compliance", href: "/app/research/ethics", icon: <ShieldCheck className="h-4 w-4" /> },
  { label: "Outputs & IP", href: "/app/research/outputs", icon: <Lightbulb className="h-4 w-4" /> },
  { label: "Analytics", href: "/app/research/analytics", icon: <BarChart3 className="h-4 w-4" /> },
];

export function ResearchNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-20">
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <FlaskConical className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Research & Sponsored Programs
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Step 61 Enterprise
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            CampusOS — One Campus. One System. One Source of Truth.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/research/projects"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-sm"
          >
            <FolderKanban className="h-3.5 w-3.5" />
            View Portfolio
          </Link>
          <Link
            href="/app/research/opportunities"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            Grant Discovery
          </Link>
        </div>
      </div>

      <div className="px-6 flex items-center gap-1 overflow-x-auto no-scrollbar border-t border-slate-800/60 pt-1">
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
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
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
