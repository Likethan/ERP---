"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  CheckCircle2,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Gavel,
  History,
  LayoutDashboard,
  RefreshCw,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavTab {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const NAV_TABS: NavTab[] = [
  { label: "Dashboard", href: "/app/legal", icon: <LayoutDashboard className="h-4 w-4" /> },
  { label: "Contracts Register", href: "/app/legal/contracts", icon: <FileText className="h-4 w-4" /> },
  { label: "Obligations & Commitments", href: "/app/legal/obligations", icon: <CheckCircle2 className="h-4 w-4" /> },
  { label: "Legal Matters (Restricted)", href: "/app/legal/matters", icon: <Gavel className="h-4 w-4" /> },
  { label: "Policy Governance", href: "/app/legal/policies", icon: <BookOpen className="h-4 w-4" /> },
  { label: "Compliance & Evidence", href: "/app/legal/compliance", icon: <ShieldCheck className="h-4 w-4" /> },
  { label: "Enterprise Risk Register", href: "/app/legal/risks", icon: <ShieldAlert className="h-4 w-4" /> },
  { label: "Deadlines & Calendar", href: "/app/legal/calendar", icon: <Calendar className="h-4 w-4" /> },
];

export function LegalNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-20">
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Scale className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
                Enterprise Legal Affairs & Contract Operations
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Step 62
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Institutional contract lifecycle, restricted matter management, policy approvals & 5x5 risk matrix
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs text-slate-600 dark:text-slate-300">
            <Shield className="h-3.5 w-3.5 text-emerald-500" />
            <span>Audited & Tenant-Isolated</span>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="px-6 flex items-center gap-1 overflow-x-auto scrollbar-none border-t border-slate-100 dark:border-slate-800/60 pt-1">
        {NAV_TABS.map((tab) => {
          const isActive =
            pathname === tab.href ||
            (tab.href !== "/app/legal" && pathname?.startsWith(tab.href));

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium rounded-t-lg transition-colors whitespace-nowrap border-b-2",
                isActive
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/30 font-semibold"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700"
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] rounded-full bg-rose-500 text-white font-bold">
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
