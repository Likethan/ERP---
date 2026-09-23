# CampusOS — Design System & UX Philosophy

CampusOS is an enterprise productivity platform designed for daily institutional use by thousands of students, faculty, and administrators. Its visual design must communicate **clarity, precision, institutional authority, and effortless efficiency**.

---

## 1. Aesthetic Foundations

> [!NOTE]
> **Enterprise SaaS, Not Marketing Demos**:
>
> - **NO** excessive glassmorphism or distracting decorative blurs.
> - **NO** rainbow gradients or neon gamification.
> - **NO** low-contrast micro-fonts or hidden scrollbars.
> - **YES** to crisp typography, structured grids, high information density, clear contrast, and instant visual hierarchy.

### 1.1 Color System

The color palette uses tailored institutional hues:

- **Base Neutrals**: Slate / Zinc tones (`slate-50` to `slate-950`) providing crisp surface backgrounds and high-contrast typography.
- **Institutional Primary**: Deep Academic Navy (`#0f172a` to `#1e293b`) with Indigo/Cobalt accents (`#3b82f6` / `#2563eb`).
- **Semantic Feedback**:
  - Success: Emerald (`#10b981`)
  - Warning/Pending: Amber (`#f59e0b`)
  - Destructive/Critical: Rose / Red (`#ef4444`)
  - Information: Sky (`#0ea5e9`)

### 1.2 Typography Hierarchy

- Font Family: Inter / System UI sans-serif.
- `Page Title`: `text-2xl font-bold tracking-tight text-slate-900`
- `Section Header`: `text-lg font-semibold text-slate-800`
- `Body / Data`: `text-sm text-slate-700`
- `Metadata / Captions`: `text-xs text-slate-500 font-medium`
- `Table Cells`: `text-sm font-normal tabular-nums`

---

## 2. Role-Driven Dashboard Philosophy

A core tenet of CampusOS UX is that **dashboards are tailored to persona workflows**, avoiding generic catch-all dashboards.

### 2.1 Principal & Executive Management

- Institutional KPIs: live campus attendance %, faculty on duty, active placement drives, fee collection velocity vs target.
- Quick statutory reports and institutional circular broadcasting.

### 2.2 Faculty Dashboard

- Today's teaching schedule: next class in X minutes with 1-click attendance entry.
- Pending internal assessment grading queue.
- Student leave requests awaiting approval.

### 2.3 Student Dashboard

- Real-time aggregate attendance % with warning badge if below 75%.
- Today's lecture schedule and room numbers.
- Upcoming fee installments and deadlines.
- Eligible active placement drives and application status.

---

## 3. Component Architecture

All UI components are organized into standard tiers:

1. **Primitives (`components/ui/`)**: Buttons, Inputs, Dropdowns, Dialogs, Badges, Tabs, Tables, Tooltips.
2. **Layout Shells (`components/layout/`)**: Top Navigation, Sidebar, Role Switcher, Breadcrumbs, Page Header.
3. **Feedback States**: Empty states with clear next actions, skeleton loaders matching exact table/card shapes, and actionable error banners with error reference codes.
