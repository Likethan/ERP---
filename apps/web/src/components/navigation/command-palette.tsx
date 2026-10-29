"use client";

import React, { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Command,
  X,
  ArrowRight,
  User,
  BookOpen,
  Briefcase,
  FileText,
  Calendar,
  DollarSign,
  Sparkles,
  Loader2,
  FileSpreadsheet,
  CheckSquare,
  Award,
} from "lucide-react";
import { searchService } from "@/services/search.service";
import { GlobalSearchResultItem } from "@/types/domain";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GlobalSearchResultItem[]>([]);
  const [isSearching, startTransition] = useTransition();

  const QUICK_LINKS = [
    {
      label: "Dashboard",
      href: "/app/dashboard",
      icon: <Command className="h-4 w-4 text-indigo-400" />,
    },
    {
      label: "Students Registry",
      href: "/app/students",
      icon: <User className="h-4 w-4 text-emerald-400" />,
    },
    {
      label: "Faculty Directory",
      href: "/app/faculty",
      icon: <User className="h-4 w-4 text-sky-400" />,
    },
    {
      label: "Academics & Curricula",
      href: "/app/academics",
      icon: <BookOpen className="h-4 w-4 text-amber-400" />,
    },
    {
      label: "Attendance Sessions",
      href: "/app/attendance",
      icon: <Calendar className="h-4 w-4 text-purple-400" />,
    },
    {
      label: "Examinations & Marks",
      href: "/app/examinations",
      icon: <FileText className="h-4 w-4 text-rose-400" />,
    },
    {
      label: "Finance & Invoices",
      href: "/app/finance",
      icon: <DollarSign className="h-4 w-4 text-emerald-400" />,
    },
    {
      label: "Placements & Career",
      href: "/app/placement",
      icon: <Briefcase className="h-4 w-4 text-blue-400" />,
    },
    {
      label: "Campus Intelligence",
      href: "/app/intelligence",
      icon: <Sparkles className="h-4 w-4 text-yellow-400" />,
    },
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onClose(); // toggle
      }
      if (e.key === "Escape" && open) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setResults([]);
      return;
    }
    const timer = setTimeout(() => {
      startTransition(async () => {
        const res = await searchService.search(query);
        setResults(res.data);
      });
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  if (!open) return null;

  const navigateTo = (href: string) => {
    onClose();
    router.push(href);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Student":
        return <User className="h-4 w-4 text-emerald-400" />;
      case "Faculty":
        return <User className="h-4 w-4 text-sky-400" />;
      case "Staff":
        return <Briefcase className="h-4 w-4 text-purple-400" />;
      case "Course":
        return <BookOpen className="h-4 w-4 text-amber-400" />;
      case "Curriculum":
        return <FileSpreadsheet className="h-4 w-4 text-emerald-400" />;
      case "Offering":
        return <CheckSquare className="h-4 w-4 text-sky-400" />;
      case "Attendance":
        return <Calendar className="h-4 w-4 text-teal-400" />;
      case "Examination":
      case "Assessment":
        return <Award className="h-4 w-4 text-rose-400" />;
      case "Drive":
      case "Placement":
        return <Briefcase className="h-4 w-4 text-purple-400" />;
      case "Company":
        return <Briefcase className="h-4 w-4 text-indigo-400" />;
      case "Application":
        return <FileSpreadsheet className="h-4 w-4 text-sky-400" />;
      case "Interview":
        return <Calendar className="h-4 w-4 text-amber-400" />;
      case "Offer":
        return <Award className="h-4 w-4 text-emerald-400" />;
      case "Invoice":
      case "Finance":
      case "Payment":
      case "Receipt":
      case "Scholarship":
        return <DollarSign className="h-4 w-4 text-emerald-400" />;
      case "Event":
        return <Calendar className="h-4 w-4 text-blue-400" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 sm:p-6 sm:pt-20">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Palette Modal */}
      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden animate-scale-in z-10"
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 border-b border-slate-800 bg-slate-950/40">
          {isSearching ? (
            <Loader2 className="h-5 w-5 text-indigo-400 animate-spin shrink-0 mr-3" />
          ) : (
            <Search className="h-5 w-5 text-slate-500 shrink-0 mr-3" />
          )}
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search CampusOS across Students, Faculty, Courses, Drives, Invoices..."
            className="h-14 w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
          />
          {query ? (
            <button
              onClick={() => setQuery("")}
              className="text-slate-500 hover:text-slate-300 p-1"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <span className="hidden sm:inline text-[11px] font-mono text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
              ESC
            </span>
          )}
        </div>

        {/* Results / Navigation Body */}
        <div className="max-h-[60vh] overflow-y-auto p-3">
          {query.trim().length >= 2 ? (
            <div>
              <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Search Results ({results.length})
              </div>
              {results.length > 0 ? (
                <div className="space-y-1 mt-1">
                  {results.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => navigateTo(item.href)}
                      className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/80 text-left transition-colors cursor-pointer group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 border border-slate-700/60">
                          {getCategoryIcon(item.category)}
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors flex items-center gap-2">
                            <span>{item.title}</span>
                            {item.badge && (
                              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-300 border border-slate-700">
                                {item.badge}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-400 mt-0.5">
                            {item.subtitle}
                          </div>
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-slate-600 group-hover:text-white transition-colors" />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-400">
                  No matching records found for "{query}".
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Quick Navigation
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-1">
                {QUICK_LINKS.map((link) => (
                  <button
                    key={link.href}
                    onClick={() => navigateTo(link.href)}
                    className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-800/70 text-slate-300 hover:text-white text-xs font-medium text-left transition-colors cursor-pointer"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded bg-slate-800/80 border border-slate-700/50">
                      {link.icon}
                    </div>
                    <span>{link.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span>Navigation: Click to jump</span>
            <span>•</span>
            <span>Search: Full cross-domain index</span>
          </div>
          <span className="font-mono">CampusOS Enterprise Search</span>
        </div>
      </div>
    </div>
  );
}
