"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";

export default function EventDetailRedirect({ params }: { params: Promise<{ id: string }> }) {
  const resolved = use(params);
  const router = useRouter();
  useEffect(() => {
    router.replace(`/app/campus/events/${resolved.id}`);
  }, [router, resolved.id]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center text-xs text-slate-500">
      Redirecting to Event Specification...
    </div>
  );
}
