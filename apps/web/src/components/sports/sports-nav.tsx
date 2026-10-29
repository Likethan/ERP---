"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Trophy,
  Building2,
  DoorOpen,
  Calendar,
  Users,
  ShieldCheck,
  UserCheck,
  Dumbbell,
  CalendarDays,
  Timer,
  CheckSquare,
  Medal,
  Wrench,
  CreditCard,
  BarChart3,
  BookOpen,
} from "lucide-react";

interface TabItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const SPORTS_TABS: TabItem[] = [
  { label: "Dashboard", href: "/app/sports", icon: <Trophy className="h-3.5 w-3.5" /> },
  { label: "Departments", href: "/app/sports/departments", icon: <Building2 className="h-3.5 w-3.5" /> },
  { label: "Facilities & Courts", href: "/app/sports/facilities", icon: <DoorOpen className="h-3.5 w-3.5" /> },
  { label: "Availability Calendar", href: "/app/sports/calendar", icon: <Calendar className="h-3.5 w-3.5" /> },
  { label: "Participant Directory", href: "/app/sports/participants", icon: <Users className="h-3.5 w-3.5" /> },
  { label: "Teams & Rosters", href: "/app/sports/teams", icon: <ShieldCheck className="h-3.5 w-3.5" /> },
  { label: "Coaches & Officials", href: "/app/sports/coaches", icon: <UserCheck className="h-3.5 w-3.5" /> },
  { label: "Training Programs", href: "/app/sports/training", icon: <Dumbbell className="h-3.5 w-3.5" /> },
  { label: "Training Schedule", href: "/app/sports/training/schedule", icon: <CalendarDays className="h-3.5 w-3.5" /> },
  { label: "Tournaments", href: "/app/sports/competitions", icon: <Trophy className="h-3.5 w-3.5" /> },
  { label: "Fixtures & Matches", href: "/app/sports/fixtures", icon: <Timer className="h-3.5 w-3.5" /> },
  { label: "Results & Standings", href: "/app/sports/results", icon: <CheckSquare className="h-3.5 w-3.5" /> },
  { label: "Achievements", href: "/app/sports/achievements", icon: <Medal className="h-3.5 w-3.5" /> },
  { label: "Equipment Allocation", href: "/app/sports/equipment", icon: <Wrench className="h-3.5 w-3.5" /> },
  { label: "Registrations & Fees", href: "/app/sports/fees", icon: <CreditCard className="h-3.5 w-3.5" /> },
  { label: "Reports & Analytics", href: "/app/sports/reports", icon: <BarChart3 className="h-3.5 w-3.5" /> },
  { label: "Configuration & Policies", href: "/app/sports/config", icon: <BookOpen className="h-3.5 w-3.5" /> },
];

export function SportsNav() {
  const pathname = usePathname();

  return (
    <div className="mb-6 border-b border-slate-800 pb-2">
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
        {SPORTS_TABS.map((tab) => {
          const isActive =
            tab.href === "/app/sports"
              ? pathname === "/app/sports"
              : pathname === tab.href || pathname.startsWith(tab.href + "/");

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-all shrink-0",
                isActive
                  ? "bg-indigo-600/90 text-white font-semibold shadow-sm shadow-indigo-600/30"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent hover:border-slate-800",
              )}
            >
              <span className={cn(isActive ? "text-white" : "text-slate-500")}>
                {tab.icon}
              </span>
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
