"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

export interface ToastProps {
  title: string;
  description?: string;
  message?: string;
  variant?: "default" | "destructive" | "error" | "success" | "warning" | "info" | string;
  type?: ToastType;
  duration?: number;
}

interface ToastContextValue {
  showToast: (toast: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
  toast: (props: ToastProps) => void;
  addToast: (props: ToastProps) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<ToastItem, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, type, title, message, duration }]);
      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const toast = useCallback(
    ({ title, description, message, variant, type, duration = 4000 }: ToastProps) => {
      let mappedType: ToastType = "info";
      if (variant === "destructive" || variant === "error" || type === "error") mappedType = "error";
      else if (variant === "success" || type === "success") mappedType = "success";
      else if (variant === "warning" || type === "warning") mappedType = "warning";

      showToast({
        title,
        message: description || message,
        type: mappedType,
        duration,
      });
    },
    [showToast]
  );

  return (
    <ToastContext.Provider value={{ showToast, removeToast, toast, addToast: toast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => {
          const icons = {
            success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />,
            error: <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />,
            warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />,
            info: <Info className="h-5 w-5 text-sky-400 shrink-0" />,
          };

          const borders = {
            success: "border-emerald-800/80 bg-slate-900/95 shadow-emerald-950/20",
            error: "border-red-800/80 bg-slate-900/95 shadow-red-950/20",
            warning: "border-amber-800/80 bg-slate-900/95 shadow-amber-950/20",
            info: "border-sky-800/80 bg-slate-900/95 shadow-sky-950/20",
          };

          return (
            <div
              key={toast.id}
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-xl border p-4 shadow-xl backdrop-blur-md animate-slide-up transition-all",
                borders[toast.type]
              )}
            >
              {icons[toast.type]}
              <div className="flex-1">
                <div className="text-sm font-semibold text-white tracking-tight">
                  {toast.title}
                </div>
                {toast.message && (
                  <div className="mt-0.5 text-xs text-slate-300 leading-relaxed">
                    {toast.message}
                  </div>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-white p-0.5 rounded transition-colors"
                aria-label="Dismiss toast"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
