"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  X,
  Layers,
  User,
  Building,
  BookOpen,
  Home,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { IntelligenceDomain } from "@campusos/types";

interface AIQueryComposerProps {
  onSend: (query: string, domain: IntelligenceDomain, context?: any) => void;
  loading: boolean;
  presetPrompts?: { label: string; query: string; domain: IntelligenceDomain }[];
  initialQuery?: string;
}

export function AIQueryComposer({
  onSend,
  loading,
  presetPrompts = [],
  initialQuery = "",
}: AIQueryComposerProps) {
  const [input, setInput] = useState(initialQuery);
  const [selectedDomain, setSelectedDomain] = useState<IntelligenceDomain>(IntelligenceDomain.ALL);
  const [selectedContext, setSelectedContext] = useState<{
    type: "ALL" | "STUDENT" | "DEPARTMENT" | "COURSE" | "HOSTEL";
    id?: string;
    label: string;
  }>({ type: "ALL", label: "All Campus" });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (initialQuery) {
      setInput(initialQuery);
      textareaRef.current?.focus();
    }
  }, [initialQuery]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    onSend(text, selectedDomain, selectedContext.type !== "ALL" ? selectedContext : undefined);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const domains = [
    { value: IntelligenceDomain.ALL, label: "All Campus" },
    { value: IntelligenceDomain.ATTENDANCE, label: "Attendance" },
    { value: IntelligenceDomain.ACADEMICS, label: "Academics" },
    { value: IntelligenceDomain.EXAMINATIONS, label: "Examinations" },
    { value: IntelligenceDomain.FINANCE, label: "Finance" },
    { value: IntelligenceDomain.PLACEMENT, label: "Placement" },
    { value: IntelligenceDomain.INFRASTRUCTURE, label: "Infrastructure" },
    { value: IntelligenceDomain.DOCUMENTS, label: "Documents" },
  ];

  const contexts = [
    { type: "ALL" as const, label: "All Campus" },
    { type: "STUDENT" as const, id: "stu-001", label: "Aarav Patel (22CS001)" },
    { type: "DEPARTMENT" as const, id: "dept-cse", label: "CSE Department" },
    { type: "COURSE" as const, id: "cs-301", label: "CS301 (Data Structures)" },
    { type: "HOSTEL" as const, id: "hst-01", label: "Block A (Boys Hostel)" },
  ];

  return (
    <div className="border-t border-slate-200 bg-white p-3 sm:p-4 space-y-2.5">
      {/* Prompt Suggestions */}
      {presetPrompts.length > 0 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-blue-500" /> Suggested:
          </span>
          {presetPrompts.slice(0, 4).map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setInput(p.query);
                setSelectedDomain(p.domain);
                textareaRef.current?.focus();
              }}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-300 transition-colors whitespace-nowrap text-xs shrink-0"
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      {/* Query Bar */}
      <form onSubmit={handleSubmit} className="relative rounded-xl border border-slate-300 bg-white focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100 transition-all shadow-sm">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask CampusOS Intelligence across academics, attendance, finance, placement, infrastructure..."
          rows={2}
          className="w-full resize-none p-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none bg-transparent"
        />

        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-t border-slate-100 bg-slate-50/50 rounded-b-xl">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Domain Selector */}
            <div className="flex items-center gap-1 text-slate-500">
              <Layers className="w-3.5 h-3.5" />
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value as IntelligenceDomain)}
                className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                {domains.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Context Selector */}
            <div className="flex items-center gap-1 text-slate-500">
              <User className="w-3.5 h-3.5" />
              <select
                value={selectedContext.type}
                onChange={(e) => {
                  const found = contexts.find((c) => c.type === e.target.value);
                  if (found) setSelectedContext(found);
                }}
                className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                {contexts.map((c) => (
                  <option key={c.type} value={c.type}>
                    Context: {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-1.5 ml-auto">
            {input && (
              <button
                type="button"
                onClick={() => setInput("")}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200 transition-colors"
                title="Clear query"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <Button
              type="submit"
              size="sm"
              disabled={!input.trim() || loading}
              className="gap-1.5 font-semibold text-xs"
            >
              {loading ? (
                <>
                  <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Send
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
