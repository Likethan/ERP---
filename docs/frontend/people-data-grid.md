# CampusOS — Enterprise DataGrid Architecture & Component Specification

## 1. Overview

The `DataGrid` component suite (`components/data-grid/`) provides a reusable, high-density, accessible enterprise data grid for CampusOS. Built without bloated external runtime dependencies, it integrates directly with TailwindCSS, Lucide icons, and the CampusOS design system.

---

## 2. Component Structure

```
components/data-grid/
├── index.ts                   # Public exports
├── data-grid.types.ts         # Types, ColumnDef, BulkAction, SortState, DataGridProps
├── data-grid.tsx              # Main DataGrid container, table renderer & lifecycle
├── data-grid-toolbar.tsx      # Search bar, filter slot, column picker, density & export
├── data-grid-pagination.tsx   # Enterprise page size selector, pager, and record counter
└── data-grid-bulk-actions.tsx # Floating bulk action toolbar for selected rows
```

---

## 3. Column Definition API (`ColumnDef<T>`)

```typescript
export interface ColumnDef<T> {
  id: string;                                          // Unique identifier
  header: string | React.ReactNode;                    // Header text or JSX
  accessorKey?: keyof T;                              // Object property key
  accessorFn?: (item: T) => string | number | boolean; // Computed accessor
  cell?: (item: T, index: number) => React.ReactNode;  // Custom cell renderer
  sortable?: boolean;                                 // Enables column sorting
  enableHiding?: boolean;                             // Controls column visibility toggle
  defaultHidden?: boolean;                            // Initially hidden
  width?: string;                                     // Column width class
  align?: "left" | "center" | "right";                // Text alignment
}
```

---

## 4. Key Capabilities & Usage

### 4.1 Sorting
- Supports single-column directional sorting (`asc` / `desc`).
- In uncontrolled mode, sorting operates client-side using `accessorFn` or `accessorKey`.
- In controlled mode, integrates with service layer query params (`sortBy`, `sortDirection`).

### 4.2 Multi-Facet Filtering
- Integrated search bar with debounced input and clear (`X`) button.
- `customFilterSlot` prop allows injecting domain-specific filter dropdowns (e.g. Department, Shift, Status, Program).

### 4.3 Row Selection & Bulk Actions
- `selectable={true}` adds a master checkbox in the header and individual row checkboxes.
- `selectedKeys` and `onSelectionChange` support controlled row tracking.
- Floating `DataGridBulkActions` bar displays selection count and triggers actions (e.g., "Batch Status Transition", "Export Selected").

### 4.4 Column Visibility
- Built-in popover menu allowing users to toggle column display.
- Persists user preferences and hides optional metadata on narrower screens.

### 4.5 Row Density Control
- Supports three row densities:
  - `compact`: `py-2` (high-density operational rosters)
  - `normal`: `py-3` (default enterprise view)
  - `spacious`: `py-4` (touch-friendly views)

### 4.6 Export Engine
- Native CSV and JSON export without external dependencies.
- Generates downloadable files using blob URLs and sanitized cell values.

### 4.7 States (Empty, Loading, Error)
- **Loading**: Renders animated `TableSkeleton` rows.
- **Empty**: Context-aware `EmptyState` component with configurable icon, title, description, and action button.
- **Error**: Error banner with `AlertTriangle` and "Retry Query" callback.

### 4.8 Mobile Responsive Fallback
- `mobileCardRender`: Custom card renderer for viewports below `md` breakpoint.
- Automatically hides non-essential columns on mobile while preserving row selection.

---

## 5. Implementation Example

```tsx
<DataGrid
  data={students}
  columns={columns}
  keyExtractor={(s) => s.id}
  loading={loading}
  selectable
  selectedKeys={selectedKeys}
  onSelectionChange={setSelectedKeys}
  bulkActions={[
    {
      label: "Update Status",
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      onClick: () => setBulkModalOpen(true),
    },
  ]}
  currentPage={currentPage}
  pageSize={pageSize}
  totalRecords={totalRecords}
  onPageChange={setCurrentPage}
  onPageSizeChange={setPageSize}
  onSearchChange={setSearch}
  customFilterSlot={filterDropdowns}
  exportFileName="campusos-students"
/>
```
