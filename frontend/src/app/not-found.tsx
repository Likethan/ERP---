import Link from "next/link";
import { FileQuestion, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="max-w-md w-full rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-600">
          <FileQuestion className="h-6 w-6" />
        </div>
        <h1 className="text-xl font-semibold text-slate-900">Page Not Found</h1>
        <p className="mt-2 text-sm text-slate-500">
          The CampusOS resource you requested could not be found or has moved.
        </p>
        <div className="mt-6">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            <ArrowLeft className="h-4 w-4" />
            Return to Portal
          </Link>
        </div>
      </div>
    </div>
  );
}
