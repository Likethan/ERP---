"use client";

import React, { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { facultyService } from "@/services/faculty.service";
import { FacultyDetailView } from "@/types/domain";
import {
  PublicationType,
  PublicationStatus,
} from "@/types/people";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import {
  ArrowLeft,
  Mail,
  Phone,
  Clock,
  Building,
  GraduationCap,
  Users,
  Award,
  Plus,
  Trash2,
  FlaskConical,
} from "lucide-react";

export default function Faculty360ProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const facultyId = resolvedParams.id;
  const { showToast } = useToast();
  const { activePersona } = useAuth();

  // Role permissions
  const canManageWorkload = activePersona.role === "ADMIN" || activePersona.role === "HOD";
  const canAddPublication = activePersona.role === "ADMIN" || activePersona.role === "HOD" || activePersona.role === "FACULTY";

  const [faculty, setFaculty] = useState<FacultyDetailView | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Lab assignment modal
  const [labModalOpen, setLabModalOpen] = useState(false);
  const [labName, setLabName] = useState("");
  const [labCourseCode, setLabCourseCode] = useState("CS301-L");
  const [labSection, setLabSection] = useState("A-Batch 1");
  const [labDay, setLabDay] = useState("Monday");
  const [labTime, setLabTime] = useState("02:00 PM - 04:00 PM");
  const [labRoom, setLabRoom] = useState("Lab 304, Turing Block");
  const [labHours, setLabHours] = useState("2");
  const [labCapacity, setLabCapacity] = useState("32");

  // Publication modal
  const [pubModalOpen, setPubModalOpen] = useState(false);
  const [pubTitle, setPubTitle] = useState("");
  const [pubVenue, setPubVenue] = useState("");
  const [pubType, setPubType] = useState<PublicationType>("JOURNAL");
  const [pubYear, setPubYear] = useState(String(new Date().getFullYear()));
  const [pubDoi, setPubDoi] = useState("");
  const [pubStatus, setPubStatus] = useState<PublicationStatus>("PUBLISHED");

  const loadFaculty = useCallback(async () => {
    setLoading(true);
    try {
      const res = await facultyService.getById(facultyId);
      if (res.data) {
        setFaculty(res.data);
      }
    } catch {
      showToast({
        type: "error",
        title: "Load Failed",
        message: `Failed to load faculty record for ${facultyId}.`,
      });
    } finally {
      setLoading(false);
    }
  }, [facultyId, showToast]);

  useEffect(() => {
    loadFaculty();
  }, [loadFaculty]);

  // Handle Lab Assignment
  const handleAssignLab = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!faculty) return;
    try {
      await facultyService.assignLab(faculty.id, {
        labName,
        courseCode: labCourseCode,
        courseName: `${labCourseCode} Practical Session`,
        section: labSection,
        dayOfWeek: labDay,
        timeSlot: labTime,
        roomNumber: labRoom,
        weeklyHours: Number(labHours),
        batchCapacity: Number(labCapacity),
      });

      showToast({
        type: "success",
        title: "Lab Assigned",
        message: `${labName} assigned to faculty schedule.`,
      });

      setLabModalOpen(false);
      setLabName("");
      loadFaculty();
    } catch {
      showToast({
        type: "error",
        title: "Assignment Failed",
        message: "Failed to link lab duty.",
      });
    }
  };

  // Handle Remove Lab
  const handleRemoveLab = async (labId: string) => {
    if (!faculty) return;
    await facultyService.removeLabAssignment(faculty.id, labId);
    showToast({
      type: "info",
      title: "Lab Removed",
      message: "Lab assignment removed from workload.",
    });
    loadFaculty();
  };

  // Handle Add Publication
  const handleCreatePublication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!faculty) return;
    try {
      await facultyService.createPublication(faculty.id, {
        title: pubTitle,
        venueName: pubVenue,
        publicationType: pubType,
        publicationYear: Number(pubYear),
        doi: pubDoi || undefined,
        status: pubStatus,
        authors: [`Dr. ${faculty.firstName} ${faculty.lastName}`],
      });

      showToast({
        type: "success",
        title: "Research Logged",
        message: `Publication "${pubTitle}" recorded in profile.`,
      });

      setPubModalOpen(false);
      setPubTitle("");
      setPubVenue("");
      setPubDoi("");
      loadFaculty();
    } catch {
      showToast({
        type: "error",
        title: "Submission Failed",
        message: "Could not log research publication.",
      });
    }
  };

  // Handle Delete Publication
  const handleDeletePublication = async (pubId: string) => {
    if (!faculty) return;
    await facultyService.deletePublication(faculty.id, pubId);
    showToast({
      type: "info",
      title: "Publication Removed",
      message: "Research entry removed from profile.",
    });
    loadFaculty();
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center text-slate-400 font-mono text-xs">
        Loading Faculty 360 Master Profile...
      </div>
    );
  }

  if (!faculty) {
    return (
      <div className="space-y-4">
        <Link href="/app/faculty">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Directory
          </Button>
        </Link>
        <EmptyState
          title="Faculty Member Not Found"
          description={`No faculty record exists with identifier "${facultyId}".`}
          actionLabel="Return to Faculty Directory"
          onAction={() => (window.location.href = "/app/faculty")}
        />
      </div>
    );
  }

  const workload = faculty.workloadSummary;
  const labDesignations = faculty.labDesignations || [];
  const publications = faculty.publications || [];

  const TABS = [
    { id: "overview", label: "Overview & Classes" },
    { id: "workload", label: `Workload (${workload?.totalAssignedHours || faculty.teachingLoadHours}h/wk)` },
    { id: "labs", label: `Lab Designations (${labDesignations.length})` },
    { id: "research", label: `Research & Publications (${publications.length})` },
    { id: "timeline", label: "Service Timeline" },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link href="/app/faculty">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Faculty Roster
          </Button>
        </Link>
      </div>

      {/* Main Faculty 360 Header Banner */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-xs backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-500/10 text-purple-600 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-500/20 text-2xl font-bold font-mono shrink-0">
              {faculty.firstName[0]}
              {faculty.lastName[0]}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  {faculty.firstName} {faculty.lastName}
                </h1>
                <Badge
                  variant={faculty.status === "ACTIVE" ? "success" : "secondary"}
                  dot
                >
                  {faculty.status}
                </Badge>
                <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  {faculty.employeeCode}
                </span>
              </div>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {faculty.designation} &bull; Department of {faculty.department}
              </p>

              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {faculty.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  {faculty.phone}
                </span>
                <span className="flex items-center gap-1.5">
                  <GraduationCap className="h-3.5 w-3.5 text-slate-400" />
                  {faculty.qualification}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center">
            <Button
              onClick={() => setActiveTab("workload")}
              variant="outline"
              size="sm"
              leftIcon={<Clock className="h-3.5 w-3.5" />}
            >
              Workload Plan
            </Button>
            <Button
              onClick={() => setActiveTab("research")}
              variant="primary"
              size="sm"
              leftIcon={<Award className="h-3.5 w-3.5" />}
            >
              Publications ({publications.length})
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* ======================================================== */}
      {/* TAB 1: OVERVIEW */}
      {/* ======================================================== */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Academic & Professional Background</CardTitle>
              <CardDescription>Highest educational degrees and areas of scholarly inquiry.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Designation</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{faculty.designation}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Department</span>
                <span className="text-slate-800 dark:text-slate-200">{faculty.department}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Highest Credential</span>
                <span className="text-slate-800 dark:text-slate-200 font-medium">{faculty.qualification}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Primary Specialization</span>
                <span className="text-slate-800 dark:text-slate-200">{faculty.specialization}</span>
              </div>
              <div className="grid grid-cols-2 py-1.5">
                <span className="text-slate-400">Appointment Date</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">{faculty.joiningDate}</span>
              </div>
            </CardContent>
          </Card>

          {/* Today's Classes */}
          <Card>
            <CardHeader>
              <CardTitle>Today&apos;s Lecture Schedule</CardTitle>
              <CardDescription>Classroom slots, halls, and attendance logging status.</CardDescription>
            </CardHeader>
            <CardContent>
              {faculty.todayClasses.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No lecture sessions scheduled today.</p>
              ) : (
                <div className="space-y-3">
                  {faculty.todayClasses.map((cls, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-slate-900 dark:text-white">{cls.subject}</div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {cls.time} &bull; {cls.room} &bull; {cls.section}
                        </p>
                      </div>
                      <Badge variant={cls.attendanceMarked ? "success" : "warning"} dot>
                        {cls.attendanceMarked ? "Logged" : "Pending"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: WORKLOAD MANAGEMENT */}
      {/* ======================================================== */}
      {activeTab === "workload" && (
        <div className="space-y-6">
          {/* Workload Progress Card */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Teaching Workload Allocation
                </h3>
                <p className="text-xs text-slate-500">
                  Academic Year 2026-2027 &bull; Semester 5 &bull; Target: {workload?.weeklyTargetHours || 16} hrs/week
                </p>
              </div>

              <Badge
                variant={
                  workload?.status === "HIGH_ALLOCATION"
                    ? "warning"
                    : workload?.status === "BALANCED"
                    ? "success"
                    : "secondary"
                }
              >
                {workload?.status || "BALANCED"}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 py-2">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Total Assigned</span>
                <div className="text-xl font-bold font-mono text-indigo-600 dark:text-indigo-400 mt-0.5">
                  {workload?.totalAssignedHours || faculty.teachingLoadHours} hrs/wk
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Lecture Theory</span>
                <div className="text-xl font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {workload?.lectureHours || 8} hrs/wk
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Lab Practicals</span>
                <div className="text-xl font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {workload?.labHours || 4} hrs/wk
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Weekly Target</span>
                <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                  {workload?.weeklyTargetHours || 16} hrs/wk
                </div>
              </div>
            </div>
          </div>

          {/* Assigned Course Sections */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-xs">
            <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-800 font-bold text-sm text-slate-900 dark:text-white">
              Assigned Course Sections & Student Enrollment
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Course Code</th>
                  <th className="px-4 py-3">Course Title</th>
                  <th className="px-4 py-3">Sem & Section</th>
                  <th className="px-4 py-3">Enrolled Cohort</th>
                  <th className="px-4 py-3 text-right">Weekly Load</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {(workload?.assignments || []).map((asg) => (
                  <tr key={asg.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {asg.code}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {asg.name}
                    </td>
                    <td className="px-4 py-3">
                      Sem {asg.semester} &bull; Sec {asg.section}
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {asg.studentCount} Students
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-semibold">
                      {asg.lectureHours + asg.labHours} hrs ({asg.lectureHours}L + {asg.labHours}P)
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: LAB DESIGNATIONS */}
      {/* ======================================================== */}
      {activeTab === "labs" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Laboratory Supervision & Practical Batches
              </h3>
              <p className="text-xs text-slate-500">
                Practical instruction venues, timing slots, and student batch capacities.
              </p>
            </div>
            {canManageWorkload && (
              <Button
                size="sm"
                variant="primary"
                leftIcon={<Plus className="h-3.5 w-3.5" />}
                onClick={() => setLabModalOpen(true)}
              >
                Assign Lab Duty
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {labDesignations.map((lab) => (
              <div
                key={lab.id}
                className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-xs"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <FlaskConical className="h-4 w-4 text-indigo-500 shrink-0" />
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                        {lab.labName}
                      </h4>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {lab.courseCode} &bull; Batch: {lab.section}
                    </p>
                  </div>
                  <Badge variant="secondary">
                    {lab.weeklyHours} hrs/wk
                  </Badge>
                </div>

                <div className="mt-4 space-y-1.5 text-xs text-slate-600 dark:text-slate-300 border-t border-slate-100 dark:border-slate-800 pt-3">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{lab.dayOfWeek} &bull; {lab.timeSlot}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Building className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{lab.roomNumber}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>Capacity: {lab.batchCapacity} workstations</span>
                  </div>
                </div>

                {canManageWorkload && (
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <Button
                      size="sm"
                      variant="ghost"
                      leftIcon={<Trash2 className="h-3.5 w-3.5 text-rose-500" />}
                      onClick={() => handleRemoveLab(lab.id)}
                    >
                      Release Duty
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: RESEARCH & PUBLICATIONS */}
      {/* ======================================================== */}
      {activeTab === "research" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Research Publications & Patents
              </h3>
              <p className="text-xs text-slate-500">
                Peer-reviewed journals, conference proceedings, patents, and scholarly output.
              </p>
            </div>
            {canAddPublication && (
              <Button
                size="sm"
                variant="primary"
                leftIcon={<Plus className="h-3.5 w-3.5" />}
                onClick={() => setPubModalOpen(true)}
              >
                Add Publication
              </Button>
            )}
          </div>

          <div className="space-y-4">
            {publications.map((pub) => (
              <div
                key={pub.id}
                className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-xs"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">{pub.publicationType}</Badge>
                      <Badge variant={pub.status === "PUBLISHED" ? "success" : "warning"}>
                        {pub.status}
                      </Badge>
                      <span className="text-xs font-mono text-slate-400">
                        {pub.publicationYear}
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-slate-900 dark:text-white mt-1.5">
                      {pub.title}
                    </h4>

                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {pub.venueName} &bull; Authors: {pub.authors.join(", ")}
                    </p>

                    {pub.abstractSummary && (
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-2 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                        {pub.abstractSummary}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {pub.doi && (
                      <span className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-1 rounded">
                        DOI: {pub.doi}
                      </span>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeletePublication(pub.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-rose-500" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 5: SERVICE TIMELINE */}
      {/* ======================================================== */}
      {activeTab === "timeline" && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
          <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
            Institutional Professorial Timeline
          </h3>
          <p className="text-xs text-slate-500 mb-6">
            Official promotions, committee appointments, and sabbatical grants.
          </p>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
            <div className="relative">
              <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
              <div className="text-xs">
                <span className="font-mono text-slate-400">2026-07-01</span>
                <h4 className="font-bold text-slate-900 dark:text-white mt-0.5">
                  Appointed Chair of Department Curriculum Scrutiny Committee
                </h4>
                <p className="text-slate-500">Board of Studies nomination for Autonomous Syllabus Formulation.</p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
              <div className="text-xs">
                <span className="font-mono text-slate-400">2023-08-15</span>
                <h4 className="font-bold text-slate-900 dark:text-white mt-0.5">
                  Promotion to Full Professor & Dean Academics
                </h4>
                <p className="text-slate-500">Conferred by University Governing Board following peer-review audit.</p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
              <div className="text-xs">
                <span className="font-mono text-slate-400">{faculty.joiningDate}</span>
                <h4 className="font-bold text-slate-900 dark:text-white mt-0.5">
                  Initial Faculty Appointment Induction
                </h4>
                <p className="text-slate-500">Joined CampusOS Academic Faculty as Assistant Professor.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODALS */}
      {/* ======================================================== */}

      {/* Assign Lab Modal */}
      <Dialog
        open={labModalOpen}
        onClose={() => setLabModalOpen(false)}
        title="Assign Laboratory Supervisory Responsibility"
      >
        <form onSubmit={handleAssignLab} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Laboratory Name *
            </label>
            <Input
              required
              value={labName}
              onChange={(e) => setLabName(e.target.value)}
              placeholder="e.g. Distributed Cloud Computing Lab"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Course Code
              </label>
              <Input
                value={labCourseCode}
                onChange={(e) => setLabCourseCode(e.target.value)}
                placeholder="CS301-L"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Batch / Section
              </label>
              <Input
                value={labSection}
                onChange={(e) => setLabSection(e.target.value)}
                placeholder="A-Batch 1"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Day of Week
              </label>
              <select
                value={labDay}
                onChange={(e) => setLabDay(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Time Slot
              </label>
              <Input
                value={labTime}
                onChange={(e) => setLabTime(e.target.value)}
                placeholder="02:00 PM - 04:00 PM"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Room / Venue
              </label>
              <Input
                value={labRoom}
                onChange={(e) => setLabRoom(e.target.value)}
                placeholder="Lab 304, Turing Block"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Weekly Hours
              </label>
              <Input
                type="number"
                value={labHours}
                onChange={(e) => setLabHours(e.target.value)}
                placeholder="2"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Batch Capacity
              </label>
              <Input
                type="number"
                value={labCapacity}
                onChange={(e) => setLabCapacity(e.target.value)}
                placeholder="32"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setLabModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Confirm Assignment
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Add Publication Modal */}
      <Dialog
        open={pubModalOpen}
        onClose={() => setPubModalOpen(false)}
        title="Record Research Publication / Scholarly Output"
      >
        <form onSubmit={handleCreatePublication} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Publication Title *
            </label>
            <Input
              required
              value={pubTitle}
              onChange={(e) => setPubTitle(e.target.value)}
              placeholder="Full scholarly title of the paper or patent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Publication Type
              </label>
              <select
                value={pubType}
                onChange={(e) => setPubType(e.target.value as PublicationType)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="JOURNAL">Peer-Reviewed Journal</option>
                <option value="CONFERENCE">Conference Proceedings</option>
                <option value="BOOK_CHAPTER">Book Chapter</option>
                <option value="PATENT">Patent Application</option>
                <option value="WORKSHOP">Workshop Paper</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Year of Publication
              </label>
              <Input
                value={pubYear}
                onChange={(e) => setPubYear(e.target.value)}
                placeholder="2026"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Journal / Conference / Publisher Name *
            </label>
            <Input
              required
              value={pubVenue}
              onChange={(e) => setPubVenue(e.target.value)}
              placeholder="e.g. IEEE Transactions on Cloud Computing"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                DOI / Serial Code
              </label>
              <Input
                value={pubDoi}
                onChange={(e) => setPubDoi(e.target.value)}
                placeholder="10.1109/TCC.2026.001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Status
              </label>
              <select
                value={pubStatus}
                onChange={(e) => setPubStatus(e.target.value as PublicationStatus)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="PUBLISHED">PUBLISHED</option>
                <option value="ACCEPTED">ACCEPTED (In Press)</option>
                <option value="SUBMITTED">SUBMITTED (Under Peer Review)</option>
                <option value="DRAFT">DRAFT</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setPubModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Save Publication
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
