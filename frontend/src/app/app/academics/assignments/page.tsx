"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { teachingService } from "@/services/teaching.service";
import {
  CourseAssignment,
  AssignmentSubmission,
  SubmissionFormat,
  AssignmentStatus,
} from "@/types/teaching";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  ClipboardCheck,
  Plus,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  AlertTriangle,
  Upload,
  ArrowRight,
  User,
  Award,
  Sparkles,
  Search,
} from "lucide-react";

export default function CourseAssignmentsPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const userRole = activePersona?.role || user?.roles?.[0]?.name || "STUDENT";
  const isFaculty =
    userRole === "FACULTY" ||
    userRole === "HOD" ||
    userRole === "ADMIN" ||
    userRole === "SUPER_ADMIN";
  const isStudent = userRole === "STUDENT";

  const [loading, setLoading] = useState(true);
  const [assignments, setAssignments] = useState<CourseAssignment[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("co-cs301-a");

  // Create Assignment Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    title: "",
    description: "",
    unitNumber: 3,
    assignedDate: new Date().toISOString().split("T")[0],
    dueDate: new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0],
    maxMarks: 50,
    weightagePercent: 10,
    submissionFormat: "PDF" as SubmissionFormat,
    allowLateSubmission: true,
    lateSubmissionDeadline: new Date(Date.now() + 10 * 86400000)
      .toISOString()
      .split("T")[0],
    latePenaltyPercent: 10,
    status: "PUBLISHED" as AssignmentStatus,
    totalEnrolled: 48,
  });

  // Faculty Submissions View Modal
  const [submissionsModalOpen, setSubmissionsModalOpen] = useState(false);
  const [activeAssignment, setActiveAssignment] =
    useState<CourseAssignment | null>(null);
  const [submissions, setSubmissions] = useState<AssignmentSubmission[]>([]);

  // Evaluation Modal
  const [evaluateModalOpen, setEvaluateModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] =
    useState<AssignmentSubmission | null>(null);
  const [evalMarks, setEvalMarks] = useState<number>(0);
  const [evalFeedback, setEvalFeedback] = useState<string>("");
  const [evaluating, setEvaluating] = useState(false);

  // Student Submission Modal
  const [studentSubmitModalOpen, setStudentSubmitModalOpen] = useState(false);
  const [targetAssignmentForSubmit, setTargetAssignmentForSubmit] =
    useState<CourseAssignment | null>(null);
  const [studentFileName, setStudentFileName] = useState("Solution_Code.zip");
  const [studentNotes, setStudentNotes] = useState("");
  const [uploadingStudentSubmission, setUploadingStudentSubmission] =
    useState(false);

  // Student's own submissions map
  const [mySubmissions, setMySubmissions] = useState<
    Record<string, AssignmentSubmission>
  >({});

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await teachingService.getAssignments({
        courseOfferingId: selectedCourse,
      });
      if (res.success) {
        setAssignments(res.data);
      }

      // If student, load their personal submissions
      if (isStudent) {
        const studentId = activePersona?.id || "std-aarav-patel";
        const subsRes = await teachingService.getSubmissions(
          undefined,
          studentId,
        );
        if (subsRes.success) {
          const map: Record<string, AssignmentSubmission> = {};
          subsRes.data.forEach((s) => {
            map[s.assignmentId] = s;
          });
          setMySubmissions(map);
        }
      }
    } catch (err) {
      console.error(err);
      showToast({
        type: "error",
        title: "Error",
        message: "Failed to load assignments.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCourse, isStudent]);

  // Load submissions for a specific assignment (Faculty action)
  const openSubmissionsForAssignment = async (asg: CourseAssignment) => {
    setActiveAssignment(asg);
    try {
      const res = await teachingService.getSubmissions(asg.id);
      if (res.success) {
        setSubmissions(res.data);
      }
      setSubmissionsModalOpen(true);
    } catch (err) {
      showToast({
        type: "error",
        title: "Error",
        message: "Failed to load submissions.",
      });
    }
  };

  // Open evaluation form
  const openEvaluation = (sub: AssignmentSubmission) => {
    setSelectedSubmission(sub);
    setEvalMarks(sub.marksObtained ?? sub.maxMarks);
    setEvalFeedback(
      sub.feedback ?? "Good effort. Comprehensive test coverage.",
    );
    setEvaluateModalOpen(true);
  };

  // Submit evaluation (Faculty)
  const handleSaveEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubmission) return;
    try {
      setEvaluating(true);
      const res = await teachingService.evaluateSubmission(
        selectedSubmission.id,
        {
          marksObtained: Number(evalMarks),
          feedback: evalFeedback,
          facultyId: activePersona?.id || "fac-cse-01",
          facultyName: activePersona?.name || "Dr. Rajesh Sharma",
        },
      );

      if (res.success) {
        showToast({
          type: "success",
          title: "Submission Evaluated",
          message: `Awarded ${evalMarks}/${selectedSubmission.maxMarks} marks. Student notified.`,
        });
        setEvaluateModalOpen(false);
        // Refresh submissions
        if (activeAssignment) {
          const updatedSubs = await teachingService.getSubmissions(
            activeAssignment.id,
          );
          if (updatedSubs.success) setSubmissions(updatedSubs.data);
        }
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Evaluation Failed",
        message: err.message,
      });
    } finally {
      setEvaluating(false);
    }
  };

  // Student submits assignment
  const handleStudentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetAssignmentForSubmit) return;
    try {
      setUploadingStudentSubmission(true);
      const res = await teachingService.submitAssignment({
        assignmentId: targetAssignmentForSubmit.id,
        courseOfferingId: targetAssignmentForSubmit.courseOfferingId,
        courseCode: targetAssignmentForSubmit.courseCode,
        courseName: targetAssignmentForSubmit.courseName,
        studentId: activePersona?.id || "std-aarav-patel",
        studentName: activePersona?.name || "Aarav Patel",
        studentRoll: "24CSE0101",
        submissionFileName: studentFileName,
        submissionFileUrl: `/assets/submissions/${studentFileName}`,
        submissionText: studentNotes,
        maxMarks: targetAssignmentForSubmit.maxMarks,
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Assignment Submitted Successfully",
          message: `Your file ${studentFileName} has been submitted for faculty evaluation.`,
        });
        setStudentSubmitModalOpen(false);
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Submission Failed",
        message: err.message,
      });
    } finally {
      setUploadingStudentSubmission(false);
    }
  };

  // Faculty creates assignment
  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "Title is required.",
      });
      return;
    }
    try {
      setSubmitting(true);
      const res = await teachingService.createAssignment({
        courseOfferingId: formData.courseOfferingId,
        courseCode: formData.courseCode,
        courseName: formData.courseName,
        section: formData.section,
        title: formData.title,
        description: formData.description,
        unitNumber: Number(formData.unitNumber),
        assignedDate: formData.assignedDate,
        dueDate: formData.dueDate,
        maxMarks: Number(formData.maxMarks),
        weightagePercent: Number(formData.weightagePercent),
        submissionFormat: formData.submissionFormat,
        allowLateSubmission: Boolean(formData.allowLateSubmission),
        lateSubmissionDeadline: formData.lateSubmissionDeadline,
        latePenaltyPercent: Number(formData.latePenaltyPercent),
        status: formData.status,
        totalEnrolled: Number(formData.totalEnrolled),
        createdByFacultyId: activePersona?.id || "fac-cse-01",
        createdByFacultyName: activePersona?.name || "Dr. Rajesh Sharma",
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Assignment Created",
          message:
            "Assignment published. Enrolled students have been notified.",
        });
        setCreateModalOpen(false);
        setFormData({ ...formData, title: "", description: "" });
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Creation Failed",
        message: err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Coursework & Continuous Assessment Engine
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            {isStudent
              ? "My Coursework Assignments"
              : "Assignments & Evaluations"}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            {isStudent
              ? "Submit homework assignments, check evaluation feedback, and monitor internal marks."
              : "Design assignments, set submission deadlines, evaluate student work, and award feedback."}
          </p>
        </div>

        {isFaculty && (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setCreateModalOpen(true)}
            >
              Create Assignment
            </Button>
          </div>
        )}
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total Assignments"
          value={assignments.length}
          description="Continuous assessment homeworks"
          variant="indigo"
          icon={<ClipboardCheck className="h-4 w-4" />}
        />
        <StatCard
          label={isStudent ? "My Submissions" : "Total Submissions"}
          value={
            isStudent
              ? Object.keys(mySubmissions).length
              : assignments.reduce((acc, a) => acc + a.totalSubmissions, 0)
          }
          description={
            isStudent
              ? "Submitted for faculty grading"
              : "Across enrolled students"
          }
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label={isStudent ? "Graded Submissions" : "Pending Evaluations"}
          value={
            isStudent
              ? Object.values(mySubmissions).filter(
                  (s) => s.status === "EVALUATED",
                ).length
              : assignments.reduce(
                  (acc, a) => acc + (a.totalSubmissions - a.evaluatedCount),
                  0,
                )
          }
          description={
            isStudent
              ? "Marks & qualitative feedback returned"
              : "Requires faculty evaluation"
          }
          variant="amber"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Course Filter */}
      <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <BookOpen className="h-4 w-4 text-yellow-600" />
          <span className="text-xs font-semibold text-slate-800">
            Course Offering:
          </span>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
          >
            <option value="co-cs301-a">
              CS301 — Data Structures & Algorithms (Sec A)
            </option>
            <option value="co-cs501-a">CS501 — Compiler Design (Sec A)</option>
            <option value="co-cs402-b">
              CS402 — Operating Systems (Sec B)
            </option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Viewing as:{" "}
          <strong className="text-slate-800">
            {activePersona?.name} ({userRole})
          </strong>
        </div>
      </div>

      {/* Assignment Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">
            Loading assignments...
          </div>
        ) : assignments.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No assignments created for this course.
          </div>
        ) : (
          assignments.map((asg) => {
            const studentSub = mySubmissions[asg.id];
            const isDuePassed = new Date() > new Date(asg.dueDate);

            return (
              <Card
                key={asg.id}
                className="overflow-hidden hover:border-yellow-300 transition-all"
              >
                <CardContent className="p-5 sm:p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant="outline"
                          className="text-[10px] font-mono"
                        >
                          Unit {asg.unitNumber} • {asg.courseCode}
                        </Badge>
                        <Badge
                          variant={
                            asg.status === "PUBLISHED" ? "success" : "secondary"
                          }
                          dot
                        >
                          {asg.status}
                        </Badge>
                        {asg.allowLateSubmission && (
                          <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                            Late Submissions Allowed (-{asg.latePenaltyPercent}
                            %)
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-slate-900">
                        {asg.title}
                      </h3>
                      <p className="text-xs text-slate-600 mt-1">
                        {asg.description}
                      </p>
                    </div>

                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      <div className="text-xs font-mono font-bold text-slate-900 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                        Max Marks: {asg.maxMarks} ({asg.weightagePercent}%
                        Weight)
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" /> Due:{" "}
                        <strong
                          className={
                            isDuePassed ? "text-rose-600" : "text-slate-800"
                          }
                        >
                          {asg.dueDate}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Submission and Feedback row */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
                    {/* Metrics for Faculty */}
                    {isFaculty && (
                      <div className="flex items-center gap-4 text-xs">
                        <div>
                          <span className="text-slate-500">Submissions: </span>
                          <strong className="text-slate-900 font-mono">
                            {asg.totalSubmissions} / {asg.totalEnrolled}
                          </strong>
                        </div>
                        <div>
                          <span className="text-slate-500">Evaluated: </span>
                          <strong className="text-emerald-700 font-mono">
                            {asg.evaluatedCount} / {asg.totalSubmissions}
                          </strong>
                        </div>
                        {asg.averageScore !== undefined && (
                          <div>
                            <span className="text-slate-500">Class Avg: </span>
                            <strong className="text-amber-700 font-mono">
                              {asg.averageScore} / {asg.maxMarks}
                            </strong>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Student Status indicator */}
                    {isStudent && (
                      <div className="text-xs">
                        {studentSub ? (
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                studentSub.status === "EVALUATED"
                                  ? "success"
                                  : "secondary"
                              }
                              dot
                            >
                              {studentSub.status === "EVALUATED"
                                ? "Evaluated"
                                : "Submitted"}
                            </Badge>
                            <span className="text-slate-600">
                              {studentSub.submissionFileName} (
                              {new Date(
                                studentSub.submittedAt,
                              ).toLocaleDateString()}
                              )
                            </span>
                            {studentSub.isLate && (
                              <Badge variant="danger" className="text-[10px]">
                                Late
                              </Badge>
                            )}
                          </div>
                        ) : (
                          <div className="text-amber-700 font-medium flex items-center gap-1.5">
                            <AlertTriangle className="h-3.5 w-3.5" />
                            <span>
                              Not submitted yet. Allowed format:{" "}
                              <strong>{asg.submissionFormat}</strong>
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      {isFaculty && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs h-8 border-yellow-300 bg-yellow-50/20 hover:bg-yellow-100"
                          onClick={() => openSubmissionsForAssignment(asg)}
                        >
                          View Submissions ({asg.totalSubmissions})
                        </Button>
                      )}

                      {isStudent && (
                        <Button
                          variant={studentSub ? "outline" : "primary"}
                          size="sm"
                          className="text-xs h-8"
                          onClick={() => {
                            setTargetAssignmentForSubmit(asg);
                            setStudentSubmitModalOpen(true);
                          }}
                        >
                          {studentSub
                            ? "Resubmit Solution"
                            : "Submit Assignment"}
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Student Feedback Panel if Evaluated */}
                  {isStudent &&
                    studentSub &&
                    studentSub.status === "EVALUATED" && (
                      <div className="rounded-xl bg-emerald-50/70 border border-emerald-200 p-3.5 text-xs text-emerald-950 mt-2">
                        <div className="flex items-center justify-between font-bold mb-1">
                          <span className="flex items-center gap-1.5 text-emerald-800">
                            <Award className="h-4 w-4 text-emerald-600" />
                            Faculty Evaluation & Marks
                          </span>
                          <span className="text-sm font-mono text-emerald-900 bg-white px-2 py-0.5 rounded-md border border-emerald-300">
                            Marks: {studentSub.marksObtained} /{" "}
                            {studentSub.maxMarks}
                          </span>
                        </div>
                        <div className="text-emerald-900 mt-1">
                          <span className="font-semibold text-emerald-800">
                            Faculty Feedback:{" "}
                          </span>
                          "{studentSub.feedback}"
                        </div>
                        <div className="text-[10px] text-emerald-600 mt-1">
                          Evaluated by {studentSub.evaluatedByFacultyName} on{" "}
                          {studentSub.evaluatedAt
                            ? new Date(
                                studentSub.evaluatedAt,
                              ).toLocaleDateString()
                            : ""}
                        </div>
                      </div>
                    )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Submissions Roster Modal (Faculty) */}
      <Dialog
        isOpen={submissionsModalOpen}
        onClose={() => setSubmissionsModalOpen(false)}
        title={`Submissions: ${activeAssignment?.title || ""}`}
      >
        <div className="space-y-4">
          <div className="text-xs text-slate-500">
            Total submissions received: <strong>{submissions.length}</strong>.
            Maximum Marks: <strong>{activeAssignment?.maxMarks}</strong>.
          </div>

          <div className="max-h-96 overflow-y-auto divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
            {submissions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No student submissions received yet.
              </div>
            ) : (
              submissions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-900">
                        {sub.studentName}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500">
                        ({sub.studentRoll})
                      </span>
                      {sub.isLate && (
                        <Badge variant="danger" className="text-[9px]">
                          Late
                        </Badge>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      File:{" "}
                      <strong className="text-slate-700">
                        {sub.submissionFileName}
                      </strong>{" "}
                      • {new Date(sub.submittedAt).toLocaleString()}
                    </div>
                    {sub.feedback && (
                      <div className="text-[11px] text-emerald-700 mt-1 italic">
                        Feedback: "{sub.feedback}"
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      {sub.status === "EVALUATED" ? (
                        <div className="font-mono font-bold text-xs text-emerald-700">
                          {sub.marksObtained} / {sub.maxMarks}
                        </div>
                      ) : (
                        <Badge variant="warning" dot className="text-[10px]">
                          Pending
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs h-7 px-2.5"
                      onClick={() => openEvaluation(sub)}
                    >
                      {sub.status === "EVALUATED" ? "Update Marks" : "Evaluate"}
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="flex justify-end pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSubmissionsModalOpen(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Evaluation Input Dialog */}
      <Dialog
        isOpen={evaluateModalOpen}
        onClose={() => setEvaluateModalOpen(false)}
        title="Evaluate Student Submission"
      >
        <form onSubmit={handleSaveEvaluation} className="space-y-4">
          <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div>
              Student:{" "}
              <strong className="text-slate-900">
                {selectedSubmission?.studentName}
              </strong>{" "}
              ({selectedSubmission?.studentRoll})
            </div>
            <div className="mt-1">
              Submission:{" "}
              <strong className="text-slate-800">
                {selectedSubmission?.submissionFileName}
              </strong>
            </div>
            {selectedSubmission?.isLate && (
              <div className="text-rose-600 font-semibold mt-1">
                * Submitted after deadline. Subject to institutional late
                penalty.
              </div>
            )}
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Marks Awarded (Max: {selectedSubmission?.maxMarks})
            </label>
            <Input
              type="number"
              min="0"
              max={selectedSubmission?.maxMarks || 100}
              value={evalMarks}
              onChange={(e) => setEvalMarks(Number(e.target.value))}
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Qualitative Feedback
            </label>
            <textarea
              rows={3}
              placeholder="Provide constructive feedback, suggestions for improvement, and comments..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={evalFeedback}
              onChange={(e) => setEvalFeedback(e.target.value)}
              required
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setEvaluateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={evaluating}
            >
              {evaluating ? "Saving..." : "Save Marks & Notify Student"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Student Submit Solution Dialog */}
      <Dialog
        isOpen={studentSubmitModalOpen}
        onClose={() => setStudentSubmitModalOpen(false)}
        title={`Submit: ${targetAssignmentForSubmit?.title || ""}`}
      >
        <form onSubmit={handleStudentSubmit} className="space-y-4">
          <div className="text-xs text-slate-600 bg-yellow-50/40 p-3 rounded-lg border border-yellow-200">
            <div>
              Course:{" "}
              <strong>
                {targetAssignmentForSubmit?.courseCode} —{" "}
                {targetAssignmentForSubmit?.courseName}
              </strong>
            </div>
            <div>
              Due Date: <strong>{targetAssignmentForSubmit?.dueDate}</strong>
            </div>
            <div>
              Allowed Format:{" "}
              <strong>{targetAssignmentForSubmit?.submissionFormat}</strong>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Solution File Name
            </label>
            <Input
              placeholder="e.g. 24CSE0101_Assignment2_Solution.pdf"
              value={studentFileName}
              onChange={(e) => setStudentFileName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Notes / Implementation Details for Faculty
            </label>
            <textarea
              rows={3}
              placeholder="Describe your solution approach or attach git repository links..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={studentNotes}
              onChange={(e) => setStudentNotes(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setStudentSubmitModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={uploadingStudentSubmission}
            >
              {uploadingStudentSubmission
                ? "Submitting..."
                : "Submit to Faculty"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Create Assignment Dialog (Faculty) */}
      <Dialog
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create Coursework Assignment"
      >
        <form onSubmit={handleCreateAssignment} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700">
              Assignment Title
            </label>
            <Input
              placeholder="e.g. Assignment 3: Disjoint Sets & Kruskal MST"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Syllabus Unit
              </label>
              <select
                value={formData.unitNumber}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    unitNumber: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="1">Unit 1: Linear Structures</option>
                <option value="2">Unit 2: Balanced Trees</option>
                <option value="3">Unit 3: Graph Algorithms</option>
                <option value="4">Unit 4: Hashing & Heaps</option>
                <option value="5">Unit 5: NP-Completeness</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700">
                Submission Format
              </label>
              <select
                value={formData.submissionFormat}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    submissionFormat: e.target.value as SubmissionFormat,
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="PDF">PDF Report (.pdf)</option>
                <option value="ZIP">ZIP Archive (.zip)</option>
                <option value="DOCX">Word Document (.docx)</option>
                <option value="CODE">Source Code (.py, .cpp, .java)</option>
                <option value="TEXT">Online Text Input</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Description / Problem Statement
            </label>
            <textarea
              rows={3}
              placeholder="Detail problem specifications, required test cases, and evaluation rubrics..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Submission Due Date
              </label>
              <Input
                type="date"
                value={formData.dueDate}
                onChange={(e) =>
                  setFormData({ ...formData, dueDate: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Maximum Marks
              </label>
              <Input
                type="number"
                min="10"
                max="100"
                value={formData.maxMarks}
                onChange={(e) =>
                  setFormData({ ...formData, maxMarks: Number(e.target.value) })
                }
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Weightage %
              </label>
              <Input
                type="number"
                min="1"
                max="50"
                value={formData.weightagePercent}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weightagePercent: Number(e.target.value),
                  })
                }
                required
              />
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="allowLate"
                checked={formData.allowLateSubmission}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    allowLateSubmission: e.target.checked,
                  })
                }
                className="h-4 w-4 rounded border-slate-300 text-yellow-500 focus:ring-yellow-400"
              />
              <label
                htmlFor="allowLate"
                className="text-xs font-medium text-slate-800"
              >
                Allow Late Submissions with Institutional Penalty
              </label>
            </div>

            {formData.allowLateSubmission && (
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="text-[11px] font-semibold text-slate-700">
                    Late Cutoff Date
                  </label>
                  <Input
                    type="date"
                    value={formData.lateSubmissionDeadline}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        lateSubmissionDeadline: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-700">
                    Penalty Percentage %
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    value={formData.latePenaltyPercent}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        latePenaltyPercent: Number(e.target.value),
                      })
                    }
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Publishing..." : "Create & Publish Assignment"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
