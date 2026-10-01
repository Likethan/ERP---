"use client";

import React, { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { studentsService } from "@/services/students.service";
import { academicsService } from "@/services/academics.service";
import { StudentComprehensiveDetail } from "@/types/domain";
import { DepartmentItem } from "@/mocks/academics.mock";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/search-input";
import { FilterBar } from "@/components/ui/filter-bar";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TablePagination,
} from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import {
  Plus,
  Users,
  GraduationCap,
  Download,
  Filter,
  Eye,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function StudentsDirectoryPage() {
  const { showToast } = useToast();
  const [students, setStudents] = useState<StudentComprehensiveDetail[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  // Search & Filter state
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedSemester, setSelectedSemester] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  // New Student Modal state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newRollNumber, setNewRollNumber] = useState("");
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newDepartment, setNewDepartment] = useState("Computer Science & Engineering");
  const [newSemester, setNewSemester] = useState("1");
  const [newGender, setNewGender] = useState("Male");

  const loadData = () => {
    startTransition(async () => {
      setLoading(true);
      const res = await studentsService.list({
        search,
        department: selectedDept || undefined,
        status: selectedStatus || undefined,
        semester: selectedSemester ? Number(selectedSemester) : undefined,
        page: currentPage,
        pageSize,
      });
      setStudents(res.data);
      if (res.pagination) {
        setTotalPages(res.pagination.totalPages || 1);
        setTotalRecords(res.pagination.totalRecords || 0);
      }
      setLoading(false);
    });
  };

  useEffect(() => {
    academicsService.getDepartments().then((res) => setDepartments(res.data));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 150);
    return () => clearTimeout(timer);
  }, [search, selectedDept, selectedStatus, selectedSemester, currentPage]);

  const handleResetFilters = () => {
    setSearch("");
    setSelectedDept("");
    setSelectedStatus("");
    setSelectedSemester("");
    setCurrentPage(1);
  };

  const activeFilterCount =
    (selectedDept ? 1 : 0) + (selectedStatus ? 1 : 0) + (selectedSemester ? 1 : 0);

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFirstName || !newLastName || !newRollNumber) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "First name, last name, and roll number are mandatory.",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await studentsService.create({
        rollNumber: newRollNumber,
        firstName: newFirstName,
        lastName: newLastName,
        email: newEmail || `${newFirstName.toLowerCase()}.${newLastName.toLowerCase()}@student.campusos.edu`,
        gender: newGender,
        currentSemester: Number(newSemester),
        program: {
          id: "prog-new",
          code: newDepartment === "Computer Science & Engineering" ? "BTECH-CSE" : "BTECH",
          name: `B.Tech in ${newDepartment}`,
          department: newDepartment,
        },
      });

      showToast({
        type: "success",
        title: "Student Registered",
        message: `Successfully enrolled ${res.data.firstName} ${res.data.lastName} (${res.data.rollNumber})`,
      });

      setCreateModalOpen(false);
      // Reset form fields
      setNewRollNumber("");
      setNewFirstName("");
      setNewLastName("");
      setNewEmail("");
      loadData();
    } catch {
      showToast({
        type: "error",
        title: "Creation Failed",
        message: "An unexpected error occurred while saving student record.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return <Badge variant="success" dot>{status}</Badge>;
      case "ADMITTED":
        return <Badge variant="info" dot>{status}</Badge>;
      case "ON_LEAVE":
        return <Badge variant="warning" dot>{status}</Badge>;
      case "SUSPENDED":
      case "WITHDRAWN":
        return <Badge variant="destructive" dot>{status}</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Title and Create Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <Users className="h-3 w-3" />
            People Domain • Unified Student Registry
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Student Admissions Directory
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Canonical institutional student master files with unified academic, attendance, and finance linkage.
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

      {/* Filter and Search Bar */}
      <FilterBar
        activeFilterCount={activeFilterCount}
        onReset={handleResetFilters}
      >
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Filter by name, roll number, email..."
          className="max-w-xs"
        />

        <div className="w-48">
          <Select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.name}>
                {d.code} — {d.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="w-36">
          <Select
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
          >
            <option value="">All Semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
              <option key={sem} value={sem}>
                Semester {sem}
              </option>
            ))}
          </Select>
        </div>

        <div className="w-36">
          <Select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ADMITTED">Admitted</option>
            <option value="ON_LEAVE">On Leave</option>
            <option value="SUSPENDED">Suspended</option>
          </Select>
        </div>
      </FilterBar>

      {/* Students Data Table */}
      {loading ? (
        <TableSkeleton rows={6} cols={6} />
      ) : students.length > 0 ? (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead>Program & Semester</TableHead>
                <TableHead>Academic CGPA</TableHead>
                <TableHead>Attendance</TableHead>
                <TableHead>Fee Dues</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {students.map((student) => (
                <TableRow key={student.id}>
                  <TableCell>
                    <Link
                      href={`/app/students/${student.rollNumber}`}
                      className="group block"
                    >
                      <div className="font-semibold text-white group-hover:text-indigo-400 transition-colors">
                        {student.firstName} {student.lastName}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {student.rollNumber}
                      </div>
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div className="text-slate-200">{student.program.code}</div>
                    <div className="text-[11px] text-slate-400">
                      Sem {student.currentSemester} (Sec {student.section})
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono font-bold text-slate-100">
                      {student.academicStats.cgpa.toFixed(2)}
                    </span>
                    <span className="text-[11px] text-slate-500 ml-1">
                      (Rank #{student.academicStats.rank})
                    </span>
                  </TableCell>
                  <TableCell>
                    <span
                      className={
                        student.attendanceSummary.overallPercentage >= 75
                          ? "font-mono font-semibold text-emerald-400"
                          : "font-mono font-semibold text-red-400"
                      }
                    >
                      {student.attendanceSummary.overallPercentage}%
                    </span>
                  </TableCell>
                  <TableCell>
                    {student.financeSummary.pendingDue === 0 ? (
                      <span className="text-xs text-emerald-400 font-medium">Cleared</span>
                    ) : (
                      <span className="text-xs text-amber-400 font-mono font-semibold">
                        ₹{student.financeSummary.pendingDue.toLocaleString()} Due
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{getStatusBadge(student.status)}</TableCell>
                  <TableCell className="text-right">
                    <Link href={`/app/students/${student.rollNumber}`}>
                      <Button variant="ghost" size="sm" leftIcon={<Eye className="h-3.5 w-3.5" />}>
                        Profile
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalRecords={totalRecords}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
          />
        </div>
      ) : (
        <EmptyState
          title="No Students Found"
          description="No student profiles match your current search filters. Try adjusting your query or reset the filter bar."
          actionLabel="Clear Filters"
          onAction={handleResetFilters}
        />
      )}

      {/* Admit New Student Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Admit New Student to Institution"
        description="Formal enrollment registration in CampusOS People Registry."
        maxWidth="lg"
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
              onClick={handleCreateStudent}
            >
              Confirm Admission
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateStudent} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                First Name *
              </label>
              <Input
                placeholder="e.g. Rahul"
                value={newFirstName}
                onChange={(e) => setNewFirstName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Last Name *
              </label>
              <Input
                placeholder="e.g. Verma"
                value={newLastName}
                onChange={(e) => setNewLastName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Roll Number *
              </label>
              <Input
                placeholder="e.g. 24CSE0120"
                value={newRollNumber}
                onChange={(e) => setNewRollNumber(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Institutional Email
              </label>
              <Input
                type="email"
                placeholder="rahul.verma@student.campusos.edu"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Department
              </label>
              <Select
                value={newDepartment}
                onChange={(e) => setNewDepartment(e.target.value)}
              >
                <option value="Computer Science & Engineering">CSE</option>
                <option value="Electronics & Communication">ECE</option>
                <option value="Mechanical Engineering">ME</option>
                <option value="Information Technology">IT</option>
              </Select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Semester
              </label>
              <Select
                value={newSemester}
                onChange={(e) => setNewSemester(e.target.value)}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Gender
              </label>
              <Select
                value={newGender}
                onChange={(e) => setNewGender(e.target.value)}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </Select>
            </div>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
