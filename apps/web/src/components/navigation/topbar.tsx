"use client";

import React, { useState } from "react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { RoleSwitcher } from "./role-switcher";
import { CommandPalette } from "./command-palette";
import { NotificationDrawer } from "./notification-drawer";
import { useAuth } from "@/lib/auth-context";
import { Search, Bell, Menu, Shield, LogOut } from "lucide-react";

interface TopbarProps {
  onToggleSidebar?: () => void;
}

export function Topbar({ onToggleSidebar }: TopbarProps) {
  const { user, activePersona, logout } = useAuth();
  const [commandOpen, setCommandOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 sm:px-6 backdrop-blur-md">
        {/* Left: Mobile hamburger & Breadcrumbs */}
        <div className="flex items-center gap-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              aria-label="Toggle navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}
          <Breadcrumbs />
        </div>

        {/* Right: Global Search Trigger, Role Switcher, Notification Bell, User Avatar */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Command Palette Trigger */}
          <button
            onClick={() => setCommandOpen(true)}
            className="hidden sm:flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-700 hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-pointer w-48 lg:w-64"
          >
            <Search className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            <span className="flex-1 text-left truncate">Search CampusOS...</span>
            <kbd className="hidden lg:inline-flex items-center rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-slate-400">
              ⌘K
            </kbd>
          </button>

          {/* Mobile search icon */}
          <button
            onClick={() => setCommandOpen(true)}
            className="sm:hidden rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
            aria-label="Search"
          >
            <Search className="h-5 w-5" />
          </button>

          {/* Role Switcher */}
          <RoleSwitcher />

          {/* Notifications Bell */}
          <button
            onClick={() => setNotifOpen(true)}
            className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            aria-label="Open notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
            </span>
          </button>

          {/* User Profile Avatar & Menu */}
          <div className="relative">
            <button
              onClick={() => setUserDropdownOpen(!userDropdownOpen)}
              className="flex items-center gap-2 rounded-lg p-1 text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Open user menu"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs font-bold font-mono">
                {activePersona.avatarInitials}
              </div>
            </button>

            {userDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setUserDropdownOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-800 bg-slate-900 p-2 shadow-2xl z-50 animate-scale-in">
                  <div className="px-3 py-2.5 border-b border-slate-800 mb-1">
                    <div className="text-xs font-semibold text-white truncate">
                      {user?.first_name} {user?.last_name}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono truncate mt-0.5">
                      {user?.email}
                    </div>
                    <div className="mt-2 inline-flex items-center gap-1 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-indigo-300 border border-slate-700">
                      <Shield className="h-3 w-3 text-indigo-400" />
                      {activePersona.roleTitle}
                    </div>
                  </div>

                  <div className="space-y-0.5 text-xs">
                    <div className="px-3 py-2 text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Tenant</span>
                      <span className="font-mono text-slate-200">
                        {user?.tenant?.code || "VSB-CAMPUS"}
                      </span>
                    </div>

                    <button
                      onClick={() => {
                        setUserDropdownOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Global Command Palette Modal */}
      <CommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />

      {/* Slide-over Notification Drawer */}
      <NotificationDrawer open={notifOpen} onClose={() => setNotifOpen(false)} />
    </>
  );
}
