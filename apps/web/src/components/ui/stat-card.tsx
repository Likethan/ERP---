import React from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface StatCardProps {
  label?: string;
  title?: string;
  value: string | number;
  description?: string;
  change?: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
  icon?: React.ReactNode;
  variant?: "default" | "indigo" | "emerald" | "amber" | "sky" | "purple";
  color?: "default" | "indigo" | "emerald" | "amber" | "sky" | "purple" | string;
  className?: string;
}

export function StatCard({
  label,
  title,
  value,
  description,
  change,
  icon,
  variant = "default",
  color,
  className,
}: StatCardProps) {
  const displayLabel = label || title || "";
  const displayVariant = (variant !== "default" ? variant : (color as StatCardProps["variant"])) || "default";

  const iconBgs: Record<string, string> = {
    default: "bg-slate-800 text-slate-300 border-slate-700/60",
    indigo: "bg-indigo-950/80 text-indigo-400 border-indigo-800/80",
    emerald: "bg-emerald-950/80 text-emerald-400 border-emerald-800/80",
    amber: "bg-amber-950/80 text-amber-400 border-amber-800/80",
    sky: "bg-sky-950/80 text-sky-400 border-sky-800/80",
    purple: "bg-purple-950/80 text-purple-400 border-purple-800/80",
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-slate-700",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {displayLabel}
        </span>
        {icon && (
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg border",
              iconBgs[displayVariant] || iconBgs.default
            )}
          >
            {icon}
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {change && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-medium",
              change.trend === "up" && "text-emerald-400",
              change.trend === "down" && "text-red-400",
              change.trend === "neutral" && "text-slate-400"
            )}
          >
            {change.trend === "up" && <TrendingUp className="h-3 w-3" />}
            {change.trend === "down" && <TrendingDown className="h-3 w-3" />}
            {change.trend === "neutral" && <Minus className="h-3 w-3" />}
            {change.value}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1 text-xs text-slate-400 leading-relaxed font-normal">
          {description}
        </p>
      )}
    </div>
  );
}
