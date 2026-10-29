"use client";

import React, { useState } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import {
  Settings,
  Shield,
  Save,
  CheckCircle2,
  Clock,
  GraduationCap,
  Bell,
  Scale,
} from "lucide-react";

export default function SportsConfigPage() {
  const [config, setConfig] = useState({
    min_cgpa_eligibility: 6.0,
    min_attendance_percentage: 75,
    medical_clearance_validity_days: 365,
    require_guardian_consent_minors: true,
    facility_booking_buffer_minutes: 15,
    max_advance_booking_days: 14,
    default_win_points: 3,
    default_draw_points: 1,
    default_loss_points: 0,
    enable_nightly_clearance_sweep: true,
    prevent_simultaneous_team_rosters: true,
    operational_hours_start: "06:00",
    operational_hours_end: "21:00",
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3500);
  };

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Sports Governance & Athletic Policies
          </h1>
          <p className="text-sm text-slate-500">
            Configure institutional eligibility rules, facility operating parameters, and tournament point systems.
          </p>
        </div>
        <button
          onClick={handleSubmit}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Institutional Policies
        </button>
      </div>

      {savedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-emerald-800 text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          Institutional sports policies successfully updated and synchronized across all campus modules.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Academic & Athletic Eligibility */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <GraduationCap className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">Academic & Medical Eligibility Thresholds</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Minimum CGPA for Varsity Representation
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={config.min_cgpa_eligibility}
                onChange={(e) => setConfig({ ...config, min_cgpa_eligibility: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Athletes below this mark will trigger an academic hold.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Minimum Academic Class Attendance (%)
              </label>
              <input
                type="number"
                min="50"
                max="100"
                value={config.min_attendance_percentage}
                onChange={(e) => setConfig({ ...config, min_attendance_percentage: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Synchronized with the campus attendance ledger.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Medical Clearance Validity (Days)
              </label>
              <input
                type="number"
                min="30"
                max="730"
                value={config.medical_clearance_validity_days}
                onChange={(e) =>
                  setConfig({ ...config, medical_clearance_validity_days: Number(e.target.value) })
                }
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Default 365 days (1 academic year cycle).
              </p>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.require_guardian_consent_minors}
                onChange={(e) =>
                  setConfig({ ...config, require_guardian_consent_minors: e.target.checked })
                }
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">
                Mandate verified guardian consent for student athletes under 18 years of age
              </span>
            </label>
          </div>
        </div>

        {/* Facility Scheduling & Conflict Rules */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Clock className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">Facility Operations & Booking Rules</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Facility Opening Time</label>
              <input
                type="time"
                value={config.operational_hours_start}
                onChange={(e) => setConfig({ ...config, operational_hours_start: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Facility Closing Time</label>
              <input
                type="time"
                value={config.operational_hours_end}
                onChange={(e) => setConfig({ ...config, operational_hours_end: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Slot Turnaround Buffer (Minutes)
              </label>
              <input
                type="number"
                min="0"
                max="60"
                value={config.facility_booking_buffer_minutes}
                onChange={(e) =>
                  setConfig({ ...config, facility_booking_buffer_minutes: Number(e.target.value) })
                }
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Max Advance Booking (Days)
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={config.max_advance_booking_days}
                onChange={(e) =>
                  setConfig({ ...config, max_advance_booking_days: Number(e.target.value) })
                }
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Tournament Scoring & Automation Sweeps */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Scale className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">Default League Scoring & System Automations</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default Points for Win</label>
              <input
                type="number"
                value={config.default_win_points}
                onChange={(e) => setConfig({ ...config, default_win_points: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default Points for Draw</label>
              <input
                type="number"
                value={config.default_draw_points}
                onChange={(e) => setConfig({ ...config, default_draw_points: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default Points for Loss</label>
              <input
                type="number"
                value={config.default_loss_points}
                onChange={(e) => setConfig({ ...config, default_loss_points: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.enable_nightly_clearance_sweep}
                onChange={(e) =>
                  setConfig({ ...config, enable_nightly_clearance_sweep: e.target.checked })
                }
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">
                Enable automated nightly background job to flag expiring medical clearances and send renewal notices
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.prevent_simultaneous_team_rosters}
                onChange={(e) =>
                  setConfig({ ...config, prevent_simultaneous_team_rosters: e.target.checked })
                }
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">
                Prevent athletes from being rostered simultaneously on conflicting varsity squads in the same sport
              </span>
            </label>
          </div>
        </div>
      </form>
    </div>
  );
}
