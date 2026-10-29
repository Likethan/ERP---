"use client";

import React, { useState, useMemo } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, AlertTriangle } from "lucide-react";
import { DataGridProps, SortState, RowDensity } from "./data-grid.types";
export type {
  ColumnDef,
  DataGridProps,
  BulkAction,
  SortState,
  RowDensity,
} from "./data-grid.types";
import { DataGridToolbar } from "./data-grid-toolbar";
import { DataGridPagination } from "./data-grid-pagination";
import { DataGridBulkActions } from "./data-grid-bulk-actions";
import { TableSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";

export function DataGrid<T>({
  data,
  columns,
  keyExtractor = (item: any) => item?.id ?? item?._id ?? String(Math.random()),
  loading = false,
  error = null,
  onRetry,
  // Selection
  selectable = false,
  selectedKeys,
  onSelectionChange,
  bulkActions = [],
  // Pagination
  paginated = true,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [10, 25, 50, 100],
  currentPage: controlledCurrentPage,
  totalRecords: controlledTotalRecords,
  onPageChange: controlledOnPageChange,
  onPageSizeChange: controlledOnPageSizeChange,
  // Toolbar features
  searchPlaceholder = "Search records...",
  onSearchChange: controlledOnSearchChange,
  customFilterSlot,
  exportFileName = "campusos-export",
  enableExport = true,
  enableDensityToggle = true,
  enableColumnVisibility = true,
  // Empty & States
  emptyTitle = "No records found",
  emptyDescription = "There are no entries matching your current query or filter criteria.",
  emptyMessage,
  emptyState,
  emptyActionLabel,
  onEmptyAction,
  // Layout
  className = "",
  mobileCardRender,
}: DataGridProps<T>) {
  // Local sorting
  const [sortState, setSortState] = useState<SortState | null>(null);

  // Local pagination if uncontrolled
  const [localPage, setLocalPage] = useState(1);
  const [localPageSize, setLocalPageSize] = useState(initialPageSize);

  // Local search if uncontrolled
  const [localSearch, setLocalSearch] = useState("");

  // Density
  const [density, setDensity] = useState<RowDensity>("normal");

  // Hidden columns
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(() => {
    const hidden = new Set<string>();
    columns.forEach((col) => {
      if (col.defaultHidden) hidden.add(col.id);
    });
    return hidden;
  });

  // Local selection if uncontrolled
  const [localSelectedKeys, setLocalSelectedKeys] = useState<Set<string>>(
    new Set(),
  );

  const activeSelectedKeys =
    selectedKeys !== undefined ? selectedKeys : localSelectedKeys;
  const setActiveSelectedKeys = (keys: Set<string>) => {
    if (onSelectionChange) {
      onSelectionChange(keys);
    } else {
      setLocalSelectedKeys(keys);
    }
  };

  const isControlledPagination =
    controlledCurrentPage !== undefined && controlledOnPageChange !== undefined;
  const currentPage = isControlledPagination
    ? controlledCurrentPage
    : localPage;
  const pageSize = isControlledPagination ? initialPageSize : localPageSize;

  const handlePageChange = (page: number) => {
    if (isControlledPagination) {
      controlledOnPageChange(page);
    } else {
      setLocalPage(page);
    }
  };

  const handlePageSizeChange = (size: number) => {
    if (controlledOnPageSizeChange) {
      controlledOnPageSizeChange(size);
    } else {
      setLocalPageSize(size);
      setLocalPage(1);
    }
  };

  const searchQuery = controlledOnSearchChange !== undefined ? "" : localSearch;
  const handleSearchChange = (query: string) => {
    if (controlledOnSearchChange) {
      controlledOnSearchChange(query);
    } else {
      setLocalSearch(query);
      setLocalPage(1);
    }
  };

  // Visible columns
  const visibleColumns = useMemo(() => {
    return columns.filter((col) => !hiddenColumns.has(col.id));
  }, [columns, hiddenColumns]);

  const toggleColumnVisibility = (colId: string) => {
    setHiddenColumns((prev) => {
      const next = new Set(prev);
      if (next.has(colId)) {
        next.delete(colId);
      } else {
        next.add(colId);
      }
      return next;
    });
  };

  // Sorting
  const handleSort = (colId: string) => {
    setSortState((prev) => {
      if (prev?.key === colId) {
        if (prev.direction === "asc") {
          return { key: colId, direction: "desc" };
        } else {
          return null; // Reset sort
        }
      }
      return { key: colId, direction: "asc" };
    });
  };

  // Client-side filtering & sorting if uncontrolled
  const processedData = useMemo(() => {
    let result = [...data];

    // Search filter
    if (!controlledOnSearchChange && localSearch.trim()) {
      const q = localSearch.toLowerCase().trim();
      result = result.filter((item) => {
        return columns.some((col) => {
          let val: unknown = undefined;
          if (col.accessorFn) {
            val = col.accessorFn(item);
          } else if (col.accessorKey) {
            val = item[col.accessorKey];
          }
          if (val === undefined || val === null) return false;
          return String(val).toLowerCase().includes(q);
        });
      });
    }

    // Sort
    if (sortState) {
      const { key, direction } = sortState;
      const targetCol = columns.find((c) => c.id === key);
      result.sort((a, b) => {
        let valA: unknown = targetCol?.accessorFn
          ? targetCol.accessorFn(a)
          : targetCol?.accessorKey
            ? a[targetCol.accessorKey]
            : "";
        let valB: unknown = targetCol?.accessorFn
          ? targetCol.accessorFn(b)
          : targetCol?.accessorKey
            ? b[targetCol.accessorKey]
            : "";

        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();

        if (String(valA) < String(valB)) return direction === "asc" ? -1 : 1;
        if (String(valA) > String(valB)) return direction === "asc" ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [data, controlledOnSearchChange, localSearch, columns, sortState]);

  // Total records & sliced data
  const totalRecords =
    isControlledPagination && controlledTotalRecords !== undefined
      ? controlledTotalRecords
      : processedData.length;
  const totalPages = Math.ceil(totalRecords / pageSize) || 1;

  const paginatedData = useMemo(() => {
    if (isControlledPagination) return data;
    if (!paginated) return processedData;
    const start = (currentPage - 1) * pageSize;
    return processedData.slice(start, start + pageSize);
  }, [
    isControlledPagination,
    data,
    paginated,
    processedData,
    currentPage,
    pageSize,
  ]);

  // Row selection helpers
  const allPageKeys = useMemo(() => {
    return paginatedData.map(keyExtractor);
  }, [paginatedData, keyExtractor]);

  const isAllPageSelected =
    allPageKeys.length > 0 &&
    allPageKeys.every((k) => activeSelectedKeys.has(k));
  const isSomePageSelected =
    allPageKeys.some((k) => activeSelectedKeys.has(k)) && !isAllPageSelected;

  const toggleSelectAll = () => {
    const next = new Set(activeSelectedKeys);
    if (isAllPageSelected) {
      allPageKeys.forEach((k) => next.delete(k));
    } else {
      allPageKeys.forEach((k) => next.add(k));
    }
    setActiveSelectedKeys(next);
  };

  const toggleSelectRow = (key: string) => {
    const next = new Set(activeSelectedKeys);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setActiveSelectedKeys(next);
  };

  // Selected items array for bulk actions
  const selectedItems = useMemo(() => {
    return data.filter((item) => activeSelectedKeys.has(keyExtractor(item)));
  }, [data, activeSelectedKeys, keyExtractor]);

  // Export functionality
  const handleExport = (format: "csv" | "json") => {
    const itemsToExport =
      selectedItems.length > 0 ? selectedItems : processedData;
    if (itemsToExport.length === 0) return;

    if (format === "json") {
      const dataStr =
        "data:text/json;charset=utf-8," +
        encodeURIComponent(JSON.stringify(itemsToExport, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `${exportFileName}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } else {
      // CSV format
      const exportCols = visibleColumns.filter(
        (c) => c.accessorKey || c.accessorFn,
      );
      const headers = exportCols.map((c) =>
        typeof c.header === "string" ? c.header : c.id,
      );
      const csvRows = [headers.join(",")];

      itemsToExport.forEach((item) => {
        const row = exportCols.map((col) => {
          let val = col.accessorFn
            ? col.accessorFn(item)
            : col.accessorKey
              ? item[col.accessorKey]
              : "";
          if (val === null || val === undefined) val = "";
          const str = String(val).replace(/"/g, '""');
          return `"${str}"`;
        });
        csvRows.push(row.join(","));
      });

      const blob = new Blob([csvRows.join("\n")], {
        type: "text/csv;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `${exportFileName}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  };

  // Density styles
  const densityStyles = {
    compact: "py-1.5 px-3 text-xs",
    normal: "py-2.5 px-4 text-xs",
    spacious: "py-3.5 px-5 text-sm",
  }[density];

  return (
    <div
      className={`rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden ${className}`}
    >
      {/* Top Toolbar */}
      <DataGridToolbar
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        searchPlaceholder={searchPlaceholder}
        customFilterSlot={customFilterSlot}
        columns={columns}
        hiddenColumns={hiddenColumns}
        onToggleColumnVisibility={toggleColumnVisibility}
        density={density}
        onDensityChange={setDensity}
        onExport={handleExport}
        enableExport={enableExport}
        enableDensityToggle={enableDensityToggle}
        enableColumnVisibility={enableColumnVisibility}
        totalRecords={totalRecords}
      />

      {/* Bulk Actions Banner */}
      {selectable && (
        <DataGridBulkActions
          selectedCount={activeSelectedKeys.size}
          selectedItems={selectedItems}
          actions={bulkActions}
          onClearSelection={() => setActiveSelectedKeys(new Set())}
        />
      )}

      {/* Main Table Content */}
      {loading ? (
        <div className="p-4">
          <TableSkeleton
            rows={pageSize > 10 ? 10 : pageSize}
            cols={visibleColumns.length + (selectable ? 1 : 0)}
          />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <AlertTriangle className="h-10 w-10 text-rose-500 mb-3" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Failed to load data
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1">{error}</p>
          {onRetry && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              className="mt-4"
            >
              Retry Query
            </Button>
          )}
        </div>
      ) : paginatedData.length === 0 ? (
        emptyState ? (
          <div className="p-8">{emptyState}</div>
        ) : (
          <div className="p-8">
            <EmptyState
              title={emptyMessage || emptyTitle}
              description={emptyDescription}
              actionLabel={emptyActionLabel}
              onAction={onEmptyAction}
            />
          </div>
        )
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  {selectable && (
                    <th className="w-10 px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={isAllPageSelected}
                        ref={(el) => {
                          if (el) el.indeterminate = isSomePageSelected;
                        }}
                        onChange={toggleSelectAll}
                        className="rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                        aria-label="Select all rows on current page"
                      />
                    </th>
                  )}

                  {visibleColumns.map((col) => {
                    const isSorted = sortState?.key === col.id;
                    const canSort =
                      col.sortable !== false &&
                      (col.accessorKey || col.accessorFn);

                    return (
                      <th
                        key={col.id}
                        style={{ width: col.width }}
                        className={`px-4 py-3 select-none ${col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"}`}
                      >
                        {canSort ? (
                          <button
                            onClick={() => handleSort(col.id)}
                            className="inline-flex items-center gap-1.5 hover:text-slate-900 dark:hover:text-white transition group focus:outline-hidden"
                          >
                            <span>{col.header}</span>
                            {isSorted ? (
                              sortState?.direction === "asc" ? (
                                <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                              ) : (
                                <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                              )
                            ) : (
                              <ArrowUpDown className="h-3 w-3 text-slate-300 dark:text-slate-600 group-hover:text-slate-500 transition" />
                            )}
                          </button>
                        ) : (
                          <span>{col.header}</span>
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900">
                {paginatedData.map((item, index) => {
                  const key = keyExtractor(item);
                  const isSelected = activeSelectedKeys.has(key);

                  return (
                    <tr
                      key={key}
                      className={`transition-colors duration-150 ${
                        isSelected
                          ? "bg-indigo-50/40 dark:bg-indigo-950/20"
                          : "hover:bg-slate-50/70 dark:hover:bg-slate-800/40"
                      }`}
                    >
                      {selectable && (
                        <td className="px-3 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelectRow(key)}
                            className="rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                            aria-label={`Select row ${key}`}
                          />
                        </td>
                      )}

                      {visibleColumns.map((col) => {
                        let content: React.ReactNode;
                        if (col.cell) {
                          const cellContext = Object.assign(
                            Object.create(item as any),
                            { row: item },
                          );
                          content = col.cell(cellContext, index);
                        } else if (col.accessorFn) {
                          content = String(col.accessorFn(item) ?? "");
                        } else if (col.accessorKey) {
                          content = String(item[col.accessorKey] ?? "");
                        }

                        return (
                          <td
                            key={col.id}
                            className={`${densityStyles} ${
                              col.align === "right"
                                ? "text-right"
                                : col.align === "center"
                                  ? "text-center"
                                  : "text-left"
                            }`}
                          >
                            {content}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Optional Mobile Cards View for smaller screens if mobileCardRender is provided */}
          {mobileCardRender && (
            <div className="block md:hidden divide-y divide-slate-100 dark:divide-slate-800 p-3 space-y-3">
              {paginatedData.map((item) => {
                const key = keyExtractor(item);
                const isSelected = activeSelectedKeys.has(key);
                return (
                  <div key={key} className="pt-2">
                    {mobileCardRender(item, isSelected, () =>
                      toggleSelectRow(key),
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Pagination Footer */}
      {paginated && totalRecords > 0 && !loading && !error && (
        <DataGridPagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalRecords={totalRecords}
          pageSize={pageSize}
          pageSizeOptions={pageSizeOptions}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      )}
    </div>
  );
}
