"use client";

import React, { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { facultyService } from "@/services/faculty.service";
import { academicsService } from "@/services/academics.service";
import { FacultyDetailView } from "@/types/domain";
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
} from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import {
  Plus,
  UserCheck,
  Building,
  Eye,
  Mail,
  Phone,
  BookOpen,
  Clock,
} from "lucide-react";

export default function FacultyDirectoryPage() {
  const { showToast } = useToast();
  const [facultyList, setFacultyList] = useState<FacultyDetailView[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  // Filters
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("");

  // Create Faculty Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [department, setDepartment] = useState("Computer Science & Engineering");
  const [designation, setDesignation] = useState("Assistant Professor");
  const [qualification, setQualification] = useState("Ph.D. / M.Tech");
  const [specialization, setSpecialization] = useState("");

  const loadData = () => {
    startTransition(async () => {
      setLoading(true);
      const res = await facultyService.list(selectedDept || undefined);
      let items = res.data;
      if (search) {
        const q = search.toLowerCase().trim();
        items = items.filter(
          (f) =>
            f.firstName.toLowerCase().includes(q) ||
            f.lastName.toLowerCase().includes(q) ||
            f.employeeCode.toLowerCase().includes(q) ||
            f.department.toLowerCase().includes(q)
        );
      }
      setFacultyList(items);
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
  }, [search, selectedDept]);

  const handleCreateFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName || !lastName || !employeeCode) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "First name, last name, and employee code are required.",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await facultyService.create({
        firstName,
        lastName,
        employeeCode,
        email: email || `${firstName.toLowerCase()}.${lastName.toLowerCase()}@campusos.edu`,
        department,
        designation,
        qualification,
        specialization,
      });

      showToast({
        type: "success",
        title: "Faculty Appointed",
        message: `Registered ${res.data.firstName} ${res.data.lastName} (${res.data.employeeCode})`,
      });

      setCreateModalOpen(false);
      setFirstName("");
      setLastName("");
      setEmployeeCode("");
      setEmail("");
      setSpecialization("");
      loadData();
    } catch {
      showToast({
        type: "error",
        title: "Registration Failed",
        message: "Unable to register faculty member.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/10 px-2.5 py-0.5 text-xs font-semibold text-sky-400 border border-sky-500/20 mb-2">
            <UserCheck className="h-3 w-3" />
            People Domain • Faculty Registry
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Faculty & Academic Staff Directory
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Teaching staff profiles, departmental appointments, qualification records, and course load.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Faculty Member
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        activeFilterCount={selectedDept ? 1 : 0}
        onReset={() => {
          setSearch("");
          setSelectedDept("");
        }}
      >
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search by name, employee code, specialization..."
          className="max-w-xs"
        />

        <div className="w-56">
          <Select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
          >
            <option value="">All Academic Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.name}>
                {d.code} — {d.name}
              </option>
            ))}
          </Select>
        </div>
      </FilterBar>

      {/* Faculty Table */}
      {loading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : facultyList.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Faculty Member</TableHead>
              <TableHead>Department & Designation</TableHead>
              <TableHead>Specialization</TableHead>
              <TableHead>Teaching Load</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {facultyList.map((f) => (
              <TableRow key={f.id}>
                <TableCell>
                  <Link href={`/app/faculty/${f.id}`} className="group block">
                    <div className="font-semibold text-white group-hover:text-sky-400 transition-colors">
                      {f.firstName} {f.lastName}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {f.employeeCode} • {f.email}
                    </div>
                  </Link>
                </TableCell>
                <TableCell>
                  <div className="text-slate-200">{f.designation}</div>
                  <div className="text-[11px] text-slate-400">{f.department}</div>
                </TableCell>
                <TableCell>
                  <div className="text-slate-300 truncate max-w-xs">{f.specialization}</div>
                  <div className="text-[10px] text-slate-500">{f.qualification}</div>
                </TableCell>
                <TableCell>
                  <span className="font-mono font-bold text-slate-200">
                    {f.teachingLoadHours} Hrs/wk
                  </span>
                  <div className="text-[10px] text-slate-400">
                    {f.assignedSubjects.length} courses assigned
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="success" dot>{f.status}</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Link href={`/app/faculty/${f.id}`}>
                    <Button variant="ghost" size="sm" leftIcon={<Eye className="h-3.5 w-3.5" />}>
                      Profile
                    </Button>
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <EmptyState
          title="No Faculty Found"
          description="No faculty members match your query. Try resetting your search filter."
          actionLabel="Reset Filters"
          onAction={() => {
            setSearch("");
            setSelectedDept("");
          }}
        />
      )}

      {/* Add Faculty Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Appoint New Faculty Member"
        description="Register a new academic staff member in the institutional faculty registry."
        maxWidth="lg"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
              onClick={handleCreateFaculty}
            >
              Confirm Appointment
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateFaculty} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                First Name *
              </label>
              <Input
                placeholder="e.g. Dr. Rajesh"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Last Name *
              </label>
              <Input
                placeholder="e.g. Sharma"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Employee Code *
              </label>
              <Input
                placeholder="e.g. FAC-CSE-009"
                value={employeeCode}
                onChange={(e) => setEmployeeCode(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Official Email
              </label>
              <Input
                type="email"
                placeholder="faculty@campusos.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Department
              </label>
              <Select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              >
                <option value="Computer Science & Engineering">CSE</option>
                <option value="Electronics & Communication">ECE</option>
                <option value="Mechanical Engineering">ME</option>
                <option value="Information Technology">IT</option>
              </Select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                Designation
              </label>
              <Select
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
              >
                <option value="Assistant Professor">Assistant Professor</option>
                <option value="Associate Professor">Associate Professor</option>
                <option value="Professor">Professor</option>
                <option value="Professor & Dean">Professor & Dean</option>
              </Select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Academic Specialization & Research Interests
            </label>
            <Input
              placeholder="e.g. Distributed Operating Systems, Machine Learning, Embedded Systems"
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
            />
          </div>
        </form>
      </Dialog>
    </div>
  );
}
