"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import { SupportPolicyConfigItem } from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Settings,
  ShieldCheck,
  CheckCircle2,
  Lock,
  Save,
  Users,
  Calendar,
  AlertCircle,
} from "lucide-react";

export default function StudentSupportConfigPage() {
  const [config, setConfig] = useState<SupportPolicyConfigItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Form State
  const [maxMentees, setMaxMentees] = useState(20);
  const [maxAdvanceDays, setMaxAdvanceDays] = useState(30);
  const [minCancelHours, setMinCancelHours] = useState(4);
  const [requireConsent, setRequireConsent] = useState(true);
  const [suppressionThreshold, setSuppressionThreshold] = useState(5);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    setLoading(true);
    try {
      const data = await StudentSupportService.getPolicyConfig();
      setConfig(data);
      setMaxMentees(data.max_mentees_per_mentor ?? data.maxMenteesPerMentor ?? 20);
      setMaxAdvanceDays(data.advance_booking_window_days ?? data.appointmentAdvanceBookingDays ?? 30);
      setMinCancelHours(data.cancellation_lead_hours ?? data.appointmentCancellationLeadHours ?? 4);
      setRequireConsent(data.require_referral_consent ?? data.requireStudentConsentForReferral ?? true);
      setSuppressionThreshold(data.privacy_suppression_threshold ?? 5);
    } catch (err) {
      console.error("Failed to load policy config:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await StudentSupportService.updatePolicyConfig({
        max_mentees_per_mentor: Number(maxMentees),
        advance_booking_window_days: Number(maxAdvanceDays),
        cancellation_lead_hours: Number(minCancelHours),
        require_referral_consent: Boolean(requireConsent),
        privacy_suppression_threshold: Number(suppressionThreshold),
      });
      setConfig(updated);
      setNotification("Institutional student support configuration saved successfully.");
    } catch (err) {
      console.error("Failed to save config:", err);
      alert("Error updating configuration.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Configuration", href: "/app/student-support/config" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Settings className="h-6 w-6 text-indigo-400" />
              Student Support Policies & Capacity Configuration
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Configure faculty mentoring workload caps, appointment booking rules, privacy thresholds, and RBAC policies.
            </p>
          </div>
        </div>
      </div>

      <StudentSupportNav />

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Form (Left 2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-6 space-y-5">
            <form onSubmit={handleSaveConfig} className="space-y-5 text-xs">
              <div>
                <h2 className="text-sm font-semibold text-white mb-1">Mentoring Workload Rules</h2>
                <p className="text-slate-400">Institutional ceilings to prevent faculty overburdening</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Maximum Mentees per Faculty Mentor</label>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    value={maxMentees}
                    onChange={(e) => setMaxMentees(Number(e.target.value))}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                  <p className="text-[11px] text-slate-500">
                    System prevents manual or automated allocation beyond this cap.
                  </p>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Default IDP Review Cadence</label>
                  <select
                    disabled
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-400"
                  >
                    <option>Every Semester (Standard)</option>
                  </select>
                  <p className="text-[11px] text-slate-500">
                    Governed by institutional curriculum cycle.
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <h2 className="text-sm font-semibold text-white mb-1">Counselling Booking & Lead Times</h2>
                <p className="text-slate-400">Rules governing student appointment scheduling</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Advance Booking Window (Days)</label>
                  <Input
                    type="number"
                    min={1}
                    max={90}
                    value={maxAdvanceDays}
                    onChange={(e) => setMaxAdvanceDays(Number(e.target.value))}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                  <p className="text-[11px] text-slate-500">
                    Maximum days in advance a student can reserve a counselling slot.
                  </p>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Minimum Cancellation Lead Time (Hours)</label>
                  <Input
                    type="number"
                    min={0}
                    max={48}
                    value={minCancelHours}
                    onChange={(e) => setMinCancelHours(Number(e.target.value))}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                  <p className="text-[11px] text-slate-500">
                    Notice required to cancel or reschedule without marking late-drop.
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <h2 className="text-sm font-semibold text-white mb-1">Consent & Differential Privacy</h2>
                <p className="text-slate-400">Privacy boundaries and data protection enforcement</p>
              </div>

              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireConsent}
                    onChange={(e) => setRequireConsent(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="text-slate-200">
                    Enforce explicit student consent verification before dispatching inter-service referrals
                  </span>
                </label>

                <div className="space-y-1 max-w-xs">
                  <label className="text-slate-400 font-medium">Small-Group Suppression Threshold</label>
                  <Input
                    type="number"
                    min={3}
                    max={20}
                    value={suppressionThreshold}
                    onChange={(e) => setSuppressionThreshold(Number(e.target.value))}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                  <p className="text-[11px] text-slate-500">
                    Cohorts below this count are suppressed from institutional telemetry.
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
                >
                  <Save className="mr-1.5 h-3.5 w-3.5" />
                  {saving ? "Saving Policy..." : "Save Configuration"}
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* RBAC Matrix Card (Right 1 Column) */}
        <div className="space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              Role Permissions & Confidentiality Matrix
            </h2>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <div className="font-semibold text-white">Student</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  View assigned mentor, request meetings, view & update own IDP goals, book counselling, submit session reflections.
                </div>
              </div>

              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <div className="font-semibold text-white">Faculty Mentor</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  View mentee directory, schedule mentoring sessions, review IDP progress, record action items, initiate referrals.
                </div>
              </div>

              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <div className="font-semibold text-white">HOD / Department Chair</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Oversee department mentor allocations, reassign mentors, view aggregate cohort completion rates.
                </div>
              </div>

              <div className="p-2.5 rounded bg-amber-950/30 border border-amber-900/40">
                <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5" />
                  Licensed Clinical Counsellor
                </div>
                <div className="text-[11px] text-slate-300 mt-0.5">
                  Exclusive access to <code className="text-amber-400 font-mono">COUNSELLING_CONFIDENTIAL_READ/WRITE</code>. Confidential clinical notes are strictly walled off from mentors, HODs, and administrators.
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
