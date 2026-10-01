"use client";

import React, { useEffect, useState, useTransition } from "react";
import { staffService } from "@/services/faculty.service";
import { StaffDetailView } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/search-input";
import { FilterBar } from "@/components/ui/filter-bar";
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
import { Users, Mail, Phone, Plus } from "lucide-react";

export default function StaffDirectoryPage() {
  const [staffList, setStaffList] = useState<StaffDetailView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isPending, startTransition] = useTransition();

  const loadData = () => {
    startTransition(async () => {
      setLoading(true);
      const res = await staffService.list();
      let items = res.data;
      if (search) {
        const q = search.toLowerCase().trim();
        items = items.filter(
          (s) =>
            s.firstName.toLowerCase().includes(q) ||
            s.lastName.toLowerCase().includes(q) ||
            s.department.toLowerCase().includes(q) ||
            s.role.toLowerCase().includes(q) ||
            s.employeeCode.toLowerCase().includes(q)
        );
      }
      setStaffList(items);
      setLoading(false);
    });
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 150);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20 mb-2">
            <Users className="h-3 w-3" />
            People Domain • Administrative Staff
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Administrative & Operational Staff
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Registry officers, lab administrators, examination staff, and library personnel.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <FilterBar onReset={() => setSearch("")} activeFilterCount={search ? 1 : 0}>
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search by name, role, department..."
          className="max-w-xs"
        />
      </FilterBar>

      {/* Staff Table */}
      {loading ? (
        <TableSkeleton rows={4} cols={4} />
      ) : staffList.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Staff Member</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Role Title</TableHead>
              <TableHead>Joining Date</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {staffList.map((s) => (
              <TableRow key={s.id}>
                <TableCell>
                  <div className="font-semibold text-white">
                    {s.firstName} {s.lastName}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    {s.employeeCode} • {s.email}
                  </div>
                </TableCell>
                <TableCell className="text-slate-300">{s.department}</TableCell>
                <TableCell className="font-medium text-slate-200">{s.role}</TableCell>
                <TableCell className="font-mono text-slate-400 text-xs">{s.joiningDate}</TableCell>
                <TableCell>
                  <Badge variant="success" dot>{s.status}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <EmptyState
          title="No Staff Records Found"
          description="No administrative staff match your search criteria."
          actionLabel="Clear Search"
          onAction={() => setSearch("")}
        />
      )}
    </div>
  );
}
