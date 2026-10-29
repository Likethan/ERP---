"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  IntegrationDataConflictModel,
  MarketplaceAppCategory,
  MarketplaceAppModel,
  MarketplaceConflictPolicy,
  MarketplaceSyncRunModel,
  PlatformMarketplaceHealthModel,
  TenantAppInstallationModel,
  TestConnectivityResultModel,
} from "@campusos/types";

export default function MarketplaceIntegrationsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "catalog" | "connected" | "history" | "conflicts" | "platform"
  >("catalog");

  const [catalogApps, setCatalogApps] = useState<MarketplaceAppModel[]>([]);
  const [connections, setConnections] = useState<TenantAppInstallationModel[]>(
    [],
  );
  const [conflicts, setConflicts] = useState<IntegrationDataConflictModel[]>(
    [],
  );
  const [selectedConnection, setSelectedConnection] =
    useState<TenantAppInstallationModel | null>(null);
  const [syncRuns, setSyncRuns] = useState<MarketplaceSyncRunModel[]>([]);
  const [platformHealth, setPlatformHealth] =
    useState<PlatformMarketplaceHealthModel | null>(null);

  // Filters & State
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Connection Modal
  const [connectModalApp, setConnectModalApp] =
    useState<MarketplaceAppModel | null>(null);
  const [configFields, setConfigFields] = useState<Record<string, string>>({});
  const [credentialFields, setCredentialFields] = useState<
    Record<string, string>
  >({});
  const [conflictPolicy, setConflictPolicy] = useState<string>(
    "CAMPUSOS_AUTHORITATIVE",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Probe Result
  const [probeResult, setProbeResult] =
    useState<TestConnectivityResultModel | null>(null);
  const [probingId, setProbingId] = useState<string | null>(null);

  const isSuperAdmin =
    user?.role === "SUPER_ADMIN" || user?.role === "PLATFORM_OPERATOR";

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [catRes, connRes, confRes, healthRes] = await Promise.all([
        apiFetch<MarketplaceAppModel[]>("/api/v1/marketplace/apps").catch(
          () => ({ data: [] }),
        ),
        apiFetch<TenantAppInstallationModel[]>(
          "/api/v1/integrations/connections",
        ).catch(() => ({ data: [] })),
        apiFetch<IntegrationDataConflictModel[]>(
          "/api/v1/integrations/conflicts",
        ).catch(() => ({ data: [] })),
        isSuperAdmin
          ? apiFetch<PlatformMarketplaceHealthModel>(
              "/api/v1/platform/marketplace/health",
            ).catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
      ]);

      setCatalogApps(catRes.data || []);
      setConnections(connRes.data || []);
      setConflicts(confRes.data || []);
      setPlatformHealth(healthRes.data || null);

      if (connRes.data && connRes.data.length > 0 && !selectedConnection) {
        setSelectedConnection(connRes.data[0]);
        loadSyncRuns(connRes.data[0].id);
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load marketplace data",
      );
    } finally {
      setLoading(false);
    }
  };

  const loadSyncRuns = async (installationId: string) => {
    try {
      const res = await apiFetch<MarketplaceSyncRunModel[]>(
        `/api/v1/integrations/connections/${installationId}/sync-runs`,
      );
      setSyncRuns(res.data || []);
    } catch {
      setSyncRuns([]);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered catalog
  const filteredApps = catalogApps.filter((app) => {
    const matchesSearch =
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      categoryFilter === "ALL" || app.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleOpenConnect = (app: MarketplaceAppModel) => {
    setConnectModalApp(app);
    setConfigFields({});
    setCredentialFields({});
    setConflictPolicy("CAMPUSOS_AUTHORITATIVE");
  };

  const handleInstallApp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!connectModalApp) return;

    try {
      setIsSubmitting(true);
      setError(null);

      await apiFetch("/api/v1/integrations/connections", {
        method: "POST",
        body: JSON.stringify({
          app_id: connectModalApp.id,
          display_name: connectModalApp.name,
          configuration: configFields,
          credentials:
            Object.keys(credentialFields).length > 0
              ? credentialFields
              : undefined,
          conflict_policy: conflictPolicy,
        }),
      });

      setActionNotice(`Successfully connected ${connectModalApp.name}!`);
      setConnectModalApp(null);
      await loadData();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to connect application",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTestProbe = async (instId: string) => {
    try {
      setProbingId(instId);
      setProbeResult(null);
      const res = await apiFetch<TestConnectivityResultModel>(
        `/api/v1/integrations/connections/${instId}/test`,
        {
          method: "POST",
        },
      );
      setProbeResult(res.data);
      setActionNotice(
        `Connectivity check: ${res.data.status} (${res.data.latency_ms}ms)`,
      );
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Test connectivity failed");
    } finally {
      setProbingId(null);
    }
  };

  const handleTriggerSync = async (instId: string) => {
    try {
      setActionNotice("Triggering on-demand synchronization...");
      const res = await apiFetch<MarketplaceSyncRunModel>(
        `/api/v1/integrations/connections/${instId}/sync`,
        {
          method: "POST",
          body: JSON.stringify({
            trigger_type: "MANUAL",
            force_full_sync: false,
          }),
        },
      );
      setActionNotice(
        `Sync completed: ${res.data.records_processed} records processed (${res.data.status})`,
      );
      await loadData();
      if (selectedConnection?.id === instId) {
        await loadSyncRuns(instId);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sync trigger failed");
    }
  };

  const handleTogglePause = async (inst: TenantAppInstallationModel) => {
    try {
      const isPaused = inst.status === "SYNC_PAUSED";
      const action = isPaused ? "resume" : "pause";
      await apiFetch(`/api/v1/integrations/connections/${inst.id}/${action}`, {
        method: "POST",
      });
      setActionNotice(`Integration sync ${isPaused ? "resumed" : "paused"}.`);
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Toggle pause failed");
    }
  };

  const handleDisconnect = async (instId: string) => {
    if (
      !confirm(
        "Are you sure you want to disconnect this integration? Vaulted credentials will be revoked.",
      )
    )
      return;
    try {
      await apiFetch(`/api/v1/integrations/connections/${instId}/disconnect`, {
        method: "POST",
      });
      setActionNotice("Integration safely disconnected.");
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Disconnection failed");
    }
  };

  const handleResolveConflict = async (
    conflictId: string,
    strategy: string,
  ) => {
    try {
      await apiFetch(`/api/v1/integrations/conflicts/${conflictId}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution_strategy: strategy }),
      });
      setActionNotice("Conflict resolved successfully.");
      await loadData();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Conflict resolution failed",
      );
    }
  };

  const handleSeedDefaults = async () => {
    try {
      setActionNotice(
        "Seeding certified production connectors into marketplace...",
      );
      await apiFetch("/api/v1/platform/marketplace/seed", { method: "POST" });
      setActionNotice("Certified connectors seeded successfully.");
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Seeding failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              CampusOS Enterprise Marketplace
            </span>
            <span className="text-xs bg-indigo-950 text-indigo-300 border border-indigo-700/60 rounded px-2.5 py-0.5 font-mono">
              Step 39
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Governed third-party extensions, API connectors, secure credential
            vaults, and bi-directional synchronization.
          </p>
        </div>

        {isSuperAdmin && (
          <button
            onClick={handleSeedDefaults}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-indigo-600/20"
          >
            Seed Certified Connectors
          </button>
        )}
      </div>

      {/* Notices & Alerts */}
      {error && (
        <div className="bg-red-950/80 border border-red-800 text-red-200 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-300 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}
      {actionNotice && (
        <div className="bg-emerald-950/80 border border-emerald-800 text-emerald-200 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
          <span>{actionNotice}</span>
          <button
            onClick={() => setActionNotice(null)}
            className="text-emerald-400 hover:text-emerald-300 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex gap-2 border-b border-slate-800">
        {[
          {
            key: "catalog",
            label: "App Marketplace",
            count: catalogApps.length,
          },
          {
            key: "connected",
            label: "Connected Apps",
            count: connections.length,
          },
          { key: "history", label: "Sync Execution", count: syncRuns.length },
          {
            key: "conflicts",
            label: "Conflict Governance",
            count: conflicts.filter((c) => c.status === "OPEN").length,
          },
          ...(isSuperAdmin
            ? [{ key: "platform", label: "Platform Health", count: undefined }]
            : []),
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === tab.key
                ? "border-indigo-500 text-indigo-400 bg-indigo-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  tab.key === "conflicts" && tab.count > 0
                    ? "bg-amber-900 text-amber-200"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab 1: Catalog */}
      {activeTab === "catalog" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <input
              type="text"
              placeholder="Search connectors by name, module, or code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-100 placeholder-slate-500 w-full sm:w-80 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex gap-2 flex-wrap">
              {[
                "ALL",
                "LMS",
                "PAYMENT_GATEWAY",
                "VIDEO_CONFERENCING",
                "HARDWARE_IOT",
                "GOVERNMENT_EXCHANGE",
              ].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                    categoryFilter === cat
                      ? "bg-indigo-600 border-indigo-500 text-white font-medium"
                      : "bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredApps.map((app) => {
              const installed = connections.find(
                (c) => c.app_id === app.id && c.status !== "DISCONNECTED",
              );
              return (
                <div
                  key={app.id}
                  className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-5 hover:border-indigo-500/60 transition flex flex-col justify-between shadow-sm relative overflow-hidden"
                >
                  {app.is_featured && (
                    <div className="absolute top-0 right-0 bg-indigo-600 text-[10px] font-bold px-2 py-0.5 rounded-bl text-white uppercase tracking-wider">
                      Featured
                    </div>
                  )}

                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-indigo-900/60 border border-indigo-700 flex items-center justify-center font-bold text-indigo-300">
                        {app.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-100">
                          {app.name}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {app.provider_name}
                        </p>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 line-clamp-3 mb-4">
                      {app.description}
                    </p>

                    <div className="space-y-2 mb-4 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Category:</span>
                        <span className="text-slate-200 font-mono">
                          {app.category}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Method:</span>
                        <span className="text-slate-200 font-mono">
                          {app.connection_method}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Required Modules:</span>
                        <span className="text-indigo-400 font-mono">
                          {app.required_entitlements.join(", ") || "None"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-700/60 pt-4 flex items-center justify-between">
                    <span className="text-xs text-slate-500">
                      v{app.min_platform_version}
                    </span>
                    {installed ? (
                      <span className="px-3 py-1 bg-emerald-950 border border-emerald-700 text-emerald-300 text-xs font-medium rounded-lg">
                        Installed ({installed.status})
                      </span>
                    ) : (
                      <button
                        onClick={() => handleOpenConnect(app)}
                        className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition"
                      >
                        Connect App
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Connected Apps */}
      {activeTab === "connected" && (
        <div className="space-y-6">
          {connections.length === 0 ? (
            <div className="text-center py-16 bg-slate-800/20 border border-slate-800 rounded-xl">
              <p className="text-slate-400 mb-2">
                No external integrations connected yet.
              </p>
              <button
                onClick={() => setActiveTab("catalog")}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium"
              >
                Browse Marketplace Catalog
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {connections.map((inst) => (
                <div
                  key={inst.id}
                  className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-lg text-slate-100">
                        {inst.display_name}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded font-mono ${
                          inst.status === "CONNECTED"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : inst.status === "DEGRADED"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : inst.status === "SYNC_PAUSED"
                                ? "bg-blue-950 text-blue-300 border border-blue-800"
                                : "bg-red-950 text-red-300 border border-red-800"
                        }`}
                      >
                        {inst.status}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        App Code: {inst.app_code}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400">
                      Sync: {inst.sync_direction} • Policy:{" "}
                      {inst.conflict_policy} • Vault:{" "}
                      {inst.has_credentials
                        ? "Encrypted Credentials Attached"
                        : "No Credentials"}
                    </p>

                    <div className="text-xs text-slate-500 flex gap-4 pt-1">
                      <span>
                        Last Health Check:{" "}
                        {inst.last_health_check_at
                          ? new Date(
                              inst.last_health_check_at,
                            ).toLocaleTimeString()
                          : "Never"}
                      </span>
                      <span>
                        Last Successful Sync:{" "}
                        {inst.last_successful_sync_at
                          ? new Date(
                              inst.last_successful_sync_at,
                            ).toLocaleString()
                          : "None"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={() => handleTestProbe(inst.id)}
                      disabled={probingId === inst.id}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition"
                    >
                      {probingId === inst.id ? "Probing..." : "Test Connection"}
                    </button>
                    <button
                      onClick={() => handleTriggerSync(inst.id)}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg transition"
                    >
                      Sync Now
                    </button>
                    <button
                      onClick={() => handleTogglePause(inst)}
                      className="px-3 py-1.5 bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
                    >
                      {inst.status === "SYNC_PAUSED" ? "Resume" : "Pause"}
                    </button>
                    <button
                      onClick={() => handleDisconnect(inst.id)}
                      className="px-3 py-1.5 bg-red-950/60 border border-red-800 text-red-300 hover:bg-red-900/60 text-xs rounded-lg transition"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Sync Execution Runs */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <div className="bg-slate-800/40 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
            <span className="text-sm text-slate-300">
              Showing synchronization runs for connected integration.
            </span>
          </div>

          <div className="overflow-x-auto bg-slate-800/60 border border-slate-700/80 rounded-xl">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="p-3">Started</th>
                  <th className="p-3">Trigger</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Fetched</th>
                  <th className="p-3">Created</th>
                  <th className="p-3">Updated</th>
                  <th className="p-3">Skipped</th>
                  <th className="p-3">Failed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {syncRuns.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-4 text-center text-slate-500">
                      No sync runs recorded yet.
                    </td>
                  </tr>
                ) : (
                  syncRuns.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-700/40">
                      <td className="p-3 font-mono text-xs">
                        {new Date(r.started_at).toLocaleTimeString()}
                      </td>
                      <td className="p-3 text-xs">{r.trigger_type}</td>
                      <td className="p-3">
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-mono ${
                            r.status === "SUCCESS"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : r.status === "PARTIAL_SUCCESS"
                                ? "bg-amber-950 text-amber-300 border border-amber-800"
                                : "bg-red-950 text-red-300 border border-red-800"
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-xs">
                        {r.records_fetched}
                      </td>
                      <td className="p-3 font-mono text-xs text-emerald-400">
                        {r.records_created}
                      </td>
                      <td className="p-3 font-mono text-xs text-blue-400">
                        {r.records_updated}
                      </td>
                      <td className="p-3 font-mono text-xs text-slate-400">
                        {r.records_skipped}
                      </td>
                      <td className="p-3 font-mono text-xs text-red-400">
                        {r.records_failed}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Conflict Governance */}
      {activeTab === "conflicts" && (
        <div className="space-y-4">
          {conflicts.length === 0 ? (
            <div className="text-center py-16 bg-slate-800/20 border border-slate-800 rounded-xl">
              <p className="text-slate-400">
                No unresolved integration data conflicts found.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {conflicts.map((conf) => (
                <div
                  key={conf.id}
                  className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-5 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-200">
                        Discrepancy in {conf.entity_type} (Record:{" "}
                        {conf.record_identifier})
                      </span>
                      <p className="text-xs text-slate-400">
                        Conflicting fields:{" "}
                        <span className="text-amber-400">
                          {conf.conflicting_fields.join(", ")}
                        </span>{" "}
                        • Status: {conf.status}
                      </p>
                    </div>
                    {conf.status === "OPEN" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() =>
                            handleResolveConflict(
                              conf.id,
                              "CAMPUSOS_AUTHORITATIVE",
                            )
                          }
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg transition"
                        >
                          Keep CampusOS
                        </button>
                        <button
                          onClick={() =>
                            handleResolveConflict(
                              conf.id,
                              "PROVIDER_AUTHORITATIVE",
                            )
                          }
                          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition"
                        >
                          Accept Provider
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                    <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                      <span className="text-slate-400 block mb-1 font-sans">
                        CampusOS Current Data:
                      </span>
                      <pre className="text-slate-200 overflow-x-auto">
                        {JSON.stringify(conf.campusos_payload, null, 2)}
                      </pre>
                    </div>
                    <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                      <span className="text-slate-400 block mb-1 font-sans">
                        External Provider Data:
                      </span>
                      <pre className="text-slate-200 overflow-x-auto">
                        {JSON.stringify(conf.provider_payload, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Platform Health (SuperAdmin) */}
      {activeTab === "platform" && platformHealth && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-800/60 border border-slate-700/80 p-5 rounded-xl">
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              Catalog Applications
            </span>
            <p className="text-3xl font-bold text-slate-100 mt-2">
              {platformHealth.total_catalog_apps}
            </p>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/80 p-5 rounded-xl">
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              Connected Instances
            </span>
            <p className="text-3xl font-bold text-emerald-400 mt-2">
              {platformHealth.active_connected_installations}
            </p>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/80 p-5 rounded-xl">
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              Degraded Connections
            </span>
            <p className="text-3xl font-bold text-amber-400 mt-2">
              {platformHealth.degraded_installations}
            </p>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/80 p-5 rounded-xl">
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              Sync Success Rate
            </span>
            <p className="text-3xl font-bold text-indigo-400 mt-2">
              {platformHealth.sync_success_rate}%
            </p>
          </div>
        </div>
      )}

      {/* Connect Application Modal */}
      {connectModalApp && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">
                Connect {connectModalApp.name}
              </h3>
              <button
                onClick={() => setConnectModalApp(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleInstallApp} className="space-y-4 text-sm">
              <p className="text-xs text-slate-400">
                {connectModalApp.setup_instructions}
              </p>

              {/* Dynamic Config Fields from Schema */}
              {connectModalApp.config_schema?.properties &&
                Object.entries(connectModalApp.config_schema.properties).map(
                  ([key, prop]: [string, any]) => (
                    <div key={key}>
                      <label className="block text-xs text-slate-400 mb-1">
                        {prop.description || key}
                      </label>
                      <input
                        type="text"
                        required={connectModalApp.config_schema.required?.includes(
                          key,
                        )}
                        value={configFields[key] || ""}
                        onChange={(e) =>
                          setConfigFields({
                            ...configFields,
                            [key]: e.target.value,
                          })
                        }
                        className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm w-full focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  ),
                )}

              {/* Secure Credentials Vault Input */}
              <div className="border-t border-slate-800 pt-3">
                <label className="block text-xs font-semibold text-indigo-300 mb-1">
                  API Key / Token / Secret (Securely Vaulted with Fernet
                  Encryption)
                </label>
                <input
                  type="password"
                  placeholder="Enter API token or secret..."
                  value={credentialFields["api_key"] || ""}
                  onChange={(e) =>
                    setCredentialFields({ api_key: e.target.value })
                  }
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm w-full focus:outline-none focus:border-indigo-500"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Secrets are never stored in plaintext or logged.
                </span>
              </div>

              {/* Conflict Policy */}
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Conflict Resolution Policy
                </label>
                <select
                  value={conflictPolicy}
                  onChange={(e) => setConflictPolicy(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm w-full focus:outline-none focus:border-indigo-500"
                >
                  <option value="CAMPUSOS_AUTHORITATIVE">
                    CampusOS Authoritative (Recommended)
                  </option>
                  <option value="PROVIDER_AUTHORITATIVE">
                    External Provider Authoritative
                  </option>
                  <option value="MANUAL_REVIEW">
                    Flag for Manual Institutional Review
                  </option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setConnectModalApp(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition"
                >
                  {isSubmitting ? "Connecting..." : "Confirm & Connect"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
