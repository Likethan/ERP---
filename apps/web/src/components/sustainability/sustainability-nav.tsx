"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Leaf,
  Target,
  Zap,
  Droplets,
  Trash2,
  Activity,
  Sprout,
  ShieldCheck,
  Cpu,
  FileSpreadsheet,
  BarChart3,
  LucideIcon,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Executive Hub", href: "/app/sustainability", icon: Leaf },
  { name: "Targets & Baselines", href: "/app/sustainability/targets", icon: Target },
  { name: "Energy & Grid", href: "/app/sustainability/energy", icon: Zap, badge: "Live" },
  { name: "Water & Conservation", href: "/app/sustainability/water", icon: Droplets },
  { name: "Waste & Circularity", href: "/app/sustainability/waste", icon: Trash2 },
  { name: "Carbon Intelligence", href: "/app/sustainability/carbon", icon: Activity },
  { name: "Green Initiatives", href: "/app/sustainability/initiatives", icon: Sprout },
  { name: "Statutory Compliance", href: "/app/sustainability/compliance", icon: ShieldCheck },
  { name: "IoT Smart Meters", href: "/app/sustainability/iot-meters", icon: Cpu },
  { name: "Invoice Imports", href: "/app/sustainability/imports", icon: FileSpreadsheet },
  { name: "Decarb Analytics", href: "/app/sustainability/analytics", icon: BarChart3 },
];

export function SustainabilityNav({
  title,
  subtitle,
}: {
  title?: string;
  subtitle?: string;
}) {
  const pathname = usePathname();

  return (
    <div className="bg-slate-900 border-b border-slate-800 mb-6 rounded-lg overflow-hidden shadow-sm">
      {/* Brand & Header Section */}
      <div className="px-6 pt-6 pb-4 bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                <Leaf className="w-3 h-3" /> CampusOS Sustainability Platform
              </span>
              <span className="text-xs text-slate-400">
                “One Campus. One System. One Source of Truth.”
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-1">
              {title || "Campus Sustainability, Energy & Carbon Intelligence"}
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {subtitle ||
                "Verified institutional energy telemetry, GHG Protocol Scope 1-3 accounting, and SPCB environmental statutory compliance."}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              ESG Composite Score: 88.4 / 100
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 text-xs font-medium">
              Target Net-Zero: 2040
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="px-4 border-t border-slate-800/80 bg-slate-950/40 flex overflow-x-auto no-scrollbar">
        <nav className="flex space-x-1 py-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/app/sustainability"
                ? pathname === "/app/sustainability"
                : pathname?.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/70"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
                {item.badge && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 text-[10px] font-semibold rounded-full ${
                      isActive
                        ? "bg-emerald-800 text-emerald-100"
                        : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

