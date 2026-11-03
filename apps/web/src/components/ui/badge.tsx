import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?:
    | "default"
    | "success"
    | "warning"
    | "destructive"
    | "danger"
    | "info"
    | "secondary"
    | "neutral"
    | "outline";
  dot?: boolean;
}

export function Badge({
  className,
  variant = "default",
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const variantStyles: Record<string, { badge: string; dot: string }> = {
    default: {
      badge: "bg-slate-100 text-slate-800 border-slate-200",
      dot: "bg-slate-500",
    },
    success: {
      badge: "bg-emerald-50 text-emerald-800 border-emerald-200",
      dot: "bg-emerald-600",
    },
    warning: {
      badge: "bg-amber-50 text-amber-900 border-amber-200",
      dot: "bg-amber-600",
    },
    destructive: {
      badge: "bg-red-50 text-red-800 border-red-200",
      dot: "bg-red-600",
    },
    danger: {
      badge: "bg-red-50 text-red-800 border-red-200",
      dot: "bg-red-600",
    },
    info: {
      badge: "bg-sky-50 text-sky-800 border-sky-200",
      dot: "bg-sky-600",
    },
    secondary: {
      badge: "bg-yellow-100 text-yellow-950 border-yellow-300 font-semibold",
      dot: "bg-yellow-600",
    },
    neutral: {
      badge: "bg-slate-100 text-slate-700 border-slate-200",
      dot: "bg-slate-500",
    },
    outline: {
      badge: "bg-white text-slate-700 border-slate-300",
      dot: "bg-slate-500",
    },
  };

  const currentVariant = variantStyles[variant] || variantStyles.default;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide transition-colors",
        currentVariant.badge,
        className,
      )}
      {...props}
    >
      {dot && (
        <span className={cn("h-1.5 w-1.5 rounded-full", currentVariant.dot)} />
      )}
      {children}
    </div>
  );
}
