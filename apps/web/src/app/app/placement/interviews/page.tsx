"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Calendar,
  Search,
  Plus,
  Clock,
  Video,
  MapPin,
  Building2,
  Users,
  CheckCircle2,
  XCircle,
  Award,
  ChevronRight,
  Eye,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import {
  Interview,
  InterviewStage,
  InterviewStatus,
  Application,
} from "@/types/placement";

export default function InterviewsSchedulePage() {
  const { showToast } = useToast();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Schedule Modal
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    applicationId: "",
    stage: "TECHNICAL" as InterviewStage,
    roundNumber: 1,
    date: new Date(Date.now() + 3 * 86400000).toISOString().split("T")[0],
    time: "10:30 AM",
    durationMinutes: 60,
    mode: "ONLINE" as "ONLINE" | "IN_PERSON",
    locationOrMeetingUrl: "https://cisco.webex.com/meet/campus-interviews",
    interviewerName: "Dr. Kunal Bhasin",
    interviewerEmail: "kunal.b@cisco.com",
    notes: "Focus on data structures and system architecture.",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [intvRes, appsRes] = await Promise.all([
        placementService.getInterviews(),
        placementService.getApplications(),
      ]);
      setInterviews(intvRes.data);
      const eligibleApps = (appsRes.data || []).filter(
        (a) => a.status === "SHORTLISTED" || a.status === "SUBMITTED",
      );
      setApplications(eligibleApps);
      if (eligibleApps.length > 0) {
        setFormData((prev) => ({ ...prev, applicationId: eligibleApps[0].id }));
      }
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load interviews",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScheduleInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.applicationId) {
      showToast({
        title: "Validation Error",
        message: "Select a shortlisted candidate application",
        type: "error",
      });
      return;
    }

    try {
      await placementService.scheduleInterview({
        applicationId: formData.applicationId,
        stage: formData.stage,
        roundNumber: Number(formData.roundNumber),
        date: formData.date,
        time: formData.time,
        durationMinutes: Number(formData.durationMinutes),
        mode: formData.mode,
        locationOrMeetingUrl: formData.locationOrMeetingUrl,
        interviewerName: formData.interviewerName,
        interviewerEmail: formData.interviewerEmail,
        notes: formData.notes,
      });

      showToast({
        title: "Scheduled",
        message: "Interview scheduled successfully",
        type: "success",
      });
      setShowModal(false);
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to schedule interview",
        type: "error",
      });
    }
  };

  const filteredInterviews = useMemo(() => {
    return interviews.filter((i) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          i.studentName.toLowerCase().includes(q) ||
          i.companyName.toLowerCase().includes(q) ||
          i.interviewerName.toLowerCase().includes(q) ||
          i.interviewCode.toLowerCase().includes(q);
        if (!matches) return false;
      }

      if (stageFilter !== "ALL" && i.stage !== stageFilter) {
        return false;
      }

      if (statusFilter !== "ALL" && i.status !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [interviews, searchQuery, stageFilter, statusFilter]);

  const columns: ColumnDef<Interview>[] = [
    {
      id: "code",
      header: "Interview Code",
      sortable: true,
      cell: (item) => (
        <Link
          href={`/app/placement/interviews/${item.id}`}
          className="font-mono font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
        >
          {item.interviewCode}
        </Link>
      ),
    },
    {
      id: "candidate",
      header: "Candidate",
      sortable: true,
      cell: (item) => (
        <div className="flex flex-col">
          <Link
            href={`/app/placement/students/${item.studentId}`}
            className="font-medium text-slate-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-400"
          >
            {item.studentName}
          </Link>
          <span className="text-xs text-slate-500 font-mono mt-0.5">
            {item.rollNumber}
          </span>
        </div>
      ),
    },
    {
      id: "role",
      header: "Company & Role",
      cell: (item) => (
        <div className="text-xs">
          <span className="font-semibold text-slate-900 dark:text-white">
            {item.companyName}
          </span>
          <p className="text-slate-500 mt-0.5">{item.positionTitle}</p>
        </div>
      ),
    },
    {
      id: "stage",
      header: "Stage & Round",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <Badge variant="outline">
            {item.stage} Round {item.roundNumber}
          </Badge>
        </div>
      ),
    },
    {
      id: "schedule",
      header: "Date & Time",
      sortable: true,
      cell: (item) => (
        <div className="text-xs">
          <div className="flex items-center gap-1.5 font-medium text-slate-900 dark:text-white">
            <Calendar className="w-3.5 h-3.5 text-indigo-500" />
            <span>{item.date}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-500 mt-0.5">
            <Clock className="w-3 h-3" />
            <span>
              {item.time} ({item.durationMinutes}m)
            </span>
          </div>
        </div>
      ),
    },
    {
      id: "interviewer",
      header: "Panelist",
      cell: (item) => (
        <div className="text-xs">
          <span className="font-medium text-slate-900 dark:text-white">
            {item.interviewerName}
          </span>
          <p className="text-[11px] text-slate-500">{item.mode}</p>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (item) => {
        const badgeColors: Record<
          InterviewStatus,
          "success" | "warning" | "destructive" | "secondary"
        > = {
          COMPLETED: "success",
          SCHEDULED: "warning",
          RESCHEDULED: "warning",
          CANCELLED: "destructive",
          NO_SHOW: "destructive",
        };
        return (
          <Badge variant={badgeColors[item.status] || "secondary"} dot>
            {item.status}
          </Badge>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      cell: (item) => (
        <div className="flex items-center justify-end gap-1.5">
          <Link href={`/app/placement/interviews/${item.id}`}>
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
              <Eye className="w-3 h-3" />
              Evaluate
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <Link
              href="/app/placement"
              className="hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Placement Hub
            </Link>
            <span>/</span>
            <span>Interviews</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Interview Rounds & Technical Evaluation Panels
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Schedule candidate rounds, manage panelist interview rooms, track
            screening stages, and record comprehensive performance evaluations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            onClick={() => setShowModal(true)}
            className="gap-2 text-xs"
          >
            <Plus className="w-4 h-4" />
            Schedule Interview
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Scheduled Rounds"
          value={
            interviews.filter(
              (i) => i.status === "SCHEDULED" || i.status === "RESCHEDULED",
            ).length
          }
          icon={<Clock className="w-5 h-5 text-indigo-500" />}
          description="Upcoming interview panels"
        />
        <StatCard
          title="Completed Evaluations"
          value={interviews.filter((i) => i.status === "COMPLETED").length}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
          description="Evaluations recorded"
        />
        <StatCard
          title="Virtual / Online"
          value={interviews.filter((i) => i.mode === "ONLINE").length}
          icon={<Video className="w-5 h-5 text-purple-500" />}
          description="Webex / Meet sessions"
        />
        <StatCard
          title="In-Person Rounds"
          value={interviews.filter((i) => i.mode === "IN_PERSON").length}
          icon={<MapPin className="w-5 h-5 text-teal-500" />}
          description="Campus auditorium & labs"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search candidate, company, panelist..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>

          <Select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Interview Stages</option>
            <option value="SCREENING">Screening</option>
            <option value="APTITUDE">Aptitude</option>
            <option value="TECHNICAL">Technical Round</option>
            <option value="MANAGERIAL">Managerial</option>
            <option value="HR">HR Round</option>
            <option value="FINAL">Final Executive Round</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs"
          >
            <option value="ALL">All Statuses</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="COMPLETED">Completed</option>
            <option value="RESCHEDULED">Rescheduled</option>
            <option value="CANCELLED">Cancelled</option>
          </Select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:bg-slate-900 dark:border-slate-800">
        <DataGrid
          data={filteredInterviews}
          columns={columns}
          keyExtractor={(item) => item.id}
          loading={loading}
          paginated
          pageSize={10}
          emptyMessage="No interview rounds found matching the selected filters."
        />
      </div>

      {/* Schedule Interview Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-white">
              Schedule Candidate Interview
            </h3>
            <p className="text-xs text-slate-400">
              Select shortlisted application, specify round, panelist details,
              and meeting room.
            </p>

            <form
              onSubmit={handleScheduleInterview}
              className="space-y-4 text-xs"
            >
              <div>
                <label className="text-slate-300 font-medium">
                  Candidate Application *
                </label>
                <select
                  value={formData.applicationId}
                  onChange={(e) =>
                    setFormData({ ...formData, applicationId: e.target.value })
                  }
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                >
                  {applications.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.studentName} ({a.rollNumber}) — {a.companyName} (
                      {a.positionTitle})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Interview Stage
                  </label>
                  <select
                    value={formData.stage}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        stage: e.target.value as InterviewStage,
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                  >
                    <option value="SCREENING">Screening</option>
                    <option value="APTITUDE">Aptitude Test</option>
                    <option value="TECHNICAL">Technical Round</option>
                    <option value="MANAGERIAL">Managerial</option>
                    <option value="HR">HR Round</option>
                    <option value="FINAL">Final Round</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Round Number
                  </label>
                  <Input
                    type="number"
                    value={formData.roundNumber}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        roundNumber: parseInt(e.target.value) || 1,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">Date *</label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) =>
                      setFormData({ ...formData, date: e.target.value })
                    }
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">Time *</label>
                  <Input
                    value={formData.time}
                    onChange={(e) =>
                      setFormData({ ...formData, time: e.target.value })
                    }
                    placeholder="10:00 AM"
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Duration (Min)
                  </label>
                  <Input
                    type="number"
                    value={formData.durationMinutes}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        durationMinutes: parseInt(e.target.value) || 45,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">Mode</label>
                  <select
                    value={formData.mode}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        mode: e.target.value as "ONLINE" | "IN_PERSON",
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white text-xs"
                  >
                    <option value="ONLINE">
                      Online / Virtual (Meeting URL)
                    </option>
                    <option value="IN_PERSON">In Person (Campus Room)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Meeting URL or Campus Room
                  </label>
                  <Input
                    value={formData.locationOrMeetingUrl}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        locationOrMeetingUrl: e.target.value,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium">
                    Lead Interviewer Name
                  </label>
                  <Input
                    value={formData.interviewerName}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        interviewerName: e.target.value,
                      })
                    }
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium">
                    Interviewer Email
                  </label>
                  <Input
                    value={formData.interviewerEmail}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        interviewerEmail: e.target.value,
                      })
                    }
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-300 font-medium">
                  Interview Brief & Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  rows={2}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Confirm Schedule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
