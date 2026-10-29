"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Award,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  Briefcase,
  FileText,
  TrendingUp,
  Users,
  UserCheck,
  ChevronRight,
  ArrowRight,
  AlertTriangle,
  Layers,
  BarChart3,
  Search,
  ExternalLink,
  Shield,
  User,
  Sparkles,
  Percent,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { formatLPA } from "@/services/placement-calculator";
import {
  PlacementDashboardSummary,
  StudentPlacementProfile,
  JobDrive,
  Position,
  Application,
  Interview,
  Offer,
  PlacementOutcome,
} from "@/types/placement";

export default function PlacementOperationsDashboardPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);

  // Active View Mode: Operational Dashboard vs Student "My Placement"
  const [viewMode, setViewMode] = useState<"OPERATIONS" | "STUDENT_PORTAL">(
    "OPERATIONS",
  );

  // Operations Data
  const [summary, setSummary] = useState<PlacementDashboardSummary | null>(
    null,
  );
  const [drives, setDrives] = useState<JobDrive[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [outcomes, setOutcomes] = useState<PlacementOutcome[]>([]);

  // Student Portal Context (simulates Aarav Patel std-001 by default, selectable)
  const [profiles, setProfiles] = useState<StudentPlacementProfile[]>([]);
  const [currentStudentId, setCurrentStudentId] = useState<string>("std-001");

  // Apply Modal state inside Student portal
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applyingDrive, setApplyingDrive] = useState<JobDrive | null>(null);
  const [submittingApp, setSubmittingApp] = useState(false);

  // Student Offer Response modal
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [respondingOffer, setRespondingOffer] = useState<Offer | null>(null);
  const [offerAction, setOfferAction] = useState<"ACCEPT" | "DECLINE">(
    "ACCEPT",
  );
  const [offerNotes, setOfferNotes] = useState("");
  const [processingOffer, setProcessingOffer] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [
        sumRes,
        drivesRes,
        posRes,
        appsRes,
        intvRes,
        ofrRes,
        outRes,
        profsRes,
      ] = await Promise.all([
        placementService.getPlacementSummary(),
        placementService.getJobDrives(),
        placementService.getPositions(),
        placementService.getApplications(),
        placementService.getInterviews(),
        placementService.getOffers(),
        placementService.getPlacementOutcomes(),
        placementService.getPlacementStudents(),
      ]);

      if (sumRes.success && sumRes.data) setSummary(sumRes.data);
      if (drivesRes.success && drivesRes.data) setDrives(drivesRes.data);
      if (posRes.success && posRes.data) setPositions(posRes.data);
      if (appsRes.success && appsRes.data) setApplications(appsRes.data);
      if (intvRes.success && intvRes.data) setInterviews(intvRes.data);
      if (ofrRes.success && ofrRes.data) setOffers(ofrRes.data);
      if (outRes.success && outRes.data) setOutcomes(outRes.data);
      if (profsRes.success && profsRes.data) setProfiles(profsRes.data);
    } catch {
      showToast({
        title: "Error Loading Data",
        message: "Failed to initialize placement operations dashboard",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Selected Student Dossier
  const currentStudent = useMemo(() => {
    return (
      profiles.find((p) => p.studentId === currentStudentId) ||
      profiles[0] ||
      null
    );
  }, [profiles, currentStudentId]);

  // Student-specific data slices
  const studentApplications = useMemo(() => {
    return applications.filter((a) => a.studentId === currentStudentId);
  }, [applications, currentStudentId]);

  const studentInterviews = useMemo(() => {
    return interviews.filter((i) => i.studentId === currentStudentId);
  }, [interviews, currentStudentId]);

  const studentOffers = useMemo(() => {
    return offers.filter((o) => o.studentId === currentStudentId);
  }, [offers, currentStudentId]);

  const studentOutcome = useMemo(() => {
    return outcomes.find((o) => o.studentId === currentStudentId);
  }, [outcomes, currentStudentId]);

  // Student Eligible Drives
  const eligibleDrives = useMemo(() => {
    if (!currentStudent) return [];
    return drives.filter((d) => d.status === "OPEN" || d.status === "UPCOMING");
  }, [drives, currentStudent]);

  // Helpers for drive positions and CTC
  const getDrivePositions = (driveId: string) =>
    positions.filter((p) => p.driveId === driveId);
  const getDriveMaxCtc = (driveId: string) => {
    const dPos = getDrivePositions(driveId);
    if (dPos.length === 0) return 12.0;
    return Math.max(...dPos.map((p) => p.ctcLpa));
  };

  const handleApplyToDrive = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentStudent || !applyingDrive) return;

    try {
      setSubmittingApp(true);
      const dPos = getDrivePositions(applyingDrive.id);
      const position = dPos[0];
      const res = await placementService.submitApplication({
        studentId: currentStudent.studentId,
        driveId: applyingDrive.id,
        positionId: position ? position.id : "pos-001",
      });

      if (res.success) {
        showToast({
          title: "Application Submitted",
          message: `Successfully applied to ${applyingDrive.companyName} for ${applyingDrive.title}`,
          type: "success",
        });
        setShowApplyModal(false);
        await loadData();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to apply";
      showToast({
        title: "Application Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setSubmittingApp(false);
    }
  };

  const handleRespondToOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!respondingOffer) return;

    try {
      setProcessingOffer(true);
      if (offerAction === "ACCEPT") {
        await placementService.acceptOffer(respondingOffer.id, offerNotes);
        showToast({
          title: "Offer Accepted",
          message: `You have formally accepted the appointment from ${respondingOffer.companyName}!`,
          type: "success",
        });
      } else {
        await placementService.declineOffer(
          respondingOffer.id,
          offerNotes || "Offer declined by student",
        );
        showToast({
          title: "Offer Declined",
          message: `Offer from ${respondingOffer.companyName} has been declined.`,
          type: "info",
        });
      }
      setShowOfferModal(false);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Action failed";
      showToast({
        title: "Response Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setProcessingOffer(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-muted-foreground mt-3">
          Loading Placement Operations Center...
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header & Role Switcher */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Award className="w-6 h-6 text-primary" />
              CampusOS Placement Operations Center
            </h1>
            <Badge variant="outline" className="text-xs font-mono">
              Enterprise Hub
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            End-to-end institutional corporate placement lifecycle, candidate
            workflows, eligibility engine, and compensation intelligence.
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2 bg-muted/60 p-1 rounded-xl border">
          <button
            onClick={() => setViewMode("OPERATIONS")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === "OPERATIONS"
                ? "bg-card text-foreground shadow-sm font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Shield className="w-3.5 h-3.5 text-primary" />
            Operations Center (Admin / Officer)
          </button>
          <button
            onClick={() => setViewMode("STUDENT_PORTAL")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === "STUDENT_PORTAL"
                ? "bg-card text-foreground shadow-sm font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <User className="w-3.5 h-3.5 text-emerald-500" />
            My Placement (Student Experience)
          </button>
        </div>
      </div>

      {/* ========================================================
          VIEW 1: PLACEMENT OPERATIONS CENTER
      ======================================================== */}
      {viewMode === "OPERATIONS" && summary && (
        <div className="space-y-6 animate-in fade-in">
          {/* Quick Submodule Navigation Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2">
            {[
              {
                label: "Students",
                href: "/app/placement/students",
                count: summary.eligibleStudentsCount,
                icon: Users,
              },
              {
                label: "Companies",
                href: "/app/placement/companies",
                count: summary.activeCompaniesCount,
                icon: Building2,
              },
              {
                label: "Drives",
                href: "/app/placement/drives",
                count: summary.openDrivesCount,
                icon: Calendar,
              },
              {
                label: "Positions",
                href: "/app/placement/positions",
                count: 8,
                icon: Briefcase,
              },
              {
                label: "Applications",
                href: "/app/placement/applications",
                count: summary.applicationsCount,
                icon: FileText,
              },
              {
                label: "Interviews",
                href: "/app/placement/interviews",
                count: summary.interviewsCount,
                icon: Clock,
              },
              {
                label: "Offers",
                href: "/app/placement/offers",
                count: summary.offersCount,
                icon: Award,
              },
              {
                label: "Outcomes",
                href: "/app/placement/outcomes",
                count: summary.placedStudentsCount,
                icon: CheckCircle2,
              },
              {
                label: "Reports",
                href: "/app/placement/reports",
                count: "Audit",
                icon: BarChart3,
              },
            ].map((mod) => {
              const Icon = mod.icon;
              return (
                <Link
                  key={mod.label}
                  href={mod.href}
                  className="bg-card border rounded-xl p-3 flex flex-col items-center text-center hover:border-primary/50 hover:bg-muted/40 transition-all group shadow-xs"
                >
                  <Icon className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors mb-1" />
                  <span className="text-xs font-semibold text-foreground">
                    {mod.label}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-0.5 font-mono">
                    {mod.count} records
                  </span>
                </Link>
              );
            })}
          </div>

          {/* Section 5: Overview Metrics (8 Canonical Pipeline Metrics) */}
          <div className="space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              Recruitment Pipeline Overview
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Active Companies
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.activeCompaniesCount}
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400">
                  Tier 1 & 2 Partners
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Open Drives
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.openDrivesCount}
                </div>
                <span className="text-[10px] text-blue-600 dark:text-blue-400">
                  Accepting apps
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Eligible Cohort
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.eligibleStudentsCount}
                </div>
                <span className="text-[10px] text-muted-foreground">
                  Class of 2026
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Applications
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.applicationsCount}
                </div>
                <span className="text-[10px] text-muted-foreground">
                  Logged submissions
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Shortlisted
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.shortlistedCount}
                </div>
                <span className="text-[10px] text-purple-600 dark:text-purple-400">
                  Round 1 qualified
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Interviews
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.interviewsCount}
                </div>
                <span className="text-[10px] text-amber-600 dark:text-amber-400">
                  Scheduled / Done
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] text-muted-foreground">
                  Offers Released
                </span>
                <div className="text-xl font-bold text-foreground">
                  {summary.offersCount}
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400">
                  Extended CTCs
                </span>
              </div>
              <div className="bg-card border rounded-xl p-3.5 space-y-1 bg-emerald-500/5 border-emerald-500/20">
                <span className="text-[11px] text-emerald-700 dark:text-emerald-300 font-semibold">
                  Placed Students
                </span>
                <div className="text-xl font-bold text-emerald-700 dark:text-emerald-400">
                  {summary.placedStudentsCount}
                </div>
                <span className="text-[10px] text-emerald-600">
                  {summary.placementRate}% overall rate
                </span>
              </div>
            </div>
          </div>

          {/* Placement Performance Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Placement Rate"
              value={`${summary.placementRate}%`}
              icon={<Percent className="w-5 h-5 text-emerald-500" />}
              description={`${summary.placedStudentsCount} of ${summary.eligibleStudentsCount} students placed`}
            />
            <StatCard
              title="Average Package (CTC)"
              value={`₹${summary.averagePackageLpa} LPA`}
              icon={<DollarSign className="w-5 h-5 text-purple-500" />}
              description={`Median CTC: ₹${summary.medianPackageLpa} LPA across all departments`}
            />
            <StatCard
              title="Highest Package Secured"
              value={`₹${summary.highestPackageLpa} LPA`}
              icon={<Award className="w-5 h-5 text-amber-500" />}
              description="Offered by Google Cloud Software Engineering"
            />
            <StatCard
              title="Offer-to-Placement Rate"
              value={`${summary.offerRate}%`}
              icon={<TrendingUp className="w-5 h-5 text-blue-500" />}
              description={`Shortlist-to-offer conversion rate: ${summary.applicationConversionRate}%`}
            />
          </div>

          {/* Operational Action Queues & Funnel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Operational Action Queues */}
            <Card className="lg:col-span-1">
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-sm font-semibold flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-primary" />
                    Operational Action Queues
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    Action Required
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                {[
                  {
                    label: "Upcoming Drives this Month",
                    count: summary.operationalQueues.upcomingDrivesCount,
                    href: "/app/placement/drives",
                    color: "text-blue-500",
                  },
                  {
                    label: "Eligibility Overrides / Reviews",
                    count: summary.operationalQueues.eligibilityReviewsCount,
                    href: "/app/placement/applications",
                    color: "text-amber-500",
                  },
                  {
                    label: "Applications Pending Review",
                    count: summary.operationalQueues.pendingApplicationsCount,
                    href: "/app/placement/applications",
                    color: "text-purple-500",
                  },
                  {
                    label: "Interviews Scheduled Today",
                    count: summary.operationalQueues.interviewsTodayCount,
                    href: "/app/placement/interviews",
                    color: "text-emerald-500",
                  },
                  {
                    label: "Offers Awaiting Candidate Response",
                    count:
                      summary.operationalQueues.offersAwaitingResponseCount,
                    href: "/app/placement/offers",
                    color: "text-rose-500",
                  },
                  {
                    label: "Recent Placements Confirmed",
                    count: summary.operationalQueues.recentPlacementsCount,
                    href: "/app/placement/outcomes",
                    color: "text-emerald-600",
                  },
                ].map((queue) => (
                  <Link
                    key={queue.label}
                    href={queue.href}
                    className="flex items-center justify-between p-2.5 rounded-lg border bg-muted/20 hover:bg-muted/50 transition-colors text-xs group"
                  >
                    <span className="text-foreground group-hover:text-primary transition-colors font-medium">
                      {queue.label}
                    </span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-bold font-mono text-sm ${queue.color}`}
                      >
                        {queue.count}
                      </span>
                      <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </Link>
                ))}
              </CardContent>
            </Card>

            {/* Department Breakdown */}
            <Card className="lg:col-span-2">
              <CardHeader className="pb-3 border-b flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-primary" />
                  Department Placement Performance Audit
                </CardTitle>
                <Link href="/app/placement/reports">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs gap-1"
                  >
                    Full Report
                    <ArrowRight className="w-3 h-3" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="pt-4 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/40 border-b">
                    <tr>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Department
                      </th>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Eligible
                      </th>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Placed
                      </th>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Rate
                      </th>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Avg Package
                      </th>
                      <th className="px-3 py-2 font-semibold text-muted-foreground">
                        Highest
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {summary.departmentStats.map((ds) => (
                      <tr key={ds.department} className="hover:bg-muted/20">
                        <td className="px-3 py-2.5 font-medium text-foreground">
                          {ds.department}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {ds.totalStudents}
                        </td>
                        <td className="px-3 py-2.5 font-semibold text-foreground">
                          {ds.placedStudents}
                        </td>
                        <td className="px-3 py-2.5">
                          <Badge
                            variant="outline"
                            className={`text-[10px] ${
                              ds.placementRate >= 80
                                ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                : "bg-blue-500/10 text-blue-600 border-blue-500/20"
                            }`}
                          >
                            {ds.placementRate}%
                          </Badge>
                        </td>
                        <td className="px-3 py-2.5 font-medium text-emerald-600 dark:text-emerald-400">
                          ₹{ds.averageCtcLpa} LPA
                        </td>
                        <td className="px-3 py-2.5 font-semibold text-foreground">
                          ₹{ds.highestCtcLpa} LPA
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>

          {/* Compensation Slab Distribution */}
          <div className="bg-card border rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center justify-between">
              <span className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-500" />
                Compensation Slab Distribution (CTC)
              </span>
              <span className="text-xs text-muted-foreground font-normal">
                Batch of 2026-2027
              </span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {summary.packageDistribution.map((bucket) => (
                <div
                  key={bucket.range}
                  className="bg-muted/30 border rounded-xl p-4 space-y-2 relative overflow-hidden"
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-semibold text-foreground">
                      {bucket.range}
                    </span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {bucket.percentage}%
                    </Badge>
                  </div>
                  <div className="text-2xl font-bold text-foreground">
                    {bucket.count} offers
                  </div>
                  <div className="w-full bg-border h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-primary h-full rounded-full transition-all"
                      style={{ width: `${bucket.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          VIEW 2: STUDENT PLACEMENT EXPERIENCE ("MY PLACEMENT")
      ======================================================== */}
      {viewMode === "STUDENT_PORTAL" && (
        <div className="space-y-6 animate-in fade-in">
          {/* Student Selector Toolbar */}
          <div className="bg-card border rounded-xl p-4 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center font-bold text-primary">
                {currentStudent?.studentName.charAt(0) || "S"}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-foreground">
                    {currentStudent?.studentName}
                  </h2>
                  <Badge variant="outline" className="text-xs font-mono">
                    {currentStudent?.rollNumber}
                  </Badge>
                  <Badge
                    className={`text-xs ${
                      currentStudent?.placementStatus === "PLACED"
                        ? "bg-emerald-500/15 text-emerald-600 border-emerald-500/30"
                        : "bg-blue-500/15 text-blue-600 border-blue-500/30"
                    }`}
                  >
                    {currentStudent?.placementStatus}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {currentStudent?.program} • {currentStudent?.department} •
                  CGPA: {currentStudent?.cgpa} • Backlogs:{" "}
                  {currentStudent?.activeBacklogs}
                </p>
              </div>
            </div>

            {/* Candidate Simulator Dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                Switch Candidate Dossier:
              </span>
              <select
                value={currentStudentId}
                onChange={(e) => setCurrentStudentId(e.target.value)}
                className="h-8 text-xs rounded-lg border bg-background px-2 text-foreground font-medium"
              >
                {profiles.map((p) => (
                  <option key={p.studentId} value={p.studentId}>
                    {p.studentName} ({p.rollNumber} - {p.placementStatus})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Student KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="bg-card border rounded-xl p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground">
                Profile Status
              </span>
              <div className="text-base font-bold text-foreground flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                {currentStudent?.status}
              </div>
              <span className="text-[10px] text-muted-foreground">
                {currentStudent?.profileCompletionPercent}% complete
              </span>
            </div>
            <div className="bg-card border rounded-xl p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground">
                Resume Dossier
              </span>
              <div className="text-base font-bold text-foreground">
                <Badge variant="outline" className="text-[10px]">
                  {currentStudent?.resumeStatus}
                </Badge>
              </div>
              <span className="text-[10px] text-muted-foreground">
                Verified by Placement Office
              </span>
            </div>
            <div className="bg-card border rounded-xl p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground">
                Eligible Drives
              </span>
              <div className="text-base font-bold text-primary">
                {eligibleDrives.length}
              </div>
              <span className="text-[10px] text-muted-foreground">
                Open for submission
              </span>
            </div>
            <div className="bg-card border rounded-xl p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground">
                Applications
              </span>
              <div className="text-base font-bold text-foreground">
                {studentApplications.length}
              </div>
              <span className="text-[10px] text-muted-foreground">
                In active pipeline
              </span>
            </div>
            <div className="bg-card border rounded-xl p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground">
                Interviews
              </span>
              <div className="text-base font-bold text-foreground">
                {studentInterviews.length}
              </div>
              <span className="text-[10px] text-muted-foreground">
                Rounds scheduled
              </span>
            </div>
            <div className="bg-card border rounded-xl p-3.5 space-y-1 bg-emerald-500/5 border-emerald-500/20">
              <span className="text-[11px] text-emerald-700 dark:text-emerald-300 font-semibold">
                Corporate Offers
              </span>
              <div className="text-base font-bold text-emerald-700 dark:text-emerald-400">
                {studentOffers.length}
              </div>
              <span className="text-[10px] text-emerald-600">
                {studentOffers.filter((o) => o.status === "ACCEPTED").length}{" "}
                accepted
              </span>
            </div>
          </div>

          {/* Eligible Drives for this Student */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                Eligible Recruitment Drives (Apply Now)
              </h3>
              <span className="text-xs text-muted-foreground">
                Matches program, CGPA ({currentStudent?.cgpa}), and backlog
                criteria
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {eligibleDrives.map((drive) => {
                const alreadyApplied = studentApplications.some(
                  (a) => a.driveId === drive.id,
                );
                const dPos = getDrivePositions(drive.id);
                const maxCtc = getDriveMaxCtc(drive.id);
                return (
                  <div
                    key={drive.id}
                    className="bg-card border rounded-xl p-4 space-y-3 shadow-xs flex flex-col justify-between hover:border-primary/40 transition-all"
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 text-primary" />
                            {drive.companyName}
                          </span>
                          <h4 className="text-sm font-bold text-foreground mt-0.5">
                            {drive.title}
                          </h4>
                        </div>
                        <Badge
                          variant="outline"
                          className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-[10px]"
                        >
                          Eligible
                        </Badge>
                      </div>

                      <div className="text-xs space-y-1 text-muted-foreground pt-1 border-t">
                        <div className="flex justify-between">
                          <span>Positions:</span>
                          <span className="font-medium text-foreground">
                            {dPos.map((p) => p.title).join(", ") ||
                              "General Engineering"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Package (CTC):</span>
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                            {formatLPA(maxCtc)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Deadline:</span>
                          <span className="font-medium text-foreground">
                            {drive.applicationDeadline}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 border-t flex items-center justify-between">
                      <Link href={`/app/placement/drives/${drive.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1"
                        >
                          Drive Details
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>

                      {alreadyApplied ? (
                        <Badge
                          variant="outline"
                          className="bg-blue-500/10 text-blue-600 border-blue-500/20 text-xs"
                        >
                          Applied
                        </Badge>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => {
                            setApplyingDrive(drive);
                            setShowApplyModal(true);
                          }}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground h-8 text-xs gap-1"
                        >
                          Apply
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Student's Current Applications */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              My Applications & Pipeline Progression
            </h3>

            {studentApplications.length === 0 ? (
              <div className="bg-card border rounded-xl p-8 text-center text-xs text-muted-foreground">
                No job applications submitted yet. Browse the eligible drives
                above to submit an application.
              </div>
            ) : (
              <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/40 border-b">
                    <tr>
                      <th className="px-4 py-3 font-semibold text-muted-foreground">
                        Company & Role
                      </th>
                      <th className="px-4 py-3 font-semibold text-muted-foreground">
                        Applied Date
                      </th>
                      <th className="px-4 py-3 font-semibold text-muted-foreground">
                        Status
                      </th>
                      <th className="px-4 py-3 font-semibold text-muted-foreground">
                        Current Stage
                      </th>
                      <th className="px-4 py-3 font-semibold text-muted-foreground text-right">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {studentApplications.map((app) => (
                      <tr key={app.id} className="hover:bg-muted/20">
                        <td className="px-4 py-3">
                          <div className="font-semibold text-foreground">
                            {app.companyName}
                          </div>
                          <span className="text-[11px] text-muted-foreground">
                            {app.positionTitle}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {app.appliedDate}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-[11px]">
                            {app.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 font-medium text-foreground">
                          {app.currentStage}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Link href={`/app/placement/applications/${app.id}`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs gap-1"
                            >
                              View Snapshot
                              <ChevronRight className="w-3 h-3" />
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Student's Corporate Offers */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-500" />
              Corporate Job Offers & Decision Desk
            </h3>

            {studentOffers.length === 0 ? (
              <div className="bg-card border rounded-xl p-8 text-center text-xs text-muted-foreground">
                No formal job offers released yet. Keep completing your
                interview stages.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {studentOffers.map((offer) => (
                  <div
                    key={offer.id}
                    className="bg-card border rounded-xl p-5 space-y-4 shadow-sm border-l-4 border-l-emerald-500"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs text-muted-foreground font-mono">
                          {offer.offerCode}
                        </span>
                        <h4 className="text-base font-bold text-foreground flex items-center gap-1.5 mt-0.5">
                          <Building2 className="w-4 h-4 text-primary" />
                          {offer.companyName}
                        </h4>
                        <span className="text-xs text-muted-foreground">
                          {offer.positionTitle}
                        </span>
                      </div>
                      <Badge
                        className={
                          offer.status === "ACCEPTED"
                            ? "bg-emerald-500/15 text-emerald-600 border-emerald-500/30"
                            : offer.status === "RELEASED"
                              ? "bg-blue-500/15 text-blue-600 border-blue-500/30"
                              : "bg-rose-500/15 text-rose-600 border-rose-500/30"
                        }
                      >
                        {offer.status}
                      </Badge>
                    </div>

                    <div className="bg-muted/30 p-3 rounded-lg flex justify-between items-center text-xs">
                      <div>
                        <span className="text-muted-foreground">
                          Total Package (CTC)
                        </span>
                        <div className="text-lg font-extrabold text-emerald-600 dark:text-emerald-400">
                          {formatLPA(offer.ctcLpa)}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-muted-foreground">
                          Base Fixed
                        </span>
                        <div className="font-semibold text-foreground">
                          {formatLPA(offer.baseSalaryLpa)}
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>Joining: {offer.joiningDate}</span>
                      <span>Deadline: {offer.responseDeadline}</span>
                    </div>

                    {offer.status === "RELEASED" && (
                      <div className="pt-2 border-t flex items-center justify-end gap-2">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => {
                            setRespondingOffer(offer);
                            setOfferAction("DECLINE");
                            setShowOfferModal(true);
                          }}
                          className="h-8 text-xs"
                        >
                          Decline
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => {
                            setRespondingOffer(offer);
                            setOfferAction("ACCEPT");
                            setShowOfferModal(true);
                          }}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs"
                        >
                          Accept Offer
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================
          STUDENT APPLY WORKFLOW MODAL
      ======================================================== */}
      {showApplyModal && applyingDrive && currentStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-primary" />
                  Submit Recruitment Application
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Review requirements and submit dossier to{" "}
                  {applyingDrive.companyName}
                </p>
              </div>
              <button
                onClick={() => setShowApplyModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-muted/30 rounded-lg space-y-1.5 border">
                <div className="font-semibold text-foreground">
                  Drive & Role Details:
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Corporate Partner:
                  </span>
                  <span className="font-medium text-foreground">
                    {applyingDrive.companyName}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Position:</span>
                  <span className="font-medium text-foreground">
                    {getDrivePositions(applyingDrive.id)[0]?.title ||
                      applyingDrive.title}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">CTC Package:</span>
                  <span className="font-semibold text-emerald-600">
                    {formatLPA(getDriveMaxCtc(applyingDrive.id))}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Application Deadline:
                  </span>
                  <span className="font-medium text-foreground">
                    {applyingDrive.applicationDeadline}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg space-y-1">
                <div className="font-semibold text-foreground flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Eligibility Status: Verified
                </div>
                <p className="text-muted-foreground text-[11px]">
                  Your academic record (CGPA {currentStudent.cgpa}, Backlogs:{" "}
                  {currentStudent.activeBacklogs}) meets the criteria for this
                  recruitment event.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowApplyModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleApplyToDrive}
                disabled={submittingApp}
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                {submittingApp
                  ? "Submitting..."
                  : "Confirm & Submit Application"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          STUDENT OFFER DECISION MODAL
      ======================================================== */}
      {showOfferModal && respondingOffer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-base font-bold text-foreground">
                {offerAction === "ACCEPT"
                  ? "Accept Appointment Offer"
                  : "Decline Appointment Offer"}
              </h2>
              <button
                onClick={() => setShowOfferModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="text-xs space-y-2">
              <div className="p-3 bg-muted/40 rounded-lg border space-y-1">
                <div className="text-muted-foreground">
                  <strong>Company:</strong> {respondingOffer.companyName}
                </div>
                <div className="text-muted-foreground">
                  <strong>Position:</strong> {respondingOffer.positionTitle}
                </div>
                <div className="text-muted-foreground">
                  <strong>Compensation:</strong>{" "}
                  {formatLPA(respondingOffer.ctcLpa)}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">
                  {offerAction === "ACCEPT"
                    ? "Remarks / Acceptance Note"
                    : "Reason for Declining"}
                </label>
                <textarea
                  rows={3}
                  value={offerNotes}
                  onChange={(e) => setOfferNotes(e.target.value)}
                  placeholder={
                    offerAction === "ACCEPT"
                      ? "e.g. Delighted to join. Thank you for this opportunity."
                      : "e.g. Opting for higher studies / accepted competing offer"
                  }
                  className="w-full text-xs p-2.5 rounded-lg border bg-background text-foreground"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowOfferModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleRespondToOffer}
                disabled={processingOffer}
                className={
                  offerAction === "ACCEPT"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                    : "bg-rose-600 hover:bg-rose-700 text-white"
                }
              >
                {processingOffer
                  ? "Processing..."
                  : offerAction === "ACCEPT"
                    ? "Confirm Acceptance"
                    : "Confirm Decline"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
