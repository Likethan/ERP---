"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function AdminPortalPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.push("/login?role=admin");
      return;
    }
    const roleNames = user.roles?.map((r) => r.name) || [];
    const isAdmin =
      roleNames.includes("SUPER_ADMIN") ||
      roleNames.includes("ADMIN") ||
      roleNames.includes("INSTITUTION_ADMIN") ||
      user.permissions?.includes("*");

    if (isAdmin) {
      router.push("/app/dashboard");
    } else {
      router.push("/login?role=admin");
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAF8F2]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-7 w-7 animate-spin rounded-full border-2 border-slate-300 border-t-amber-500" />
        <span className="text-xs font-semibold text-slate-500">
          Redirecting to CampusOS Administrator Workspace...
        </span>
      </div>
    </div>
  );
}
