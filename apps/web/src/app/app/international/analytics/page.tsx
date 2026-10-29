"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Award,
  BarChart3,
  Building2,
  Compass,
  DoorOpen,
  Globe,
  MapPin,
  PieChart,
  Scale,
  TrendingUp,
  Users,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InternationalDashboardMetrics, InternationalPartner } from "@/types/international";

export default function MobilityAnalyticsPage() {
  const [metrics, setMetrics] = useState<InternationalDashboardMetrics | null>(null);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [m, p] = await Promise.all([
          internationalService.getDashboardMetrics(),
          internationalService.getPartners(),
        ]);
        setMetrics(m);
        setPartners(p);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const countryDistribution = [
    { country: "Germany", code: "DE", partners: 1, outbound: 8, inbound: 3, percentage: 35 },
    { country: "Singapore", code: "SG", partners: 1, outbound: 6, inbound: 2, percentage: 26 },
    { country: "Switzerland", code: "CH", partners: 1, outbound: 3, inbound: 1, percentage: 17 },
    { country: "Netherlands", code: "NL", partners: 1, outbound: 2, inbound: 1, percentage: 13 },
    { country: "United Kingdom", code: "GB", partners: 1, outbound: 1, inbound: 0, percentage: 5 },
    { country: "Australia", code: "AU", partners: 1, outbound: 1, inbound: 0, percentage: 4 },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-cyan-400" />
            Global Mobility & Treaty Operational Analytics
          </h2>
          <p className="text-xs text-slate-400">
            Institutional reciprocity balance, geographic distribution, and cross-border academic collaboration trends
          </p>
        </div>

        {/* High-level metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase">Reciprocity Ratio</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">2.7 : 1</span>
              <span className="text-xs text-cyan-400 font-medium">Outbound to Inbound</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">19 Outbound vs 7 Inbound</p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase">Global Partner Footprint</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">6 Countries</span>
              <span className="text-xs text-emerald-400 font-medium">Tier-1 Consortia</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">100% Accredited Institutions</p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase">Credit Transfer Approval</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">94.2%</span>
              <span className="text-xs text-purple-400 font-medium">Council Approved</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">ECTS / UGC Parity Guaranteed</p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase">Grant Utilization</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">88.5%</span>
              <span className="text-xs text-amber-400 font-medium">Endowment Disbursed</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">$45,000 of $50,000 Total Pool</p>
          </div>
        </div>

        {/* Geographic Distribution Breakdown */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Globe className="h-4 w-4 text-cyan-400" />
                Geographic Mobility Distribution & Partner Participation
              </h3>
              <p className="text-xs text-slate-400">
                Breakdown of active student mobility volumes across international partner jurisdictions
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            {countryDistribution.map((item) => (
              <div key={item.country} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white flex items-center gap-2">
                    <span className="font-mono text-cyan-400">{item.code}</span>
                    <span>{item.country}</span>
                    <span className="text-slate-500 text-[11px]">({item.partners} Partner)</span>
                  </span>
                  <span className="text-slate-400 text-xs">
                    {item.outbound} Outbound · {item.inbound} Inbound ({item.percentage}%)
                  </span>
                </div>

                <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-500"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
