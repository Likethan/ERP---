import React from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface StatCardProps {
  label?: string;
  title?: string;
  value: string | number;
  description?: string;
  subtitle?: string;
  change?: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
  icon?: React.ReactNode;
  variant?: "default" | "indigo" | "emerald" | "amber" | "sky" | "purple";
  color?:
    "default" | "indigo" | "emerald" | "amber" | "sky" | "purple" | string;
  className?: string;
}

export function StatCard({
  label,
  title,
  value,
  description,
  subtitle,
  change,
  icon,
  variant = "default",
  color,
  className,
}: StatCardProps) {
  const displayLabel = label || title || "";
  const displayVariant =
    (variant !== "default" ? variant : (color as StatCardProps["variant"])) ||
    "default";
  const displayDesc = description || subtitle;

  const iconBgs: Record<string, string> = {
    default: "bg-amber-50 text-amber-800 border-amber-100",
    indigo: "bg-amber-50 text-amber-900 border-amber-100",
    emerald: "bg-emerald-50 text-emerald-800 border-emerald-200",
    amber: "bg-amber-50 text-amber-900 border-amber-200",
    sky: "bg-sky-50 text-sky-800 border-sky-200",
    purple: "bg-purple-50 text-purple-800 border-purple-200",
  };

  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/90 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.04)] transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-[0_8px_24px_rgba(16,24,40,0.07)]",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {displayLabel}
        </span>
        {icon && (
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl border",
              iconBgs[displayVariant] || iconBgs.default,
            )}
          >
            {icon}
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-[30px] font-semibold tracking-[-0.04em] text-slate-900 tabular-nums">
          {value}
        </span>
        {change && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-medium",
              change.trend === "up" && "text-emerald-600",
              change.trend === "down" && "text-red-600",
              change.trend === "neutral" && "text-slate-500",
            )}
          >
            {change.trend === "up" && <TrendingUp className="h-3 w-3" />}
            {change.trend === "down" && <TrendingDown className="h-3 w-3" />}
            {change.trend === "neutral" && <Minus className="h-3 w-3" />}
            {change.value}
          </span>
        )}
      </div>

      {displayDesc && (
        <p className="mt-1 text-xs text-slate-500 leading-relaxed font-normal">
          {displayDesc}
        </p>
      )}
    </div>
  );
}
