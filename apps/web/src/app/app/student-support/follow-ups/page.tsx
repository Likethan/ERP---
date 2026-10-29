"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import { SupportFollowUpItem } from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  Search,
  Filter,
  CheckSquare,
  Square,
  UserCheck,
} from "lucide-react";

export default function FollowUpManagementPage() {
  const [followUps, setFollowUps] = useState<SupportFollowUpItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<"LOW" | "MEDIUM" | "HIGH" | "URGENT">("MEDIUM");
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadFollowUps();
  }, []);

  async function loadFollowUps() {
    setLoading(true);
    try {
      const data = await StudentSupportService.getFollowUps();
      setFollowUps(data);
    } catch (err) {
      console.error("Failed to load follow ups:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleComplete(item: SupportFollowUpItem) {
    const isCompleted = item.status === "COMPLETED";
    const nextStatus = isCompleted ? "PENDING" : "COMPLETED";
    try {
      await StudentSupportService.updateFollowUp(item.id, {
        status: nextStatus,
        completed_at: nextStatus === "COMPLETED" ? new Date().toISOString() : undefined,
      });
      loadFollowUps();
    } catch (err) {
      console.error("Failed to toggle follow up:", err);
      alert("Unable to update follow-up task.");
    }
  }

  async function handleCreateFollowUp(e: React.FormEvent) {
    e.preventDefault();
    if (!title || !dueDate) return;
    setSubmitting(true);
    try {
      await StudentSupportService.createFollowUp({
        title,
        priority,
        due_date: new Date(dueDate).toISOString(),
        assigned_to_user_id: "staff-lead",
        notes,
      });

      setNotification("Follow-up task created and scheduled.");
      setCreateModalOpen(false);
      setTitle("");
      setDueDate("");
      setNotes("");
      loadFollowUps();
    } catch (err) {
      console.error("Failed to create follow-up:", err);
      alert("Error creating follow-up task.");
    } finally {
      setSubmitting(false);
    }
  }

  const now = new Date();

  const filteredFollowUps = followUps.filter((item) => {
    const matchesPriority = priorityFilter === "ALL" || item.priority === priorityFilter;
    const matchesStatus = statusFilter === "ALL" || item.status === statusFilter;
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.assigned_to_name && item.assigned_to_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesPriority && matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Follow-Ups", href: "/app/student-support/follow-ups" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Clock className="h-6 w-6 text-orange-400" />
              Support Action Items & Follow-Up Tasks
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Ensure accountability across faculty mentoring commitments, referral deadlines, and student milestones.
            </p>
          </div>
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
          >
            <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
            Add Follow-Up Task
          </Button>
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

      {/* Filter and Search Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search tasks or assigned staff..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950 border-slate-800 text-xs"
            />
          </div>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Priorities</option>
            <option value="URGENT">Urgent</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
      </Card>

      {/* Follow-up Tasks List */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading follow-up tasks...</div>
      ) : filteredFollowUps.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No follow-up items found matching criteria.
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredFollowUps.map((item) => {
            const isOverdue = item.status === "PENDING" && new Date(item.due_date || item.dueDate || "") < now;
            return (
              <Card
                key={item.id}
                className={`p-4 border transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  isOverdue
                    ? "border-red-900/50 bg-red-950/10"
                    : "border-slate-800 bg-slate-900/60"
                }`}
              >
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => handleToggleComplete(item)}
                    className="mt-0.5 text-slate-400 hover:text-white transition"
                  >
                    {item.status === "COMPLETED" ? (
                      <CheckSquare className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <Square className="h-5 w-5 text-slate-500 hover:text-slate-300" />
                    )}
                  </button>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-medium text-sm ${
                          item.status === "COMPLETED" ? "line-through text-slate-500" : "text-white"
                        }`}
                      >
                        {item.title}
                      </span>
                      <Badge
                        variant="outline"
                        className={
                          item.priority === "URGENT" || item.priority === "HIGH"
                            ? "border-rose-500/30 text-rose-400 bg-rose-500/10 text-[10px]"
                            : "border-slate-700 text-slate-400 text-[10px]"
                        }
                      >
                        {item.priority}
                      </Badge>
                      {isOverdue && (
                        <span className="text-[10px] text-red-400 bg-red-950/40 px-1.5 py-0.5 rounded border border-red-800/40 font-semibold">
                          OVERDUE
                        </span>
                      )}
                    </div>

                    {item.notes && <p className="text-xs text-slate-400">{item.notes}</p>}

                    <div className="text-[11px] text-slate-500 flex items-center gap-3 pt-0.5">
                      <span>Assigned to: {item.assigned_to_name ?? item.assignedUserName ?? "Faculty Staff"}</span>
                      <span>•</span>
                      <span>Due: {new Date(item.due_date || item.dueDate || "").toLocaleDateString()}</span>
                      {item.completed_at && (
                        <>
                          <span>•</span>
                          <span className="text-emerald-400">
                            Completed on {new Date(item.completed_at).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleToggleComplete(item)}
                    className="text-xs border-slate-700"
                  >
                    {item.status === "COMPLETED" ? "Reopen" : "Mark Done"}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <PlusCircle className="h-4 w-4 text-indigo-400" />
              Create Support Follow-Up Task
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateFollowUp} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Task Title *</label>
              <Input
                required
                placeholder="e.g. Verify student registered for placement coding mock test"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Priority *</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Due Date *</label>
                <Input
                  required
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Task Notes & Details</label>
              <Textarea
                placeholder="Additional instructions or background..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setCreateModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submitting ? "Saving..." : "Create Task"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
