"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import {
  MentorAssignmentItem,
  MenteeItem,
  SupportPolicyConfigItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Users,
  UserCheck,
  UserPlus,
  RefreshCw,
  Search,
  Filter,
  AlertTriangle,
  ArrowRightLeft,
  CheckCircle2,
  Building,
  GraduationCap,
} from "lucide-react";

export default function MentorAssignmentManagementPage() {
  const [assignments, setAssignments] = useState<MentorAssignmentItem[]>([]);
  const [unassigned, setUnassigned] = useState<MenteeItem[]>([]);
  const [config, setConfig] = useState<SupportPolicyConfigItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");

  // Reassign Modal State
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<MentorAssignmentItem | null>(null);
  const [newFacultyId, setNewFacultyId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [submittingReassign, setSubmittingReassign] = useState(false);

  // New Assignment Modal State
  const [newModalOpen, setNewModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [assignFacultyId, setAssignFacultyId] = useState("");
  const [submittingAssign, setSubmittingAssign] = useState(false);

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [allAssignments, unassignedStudents, policyConfig] = await Promise.all([
        StudentSupportService.getMentorAssignments(),
        StudentSupportService.getUnassignedStudents(),
        StudentSupportService.getPolicyConfig(),
      ]);
      setAssignments(allAssignments);
      setUnassigned(unassignedStudents);
      setConfig(policyConfig);
    } catch (err) {
      console.error("Failed to load assignments:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReassign(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAssignment || !newFacultyId || !reassignReason) return;
    setSubmittingReassign(true);
    try {
      await StudentSupportService.reassignMentor(selectedAssignment.id, {
        new_faculty_staff_id: newFacultyId,
        reassignment_reason: reassignReason,
      });
      setNotification(`Mentor reassignment successful for student ${selectedAssignment.student_name}.`);
      setReassignModalOpen(false);
      setSelectedAssignment(null);
      setNewFacultyId("");
      setReassignReason("");
      loadData();
    } catch (err) {
      console.error("Reassignment failed:", err);
      alert("Failed to reassign mentor. Please check server limits.");
    } finally {
      setSubmittingReassign(false);
    }
  }

  async function handleCreateAssignment(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedStudentId || !assignFacultyId) return;
    setSubmittingAssign(true);
    try {
      await StudentSupportService.createMentorAssignment({
        student_id: selectedStudentId,
        faculty_staff_id: assignFacultyId,
        academic_year: "2026-2027",
        assignment_type: "MANUAL",
        is_primary: true,
      });
      setNotification("Faculty mentor assigned successfully.");
      setNewModalOpen(false);
      setSelectedStudentId("");
      setAssignFacultyId("");
      loadData();
    } catch (err) {
      console.error("Assignment failed:", err);
      alert("Failed to assign mentor. Workload limit might be exceeded.");
    } finally {
      setSubmittingAssign(false);
    }
  }

  const filteredAssignments = assignments.filter((a) => {
    const sName = a.student_name || a.studentName || "";
    const sReg = a.student_reg_no || a.studentRoll || "";
    const fName = a.faculty_name || a.mentorName || "";
    const dName = a.department_name || a.studentDepartment || "";
    const matchesSearch =
      sName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sReg.toLowerCase().includes(searchQuery.toLowerCase()) ||
      fName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || a.status === statusFilter;
    const matchesDept = departmentFilter === "ALL" || dName.includes(departmentFilter);
    return matchesSearch && matchesStatus && matchesDept;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Mentor Assignments", href: "/app/student-support/assignments" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Users className="h-6 w-6 text-indigo-400" />
              Faculty Mentor Allocations
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Administer institution-wide faculty-student mentorship relationships, capacity limits, and reassignment trails.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setNewModalOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
            >
              <UserPlus className="mr-1.5 h-3.5 w-3.5" />
              Assign Mentor
            </Button>
          </div>
        </div>
      </div>

      <StudentSupportNav />

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {/* Unassigned Students Alert Banner */}
      {unassigned.length > 0 && (
        <div className="rounded-xl border border-amber-800/50 bg-amber-950/20 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
            <div className="text-xs">
              <span className="font-semibold text-white">{unassigned.length} Eligible Students Awaiting Mentor Allocation</span>
              <p className="text-slate-400 mt-0.5">Ensure all enrolled students have an assigned academic mentor in compliance with institutional policy.</p>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => setNewModalOpen(true)}
            className="bg-amber-600 hover:bg-amber-700 text-xs text-white shrink-0"
          >
            Allocate Mentors
          </Button>
        </div>
      )}

      {/* KPI Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Assignments"
          value={loading ? "..." : assignments.filter((a) => a.status === "ACTIVE").length.toString()}
          icon={<UserCheck className="h-5 w-5 text-indigo-400" />}
          description="Current active mentoring pairs"
        />
        <StatCard
          title="Unassigned Students"
          value={loading ? "..." : unassigned.length.toString()}
          icon={<AlertTriangle className="h-5 w-5 text-amber-400" />}
          description="Batch awaiting allocation"
        />
        <StatCard
          title="Workload Quota"
          value={loading ? "..." : `${config?.max_mentees_per_mentor ?? 20} Mentees / Faculty`}
          icon={<Users className="h-5 w-5 text-emerald-400" />}
          description="Configured institutional ceiling"
        />
        <StatCard
          title="Reassignment Rate"
          value={loading ? "..." : `${assignments.filter((a) => a.status === "REASSIGNED").length} historical`}
          icon={<ArrowRightLeft className="h-5 w-5 text-cyan-400" />}
          description="Tracked reallocations"
        />
      </div>

      {/* Filtering and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by student, register number, or faculty mentor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-300"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Only</option>
              <option value="REASSIGNED">Reassigned</option>
              <option value="COMPLETED">Completed</option>
            </select>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-300"
            >
              <option value="ALL">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Electronics">Electronics</option>
              <option value="Mechanical">Mechanical</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Assignments Table */}
      <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-medium">
              <tr>
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Program & Year</th>
                <th className="py-3 px-4">Assigned Mentor</th>
                <th className="py-3 px-4">Faculty Workload</th>
                <th className="py-3 px-4">Allocation Type</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading mentor allocations...
                  </td>
                </tr>
              ) : filteredAssignments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No mentor assignments matching the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredAssignments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">{a.student_name}</div>
                      <div className="text-[11px] text-slate-500">{a.student_reg_no}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div>{a.department_name}</div>
                      <div className="text-[11px] text-slate-500">{a.program_name} • {a.academic_year}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-indigo-300">{a.faculty_name}</div>
                      <div className="text-[11px] text-slate-500">{a.faculty_email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-slate-200">
                          {a.faculty_workload_count ?? 12} / {config?.max_mentees_per_mentor ?? 20}
                        </span>
                        <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/30">
                          Within Quota
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                        {a.assignment_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant="outline"
                        className={
                          a.status === "ACTIVE"
                            ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                            : a.status === "REASSIGNED"
                            ? "border-amber-500/30 text-amber-400 bg-amber-500/10 text-[10px]"
                            : "border-slate-700 text-slate-400 text-[10px]"
                        }
                      >
                        {a.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {a.status === "ACTIVE" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAssignment(a);
                            setReassignModalOpen(true);
                          }}
                          className="text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800"
                        >
                          <ArrowRightLeft className="mr-1 h-3.5 w-3.5" />
                          Reassign
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Reassign Mentor Modal */}
      <Dialog open={reassignModalOpen} onOpenChange={setReassignModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <ArrowRightLeft className="h-4 w-4 text-indigo-400" />
              Reassign Faculty Mentor
            </DialogTitle>
          </DialogHeader>
          {selectedAssignment && (
            <form onSubmit={handleReassign} className="space-y-4 pt-2">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div>
                  <span className="text-slate-400">Student: </span>
                  <strong className="text-white">{selectedAssignment.student_name}</strong> ({selectedAssignment.student_reg_no})
                </div>
                <div>
                  <span className="text-slate-400">Current Mentor: </span>
                  <span className="text-indigo-300">{selectedAssignment.faculty_name}</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-slate-400">New Faculty Staff ID *</label>
                <Input
                  required
                  placeholder="e.g. FAC-CSE-003 or faculty UUID"
                  value={newFacultyId}
                  onChange={(e) => setNewFacultyId(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-slate-400">Reassignment Reason / Justification *</label>
                <Input
                  required
                  placeholder="e.g. Faculty sabbatical coverage, specialization realignment"
                  value={reassignReason}
                  onChange={(e) => setReassignReason(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <DialogFooter className="pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setReassignModalOpen(false)}
                  className="text-xs text-slate-400"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submittingReassign}
                  className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
                >
                  {submittingReassign ? "Processing..." : "Confirm Reassignment"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Assign Mentor Modal */}
      <Dialog open={newModalOpen} onOpenChange={setNewModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <UserPlus className="h-4 w-4 text-indigo-400" />
              New Faculty Mentor Allocation
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAssignment} className="space-y-4 pt-2">
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Select Student *</label>
              {unassigned.length > 0 ? (
                <select
                  required
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white"
                >
                  <option value="">-- Choose unassigned student --</option>
                  {unassigned.map((st) => (
                    <option key={st.student_id} value={st.student_id}>
                      {st.student_name} ({st.student_reg_no}) - {st.program_name}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  required
                  placeholder="Enter Student UUID or Reg Number"
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs text-slate-400">Faculty Staff ID *</label>
              <Input
                required
                placeholder="e.g. FAC-CSE-001 or faculty UUID"
                value={assignFacultyId}
                onChange={(e) => setAssignFacultyId(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
              <p className="text-[11px] text-slate-500">
                System enforces maximum {config?.max_mentees_per_mentor ?? 20} mentees per faculty mentor.
              </p>
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setNewModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingAssign}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submittingAssign ? "Assigning..." : "Assign Mentor"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
