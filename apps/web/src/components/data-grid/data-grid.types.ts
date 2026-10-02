import React from "react";

export type SortDirection = "asc" | "desc";

export interface SortState {
  key: string;
  direction: SortDirection;
}

export type RowDensity = "compact" | "normal" | "spacious";

export interface ColumnDef<T> {
  id: string;
  header: string | React.ReactNode;
  accessorKey?: keyof T;
  cell?: (item: T & { row: T; index?: number }, index?: number) => React.ReactNode;
  sortable?: boolean;
  enableHiding?: boolean;
  defaultHidden?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
  /** Custom accessor function for sorting/filtering */
  accessorFn?: (item: T) => string | number | boolean | null | undefined;
}

export interface BulkAction<T> {
  label: string;
  icon?: React.ReactNode;
  variant?: "primary" | "secondary" | "destructive" | "outline";
  onClick: (selectedItems: T[]) => void | Promise<void>;
}

export interface DataGridProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  keyExtractor: (item: T) => string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  // Selection
  selectable?: boolean;
  selectedKeys?: Set<string>;
  onSelectionChange?: (selectedKeys: Set<string>) => void;
  bulkActions?: BulkAction<T>[];
  // Pagination
  paginated?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  currentPage?: number;
  totalRecords?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  // Toolbar features
  searchPlaceholder?: string;
  onSearchChange?: (query: string) => void;
  customFilterSlot?: React.ReactNode;
  exportFileName?: string;
  enableExport?: boolean;
  enableDensityToggle?: boolean;
  enableColumnVisibility?: boolean;
  // Empty & States
  emptyTitle?: string;
  emptyDescription?: string;
  emptyMessage?: string;
  emptyState?: React.ReactNode;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  // Layout
  className?: string;
  mobileCardRender?: (item: T, isSelected: boolean, onToggle: () => void) => React.ReactNode;
}
