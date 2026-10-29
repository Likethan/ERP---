"use client";

import React, { useState, useEffect } from "react";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCategoryModel,
  StudentAffairsOfficeModel,
  SACaseType,
  SACasePriority,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Settings,
  ShieldCheck,
  Building2,
  FolderPlus,
  CheckCircle2,
  Users,
  Lock,
  Clock,
} from "lucide-react";

export default function ConfigurationPage() {
  const [categories, setCategories] = useState<GrievanceCategoryModel[]>([]);
  const [offices, setOffices] = useState<StudentAffairsOfficeModel[]>([]);

  // Category form
  const [catCode, setCatCode] = useState("");
  const [catName, setCatName] = useState("");
  const [caseType, setCaseType] = useState<SACaseType>(SACaseType.GRIEVANCE);
  const [defaultPriority, setDefaultPriority] = useState<SACasePriority>(SACasePriority.MEDIUM);
  const [slaResponseHours, setSlaResponseHours] = useState(48);
  const [slaResolutionDays, setSlaResolutionDays] = useState(10);
  const [isConfidential, setIsConfidential] = useState(false);
  const [allowAnonymous, setAllowAnonymous] = useState(true);

  const [notification, setNotification] = useState("");

  useEffect(() => {
    async function load() {
      const cats = await studentAffairsService.getCategories();
      const offs = await studentAffairsService.getOffices();
      setCategories(cats);
      setOffices(offs);
    }
    load();
  }, []);

  function handleAddCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!catCode || !catName) return;

    const newCat: GrievanceCategoryModel = {
      id: `cat-${Date.now()}`,
      tenant_id: "ten-001",
      code: catCode.toUpperCase(),
      name: catName,
      case_type: caseType,
      default_priority: defaultPriority,
      sla_response_hours: slaResponseHours,
      sla_resolution_days: slaResolutionDays,
      is_confidential_by_default: isConfidential,
      allow_anonymous: allowAnonymous,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setCategories((prev) => [...prev, newCat]);
    setNotification(`Grievance category "${catName}" registered.`);
    setCatCode("");
    setCatName("");
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Configuration & Policies", href: "/app/student-affairs/config" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Settings className="h-6 w-6 text-indigo-400" />
          Student Affairs, SLA & RBAC Workflow Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure institutional offices, grievance categories, statutory SLA targets, and case-level permission policies.
        </p>
      </div>

      <StudentAffairsNav />

      {notification && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Offices Strip */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-indigo-400" />
          Institutional Student Affairs Offices ({offices.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {offices.map((off) => (
            <Card key={off.id} className="p-5 border-slate-800 bg-slate-900/40 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-indigo-400 font-bold">{off.code}</span>
                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[9px]">
                  Active
                </Badge>
              </div>
              <h3 className="font-semibold text-white">{off.name}</h3>
              <p className="text-slate-400 text-[11px]">{off.description}</p>
              <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-800/80">
                Location: {off.room_location}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Categories & New Category Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4 border-t border-slate-800/80">
        {/* Categories List (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Registered Grievance Categories ({categories.length})
          </h2>

          <div className="space-y-3">
            {categories.map((cat) => (
              <Card key={cat.id} className="p-4 border-slate-800 bg-slate-900/40 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{cat.name}</span>
                    <span className="font-mono text-[10px] text-indigo-400">({cat.code})</span>
                  </div>
                  <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">
                    {cat.case_type}
                  </Badge>
                </div>
                <p className="text-slate-400 text-[11px]">{cat.description || "Configured standard institutional category."}</p>
                <div className="flex flex-wrap items-center gap-4 text-[10px] text-slate-400 pt-2 border-t border-slate-800/60">
                  <span>Priority: <strong className="text-slate-200">{cat.default_priority}</strong></span>
                  <span>Response SLA: <strong className="text-slate-200">{cat.sla_response_hours}h</strong></span>
                  <span>Resolution SLA: <strong className="text-slate-200">{cat.sla_resolution_days}d</strong></span>
                  <span>Allow Anonymous: <strong className={cat.allow_anonymous ? "text-emerald-400" : "text-slate-500"}>{cat.allow_anonymous ? "Yes" : "No"}</strong></span>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Add Category Form (1 Col) */}
        <div>
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <FolderPlus className="h-4 w-4 text-indigo-400" />
              Configure Category
            </h2>

            <form onSubmit={handleAddCategory} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Category Code *</label>
                <input
                  type="text"
                  placeholder="e.g. LAB_EQUIP"
                  value={catCode}
                  onChange={(e) => setCatCode(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Display Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Laboratory Equipment Discrepancy"
                  value={catName}
                  onChange={(e) => setCatName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-300 mb-1">Case Type</label>
                  <select
                    value={caseType}
                    onChange={(e) => setCaseType(e.target.value as SACaseType)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-white text-[11px]"
                  >
                    <option value={SACaseType.GRIEVANCE}>GRIEVANCE</option>
                    <option value={SACaseType.DISCIPLINARY}>DISCIPLINARY</option>
                    <option value={SACaseType.MEDIATION}>MEDIATION</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">Default Priority</label>
                  <select
                    value={defaultPriority}
                    onChange={(e) => setDefaultPriority(e.target.value as SACasePriority)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-white text-[11px]"
                  >
                    <option value={SACasePriority.LOW}>LOW</option>
                    <option value={SACasePriority.MEDIUM}>MEDIUM</option>
                    <option value={SACasePriority.HIGH}>HIGH</option>
                    <option value={SACasePriority.CRITICAL_URGENT}>CRITICAL</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-300 mb-1">SLA Response (Hrs)</label>
                  <input
                    type="number"
                    value={slaResponseHours}
                    onChange={(e) => setSlaResponseHours(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                    min={6}
                    max={120}
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">SLA Resolution (Days)</label>
                  <input
                    type="number"
                    value={slaResolutionDays}
                    onChange={(e) => setSlaResolutionDays(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                    min={1}
                    max={60}
                  />
                </div>
              </div>

              <div className="space-y-2 pt-1 text-slate-300">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowAnonymous}
                    onChange={(e) => setAllowAnonymous(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                  />
                  <span>Permit Anonymous Submissions</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isConfidential}
                    onChange={(e) => setIsConfidential(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                  />
                  <span>Confidential by Default</span>
                </label>
              </div>

              <Button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs mt-2"
              >
                Register Category
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
