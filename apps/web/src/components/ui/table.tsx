import React from "react";
import { cn } from "@/lib/utils";

export function Table({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="relative w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-xs">
      <table
        className={cn(
          "w-full caption-bottom text-sm text-left text-slate-800",
          className,
        )}
        {...props}
      />
    </div>
  );
}

export function TableHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn(
        "border-b border-slate-200 bg-yellow-50/60 text-xs font-semibold uppercase tracking-wider text-slate-700",
        className,
      )}
      {...props}
    />
  );
}

export function TableBody({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody
      className={cn(
        "[&_tr:last-child]:border-0 divide-y divide-slate-100",
        className,
      )}
      {...props}
    />
  );
}

export function TableRow({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        "transition-colors hover:bg-yellow-50/40 data-[state=selected]:bg-yellow-100/50",
        className,
      )}
      {...props}
    />
  );
}

export function TableHead({
  className,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        "h-10 px-4 text-left align-middle font-medium text-slate-600 whitespace-nowrap",
        className,
      )}
      {...props}
    />
  );
}

export function TableCell({
  className,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn("px-4 py-3 align-middle text-slate-700 text-sm", className)}
      {...props}
    />
  );
}

export interface TablePaginationProps {
  currentPage: number;
  totalPages: number;
  totalRecords?: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function TablePagination({
  currentPage,
  totalPages,
  totalRecords,
  pageSize,
  onPageChange,
  className,
}: TablePaginationProps) {
  const startRecord = Math.min(
    (currentPage - 1) * pageSize + 1,
    totalRecords || 0,
  );
  const endRecord = Math.min(currentPage * pageSize, totalRecords || 0);

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t border-slate-200 text-xs text-slate-500 bg-yellow-50/20",
        className,
      )}
    >
      <div>
        {totalRecords !== undefined ? (
          <span>
            Showing <strong className="text-slate-900">{startRecord}</strong> to{" "}
            <strong className="text-slate-900">{endRecord}</strong> of{" "}
            <strong className="text-slate-900">{totalRecords}</strong> entries
          </span>
        ) : (
          <span>
            Page {currentPage} of {totalPages}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="inline-flex items-center justify-center h-8 px-2.5 rounded border border-slate-200 bg-white text-slate-700 hover:bg-yellow-50 hover:border-yellow-300 hover:text-slate-950 disabled:opacity-40 disabled:pointer-events-none transition-colors shadow-xs"
        >
          Previous
        </button>
        <span className="px-2 font-mono text-xs text-slate-700">
          {currentPage} / {Math.max(1, totalPages)}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="inline-flex items-center justify-center h-8 px-2.5 rounded border border-slate-200 bg-white text-slate-700 hover:bg-yellow-50 hover:border-yellow-300 hover:text-slate-950 disabled:opacity-40 disabled:pointer-events-none transition-colors shadow-xs"
        >
          Next
        </button>
      </div>
    </div>
  );
}
