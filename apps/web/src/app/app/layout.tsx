"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Sidebar, isPathAuthorized } from "@/components/navigation/sidebar";
import { Topbar } from "@/components/navigation/topbar";
import { ToastProvider } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <svg
            className="h-8 w-8 animate-spin text-yellow-500"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span className="text-sm font-medium">
            Resolving CampusOS Institutional Workspace...
          </span>
        </div>
      </div>
    );
  }

  const isAuthorized = isPathAuthorized(pathname, user);

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-background text-foreground antialiased font-sans">
        {/* Navigation Sidebar */}
        <Sidebar
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-yellow-50/25">
          {/* Global Topbar */}
          <Topbar
            onToggleSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          />

          {/* Page Content Shell */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-fade-in">
            {!isAuthorized ? (
              <div
                role="alert"
                aria-live="assertive"
                className="rounded-xl border border-amber-200 bg-amber-50/80 p-8 sm:p-12 text-center max-w-xl mx-auto my-12 shadow-sm"
              >
                <div className="mx-auto w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 mb-4 border border-amber-300">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-200 text-amber-900 mb-2">
                  Institutional Security Boundary
                </div>
                <h2 className="text-xl font-bold text-slate-900">
                  Access Restricted
                </h2>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                  Your current portal role (
                  <span className="font-semibold text-slate-900">
                    {user?.roles?.[0]?.display_name ||
                      user?.roles?.[0]?.name ||
                      "Authenticated User"}
                  </span>
                  ) is not authorized to view this module (
                  <code className="text-xs bg-amber-100/90 text-amber-950 px-1.5 py-0.5 rounded font-mono">
                    {pathname}
                  </code>
                  ). Direct navigation to unauthorized routes is blocked in
                  accordance with CampusOS role-based access governance.
                </p>
                <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
                  <Link href="/app/dashboard">
                    <Button
                      variant="primary"
                      className="bg-yellow-400 text-slate-950 hover:bg-yellow-500 font-bold shadow-xs border border-yellow-500 gap-2"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Return to Dashboard
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              children
            )}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
