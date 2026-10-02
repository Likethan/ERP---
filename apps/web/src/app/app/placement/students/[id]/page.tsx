"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  User,
  GraduationCap,
  Briefcase,
  FileCheck2,
  Calendar,
  Award,
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  Clock,
  Building2,
  ShieldCheck,
  FileText,
  ExternalLink,
  Edit3,
  Layers,
  Check,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { formatLPA } from "@/services/placement-calculator";
import {
  StudentPlacementProfile,
  Application,
  Interview,
  Offer,
  PlacementOutcome,
  ResumeStatus,
} from "@/types/placement";

export default function StudentPlacementProfileDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const studentId = params?.id as string;

  const [profile, setProfile] = useState<StudentPlacementProfile | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [outcome, setOutcome] = useState<PlacementOutcome | null>(null);
  const [loading, setLoading] = useState(true);

  // Resume status update modal
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [newResumeStatus, setNewResumeStatus] = useState<ResumeStatus>("VERIFIED");
  const [resumeReviewNotes, setResumeReviewNotes] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [profRes, appsRes, intvRes, ofrRes, outRes] = await Promise.all([
        placementService.getPlacementStudentById(studentId),
        placementService.getApplications({ studentId }),
        placementService.getInterviews({ studentId }),
        placementService.getOffers({ studentId }),
        placementService.getPlacementOutcomeByStudent(studentId),
      ]);

      if (!profRes.data) {
        showToast({ title: "Not Found", message: "Student placement profile not found", type: "error" });
        router.push("/app/placement/students");
        return;
      }

      setProfile(profRes.data);
      setApplications(appsRes.data || []);
      setInterviews(intvRes.data || []);
      setOffers(ofrRes.data || []);
      setOutcome(outRes.data || null);
    } catch {
      showToast({ title: "Error", message: "Failed to load student placement 360 profile", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const handleUpdateResume = async () => {
    if (!profile) return;
    try {
      await placementService.updateResumeStatus(profile.studentId, newResumeStatus, resumeReviewNotes);
      showToast({ title: "Updated", message: `Resume status updated to ${newResumeStatus}`, type: "success" });
      setShowResumeModal(false);
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to update resume status", type: "error" });
    }
  };

  if (loading || !profile) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading student placement 360° dossier...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/placement/students"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Students Roster
        </Link>
      </div>

      {/* Header Profile Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              {profile.studentName.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {profile.studentName}
                </h1>
                {profile.placementStatus === "PLACED" ? (
                  <Badge variant="success" dot>
                    PLACED — {profile.placedCompany}
                  </Badge>
                ) : profile.placementStatus === "IN_PROCESS" ? (
                  <Badge variant="warning" dot>
                    IN RECRUITMENT
                  </Badge>
                ) : (
                  <Badge variant="secondary" dot>
                    NOT PLACED
                  </Badge>
                )}
                <Badge variant="outline">
                  Resume: {profile.resumeStatus.replace("_", " ")}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <span className="font-mono font-medium">{profile.rollNumber}</span>
                <span>•</span>
                <span>{profile.program}</span>
                <span>•</span>
                <span>Class of {profile.graduationYear} (Semester {profile.currentSemester})</span>
                <span>•</span>
                <span>{profile.email}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setNewResumeStatus(profile.resumeStatus);
                setResumeReviewNotes(profile.resumeNotes || "");
                setShowResumeModal(true);
              }}
              className="gap-1.5 text-xs"
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              Verify Resume
            </Button>
            <Link href={`/app/students/${profile.studentId}`}>
              <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                <User className="w-3.5 h-3.5" />
                Academic 360°
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-100 p-1 dark:bg-slate-800">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="academic">Academic & Eligibility</TabsTrigger>
          <TabsTrigger value="skills">Technical Skills</TabsTrigger>
          <TabsTrigger value="resume">Resume Verification</TabsTrigger>
          <TabsTrigger value="applications">Applications ({applications.length})</TabsTrigger>
          <TabsTrigger value="interviews">Interviews ({interviews.length})</TabsTrigger>
          <TabsTrigger value="offers">Offers ({offers.length})</TabsTrigger>
          <TabsTrigger value="timeline">Audit Timeline</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Academic CGPA"
              value={`${profile.cgpa.toFixed(2)} / 10.0`}
              icon={<GraduationCap className="w-5 h-5 text-indigo-500" />}
              description={`${profile.activeBacklogs} active backlogs`}
            />
            <StatCard
              title="Applications Submitted"
              value={profile.applicationsCount}
              icon={<FileCheck2 className="w-5 h-5 text-sky-500" />}
              description={`${profile.shortlistsCount} shortlisted`}
            />
            <StatCard
              title="Interview Rounds"
              value={profile.interviewsCount}
              icon={<Calendar className="w-5 h-5 text-amber-500" />}
              description="Technical & HR panels"
            />
            <StatCard
              title="Offers Received"
              value={profile.offersCount}
              icon={<Award className="w-5 h-5 text-emerald-500" />}
              description={profile.placedPackageLpa ? `Highest: ${formatLPA(profile.placedPackageLpa)}` : "Awaiting final offers"}
            />
          </div>

          {/* Placement Status Callout */}
          {profile.placementStatus === "PLACED" && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-6 dark:bg-emerald-950/20 dark:border-emerald-800/60">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-emerald-500 text-white shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-emerald-900 dark:text-emerald-200">
                    Candidate Confirmed & Placed at {profile.placedCompany}
                  </h3>
                  <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-1">
                    Formal offer letter accepted. Compensation:{" "}
                    <strong>{formatLPA(profile.placedPackageLpa || 0)}</strong>. Target joining date scheduled for July 2027.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Core Skills Snapshot */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Key Competencies & Skill Matrix
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-xs font-semibold text-slate-500">Programming Languages:</span>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {profile.skills.programmingLanguages.map((l) => (
                    <span
                      key={l}
                      className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200"
                    >
                      {l}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-500">Technical Domains & Frameworks:</span>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {profile.skills.technical.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
                    >
                      {t}
                    </span>
                  ))}
                  {profile.skills.toolsAndFrameworks.map((tool) => (
                    <span
                      key={tool}
                      className="px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 2: Academic */}
        <TabsContent value="academic" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Academic Eligibility Parameters
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="space-y-1">
                <span className="text-xs text-slate-500">Cumulative GPA (CGPA)</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white font-mono">
                  {profile.cgpa.toFixed(2)}
                </p>
                <p className="text-[11px] text-slate-500">Scale of 10.0</p>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-slate-500">Active Backlogs</span>
                <p
                  className={`text-lg font-bold font-mono ${
                    profile.activeBacklogs === 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {profile.activeBacklogs} Backlogs
                </p>
                <p className="text-[11px] text-slate-500">Historical Backlogs: {profile.historyBacklogs}</p>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-slate-500">Academic Attendance</span>
                <p
                  className={`text-lg font-bold font-mono ${
                    profile.attendancePercent >= 75 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"
                  }`}
                >
                  {profile.attendancePercent}%
                </p>
                <p className="text-[11px] text-slate-500">Institutional Threshold: 75%</p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 3: Skills */}
        <TabsContent value="skills" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2">
                Programming Languages
              </h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills.programmingLanguages.map((item) => (
                  <span
                    key={item}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2">
                Technical Architecture & Frameworks
              </h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills.technical.map((item) => (
                  <span
                    key={item}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
                  >
                    {item}
                  </span>
                ))}
                {profile.skills.toolsAndFrameworks.map((item) => (
                  <span
                    key={item}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2">
                Industry Certifications
              </h3>
              <div className="space-y-2">
                {profile.skills.certifications.length > 0 ? (
                  profile.skills.certifications.map((cert) => (
                    <div
                      key={cert}
                      className="flex items-center gap-2 text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-100 dark:bg-slate-800/60 dark:border-slate-700"
                    >
                      <Award className="w-4 h-4 text-amber-500" />
                      <span className="font-medium text-slate-800 dark:text-slate-200">{cert}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500">No certifications recorded.</p>
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 4: Resume */}
        <TabsContent value="resume" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Verified Candidate Resume
            </h2>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-indigo-500 text-white">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    {profile.studentName.replace(/\s+/g, "_")}_Resume_2026.pdf
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Last updated: {profile.resumeUpdatedAt || "Recently"} • Status:{" "}
                    <strong>{profile.resumeStatus}</strong>
                  </p>
                  {profile.resumeNotes && (
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 italic">
                      Reviewer Notes: "{profile.resumeNotes}"
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowResumeModal(true)}
                  className="gap-1.5 text-xs"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  Review & Verify
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 5: Applications */}
        <TabsContent value="applications" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Recruitment Drive Applications
            </h2>
            {applications.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {applications.map((app) => (
                  <div key={app.id} className="py-3 flex items-center justify-between">
                    <div>
                      <Link
                        href={`/app/placement/applications/${app.id}`}
                        className="text-xs font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                      >
                        {app.companyName} — {app.positionTitle}
                      </Link>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Code: {app.applicationCode} • Applied: {app.appliedDate.split("T")[0]}
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          app.status === "SELECTED"
                            ? "success"
                            : app.status === "SHORTLISTED"
                            ? "info"
                            : app.status === "REJECTED"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {app.status}
                      </Badge>
                      <Link href={`/app/placement/applications/${app.id}`}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs">
                          Inspect
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No applications submitted yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 6: Interviews */}
        <TabsContent value="interviews" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Scheduled & Completed Interviews
            </h2>
            {interviews.length > 0 ? (
              <div className="space-y-3">
                {interviews.map((intv) => (
                  <div
                    key={intv.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-slate-900 dark:text-white">
                          {intv.companyName} ({intv.stage} Round {intv.roundNumber})
                        </span>
                        <Badge
                          variant={
                            intv.status === "COMPLETED"
                              ? "success"
                              : intv.status === "SCHEDULED"
                              ? "warning"
                              : "secondary"
                          }
                        >
                          {intv.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {intv.date} at {intv.time} • Panel: {intv.interviewerName}
                      </p>
                      {intv.evaluation && (
                        <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1 font-medium">
                          Result: {intv.evaluation.overallRecommendation} — "{intv.evaluation.notes}"
                        </p>
                      )}
                    </div>

                    <Link href={`/app/placement/interviews/${intv.id}`}>
                      <Button variant="outline" size="sm" className="text-xs">
                        Evaluation Dossier
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No interviews scheduled yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 7: Offers */}
        <TabsContent value="offers" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Corporate Job Offers
            </h2>
            {offers.length > 0 ? (
              <div className="space-y-3">
                {offers.map((ofr) => (
                  <div
                    key={ofr.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-800/40 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 dark:text-white">
                          {ofr.companyName}
                        </span>
                        <Badge
                          variant={
                            ofr.status === "ACCEPTED"
                              ? "success"
                              : ofr.status === "RELEASED"
                              ? "warning"
                              : "secondary"
                          }
                        >
                          {ofr.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Role: {ofr.positionTitle} • Joining: {ofr.joiningDate}
                      </p>
                      <p className="text-sm font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                        {formatLPA(ofr.ctcLpa)} (Base: {formatLPA(ofr.baseSalaryLpa)})
                      </p>
                    </div>

                    <Link href={`/app/placement/offers/${ofr.id}`}>
                      <Button variant="outline" size="sm" className="text-xs">
                        View Offer Letter
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No offers released yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Tab 8: Timeline */}
        <TabsContent value="timeline" className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Chronological Placement Audit History
            </h2>
            <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-6">
              {profile.timeline.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-indigo-500 border-2 border-white dark:border-slate-900" />
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {entry.action}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    By {entry.actor} • {new Date(entry.timestamp).toLocaleString()}
                  </div>
                  {entry.details && (
                    <div className="text-xs text-slate-600 dark:text-slate-300 mt-1 bg-slate-50 dark:bg-slate-800 p-2 rounded">
                      {entry.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Verify Resume Modal */}
      {showResumeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Review & Verify Resume</h3>
            <p className="text-xs text-slate-400">
              Set candidate resume status and add placement cell review notes.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium">Resume Verification Decision</label>
                <select
                  value={newResumeStatus}
                  onChange={(e) => setNewResumeStatus(e.target.value as ResumeStatus)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                >
                  <option value="VERIFIED">VERIFIED (Approved for Job Drives)</option>
                  <option value="UNDER_REVIEW">UNDER REVIEW (Pending revisions)</option>
                  <option value="REJECTED">REJECTED (Requires formatting resubmission)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-medium">Reviewer Feedback Notes</label>
                <textarea
                  value={resumeReviewNotes}
                  onChange={(e) => setResumeReviewNotes(e.target.value)}
                  placeholder="e.g. Verified projects and CGPA cutoff match official university transcripts."
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setShowResumeModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleUpdateResume}>
                Save Verification
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
