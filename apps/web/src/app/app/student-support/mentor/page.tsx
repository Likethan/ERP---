"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import {
  MentorAssignmentItem,
  MentoringSessionItem,
  StudentDevelopmentPlanItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  UserCheck,
  Mail,
  Building,
  Calendar,
  Clock,
  Sparkles,
  CheckCircle2,
  FileText,
  MessagesSquare,
  AlertCircle,
  HelpCircle,
  PlusCircle,
} from "lucide-react";

export default function MyMentorPage() {
  const [assignment, setAssignment] = useState<MentorAssignmentItem | null>(null);
  const [sessions, setSessions] = useState<MentoringSessionItem[]>([]);
  const [developmentPlan, setDevelopmentPlan] = useState<StudentDevelopmentPlanItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Request Meeting Dialog State
  const [openMeetingDialog, setOpenMeetingDialog] = useState(false);
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingDate, setMeetingDate] = useState("");
  const [meetingTime, setMeetingTime] = useState("");
  const [meetingNotes, setMeetingNotes] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Mentee Reflection State
  const [reflectionSessionId, setReflectionSessionId] = useState<string | null>(null);
  const [reflectionText, setReflectionText] = useState("");
  const [savingReflection, setSavingReflection] = useState(false);

  useEffect(() => {
    loadMentorData();
  }, []);

  async function loadMentorData() {
    setLoading(true);
    setError(null);
    try {
      // Fetch assignments, sessions, and IDP for current student
      const [assignments, allSessions, plans] = await Promise.all([
        StudentSupportService.getMentorAssignments({ status: "ACTIVE" }),
        StudentSupportService.getMentoringSessions(),
        StudentSupportService.getDevelopmentPlans(),
      ]);

      if (assignments.length > 0) {
        setAssignment(assignments[0]);
      }
      setSessions(allSessions);
      if (plans.length > 0) {
        setDevelopmentPlan(plans[0]);
      }
    } catch (err) {
      console.error("Failed to load mentor data:", err);
      setError("Unable to load assigned mentor details.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestMeeting(e: React.FormEvent) {
    e.preventDefault();
    if (!meetingTitle || !meetingDate || !meetingTime) return;
    setScheduling(true);
    try {
      const scheduledStart = new Date(`${meetingDate}T${meetingTime}:00Z`).toISOString();
      const scheduledEnd = new Date(new Date(scheduledStart).getTime() + 45 * 60000).toISOString();

      await StudentSupportService.createMentoringSession({
        title: meetingTitle,
        mentor_staff_id: assignment?.faculty_id ?? "unknown",
        session_type: "ONE_ON_ONE",
        scheduled_start: scheduledStart,
        scheduled_end: scheduledEnd,
        location: "Faculty Cabin 302 / CampusOS Video Room",
        discussion_points: meetingNotes,
        student_ids: [assignment?.student_id ?? "current-student"],
      });

      setSuccessMessage("Mentoring meeting request submitted to faculty mentor.");
      setOpenMeetingDialog(false);
      setMeetingTitle("");
      setMeetingDate("");
      setMeetingTime("");
      setMeetingNotes("");
      loadMentorData();
    } catch (err) {
      console.error("Meeting request failed:", err);
      alert("Failed to submit meeting request. Please verify connection.");
    } finally {
      setScheduling(false);
    }
  }

  async function handleSaveReflection(sessionId: string) {
    if (!reflectionText) return;
    setSavingReflection(true);
    try {
      await StudentSupportService.submitMenteeReflection(sessionId, reflectionText);
      setSuccessMessage("Your reflection was recorded successfully.");
      setReflectionSessionId(null);
      setReflectionText("");
      loadMentorData();
    } catch (err) {
      console.error("Failed to submit reflection:", err);
      alert("Failed to submit reflection.");
    } finally {
      setSavingReflection(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "My Mentor", href: "/app/student-support/mentor" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <UserCheck className="h-6 w-6 text-indigo-400" />
              My Faculty Mentor
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Your designated academic and professional development guide for the 2026–2027 academic year.
            </p>
          </div>
          {assignment && (
            <Button
              onClick={() => setOpenMeetingDialog(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
            >
              <Calendar className="mr-1.5 h-3.5 w-3.5" />
              Request Mentoring Meeting
            </Button>
          )}
        </div>
      </div>

      <StudentSupportNav />

      {successMessage && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading your faculty mentor details...</div>
      ) : !assignment ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-amber-400 opacity-80 mb-3" />
          <h2 className="text-lg font-semibold text-white">No Active Faculty Mentor Assigned</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto mt-2">
            Your department coordinator is currently finalizing mentor allocations for your batch. If you require immediate academic advice, please consult your HOD or submit a support referral.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/app/student-support/referrals">
              <Button variant="outline" className="border-slate-700 text-xs">
                Submit Support Referral
              </Button>
            </Link>
            <Link href="/app/student-support/counselling">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white">
                Book Institutional Counselling
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left Column: Mentor Profile Card */}
          <div className="space-y-6">
            <Card className="border-slate-800 bg-slate-900/60 p-6 space-y-4">
              <div className="flex items-center gap-4 border-b border-slate-800 pb-4">
                <div className="h-14 w-14 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-lg">
                  {(assignment.faculty_name || assignment.mentorName || "Faculty Mentor").split(" ").map((n) => n[0]).join("")}
                </div>
                <div>
                  <h2 className="text-base font-semibold text-white">{assignment.faculty_name || assignment.mentorName || "Faculty Mentor"}</h2>
                  <div className="text-xs text-indigo-400">{assignment.department_name || assignment.studentDepartment || "Department"}</div>
                  <Badge variant="outline" className="mt-1 border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]">
                    Active Assignment
                  </Badge>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center gap-2.5 text-slate-300">
                  <Mail className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{assignment.faculty_email || "mentor.contact@campusos.edu"}</span>
                </div>
                <div className="flex items-center gap-2.5 text-slate-300">
                  <Building className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>Department Block B, Cabin 302</span>
                </div>
                <div className="flex items-center gap-2.5 text-slate-300">
                  <Clock className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>Office Hours: Tue & Thu, 2:00 PM – 4:30 PM</span>
                </div>
                <div className="flex items-center gap-2.5 text-slate-300">
                  <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>Assigned: {new Date(assignment.assigned_at || assignment.assignedDate || "").toLocaleDateString()}</span>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  onClick={() => setOpenMeetingDialog(true)}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
                >
                  <Calendar className="mr-1.5 h-3.5 w-3.5" />
                  Request Meeting
                </Button>
              </div>
            </Card>

            {/* Quick Guidance Tips Card */}
            <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-3">
              <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                <HelpCircle className="h-4 w-4 text-indigo-400" />
                Mentorship Expectations
              </h3>
              <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
                <li>Meet with your mentor at least twice per semester.</li>
                <li>Keep your Student Development Plan goals updated.</li>
                <li>Submit reflections after each completed session.</li>
                <li>Contact directly for career or elective guidance.</li>
              </ul>
            </Card>
          </div>

          {/* Right 2 Columns: Active IDP & Recent Mentoring Sessions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Student Development Plan */}
            <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-white flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-400" />
                    Individual Development Plan (IDP)
                  </h2>
                  <p className="text-xs text-slate-400">Your roadmap for academic and career excellence</p>
                </div>
                <Link href="/app/student-support/development-plans">
                  <Button variant="outline" size="sm" className="border-slate-700 text-xs">
                    View Full Plan
                  </Button>
                </Link>
              </div>

              {developmentPlan ? (
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300 font-medium">{developmentPlan.title}</span>
                      <span className="text-indigo-400 font-semibold">{developmentPlan.overall_progress_pct}% Completed</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                        style={{ width: `${developmentPlan.overall_progress_pct}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs space-y-1">
                      <span className="text-slate-400 font-medium">Core Strengths Identified:</span>
                      <p className="text-slate-200">{developmentPlan.strengths_summary || "Analytical skills, algorithmic programming."}</p>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs space-y-1">
                      <span className="text-slate-400 font-medium">Target Growth Areas:</span>
                      <p className="text-slate-200">{developmentPlan.growth_areas_summary || "Technical communication, system design architecture."}</p>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 flex items-center gap-2 pt-1">
                    <span>Review Frequency: <strong className="text-slate-300">{developmentPlan.review_frequency}</strong></span>
                    <span>•</span>
                    <span>Next Scheduled Review: {developmentPlan.next_review_date ? new Date(developmentPlan.next_review_date).toLocaleDateString() : "Pending"}</span>
                  </div>
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-slate-500">
                  No development plan created yet. Discuss your goals with your mentor.
                </div>
              )}
            </Card>

            {/* Mentoring Sessions & Reflections */}
            <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-white flex items-center gap-2">
                    <MessagesSquare className="h-4 w-4 text-indigo-400" />
                    Session History & Mentee Reflections
                  </h2>
                  <p className="text-xs text-slate-400">Review outcomes, action points, and submit personal reflections</p>
                </div>
              </div>

              {sessions.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">No session records available yet.</div>
              ) : (
                <div className="space-y-4">
                  {sessions.map((sess) => (
                    <div key={sess.id} className="p-4 rounded-xl border border-slate-800 bg-slate-950/30 space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
                        <div>
                          <div className="font-semibold text-sm text-slate-100">{sess.title}</div>
                          <div className="text-xs text-slate-400">
                            {new Date(sess.scheduled_start || sess.sessionDate || "").toLocaleDateString()} at {new Date(sess.scheduled_start || sess.sessionDate || "").toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} • {sess.location || sess.locationOrLink || "Online"}
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className={
                            sess.status === "COMPLETED"
                              ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                              : "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                          }
                        >
                          {sess.status}
                        </Badge>
                      </div>

                      {sess.summary_notes && (
                        <div className="text-xs space-y-1">
                          <span className="text-slate-400 font-medium">Mentor Summary:</span>
                          <p className="text-slate-200 bg-slate-900/80 p-2.5 rounded border border-slate-800">
                            {sess.summary_notes}
                          </p>
                        </div>
                      )}

                      {/* Mentee Reflection Area */}
                      <div className="pt-1">
                        {sess.student_reflection ? (
                          <div className="text-xs space-y-1">
                            <span className="text-indigo-400 font-medium flex items-center gap-1.5">
                              <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                              Your Reflection:
                            </span>
                            <p className="text-slate-300 italic bg-indigo-950/20 p-2.5 rounded border border-indigo-900/30">
                              "{sess.student_reflection}"
                            </p>
                          </div>
                        ) : reflectionSessionId === sess.id ? (
                          <div className="space-y-2 pt-2">
                            <Textarea
                              placeholder="Record your takeaways, lessons learned, or follow-up commitments from this session..."
                              value={reflectionText}
                              onChange={(e) => setReflectionText(e.target.value)}
                              className="text-xs bg-slate-900 border-slate-700"
                              rows={3}
                            />
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => handleSaveReflection(sess.id)}
                                disabled={savingReflection || !reflectionText.trim()}
                                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
                              >
                                {savingReflection ? "Saving..." : "Submit Reflection"}
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  setReflectionSessionId(null);
                                  setReflectionText("");
                                }}
                                className="text-xs text-slate-400"
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setReflectionSessionId(sess.id);
                              setReflectionText("");
                            }}
                            className="text-xs border-indigo-900/50 text-indigo-400 hover:bg-indigo-950/40"
                          >
                            <FileText className="mr-1.5 h-3.5 w-3.5" />
                            Add Student Reflection
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* Request Meeting Modal */}
      <Dialog open={openMeetingDialog} onOpenChange={setOpenMeetingDialog}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Calendar className="h-4 w-4 text-indigo-400" />
              Request Mentoring Meeting
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleRequestMeeting} className="space-y-4 pt-2">
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Meeting Topic / Agenda *</label>
              <Input
                required
                placeholder="e.g. Elective choices & semester progress review"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-slate-400">Preferred Date *</label>
                <Input
                  required
                  type="date"
                  value={meetingDate}
                  onChange={(e) => setMeetingDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-slate-400">Preferred Time *</label>
                <Input
                  required
                  type="time"
                  value={meetingTime}
                  onChange={(e) => setMeetingTime(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Brief Notes for Mentor</label>
              <Textarea
                placeholder="Specify any questions, upcoming project dilemmas, or specific guidance requested..."
                value={meetingNotes}
                onChange={(e) => setMeetingNotes(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>
            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setOpenMeetingDialog(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={scheduling}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {scheduling ? "Sending..." : "Send Meeting Request"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
