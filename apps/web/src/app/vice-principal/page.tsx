"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function VicePrincipalPortalEntryPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (user) {
      router.push("/vice-principal/dashboard");
    } else {
      router.push("/login?role=vice_principal");
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAF8F2]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-7 w-7 animate-spin rounded-full border-2 border-slate-300 border-t-amber-500" />
        <span className="text-xs font-semibold text-slate-500">
          Redirecting to CampusOS Vice Principal Workspace...
        </span>
      </div>
    </div>
  );
}
