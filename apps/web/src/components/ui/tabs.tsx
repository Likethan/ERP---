"use client";

import React, { createContext, useContext, useState } from "react";
import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  count?: number | string;
  icon?: React.ReactNode;
}

export interface LegacyTabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export interface CompoundTabsProps {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}

export type TabsProps =
  LegacyTabsProps | (CompoundTabsProps & { tabs?: never });

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

export function Tabs(props: TabsProps) {
  const defaultValue = "defaultValue" in props ? props.defaultValue : "";
  const [internalValue, setInternalValue] = useState(defaultValue || "");

  // If legacy props provided
  if ("tabs" in props && Array.isArray(props.tabs)) {
    const { tabs, activeTab, onChange, className } = props as LegacyTabsProps;
    return (
      <div
        className={cn(
          "flex items-center gap-1 border-b border-slate-800 overflow-x-auto no-scrollbar",
          className,
        )}
        role="tablist"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              className={cn(
                "group inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition-colors cursor-pointer",
                isActive
                  ? "border-indigo-500 text-white font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700",
              )}
            >
              {tab.icon && (
                <span
                  className={cn(
                    "transition-colors",
                    isActive
                      ? "text-indigo-400"
                      : "text-slate-500 group-hover:text-slate-400",
                  )}
                >
                  {tab.icon}
                </span>
              )}
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={cn(
                    "ml-1 rounded-full px-2 py-0.5 text-[10px] font-mono",
                    isActive
                      ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700/60",
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  // Compound component mode
  const { value, onValueChange, className, children } =
    props as CompoundTabsProps;

  const activeTab = value !== undefined ? value : internalValue;
  const setActiveTab = (newVal: string) => {
    if (value === undefined) setInternalValue(newVal);
    onValueChange?.(newVal);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex items-center justify-start rounded-xl p-1 text-slate-400",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({
  value,
  children,
  className,
}: {
  value: string;
  children: React.ReactNode;
  className?: string;
}) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("TabsTrigger must be used inside Tabs");

  const isActive = ctx.activeTab === value;

  return (
    <button
      role="tab"
      type="button"
      aria-selected={isActive}
      data-state={isActive ? "active" : "inactive"}
      onClick={() => ctx.setActiveTab(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
        isActive
          ? "bg-slate-800 text-white shadow-xs font-semibold"
          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({
  value,
  children,
  className,
}: {
  value: string;
  children: React.ReactNode;
  className?: string;
}) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("TabsContent must be used inside Tabs");

  if (ctx.activeTab !== value) return null;

  return (
    <div
      role="tabpanel"
      data-state="active"
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none",
        className,
      )}
    >
      {children}
    </div>
  );
}
