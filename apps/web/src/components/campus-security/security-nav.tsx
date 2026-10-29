"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  DoorOpen,
  Flame,
  Footprints,
  KeyRound,
  Layers,
  Shield,
  ShieldAlert,
  UserCheck,
  Users,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/app/campus-security", label: "Security Hub", icon: Shield, exact: true },
  { href: "/app/campus-security/visitors", label: "Visitor Directory", icon: Users },
  { href: "/app/campus-security/gate-operations", label: "Gate Operations", icon: DoorOpen },
  { href: "/app/campus-security/contractors", label: "Contractor Access", icon: UserCheck },
  { href: "/app/campus-security/zones", label: "Security Zones", icon: Layers },
  { href: "/app/campus-security/access-grants", label: "Access Grants", icon: KeyRound },
  { href: "/app/campus-security/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/app/campus-security/emergency", label: "Emergency Response", icon: Flame },
  { href: "/app/campus-security/patrols", label: "Patrol Rounds", icon: Footprints },
];

export function SecurityNav() {
  const pathname = usePathname();

  return (
    <div className="border-b border-border bg-card/60 backdrop-blur-md sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="h-6 w-6 text-primary animate-pulse" />
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Campus Security & Access Intelligence
            </span>
          </div>
          <div className="flex items-center space-x-1 overflow-x-auto py-1 scrollbar-none">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 whitespace-nowrap ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/80"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

