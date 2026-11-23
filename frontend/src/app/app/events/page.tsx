"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function EventsRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/app/campus/events");
  }, [router]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center text-xs text-slate-500">
      Redirecting to Campus Events Hub...
    </div>
  );
}
