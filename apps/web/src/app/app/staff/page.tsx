"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { staffService } from "@/services/staff.service";
import { StaffDetailView } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { DataGrid, ColumnDef } from "@/components/data-grid";
import {
  Users,
  Clock,
  Calendar,
  Eye,
  Plus,
  CheckCircle2,
} from "lucide-react";

export default function StaffDirectoryPage() {
  const { showToast } = useToast();
  const [staffList, setStaffList] = useState<StaffDetailView[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters & Pagination
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedShift, setSelectedShift] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedType, setSelectedType] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalRecords, setTotalRecords] = useState(0);

  // Create Staff Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [department, setDepartment] = useState("Academic Administration");
  const [role, setRole] = useState("Assistant Registrar");
  const [employmentType, setEmploymentType] = useState<"PERMANENT" | "CONTRACT" | "PROBATION">("PERMANENT");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await staffService.list({
        search,
        department: selectedDept !== "ALL" ? selectedDept : undefined,
        shift: selectedShift !== "ALL" ? selectedShift : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        employmentType: selectedType !== "ALL" ? selectedType : undefined,
        page: currentPage,
        pageSize,
      });
      if (res.data) {
        setStaffList(res.data);
        setTotalRecords(res.pagination?.totalRecords || res.data.length);
      }
    } catch {
      showToast({
        type: "error",
        title: "Load Failed",
        message: "Failed to query staff personnel records.",
      });
    } finally {
      setLoading(false);
    }
  }, [search, selectedDept, selectedShift, selectedStatus, selectedType, currentPage, pageSize, showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await staffService.create({
        firstName,
        lastName,
        email,
        phone: phone || "+91 94480 11999",
        employeeCode: employeeCode || `STF-ADM-0${staffList.length + 10}`,
        department,
        role,
        designation: role,
        employmentType,
        joiningDate: new Date().toISOString().split("T")[0],
      });

      showToast({
        type: "success",
        title: "Staff Member Inducted",
        message: `${firstName} ${lastName} enrolled into ${department}.`,
      });

      setCreateModalOpen(false);
      setFirstName("");
      setLastName("");
      setEmail("");
      setPhone("");
      setEmployeeCode("");
      loadData();
    } catch {
      showToast({
        type: "error",
        title: "Induction Failed",
        message: "Could not create staff record.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // DataGrid Columns
  const columns: ColumnDef<StaffDetailView>[] = useMemo(() => [
    {
      id: "employeeCode",
      header: "Staff ID",
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
      header: "Staff Identity",
      sortable: true,
      accessorFn: (item) => `${item.firstName} ${item.lastName}`,
      cell: (item) => (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-500/10 text-slate-700 dark:bg-slate-800 dark:text-slate-300 font-bold text-xs shrink-0 border border-slate-500/20">
            {item.firstName[0]}
            {item.lastName[0]}
          </div>
          <div>
            <Link
              href={`/app/staff/${item.id}`}
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
      header: "Department / Section",
      sortable: true,
      accessorKey: "department",
      cell: (item) => (
        <div>
          <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
            {item.department}
          </span>
          <p className="text-[11px] text-slate-400 truncate max-w-[200px]">
            {item.role || item.designation}
          </p>
        </div>
      ),
    },
    {
      id: "shift",
      header: "Assigned Shift",
      sortable: true,
      accessorFn: (item) => item.shift?.shiftName || "General Shift",
      cell: (item) => (
        <div>
          <span className="rounded bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60">
            {item.shift?.shiftType || "GENERAL"}
          </span>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            {item.shift?.startTime} - {item.shift?.endTime}
          </p>
        </div>
      ),
    },
    {
      id: "employment",
      header: "Employment",
      sortable: true,
      accessorKey: "employmentType",
      cell: (item) => (
        <span className="text-xs text-slate-700 dark:text-slate-300 font-mono">
          {item.employmentType || "PERMANENT"}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      accessorKey: "status",
      cell: (item) => (
        <Badge
          variant={
            item.status === "ACTIVE"
              ? "success"
              : item.status === "ON_LEAVE"
              ? "warning"
              : "destructive"
          }
          dot
        >
          {item.status}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      enableHiding: false,
      cell: (item) => (
        <div className="flex items-center justify-end gap-1.5">
          <Link href={`/app/staff/${item.id}`}>
            <Button size="sm" variant="ghost" leftIcon={<Eye className="h-3.5 w-3.5" />}>
              Profile
            </Button>
          </Link>
        </div>
      ),
    },
  ], []);

  // Filter Slot
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
        <option value="Academic Administration">Academic Administration</option>
        <option value="Accounts & Financial Services">Accounts & Financial Services</option>
        <option value="Information Technology & Networks">IT & Networks</option>
        <option value="Computer Science Laboratories">CS Laboratories</option>
        <option value="Student Hostels & Residential Affairs">Hostels & Residential</option>
        <option value="Transport & Logistics">Transport & Fleet</option>
        <option value="Campus Safety & Security">Campus Security</option>
      </select>

      <select
        value={selectedShift}
        onChange={(e) => {
          setSelectedShift(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Shifts</option>
        <option value="MORNING">Morning (07:30 AM - 03:30 PM)</option>
        <option value="GENERAL">General (09:00 AM - 05:30 PM)</option>
        <option value="EVENING">Evening (01:30 PM - 09:30 PM)</option>
        <option value="NIGHT">Night Vigil (09:30 PM - 06:00 AM)</option>
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
        <option value="ACTIVE">Active Duty</option>
        <option value="ON_LEAVE">On Leave</option>
        <option value="RESIGNED">Resigned</option>
      </select>

      <select
        value={selectedType}
        onChange={(e) => {
          setSelectedType(e.target.value);
          setCurrentPage(1);
        }}
        className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
      >
        <option value="ALL">All Terms</option>
        <option value="PERMANENT">Permanent</option>
        <option value="CONTRACT">Contract</option>
        <option value="PROBATION">Probation</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-slate-500/10 px-2.5 py-0.5 text-xs font-semibold text-slate-500 dark:text-slate-400 border border-slate-500/20 mb-2">
            <Users className="h-3 w-3" />
            People Domain &bull; Administrative & Technical Personnel
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Non-Teaching Staff & Support Operations
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Institutional administrative personnel, laboratory technicians, shift allocations, and departmental rosters.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Induct Staff Member
          </Button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Staff"
          value="48"
          description="Operational personnel"
          variant="indigo"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="On Duty Today"
          value="38"
          description="Active on campus shifts"
          variant="emerald"
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
        <StatCard
          label="Operational Shifts"
          value="4"
          description="Morning, Day, Eve, Night"
          variant="purple"
          icon={<Clock className="h-5 w-5" />}
        />
        <StatCard
          label="Pending Leaves"
          value="3"
          description="Awaiting department review"
          variant="amber"
          icon={<Calendar className="h-5 w-5" />}
        />
      </div>

      {/* Enterprise Data Grid */}
      <DataGrid
        data={staffList}
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
        searchPlaceholder="Search staff by name, staff ID, role, or department..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-staff-roster"
        emptyTitle="No Staff Members Found"
        emptyDescription="No administrative personnel matched your query. Try changing your filters."
        emptyActionLabel="Clear Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedDept("ALL");
          setSelectedShift("ALL");
          setSelectedStatus("ALL");
        }}
      />

      {/* Induct Staff Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Induct Non-Teaching Staff Member"
      >
        <form onSubmit={handleCreateStaff} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Employee Code
              </label>
              <Input
                value={employeeCode}
                onChange={(e) => setEmployeeCode(e.target.value)}
                placeholder="e.g. STF-ADM-010"
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
                <option value="Academic Administration">Academic Administration</option>
                <option value="Accounts & Financial Services">Accounts & Financial Services</option>
                <option value="Information Technology & Networks">IT & Networks</option>
                <option value="Computer Science Laboratories">CS Laboratories</option>
                <option value="Student Hostels & Residential Affairs">Hostels & Residential</option>
                <option value="Transport & Logistics">Transport & Fleet</option>
                <option value="Campus Safety & Security">Campus Security</option>
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
                placeholder="e.g. Rajesh"
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
                Official Email *
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
                Designation / Position
              </label>
              <Input
                required
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Lead Hardware Technician"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Employment Terms
              </label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value as "PERMANENT" | "CONTRACT" | "PROBATION")}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="PERMANENT">PERMANENT (Regular)</option>
                <option value="CONTRACT">CONTRACT (Fixed-Term)</option>
                <option value="PROBATION">PROBATION (Trainee)</option>
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
              Complete Induction
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
