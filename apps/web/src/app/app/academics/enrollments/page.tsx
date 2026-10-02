"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import { studentsService } from "@/services/students.service";
import {
  StudentCourseEnrollmentRecord,
  CourseEnrollmentStatus,
  CourseOfferingDetail,
  AcademicSubject,
} from "@/types/academics";
import { StudentComprehensiveDetail } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef, BulkAction } from "@/components/data-grid";
import {
  UserCheck,
  Plus,
  Users,
  CheckCircle2,
  Trash2,
  BookOpen,
  Layers,
  GraduationCap,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  Filter,
} from "lucide-react";

export default function StudentCourseEnrollmentsPage() {
  const { showToast } = useToast();
  const { hasPermission } = useAuth();

  const [enrollments, setEnrollments] = useState<StudentCourseEnrollmentRecord[]>([]);
  const [offerings, setOfferings] = useState<CourseOfferingDetail[]>([]);
  const [students, setStudents] = useState<StudentComprehensiveDetail[]>([]);
  const [loading, setLoading] = useState(true);

  // Tabs: Master Registrations vs Elective Selection
  const [activeTab, setActiveTab] = useState<"registrations" | "electives">("registrations");

  // Filter states
  const [search, setSearch] = useState("");
  const [selectedSemester, setSelectedSemester] = useState("ALL");
  const [selectedSection, setSelectedSection] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedOfferingId, setSelectedOfferingId] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // Bulk Enrollment Modal
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [bulkSemester, setBulkSemester] = useState<number>(5);
  const [bulkSection, setBulkSection] = useState("A");
  const [bulkOfferingId, setBulkOfferingId] = useState("");
  const [selectedBulkStudentIds, setSelectedBulkStudentIds] = useState<string[]>([]);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);

  // Elective Selection Wizard
  const [selectedStudentForElective, setSelectedStudentForElective] = useState("");
  const [chosenElectiveCode, setChosenElectiveCode] = useState("PE-CS-01");
  const [isSubmittingElective, setIsSubmittingElective] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [enrRes, offRes, studRes] = await Promise.all([
        academicsService.getStudentCourseEnrollments(),
        academicsService.getCourseOfferingDetails(),
        studentsService.list(),
      ]);
      setEnrollments(enrRes.data);
      setOfferings(offRes.data);
      setStudents(studRes.data);
      if (offRes.data.length > 0 && !bulkOfferingId) {
        setBulkOfferingId(offRes.data[0].id);
      }
      if (studRes.data.length > 0 && !selectedStudentForElective) {
        setSelectedStudentForElective(studRes.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load course enrollments:", err);
      showToast({ title: "Failed to load course enrollments", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast, bulkOfferingId, selectedStudentForElective]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Cohort students filtered for bulk selection
  const cohortStudents = useMemo(() => {
    return students.filter(
      (s) => s.currentSemester === Number(bulkSemester) && s.section === bulkSection
    );
  }, [students, bulkSemester, bulkSection]);

  // Filtering enrollments
  const filteredEnrollments = useMemo(() => {
    return enrollments.filter((e) => {
      if (selectedSemester !== "ALL" && e.semester !== Number(selectedSemester)) {
        return false;
      }
      if (selectedSection !== "ALL" && e.section !== selectedSection) {
        return false;
      }
      if (selectedStatus !== "ALL" && e.status !== selectedStatus) {
        return false;
      }
      if (selectedOfferingId !== "ALL" && e.courseOfferingId !== selectedOfferingId) {
        return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return (
          e.studentName.toLowerCase().includes(q) ||
          e.rollNumber.toLowerCase().includes(q) ||
          e.subjectCode.toLowerCase().includes(q) ||
          e.subjectName.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [enrollments, selectedSemester, selectedSection, selectedStatus, selectedOfferingId, search]);

  const paginatedEnrollments = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEnrollments.slice(start, start + pageSize);
  }, [filteredEnrollments, currentPage, pageSize]);

  // Bulk Enrollment Execution
  const handleExecuteBulkEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkOfferingId || selectedBulkStudentIds.length === 0) return;

    try {
      setIsBulkSubmitting(true);
      const res = await academicsService.bulkEnrollStudents({
        courseOfferingId: bulkOfferingId,
        studentIds: selectedBulkStudentIds,
        academicYear: "2026-2027",
        semester: Number(bulkSemester),
        section: bulkSection,
      });

      if (res.success) {
        showToast({
          title: "Bulk Registration Completed",
          message: `Successfully enrolled ${res.data.enrolledCount} students into course offering.`,
          type: "success",
        });
        setBulkModalOpen(false);
        setSelectedBulkStudentIds([]);
        loadData();
      }
    } catch (err: any) {
      showToast({ title: "Bulk enrollment failed", message: err.message, type: "error" });
    } finally {
      setIsBulkSubmitting(false);
    }
  };

  // Drop enrollment
  const handleDropEnrollment = async (enrollmentId: string) => {
    try {
      const res = await academicsService.dropEnrollment(enrollmentId);
      if (res.success) {
        showToast({ title: "Enrollment Marked as Dropped", type: "warning" });
        loadData();
      }
    } catch (err: any) {
      showToast({ title: "Failed to drop enrollment", message: err.message, type: "error" });
    }
  };

  // Submit Elective Selection
  const handleSubmitElective = async () => {
    const stud = students.find((s) => s.id === selectedStudentForElective);
    if (!stud) return;

    const electiveNames: Record<string, string> = {
      "PE-CS-01": "Blockchain Technologies & Consensus",
      "PE-CS-02": "Deep Learning & Neural Architectures",
      "PE-CS-03": "Cloud Native Systems Engineering",
    };

    try {
      setIsSubmittingElective(true);
      const res = await academicsService.enrollStudent({
        studentId: stud.id,
        studentName: `${stud.firstName} ${stud.lastName}`,
        rollNumber: stud.rollNumber,
        program: stud.program.name,
        department: stud.program.department,
        academicYear: "2026-2027",
        semester: stud.currentSemester,
        section: stud.section,
        courseOfferingId: `off-${chosenElectiveCode.toLowerCase()}-a`,
        subjectCode: chosenElectiveCode,
        subjectName: electiveNames[chosenElectiveCode] || "Elective Course",
        credits: 3,
        isElective: true,
        electiveGroup: "Professional Elective I",
      });

      if (res.success) {
        showToast({
          title: "Elective Choice Confirmed",
          message: `${stud.firstName} registered for ${chosenElectiveCode} - ${electiveNames[chosenElectiveCode]}`,
          type: "success",
        });
        loadData();
      }
    } catch (err: any) {
      showToast({ title: "Elective registration failed", message: err.message, type: "error" });
    } finally {
      setIsSubmittingElective(false);
    }
  };

  // Bulk Actions for DataGrid
  const bulkActions: BulkAction<StudentCourseEnrollmentRecord>[] = [
    {
      label: "Mark as Dropped",
      variant: "destructive",
      onClick: async (items) => {
        for (const item of items) {
          await academicsService.updateEnrollmentStatus(item.id, "DROPPED");
        }
        showToast({ title: `Marked ${items.length} enrollments as DROPPED`, type: "warning" });
        setSelectedKeys(new Set());
        loadData();
      },
    },
  ];

  // DataGrid Columns
  const columns: ColumnDef<StudentCourseEnrollmentRecord>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student & Roll No",
        sortable: true,
        accessorKey: "studentName",
        cell: (item) => (
          <div className="space-y-0.5">
            <Link
              href={`/app/students/${item.studentId}`}
              className="font-medium text-white hover:text-indigo-400 transition-colors"
            >
              {item.studentName}
            </Link>
            <div className="font-mono text-xs text-indigo-300 font-semibold">{item.rollNumber}</div>
          </div>
        ),
      },
      {
        id: "course",
        header: "Enrolled Course & Code",
        sortable: true,
        accessorKey: "subjectCode",
        cell: (item) => (
          <div>
            <Link
              href={`/app/academics/course-offerings/${item.courseOfferingId}`}
              className="font-semibold text-slate-200 hover:text-white transition-colors font-mono"
            >
              {item.subjectCode}
            </Link>
            <div className="text-xs text-slate-400 line-clamp-1">{item.subjectName}</div>
            {item.isElective && (
              <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20 mt-0.5">
                {item.electiveGroup || "Elective Basket"}
              </span>
            )}
          </div>
        ),
      },
      {
        id: "cohort",
        header: "Cohort / Section",
        cell: (item) => (
          <div className="text-xs font-mono text-slate-300">
            <span className="rounded bg-slate-800 px-2 py-0.5 border border-slate-700">
              Sem {item.semester} • Sec {item.section}
            </span>
            <div className="text-[10px] text-slate-500 mt-1">AY {item.academicYear}</div>
          </div>
        ),
      },
      {
        id: "credits",
        header: "Credits",
        sortable: true,
        accessorKey: "credits",
        cell: (item) => (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            {item.credits} Cr
          </span>
        ),
      },
      {
        id: "status",
        header: "Status",
        sortable: true,
        accessorKey: "status",
        cell: (item) => {
          const statusMap: Record<CourseEnrollmentStatus, "success" | "warning" | "destructive" | "info" | "secondary"> = {
            ENROLLED: "success",
            PENDING: "warning",
            DROPPED: "destructive",
            COMPLETED: "info",
            WITHDRAWN: "secondary",
          };
          return (
            <Badge variant={statusMap[item.status] || "secondary"} dot>
              {item.status}
            </Badge>
          );
        },
      },
      {
        id: "attendance",
        header: "Attendance",
        sortable: true,
        accessorFn: (item) => item.attendanceRate || 100,
        cell: (item) => (
          <span className="font-mono text-xs font-semibold text-emerald-400">
            {item.attendanceRate || 100}%
          </span>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        align: "right",
        cell: (item) => (
          <div className="flex items-center justify-end gap-1.5">
            {item.status === "ENROLLED" && (
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10"
                onClick={() => handleDropEnrollment(item.id)}
              >
                Drop
              </Button>
            )}
          </div>
        ),
      },
    ],
    []
  );

  // Custom filter slot
  const customFilterSlot = (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={selectedSemester}
        onChange={(e) => {
          setSelectedSemester(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Semesters</option>
        {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
          <option key={s} value={s}>
            Semester {s}
          </option>
        ))}
      </select>

      <select
        value={selectedSection}
        onChange={(e) => {
          setSelectedSection(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Sections</option>
        <option value="A">Section A</option>
        <option value="B">Section B</option>
        <option value="C">Section C</option>
      </select>

      <select
        value={selectedOfferingId}
        onChange={(e) => {
          setSelectedOfferingId(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none max-w-[200px]"
      >
        <option value="ALL">All Courses</option>
        {offerings.map((o) => (
          <option key={o.id} value={o.id}>
            {o.subjectCode} (Sec {o.section})
          </option>
        ))}
      </select>

      <select
        value={selectedStatus}
        onChange={(e) => {
          setSelectedStatus(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Statuses</option>
        <option value="ENROLLED">Enrolled</option>
        <option value="PENDING">Pending</option>
        <option value="DROPPED">Dropped</option>
        <option value="COMPLETED">Completed</option>
        <option value="WITHDRAWN">Withdrawn</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/academics" className="hover:text-white transition-colors">
              Academics
            </Link>
            <span>/</span>
            <span className="text-white">Student Course Enrollments</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Student Course Registrations & Electives
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Course offering enrollment records, section cohort batch onboarding, and choice-based elective selection.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Users className="h-4 w-4" />}
            onClick={() => {
              setBulkModalOpen(true);
            }}
          >
            Bulk Cohort Enrollment
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Enrollments"
          value={enrollments.length}
          description="Subject-student mappings"
          variant="indigo"
          icon={<UserCheck className="h-4 w-4" />}
        />
        <StatCard
          label="Active Registrations"
          value={enrollments.filter((e) => e.status === "ENROLLED").length}
          description="Currently attending lectures"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Elective Enrollments"
          value={enrollments.filter((e) => e.isElective).length}
          description="Professional & Open Electives"
          variant="sky"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Dropped / Withdrawn"
          value={enrollments.filter((e) => e.status === "DROPPED" || e.status === "WITHDRAWN").length}
          description="Roster adjustments"
          variant="amber"
          icon={<AlertTriangle className="h-4 w-4" />}
        />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800 text-xs">
        <button
          onClick={() => setActiveTab("registrations")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "registrations"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <UserCheck className="h-3.5 w-3.5" />
          Master Course Registrations
        </button>
        <button
          onClick={() => setActiveTab("electives")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "electives"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Sparkles className="h-3.5 w-3.5 text-purple-400" />
          Choice-Based Elective Selection
        </button>
      </div>

      {/* Tab 1: Master Registrations DataGrid */}
      {activeTab === "registrations" && (
        <DataGrid<StudentCourseEnrollmentRecord>
          data={paginatedEnrollments}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          selectable
          selectedKeys={selectedKeys}
          onSelectionChange={setSelectedKeys}
          bulkActions={bulkActions}
          paginated
          pageSize={pageSize}
          currentPage={currentPage}
          totalRecords={filteredEnrollments.length}
          onPageChange={setCurrentPage}
          onPageSizeChange={(sz) => {
            setPageSize(sz);
            setCurrentPage(1);
          }}
          onSearchChange={(q) => {
            setSearch(q);
            setCurrentPage(1);
          }}
          searchPlaceholder="Search enrollment by student name, roll number, or subject..."
          customFilterSlot={customFilterSlot}
          exportFileName="campusos-course-enrollments"
          emptyTitle="No Course Enrollments Found"
          emptyDescription="No enrollment records matched your filter criteria."
          emptyActionLabel="Clear Filters"
          onEmptyAction={() => {
            setSearch("");
            setSelectedSemester("ALL");
            setSelectedSection("ALL");
            setSelectedStatus("ALL");
            setSelectedOfferingId("ALL");
          }}
        />
      )}

      {/* Tab 2: Elective Selection Workflow */}
      {activeTab === "electives" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Professional Elective I Selection (Semester 5)</CardTitle>
                <CardDescription>
                  Autonomous CBCS Regulation R-2024 • Choose exactly 1 course from the professional basket.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  {[
                    {
                      code: "PE-CS-01",
                      name: "Blockchain Technologies & Consensus",
                      desc: "Cryptographic hashing, Ethereum smart contracts, distributed consensus mechanisms, and decentralized applications.",
                      credits: 3,
                      capacity: "45 / 60 Enrolled",
                    },
                    {
                      code: "PE-CS-02",
                      name: "Deep Learning & Neural Architectures",
                      desc: "Backpropagation, convolutional networks, transformers, sequence modeling, and PyTorch implementations.",
                      credits: 3,
                      capacity: "58 / 60 Enrolled",
                    },
                    {
                      code: "PE-CS-03",
                      name: "Cloud Native Systems Engineering",
                      desc: "Microservices architecture, Kubernetes orchestration, Docker containers, and cloud infrastructure reliability.",
                      credits: 3,
                      capacity: "32 / 60 Enrolled",
                    },
                  ].map((track) => (
                    <label
                      key={track.code}
                      className={`block p-4 rounded-xl border transition-all cursor-pointer ${
                        chosenElectiveCode === track.code
                          ? "border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500/30"
                          : "border-slate-800 bg-slate-900/60 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <input
                            type="radio"
                            name="electiveTrack"
                            value={track.code}
                            checked={chosenElectiveCode === track.code}
                            onChange={() => setChosenElectiveCode(track.code)}
                            className="text-indigo-600 focus:ring-indigo-500"
                          />
                          <div>
                            <div className="font-semibold text-white flex items-center gap-2">
                              <span className="font-mono text-indigo-400">{track.code}</span>
                              <span>{track.name}</span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                              {track.desc}
                            </p>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="font-mono text-xs font-bold text-white block">
                            {track.credits} Credits
                          </span>
                          <span className="text-[11px] text-slate-500 font-mono">
                            {track.capacity}
                          </span>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Advisor / Student Confirmation</CardTitle>
                <CardDescription>
                  Confirm registration for selected candidate.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Select Student</label>
                  <select
                    value={selectedStudentForElective}
                    onChange={(e) => setSelectedStudentForElective(e.target.value)}
                    className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    {students.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.rollNumber} - {s.firstName} {s.lastName} (Sec {s.section})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 space-y-2 text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Basket:</span>
                    <span className="font-medium text-white">Professional Elective I</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Selected:</span>
                    <span className="font-mono font-bold text-indigo-400">{chosenElectiveCode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Rule check:</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" /> Valid (1/1 Selected)
                    </span>
                  </div>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  onClick={handleSubmitElective}
                  isLoading={isSubmittingElective}
                  leftIcon={<Sparkles className="h-3.5 w-3.5" />}
                >
                  Confirm Elective Selection
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Bulk Cohort Enrollment Dialog */}
      <Dialog
        open={bulkModalOpen}
        onClose={() => setBulkModalOpen(false)}
        title="Bulk Cohort Course Enrollment"
      >
        <form onSubmit={handleExecuteBulkEnrollment} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Semester</label>
              <select
                value={bulkSemester}
                onChange={(e) => setBulkSemester(Number(e.target.value))}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Section</label>
              <select
                value={bulkSection}
                onChange={(e) => setBulkSection(e.target.value)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                <option value="A">Section A</option>
                <option value="B">Section B</option>
                <option value="C">Section C</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Target Course Offering <span className="text-red-400">*</span>
            </label>
            <select
              value={bulkOfferingId}
              onChange={(e) => setBulkOfferingId(e.target.value)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {offerings.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.subjectCode} - {o.subjectName} (Sem {o.semester} Sec {o.section})
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">
                Select Cohort Students ({cohortStudents.length} Available)
              </label>
              <button
                type="button"
                onClick={() => {
                  if (selectedBulkStudentIds.length === cohortStudents.length) {
                    setSelectedBulkStudentIds([]);
                  } else {
                    setSelectedBulkStudentIds(cohortStudents.map((s) => s.id));
                  }
                }}
                className="text-[11px] text-indigo-400 hover:text-indigo-300"
              >
                {selectedBulkStudentIds.length === cohortStudents.length
                  ? "Deselect All"
                  : "Select All Cohort"}
              </button>
            </div>

            <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 p-2 space-y-1">
              {cohortStudents.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500">
                  No students found in Semester {bulkSemester} Section {bulkSection}.
                </div>
              ) : (
                cohortStudents.map((s) => {
                  const checked = selectedBulkStudentIds.includes(s.id);
                  return (
                    <label
                      key={s.id}
                      className="flex items-center gap-2 p-1.5 rounded hover:bg-slate-800 text-xs text-slate-200 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => {
                          if (checked) {
                            setSelectedBulkStudentIds(selectedBulkStudentIds.filter((x) => x !== s.id));
                          } else {
                            setSelectedBulkStudentIds([...selectedBulkStudentIds, s.id]);
                          }
                        }}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="font-mono text-indigo-300 font-semibold">{s.rollNumber}</span>
                      <span>{s.firstName} {s.lastName}</span>
                    </label>
                  );
                })
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setBulkModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isBulkSubmitting}
              disabled={selectedBulkStudentIds.length === 0}
            >
              Enroll Selected ({selectedBulkStudentIds.length})
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
