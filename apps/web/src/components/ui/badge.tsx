import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?:
    | "default"
    | "success"
    | "warning"
    | "destructive"
    | "info"
    | "secondary"
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
      badge: "bg-slate-800 text-slate-300 border-slate-700/60",
      dot: "bg-slate-400",
    },
    success: {
      badge: "bg-emerald-950/70 text-emerald-400 border-emerald-800/80",
      dot: "bg-emerald-400",
    },
    warning: {
      badge: "bg-amber-950/70 text-amber-400 border-amber-800/80",
      dot: "bg-amber-400",
    },
    destructive: {
      badge: "bg-red-950/70 text-red-400 border-red-800/80",
      dot: "bg-red-400",
    },
    info: {
      badge: "bg-sky-950/70 text-sky-400 border-sky-800/80",
      dot: "bg-sky-400",
    },
    secondary: {
      badge: "bg-indigo-950/70 text-indigo-400 border-indigo-800/80",
      dot: "bg-indigo-400",
    },
    outline: {
      badge: "bg-transparent text-slate-400 border-slate-700",
      dot: "bg-slate-400",
    },
  };

  const currentVariant = variantStyles[variant] || variantStyles.default;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide transition-colors",
        currentVariant.badge,
        className
      )}
      {...props}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", currentVariant.dot)} />}
      {children}
    </div>
  );
}
