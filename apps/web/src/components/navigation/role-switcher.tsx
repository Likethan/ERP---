"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  ChevronDown,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  Building,
  Briefcase,
  Landmark,
  BedDouble,
  Bus,
  Wrench,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function RoleSwitcher({ className }: { className?: string }) {
  const { activePersona, personas, switchPersona } = useAuth();
  const [open, setOpen] = useState(false);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "SUPER_ADMIN":
        return <ShieldCheck className="h-4 w-4 text-emerald-400" />;
      case "HOD":
        return <Building className="h-4 w-4 text-indigo-400" />;
      case "FACULTY":
        return <UserCheck className="h-4 w-4 text-sky-400" />;
      case "STUDENT":
        return <GraduationCap className="h-4 w-4 text-amber-400" />;
      case "ACCOUNTS":
        return <Landmark className="h-4 w-4 text-emerald-400" />;
      case "PLACEMENT_OFFICER":
        return <Briefcase className="h-4 w-4 text-purple-400" />;
      case "WARDEN":
        return <BedDouble className="h-4 w-4 text-teal-400" />;
      case "TRANSPORT_OFFICER":
        return <Bus className="h-4 w-4 text-orange-400" />;
      case "FACILITY_OFFICER":
        return <Wrench className="h-4 w-4 text-yellow-400" />;
      default:
        return <UserCheck className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-800 hover:border-yellow-400 hover:bg-yellow-50/50 transition-all cursor-pointer shadow-xs"
        aria-label="Switch Role Persona"
      >
        <span className="flex items-center gap-1.5">
          {getRoleIcon(activePersona.role)}
          <span className="font-semibold text-slate-900 max-w-[130px] truncate sm:max-w-none">
            {activePersona.role.replace("_", " ")}
          </span>
        </span>
        <span className="hidden md:inline text-slate-400 font-mono text-[11px] border-l border-slate-200 pl-2 text-slate-500">
          {activePersona.name}
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-2 shadow-xl z-50 animate-scale-in">
            <div className="px-3 py-2 border-b border-slate-100 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                Switch Role Persona (Demo Mode)
              </span>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Experience role-aware dashboards & permissions.
              </p>
            </div>

            <div className="space-y-1">
              {personas.map((persona) => {
                const isCurrent = persona.role === activePersona.role;
                return (
                  <button
                    key={persona.id}
                    onClick={() => {
                      switchPersona(persona.role);
                      setOpen(false);
                    }}
                    className={cn(
                      "w-full text-left rounded-lg px-3 py-2 text-xs transition-colors flex items-start gap-2.5 cursor-pointer",
                      isCurrent
                        ? "bg-yellow-100 text-slate-950 font-semibold border border-yellow-400"
                        : "text-slate-700 hover:bg-yellow-50 hover:text-slate-950",
                    )}
                  >
                    <div className="mt-0.5 shrink-0">
                      {getRoleIcon(persona.role)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold flex items-center justify-between text-slate-900">
                        <span>{persona.name}</span>
                        {isCurrent && (
                          <span className="text-[10px] text-yellow-800 font-bold font-mono uppercase">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">
                        {persona.roleTitle}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
