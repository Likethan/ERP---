"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import type { NotificationPreference } from "@campusos/types";

const CATEGORY_DESCRIPTIONS: Record<string, string> = {
  ACADEMIC:
    "Curriculum updates, grade card publications, and semester registration deadlines.",
  ATTENDANCE:
    "Attendance shortfall warnings, daily session records, and leave approvals.",
  FINANCE:
    "Fee invoice notifications, payment confirmation receipts, and dues reminders.",
  PLACEMENT:
    "Placement drive announcements, interview schedules, and offer letters.",
  EVENTS:
    "Collegiate symposiums, hackathon invitations, and registration confirmations.",
  CLUBS:
    "Society membership decisions, club event bulletins, and committee circulars.",
  ANNOUNCEMENTS:
    "Official campus circulars, holiday notices, and general broadcasts.",
  SECURITY:
    "Account sign-in security alerts, password resets, and critical statutory warnings (Mandatory).",
};

export default function NotificationPreferencesPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);

  useEffect(() => {
    async function loadPreferences() {
      try {
        setLoading(true);
        setError(null);
        const res = await apiFetch<NotificationPreference[]>(
          "/api/v1/notifications/preferences",
        );
        setPreferences(res.data || []);
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Failed to load preferences.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadPreferences();
  }, []);

  const handleToggle = (category: string, channel: string) => {
    setPreferences((prev) =>
      prev.map((p) => {
        if (p.category === category && p.channel === channel) {
          if (p.is_mandatory) return p; // Cannot toggle mandatory
          return { ...p, is_enabled: !p.is_enabled };
        }
        return p;
      }),
    );
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      await apiFetch("/api/v1/notifications/preferences", {
        method: "POST",
        body: JSON.stringify({
          preferences: preferences.map((p) => ({
            category: p.category,
            channel: p.channel,
            is_enabled: p.is_enabled,
          })),
        }),
      });

      setSuccess("Your notification channel preferences have been updated.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to save preferences.",
      );
    } finally {
      setSaving(false);
    }
  };

  const categories = Array.from(new Set(preferences.map((p) => p.category)));

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <Link
            href="/app/notifications"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors mb-2"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"
              />
            </svg>
            Back to Notification Center
          </Link>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Notification Channel Preferences
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Customize which institutional communication categories you receive
            across in-app and email channels.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving || loading}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-sm transition-colors disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/60 text-xs text-emerald-300">
          {success}
        </div>
      )}

      {loading ? (
        <div className="py-20 text-center text-slate-500 text-sm">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
          <p>Loading user preferences matrix...</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden divide-y divide-slate-800">
          {/* Header Row */}
          <div className="grid grid-cols-12 gap-4 p-4 bg-slate-950 text-xs font-semibold text-slate-400">
            <div className="col-span-8">Category & Purpose</div>
            <div className="col-span-2 text-center">In-App Center</div>
            <div className="col-span-2 text-center">Email Dispatch</div>
          </div>

          {/* Category Rows */}
          {categories.map((cat) => {
            const inAppPref = preferences.find(
              (p) => p.category === cat && p.channel === "IN_APP",
            );
            const emailPref = preferences.find(
              (p) => p.category === cat && p.channel === "EMAIL",
            );
            const isMandatory =
              inAppPref?.is_mandatory || emailPref?.is_mandatory;

            return (
              <div
                key={cat}
                className="grid grid-cols-12 gap-4 p-4 items-center hover:bg-slate-900/80 transition-colors"
              >
                <div className="col-span-8 space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">
                      {cat}
                    </span>
                    {isMandatory && (
                      <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-950/70 border border-amber-800/60 px-1.5 py-0.2 rounded">
                        Mandatory
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">
                    {CATEGORY_DESCRIPTIONS[cat] ||
                      "Collegiate updates and communications."}
                  </p>
                </div>

                {/* In-App Toggle */}
                <div className="col-span-2 flex justify-center">
                  <button
                    type="button"
                    disabled={inAppPref?.is_mandatory}
                    onClick={() => handleToggle(cat, "IN_APP")}
                    className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      inAppPref?.is_enabled ? "bg-indigo-600" : "bg-slate-800"
                    } ${inAppPref?.is_mandatory ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        inAppPref?.is_enabled
                          ? "translate-x-4"
                          : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* Email Toggle */}
                <div className="col-span-2 flex justify-center">
                  <button
                    type="button"
                    disabled={emailPref?.is_mandatory}
                    onClick={() => handleToggle(cat, "EMAIL")}
                    className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      emailPref?.is_enabled ? "bg-indigo-600" : "bg-slate-800"
                    } ${emailPref?.is_mandatory ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        emailPref?.is_enabled
                          ? "translate-x-4"
                          : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
