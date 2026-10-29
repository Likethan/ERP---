"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  UserCheck,
  Users,
  Calendar,
  Lock,
  MessagesSquare,
  Target,
  CheckSquare,
  ArrowRightLeft,
  GraduationCap,
  Clock,
  BarChart3,
  Settings,
  Heart,
  Sparkles,
} from "lucide-react";

interface TabItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const SUPPORT_TABS: TabItem[] = [
  { label: "Support Hub", href: "/app/student-support", icon: <LayoutDashboard className="h-3.5 w-3.5" /> },
  { label: "My Mentor", href: "/app/student-support/mentor", icon: <UserCheck className="h-3.5 w-3.5" /> },
  { label: "Assignments", href: "/app/student-support/assignments", icon: <Users className="h-3.5 w-3.5" /> },
  { label: "Mentee Directory", href: "/app/student-support/mentees", icon: <GraduationCap className="h-3.5 w-3.5" /> },
  { label: "Book Counselling", href: "/app/student-support/counselling", icon: <Heart className="h-3.5 w-3.5" /> },
  { label: "Counselling Schedule", href: "/app/student-support/counselling/schedule", icon: <Calendar className="h-3.5 w-3.5" /> },
  { label: "Restricted Workspace", href: "/app/student-support/counselling/workspace", icon: <Lock className="h-3.5 w-3.5" />, badge: "Confidential" },
  { label: "Mentoring Sessions", href: "/app/student-support/sessions", icon: <MessagesSquare className="h-3.5 w-3.5" /> },
  { label: "Development Plans", href: "/app/student-support/development-plans", icon: <Sparkles className="h-3.5 w-3.5" /> },
  { label: "Goals & Actions", href: "/app/student-support/goals", icon: <Target className="h-3.5 w-3.5" /> },
  { label: "Support Referrals", href: "/app/student-support/referrals", icon: <ArrowRightLeft className="h-3.5 w-3.5" /> },
  { label: "Guidance Timeline", href: "/app/student-support/guidance", icon: <GraduationCap className="h-3.5 w-3.5" /> },
  { label: "Follow-Ups", href: "/app/student-support/follow-ups", icon: <Clock className="h-3.5 w-3.5" /> },
  { label: "Analytics", href: "/app/student-support/analytics", icon: <BarChart3 className="h-3.5 w-3.5" /> },
  { label: "Configuration", href: "/app/student-support/config", icon: <Settings className="h-3.5 w-3.5" /> },
];

export function StudentSupportNav() {
  const pathname = usePathname();

  return (
    <div className="mb-6 border-b border-slate-800 pb-2">
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
        {SUPPORT_TABS.map((tab) => {
          const isActive =
            tab.href === "/app/student-support"
              ? pathname === "/app/student-support"
              : pathname.startsWith(tab.href);

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                isActive
                  ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm"
                  : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-1 rounded bg-amber-500/20 px-1 py-0.2 text-[10px] font-semibold text-amber-400 border border-amber-500/30">
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
