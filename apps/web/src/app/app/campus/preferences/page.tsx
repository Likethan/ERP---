"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  CategoryNotificationPreference,
  NotificationDeliverySummary,
  CommunicationRecord,
  NotificationCategory,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  SlidersHorizontal,
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Save,
  CheckCircle2,
  AlertTriangle,
  Send,
  History,
  ShieldAlert,
  Clock,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CommunicationPreferencesPage() {
  const { user, hasPermission } = useAuth();
  const [preferences, setPreferences] = useState<CategoryNotificationPreference[]>([]);
  const [deliveries, setDeliveries] = useState<NotificationDeliverySummary[]>([]);
  const [history, setHistory] = useState<CommunicationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"preferences" | "delivery" | "history">("preferences");

  const isAdmin = hasPermission("campus.manage_notifications") || hasPermission("*");

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [prefRes, delRes, histRes] = await Promise.all([
          campusService.getNotificationPreferences(),
          campusService.getDeliverySummaries(),
          campusService.getCommunicationHistory(),
        ]);

        if (prefRes.data) setPreferences(prefRes.data);
        if (delRes.data) setDeliveries(delRes.data);
        if (histRes.data) setHistory(histRes.data);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleToggle = (category: NotificationCategory, channel: "inApp" | "email" | "sms" | "push") => {
    setPreferences((prev) =>
      prev.map((item) =>
        item.category === category
          ? {
              ...item,
              [channel]: !item[channel],
            }
          : item
      )
    );
  };

  const handleSavePreferences = async () => {
    try {
      setSaving(true);
      await campusService.updateNotificationPreferences(preferences);
      setFeedback("Communication channel preferences saved successfully!");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/app/campus" className="text-xs text-slate-400 hover:text-indigo-400">
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">Communication Settings</span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <SlidersHorizontal className="h-6 w-6 text-indigo-400" />
            Communication Channels & Delivery Console
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Control notification channel routing across In-App, Email, SMS, and Push dispatches.
          </p>
        </div>

        {activeTab === "preferences" && (
          <Button
            variant="primary"
            size="sm"
            isLoading={saving}
            onClick={handleSavePreferences}
            leftIcon={<Save className="h-4 w-4" />}
            className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
          >
            Save Preferences
          </Button>
        )}
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("preferences")}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === "preferences"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
              : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          Channel Preferences
        </button>
        {isAdmin && (
          <>
            <button
              onClick={() => setActiveTab("delivery")}
              className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                activeTab === "delivery"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              Simulated Delivery Status
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                activeTab === "history"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              Communication History ({history.length})
            </button>
          </>
        )}
      </div>

      {/* TAB 1: PREFERENCES MATRIX */}
      {activeTab === "preferences" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-4">Notification Category</th>
                    <th className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Bell className="h-3.5 w-3.5 text-indigo-400" />
                        <span>In-App</span>
                      </div>
                    </th>
                    <th className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Mail className="h-3.5 w-3.5 text-blue-400" />
                        <span>Email</span>
                      </div>
                    </th>
                    <th className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <MessageSquare className="h-3.5 w-3.5 text-emerald-400" />
                        <span>SMS</span>
                      </div>
                    </th>
                    <th className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Smartphone className="h-3.5 w-3.5 text-purple-400" />
                        <span>Push</span>
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {preferences.map((item) => (
                    <tr key={item.category} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4">
                        <div className="font-bold text-white text-xs">{item.categoryLabel}</div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">{item.category}</div>
                      </td>

                      {/* In-App Toggle */}
                      <td className="p-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleToggle(item.category, "inApp")}
                          className={`w-12 h-6 rounded-full transition-colors p-0.5 inline-flex items-center cursor-pointer ${
                            item.inApp ? "bg-indigo-600 justify-end" : "bg-slate-800 justify-start"
                          }`}
                        >
                          <span className="w-5 h-5 rounded-full bg-white block shadow" />
                        </button>
                      </td>

                      {/* Email Toggle */}
                      <td className="p-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleToggle(item.category, "email")}
                          className={`w-12 h-6 rounded-full transition-colors p-0.5 inline-flex items-center cursor-pointer ${
                            item.email ? "bg-blue-600 justify-end" : "bg-slate-800 justify-start"
                          }`}
                        >
                          <span className="w-5 h-5 rounded-full bg-white block shadow" />
                        </button>
                      </td>

                      {/* SMS Toggle */}
                      <td className="p-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleToggle(item.category, "sms")}
                          className={`w-12 h-6 rounded-full transition-colors p-0.5 inline-flex items-center cursor-pointer ${
                            item.sms ? "bg-emerald-600 justify-end" : "bg-slate-800 justify-start"
                          }`}
                        >
                          <span className="w-5 h-5 rounded-full bg-white block shadow" />
                        </button>
                      </td>

                      {/* Push Toggle */}
                      <td className="p-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleToggle(item.category, "push")}
                          className={`w-12 h-6 rounded-full transition-colors p-0.5 inline-flex items-center cursor-pointer ${
                            item.push ? "bg-purple-600 justify-end" : "bg-slate-800 justify-start"
                          }`}
                        >
                          <span className="w-5 h-5 rounded-full bg-white block shadow" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Preference Policy: </span>
            Critical security dispatches, examination CIA-1 timetables, and fee dues receipts are delivered to In-App and Email by default.
          </div>
        </div>
      )}

      {/* TAB 2: SIMULATED DELIVERY STATUS (FOR ADMINS) */}
      {activeTab === "delivery" && isAdmin && (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/20 text-amber-300 text-xs flex items-center gap-2 font-medium">
            <ShieldAlert className="h-4 w-4 shrink-0 text-amber-400" />
            <span>
              <strong>Note:</strong> Delivery statistics are frontend mock simulations representing future gateway queues.
            </span>
          </div>

          <div className="space-y-3">
            {deliveries.map((d, idx) => (
              <div
                key={idx}
                className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="font-bold text-white text-sm">{d.title}</div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 self-start sm:self-auto">
                    {d.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Total Audience:</span>
                    <span className="font-mono font-bold text-white">{d.audienceSize.toLocaleString()}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">In-App Delivered:</span>
                    <span className="font-mono font-bold text-indigo-400">{d.inAppDelivered.toLocaleString()}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Email Delivered:</span>
                    <span className="font-mono font-bold text-blue-400">
                      {d.emailDelivered.toLocaleString()}
                      {d.emailFailed > 0 && <span className="text-rose-400 text-[10px] ml-1">({d.emailFailed} fail)</span>}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">SMS Delivered:</span>
                    <span className="font-mono font-bold text-emerald-400">
                      {d.smsDelivered.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 font-mono pt-1">
                  Dispatched: {d.timestamp}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: COMMUNICATION HISTORY */}
      {activeTab === "history" && isAdmin && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Announcement / Alert</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5">Target Audience</th>
                  <th className="p-3.5">Publisher</th>
                  <th className="p-3.5">Channel Breakdown</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {history.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3.5 font-bold text-white max-w-xs truncate">{record.title}</td>
                    <td className="p-3.5">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {record.category}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-300">{record.audience}</td>
                    <td className="p-3.5 text-slate-400">{record.publisher}</td>
                    <td className="p-3.5 text-[11px] font-mono text-slate-400">{record.channelSummary}</td>
                    <td className="p-3.5">
                      <span className="font-mono text-[10px] font-bold text-emerald-400">
                        {record.deliveryStatus} ({record.deliveredRate}%)
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-500 text-[11px]">{record.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
