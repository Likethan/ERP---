"use client";

import React from "react";
import { Filter, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

export interface FilterBarProps {
  children: React.ReactNode;
  activeFilterCount?: number;
  onReset?: () => void;
  className?: string;
}

export function FilterBar({
  children,
  activeFilterCount = 0,
  onReset,
  className,
}: FilterBarProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 p-3 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm",
        className,
      )}
    >
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1">
        <Filter className="h-3.5 w-3.5 text-indigo-400" />
        <span>Filters</span>
        {activeFilterCount > 0 && (
          <span className="flex h-4 min-w-[16px] items-center justify-center rounded-full bg-indigo-500/20 px-1 text-[10px] font-mono text-indigo-300 border border-indigo-500/30">
            {activeFilterCount}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2.5 flex-1">
        {children}
      </div>

      {activeFilterCount > 0 && onReset && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="text-xs text-slate-400 hover:text-white h-8 px-2"
          leftIcon={<RotateCcw className="h-3 w-3" />}
        >
          Reset
        </Button>
      )}
    </div>
  );
}
