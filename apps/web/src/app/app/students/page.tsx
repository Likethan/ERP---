"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { studentsService } from "@/services/students.service";
import { academicsService } from "@/services/academics.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import { AdmissionQuota, StudentStatus } from "@/types/people";
import { DepartmentItem } from "@/mocks/academics.mock";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { DataGrid, ColumnDef, BulkAction } from "@/components/data-grid";
import { useDebounce } from "@/lib/use-debounce";
import {
  Users,
  GraduationCap,
  UserCheck,
  Award,
  Eye,
  Plus,
} from "lucide-react";

export default function StudentsDirectoryPage() {
  const { showToast } = useToast();
  const [students, setStudents] = useState<StudentComprehensiveDetail[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedSemester, setSelectedSemester] = useState("ALL");
  const [selectedGender, setSelectedGender] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalRecords, setTotalRecords] = useState(0);

  // Row selection
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // New Student Modal state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newRollNumber, setNewRollNumber] = useState("");
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newDepartment, setNewDepartment] = useState("Computer Science & Engineering");
  const [newSemester, setNewSemester] = useState("1");
  const [newGender, setNewGender] = useState("Male");
  const [newQuota, setNewQuota] = useState("MERIT");

  // Bulk Status Modal
  const [bulkStatusModalOpen, setBulkStatusModalOpen] = useState(false);
  const [targetBulkStatus, setTargetBulkStatus] = useState<StudentComprehensiveDetail["status"]>("ACTIVE");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await studentsService.list({
        search: debouncedSearch.trim() || undefined,
        department: selectedDept !== "ALL" ? selectedDept : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        semester: selectedSemester !== "ALL" ? Number(selectedSemester) : undefined,
        gender: selectedGender !== "ALL" ? selectedGender : undefined,
        page: currentPage,
        pageSize,
      });

      if (res.data) {
        setStudents(res.data);
        setTotalRecords(res.pagination?.totalRecords || res.data.length);
      }
    } catch {
      showToast({
        type: "error",
        title: "Query Failed",
        message: "Unable to retrieve student records from master registry.",
      });
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, selectedDept, selectedStatus, selectedSemester, selectedGender, currentPage, pageSize, showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    academicsService.getDepartments().then((res) => {
      if (res.data) setDepartments(res.data);
    });
  }, []);

  // Handle student creation
  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await studentsService.create({
        rollNumber: newRollNumber,
        firstName: newFirstName,
        lastName: newLastName,
        email: newEmail,
        phone: newPhone || "+91 98450 11000",
        gender: newGender,
        currentSemester: Number(newSemester),
        quota: newQuota as AdmissionQuota,
        program: {
          id: "prog-btech",
          code: "BTECH",
          name: `B.Tech in ${newDepartment}`,
          department: newDepartment,
        },
      });

      showToast({
        type: "success",
        title: "Student Admitted",
        message: `${newFirstName} ${newLastName} (${newRollNumber}) enrolled successfully.`,
      });

      setCreateModalOpen(false);
      // Reset form
      setNewRollNumber("");
      setNewFirstName("");
      setNewLastName("");
      setNewEmail("");
      setNewPhone("");
      loadData();
    } catch {
      showToast({
        type: "error",
        title: "Enrollment Failed",
        message: "Failed to persist new student record.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Bulk Status Update handler
  const handleApplyBulkStatus = async () => {
    for (const key of Array.from(selectedKeys)) {
      await studentsService.update(key, { status: targetBulkStatus });
    }
    showToast({
      type: "success",
      title: "Bulk Status Updated",
      message: `Updated status to ${targetBulkStatus} for ${selectedKeys.size} students.`,
    });
    setBulkStatusModalOpen(false);
    setSelectedKeys(new Set());
    loadData();
  };

  // Bulk actions definition
  const bulkActions: BulkAction<StudentComprehensiveDetail>[] = [
    {
      label: "Update Status",
      variant: "secondary",
      onClick: () => setBulkStatusModalOpen(true),
    },
    {
      label: "Notify Selected",
      variant: "outline",
      onClick: (items) => {
        showToast({
          type: "info",
          title: "Communications Queue",
          message: `Dispatched SMS/Email notification trigger to ${items.length} students.`,
        });
      },
    },
  ];

  // Column definitions for Enterprise Data Grid
  const columns: ColumnDef<StudentComprehensiveDetail>[] = useMemo(() => [
    {
      id: "rollNumber",
      header: "Roll Number",
      accessorKey: "rollNumber",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
            {item.rollNumber}
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            {item.registrationNumber}
          </span>
        </div>
      ),
    },
    {
      id: "name",
      header: "Student Identity",
      sortable: true,
      accessorFn: (item) => `${item.firstName} ${item.lastName}`,
      cell: (item) => (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-300 font-bold text-xs shrink-0 border border-indigo-500/20">
            {item.firstName[0]}
            {item.lastName[0]}
          </div>
          <div>
            <Link
              href={`/app/students/${item.id}`}
              className="font-semibold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition"
            >
              {item.firstName} {item.lastName}
            </Link>
            <div className="text-[11px] text-slate-400 flex items-center gap-2">
              <span>{item.email}</span>
              <span>&bull;</span>
              <span>{item.gender}</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "program",
      header: "Academic Program",
      sortable: true,
      accessorFn: (item) => item.program.name,
      cell: (item) => (
        <div>
          <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
            {item.program.code}
          </span>
          <p className="text-[11px] text-slate-400 truncate max-w-[200px]">
            {item.program.department}
          </p>
        </div>
      ),
    },
    {
      id: "progression",
      header: "Sem & Sec",
      sortable: true,
      accessorFn: (item) => item.currentSemester,
      cell: (item) => (
        <div className="flex items-center gap-1.5">
          <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-mono font-medium text-slate-700 dark:text-slate-300">
            Sem {item.currentSemester}
          </span>
          <span className="rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-500">
            {item.section}
          </span>
        </div>
      ),
    },
    {
      id: "academics",
      header: "CGPA / Attnd",
      sortable: true,
      accessorFn: (item) => item.academicStats?.cgpa || 0,
      cell: (item) => (
        <div className="text-xs">
          <div className="flex items-center gap-1.5 font-mono font-semibold text-slate-900 dark:text-white">
            <span>CGPA: {item.academicStats?.cgpa?.toFixed(2) || "N/A"}</span>
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">
            {item.attendanceSummary?.overallPercentage}% Attnd
          </div>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      accessorKey: "status",
      cell: (item) => {
        const variantMap: Record<string, "success" | "warning" | "destructive" | "secondary"> = {
          ACTIVE: "success",
          ADMITTED: "secondary",
          SUSPENDED: "destructive",
          GRADUATED: "secondary",
          ON_LEAVE: "warning",
          WITHDRAWN: "destructive",
        };
        return (
          <Badge variant={variantMap[item.status] || "secondary"} dot>
            {item.status}
          </Badge>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      enableHiding: false,
      cell: (item) => (
        <div className="flex items-center justify-end gap-1.5">
          <Link href={`/app/students/${item.id}`}>
            <Button size="sm" variant="ghost" leftIcon={<Eye className="h-3.5 w-3.5" />}>
              Profile
            </Button>
          </Link>
        </div>
      ),
    },
  ], []);

  // Custom filter slot in the DataGrid toolbar
  const customFilterSlot = (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={selectedDept}
        onChange={(e) => {
          setSelectedDept(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Departments</option>
        {departments.map((dept) => (
          <option key={dept.id} value={dept.name}>
            {dept.name}
          </option>
        ))}
      </select>

      <select
        value={selectedSemester}
        onChange={(e) => {
          setSelectedSemester(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Semesters</option>
        {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
          <option key={s} value={s}>
            Semester {s}
          </option>
        ))}
      </select>

      <select
        value={selectedStatus}
        onChange={(e) => {
          setSelectedStatus(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Statuses</option>
        <option value="ACTIVE">Active</option>
        <option value="ADMITTED">Admitted</option>
        <option value="ON_LEAVE">On Leave</option>
        <option value="SUSPENDED">Suspended</option>
        <option value="GRADUATED">Graduated</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <Users className="h-3 w-3" />
            People Domain &bull; Student Lifecycle Master
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Management & 360 Registry
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Canonical university student directory, admissions lifecycle, and academic identity records.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Admit New Student
          </Button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Students"
          value="1,420"
          description="Registered active students"
          variant="indigo"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="Good Standing"
          value="1,385"
          description="Active enrollment (97.5%)"
          variant="emerald"
          icon={<UserCheck className="h-5 w-5" />}
        />
        <StatCard
          label="Fresh Cohort 2026"
          value="420"
          description="New student admissions"
          variant="purple"
          icon={<GraduationCap className="h-5 w-5" />}
        />
        <StatCard
          label="Graduating Class"
          value="310"
          description="Final year seniors"
          variant="amber"
          icon={<Award className="h-5 w-5" />}
        />
      </div>

      {/* Enterprise Data Grid */}
      <DataGrid
        data={students}
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
        totalRecords={totalRecords}
        onPageChange={setCurrentPage}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setCurrentPage(1);
        }}
        onSearchChange={(q) => {
          setSearch(q);
          setCurrentPage(1);
        }}
        searchPlaceholder="Search student by name, roll number, or email..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-students-master"
        emptyTitle="No Students Found"
        emptyDescription="No student master records matched your query. Try broadening your search or clear filters."
        emptyActionLabel="Clear All Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedDept("ALL");
          setSelectedStatus("ALL");
          setSelectedSemester("ALL");
          setSelectedGender("ALL");
        }}
      />

      {/* New Student Admission Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Direct Student Admission & Onboarding"
      >
        <form onSubmit={handleCreateStudent} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Roll Number *
              </label>
              <Input
                required
                value={newRollNumber}
                onChange={(e) => setNewRollNumber(e.target.value)}
                placeholder="e.g. 24CSE0199"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Admission Quota
              </label>
              <select
                value={newQuota}
                onChange={(e) => setNewQuota(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="MERIT">Merit Quota (State CET)</option>
                <option value="MANAGEMENT">Management Quota</option>
                <option value="SPORTS">Sports Concession</option>
                <option value="GOVERNMENT">Government Sponsored</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                First Name *
              </label>
              <Input
                required
                value={newFirstName}
                onChange={(e) => setNewFirstName(e.target.value)}
                placeholder="Student first name"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Last Name *
              </label>
              <Input
                required
                value={newLastName}
                onChange={(e) => setNewLastName(e.target.value)}
                placeholder="Student surname"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Email Address *
              </label>
              <Input
                type="email"
                required
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="name@student.campusos.edu"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Phone Number
              </label>
              <Input
                value={newPhone}
                onChange={(e) => setNewPhone(e.target.value)}
                placeholder="+91 98450 00000"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Department
              </label>
              <select
                value={newDepartment}
                onChange={(e) => setNewDepartment(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Semester
              </label>
              <select
                value={newSemester}
                onChange={(e) => setNewSemester(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Gender
              </label>
              <select
                value={newGender}
                onChange={(e) => setNewGender(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
            >
              Confirm Admission
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Bulk Status Update Dialog */}
      <Dialog
        open={bulkStatusModalOpen}
        onClose={() => setBulkStatusModalOpen(false)}
        title={`Update Status for ${selectedKeys.size} Selected Students`}
      >
        <div className="space-y-4 pt-2">
          <p className="text-xs text-slate-500">
            Select the new enrollment lifecycle status to apply across all currently checked student records.
          </p>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              New Lifecycle Status
            </label>
            <select
              value={targetBulkStatus}
              onChange={(e) => setTargetBulkStatus(e.target.value as StudentStatus)}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
            >
              <option value="ACTIVE">ACTIVE — In Good Academic Standing</option>
              <option value="ON_LEAVE">ON_LEAVE — Approved Sabbatical / Medical</option>
              <option value="SUSPENDED">SUSPENDED — Administrative / Disciplinary</option>
              <option value="GRADUATED">GRADUATED — Course Credits Completed</option>
            </select>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setBulkStatusModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleApplyBulkStatus}
            >
              Apply Status Update
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
