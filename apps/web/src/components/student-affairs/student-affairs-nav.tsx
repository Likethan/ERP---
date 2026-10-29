"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  ShieldAlert,
  FileEdit,
  UserCheck,
  Inbox,
  Users,
  Gavel,
  FolderLock,
  Calendar,
  CheckSquare,
  Scale,
  MessageSquare,
  AlertTriangle,
  BookOpen,
  BarChart3,
  Settings,
} from "lucide-react";

interface TabItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const STUDENT_AFFAIRS_TABS: TabItem[] = [
  { label: "Overview Hub", href: "/app/student-affairs", icon: <ShieldAlert className="h-3.5 w-3.5" /> },
  { label: "Submit Grievance", href: "/app/student-affairs/submit", icon: <FileEdit className="h-3.5 w-3.5" /> },
  { label: "My Cases", href: "/app/student-affairs/my-cases", icon: <UserCheck className="h-3.5 w-3.5" /> },
  { label: "Intake Queue", href: "/app/student-affairs/intake", icon: <Inbox className="h-3.5 w-3.5" /> },
  { label: "Assignments", href: "/app/student-affairs/assignments", icon: <Users className="h-3.5 w-3.5" /> },
  { label: "Disciplinary", href: "/app/student-affairs/disciplinary", icon: <Gavel className="h-3.5 w-3.5" /> },
  { label: "Evidence", href: "/app/student-affairs/evidence", icon: <FolderLock className="h-3.5 w-3.5" /> },
  { label: "Meetings & Hearings", href: "/app/student-affairs/meetings", icon: <Calendar className="h-3.5 w-3.5" /> },
  { label: "Resolutions", href: "/app/student-affairs/resolutions", icon: <CheckSquare className="h-3.5 w-3.5" /> },
  { label: "Appeals", href: "/app/student-affairs/appeals", icon: <Scale className="h-3.5 w-3.5" /> },
  { label: "Communications", href: "/app/student-affairs/communications", icon: <MessageSquare className="h-3.5 w-3.5" /> },
  { label: "Escalations", href: "/app/student-affairs/escalations", icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  { label: "Policies & Law", href: "/app/student-affairs/policies", icon: <BookOpen className="h-3.5 w-3.5" /> },
  { label: "Analytics", href: "/app/student-affairs/reports", icon: <BarChart3 className="h-3.5 w-3.5" /> },
  { label: "Configuration", href: "/app/student-affairs/config", icon: <Settings className="h-3.5 w-3.5" /> },
];

export function StudentAffairsNav() {
  const pathname = usePathname();

  return (
    <div className="mb-6 border-b border-slate-800 pb-2">
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
        {STUDENT_AFFAIRS_TABS.map((tab) => {
          const isActive =
            tab.href === "/app/student-affairs"
              ? pathname === "/app/student-affairs"
              : pathname.startsWith(tab.href);

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                isActive
                  ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30"
                  : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
              )}
            >
              {tab.icon}
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
