"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  CustomerSuccessTenantSummaryModel,
  DowngradeImpactPreviewModel,
  EffectiveEntitlementsModel,
  SubscriptionInvoiceModel,
  SubscriptionPlanModel,
  SubscriptionQuotaStatusModel,
  TenantSubscriptionModel,
} from "@campusos/types";

export default function SubscriptionsCustomerSuccessPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"subscription" | "entitlements" | "quotas" | "invoices" | "platform_cs">("subscription");

  const [subscription, setSubscription] = useState<TenantSubscriptionModel | null>(null);
  const [entitlements, setEntitlements] = useState<EffectiveEntitlementsModel | null>(null);
  const [quotas, setQuotas] = useState<SubscriptionQuotaStatusModel[]>([]);
  const [invoices, setInvoices] = useState<SubscriptionInvoiceModel[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlanModel[]>([]);
  const [csSummaries, setCsSummaries] = useState<CustomerSuccessTenantSummaryModel[]>([]);

  // Downgrade preview modal
  const [showDowngradeModal, setShowDowngradeModal] = useState(false);
  const [selectedTargetPlan, setSelectedTargetPlan] = useState<string>("");
  const [downgradePreview, setDowngradePreview] = useState<DowngradeImpactPreviewModel | null>(null);
  const [evaluatingDowngrade, setEvaluatingDowngrade] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const isSuperAdmin = user?.role === "SUPER_ADMIN" || user?.role === "PLATFORM_OPERATOR";

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subRes, entRes, quotasRes, invRes, plansRes, csRes] = await Promise.all([
        apiFetch<TenantSubscriptionModel>("/api/v1/subscriptions/my").catch(() => ({ data: null })),
        apiFetch<EffectiveEntitlementsModel>("/api/v1/subscriptions/my/entitlements").catch(() => ({ data: null })),
        apiFetch<SubscriptionQuotaStatusModel[]>("/api/v1/subscriptions/my/quotas").catch(() => ({ data: [] })),
        apiFetch<SubscriptionInvoiceModel[]>("/api/v1/subscriptions/my/invoices").catch(() => ({ data: [] })),
        isSuperAdmin
          ? apiFetch<SubscriptionPlanModel[]>("/api/v1/platform/plans").catch(() => ({ data: [] }))
          : Promise.resolve({ data: [] }),
        isSuperAdmin
          ? apiFetch<CustomerSuccessTenantSummaryModel[]>("/api/v1/platform/customer-success/summary").catch(() => ({ data: [] }))
          : Promise.resolve({ data: [] }),
      ]);

      setSubscription(subRes.data || null);
      setEntitlements(entRes.data || null);
      setQuotas(quotasRes.data || []);
      setInvoices(invRes.data || []);
      setPlans(plansRes.data || []);
      setCsSummaries(csRes.data || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load subscription data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePreviewDowngrade = async (planId: string) => {
    if (!planId) return;
    setEvaluatingDowngrade(true);
    try {
      const res = await apiFetch<DowngradeImpactPreviewModel>(
        `/api/v1/subscriptions/my/preview-downgrade?target_plan_id=${planId}`,
        { method: "POST" }
      );
      setDowngradePreview(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to preview downgrade impact");
    } finally {
      setEvaluatingDowngrade(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <span className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              💎
            </span>
            SaaS Subscriptions & Entitlements
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Institutional commercial plan, usage capacity meters, feature gating, and billing governance.
          </p>
        </div>

        {subscription && (
          <div className="flex items-center gap-3 bg-gray-900/80 border border-gray-800 px-4 py-2.5 rounded-xl">
            <div className="text-right">
              <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Active Tier</div>
              <div className="text-sm font-bold text-indigo-400">{subscription.plan?.name || "Enterprise"}</div>
            </div>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {subscription.status}
            </span>
          </div>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">✕</button>
        </div>
      )}
      {actionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-800 pb-3">
        {[
          { key: "subscription", label: "Subscription Overview", icon: "📋" },
          { key: "entitlements", label: "Enabled Modules & Gates", icon: "🛡️" },
          { key: "quotas", label: "Capacity & Quotas", icon: "📊" },
          { key: "invoices", label: "Billing & Invoices", icon: "🧾" },
          ...(isSuperAdmin ? [{ key: "platform_cs", label: "Platform Customer Success", icon: "🌟" }] : []),
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              activeTab === tab.key
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "text-gray-400 hover:text-white hover:bg-gray-800/60"
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-20 text-center text-gray-500 text-sm animate-pulse">
          Loading subscription governance records...
        </div>
      ) : (
        <>
          {/* TAB 1: Subscription Overview */}
          {activeTab === "subscription" && subscription && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-6">
                <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-6">
                  <div className="flex items-center justify-between border-b border-gray-800/60 pb-4">
                    <div>
                      <h2 className="text-lg font-bold text-white">{subscription.plan?.name || "CampusOS Plan"}</h2>
                      <p className="text-sm text-gray-400 mt-0.5">{subscription.plan?.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-black text-white">
                        ₹{Number(subscription.unit_price).toLocaleString("en-IN")}
                      </div>
                      <div className="text-xs text-gray-400">per {subscription.billing_interval.toLowerCase()}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="p-3.5 rounded-xl bg-gray-800/40 border border-gray-700/40">
                      <div className="text-xs text-gray-400">Current Period Start</div>
                      <div className="text-sm font-semibold text-white mt-1">
                        {new Date(subscription.current_period_start).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-gray-800/40 border border-gray-700/40">
                      <div className="text-xs text-gray-400">Current Period End</div>
                      <div className="text-sm font-semibold text-white mt-1">
                        {new Date(subscription.current_period_end).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-gray-800/40 border border-gray-700/40">
                      <div className="text-xs text-gray-400">Auto Renewal</div>
                      <div className="text-sm font-semibold text-emerald-400 mt-1">
                        {subscription.auto_renew ? "Enabled" : "Disabled"}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-gray-800/40 border border-gray-700/40">
                      <div className="text-xs text-gray-400">Support Level</div>
                      <div className="text-sm font-semibold text-indigo-400 mt-1">
                        {subscription.plan?.support_tier || "STANDARD"}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <button
                      onClick={() => setShowDowngradeModal(true)}
                      className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 transition-colors border border-gray-700"
                    >
                      Assess Plan Downgrade
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick Status Sidebar */}
              <div className="space-y-6">
                <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
                  <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Account Entitlements</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">Status</span>
                      <span className="font-semibold text-emerald-400">{subscription.status}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">Included Modules</span>
                      <span className="font-semibold text-white">{subscription.snapshot_modules_json.length}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">Max Active Users</span>
                      <span className="font-semibold text-white">
                        {subscription.snapshot_limits_json.max_active_users?.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">Max Students</span>
                      <span className="font-semibold text-white">
                        {subscription.snapshot_limits_json.max_students?.toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Enabled Modules & Capabilities */}
          {activeTab === "entitlements" && entitlements && (
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-6">
                <div>
                  <h2 className="text-lg font-bold text-white">Active ERP Modules</h2>
                  <p className="text-sm text-gray-400 mt-1">
                    Modules unlocked for your institutional subscription under tier {entitlements.plan_code}.
                  </p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                  {entitlements.enabled_modules.map((m) => (
                    <div key={m} className="p-3 rounded-xl bg-gray-800/40 border border-indigo-500/20 text-center">
                      <div className="text-indigo-400 text-lg mb-1">📦</div>
                      <div className="text-xs font-bold text-white tracking-wide">{m}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-6">
                <div>
                  <h2 className="text-lg font-bold text-white">Feature Capabilities</h2>
                  <p className="text-sm text-gray-400 mt-1">
                    Premium and enterprise-level feature gates configured for your subscription.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(entitlements.feature_capabilities).map(([key, val]) => (
                    <div key={key} className="p-4 rounded-xl bg-gray-800/30 border border-gray-800 flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-white capitalize">{key.replace(/_/g, " ")}</div>
                        <div className="text-xs text-gray-500">{key}</div>
                      </div>
                      <span className={`px-2 py-0.5 text-xs font-bold rounded-md ${
                        val ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-gray-800 text-gray-500 border border-gray-700"
                      }`}>
                        {val ? "ENABLED" : "LOCKED"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Capacity & Quotas */}
          {activeTab === "quotas" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {quotas.map((q) => (
                <div key={q.resource_type} className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">{q.resource_type.replace(/_/g, " ")}</h3>
                      <div className="text-xs text-gray-500">{q.unit}</div>
                    </div>
                    <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                      q.is_exceeded
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        : q.utilization_percentage >= 80
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    }`}>
                      {q.utilization_percentage}%
                    </span>
                  </div>

                  <div className="w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-500 ${
                        q.is_exceeded ? "bg-rose-500" : q.utilization_percentage >= 80 ? "bg-amber-500" : "bg-indigo-500"
                      }`}
                      style={{ width: `${Math.min(100, q.utilization_percentage)}%` }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-xs text-gray-400 pt-1">
                    <span>Current: <strong className="text-white">{q.current_usage.toLocaleString()}</strong></span>
                    <span>Limit: <strong className="text-white">{q.hard_limit.toLocaleString()}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 4: Billing & Invoices */}
          {activeTab === "invoices" && (
            <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
              <h2 className="text-lg font-bold text-white">Subscription Invoices</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-400">
                  <thead className="text-xs uppercase bg-gray-800/60 text-gray-400 border-b border-gray-700/60">
                    <tr>
                      <th className="px-4 py-3">Invoice #</th>
                      <th className="px-4 py-3">Period</th>
                      <th className="px-4 py-3">Due Date</th>
                      <th className="px-4 py-3">Total Amount</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {invoices.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                          No invoices issued yet.
                        </td>
                      </tr>
                    ) : (
                      invoices.map((inv) => (
                        <tr key={inv.id} className="hover:bg-gray-800/30 transition-colors">
                          <td className="px-4 py-3 font-semibold text-white">{inv.invoice_number}</td>
                          <td className="px-4 py-3 text-xs">
                            {new Date(inv.billing_period_start).toLocaleDateString()} – {new Date(inv.billing_period_end).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-xs">{new Date(inv.due_date).toLocaleDateString()}</td>
                          <td className="px-4 py-3 font-semibold text-white">
                            ₹{Number(inv.total_amount).toLocaleString("en-IN")}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 text-xs font-bold rounded-md ${
                              inv.status === "PAID"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : inv.status === "PAST_DUE"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}>
                              {inv.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-indigo-400 hover:text-indigo-300 text-xs font-semibold cursor-pointer">
                              Download PDF
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: Platform Customer Success (Admin Only) */}
          {activeTab === "platform_cs" && isSuperAdmin && (
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-white">Platform Customer Success Health Matrix</h2>
                    <p className="text-sm text-gray-400 mt-1">
                      Multi-tenant operational health, renewal horizons, quota pressure, and critical support ticket tracking.
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-gray-400">
                    <thead className="text-xs uppercase bg-gray-800/60 text-gray-400 border-b border-gray-700/60">
                      <tr>
                        <th className="px-4 py-3">Institution</th>
                        <th className="px-4 py-3">Plan</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Health Score</th>
                        <th className="px-4 py-3">Renewal In</th>
                        <th className="px-4 py-3">Utilization</th>
                        <th className="px-4 py-3">Critical Tickets</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {csSummaries.map((s) => (
                        <tr key={s.tenant_id} className="hover:bg-gray-800/30 transition-colors">
                          <td className="px-4 py-3 font-semibold text-white">
                            {s.institution_name}
                            <div className="text-xs text-gray-500">{s.institution_code}</div>
                          </td>
                          <td className="px-4 py-3">{s.plan_name}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-gray-800 text-gray-300 border border-gray-700">
                              {s.subscription_status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                              s.health_score >= 80
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : s.health_score >= 60
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}>
                              {s.health_score} ({s.health_status})
                            </span>
                          </td>
                          <td className="px-4 py-3 text-xs">
                            {s.days_until_renewal} days
                          </td>
                          <td className="px-4 py-3 text-xs">{s.utilization_pct}%</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 text-xs font-bold rounded-md ${
                              s.open_critical_tickets > 0 ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "text-gray-500"
                            }`}>
                              {s.open_critical_tickets}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Downgrade Impact Assessment Modal */}
      {showDowngradeModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Pre-Flight Downgrade Capacity Assessment</h3>
                <p className="text-xs text-gray-400 mt-1">Non-destructive evaluation of target plan limits against live data</p>
              </div>
              <button onClick={() => { setShowDowngradeModal(false); setDowngradePreview(null); }} className="text-gray-500 hover:text-white">✕</button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">Select Target Plan</label>
                <select
                  value={selectedTargetPlan}
                  onChange={(e) => {
                    setSelectedTargetPlan(e.target.value);
                    handlePreviewDowngrade(e.target.value);
                  }}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">-- Choose a packaging plan --</option>
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} (₹{Number(p.base_price).toLocaleString("en-IN")})</option>
                  ))}
                </select>
              </div>

              {evaluatingDowngrade && (
                <div className="py-6 text-center text-sm text-gray-400 animate-pulse">
                  Analyzing capacity differences and data limits...
                </div>
              )}

              {downgradePreview && (
                <div className="space-y-4">
                  <div className={`p-4 rounded-xl border ${
                    downgradePreview.has_capacity_violations
                      ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                      : "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  } text-sm`}>
                    <div className="font-bold flex items-center gap-2">
                      <span>{downgradePreview.has_capacity_violations ? "⚠️ Capacity Violations Detected" : "✅ Capacity Safe"}</span>
                    </div>
                    <p className="text-xs mt-1">
                      {downgradePreview.has_capacity_violations
                        ? "Your institution currently holds data exceeding the target plan caps. Student and faculty records will never be deleted."
                        : "Current data fits comfortably within the target plan limits."}
                    </p>
                  </div>

                  {downgradePreview.violations.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Violations Breakdown</div>
                      {downgradePreview.violations.map((v, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-gray-800/40 border border-gray-700/60 text-xs text-gray-300">
                          <span className="font-bold text-white">{v.resource}: </span>
                          Current: {v.current_usage} &gt; Cap: {v.target_limit} (Excess: +{v.excess}).
                          <div className="text-amber-400 mt-1">{v.remediation}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {downgradePreview.removed_modules.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Modules To Be Removed</div>
                      <div className="flex flex-wrap gap-1.5">
                        {downgradePreview.removed_modules.map((m) => (
                          <span key={m} className="px-2 py-0.5 text-xs rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 border-t border-gray-800 pt-4">
              <button
                onClick={() => { setShowDowngradeModal(false); setDowngradePreview(null); }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
