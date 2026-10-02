"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  Globe,
  Users,
  Briefcase,
  Phone,
  Mail,
  Calendar,
  Award,
  ChevronLeft,
  ExternalLink,
  MapPin,
  Clock,
  ShieldCheck,
  CheckCircle2,
  FileCheck2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { formatLPA } from "@/services/placement-calculator";
import { Company, JobDrive, Application, Interview, Offer } from "@/types/placement";

export default function CompanyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const companyId = params?.id as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [drives, setDrives] = useState<JobDrive[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [compRes, drivesRes, appsRes, ofrRes] = await Promise.all([
        placementService.getCompanyById(companyId),
        placementService.getJobDrives(),
        placementService.getApplications(),
        placementService.getOffers(),
      ]);

      if (!compRes.data) {
        showToast({ title: "Not Found", message: "Company profile not found", type: "error" });
        router.push("/app/placement/companies");
        return;
      }

      setCompany(compRes.data);
      setDrives((drivesRes.data || []).filter((d) => d.companyId === compRes.data?.id));
      setApplications((appsRes.data || []).filter((a) => a.companyId === compRes.data?.id));
      setOffers((ofrRes.data || []).filter((o) => o.companyId === compRes.data?.id));
    } catch {
      showToast({ title: "Error", message: "Failed to load company 360 profile", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (companyId) {
      loadData();
    }
  }, [companyId]);

  if (loading || !company) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading corporate partner profile...</p>
        </div>
      </div>
    );
  }

  const acceptedOffers = offers.filter((o) => o.status === "ACCEPTED").length;
  const pendingOffers = offers.filter((o) => o.status === "RELEASED").length;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/placement/companies"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Corporate Partners
        </Link>
      </div>

      {/* Header Profile Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              <Building2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {company.name}
                </h1>
                <Badge variant={company.status === "ACTIVE" ? "success" : "secondary"} dot>
                  {company.status}
                </Badge>
                <Badge variant="outline">{company.tier.replace(/_/g, " ")}</Badge>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <span className="font-mono font-medium">{company.code}</span>
                <span>•</span>
                <span>{company.industry}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {company.headquarters}
                </span>
                <span>•</span>
                <a
                  href={company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  <Globe className="w-3.5 h-3.5" />
                  Website
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href={`/app/placement/drives`}>
              <Button variant="primary" size="sm" className="gap-1.5 text-xs">
                <Briefcase className="w-3.5 h-3.5" />
                Launch Recruitment Drive
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-100 p-1 dark:bg-slate-800">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contacts">Contacts ({company.contacts.length})</TabsTrigger>
          <TabsTrigger value="drives">Job Drives ({drives.length})</TabsTrigger>
          <TabsTrigger value="applications">Applications ({applications.length})</TabsTrigger>
          <TabsTrigger value="offers">Offers ({offers.length})</TabsTrigger>
          <TabsTrigger value="history">Engagement History</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Average Package"
              value={formatLPA(company.averageCtcLpa)}
              icon={<Award className="w-5 h-5 text-indigo-500" />}
              description={`Peak: ${formatLPA(company.highestCtcLpa)}`}
            />
            <StatCard
              title="Total Alumni Placed"
              value={company.totalHiredCount}
              icon={<Users className="w-5 h-5 text-emerald-500" />}
              description="Graduates currently employed"
            />
            <StatCard
              title="Campus Drives Conducted"
              value={drives.length}
              icon={<Briefcase className="w-5 h-5 text-purple-500" />}
              description={`${company.activeDrivesCount} active in current season`}
            />
            <StatCard
              title="Current Season Offers"
              value={offers.length}
              icon={<CheckCircle2 className="w-5 h-5 text-teal-500" />}
              description={`${acceptedOffers} accepted, ${pendingOffers} pending`}
            />
          </div>

          {/* Details Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Corporate Overview & Relationship Details
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs">
              <div>
                <span className="text-slate-500">Corporate Legal Name:</span>
                <p className="font-semibold text-slate-900 dark:text-white mt-1">
                  {company.legalName || company.name}
                </p>
              </div>

              <div>
                <span className="text-slate-500">Enterprise Hiring Tier:</span>
                <p className="font-semibold text-slate-900 dark:text-white mt-1">
                  {company.tier.replace(/_/g, " ")}
                </p>
              </div>

              <div>
                <span className="text-slate-500">University Relationship Status:</span>
                <p className="font-semibold text-indigo-600 dark:text-indigo-400 mt-1">
                  {company.relationshipStatus.replace("_", " ")}
                </p>
              </div>
            </div>

            {company.notes && (
              <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-100 dark:bg-slate-800/40 dark:border-slate-700 text-xs">
                <span className="font-medium text-slate-500">Placement Cell Notes:</span>
                <p className="text-slate-700 dark:text-slate-300 mt-1">{company.notes}</p>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Tab 2: Contacts */}
        <TabsContent value="contacts" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Corporate HR & Campus Talent Leads
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {company.contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 dark:text-white">
                      {contact.name}
                    </span>
                    {contact.isPrimary && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                        PRIMARY SPOC
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 font-medium">{contact.role}</p>

                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60 space-y-1 text-xs">
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <a href={`mailto:${contact.email}`} className="hover:underline">
                        {contact.email}
                      </a>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{contact.phone}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Tab 3: Drives */}
        <TabsContent value="drives" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Campus Recruitment Drives
            </h2>
            {drives.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {drives.map((d) => (
                  <div key={d.id} className="py-4 flex items-center justify-between">
                    <div>
                      <Link
                        href={`/app/placement/drives/${d.id}`}
                        className="text-sm font-bold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                      >
                        {d.title}
                      </Link>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                        <span>Drive Date: {d.driveDate}</span>
                        <span>•</span>
                        <span>Positions: {d.positionsCount}</span>
                        <span>•</span>
                        <span>Applicants: {d.applicantsCount}</span>
                        <span>•</span>
                        <span>Offers: {d.offersCount}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge variant={d.status === "OPEN" ? "success" : "secondary"}>
                        {d.status}
                      </Badge>
                      <Link href={`/app/placement/drives/${d.id}`}>
                        <Button variant="outline" size="sm" className="text-xs">
                          Inspect Drive
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No recruitment drives recorded for this partner.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 4: Applications */}
        <TabsContent value="applications" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Candidate Applications
            </h2>
            {applications.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {applications.map((app) => (
                  <div key={app.id} className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-xs text-slate-900 dark:text-white">
                        {app.studentName} ({app.rollNumber})
                      </span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Applied for {app.positionTitle} on {app.appliedDate.split("T")[0]}
                      </p>
                    </div>
                    <Badge variant={app.status === "SELECTED" ? "success" : "secondary"}>
                      {app.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No candidate applications recorded.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 5: Offers */}
        <TabsContent value="offers" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Formal Job Offers Released
            </h2>
            {offers.length > 0 ? (
              <div className="space-y-3">
                {offers.map((ofr) => (
                  <div
                    key={ofr.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 flex items-center justify-between"
                  >
                    <div>
                      <span className="font-bold text-xs text-slate-900 dark:text-white">
                        {ofr.studentName} ({ofr.rollNumber})
                      </span>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {ofr.positionTitle} • Joining: {ofr.joiningDate}
                      </p>
                      <p className="text-sm font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                        {formatLPA(ofr.ctcLpa)}
                      </p>
                    </div>
                    <Badge variant={ofr.status === "ACCEPTED" ? "success" : "warning"}>
                      {ofr.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No offers released by this partner yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 6: History */}
        <TabsContent value="history" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Engagement Audit Trail
            </h2>
            <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-4">
              {company.timeline.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-indigo-500 border-2 border-white dark:border-slate-900" />
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {entry.action}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    By {entry.actor} • {new Date(entry.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
