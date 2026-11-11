import React from "react";
import { cn } from "@/lib/utils";
import { FolderOpen } from "lucide-react";
import { Button } from "./button";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-slate-300 bg-yellow-50/30 my-6",
        className,
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-yellow-50 border border-yellow-200 text-yellow-700 shadow-xs mb-4">
        {icon || <FolderOpen className="h-6 w-6 text-yellow-600" />}
      </div>
      <h3 className="text-base sm:text-lg font-semibold text-slate-900 tracking-tight">
        {title}
      </h3>
      <p className="mt-1.5 max-w-md text-xs sm:text-sm text-slate-600 leading-relaxed">
        {description}
      </p>
      {actionLabel && onAction && (
        <div className="mt-5">
          <Button onClick={onAction} size="sm" variant="primary">
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
