"use client";

import React, { useState, useEffect } from "react";
import { sportsService } from "@/services/sports.service";
import { SportsDepartmentItem } from "@/types/sports";
import { SportsNav } from "@/components/sports/sports-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { SearchInput } from "@/components/ui/search-input";
import { useToast } from "@/components/ui/toast";
import {
  Building2,
  PlusCircle,
  Clock,
  UserCheck,
  DoorOpen,
  ShieldCheck,
  Edit,
} from "lucide-react";

export default function SportsDepartmentsPage() {
  const { addToast } = useToast();
  const [departments, setDepartments] = useState<SportsDepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [campusFilter, setCampusFilter] = useState("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    campusId: "campus-main",
    description: "",
    headUserName: "",
    weekdayHours: "06:00 - 21:00",
    weekendHours: "06:00 - 18:00",
  });

  useEffect(() => {
    loadDepartments();
  }, [campusFilter]);

  async function loadDepartments() {
    setLoading(true);
    const res = await sportsService.listDepartments(campusFilter);
    if (res.success && res.data) {
      setDepartments(res.data);
    }
    setLoading(false);
  }

  const filtered = departments.filter((d) => {
    const matchesSearch =
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.code.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.name || !formData.code) {
      addToast({ type: "error", title: "Validation Error", message: "Code and Name are required." });
      return;
    }

    const res = await sportsService.createDepartment({
      code: formData.code.toUpperCase(),
      name: formData.name,
      campusId: formData.campusId,
      campusName: formData.campusId === "campus-north" ? "North Campus" : "Main Campus",
      description: formData.description,
      headUserName: formData.headUserName || "Assigned Officer",
      operatingHours: {
        weekday: formData.weekdayHours,
        weekend: formData.weekendHours,
      },
    });

    if (res.success) {
      addToast({ type: "success", title: "Created", message: `Sports department "${formData.name}" created successfully.` });
      setIsCreateOpen(false);
      setFormData({
        code: "",
        name: "",
        campusId: "campus-main",
        description: "",
        headUserName: "",
        weekdayHours: "06:00 - 21:00",
        weekendHours: "06:00 - 18:00",
      });
      loadDepartments();
    } else {
      addToast({ type: "error", title: "Error", message: res.error as string || "Failed to create department." });
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Sports & Athletics", href: "/app/sports" },
          { label: "Departments", href: "/app/sports/departments" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Sports Department Administration
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Governing recreation centers, athletic divisions, operating hours, and multi-campus facilities.
          </p>
        </div>

        <Button
          size="sm"
          className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500"
          onClick={() => setIsCreateOpen(true)}
        >
          <PlusCircle className="h-3.5 w-3.5" />
          Add Department
        </Button>
      </div>

      <SportsNav />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <SearchInput
            placeholder="Search by code or department..."
            value={search}
            onChange={(val) => setSearch(val)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={campusFilter}
            onChange={(e) => setCampusFilter(e.target.value)}
            options={[
              { value: "ALL", label: "All Campuses" },
              { value: "campus-main", label: "Main Campus" },
              { value: "campus-north", label: "North Campus" },
            ]}
          />
        </div>
      </div>

      {/* Departments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((dept) => (
          <Card key={dept.id} className="p-5 border-slate-800 bg-slate-900/40 hover:border-slate-700 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                  {dept.code}
                </span>
                <Badge variant={dept.status === "ACTIVE" ? "success" : "default"}>
                  {dept.status}
                </Badge>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5">{dept.name}</h3>
              <p className="text-xs text-slate-400 mb-4 line-clamp-2">
                {dept.description || "No description provided."}
              </p>

              <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800/80 pt-3">
                <div className="flex items-center gap-2">
                  <UserCheck className="h-3.5 w-3.5 text-slate-500" />
                  <span className="text-slate-400">Head:</span>
                  <span className="font-medium text-white truncate">{dept.headUserName || "Unassigned"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5 text-slate-500" />
                  <span className="text-slate-400">Hours:</span>
                  <span>{dept.operatingHours?.weekday || "06:00 - 21:00"}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mt-5 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <DoorOpen className="h-3.5 w-3.5 text-purple-400" />
                  {dept.facilitiesCount ?? 0} Facilities
                </span>
                <span className="flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
                  {dept.teamsCount ?? 0} Teams
                </span>
              </div>
              <span className="text-slate-500 font-mono">{dept.campusName || "Main Campus"}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Create Department Modal Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Building2 className="h-5 w-5 text-indigo-400" />
              Register Sports Department
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreate} className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="code" className="text-xs">Department Code *</Label>
                <Input
                  id="code"
                  placeholder="e.g. DEPT-ATH-02"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="font-mono uppercase text-xs mt-1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="campus" className="text-xs">Campus *</Label>
                <Select
                  id="campus"
                  value={formData.campusId}
                  onChange={(e) => setFormData({ ...formData, campusId: e.target.value })}
                  options={[
                    { value: "campus-main", label: "Main Campus" },
                    { value: "campus-north", label: "North Campus" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="name" className="text-xs">Department Name *</Label>
              <Input
                id="name"
                placeholder="e.g. Directorate of Physical Education"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="text-xs mt-1"
                required
              />
            </div>

            <div>
              <Label htmlFor="headUserName" className="text-xs">Director / Head Coach</Label>
              <Input
                id="headUserName"
                placeholder="e.g. Dr. Arvind Swaminathan"
                value={formData.headUserName}
                onChange={(e) => setFormData({ ...formData, headUserName: e.target.value })}
                className="text-xs mt-1"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="weekdayHours" className="text-xs">Weekday Operating Hours</Label>
                <Input
                  id="weekdayHours"
                  value={formData.weekdayHours}
                  onChange={(e) => setFormData({ ...formData, weekdayHours: e.target.value })}
                  className="text-xs mt-1 font-mono"
                />
              </div>
              <div>
                <Label htmlFor="weekendHours" className="text-xs">Weekend Operating Hours</Label>
                <Input
                  id="weekendHours"
                  value={formData.weekendHours}
                  onChange={(e) => setFormData({ ...formData, weekendHours: e.target.value })}
                  className="text-xs mt-1 font-mono"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="desc" className="text-xs">Description & Scope</Label>
              <Textarea
                id="desc"
                placeholder="Operational purpose, policies, and facilities under management..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="text-xs mt-1"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-500">
                Register Department
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
