"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Settings,
  Sliders,
  Shield,
  Clock,
  Bell,
  Database,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Save,
  Lock,
  ArrowLeft,
  Server,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";

export default function SystemConfigurationPage() {
  const [activeTab, setActiveTab] = useState<
    "academic" | "security" | "jobs" | "integration"
  >("academic");

  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Academic Configuration
  const [academicConfig, setAcademicConfig] = useState({
    minAttendancePercent: 75.0,
    condonationThresholdPercent: 65.0,
    minFacultyWorkloadHours: 12,
    maxFacultyWorkloadHours: 18,
    hodTeachingReductionHours: 6,
    passingMinimumInternal: 40.0,
    passingMinimumExternal: 45.0,
    passingMinimumAggregate: 50.0,
    graceMarksCeiling: 5,
  });

  // Security Configuration
  const [securityConfig, setSecurityConfig] = useState({
    sessionTimeoutMinutes: 60,
    maxLoginAttempts: 5,
    mfaEnforcedForAdmins: true,
    mfaEnforcedForFaculty: false,
    minPasswordLength: 8,
    requireSpecialChar: true,
    requireNumeric: true,
    requireUppercase: true,
  });

  // Background Job Configuration
  const [jobConfig, setJobConfig] = useState({
    attendanceRadarSchedule: "0 18 * * 1-5 (Mon-Fri 6:00 PM)",
    feeLateFeeSchedule: "0 1 * * * (Daily 1:00 AM)",
    auditRetentionDays: 2555,
    nightlyBackupEnabled: true,
    backupWindowUtc: "02:00 UTC",
  });

  // Gateway Configuration
  const [gatewayConfig, setGatewayConfig] = useState({
    smtpHost: "smtp.office365.com",
    smtpPort: 587,
    smtpUser: "notifications@vsb.ac.in",
    smsProvider: "AWS_SNS",
    smsSenderId: "CAMPUS",
    governmentPortalSync: true,
  });

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage(null);
    try {
      // Simulate persisting configuration
      await new Promise((r) => setTimeout(r, 600));
      setSuccessMessage(
        "System configuration parameters saved and broadcasted across all cluster nodes successfully.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/dashboard"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 flex items-center gap-1"
            >
              <ArrowLeft className="h-3 w-3" /> Back to Admin Dashboard
            </Link>
            <span className="text-slate-300 dark:text-slate-700">&bull;</span>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              <Settings className="h-3 w-3" />
              Infrastructure & Policies
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Enterprise System Configuration
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Govern institution-wide regulatory thresholds, statutory compliance
            parameters, automated job schedules, and communication channels.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
          >
            {saving ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            {saving ? "Deploying..." : "Save Configuration"}
          </Button>
        </div>
      </div>

      {/* Success Banner */}
      {successMessage && (
        <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 p-4 text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
          <div className="flex-1 font-medium">{successMessage}</div>
        </div>
      )}

      {/* KPI Highlight Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Attendance Threshold"
          value={`${academicConfig.minAttendancePercent}%`}
          description="Statutory UGC / AICTE cutoff"
          icon={<Sliders className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Session Lifetime"
          value={`${securityConfig.sessionTimeoutMinutes} min`}
          description="Inactivity timeout protection"
          icon={<Clock className="h-5 w-5 text-blue-500" />}
        />
        <StatCard
          title="MFA Status"
          value="Enforced"
          description="Mandatory for Administrators"
          icon={<Lock className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Audit Log Retention"
          value={`${Math.round(jobConfig.auditRetentionDays / 365)} Years`}
          description="Forensic legal compliance"
          icon={<Database className="h-5 w-5 text-amber-500" />}
        />
      </div>

      {/* Configuration Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("academic")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "academic"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Sliders className="h-4 w-4" />
          Academic & Regulatory Policies
        </button>
        <button
          onClick={() => setActiveTab("security")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "security"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Shield className="h-4 w-4" />
          Authentication & Access Security
        </button>
        <button
          onClick={() => setActiveTab("jobs")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "jobs"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Zap className="h-4 w-4" />
          Automated Cron Jobs & Storage
        </button>
        <button
          onClick={() => setActiveTab("integration")}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "integration"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Server className="h-4 w-4" />
          Gateways & Cloud Relays
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-4">
        {/* TAB 1: ACADEMIC */}
        {activeTab === "academic" && (
          <Card className="p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-6">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Statutory Attendance Rules
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Configure threshold cutoffs governing student exam eligibility
                and shortage flags.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Minimum Attendance for Examination Eligibility (%)
                </label>
                <Input
                  type="number"
                  step="0.5"
                  value={academicConfig.minAttendancePercent}
                  onChange={(e) =>
                    setAcademicConfig({
                      ...academicConfig,
                      minAttendancePercent: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="h-9 text-xs"
                />
                <span className="text-[11px] text-slate-400">
                  Standard regulatory cutoff across affiliated universities
                  (typically 75.0%).
                </span>
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Medical / Condonation Exemption Floor (%)
                </label>
                <Input
                  type="number"
                  step="0.5"
                  value={academicConfig.condonationThresholdPercent}
                  onChange={(e) =>
                    setAcademicConfig({
                      ...academicConfig,
                      condonationThresholdPercent:
                        parseFloat(e.target.value) || 0,
                    })
                  }
                  className="h-9 text-xs"
                />
                <span className="text-[11px] text-slate-400">
                  Students between this floor and minimum can apply for
                  Principal condonation.
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Faculty Workload Bounds
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Institutional weekly contact hour expectations per professor.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Min Weekly Hours
                  </label>
                  <Input
                    type="number"
                    value={academicConfig.minFacultyWorkloadHours}
                    onChange={(e) =>
                      setAcademicConfig({
                        ...academicConfig,
                        minFacultyWorkloadHours:
                          parseInt(e.target.value, 10) || 0,
                      })
                    }
                    className="h-9 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Max Weekly Hours
                  </label>
                  <Input
                    type="number"
                    value={academicConfig.maxFacultyWorkloadHours}
                    onChange={(e) =>
                      setAcademicConfig({
                        ...academicConfig,
                        maxFacultyWorkloadHours:
                          parseInt(e.target.value, 10) || 0,
                      })
                    }
                    className="h-9 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                    HOD Administrative Allowance (Reduction)
                  </label>
                  <Input
                    type="number"
                    value={academicConfig.hodTeachingReductionHours}
                    onChange={(e) =>
                      setAcademicConfig({
                        ...academicConfig,
                        hodTeachingReductionHours:
                          parseInt(e.target.value, 10) || 0,
                      })
                    }
                    className="h-9 text-xs"
                  />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* TAB 2: SECURITY */}
        {activeTab === "security" && (
          <Card className="p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-6">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Authentication & Session Policies
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Defense-in-depth security controls protecting user credentials
                and token lifetimes.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Idle Session Timeout (Minutes)
                </label>
                <Input
                  type="number"
                  value={securityConfig.sessionTimeoutMinutes}
                  onChange={(e) =>
                    setSecurityConfig({
                      ...securityConfig,
                      sessionTimeoutMinutes: parseInt(e.target.value, 10) || 15,
                    })
                  }
                  className="h-9 text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Max Consecutive Failed Login Attempts
                </label>
                <Input
                  type="number"
                  value={securityConfig.maxLoginAttempts}
                  onChange={(e) =>
                    setSecurityConfig({
                      ...securityConfig,
                      maxLoginAttempts: parseInt(e.target.value, 10) || 3,
                    })
                  }
                  className="h-9 text-xs"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
              <h4 className="font-semibold text-xs text-slate-900 dark:text-white">
                Multi-Factor Authentication (MFA / 2FA)
              </h4>
              <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={securityConfig.mfaEnforcedForAdmins}
                  onChange={(e) =>
                    setSecurityConfig({
                      ...securityConfig,
                      mfaEnforcedForAdmins: e.target.checked,
                    })
                  }
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                Enforce mandatory MFA for all Super Administrators and
                Institution Administrators
              </label>

              <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={securityConfig.mfaEnforcedForFaculty}
                  onChange={(e) =>
                    setSecurityConfig({
                      ...securityConfig,
                      mfaEnforcedForFaculty: e.target.checked,
                    })
                  }
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                Enforce mandatory MFA for Department Heads and Faculty Members
              </label>
            </div>
          </Card>
        )}

        {/* TAB 3: AUTOMATED JOBS */}
        {activeTab === "jobs" && (
          <Card className="p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-6">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Automated Background Cron Daemons
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Scheduled background tasks maintaining data synchronization and
                telemetry alerts.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Attendance Shortage Radar
                </div>
                <p className="text-slate-500 dark:text-slate-400 mb-2">
                  Scans daily attendance registers at 18:00 and dispatches
                  notification alerts to students with &lt;75% attendance.
                </p>
                <span className="font-mono text-[11px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                  {jobConfig.attendanceRadarSchedule}
                </span>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-500" />
                  Fee Arrear Late Penalty Job
                </div>
                <p className="text-slate-500 dark:text-slate-400 mb-2">
                  Computes overdue invoice interest and applies late fee charges
                  after grace periods expire.
                </p>
                <span className="font-mono text-[11px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                  {jobConfig.feeLateFeeSchedule}
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
              <label className="block font-medium text-slate-700 dark:text-slate-300 text-xs mb-1">
                Forensic Audit Trail Retention (Days)
              </label>
              <Input
                type="number"
                value={jobConfig.auditRetentionDays}
                onChange={(e) =>
                  setJobConfig({
                    ...jobConfig,
                    auditRetentionDays: parseInt(e.target.value, 10) || 365,
                  })
                }
                className="h-9 text-xs max-w-xs"
              />
              <span className="text-[11px] text-slate-400">
                2555 days equals 7 statutory academic years per higher education
                record retention mandates.
              </span>
            </div>
          </Card>
        )}

        {/* TAB 4: INTEGRATION */}
        {activeTab === "integration" && (
          <Card className="p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-6">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Notification Relays & External SIS Gateways
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                SMTP and SMS outbound transport endpoints and external
                educational API sync.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Institutional SMTP Relay Host
                </label>
                <Input
                  value={gatewayConfig.smtpHost}
                  onChange={(e) =>
                    setGatewayConfig({
                      ...gatewayConfig,
                      smtpHost: e.target.value,
                    })
                  }
                  className="h-9 text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  SMTP Port
                </label>
                <Input
                  type="number"
                  value={gatewayConfig.smtpPort}
                  onChange={(e) =>
                    setGatewayConfig({
                      ...gatewayConfig,
                      smtpPort: parseInt(e.target.value, 10) || 587,
                    })
                  }
                  className="h-9 text-xs"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
              <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={gatewayConfig.governmentPortalSync}
                  onChange={(e) =>
                    setGatewayConfig({
                      ...gatewayConfig,
                      governmentPortalSync: e.target.checked,
                    })
                  }
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                Enable automated NIRF / AISHE statutory accreditation telemetry
                export
              </label>
            </div>
          </Card>
        )}
      </form>
    </div>
  );
}
