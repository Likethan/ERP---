"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import { staffService } from "@/services/staff.service";
import { studentsService } from "@/services/students.service";
import {
  CourseOfferingDetail,
  FacultyAssignmentRole,
  StudentCourseEnrollmentRecord,
  ScheduledTimetableEntry,
} from "@/types/academics";
import { StaffDetailView } from "@/types/domain";
import { StudentComprehensiveDetail } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import {
  CheckSquare,
  ArrowLeft,
  Users,
  GraduationCap,
  Calendar,
  Clock,
  Plus,
  Trash2,
  AlertTriangle,
  BookOpen,
  UserCheck,
  ShieldCheck,
  Building,
} from "lucide-react";

interface CourseOfferingDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CourseOfferingDetailPage({ params }: CourseOfferingDetailPageProps) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const { showToast } = useToast();
  const { hasPermission } = useAuth();

  const [offering, setOffering] = useState<CourseOfferingDetail | null>(null);
  const [enrollments, setEnrollments] = useState<StudentCourseEnrollmentRecord[]>([]);
  const [scheduledPeriods, setScheduledPeriods] = useState<ScheduledTimetableEntry[]>([]);
  const [availableFaculty, setAvailableFaculty] = useState<StaffDetailView[]>([]);
  const [availableStudents, setAvailableStudents] = useState<StudentComprehensiveDetail[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "faculty" | "students" | "timetable">("overview");
  const [loading, setLoading] = useState(true);

  // Assign Faculty Dialog
  const [assignFacultyModalOpen, setAssignFacultyModalOpen] = useState(false);
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [assignmentRole, setAssignmentRole] = useState<FacultyAssignmentRole>("PRIMARY_INSTRUCTOR");
  const [assignedHours, setAssignedHours] = useState<number>(4);
  const [isAssigning, setIsAssigning] = useState(false);

  // Enroll Student Dialog
  const [enrollModalOpen, setEnrollModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [isEnrolling, setIsEnrolling] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [offRes, enrRes, ttRes, staffRes, studRes] = await Promise.all([
          academicsService.getCourseOfferingDetailById(id),
          academicsService.getStudentCourseEnrollments({ courseOfferingId: id }),
          academicsService.getScheduledTimetable(),
          staffService.list(),
          studentsService.list(),
        ]);

        if (offRes.data) {
          setOffering(offRes.data);
          setEnrollments(enrRes.data);
          // Match timetable periods for this offering
          const periods = ttRes.data.filter(
            (t: ScheduledTimetableEntry) =>
              t.courseOfferingId === id ||
              (t.subjectCode === offRes.data!.subjectCode && t.section === offRes.data!.section)
          );
          setScheduledPeriods(periods);
          setAvailableFaculty(staffRes.data);
          setAvailableStudents(studRes.data);
        }
      } catch (err) {
        console.error("Failed to load offering details:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  // Handle Faculty Assignment with conflict detection
  const handleAssignFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offering || !selectedStaffId) return;

    // Check if faculty already assigned
    const alreadyAssigned = offering.facultyAssignments.some((f) => f.facultyId === selectedStaffId);
    if (alreadyAssigned) {
      showToast({
        title: "Assignment Conflict",
        message: "This faculty member is already assigned to this course offering.",
        type: "error",
      });
      return;
    }

    const staffObj = availableFaculty.find((s) => s.id === selectedStaffId);
    if (!staffObj) return;

    try {
      setIsAssigning(true);
      const res = await academicsService.assignFacultyToOffering(offering.id, {
        facultyId: staffObj.id,
        facultyName: `${staffObj.firstName} ${staffObj.lastName}`,
        employeeCode: staffObj.employeeCode,
        email: staffObj.email,
        role: assignmentRole,
        assignedWeeklyHours: assignedHours,
        status: "CONFIRMED",
      });

      if (res.success) {
        setOffering({ ...res.data });
        showToast({
          title: "Faculty Assigned",
          message: `Assigned ${staffObj.firstName} ${staffObj.lastName} as ${assignmentRole.replace("_", " ")}`,
          type: "success",
        });
        setAssignFacultyModalOpen(false);
        setSelectedStaffId("");
      }
    } catch (err: any) {
      showToast({ title: "Failed to assign faculty", message: err.message, type: "error" });
    } finally {
      setIsAssigning(false);
    }
  };

  // Remove Faculty Assignment
  const handleRemoveFaculty = async (assignmentId: string) => {
    if (!offering) return;
    try {
      const res = await academicsService.removeFacultyFromOffering(offering.id, assignmentId);
      if (res.success) {
        setOffering({ ...res.data });
        showToast({ title: "Faculty assignment removed", type: "info" });
      }
    } catch (err: any) {
      showToast({ title: "Failed to remove assignment", message: err.message, type: "error" });
    }
  };

  // Handle Enroll Student
  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offering || !selectedStudentId) return;

    const studObj = availableStudents.find((s) => s.id === selectedStudentId);
    if (!studObj) return;

    try {
      setIsEnrolling(true);
      const res = await academicsService.enrollStudent({
        studentId: studObj.id,
        studentName: `${studObj.firstName} ${studObj.lastName}`,
        rollNumber: studObj.rollNumber,
        program: offering.programName,
        department: offering.department,
        academicYear: offering.academicYear,
        semester: offering.semester,
        section: offering.section,
        courseOfferingId: offering.id,
        subjectCode: offering.subjectCode,
        subjectName: offering.subjectName,
        credits: offering.credits,
        isElective: false,
      });

      if (res.success) {
        setEnrollments((prev) => [res.data, ...prev]);
        setOffering((prev) => (prev ? { ...prev, enrolledCount: prev.enrolledCount + 1 } : null));
        showToast({
          title: "Student Registered",
          message: `Enrolled ${studObj.firstName} in ${offering.subjectCode}`,
          type: "success",
        });
        setEnrollModalOpen(false);
        setSelectedStudentId("");
      }
    } catch (err: any) {
      showToast({ title: "Enrollment failed", message: err.message, type: "error" });
    } finally {
      setIsEnrolling(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
          ))}
        </div>
        <TableSkeleton rows={5} />
      </div>
    );
  }

  if (!offering) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center">
        <CheckSquare className="mx-auto h-12 w-12 text-slate-600 mb-3" />
        <h3 className="text-lg font-semibold text-white">Course Offering Not Found</h3>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          The requested course offering with identifier &ldquo;{id}&rdquo; was not found.
        </p>
        <Link href="/app/academics/course-offerings">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Course Offerings
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/academics" className="hover:text-white transition-colors">
              Academics
            </Link>
            <span>/</span>
            <Link href="/app/academics/course-offerings" className="hover:text-white transition-colors">
              Offerings
            </Link>
            <span>/</span>
            <span className="text-white font-mono">{offering.subjectCode} (Sec {offering.section})</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              {offering.subjectCode} — Section {offering.section}
            </h1>
            <Badge variant="info">Sem {offering.semester}</Badge>
            <Badge variant={offering.status === "ACTIVE" ? "success" : "info"} dot>
              {offering.status}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {offering.subjectName} • {offering.programName} ({offering.department}) • AY {offering.academicYear}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/course-offerings">
            <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}>
              Back to Offerings
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Plus className="h-3.5 w-3.5" />}
            onClick={() => setAssignFacultyModalOpen(true)}
          >
            Assign Faculty
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<UserCheck className="h-3.5 w-3.5" />}
            onClick={() => setEnrollModalOpen(true)}
          >
            Register Student
          </Button>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Enrolled Students</div>
          <div className="mt-1 text-2xl font-bold text-indigo-400 font-mono">
            {offering.enrolledCount} / {offering.maxCapacity}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {Math.round((offering.enrolledCount / offering.maxCapacity) * 100)}% Capacity filled
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Assigned Faculty</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400 font-mono">
            {offering.facultyAssignments.length} Staff
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {offering.facultyAssignments.length === 0 ? "Staffing required" : "Primary instructor active"}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Scheduled Periods</div>
          <div className="mt-1 text-2xl font-bold text-sky-400 font-mono">
            {scheduledPeriods.length} Periods/Wk
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">In master timetable</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Credits / Hours</div>
          <div className="mt-1 text-2xl font-bold text-white font-mono">
            {offering.credits} Cr ({offering.lectureHours}L - {offering.labHours}P)
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Contact load</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800 text-xs">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "overview"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <BookOpen className="h-3.5 w-3.5" />
          Overview & Config
        </button>
        <button
          onClick={() => setActiveTab("faculty")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "faculty"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <GraduationCap className="h-3.5 w-3.5" />
          Faculty Instructors
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {offering.facultyAssignments.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("students")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "students"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Users className="h-3.5 w-3.5" />
          Enrolled Cohort
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {enrollments.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("timetable")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "timetable"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Calendar className="h-3.5 w-3.5" />
          Timetable Slots
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {scheduledPeriods.length}
          </span>
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Course Offering Specification</CardTitle>
                <CardDescription>
                  Autonomous academic curriculum delivery parameters.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs text-slate-300">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40">
                    <span className="text-slate-400 block mb-1">Subject Identity</span>
                    <span className="font-semibold text-white font-mono text-sm">{offering.subjectCode}</span>
                    <span className="block text-slate-300 mt-0.5">{offering.subjectName}</span>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40">
                    <span className="text-slate-400 block mb-1">Section Cohort</span>
                    <span className="font-semibold text-white font-mono text-sm">
                      Semester {offering.semester} • Section {offering.section}
                    </span>
                    <span className="block text-slate-300 mt-0.5">{offering.programName}</span>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-2">
                  <h4 className="text-xs font-semibold text-white">Instructional Workload</h4>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-2 rounded bg-slate-800/60">
                      <div className="text-[10px] text-slate-400">Lectures</div>
                      <div className="text-sm font-bold text-white font-mono">{offering.lectureHours} hrs/wk</div>
                    </div>
                    <div className="p-2 rounded bg-slate-800/60">
                      <div className="text-[10px] text-slate-400">Practicals/Labs</div>
                      <div className="text-sm font-bold text-white font-mono">{offering.labHours} hrs/wk</div>
                    </div>
                    <div className="p-2 rounded bg-slate-800/60">
                      <div className="text-[10px] text-slate-400">Credits</div>
                      <div className="text-sm font-bold text-indigo-400 font-mono">{offering.credits} Cr</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Offering Status & Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Current Status</span>
                  <Badge variant={offering.status === "ACTIVE" ? "success" : "info"} dot>
                    {offering.status}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Academic Year</span>
                  <span className="font-mono text-white">{offering.academicYear}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Enrolled Count</span>
                  <span className="font-mono text-indigo-400 font-bold">{offering.enrolledCount} Students</span>
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <Link href={`/app/academics/subjects/${offering.subjectId || offering.subjectCode}`}>
                    <Button variant="outline" size="sm" className="w-full text-xs" leftIcon={<BookOpen className="h-3.5 w-3.5" />}>
                      View Subject Master
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Faculty */}
      {activeTab === "faculty" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Assigned Faculty Staff</CardTitle>
              <CardDescription>
                Faculty members delivering lectures, laboratories, and tutorials for this section.
              </CardDescription>
            </div>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setAssignFacultyModalOpen(true)}
            >
              Assign Faculty
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {offering.facultyAssignments.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-400">
                <p>No faculty members are assigned to this course offering yet.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  leftIcon={<Plus className="h-3.5 w-3.5" />}
                  onClick={() => setAssignFacultyModalOpen(true)}
                >
                  Assign Primary Instructor
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Faculty Name</th>
                      <th className="px-4 py-3">Instructional Role</th>
                      <th className="px-4 py-3">Weekly Hours</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {offering.facultyAssignments.map((fac) => (
                      <tr key={fac.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-medium text-white">
                          <div className="font-semibold">{fac.facultyName}</div>
                          <div className="text-[11px] text-slate-400 font-mono">{fac.employeeCode} • {fac.email}</div>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="font-mono text-xs text-indigo-300">
                            {fac.role.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono text-white font-medium">
                          {fac.assignedWeeklyHours} hrs/wk
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant={fac.status === "CONFIRMED" ? "success" : "warning"} dot>
                            {fac.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <button
                            onClick={() => handleRemoveFaculty(fac.id)}
                            className="p-1 text-slate-400 hover:text-red-400 transition-colors rounded hover:bg-red-500/10"
                            title="Remove assignment"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Enrolled Students */}
      {activeTab === "students" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Enrolled Students Roster ({enrollments.length})</CardTitle>
              <CardDescription>
                Students registered in Section {offering.section} for {offering.subjectCode}.
              </CardDescription>
            </div>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setEnrollModalOpen(true)}
            >
              Enroll Student
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {enrollments.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-400">
                No students enrolled in this offering yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Roll Number</th>
                      <th className="px-4 py-3">Student Name</th>
                      <th className="px-4 py-3">Registered Date</th>
                      <th className="px-4 py-3">Attendance</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {enrollments.map((enr) => (
                      <tr key={enr.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-mono font-semibold text-indigo-300">
                          {enr.rollNumber}
                        </td>
                        <td className="px-4 py-3.5 font-medium text-white">{enr.studentName}</td>
                        <td className="px-4 py-3.5 font-mono text-slate-400">{enr.enrolledDate}</td>
                        <td className="px-4 py-3.5 font-mono text-emerald-400">
                          {enr.attendanceRate || 100}%
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant="success" dot>{enr.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Timetable Slots */}
      {activeTab === "timetable" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Timetable Periods Scheduled</CardTitle>
              <CardDescription>
                Live periods assigned in master timetable for {offering.subjectCode} (Section {offering.section}).
              </CardDescription>
            </div>
            <Link href="/app/academics/timetable">
              <Button variant="outline" size="sm" leftIcon={<Calendar className="h-3.5 w-3.5" />}>
                Master Timetable
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {scheduledPeriods.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-400">
                No timetable slots scheduled for this course offering yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Day</th>
                      <th className="px-4 py-3">Time Window</th>
                      <th className="px-4 py-3">Room & Venue</th>
                      <th className="px-4 py-3">Instructor</th>
                      <th className="px-4 py-3">Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {scheduledPeriods.map((slot) => (
                      <tr key={slot.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-semibold text-white">
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-200 border border-slate-700">
                            {slot.day}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono text-indigo-300">
                          {slot.startTime} – {slot.endTime}
                        </td>
                        <td className="px-4 py-3.5 text-slate-200">
                          <span className="font-medium">{slot.roomNumber}</span>
                          <span className="text-[11px] text-slate-400 block">{slot.building}</span>
                        </td>
                        <td className="px-4 py-3.5 text-slate-200">{slot.facultyName}</td>
                        <td className="px-4 py-3.5">
                          <Badge variant="info">{slot.entryType}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Assign Faculty Dialog */}
      <Dialog
        open={assignFacultyModalOpen}
        onClose={() => setAssignFacultyModalOpen(false)}
        title="Assign Faculty Instructor"
      >
        <form onSubmit={handleAssignFaculty} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Faculty Member <span className="text-red-400">*</span>
            </label>
            <select
              value={selectedStaffId}
              onChange={(e) => setSelectedStaffId(e.target.value)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">-- Choose Instructor --</option>
              {availableFaculty.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.firstName} {f.lastName} ({f.employeeCode}) • {f.department}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Role</label>
              <select
                value={assignmentRole}
                onChange={(e) => setAssignmentRole(e.target.value as FacultyAssignmentRole)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                <option value="PRIMARY_INSTRUCTOR">Primary Instructor</option>
                <option value="CO_INSTRUCTOR">Co-Instructor</option>
                <option value="LAB_INSTRUCTOR">Lab Instructor</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Weekly Assigned Hours</label>
              <Input
                type="number"
                min="1"
                max="12"
                value={assignedHours}
                onChange={(e) => setAssignedHours(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAssignFacultyModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isAssigning}
              disabled={!selectedStaffId}
            >
              Confirm Assignment
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Enroll Student Dialog */}
      <Dialog
        open={enrollModalOpen}
        onClose={() => setEnrollModalOpen(false)}
        title="Direct Student Course Registration"
      >
        <form onSubmit={handleEnrollStudent} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Student from Cohort <span className="text-red-400">*</span>
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">-- Choose Student --</option>
              {availableStudents.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.rollNumber} - {s.firstName} {s.lastName} (Sem {s.currentSemester} Sec {s.section})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEnrollModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isEnrolling}
              disabled={!selectedStudentId}
            >
              Register into Section
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
