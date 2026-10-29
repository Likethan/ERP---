import React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./button";

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Failed to load data",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-xl border border-red-900/50 bg-red-950/20 my-6",
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-950/40 border border-red-800/60 text-red-400 mb-3">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-semibold text-white tracking-tight">
        {title}
      </h3>
      <p className="mt-1 max-w-md text-xs text-red-300/80 leading-relaxed">
        {message}
      </p>
      {onRetry && (
        <div className="mt-4">
          <Button
            onClick={onRetry}
            size="sm"
            variant="outline"
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
}
