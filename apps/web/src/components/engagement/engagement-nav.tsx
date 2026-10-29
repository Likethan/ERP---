"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  BarChart3,
  BookOpenCheck,
  CalendarDays,
  Clock,
  Compass,
  FileCheck2,
  HandHeart,
  LayoutDashboard,
  Users2,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Civic Hub",
    href: "/app/engagement",
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: "Programs",
    href: "/app/engagement/programs",
    icon: <HandHeart className="h-4 w-4" />,
  },
  {
    label: "Partners",
    href: "/app/engagement/partners",
    icon: <Users2 className="h-4 w-4" />,
  },
  {
    label: "Opportunities",
    href: "/app/engagement/opportunities",
    icon: <Compass className="h-4 w-4" />,
  },
  {
    label: "Applications",
    href: "/app/engagement/applications",
    icon: <FileCheck2 className="h-4 w-4" />,
  },
  {
    label: "Shifts & Rosters",
    href: "/app/engagement/shifts",
    icon: <CalendarDays className="h-4 w-4" />,
  },
  {
    label: "Service Hours",
    href: "/app/engagement/service-hours",
    icon: <Clock className="h-4 w-4" />,
  },
  {
    label: "Reflections & SDGs",
    href: "/app/engagement/reflections",
    icon: <BookOpenCheck className="h-4 w-4" />,
  },
  {
    label: "Certificates",
    href: "/app/engagement/certificates",
    icon: <Award className="h-4 w-4" />,
  },
  {
    label: "Impact Analytics",
    href: "/app/engagement/analytics",
    icon: <BarChart3 className="h-4 w-4" />,
  },
];

export function EngagementNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-border bg-card/60 backdrop-blur-sm sticky top-0 z-20">
      <div className="flex items-center space-x-1 overflow-x-auto py-2 px-4 no-scrollbar">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/app/engagement"
              ? pathname === "/app/engagement"
              : pathname?.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

