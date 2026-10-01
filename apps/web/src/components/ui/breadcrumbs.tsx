"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BreadcrumbSegment {
  label: string;
  href?: string;
}

export interface BreadcrumbsProps {
  customSegments?: BreadcrumbSegment[];
  items?: BreadcrumbSegment[];
  className?: string;
}

export function Breadcrumbs({ customSegments, items, className }: BreadcrumbsProps) {
  const pathname = usePathname();
  const segments = customSegments || items;

  // If custom segments or items provided, use them
  if (segments && segments.length > 0) {
    return (
      <nav aria-label="Breadcrumb" className={cn("flex items-center text-xs text-slate-400", className)}>
        <ol className="flex items-center gap-1.5 flex-wrap">
          <li>
            <Link
              href="/app/dashboard"
              className="text-slate-500 hover:text-slate-300 transition-colors flex items-center"
            >
              <Home className="h-3.5 w-3.5" />
            </Link>
          </li>
          {segments.map((segment, idx) => {
            const isLast = idx === segments.length - 1;
            return (
              <li key={idx} className="flex items-center gap-1.5">
                <ChevronRight className="h-3 w-3 text-slate-600" />
                {segment.href && !isLast ? (
                  <Link
                    href={segment.href}
                    className="text-slate-400 hover:text-white transition-colors"
                  >
                    {segment.label}
                  </Link>
                ) : (
                  <span className="font-medium text-slate-200">{segment.label}</span>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    );
  }

  // Derive automatically from pathname
  const parts = pathname.split("/").filter(Boolean);
  // parts e.g. ["app", "students", "24CSE0101"]
  const appIndex = parts.indexOf("app");
  const relevantParts = appIndex !== -1 ? parts.slice(appIndex + 1) : parts;

  const formatLabel = (str: string) => {
    return str
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center text-xs text-slate-400", className)}>
      <ol className="flex items-center gap-1.5 flex-wrap">
        <li>
          <Link
            href="/app/dashboard"
            className="text-slate-500 hover:text-slate-300 transition-colors flex items-center"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
        </li>
        {relevantParts.map((part, idx) => {
          const isLast = idx === relevantParts.length - 1;
          const href = `/app/${relevantParts.slice(0, idx + 1).join("/")}`;
          return (
            <li key={idx} className="flex items-center gap-1.5">
              <ChevronRight className="h-3 w-3 text-slate-600" />
              {isLast ? (
                <span className="font-medium text-slate-200">{formatLabel(part)}</span>
              ) : (
                <Link
                  href={href}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  {formatLabel(part)}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
