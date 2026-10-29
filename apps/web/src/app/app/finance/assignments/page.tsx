"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  UserCheck,
  Plus,
  Users,
  Search,
  Filter,
  DollarSign,
  ArrowRight,
  Layers,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Gift,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { StudentFeeAssignment, FeeStructure } from "@/types/finance";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export default function FeeAssignmentsPage() {
  const { showToast } = useToast();

  const [assignments, setAssignments] = useState<StudentFeeAssignment[]>([]);
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [programFilter, setProgramFilter] = useState("ALL");

  // Single Assignment Modal
  const [singleModalOpen, setSingleModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState(
    MOCK_STUDENTS[0]?.id || "",
  );
  const [selectedStructureId, setSelectedStructureId] = useState("");
  const [discountAmount, setDiscountAmount] = useState(0);
  const [scholarshipAmount, setScholarshipAmount] = useState(0);
  const [assignNotes, setAssignNotes] = useState("");
  const [assigning, setAssigning] = useState(false);

  // Bulk Assignment Modal
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [bulkStructureId, setBulkStructureId] = useState("");
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [bulkAssigning, setBulkAssigning] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [assignRes, fsRes] = await Promise.all([
        financeService.getFeeAssignments(),
        financeService.getFeeStructures(),
      ]);
      setAssignments(assignRes.data);
      setStructures(fsRes.data);
      if (fsRes.data.length > 0 && !selectedStructureId) {
        setSelectedStructureId(fsRes.data[0].id);
        setBulkStructureId(fsRes.data[0].id);
      }
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Assignments",
        message:
          err instanceof Error
            ? err.message
            : "Unable to retrieve student fee assignments",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSingleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentId || !selectedStructureId) {
      showToast({
        title: "Validation Error",
        message: "Select student and fee structure.",
        type: "error",
      });
      return;
    }

    try {
      setAssigning(true);
      const res = await financeService.createFeeAssignment({
        studentId: selectedStudentId,
        feeStructureId: selectedStructureId,
        discountAmount: Number(discountAmount) || 0,
        scholarshipAmount: Number(scholarshipAmount) || 0,
        notes: assignNotes,
      });

      showToast({
        title: "Fee Assigned",
        message: `Assigned to ${res.data.studentName}. Generated Invoice INV-${res.data.invoiceId?.slice(-4) || "NEW"}.`,
        type: "success",
      });

      setSingleModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Assignment Failed",
        message:
          err instanceof Error ? err.message : "Error creating fee assignment",
        type: "error",
      });
    } finally {
      setAssigning(false);
    }
  };

  const handleBulkAssign = async () => {
    if (!bulkStructureId || selectedStudentIds.length === 0) {
      showToast({
        title: "Validation Error",
        message: "Select fee structure and at least one student.",
        type: "error",
      });
      return;
    }

    try {
      setBulkAssigning(true);
      const res = await financeService.bulkAssignFees({
        feeStructureId: bulkStructureId,
        studentIds: selectedStudentIds,
      });

      showToast({
        title: "Bulk Assignment Complete",
        message: `Successfully generated fee assignments & invoices for ${res.data.assignedCount} students.`,
        type: "success",
      });

      setBulkModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Bulk Assignment Failed",
        message:
          err instanceof Error
            ? err.message
            : "Error processing bulk assignments",
        type: "error",
      });
    } finally {
      setBulkAssigning(false);
    }
  };

  const toggleSelectAllStudents = () => {
    if (selectedStudentIds.length === MOCK_STUDENTS.length) {
      setSelectedStudentIds([]);
    } else {
      setSelectedStudentIds(MOCK_STUDENTS.map((s) => s.id));
    }
  };

  const toggleStudentSelection = (sId: string) => {
    setSelectedStudentIds((prev) =>
      prev.includes(sId) ? prev.filter((id) => id !== sId) : [...prev, sId],
    );
  };

  const filteredAssignments = useMemo(() => {
    return assignments.filter((a) => {
      const matchesSearch =
        a.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.feeStructureName.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === "ALL" || a.status === statusFilter;
      const matchesProgram =
        programFilter === "ALL" || a.program.includes(programFilter);
      return matchesSearch && matchesStatus && matchesProgram;
    });
  }, [assignments, searchQuery, statusFilter, programFilter]);

  const totalGross = assignments.reduce((acc, a) => acc + a.grossAmount, 0);
  const totalOutstanding = assignments.reduce(
    (acc, a) => acc + a.outstandingAmount,
    0,
  );
  const totalScholarships = assignments.reduce(
    (acc, a) => acc + a.scholarshipAmount + a.discountAmount,
    0,
  );

  const columns: ColumnDef<StudentFeeAssignment>[] = [
    {
      id: "student",
      header: "Candidate",
      accessorKey: "studentName",
      sortable: true,
      cell: (row) => (
        <div>
          <p className="font-medium text-slate-200">{row.studentName}</p>
          <p className="font-mono text-xs text-indigo-400">{row.rollNumber}</p>
        </div>
      ),
    },
    {
      id: "structure",
      header: "Fee Structure",
      accessorKey: "feeStructureName",
      sortable: true,
      cell: (row) => (
        <div>
          <p className="text-xs font-medium text-slate-200 line-clamp-1">
            {row.feeStructureName}
          </p>
          <p className="text-[11px] text-slate-400">
            {row.program} • Sem {row.semester} ({row.academicYear})
          </p>
        </div>
      ),
    },
    {
      id: "gross",
      header: "Gross Total",
      accessorKey: "grossAmount",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs text-slate-300">
          {formatMoney(row.grossAmount)}
        </span>
      ),
    },
    {
      id: "concession",
      header: "Scholarship / Waiver",
      cell: (row) => {
        const concession = row.scholarshipAmount + row.discountAmount;
        return (
          <span className="font-mono text-xs text-cyan-400">
            {concession > 0 ? `-${formatMoney(concession)}` : "—"}
          </span>
        );
      },
    },
    {
      id: "netPayable",
      header: "Net Payable",
      accessorKey: "netPayable",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-200">
          {formatMoney(row.netPayable)}
        </span>
      ),
    },
    {
      id: "outstanding",
      header: "Outstanding",
      accessorKey: "outstandingAmount",
      sortable: true,
      cell: (row) => (
        <span
          className={`font-mono text-xs font-semibold ${
            row.outstandingAmount > 0 ? "text-rose-400" : "text-emerald-400"
          }`}
        >
          {formatMoney(row.outstandingAmount)}
        </span>
      ),
    },
    {
      id: "invoice",
      header: "Billing Invoice",
      cell: (row) =>
        row.invoiceId ? (
          <Link
            href={`/app/finance/invoices/${row.invoiceId}`}
            className="inline-flex items-center gap-1 text-xs font-mono font-medium text-indigo-400 hover:text-indigo-300"
          >
            <FileText className="h-3.5 w-3.5" />
            View
          </Link>
        ) : (
          <span className="text-xs text-slate-500">—</span>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
            <Link
              href="/app/finance"
              className="hover:text-slate-200 transition-colors"
            >
              Finance
            </Link>
            <span>/</span>
            <span className="text-slate-200">Fee Assignments</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <UserCheck className="h-6 w-6 text-indigo-400" />
            Student Fee Assignments & Invoicing
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Map students to approved academic fee structures, apply scholarship
            exemptions, and automatically dispatch billing invoices.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setBulkModalOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Users className="h-3.5 w-3.5" />
            Bulk Cohort Assignment
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setSingleModalOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            Assign Student Fee
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Assigned Gross"
          value={formatMoney(totalGross)}
          description="Cumulative billing scheduled"
          icon={<DollarSign className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Scholarships & Waivers"
          value={formatMoney(totalScholarships)}
          description="Institutional financial aid"
          icon={<Gift className="h-5 w-5 text-cyan-400" />}
        />
        <StatCard
          title="Pending Collection"
          value={formatMoney(totalOutstanding)}
          description="Current student accounts due"
          icon={<AlertTriangle className="h-5 w-5 text-rose-400" />}
        />
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search student, roll number, scheme..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs bg-slate-950/60 border-slate-800 text-slate-200"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
            className="h-9 text-xs w-52 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Academic Disciplines</option>
            <option value="Computer Science">
              Computer Science & Engineering
            </option>
            <option value="Electronics">Electronics & Communication</option>
            <option value="AI">AI & Data Science</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 text-xs w-32 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="EXEMPTED">Exempted</option>
            <option value="CANCELLED">Cancelled</option>
          </Select>
        </div>
      </div>

      {/* Assignments DataGrid */}
      <DataGrid
        data={filteredAssignments}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        emptyState={
          <div className="py-12 text-center">
            <UserCheck className="mx-auto h-10 w-10 text-slate-600 mb-2" />
            <p className="text-sm font-semibold text-slate-300">
              No Student Fee Assignments
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Assign students individually or in bulk cohorts to initiate
              billing.
            </p>
          </div>
        }
      />

      {/* Single Assignment Dialog */}
      <Dialog open={singleModalOpen} onOpenChange={setSingleModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-indigo-400" />
              Assign Fee Structure to Student
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSingleAssign} className="space-y-4 py-2">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Select Student <span className="text-rose-400">*</span>
              </label>
              <Select
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                {MOCK_STUDENTS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.firstName} {s.lastName} ({s.rollNumber})
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Approved Fee Structure <span className="text-rose-400">*</span>
              </label>
              <Select
                value={selectedStructureId}
                onChange={(e) => setSelectedStructureId(e.target.value)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                {structures.map((fs) => (
                  <option key={fs.id} value={fs.id}>
                    {fs.name} ({formatMoney(fs.grossTotal)})
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Scholarship Deduction (₹)
                </label>
                <Input
                  type="number"
                  min="0"
                  value={scholarshipAmount.toString()}
                  onChange={(e) =>
                    setScholarshipAmount(parseFloat(e.target.value) || 0)
                  }
                  className="h-8 text-xs font-mono bg-slate-950 border-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Institutional Discount (₹)
                </label>
                <Input
                  type="number"
                  min="0"
                  value={discountAmount.toString()}
                  onChange={(e) =>
                    setDiscountAmount(parseFloat(e.target.value) || 0)
                  }
                  className="h-8 text-xs font-mono bg-slate-950 border-slate-800"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Remarks / Approval Reference
              </label>
              <Textarea
                rows={2}
                value={assignNotes}
                onChange={(e) => setAssignNotes(e.target.value)}
                placeholder="Admission quota, sports waiver or special council reference..."
                className="text-xs bg-slate-950 border-slate-800"
              />
            </div>

            <DialogFooter className="pt-3 border-t border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSingleModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={assigning}
              >
                {assigning ? "Assigning..." : "Assign & Generate Invoice"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Bulk Assignment Modal */}
      <Dialog open={bulkModalOpen} onOpenChange={setBulkModalOpen}>
        <DialogContent className="max-w-xl bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <Users className="h-5 w-5 text-indigo-400" />
              Bulk Cohort Fee Assignment
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Target Fee Structure Scheme
              </label>
              <Select
                value={bulkStructureId}
                onChange={(e) => setBulkStructureId(e.target.value)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                {structures.map((fs) => (
                  <option key={fs.id} value={fs.id}>
                    {fs.name} ({formatMoney(fs.grossTotal)})
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <span className="font-semibold text-slate-300">
                  Select Candidates ({selectedStudentIds.length} of{" "}
                  {MOCK_STUDENTS.length})
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleSelectAllStudents}
                  className="h-6 text-xs text-indigo-400 p-0"
                >
                  {selectedStudentIds.length === MOCK_STUDENTS.length
                    ? "Deselect All"
                    : "Select All"}
                </Button>
              </div>

              <div className="max-h-52 overflow-y-auto space-y-1.5 p-2 rounded-lg bg-slate-950 border border-slate-800">
                {MOCK_STUDENTS.map((student) => {
                  const isChecked = selectedStudentIds.includes(student.id);
                  return (
                    <label
                      key={student.id}
                      className="flex items-center justify-between p-2 rounded hover:bg-slate-900 cursor-pointer"
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleStudentSelection(student.id)}
                          className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                        />
                        <div>
                          <p className="font-medium text-slate-200">
                            {student.firstName} {student.lastName}
                          </p>
                          <p className="text-[11px] font-mono text-slate-400">
                            {student.rollNumber}
                          </p>
                        </div>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {student.program?.department || "Department"}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Selected Cohort Size:</span>
                <span className="font-semibold text-white">
                  {selectedStudentIds.length} students
                </span>
              </div>
              <div className="flex justify-between font-bold text-sm pt-1 border-t border-slate-800">
                <span className="text-white">Estimated Gross Billing:</span>
                <span className="font-mono text-emerald-400">
                  {formatMoney(
                    selectedStudentIds.length *
                      (structures.find((f) => f.id === bulkStructureId)
                        ?.grossTotal || 0),
                  )}
                </span>
              </div>
            </div>
          </div>

          <DialogFooter className="pt-3 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setBulkModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleBulkAssign}
              disabled={bulkAssigning || selectedStudentIds.length === 0}
            >
              {bulkAssigning
                ? "Processing..."
                : `Assign to ${selectedStudentIds.length} Students`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
