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
        "flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-950/40 my-6",
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 mb-4">
        {icon || <FolderOpen className="h-6 w-6 text-slate-500" />}
      </div>
      <h3 className="text-base font-semibold text-white tracking-tight">
        {title}
      </h3>
      <p className="mt-1 max-w-sm text-xs text-slate-400 leading-relaxed">
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
