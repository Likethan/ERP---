"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Briefcase,
  Calendar,
  Clock,
  Building2,
  Users,
  Award,
  ChevronLeft,
  FileCheck2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Layers,
  MapPin,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { formatLPA } from "@/services/placement-calculator";
import {
  JobDrive,
  Position,
  Application,
  Interview,
  Offer,
  DriveStatus,
} from "@/types/placement";

export default function JobDriveDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const driveId = params?.id as string;

  const [drive, setDrive] = useState<JobDrive | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [driveRes, posRes, appsRes, intvRes, ofrRes] = await Promise.all([
        placementService.getJobDriveById(driveId),
        placementService.getPositions(driveId),
        placementService.getApplications({ driveId }),
        placementService.getInterviews(),
        placementService.getOffers(),
      ]);

      if (!driveRes.data) {
        showToast({
          title: "Not Found",
          message: "Job drive not found",
          type: "error",
        });
        router.push("/app/placement/drives");
        return;
      }

      setDrive(driveRes.data);
      setPositions(posRes.data || []);
      setApplications(appsRes.data || []);
      setInterviews(
        (intvRes.data || []).filter(
          (i) => i.companyId === driveRes.data?.companyId,
        ),
      );
      setOffers(
        (ofrRes.data || []).filter(
          (o) => o.companyId === driveRes.data?.companyId,
        ),
      );
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load drive details",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (driveId) {
      loadData();
    }
  }, [driveId]);

  const handlePublishDrive = async () => {
    if (!drive) return;
    try {
      await placementService.publishJobDrive(drive.id);
      showToast({
        title: "Drive Published",
        message: "Applications are now OPEN to all eligible students.",
        type: "success",
      });
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to publish drive",
        type: "error",
      });
    }
  };

  const handleCloseDrive = async () => {
    if (!drive) return;
    try {
      await placementService.closeJobDrive(drive.id);
      showToast({
        title: "Drive Closed",
        message: "Applications closed for this recruitment cycle.",
        type: "info",
      });
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to close drive",
        type: "error",
      });
    }
  };

  const handleShortlistApplicant = async (appId: string) => {
    try {
      await placementService.shortlistApplications(
        [appId],
        "Placement Officer",
      );
      showToast({
        title: "Candidate Shortlisted",
        message: "Moved to technical interview pipeline",
        type: "success",
      });
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to shortlist candidate",
        type: "error",
      });
    }
  };

  if (loading || !drive) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">
            Loading campus drive operations center...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/placement/drives"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Job Drives
        </Link>
      </div>

      {/* Header Profile Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              <Briefcase className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {drive.title}
                </h1>
                <Badge
                  variant={
                    drive.status === "OPEN"
                      ? "success"
                      : drive.status === "UPCOMING"
                        ? "warning"
                        : "secondary"
                  }
                  dot
                >
                  {drive.status}
                </Badge>
                <Badge variant="outline">
                  {drive.companyTier.replace(/_/g, " ")}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <span className="font-mono font-medium">{drive.code}</span>
                <span>•</span>
                <Link
                  href={`/app/placement/companies/${drive.companyId}`}
                  className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  {drive.companyName}
                </Link>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {drive.location}
                </span>
                <span>•</span>
                <span>Drive Date: {drive.driveDate}</span>
                <span>•</span>
                <span className="text-rose-600 dark:text-rose-400 font-semibold">
                  Deadline: {drive.applicationDeadline}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {drive.status === "DRAFT" || drive.status === "UPCOMING" ? (
              <Button
                variant="primary"
                size="sm"
                onClick={handlePublishDrive}
                className="gap-1.5 text-xs"
              >
                <Check className="w-3.5 h-3.5" />
                Publish & Open Applications
              </Button>
            ) : drive.status === "OPEN" ? (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCloseDrive}
                className="gap-1.5 text-xs text-rose-600 border-rose-300"
              >
                <Clock className="w-3.5 h-3.5" />
                Close Applications
              </Button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-100 p-1 dark:bg-slate-800">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="positions">
            Positions ({positions.length})
          </TabsTrigger>
          <TabsTrigger value="applicants">
            Applicants ({applications.length})
          </TabsTrigger>
          <TabsTrigger value="interviews">
            Interviews ({interviews.length})
          </TabsTrigger>
          <TabsTrigger value="offers">Offers ({offers.length})</TabsTrigger>
          <TabsTrigger value="timeline">Governance Timeline</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Eligible Students"
              value={drive.eligibleStudentsCount}
              icon={<Users className="w-5 h-5 text-indigo-500" />}
              description="Batch of 2026 meeting criteria"
            />
            <StatCard
              title="Applications Submitted"
              value={applications.length}
              icon={<FileCheck2 className="w-5 h-5 text-sky-500" />}
              description={`${drive.applicantsCount} student submissions`}
            />
            <StatCard
              title="Candidates Shortlisted"
              value={
                applications.filter(
                  (a) => a.status === "SHORTLISTED" || a.status === "SELECTED",
                ).length
              }
              icon={<Award className="w-5 h-5 text-amber-500" />}
              description="Advanced to interview rounds"
            />
            <StatCard
              title="Final Offers"
              value={offers.length}
              icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
              description="Released job offers"
            />
          </div>

          {/* Description & Guidelines */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Drive Brief & Student Instructions
            </h2>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              {drive.description}
            </p>
            {drive.guidelines && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 dark:bg-amber-950/20 dark:border-amber-800 dark:text-amber-200 text-xs">
                <strong>Important Guidelines:</strong> {drive.guidelines}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Tab 2: Positions */}
        <TabsContent value="positions" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Recruitment Positions & Eligibility Criteria
            </h2>
            <div className="space-y-4">
              {positions.map((pos) => (
                <div
                  key={pos.id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                        {pos.title}
                      </h4>
                      <p className="text-xs text-slate-500">
                        {pos.departmentFunction}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold font-mono text-emerald-600 dark:text-emerald-400 text-sm">
                        {formatLPA(pos.ctcLpa)}
                      </span>
                      <p className="text-[11px] text-slate-500">
                        Base: {formatLPA(pos.baseSalaryLpa)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-2 border-t border-slate-200 dark:border-slate-700">
                    <div>
                      <span className="text-slate-500">Min CGPA:</span>{" "}
                      <strong className="text-slate-900 dark:text-white">
                        {pos.minCgpa}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-500">Max Backlogs:</span>{" "}
                      <strong className="text-slate-900 dark:text-white">
                        {pos.maxBacklogs}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-500">Vacancies:</span>{" "}
                      <strong className="text-slate-900 dark:text-white">
                        {pos.vacancies} open
                      </strong>
                    </div>
                  </div>

                  <div>
                    <span className="text-xs text-slate-500">
                      Mandatory Skills:
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {pos.requiredSkills.map((s) => (
                        <span
                          key={s}
                          className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Tab 3: Applicants */}
        <TabsContent value="applicants" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Registered Candidate Submissions
            </h2>
            {applications.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {applications.map((app) => (
                  <div
                    key={app.id}
                    className="py-3 flex items-center justify-between"
                  >
                    <div>
                      <Link
                        href={`/app/placement/applications/${app.id}`}
                        className="text-xs font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                      >
                        {app.studentName} ({app.rollNumber})
                      </Link>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {app.program} • CGPA: {app.cgpa.toFixed(2)} • Applied:{" "}
                        {app.appliedDate.split("T")[0]}
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          app.status === "SELECTED"
                            ? "success"
                            : app.status === "SHORTLISTED"
                              ? "info"
                              : "secondary"
                        }
                      >
                        {app.status}
                      </Badge>
                      {app.status === "SUBMITTED" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleShortlistApplicant(app.id)}
                          className="h-7 text-xs"
                        >
                          Shortlist
                        </Button>
                      )}
                      <Link href={`/app/placement/applications/${app.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs"
                        >
                          Review
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                No student applications submitted yet.
              </p>
            )}
          </div>
        </TabsContent>

        {/* Tab 4: Interviews */}
        <TabsContent value="interviews" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Scheduled Interview Panels
            </h2>
            {interviews.length > 0 ? (
              <div className="space-y-3">
                {interviews.map((intv) => (
                  <div
                    key={intv.id}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {intv.studentName} — {intv.stage} Round{" "}
                        {intv.roundNumber}
                      </span>
                      <p className="text-slate-500 mt-0.5">
                        {intv.date} at {intv.time} • Mode: {intv.mode}
                      </p>
                    </div>
                    <Badge
                      variant={
                        intv.status === "COMPLETED" ? "success" : "warning"
                      }
                    >
                      {intv.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                No interviews scheduled yet for this drive.
              </p>
            )}
          </div>
        </TabsContent>

        {/* Tab 5: Offers */}
        <TabsContent value="offers" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Offers Extended
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
                    <Badge
                      variant={
                        ofr.status === "ACCEPTED" ? "success" : "warning"
                      }
                    >
                      {ofr.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No offers extended yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 6: Timeline */}
        <TabsContent value="timeline" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Governance & Execution History
            </h2>
            <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-4">
              {drive.timeline.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-indigo-500 border-2 border-white dark:border-slate-900" />
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {entry.action}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    By {entry.actor} •{" "}
                    {new Date(entry.timestamp).toLocaleString()}
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
