"use client";

import React, { useState } from "react";
import {
  Search,
  X,
  Download,
  Eye,
  Rows,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ColumnDef, RowDensity } from "./data-grid.types";

interface DataGridToolbarProps<T> {
  searchQuery: string;
  onSearchChange?: (val: string) => void;
  searchPlaceholder?: string;
  customFilterSlot?: React.ReactNode;
  columns: ColumnDef<T>[];
  hiddenColumns: Set<string>;
  onToggleColumnVisibility: (colId: string) => void;
  density: RowDensity;
  onDensityChange: (density: RowDensity) => void;
  onExport: (format: "csv" | "json") => void;
  enableExport?: boolean;
  enableDensityToggle?: boolean;
  enableColumnVisibility?: boolean;
  totalRecords?: number;
}

export function DataGridToolbar<T>({
  searchQuery,
  onSearchChange,
  searchPlaceholder = "Search records...",
  customFilterSlot,
  columns,
  hiddenColumns,
  onToggleColumnVisibility,
  density,
  onDensityChange,
  onExport,
  enableExport = true,
  enableDensityToggle = true,
  enableColumnVisibility = true,
  totalRecords,
}: DataGridToolbarProps<T>) {
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const [densityMenuOpen, setDensityMenuOpen] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 rounded-t-xl">
      {/* Left: Search & Filter Slots */}
      <div className="flex flex-wrap items-center gap-2.5 flex-1">
        {onSearchChange && (
          <div className="relative flex-1 min-w-[220px] max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full pl-9 pr-8 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 transition"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange("")}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                aria-label="Clear search"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}

        {customFilterSlot}
        {totalRecords !== undefined && (
          <span className="hidden sm:inline-flex items-center text-xs text-slate-500 dark:text-slate-400 font-medium px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded-md">
            {totalRecords} records
          </span>
        )}
      </div>

      {/* Right: Controls & Actions */}
      <div className="flex items-center gap-2 self-end md:self-auto">
        {/* Column Visibility Menu */}
        {enableColumnVisibility && (
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Eye className="h-3.5 w-3.5" />}
              onClick={() => setColMenuOpen(!colMenuOpen)}
            >
              Columns
            </Button>

            {colMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setColMenuOpen(false)}
                />
                <div className="absolute right-0 mt-1.5 w-48 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 shadow-lg z-30 space-y-1">
                  <div className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Toggle Columns
                  </div>
                  {columns
                    .filter((c) => c.enableHiding !== false)
                    .map((col) => {
                      const isVisible = !hiddenColumns.has(col.id);
                      return (
                        <button
                          key={col.id}
                          onClick={() => onToggleColumnVisibility(col.id)}
                          className="flex items-center justify-between w-full px-2 py-1.5 text-xs text-left rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                        >
                          <span className="truncate">
                            {typeof col.header === "string" ? col.header : col.id}
                          </span>
                          {isVisible && <Check className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />}
                        </button>
                      );
                    })}
                </div>
              </>
            )}
          </div>
        )}

        {/* Density Control */}
        {enableDensityToggle && (
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Rows className="h-3.5 w-3.5" />}
              onClick={() => setDensityMenuOpen(!densityMenuOpen)}
            >
              Density
            </Button>

            {densityMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setDensityMenuOpen(false)}
                />
                <div className="absolute right-0 mt-1.5 w-36 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1.5 shadow-lg z-30 space-y-0.5">
                  {(["compact", "normal", "spacious"] as RowDensity[]).map((d) => (
                    <button
                      key={d}
                      onClick={() => {
                        onDensityChange(d);
                        setDensityMenuOpen(false);
                      }}
                      className={`flex items-center justify-between w-full px-2 py-1.5 text-xs capitalize rounded transition ${
                        density === d
                          ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold"
                          : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      <span>{d}</span>
                      {density === d && <Check className="h-3.5 w-3.5" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Export Data */}
        {enableExport && (
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Download className="h-3.5 w-3.5" />}
              onClick={() => setExportMenuOpen(!exportMenuOpen)}
            >
              Export
            </Button>

            {exportMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setExportMenuOpen(false)}
                />
                <div className="absolute right-0 mt-1.5 w-36 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1.5 shadow-lg z-30 space-y-0.5">
                  <button
                    onClick={() => {
                      onExport("csv");
                      setExportMenuOpen(false);
                    }}
                    className="flex items-center gap-2 w-full px-2.5 py-1.5 text-xs text-left rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                  >
                    Export as CSV
                  </button>
                  <button
                    onClick={() => {
                      onExport("json");
                      setExportMenuOpen(false);
                    }}
                    className="flex items-center gap-2 w-full px-2.5 py-1.5 text-xs text-left rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                  >
                    Export as JSON
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
