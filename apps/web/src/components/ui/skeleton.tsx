import React from "react";
import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-slate-800/80", className)}
      {...props}
    />
  );
}

export function TableSkeleton({
  rows = 5,
  cols = 4,
}: {
  rows?: number;
  cols?: number;
}) {
  return (
    <div className="w-full space-y-3 p-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-8 w-32" />
      </div>
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div
            key={rIdx}
            className="flex gap-4 py-2 border-b border-slate-800/50"
          >
            {Array.from({ length: cols }).map((_, cIdx) => (
              <Skeleton
                key={cIdx}
                className={cn("h-4", cIdx === 0 ? "w-1/4" : "w-1/5")}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
