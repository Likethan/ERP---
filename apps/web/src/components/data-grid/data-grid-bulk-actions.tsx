"use client";

import React from "react";
import { CheckSquare, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BulkAction } from "./data-grid.types";

interface DataGridBulkActionsProps<T> {
  selectedCount: number;
  selectedItems: T[];
  actions?: BulkAction<T>[];
  onClearSelection: () => void;
}

export function DataGridBulkActions<T>({
  selectedCount,
  selectedItems,
  actions = [],
  onClearSelection,
}: DataGridBulkActionsProps<T>) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-indigo-50/90 dark:bg-indigo-950/80 border-b border-indigo-200 dark:border-indigo-800/80 text-xs text-indigo-950 dark:text-indigo-200 transition-all duration-200">
      <div className="flex items-center gap-2">
        <CheckSquare className="h-4 w-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
        <span className="font-semibold">
          {selectedCount} {selectedCount === 1 ? "record" : "records"} selected
        </span>
      </div>

      <div className="flex items-center gap-2">
        {actions.map((act, idx) => (
          <Button
            key={idx}
            size="sm"
            variant={act.variant || "secondary"}
            leftIcon={act.icon}
            onClick={() => act.onClick(selectedItems)}
          >
            {act.label}
          </Button>
        ))}

        <Button
          size="sm"
          variant="ghost"
          onClick={onClearSelection}
          leftIcon={<X className="h-3.5 w-3.5" />}
          className="text-slate-500 hover:text-slate-700 dark:text-slate-400"
        >
          Deselect
        </Button>
      </div>
    </div>
  );
}
