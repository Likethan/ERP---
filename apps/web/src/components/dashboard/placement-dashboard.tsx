"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/ui/stat-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { placementsService } from "@/services/placements.service";
import { CompanyProfileItem, JobDriveItem, PlacementOfferItem } from "@/mocks/placements.mock";
import {
  Briefcase,
  Building,
  GraduationCap,
  Users,
  ArrowRight,
  TrendingUp,
  Award,
  Plus,
} from "lucide-react";

export function PlacementDashboard() {
  const [companies, setCompanies] = useState<CompanyProfileItem[]>([]);
  const [drives, setDrives] = useState<JobDriveItem[]>([]);
  const [offers, setOffers] = useState<PlacementOfferItem[]>([]);

  useEffect(() => {
    placementsService.getCompanies().then((res) => setCompanies(res.data));
    placementsService.getDrives().then((res) => setDrives(res.data));
    placementsService.getOffers().then((res) => setOffers(res.data));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-purple-950/40 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-purple-500/10 px-2.5 py-0.5 text-xs font-semibold text-purple-400 border border-purple-500/20 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
            Corporate Relations & Career Placement Cell
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Placement & Corporate Recruiting Hub
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Empanelled corporate recruiters, recruitment drives, candidate shortlisting, and verified job offers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/placement">
            <Button variant="primary" size="sm" leftIcon={<Plus className="h-3.5 w-3.5" />}>
              Create Job Drive
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Empanelled Recruiters"
          value={companies.length + 24}
          description="Tier-1 Super Dream & Dream partners"
          variant="indigo"
          icon={<Building className="h-4 w-4" />}
        />
        <StatCard
          label="Active Drives in Progress"
          value={drives.length}
          description="Cisco, Microsoft, TCS Digital"
          variant="purple"
          icon={<Briefcase className="h-4 w-4" />}
        />
        <StatCard
          label="Highest CTC Verified"
          value="₹24.0 LPA"
          change={{ value: "Microsoft Cloud", trend: "up" }}
          description="Software Engineering R&D"
          variant="emerald"
          icon={<Award className="h-4 w-4" />}
        />
        <StatCard
          label="Average Package (CTC)"
          value="₹12.4 LPA"
          change={{ value: "+14.2% vs 2025", trend: "up" }}
          description="Across 185 placed candidates"
          variant="sky"
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      {/* Active Drives & Offers Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Drives List */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Active Recruitment Drives</CardTitle>
              <CardDescription>On-campus interview cycles and eligibility criteria.</CardDescription>
            </div>
            <Link href="/app/placement">
              <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                All Drives <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {drives.map((d) => (
              <div
                key={d.id}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="font-bold text-white text-sm">{d.companyName}</div>
                  <Badge variant="success">₹{d.packageLPA} LPA</Badge>
                </div>
                <div className="text-slate-300 font-medium">{d.roleTitle}</div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
                  <span>
                    Min CGPA: <strong className="text-slate-200">{d.minimumCGPA}</strong>
                  </span>
                  <span>
                    {d.totalApplicants} Applicants • {d.shortlistedCount} Shortlisted
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Official Offers */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Verified Official Offers</CardTitle>
              <CardDescription>Accepted offers formally lodged in Career Records.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {offers.map((o) => (
              <div
                key={o.id}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 text-xs"
              >
                <div>
                  <div className="font-semibold text-white">
                    {o.studentName} ({o.rollNumber})
                  </div>
                  <div className="text-slate-400 text-[11px] mt-0.5">
                    {o.companyName} • {o.designation}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-emerald-400 text-sm">
                    ₹{o.packageLPA} LPA
                  </div>
                  <Badge variant="success" dot className="mt-0.5">
                    {o.acceptanceStatus}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
