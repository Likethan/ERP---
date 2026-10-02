"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Calendar,
  Clock,
  Video,
  MapPin,
  Building2,
  User,
  Award,
  ChevronLeft,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileCheck2,
  Star,
  Check,
  Edit3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { Interview, InterviewEvaluation } from "@/types/placement";

export default function InterviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const interviewId = params?.id as string;

  const [interview, setInterview] = useState<Interview | null>(null);
  const [loading, setLoading] = useState(true);

  // Evaluation form state
  const [techRating, setTechRating] = useState(5);
  const [commRating, setCommRating] = useState(4);
  const [probRating, setProbRating] = useState(4);
  const [fitRating, setFitRating] = useState(5);
  const [recommendation, setRecommendation] = useState<"STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE">("STRONG_HIRE");
  const [evalNotes, setEvalNotes] = useState("");

  // Reschedule modal
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [rescheduleReason, setRescheduleReason] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await placementService.getInterviewById(interviewId);
      if (!res.data) {
        showToast({ title: "Not Found", message: "Interview session not found", type: "error" });
        router.push("/app/placement/interviews");
        return;
      }
      setInterview(res.data);
      if (res.data.evaluation) {
        setTechRating(res.data.evaluation.technicalRating);
        setCommRating(res.data.evaluation.communicationRating);
        setProbRating(res.data.evaluation.problemSolvingRating);
        setFitRating(res.data.evaluation.roleFitRating);
        setRecommendation(res.data.evaluation.overallRecommendation);
        setEvalNotes(res.data.evaluation.notes || "");
      }
      setNewDate(res.data.date);
      setNewTime(res.data.time);
    } catch {
      showToast({ title: "Error", message: "Failed to load interview dossier", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (interviewId) {
      loadData();
    }
  }, [interviewId]);

  const handleSubmitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!interview) return;

    try {
      await placementService.completeInterview(interview.id, {
        technicalRating: techRating,
        communicationRating: commRating,
        problemSolvingRating: probRating,
        roleFitRating: fitRating,
        overallRecommendation: recommendation,
        notes: evalNotes,
        evaluatedBy: interview.interviewerName,
        evaluatedAt: new Date().toISOString(),
      });

      showToast({ title: "Evaluation Saved", message: "Candidate evaluation submitted & round completed", type: "success" });
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to record evaluation", type: "error" });
    }
  };

  const handleReschedule = async () => {
    if (!interview || !newDate || !newTime) return;

    try {
      await placementService.rescheduleInterview(
        interview.id,
        newDate,
        newTime,
        rescheduleReason || "Panel availability adjustment",
        "Placement Coordinator"
      );
      showToast({ title: "Interview Rescheduled", message: `Updated to ${newDate} at ${newTime}`, type: "info" });
      setShowRescheduleModal(false);
      loadData();
    } catch {
      showToast({ title: "Error", message: "Failed to reschedule interview", type: "error" });
    }
  };

  if (loading || !interview) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading interview evaluation dossier...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/placement/interviews"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Interviews
        </Link>
      </div>

      {/* Header Profile Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              <Calendar className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Interview {interview.interviewCode}
                </h1>
                <Badge
                  variant={
                    interview.status === "COMPLETED"
                      ? "success"
                      : interview.status === "SCHEDULED"
                      ? "warning"
                      : "secondary"
                  }
                  dot
                >
                  {interview.status}
                </Badge>
                <Badge variant="outline">{interview.stage} Round {interview.roundNumber}</Badge>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <Link
                  href={`/app/placement/students/${interview.studentId}`}
                  className="font-semibold text-slate-900 dark:text-slate-200 hover:underline"
                >
                  {interview.studentName} ({interview.rollNumber})
                </Link>
                <span>•</span>
                <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                  {interview.companyName} — {interview.positionTitle}
                </span>
                <span>•</span>
                <span>{interview.date} at {interview.time} ({interview.durationMinutes} mins)</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {interview.status !== "COMPLETED" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRescheduleModal(true)}
                className="gap-1.5 text-xs"
              >
                <Clock className="w-3.5 h-3.5" />
                Reschedule
              </Button>
            )}
            <Link href={`/app/placement/applications/${interview.applicationId}`}>
              <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                <FileCheck2 className="w-3.5 h-3.5" />
                View Application
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Evaluation Panel (Left 2 cols) & Timeline (Right 1 col) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Meeting Room Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Panelist & Meeting Room Coordinates
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-500">Interview Mode:</span>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {interview.mode === "ONLINE" ? "Virtual / Video Conference" : "In Person (Campus)"}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Meeting Room / URL:</span>
                <p className="font-mono text-indigo-600 dark:text-indigo-400 mt-0.5 truncate">
                  {interview.locationOrMeetingUrl}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Lead Panelist:</span>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {interview.interviewerName}
                </p>
              </div>
              {interview.interviewerEmail && (
                <div>
                  <span className="text-slate-500">Panelist Email:</span>
                  <p className="text-slate-700 dark:text-slate-300 mt-0.5 font-mono">
                    {interview.interviewerEmail}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Performance Evaluation Form */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Performance Evaluation & Hiring Recommendation
              </h2>
              {interview.status === "COMPLETED" && (
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  EVALUATION RECORDED
                </span>
              )}
            </div>

            <form onSubmit={handleSubmitEvaluation} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-slate-600 dark:text-slate-300 font-medium">
                    Technical Competence (1 - 5)
                  </label>
                  <select
                    value={techRating}
                    onChange={(e) => setTechRating(parseInt(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map((num) => (
                      <option key={num} value={num}>
                        {num} — {num === 5 ? "Exceptional" : num === 4 ? "Strong" : num === 3 ? "Adequate" : "Poor"}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-slate-600 dark:text-slate-300 font-medium">
                    Communication & Articulation (1 - 5)
                  </label>
                  <select
                    value={commRating}
                    onChange={(e) => setCommRating(parseInt(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map((num) => (
                      <option key={num} value={num}>
                        {num} — {num === 5 ? "Exceptional" : num === 4 ? "Strong" : num === 3 ? "Adequate" : "Poor"}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-slate-600 dark:text-slate-300 font-medium">
                    Problem Solving & Analytical Thinking (1 - 5)
                  </label>
                  <select
                    value={probRating}
                    onChange={(e) => setProbRating(parseInt(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map((num) => (
                      <option key={num} value={num}>
                        {num} — {num === 5 ? "Exceptional" : num === 4 ? "Strong" : num === 3 ? "Adequate" : "Poor"}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-slate-600 dark:text-slate-300 font-medium">
                    Role & Cultural Alignment (1 - 5)
                  </label>
                  <select
                    value={fitRating}
                    onChange={(e) => setFitRating(parseInt(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  >
                    {[1, 2, 3, 4, 5].map((num) => (
                      <option key={num} value={num}>
                        {num} — {num === 5 ? "Exceptional" : num === 4 ? "Strong" : num === 3 ? "Adequate" : "Poor"}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-600 dark:text-slate-300 font-medium">
                  Overall Recommendation *
                </label>
                <select
                  value={recommendation}
                  onChange={(e) => setRecommendation(e.target.value as any)}
                  className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white font-semibold"
                >
                  <option value="STRONG_HIRE">STRONG HIRE (Priority Offer)</option>
                  <option value="HIRE">HIRE (Qualified for Offer)</option>
                  <option value="BORDERLINE">BORDERLINE (Requires Second Review)</option>
                  <option value="NO_HIRE">NO HIRE (Reject)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-600 dark:text-slate-300 font-medium">
                  Qualitative Panelist Evaluation Notes
                </label>
                <textarea
                  value={evalNotes}
                  onChange={(e) => setEvalNotes(e.target.value)}
                  placeholder="Record observations regarding technical problem-solving depth, architecture considerations, and responses to scenario questions."
                  rows={4}
                  className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button variant="primary" size="sm" type="submit" className="gap-1.5">
                  <Check className="w-3.5 h-3.5" />
                  Save Performance Evaluation
                </Button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Col: Timeline */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
              Round Timeline & Audit
            </h3>
            <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-4">
              {interview.timeline.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-indigo-500 border-2 border-white dark:border-slate-900" />
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {entry.action}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    By {entry.actor} • {new Date(entry.timestamp).toLocaleDateString()}
                  </div>
                  {entry.details && (
                    <div className="text-[11px] text-slate-600 dark:text-slate-300 mt-1 bg-slate-50 dark:bg-slate-800 p-2 rounded">
                      {entry.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Reschedule Modal */}
      {showRescheduleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Reschedule Interview Round</h3>
            <p className="text-xs text-slate-400">
              Provide new interview date, time, and documented rescheduling reason.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium">New Date *</label>
                <Input
                  type="date"
                  value={newDate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewDate(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium">New Time *</label>
                <Input
                  value={newTime}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewTime(e.target.value)}
                  placeholder="e.g. 02:30 PM"
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium">Rescheduling Reason *</label>
                <textarea
                  value={rescheduleReason}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setRescheduleReason(e.target.value)}
                  placeholder="e.g. Recruiter panel flight delay or conflict with university exam."
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setShowRescheduleModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleReschedule}>
                Confirm Reschedule
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
