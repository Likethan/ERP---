"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import {
  MentoringSessionItem,
  MenteeItem,
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
  MessagesSquare,
  Calendar,
  Clock,
  PlusCircle,
  CheckCircle2,
  Users,
  Search,
  Filter,
  FileText,
  MapPin,
  CheckSquare,
} from "lucide-react";

export default function MentoringSessionsPage() {
  const [sessions, setSessions] = useState<MentoringSessionItem[]>([]);
  const [mentees, setMentees] = useState<MenteeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Schedule Modal State
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [sessionType, setSessionType] = useState<"ONE_ON_ONE" | "GROUP">("ONE_ON_ONE");
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [location, setLocation] = useState("Faculty Cabin 302");
  const [discussionPoints, setDiscussionPoints] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [submittingSchedule, setSubmittingSchedule] = useState(false);

  // Complete Session Modal State
  const [completeModalOpen, setCompleteModalOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<MentoringSessionItem | null>(null);
  const [summaryNotes, setSummaryNotes] = useState("");
  const [actionItemText, setActionItemText] = useState("");
  const [submittingComplete, setSubmittingComplete] = useState(false);

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    setLoading(true);
    try {
      const [allSessions, allMentees] = await Promise.all([
        StudentSupportService.getMentoringSessions(),
        StudentSupportService.getAssignedMentees(),
      ]);
      setSessions(allSessions);
      setMentees(allMentees);
      if (allMentees.length > 0) {
        setSelectedStudentId(allMentees[0].student_id || allMentees[0].studentId || "");
      }
    } catch (err) {
      console.error("Failed to load mentoring sessions:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleScheduleSession(e: React.FormEvent) {
    e.preventDefault();
    if (!title || !startDate || !startTime) return;
    setSubmittingSchedule(true);
    try {
      const startIso = new Date(`${startDate}T${startTime}:00Z`).toISOString();
      const endIso = new Date(new Date(startIso).getTime() + durationMinutes * 60000).toISOString();

      await StudentSupportService.createMentoringSession({
        title,
        session_type: sessionType,
        scheduled_start: startIso,
        scheduled_end: endIso,
        location,
        discussion_points: discussionPoints,
        student_ids: selectedStudentId ? [selectedStudentId] : [],
      });

      setNotification("Mentoring session scheduled successfully.");
      setScheduleModalOpen(false);
      setTitle("");
      setStartDate("");
      setStartTime("");
      setDiscussionPoints("");
      loadSessions();
    } catch (err) {
      console.error("Failed to schedule session:", err);
      alert("Error scheduling mentoring session.");
    } finally {
      setSubmittingSchedule(false);
    }
  }

  async function handleCompleteSession(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedSession || !summaryNotes.trim()) return;
    setSubmittingComplete(true);
    try {
      await StudentSupportService.completeMentoringSession(selectedSession.id, {
        summary_notes: summaryNotes,
        action_items: actionItemText
          ? actionItemText.split("\n").filter((l) => l.trim()).map((t) => ({
              title: t.trim(),
              assigned_to_role: "STUDENT",
            }))
          : undefined,
      });

      setNotification("Mentoring session marked completed with recorded outcomes.");
      setCompleteModalOpen(false);
      setSelectedSession(null);
      setSummaryNotes("");
      setActionItemText("");
      loadSessions();
    } catch (err) {
      console.error("Failed to complete session:", err);
      alert("Error saving session completion.");
    } finally {
      setSubmittingComplete(false);
    }
  }

  const filteredSessions = sessions.filter((s) => {
    const sTitle = s.title || s.sessionTitle || "";
    const mName = s.mentor_name || s.mentorName || "";
    const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
    const matchesSearch =
      sTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Mentoring Sessions", href: "/app/student-support/sessions" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <MessagesSquare className="h-6 w-6 text-indigo-400" />
              Faculty Mentoring Sessions
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Organize 1-on-1 and cohort mentoring discussions, record meeting summaries, and track actionable tasks.
            </p>
          </div>
          <Button
            onClick={() => setScheduleModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
          >
            <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
            Schedule Session
          </Button>
        </div>
      </div>

      <StudentSupportNav />

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search sessions by topic or mentor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Statuses</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </Card>

      {/* Sessions List */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading mentoring sessions...</div>
      ) : filteredSessions.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No mentoring sessions found matching the filter.
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredSessions.map((session) => (
            <Card
              key={session.id}
              className="border-slate-800 bg-slate-900/60 p-5 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-base">{session.title}</span>
                    <Badge
                      variant="outline"
                      className={
                        session.status === "COMPLETED"
                          ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-xs"
                          : session.status === "SCHEDULED"
                          ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-xs"
                          : "border-slate-700 text-slate-400 text-xs"
                      }
                    >
                      {session.status}
                    </Badge>
                    <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {session.session_type === "ONE_ON_ONE" ? "1-on-1 Individual" : "Group Cohort"}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Faculty Mentor: <span className="text-slate-200">{session.mentor_name ?? "Faculty Staff"}</span> • Location:{" "}
                    <span className="text-slate-200">{session.location}</span>
                  </div>
                </div>

                <div className="text-right text-xs">
                  <div className="font-semibold text-indigo-300">
                    {new Date(session.scheduled_start || session.sessionDate || "").toLocaleDateString()} at{" "}
                    {new Date(session.scheduled_start || session.sessionDate || "").toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="text-slate-400 mt-0.5">
                    {session.attendees_count ?? 1} Participant(s) • {session.action_items_count ?? 0} Action Item(s)
                  </div>
                </div>
              </div>

              {session.discussion_points && (
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-medium">Planned Agenda:</span>
                  <p className="text-slate-300">{session.discussion_points}</p>
                </div>
              )}

              {session.summary_notes && (
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-medium">Session Summary & Outcomes:</span>
                  <p className="text-slate-200 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    {session.summary_notes}
                  </p>
                </div>
              )}

              {session.student_reflection && (
                <div className="text-xs space-y-1">
                  <span className="text-indigo-400 font-medium">Student Reflection:</span>
                  <p className="text-slate-300 italic bg-indigo-950/20 p-2.5 rounded border border-indigo-900/30">
                    "{session.student_reflection}"
                  </p>
                </div>
              )}

              {/* Complete Session Action Button */}
              {session.status === "SCHEDULED" && (
                <div className="pt-2 flex justify-end">
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedSession(session);
                      setCompleteModalOpen(true);
                    }}
                    className="bg-emerald-600 hover:bg-emerald-700 text-xs text-white"
                  >
                    <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
                    Record Session Completion
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Schedule Modal */}
      <Dialog open={scheduleModalOpen} onOpenChange={setScheduleModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Calendar className="h-4 w-4 text-indigo-400" />
              Schedule Mentoring Session
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleScheduleSession} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Session Title / Topic *</label>
              <Input
                required
                placeholder="e.g. Mid-semester academic & project review"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Session Type *</label>
                <select
                  value={sessionType}
                  onChange={(e) => setSessionType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                >
                  <option value="ONE_ON_ONE">1-on-1 Individual</option>
                  <option value="GROUP">Group Cohort</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Student Mentee</label>
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                >
                  {mentees.map((m) => (
                    <option key={m.student_id || m.studentId} value={m.student_id || m.studentId}>
                      {m.student_name || m.studentName} ({m.student_reg_no || m.rollNumber})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Date *</label>
                <Input
                  required
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Time *</label>
                <Input
                  required
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Location</label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Discussion Points / Agenda</label>
              <Textarea
                placeholder="Key items to discuss..."
                value={discussionPoints}
                onChange={(e) => setDiscussionPoints(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setScheduleModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingSchedule}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submittingSchedule ? "Scheduling..." : "Schedule Session"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Complete Session Modal */}
      <Dialog open={completeModalOpen} onOpenChange={setCompleteModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Record Mentoring Session Completion
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCompleteSession} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Session Summary & Discussion Outcomes *</label>
              <Textarea
                required
                placeholder="Describe key guidance shared, academic recommendations, and student commitments..."
                value={summaryNotes}
                onChange={(e) => setSummaryNotes(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={4}
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">New Action Items (One per line)</label>
              <Textarea
                placeholder="e.g. Complete online machine learning lab 3&#10;Consult placement cell for resume critique"
                value={actionItemText}
                onChange={(e) => setActionItemText(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setCompleteModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingComplete}
                className="bg-emerald-600 hover:bg-emerald-700 text-xs text-white"
              >
                {submittingComplete ? "Saving..." : "Save Session Outcomes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
