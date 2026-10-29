"use client";

import React, { useState, useEffect } from "react";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsPolicyConfigModel } from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BookOpen,
  FileText,
  Download,
  Calendar,
  Clock,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

export default function PolicyReferencesPage() {
  const [policies, setPolicies] = useState<StudentAffairsPolicyConfigModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await studentAffairsService.getPolicies();
      setPolicies(data);
      setLoading(false);
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Policy & Procedure References", href: "/app/student-affairs/policies" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <BookOpen className="h-6 w-6 text-indigo-400" />
          Institutional Policies, Codes of Conduct & Procedural Regulations
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Version-controlled institutional policy frameworks, UGC statutory fairness regulations, and procedural timeline benchmarks.
        </p>
      </div>

      <StudentAffairsNav />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {policies.map((pol) => (
          <Card
            key={pol.id}
            className="p-6 border-slate-800 bg-slate-900/40 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-indigo-400">
                  {pol.policy_code}
                </span>
                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]">
                  {pol.current_version}
                </Badge>
              </div>

              <h2 className="text-sm font-semibold text-white leading-snug">
                {pol.policy_name}
              </h2>

              <div className="space-y-1.5 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                <div className="flex justify-between">
                  <span>Effective Date:</span>
                  <span className="text-slate-200">{pol.effective_date}</span>
                </div>
                <div className="flex justify-between">
                  <span>Triage SLA Window:</span>
                  <span className="text-slate-200">{pol.sla_triage_hours} Hours</span>
                </div>
                <div className="flex justify-between">
                  <span>Investigation Window:</span>
                  <span className="text-slate-200">{pol.sla_investigation_days} Days</span>
                </div>
                <div className="flex justify-between">
                  <span>Statutory Appeal Window:</span>
                  <span className="text-emerald-400 font-medium">{pol.standard_appeal_window_days} Days</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">Official Syndicate Gazette</span>
              <Button size="sm" variant="outline" className="border-slate-700 text-slate-300 text-xs gap-1.5">
                <Download className="h-3 w-3" />
                Charter PDF
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
