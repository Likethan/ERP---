"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { facultyService } from "@/services/faculty.service";
import { academicsService } from "@/services/academics.service";
import { FacultyDetailView } from "@/types/domain";
import { DepartmentItem } from "@/mocks/academics.mock";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { DataGrid, ColumnDef } from "@/components/data-grid";
import { GraduationCap, Award, BookOpen, Clock, Eye, Plus } from "lucide-react";

export default function FacultyDirectoryPage() {
  const { showToast } = useToast();
  const [facultyList, setFacultyList] = useState<FacultyDetailView[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters & Pagination
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedDesignation, setSelectedDesignation] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalRecords, setTotalRecords] = useState(0);

  // Create Faculty Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [department, setDepartment] = useState(
    "Computer Science & Engineering",
  );
  const [designation, setDesignation] = useState("Assistant Professor");
  const [qualification, setQualification] = useState("Ph.D. / M.Tech");
  const [specialization, setSpecialization] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await facultyService.list({
        search,
        department: selectedDept !== "ALL" ? selectedDept : undefined,
        designation:
          selectedDesignation !== "ALL" ? selectedDesignation : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        page: currentPage,
        pageSize,
      });
      if (res.data) {
        setFacultyList(res.data);
        setTotalRecords(res.pagination?.totalRecords || res.data.length);
      }
    } catch {
      showToast({
        type: "error",
        title: "Load Failed",
        message: "Failed to query faculty records from master registry.",
      });
    } finally {
      setLoading(false);
    }
  }, [
    search,
    selectedDept,
    selectedDesignation,
    selectedStatus,
    currentPage,
    pageSize,
    showToast,
  ]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    academicsService.getDepartments().then((res) => {
      if (res.data) setDepartments(res.data);
    });
  }, []);

  const handleCreateFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await facultyService.create({
        firstName,
        lastName,
        email,
        phone: phone || "+91 94480 12000",
        employeeCode: employeeCode || `FAC-CSE-0${facultyList.length + 10}`,
        department,
        designation,
        qualification,
        specialization: specialization || "Computer Science Disciplines",
      });

      showToast({
        type: "success",
        title: "Faculty Appointed",
        message: `Dr./Prof. ${firstName} ${lastName} inducted into ${department}.`,
      });

      setCreateModalOpen(false);
      setFirstName("");
      setLastName("");
      setEmail("");
      setPhone("");
      setEmployeeCode("");
      setSpecialization("");
      loadData();
    } catch {
      showToast({
        type: "error",
        title: "Creation Failed",
        message: "Unable to record faculty appointment.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // DataGrid Column Definitions
  const columns: ColumnDef<FacultyDetailView>[] = useMemo(
    () => [
      {
        id: "employeeCode",
        header: "Employee Code",
        accessorKey: "employeeCode",
        sortable: true,
        cell: (item) => (
          <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
            {item.employeeCode}
          </span>
        ),
      },
      {
        id: "name",
        header: "Faculty Identity",
        sortable: true,
        accessorFn: (item) => `${item.firstName} ${item.lastName}`,
        cell: (item) => (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-500/10 text-purple-600 dark:bg-purple-950/60 dark:text-purple-300 font-bold text-xs shrink-0 border border-purple-500/20">
              {item.firstName[0]}
              {item.lastName[0]}
            </div>
            <div>
              <Link
                href={`/app/faculty/${item.id}`}
                className="font-semibold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition"
              >
                {item.firstName} {item.lastName}
              </Link>
              <div className="text-[11px] text-slate-400 flex items-center gap-2">
                <span>{item.email}</span>
                <span>&bull;</span>
                <span>{item.phone}</span>
              </div>
            </div>
          </div>
        ),
      },
      {
        id: "department",
        header: "Department",
        sortable: true,
        accessorKey: "department",
        cell: (item) => (
          <div>
            <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
              {item.department}
            </span>
            <p className="text-[11px] text-slate-400">{item.designation}</p>
          </div>
        ),
      },
      {
        id: "qualification",
        header: "Credentials",
        sortable: true,
        accessorKey: "qualification",
        cell: (item) => (
          <div>
            <span className="text-xs text-slate-800 dark:text-slate-200 font-medium">
              {item.qualification}
            </span>
            <p className="text-[11px] text-slate-400 truncate max-w-[180px]">
              {item.specialization}
            </p>
          </div>
        ),
      },
      {
        id: "workload",
        header: "Weekly Load",
        sortable: true,
        accessorFn: (item) => item.teachingLoadHours,
        cell: (item) => (
          <div className="flex items-center gap-2 text-xs">
            <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <span className="font-mono font-semibold text-slate-900 dark:text-white">
              {item.teachingLoadHours} hrs/wk
            </span>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        sortable: true,
        accessorKey: "status",
        cell: (item) => {
          const variantMap: Record<
            string,
            "success" | "warning" | "destructive" | "secondary"
          > = {
            ACTIVE: "success",
            ON_LEAVE: "warning",
            SABBATICAL: "secondary",
            RESIGNED: "destructive",
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
            <Link href={`/app/faculty/${item.id}`}>
              <Button
                size="sm"
                variant="ghost"
                leftIcon={<Eye className="h-3.5 w-3.5" />}
              >
                Profile
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    [],
  );

  // Custom filter slot in DataGrid
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
        value={selectedDesignation}
        onChange={(e) => {
          setSelectedDesignation(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Designations</option>
        <option value="Professor">Professors & Deans</option>
        <option value="Associate Professor">Associate Professors</option>
        <option value="Assistant Professor">Assistant Professors</option>
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
        <option value="ON_LEAVE">On Leave</option>
        <option value="SABBATICAL">Sabbatical</option>
        <option value="RESIGNED">Resigned</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-purple-500/10 px-2.5 py-0.5 text-xs font-semibold text-purple-400 border border-purple-500/20 mb-2">
            <GraduationCap className="h-3 w-3" />
            People Domain &bull; Academic Faculty Roster
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Faculty Directory & Professorial Roster
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Professorial appointments, designations, academic teaching workload,
            and laboratory supervisors.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Appoint Faculty
          </Button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Faculty"
          value="84"
          description="Professors & Instructors"
          variant="purple"
          icon={<GraduationCap className="h-5 w-5" />}
        />
        <StatCard
          label="Ph.D. Holders"
          value="56"
          description="66.7% Doctoral Credentialed"
          variant="indigo"
          icon={<Award className="h-5 w-5" />}
        />
        <StatCard
          label="Teaching Labs"
          value="18"
          description="Supervised laboratory nodes"
          variant="emerald"
          icon={<BookOpen className="h-5 w-5" />}
        />
        <StatCard
          label="Avg Workload"
          value="14.2 hrs"
          description="Standard weekly lecture hours"
          variant="amber"
          icon={<Clock className="h-5 w-5" />}
        />
      </div>

      {/* Enterprise Data Grid */}
      <DataGrid
        data={facultyList}
        columns={columns}
        keyExtractor={(item) => item.id}
        loading={loading}
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
        searchPlaceholder="Search faculty by name, employee code, or specialization..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-faculty-roster"
        emptyTitle="No Faculty Found"
        emptyDescription="No faculty records matched your query. Try broadening your filter criteria."
        emptyActionLabel="Clear Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedDept("ALL");
          setSelectedDesignation("ALL");
          setSelectedStatus("ALL");
        }}
      />

      {/* Appoint Faculty Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Appoint New Faculty Member"
      >
        <form onSubmit={handleCreateFaculty} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Employee Code
              </label>
              <Input
                value={employeeCode}
                onChange={(e) => setEmployeeCode(e.target.value)}
                placeholder="e.g. FAC-CSE-012"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Department *
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.name}>
                    {d.name}
                  </option>
                ))}
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
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="e.g. Dr. Rajesh"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Last Name *
              </label>
              <Input
                required
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="e.g. Sharma"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Institutional Email *
              </label>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@campusos.edu"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Phone Number
              </label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 94480 00000"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Designation
              </label>
              <select
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="Professor">Professor & Chair</option>
                <option value="Associate Professor">Associate Professor</option>
                <option value="Assistant Professor">Assistant Professor</option>
                <option value="Adjunct Professor">
                  Adjunct / Visiting Professor
                </option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Highest Qualification
              </label>
              <Input
                value={qualification}
                onChange={(e) => setQualification(e.target.value)}
                placeholder="e.g. Ph.D. (Distributed Systems, IISc)"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Research Specialization
            </label>
            <Input
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
              placeholder="e.g. Operating Systems, High Performance Computing"
            />
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
              Confirm Appointment
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
