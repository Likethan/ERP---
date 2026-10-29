"use client";

import { useEffect, useState } from "react";
import {
  Calendar,
  CalendarDays,
  CheckCircle2,
  Clock,
  Compass,
  MapPin,
  PlusCircle,
  Search,
  UserCheck,
  Users2,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  ShiftCreateInput,
  VolunteerOpportunity,
  VolunteerShift,
} from "@/types/engagement";

export default function EngagementShiftsPage() {
  const [shifts, setShifts] = useState<VolunteerShift[]>([]);
  const [opportunities, setOpportunities] = useState<VolunteerOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedShift, setSelectedShift] = useState<VolunteerShift | null>(null);

  // Create Shift Form State
  const [oppId, setOppId] = useState("");
  const [title, setTitle] = useState("");
  const [shiftDate, setShiftDate] = useState(new Date().toISOString().split("T")[0]);
  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("12:00");
  const [capacity, setCapacity] = useState(15);
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [shs, opps] = await Promise.all([
        EngagementService.listShifts(),
        EngagementService.listOpportunities(),
      ]);
      setShifts(shs);
      setOpportunities(opps);
      if (opps.length > 0) setOppId(opps[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateShift(e: React.FormEvent) {
    e.preventDefault();
    if (!oppId || !title) return;

    try {
      const input: ShiftCreateInput = {
        opportunity_id: oppId,
        title,
        shift_date: shiftDate,
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
        capacity: Number(capacity),
        location,
        notes,
      };

      await EngagementService.createShift(input);
      setActionMessage("Shift scheduled successfully!");
      setIsCreateOpen(false);
      setTitle("");
      setNotes("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error scheduling shift: ${err.message}`);
    }
  }

  const filteredShifts = shifts.filter((s) => {
    return (
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      (s.location && s.location.toLowerCase().includes(search.toLowerCase()))
    );
  });

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {actionMessage && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-medium flex items-center justify-between">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <CalendarDays className="h-6 w-6 text-emerald-500" />
              Shifts, Rosters & Slot Management
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Organize field operations, schedule volunteer rosters, and monitor participant attendance
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create Shift</span>
          </button>
        </div>

        {/* Search */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search shifts by title, sector, or location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Shifts List Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredShifts.map((shift) => {
            const isFull = shift.assigned_count >= shift.capacity;

            return (
              <div
                key={shift.id}
                className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-emerald-500/50 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                      {shift.shift_date}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        isFull
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-blue-500/10 text-blue-500"
                      }`}
                    >
                      {shift.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-foreground line-clamp-1">{shift.title}</h3>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {shift.notes || "Standard volunteer service shift."}
                    </p>
                  </div>

                  <div className="space-y-1.5 text-xs text-muted-foreground border-t border-border pt-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" /> Timing:
                      </span>
                      <span className="text-foreground font-medium">
                        {shift.start_time.slice(0, 5)} - {shift.end_time.slice(0, 5)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Users2 className="h-3.5 w-3.5" /> Roster Count:
                      </span>
                      <span className="text-foreground font-semibold">
                        {shift.assigned_count} / {shift.capacity} volunteers
                      </span>
                    </div>

                    {shift.location && (
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5" /> Location:
                        </span>
                        <span className="text-foreground font-medium truncate max-w-[150px]">
                          {shift.location}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-t border-border pt-3">
                  <button
                    onClick={() => setSelectedShift(shift)}
                    className="w-full py-1.5 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium text-center"
                  >
                    View Roster & Volunteers
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Shift Details & Roster Modal */}
        {selectedShift && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground block">
                    Shift {selectedShift.shift_date} ({selectedShift.start_time.slice(0, 5)} - {selectedShift.end_time.slice(0, 5)})
                  </span>
                  <h2 className="text-base font-bold text-foreground">{selectedShift.title}</h2>
                </div>
                <button onClick={() => setSelectedShift(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="bg-muted/30 p-3 rounded-lg border border-border">
                  <h4 className="font-semibold text-foreground mb-1">Field Logistics:</h4>
                  <p className="text-muted-foreground">{selectedShift.notes || "No special logistics recorded."}</p>
                  {selectedShift.location && (
                    <p className="text-foreground font-medium mt-1">Location: {selectedShift.location}</p>
                  )}
                </div>

                <div>
                  <h4 className="font-semibold text-foreground mb-2 flex items-center justify-between">
                    <span>Enrolled Participants Roster ({selectedShift.assigned_count})</span>
                    <span className="text-[10px] text-muted-foreground">
                      Max {selectedShift.capacity}
                    </span>
                  </h4>
                  <div className="border border-border rounded-lg divide-y divide-border">
                    <div className="p-2.5 flex items-center justify-between">
                      <div>
                        <span className="font-medium text-foreground block">Kavya Ramesh</span>
                        <span className="text-[10px] text-muted-foreground font-mono">2023-CSE-042</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-[10px] font-semibold">
                        ASSIGNED
                      </span>
                    </div>
                    <div className="p-2.5 flex items-center justify-between">
                      <div>
                        <span className="font-medium text-foreground block">Pooja Sundaram</span>
                        <span className="text-[10px] text-muted-foreground font-mono">2023-IT-088</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-[10px] font-semibold">
                        CONFIRMED
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedShift(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Shift Modal */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-emerald-500" />
                  Schedule Volunteer Shift
                </h2>
                <button onClick={() => setIsCreateOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleCreateShift} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Linked Opportunity *</label>
                  <select
                    value={oppId}
                    onChange={(e) => setOppId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    required
                  >
                    {opportunities.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Shift Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Morning Cleanliness Marshall Shift"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Date *</label>
                    <input
                      type="date"
                      required
                      value={shiftDate}
                      onChange={(e) => setShiftDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Start Time *</label>
                    <input
                      type="time"
                      required
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">End Time *</label>
                    <input
                      type="time"
                      required
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Slot Capacity *</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      required
                      value={capacity}
                      onChange={(e) => setCapacity(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Field Location</label>
                    <input
                      type="text"
                      placeholder="e.g. Sector 2 Base Tent"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Operational Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Instructions for equipment, check-in requirements, or clothing..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Create Shift
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

