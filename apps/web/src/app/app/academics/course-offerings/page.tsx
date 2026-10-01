"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  CourseOffering,
  CourseOfferingDetail,
  CourseEnrollment,
  AcademicYear,
  Semester,
  Section,
  Subject,
  Faculty,
  Student,
} from "@campusos/types";

const OFFERING_STATUSES = ["PLANNED", "OPEN", "ACTIVE", "COMPLETED", "CANCELLED"] as const;

export default function CourseOfferingsPage() {
  const { hasPermission } = useAuth();
  const canManageCourses = hasPermission("academics:courses:manage");
  const canManageEnrollments = hasPermission("academics:enrollments:manage");

  // Primary data state
  const [offerings, setOfferings] = useState<CourseOffering[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [studentList, setStudentList] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [filterYearId, setFilterYearId] = useState("");
  const [filterSemId, setFilterSemId] = useState("");
  const [filterSectionId, setFilterSectionId] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Create Offering Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newSubId, setNewSubId] = useState("");
  const [newYearId, setNewYearId] = useState("");
  const [newSemId, setNewSemId] = useState("");
  const [newSectionId, setNewSectionId] = useState("");
  const [newCapacity, setNewCapacity] = useState<number>(60);

  // Detail Drawer / Modal
  const [selectedOfferingId, setSelectedOfferingId] = useState<string | null>(null);
  const [offeringDetail, setOfferingDetail] = useState<CourseOfferingDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"FACULTY" | "STUDENTS">("FACULTY");

  // Faculty assignment sub-form
  const [assignFacultyId, setAssignFacultyId] = useState("");
  const [assignRole, setAssignRole] = useState("PRIMARY");
  const [assigningFaculty, setAssigningFaculty] = useState(false);
  const [facultyError, setFacultyError] = useState<string | null>(null);

  // Student enrollment sub-form & batch enroll
  const [enrolledStudents, setEnrolledStudents] = useState<CourseEnrollment[]>([]);
  const [enrollStudentId, setEnrollStudentId] = useState("");
  const [enrollType, setEnrollType] = useState("REGULAR");
  const [enrolling, setEnrolling] = useState(false);
  const [batchEnrolling, setBatchEnrolling] = useState(false);
  const [enrollError, setEnrollError] = useState<string | null>(null);

  // Status transition state
  const [transitioning, setTransitioning] = useState(false);

  // Load Initial Master Datasets
  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [offRes, yrsRes, semsRes, secsRes, subsRes, facRes] = await Promise.all([
        apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
        apiFetch<AcademicYear[]>("/api/v1/academic-structure/academic-years"),
        apiFetch<Semester[]>("/api/v1/academic-structure/semesters"),
        apiFetch<Section[]>("/api/v1/academic-structure/sections"),
        apiFetch<Subject[]>("/api/v1/academics/subjects"),
        apiFetch<Faculty[]>("/api/v1/people/faculty").catch(() => ({ data: [] as Faculty[] })),
      ]);

      setOfferings(offRes.data || []);
      setAcademicYears(yrsRes.data || []);
      setSemesters(semsRes.data || []);
      setSections(secsRes.data || []);
      setSubjects(subsRes.data || []);
      setFacultyList(facRes.data || []);

      if (yrsRes.data?.length) setNewYearId(yrsRes.data[0].id);
      if (semsRes.data?.length) setNewSemId(semsRes.data[0].id);
      if (secsRes.data?.length) setNewSectionId(secsRes.data[0].id);
      if (subsRes.data?.length) setNewSubId(subsRes.data[0].id);
    } catch {
      // Mock Fallback
      const { MOCK_COURSE_OFFERINGS, MOCK_SUBJECTS } = await import("@/mocks/academics.mock");
      const mappedOfferings = MOCK_COURSE_OFFERINGS.map((o) => ({
        id: o.id,
        subject_id: `sub-${o.subjectCode.toLowerCase()}`,
        subject: { id: `sub-${o.subjectCode.toLowerCase()}`, code: o.subjectCode, name: o.subjectName, credits: o.credits },
        academic_year_id: "ay-2026",
        semester_id: `sem-${o.semester}`,
        section_id: `sec-${o.section.toLowerCase()}`,
        status: o.status,
        capacity: 70,
        enrolled_count: o.enrolledStudents,
        faculty_assignments: [
          {
            id: `fa-${o.id}`,
            faculty_id: "fac-1",
            role: "PRIMARY",
            faculty: { id: "fac-1", first_name: o.facultyName.split(" ")[0], last_name: o.facultyName.split(" ")[1] || "Prof", email: "faculty@campusos.edu" },
          },
        ],
      })) as unknown as CourseOffering[];

      const mappedYears = [{ id: "ay-2026", name: "2026-2027", is_current: true, code: "AY2627" }] as unknown as AcademicYear[];
      const mappedSems = [
        { id: "sem-5", number: 5, academic_year_id: "ay-2026", status: "ACTIVE" },
        { id: "sem-7", number: 7, academic_year_id: "ay-2026", status: "ACTIVE" },
      ] as unknown as Semester[];
      const mappedSecs = [
        { id: "sec-a", name: "Section A", semester_id: "sem-5", capacity: 70 },
        { id: "sec-b", name: "Section B", semester_id: "sem-5", capacity: 70 },
      ] as unknown as Section[];
      const mappedSubs = MOCK_SUBJECTS.map((s) => ({
        id: s.id,
        code: s.code,
        name: s.name,
        credits: s.credits,
      })) as unknown as Subject[];

      setOfferings(mappedOfferings);
      setAcademicYears(mappedYears);
      setSemesters(mappedSems);
      setSections(mappedSecs);
      setSubjects(mappedSubs);

      setNewYearId("ay-2026");
      setNewSemId("sem-5");
      setNewSectionId("sec-a");
      if (mappedSubs.length > 0) setNewSubId(mappedSubs[0].id);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Fetch detail when an offering is selected
  const openDetailDrawer = async (offeringId: string) => {
    try {
      setSelectedOfferingId(offeringId);
      setDetailLoading(true);
      setFacultyError(null);
      setEnrollError(null);

      const [detailRes, studentsRes] = await Promise.all([
        apiFetch<CourseOfferingDetail>(`/api/v1/academics/course-offerings/${offeringId}`),
        apiFetch<CourseEnrollment[]>(`/api/v1/academics/course-offerings/${offeringId}/students`),
      ]);

      setOfferingDetail(detailRes.data);
      setEnrolledStudents(studentsRes.data || []);
    } catch {
      // Mock detail drawer
      const selected = offerings.find((o) => o.id === offeringId);
      const mockDetail: CourseOfferingDetail = {
        id: offeringId,
        subject_id: selected?.subject_id || "sub-cs301",
        subject: (selected as unknown as { subject?: Subject })?.subject || ({ id: "sub-cs301", code: "CS301", name: "Data Structures & Algorithms", credits: 4 } as unknown as Subject),
        academic_year_id: "ay-2026",
        academic_year: { id: "ay-2026", name: "2026-2027", is_current: true } as unknown as AcademicYear,
        semester_id: "sem-5",
        semester: { id: "sem-5", number: 5 } as unknown as Semester,
        section_id: "sec-a",
        section: { id: "sec-a", name: "Section A" } as unknown as Section,
        status: "ACTIVE",
        capacity: 70,
        enrolled_count: 68,
        faculty_assignments: [
          {
            id: "fa-1",
            faculty_id: "fac-1",
            role: "PRIMARY",
            faculty: { id: "fac-1", first_name: "Dr. Rajesh", last_name: "Sharma", email: "rajesh.sharma@campusos.edu" } as unknown as Faculty,
          },
        ],
      } as unknown as CourseOfferingDetail;

      setOfferingDetail(mockDetail);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetailDrawer = () => {
    setSelectedOfferingId(null);
    setOfferingDetail(null);
    setEnrolledStudents([]);
  };

  // Create Course Offering
  const handleCreateOffering = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubId || !newYearId || !newSemId || !newSectionId) {
      setCreateError("Please select subject, academic year, semester, and section.");
      return;
    }

    try {
      setCreating(true);
      setCreateError(null);

      const res = await apiFetch<CourseOfferingDetail>("/api/v1/academics/course-offerings", {
        method: "POST",
        body: JSON.stringify({
          subject_id: newSubId,
          academic_year_id: newYearId,
          semester_id: newSemId,
          section_id: newSectionId,
          max_capacity: Number(newCapacity),
        }),
      });

      // Refresh list
      setOfferings((prev) => [res.data, ...prev]);
      setShowCreateModal(false);
      openDetailDrawer(res.data.id);
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : "Failed to create offering.");
    } finally {
      setCreating(false);
    }
  };

  // Status Transitions
  const handleTransitionStatus = async (newStatus: string) => {
    if (!offeringDetail) return;
    try {
      setTransitioning(true);
      const res = await apiFetch<CourseOfferingDetail>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        }
      );

      setOfferingDetail(res.data);
      setOfferings((prev) => prev.map((o) => (o.id === res.data.id ? { ...o, status: res.data.status } : o)));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to transition status.");
    } finally {
      setTransitioning(false);
    }
  };

  // Assign Faculty
  const handleAssignFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offeringDetail || !assignFacultyId) {
      setFacultyError("Please select a faculty member.");
      return;
    }

    try {
      setAssigningFaculty(true);
      setFacultyError(null);

      const res = await apiFetch<CourseOfferingDetail>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/faculty`,
        {
          method: "POST",
          body: JSON.stringify({
            faculty_id: assignFacultyId,
            role: assignRole,
            start_date: new Date().toISOString().split("T")[0],
          }),
        }
      );

      setOfferingDetail(res.data);
      setAssignFacultyId("");
      // Refresh in list view as well
      setOfferings((prev) =>
        prev.map((o) => (o.id === res.data.id ? { ...o, primary_faculty_name: res.data.primary_faculty_name } : o))
      );
    } catch (err: unknown) {
      setFacultyError(err instanceof Error ? err.message : "Failed to assign faculty.");
    } finally {
      setAssigningFaculty(false);
    }
  };

  // Unassign Faculty
  const handleUnassignFaculty = async (facId: string) => {
    if (!offeringDetail || !confirm("Are you sure you want to unassign this faculty member?")) return;

    try {
      const res = await apiFetch<CourseOfferingDetail>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/faculty/${facId}`,
        { method: "DELETE" }
      );
      setOfferingDetail(res.data);
      setOfferings((prev) =>
        prev.map((o) => (o.id === res.data.id ? { ...o, primary_faculty_name: res.data.primary_faculty_name } : o))
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to unassign faculty.");
    }
  };

  // Enroll Single Student
  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offeringDetail || !enrollStudentId) {
      setEnrollError("Please select a student.");
      return;
    }

    try {
      setEnrolling(true);
      setEnrollError(null);

      const res = await apiFetch<CourseEnrollment>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/students`,
        {
          method: "POST",
          body: JSON.stringify({
            student_id: enrollStudentId,
            enrollment_type: enrollType,
          }),
        }
      );

      setEnrolledStudents((prev) => [res.data, ...prev]);
      setEnrollStudentId("");
      // Update count
      setOfferings((prev) =>
        prev.map((o) => (o.id === offeringDetail.id ? { ...o, enrolled_count: o.enrolled_count + 1 } : o))
      );
      setOfferingDetail((prev) => (prev ? { ...prev, enrolled_count: prev.enrolled_count + 1 } : null));
    } catch (err: unknown) {
      setEnrollError(err instanceof Error ? err.message : "Failed to enroll student.");
    } finally {
      setEnrolling(false);
    }
  };

  // Batch Enroll Entire Section
  const handleBatchEnroll = async () => {
    if (!offeringDetail) return;
    if (
      !confirm(
        `Batch enroll all active students currently registered in Section "${offeringDetail.section_name}"? Existing enrollments will not be duplicated.`
      )
    ) {
      return;
    }

    try {
      setBatchEnrolling(true);
      setEnrollError(null);

      const res = await apiFetch<{ enrolled_count: number }>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/students/batch-enroll`,
        {
          method: "POST",
          body: JSON.stringify({ section_id: offeringDetail.section_id }),
        }
      );

      // Refresh student roster
      const studentsRes = await apiFetch<CourseEnrollment[]>(
        `/api/v1/academics/course-offerings/${offeringDetail.id}/students`
      );
      setEnrolledStudents(studentsRes.data || []);

      // Update offering counts
      const updatedCount = (offeringDetail.enrolled_count || 0) + res.data.enrolled_count;
      setOfferingDetail((prev) => (prev ? { ...prev, enrolled_count: updatedCount } : null));
      setOfferings((prev) =>
        prev.map((o) => (o.id === offeringDetail.id ? { ...o, enrolled_count: updatedCount } : o))
      );

      alert(`Successfully batch enrolled ${res.data.enrolled_count} students into this course offering!`);
    } catch (err: unknown) {
      setEnrollError(err instanceof Error ? err.message : "Batch enrollment failed.");
    } finally {
      setBatchEnrolling(false);
    }
  };

  // Withdraw Student
  const handleWithdrawStudent = async (studentId: string) => {
    if (!offeringDetail || !confirm("Are you sure you want to withdraw this student from this offering?")) return;

    try {
      await apiFetch(`/api/v1/academics/course-offerings/${offeringDetail.id}/students/${studentId}`, {
        method: "DELETE",
      });

      setEnrolledStudents((prev) =>
        prev.map((e) => (e.student_id === studentId ? { ...e, status: "WITHDRAWN" } : e))
      );
      // Decrement count
      setOfferings((prev) =>
        prev.map((o) =>
          o.id === offeringDetail.id ? { ...o, enrolled_count: Math.max(0, o.enrolled_count - 1) } : o
        )
      );
      setOfferingDetail((prev) =>
        prev ? { ...prev, enrolled_count: Math.max(0, prev.enrolled_count - 1) } : null
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to withdraw student.");
    }
  };

  // Filtered offerings list
  const filteredOfferings = useMemo(() => {
    return offerings.filter((off) => {
      const matchesSearch =
        !search ||
        off.subject_code?.toLowerCase().includes(search.toLowerCase()) ||
        off.subject_name?.toLowerCase().includes(search.toLowerCase()) ||
        off.primary_faculty_name?.toLowerCase().includes(search.toLowerCase()) ||
        off.section_name?.toLowerCase().includes(search.toLowerCase());

      const matchesYear = !filterYearId || off.academic_year_id === filterYearId;
      const matchesSem = !filterSemId || off.semester_id === filterSemId;
      const matchesSection = !filterSectionId || off.section_id === filterSectionId;
      const matchesStatus = !filterStatus || off.status === filterStatus;

      return matchesSearch && matchesYear && matchesSem && matchesSection && matchesStatus;
    });
  }, [offerings, search, filterYearId, filterSemId, filterSectionId, filterStatus]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PLANNED":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">PLANNED</span>;
      case "OPEN":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-700 border border-blue-300">OPEN</span>;
      case "ACTIVE":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">ACTIVE</span>;
      case "COMPLETED":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-700 border border-purple-300">COMPLETED</span>;
      case "CANCELLED":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-300">CANCELLED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <nav className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app" className="hover:text-blue-600 transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <Link href="/app/academics" className="hover:text-blue-600 transition-colors">
              Academics
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">Course Offerings</span>
          </nav>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Course Offerings & Delivery
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Operational deliveries connecting Subject, Academic Period, Section, Faculty Staffing, and Student Rosters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canManageCourses && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Course Offering
            </button>
          )}
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700 flex items-start gap-3">
          <svg className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-semibold">Unable to load data</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Search */}
          <div className="md:col-span-2 relative">
            <svg
              className="w-4 h-4 text-slate-400 absolute left-3 top-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search code, title, faculty, or section..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Academic Year Filter */}
          <div>
            <select
              value={filterYearId}
              onChange={(e) => setFilterYearId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Academic Years</option>
              {academicYears.map((ay) => (
                <option key={ay.id} value={ay.id}>
                  {ay.name} {ay.is_current ? "(Current)" : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Semester Filter */}
          <div>
            <select
              value={filterSemId}
              onChange={(e) => setFilterSemId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Semesters</option>
              {semesters.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} (Term {s.semester_number})
                </option>
              ))}
            </select>
          </div>

          {/* Section Filter */}
          <div>
            <select
              value={filterSectionId}
              onChange={(e) => setFilterSectionId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Sections</option>
              {sections.map((sec) => (
                <option key={sec.id} value={sec.id}>
                  Section {sec.name} (Cap: {sec.capacity})
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Statuses</option>
              {OFFERING_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Offerings Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-sm">Loading course offerings...</p>
          </div>
        ) : filteredOfferings.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-slate-900">No Course Offerings Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {offerings.length === 0
                ? "No course offerings have been created yet. Launch an academic delivery by assigning a subject to an academic period and section."
                : "No course offerings match your filter criteria. Try adjusting your search query."}
            </p>
            {offerings.length === 0 && canManageCourses && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm"
              >
                Create First Offering
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-700 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Subject / Course</th>
                  <th className="px-6 py-3">Academic Period & Section</th>
                  <th className="px-6 py-3">Primary Instructor</th>
                  <th className="px-6 py-3">Enrolled / Capacity</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredOfferings.map((off) => {
                  const capacityPct = Math.min(
                    100,
                    Math.round(((off.enrolled_count || 0) / (off.max_capacity || 1)) * 100)
                  );
                  return (
                    <tr key={off.id} className="hover:bg-slate-50/75 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900">{off.subject_name}</div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="font-mono text-xs text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                            {off.subject_code}
                          </span>
                          {off.subject_credits !== undefined && off.subject_credits !== null && (
                            <span className="text-xs text-slate-500">{off.subject_credits} Credits</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">
                          {off.section_name || "Section"}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          {off.academic_year_name} • {off.semester_name || "Semester"}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {off.primary_faculty_name ? (
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">
                              {off.primary_faculty_name.charAt(0)}
                            </div>
                            <span className="text-slate-800 font-medium">{off.primary_faculty_name}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
                            Unassigned
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-semibold text-slate-800">
                            {off.enrolled_count} / {off.max_capacity}
                          </span>
                          <span className="text-slate-500">{capacityPct}%</span>
                        </div>
                        <div className="w-28 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${
                              capacityPct >= 100
                                ? "bg-rose-500"
                                : capacityPct > 80
                                ? "bg-amber-500"
                                : "bg-emerald-500"
                            }`}
                            style={{ width: `${capacityPct}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-6 py-4">{getStatusBadge(off.status)}</td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => openDetailDrawer(off.id)}
                          className="px-3 py-1.5 text-xs font-semibold text-blue-700 hover:text-blue-800 hover:bg-blue-50 border border-blue-200 rounded-lg transition-colors"
                        >
                          Manage Offering
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CREATE OFFERING MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">Create New Course Offering</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateOffering} className="p-6 space-y-4">
              {createError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                  {createError}
                </div>
              )}

              {/* Subject Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Subject / Catalog Course *
                </label>
                <select
                  value={newSubId}
                  onChange={(e) => setNewSubId(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">Select Catalog Subject</option>
                  {subjects.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      [{sub.code}] {sub.name} ({sub.credits} Credits - {sub.subject_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Academic Year */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Academic Year *
                </label>
                <select
                  value={newYearId}
                  onChange={(e) => setNewYearId(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">Select Academic Year</option>
                  {academicYears.map((ay) => (
                    <option key={ay.id} value={ay.id}>
                      {ay.name} {ay.is_current ? "(Current Period)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* Semester & Section Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Semester *
                  </label>
                  <select
                    value={newSemId}
                    onChange={(e) => setNewSemId(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Select Semester</option>
                    {semesters.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} (Term {s.semester_number})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Class Section *
                  </label>
                  <select
                    value={newSectionId}
                    onChange={(e) => setNewSectionId(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Select Section</option>
                    {sections.map((sec) => (
                      <option key={sec.id} value={sec.id}>
                        Section {sec.name} (Capacity: {sec.capacity})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Max Capacity */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Maximum Enrollment Capacity
                </label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={newCapacity}
                  onChange={(e) => setNewCapacity(Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Default section cohort size. Can be raised if combining cross-department electives.
                </p>
              </div>

              <div className="pt-4 border-t border-slate-200 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {creating ? "Creating Offering..." : "Initialize Course Offering"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DETAIL DRAWER / MODAL */}
      {selectedOfferingId && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-3xl bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 overflow-hidden">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 bg-slate-50 flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-xs font-semibold text-blue-800 bg-blue-100 px-2 py-0.5 rounded border border-blue-200">
                    {offeringDetail?.subject_code || "COURSE"}
                  </span>
                  {offeringDetail && getStatusBadge(offeringDetail.status)}
                </div>
                <h2 className="text-xl font-bold text-slate-900">
                  {offeringDetail?.subject_name || "Course Offering Details"}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Section: {offeringDetail?.section_name} • {offeringDetail?.academic_year_name} (
                  {offeringDetail?.semester_name})
                </p>
              </div>

              <button
                onClick={closeDetailDrawer}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {detailLoading ? (
              <div className="p-12 text-center text-slate-500 my-auto">
                <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
                <p className="text-sm">Loading details and rosters...</p>
              </div>
            ) : offeringDetail ? (
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Offering Overview Card */}
                <div className="grid grid-cols-3 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <div>
                    <span className="text-slate-500 block">Catalog Subject</span>
                    <span className="font-semibold text-slate-800 text-sm">
                      {offeringDetail.subject_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Enrolled Capacity</span>
                    <span className="font-semibold text-slate-800 text-sm">
                      {offeringDetail.enrolled_count} / {offeringDetail.max_capacity}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Primary Instructor</span>
                    <span className="font-semibold text-slate-800 text-sm">
                      {offeringDetail.primary_faculty_name || "None Assigned"}
                    </span>
                  </div>
                </div>

                {/* Lifecycle State Controls */}
                {canManageCourses && (
                  <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100 flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                      <span className="text-xs font-semibold text-blue-900 block">
                        Academic Delivery Lifecycle
                      </span>
                      <span className="text-xs text-blue-700">
                        Current Status: <strong>{offeringDetail.status}</strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {offeringDetail.status === "PLANNED" && (
                        <>
                          <button
                            onClick={() => handleTransitionStatus("OPEN")}
                            disabled={transitioning}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                          >
                            Open for Enrollment
                          </button>
                          <button
                            onClick={() => handleTransitionStatus("CANCELLED")}
                            disabled={transitioning}
                            className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg"
                          >
                            Cancel
                          </button>
                        </>
                      )}

                      {offeringDetail.status === "OPEN" && (
                        <>
                          <button
                            onClick={() => handleTransitionStatus("ACTIVE")}
                            disabled={transitioning}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                          >
                            Activate (Classes Begun)
                          </button>
                          <button
                            onClick={() => handleTransitionStatus("CANCELLED")}
                            disabled={transitioning}
                            className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg"
                          >
                            Cancel
                          </button>
                        </>
                      )}

                      {offeringDetail.status === "ACTIVE" && (
                        <button
                          onClick={() => handleTransitionStatus("COMPLETED")}
                          disabled={transitioning}
                          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                        >
                          Mark Completed (Term Ended)
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Tabs Header */}
                <div className="border-b border-slate-200 flex items-center gap-6">
                  <button
                    onClick={() => setActiveTab("FACULTY")}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                      activeTab === "FACULTY"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Faculty Assignments ({offeringDetail.faculty_assignments?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab("STUDENTS")}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                      activeTab === "STUDENTS"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Student Enrollment Roster ({enrolledStudents.length})
                  </button>
                </div>

                {/* TAB 1: FACULTY ASSIGNMENTS */}
                {activeTab === "FACULTY" && (
                  <div className="space-y-6">
                    {/* Add Faculty Form */}
                    {canManageCourses && (
                      <form
                        onSubmit={handleAssignFaculty}
                        className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3"
                      >
                        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                          Assign Faculty Member
                        </h4>
                        {facultyError && (
                          <div className="p-2 bg-rose-50 border border-rose-200 text-rose-700 rounded text-xs">
                            {facultyError}
                          </div>
                        )}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="md:col-span-2">
                            <select
                              value={assignFacultyId}
                              onChange={(e) => setAssignFacultyId(e.target.value)}
                              required
                              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                              <option value="">Select Instructor...</option>
                              {facultyList.map((f) => (
                                <option key={f.id} value={f.id}>
                                  {f.first_name} {f.last_name} ({f.employee_code} - {f.designation})
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <select
                              value={assignRole}
                              onChange={(e) => setAssignRole(e.target.value)}
                              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                              <option value="PRIMARY">PRIMARY</option>
                              <option value="CO_FACULTY">CO_FACULTY</option>
                              <option value="LAB_INSTRUCTOR">LAB_INSTRUCTOR</option>
                              <option value="TEACHING_ASSISTANT">TEACHING_ASSISTANT</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <button
                            type="submit"
                            disabled={assigningFaculty}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
                          >
                            {assigningFaculty ? "Assigning..." : "Assign to Offering"}
                          </button>
                        </div>
                      </form>
                    )}

                    {/* Faculty Assignments Table */}
                    <div className="border border-slate-200 rounded-xl overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                          <tr>
                            <th className="px-4 py-2.5">Faculty Member</th>
                            <th className="px-4 py-2.5">Instructional Role</th>
                            <th className="px-4 py-2.5">Active From</th>
                            <th className="px-4 py-2.5 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {offeringDetail.faculty_assignments?.length === 0 ? (
                            <tr>
                              <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                                No faculty members currently assigned to this course offering.
                              </td>
                            </tr>
                          ) : (
                            offeringDetail.faculty_assignments.map((fa) => (
                              <tr key={fa.id} className="hover:bg-slate-50/75">
                                <td className="px-4 py-3">
                                  <div className="font-semibold text-slate-800">{fa.faculty_name}</div>
                                  <div className="text-slate-400 font-mono text-[11px]">
                                    {fa.faculty_employee_code}
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <span className="px-2 py-0.5 rounded font-mono font-medium text-[11px] bg-indigo-50 text-indigo-700 border border-indigo-200">
                                    {fa.role}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-slate-600">{fa.start_date}</td>
                                <td className="px-4 py-3 text-right">
                                  {canManageCourses && (
                                    <button
                                      onClick={() => handleUnassignFaculty(fa.faculty_id)}
                                      className="text-rose-600 hover:text-rose-800 font-medium"
                                    >
                                      Remove
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB 2: STUDENT ENROLLMENT ROSTER */}
                {activeTab === "STUDENTS" && (
                  <div className="space-y-6">
                    {/* Batch Enroll Action Card */}
                    {canManageEnrollments && (
                      <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center justify-between gap-4">
                        <div>
                          <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                            Section Batch Enrollment
                          </h4>
                          <p className="text-xs text-emerald-800 mt-0.5">
                            One-click enrollment for all active students registered in Section &ldquo;
                            {offeringDetail.section_name}&rdquo;.
                          </p>
                        </div>
                        <button
                          onClick={handleBatchEnroll}
                          disabled={batchEnrolling}
                          className="px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-lg shadow-sm whitespace-nowrap disabled:opacity-50"
                        >
                          {batchEnrolling ? "Enrolling Section..." : "Batch Enroll Section"}
                        </button>
                      </div>
                    )}

                    {/* Single Student Enroll Form */}
                    {canManageEnrollments && (
                      <form
                        onSubmit={handleEnrollStudent}
                        className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3"
                      >
                        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                          Enroll Individual Student
                        </h4>
                        {enrollError && (
                          <div className="p-2 bg-rose-50 border border-rose-200 text-rose-700 rounded text-xs">
                            {enrollError}
                          </div>
                        )}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="md:col-span-2">
                            <select
                              value={enrollStudentId}
                              onChange={(e) => setEnrollStudentId(e.target.value)}
                              required
                              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                              <option value="">Select Student...</option>
                              {studentList.map((s) => (
                                <option key={s.id} value={s.id}>
                                  {s.first_name} {s.last_name} ({s.roll_number} - {s.admission_number})
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <select
                              value={enrollType}
                              onChange={(e) => setEnrollType(e.target.value)}
                              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                              <option value="REGULAR">REGULAR</option>
                              <option value="ELECTIVE">ELECTIVE</option>
                              <option value="REPEAT">REPEAT</option>
                              <option value="AUDIT">AUDIT</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <button
                            type="submit"
                            disabled={enrolling}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
                          >
                            {enrolling ? "Enrolling..." : "Enroll Student"}
                          </button>
                        </div>
                      </form>
                    )}

                    {/* Enrolled Students Table */}
                    <div className="border border-slate-200 rounded-xl overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                          <tr>
                            <th className="px-4 py-2.5">Student</th>
                            <th className="px-4 py-2.5">Roll / Admission #</th>
                            <th className="px-4 py-2.5">Type</th>
                            <th className="px-4 py-2.5">Status</th>
                            <th className="px-4 py-2.5 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {enrolledStudents.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                                No students currently enrolled in this course offering.
                              </td>
                            </tr>
                          ) : (
                            enrolledStudents.map((enr) => (
                              <tr key={enr.id} className="hover:bg-slate-50/75">
                                <td className="px-4 py-3 font-semibold text-slate-800">
                                  {enr.student_name}
                                </td>
                                <td className="px-4 py-3 font-mono text-slate-600">
                                  {enr.student_roll_number || enr.student_admission_number || "—"}
                                </td>
                                <td className="px-4 py-3">
                                  <span className="px-2 py-0.5 rounded font-mono font-medium text-[11px] bg-slate-100 text-slate-700 border border-slate-200">
                                    {enr.enrollment_type}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  {enr.status === "ENROLLED" ? (
                                    <span className="px-2 py-0.5 rounded font-semibold text-[11px] bg-emerald-100 text-emerald-800 border border-emerald-300">
                                      ENROLLED
                                    </span>
                                  ) : (
                                    <span className="px-2 py-0.5 rounded font-semibold text-[11px] bg-rose-100 text-rose-800 border border-rose-300">
                                      {enr.status}
                                    </span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-right">
                                  {canManageEnrollments && enr.status === "ENROLLED" && (
                                    <button
                                      onClick={() => handleWithdrawStudent(enr.student_id)}
                                      className="text-rose-600 hover:text-rose-800 font-medium"
                                    >
                                      Withdraw
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
