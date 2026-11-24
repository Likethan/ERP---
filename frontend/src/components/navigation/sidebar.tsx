"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getPortalNavSections,
  getPortalHeaderMeta,
  NAV_SECTIONS,
  isPathAuthorized,
  type NavLinkItem,
  type NavSection,
} from "./nav-config";

export {
  NAV_SECTIONS,
  isPathAuthorized,
  getPortalNavSections,
  getPortalHeaderMeta,
};
export type { NavLinkItem, NavSection };

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}


export function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const portalSections = getPortalNavSections(user);
  const portalMeta = getPortalHeaderMeta(user);

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200 text-slate-800">
      {/* Brand Header with Role-Specific Portal Identity */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200">
        <Link href="/app/dashboard" className="flex items-center gap-3 min-w-0">
          <div className="relative h-10 w-10 shrink-0">
            <Image
              src="/college-logo.jpg"
              alt="V.S.B. Engineering College"
              fill
              className="object-contain rounded-md"
              priority
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-slate-900 truncate">
                CampusOS
              </span>
              <span
                suppressHydrationWarning
                className={cn(
                  "rounded px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase border shrink-0",
                  portalMeta.badgeClass,
                )}
              >
                {portalMeta.badge}
              </span>
            </div>
            <div
              suppressHydrationWarning
              className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold truncate"
            >
              {portalMeta.title}
            </div>
          </div>
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-slate-800 hover:bg-yellow-50"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Role-Specific Portal Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {portalSections.map((section, sIdx) => {
          if (!section.items || section.items.length === 0) return null;

          return (
            <div key={section.title || sIdx} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                {section.title}
              </div>
              {section.items.map((item, itemIdx) => {
                const isActive =
                  item.href === "/app/dashboard"
                    ? pathname === "/app/dashboard"
                    : pathname.startsWith(item.href);

                return (
                  <Link
                    key={`${section.title}-${item.href}-${item.label || itemIdx}`}
                    href={item.href}
                    prefetch={false}
                    onClick={onCloseMobile}
                    className={cn(
                      "flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors group",
                      isActive
                        ? "bg-yellow-400 text-slate-950 shadow-xs font-bold"
                        : "text-slate-600 hover:bg-yellow-50 hover:text-slate-950",
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "transition-colors",
                          isActive
                            ? "text-slate-950"
                            : "text-slate-400 group-hover:text-slate-800",
                        )}
                      >
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={cn(
                          "rounded-full px-1.5 py-0.2 text-[9px] font-mono",
                          isActive
                            ? "bg-yellow-500/30 text-slate-950 border border-yellow-600/30 font-semibold"
                            : "bg-slate-100 text-slate-600 border border-slate-200",
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* Tenant Context Footer */}
      <div className="p-3.5 border-t border-slate-200 bg-yellow-50/40">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>Tenant Scope</span>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </div>
          <div className="text-xs font-semibold text-slate-900 truncate">
            {user?.tenant?.name || "Vidyasagar State University"}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            CODE: {user?.tenant?.code || "VSB-CAMPUS"}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 h-screen sticky top-0 overflow-hidden z-20">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs animate-fade-in"
            onClick={onCloseMobile}
          />
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl animate-slide-right z-10">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
