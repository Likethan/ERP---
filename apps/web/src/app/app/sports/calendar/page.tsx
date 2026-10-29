"use client";

import React, { useState, useEffect } from "react";
import { sportsService } from "@/services/sports.service";
import { FacilityBookingItem, SportsFacilityItem } from "@/types/sports";
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
import { useToast } from "@/components/ui/toast";
import {
  Calendar,
  Clock,
  DoorOpen,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Users,
} from "lucide-react";

export default function FacilityCalendarPage() {
  const { addToast } = useToast();
  const [facilities, setFacilities] = useState<SportsFacilityItem[]>([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [bookings, setBookings] = useState<FacilityBookingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isBookOpen, setIsBookOpen] = useState(false);
  const [conflictWarning, setConflictWarning] = useState<string | null>(null);

  const [bookingForm, setBookingForm] = useState({
    title: "",
    purpose: "TRAINING",
    startTime: "16:00",
    endTime: "18:00",
    participantCount: 15,
    notes: "",
  });

  useEffect(() => {
    loadFacilities();
  }, []);

  useEffect(() => {
    if (selectedFacilityId) {
      loadBookings();
    }
  }, [selectedFacilityId, selectedDate]);

  async function loadFacilities() {
    const res = await sportsService.listFacilities();
    if (res.success && res.data.length > 0) {
      setFacilities(res.data);
      setSelectedFacilityId(res.data[0].id);
    }
  }

  async function loadBookings() {
    setLoading(true);
    const res = await sportsService.listBookings(selectedFacilityId, selectedDate);
    if (res.success && res.data) {
      setBookings(res.data);
    }
    setLoading(false);
  }

  const selectedFacility = facilities.find((f) => f.id === selectedFacilityId);

  async function handleCreateBooking(e: React.FormEvent) {
    e.preventDefault();
    setConflictWarning(null);

    const res = await sportsService.createBooking({
      facilityId: selectedFacilityId,
      facilityName: selectedFacility?.name || "Facility",
      title: bookingForm.title,
      purpose: bookingForm.purpose as any,
      bookingDate: selectedDate,
      startTime: bookingForm.startTime,
      endTime: bookingForm.endTime,
      participantCount: Number(bookingForm.participantCount),
      notes: bookingForm.notes,
    });

    if (res.success) {
      addToast({
        type: "success",
        title: "Reservation Confirmed",
        message: `Time slot ${bookingForm.startTime}-${bookingForm.endTime} reserved successfully.`,
      });
      setIsBookOpen(false);
      setBookingForm({
        title: "",
        purpose: "TRAINING",
        startTime: "16:00",
        endTime: "18:00",
        participantCount: 15,
        notes: "",
      });
      loadBookings();
    } else {
      setConflictWarning(res.error as string || "Booking conflict detected.");
      addToast({
        type: "error",
        title: "Reservation Conflict",
        message: res.error as string || "Reservation failed.",
      });
    }
  }

  async function handleCancelBooking(id: string) {
    const res = await sportsService.cancelBooking(id, "Cancelled by user");
    if (res.success) {
      addToast({
        type: "info",
        title: "Cancelled",
        message: "Facility reservation cancelled.",
      });
      loadBookings();
    }
  }

  // Generate hourly blocks from 06:00 to 22:00 for the daily schedule
  const hours = Array.from({ length: 16 }, (_, i) => i + 6);

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Sports & Athletics", href: "/app/sports" },
          { label: "Facility Calendar", href: "/app/sports/calendar" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Facility Availability Calendar & Conflict Engine
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Real-time court reservations, schedule conflict detection, and maintenance block synchronization.
          </p>
        </div>

        <Button
          size="sm"
          className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500"
          onClick={() => {
            setConflictWarning(null);
            setIsBookOpen(true);
          }}
          disabled={selectedFacility?.status === "MAINTENANCE_CLOSED"}
        >
          <PlusCircle className="h-3.5 w-3.5" />
          New Reservation
        </Button>
      </div>

      <SportsNav />

      {/* Date & Facility Selector Controls */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
        <div className="w-full sm:w-80">
          <Label className="text-xs text-slate-400 mb-1 block">Selected Facility / Court</Label>
          <Select
            value={selectedFacilityId}
            onChange={(e) => setSelectedFacilityId(e.target.value)}
            options={facilities.map((f) => ({
              value: f.id,
              label: `${f.name} (${f.surface}) ${f.status === "MAINTENANCE_CLOSED" ? "[CLOSED]" : ""}`,
            }))}
            className="text-xs"
          />
        </div>

        <div className="w-full sm:w-56">
          <Label className="text-xs text-slate-400 mb-1 block">Reservation Date</Label>
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-xs font-mono"
          />
        </div>

        <div className="sm:ml-auto flex items-center gap-2 pt-4 sm:pt-0">
          <Badge variant={selectedFacility?.status === "MAINTENANCE_CLOSED" ? "warning" : "success"}>
            {selectedFacility?.status || "AVAILABLE"}
          </Badge>
          <span className="text-xs text-slate-400 font-mono">
            Cap: {selectedFacility?.capacity || 0} pax
          </span>
        </div>
      </div>

      {/* Maintenance Closure Warning if selected facility is shut down */}
      {selectedFacility?.status === "MAINTENANCE_CLOSED" && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/40 bg-amber-950/20 p-4 text-amber-200">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-bold text-amber-300 text-sm">
              Venue Closed for Maintenance: {selectedFacility.name}
            </span>
            <p>
              This facility is currently marked <span className="font-mono">MAINTENANCE_CLOSED</span>. The system prevents all new training and tournament bookings for this space until certified reopened by the facility administrator.
            </p>
            <p className="text-slate-400 font-mono">
              Reason: {selectedFacility.maintenanceNotes || "Scheduled repairs"}
            </p>
          </div>
        </div>
      )}

      {/* Daily Visual Timeline & Bookings */}
      <Card className="p-5 border-slate-800 bg-slate-900/40">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <DoorOpen className="h-4 w-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">
              Schedule Timeline for {selectedFacility?.name} &bull; {selectedDate}
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            {bookings.filter((b) => b.status !== "CANCELLED").length} active slot(s) reserved
          </span>
        </div>

        {/* Visual Slot Ribbon */}
        <div className="mb-6 overflow-x-auto pb-2">
          <div className="min-w-[700px] border border-slate-800 rounded-lg p-3 bg-slate-950/60">
            <div className="grid grid-cols-16 gap-1 text-[10px] font-mono text-slate-500 text-center mb-2">
              {hours.map((h) => (
                <div key={h}>{`${h}:00`}</div>
              ))}
            </div>

            <div className="relative h-12 bg-slate-900/50 rounded-md border border-slate-800/80 flex items-center px-1">
              {bookings
                .filter((b) => b.status !== "CANCELLED")
                .map((b) => {
                  const startH = parseInt(b.startTime.split(":")[0], 10);
                  const startM = parseInt(b.startTime.split(":")[1], 10) || 0;
                  const endH = parseInt(b.endTime.split(":")[0], 10);
                  const endM = parseInt(b.endTime.split(":")[1], 10) || 0;

                  const startPos = Math.max(0, ((startH - 6) * 60 + startM) / (16 * 60)) * 100;
                  const duration = (((endH - startH) * 60 + (endM - startM)) / (16 * 60)) * 100;

                  return (
                    <div
                      key={b.id}
                      style={{ left: `${startPos}%`, width: `${duration}%` }}
                      className="absolute h-9 rounded bg-indigo-600/80 border border-indigo-400/40 px-2 py-0.5 text-[10px] text-white font-medium overflow-hidden truncate shadow-sm flex items-center justify-between"
                      title={`${b.title} (${b.startTime} - ${b.endTime})`}
                    >
                      <span className="truncate">{b.title}</span>
                      <span className="text-[9px] font-mono text-indigo-200 shrink-0 ml-1">
                        {b.startTime}-{b.endTime}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>

        {/* Bookings List Table */}
        <div className="space-y-3">
          {bookings.map((booking) => (
            <div
              key={booking.id}
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg border transition-all ${
                booking.status === "CANCELLED"
                  ? "border-slate-800/50 bg-slate-950/30 opacity-60"
                  : "border-slate-800 bg-slate-950/70 hover:border-slate-700"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white">{booking.title}</span>
                  <Badge variant={booking.status === "CONFIRMED" ? "success" : "default"}>
                    {booking.status}
                  </Badge>
                  <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-300">
                    {booking.purpose}
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-3">
                  <span className="flex items-center gap-1 font-mono text-indigo-300">
                    <Clock className="h-3 w-3" /> {booking.startTime} - {booking.endTime}
                  </span>
                  {booking.participantCount && (
                    <span className="flex items-center gap-1 text-slate-400">
                      <Users className="h-3 w-3" /> {booking.participantCount} pax
                    </span>
                  )}
                  {booking.notes && <span className="text-slate-400 italic">"{booking.notes}"</span>}
                </div>
              </div>

              {booking.status !== "CANCELLED" && (
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs text-rose-400 border-rose-500/30 hover:bg-rose-950/20 self-start sm:self-center"
                  onClick={() => handleCancelBooking(booking.id)}
                >
                  <XCircle className="h-3.5 w-3.5 mr-1" />
                  Cancel Slot
                </Button>
              )}
            </div>
          ))}

          {bookings.length === 0 && !loading && (
            <div className="h-32 flex flex-col items-center justify-center text-slate-500 text-xs gap-1.5 border border-dashed border-slate-800 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-emerald-500/60" />
              <span>Court is completely free on this date. No active bookings scheduled.</span>
            </div>
          )}
        </div>
      </Card>

      {/* Booking Modal Dialog */}
      <Dialog open={isBookOpen} onOpenChange={setIsBookOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Calendar className="h-5 w-5 text-indigo-400" />
              Reserve Facility Slot: {selectedFacility?.name}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateBooking} className="space-y-4 py-2">
            {conflictWarning && (
              <div className="p-3 rounded-lg border border-rose-500/40 bg-rose-950/30 text-rose-200 text-xs flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-rose-300">Conflict Detected:</span>{" "}
                  {conflictWarning}
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="bookTitle" className="text-xs">Event / Session Title *</Label>
              <Input
                id="bookTitle"
                placeholder="e.g. Varsity Squad Evening Practice"
                value={bookingForm.title}
                onChange={(e) => setBookingForm({ ...bookingForm, title: e.target.value })}
                className="text-xs mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="purpose" className="text-xs">Reservation Purpose</Label>
                <Select
                  id="purpose"
                  value={bookingForm.purpose}
                  onChange={(e) => setBookingForm({ ...bookingForm, purpose: e.target.value })}
                  options={[
                    { value: "TRAINING", label: "Team Training / Drills" },
                    { value: "MATCH", label: "Tournament Match" },
                    { value: "RECREATION", label: "Student Recreation" },
                    { value: "CLASS", label: "Physical Education Class" },
                    { value: "EVENT", label: "Campus Sports Gala" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>

              <div>
                <Label htmlFor="pax" className="text-xs">Estimated Attendees</Label>
                <Input
                  id="pax"
                  type="number"
                  value={bookingForm.participantCount}
                  onChange={(e) => setBookingForm({ ...bookingForm, participantCount: Number(e.target.value) })}
                  className="text-xs mt-1 font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="startTime" className="text-xs">Start Time (HH:MM) *</Label>
                <Input
                  id="startTime"
                  type="time"
                  value={bookingForm.startTime}
                  onChange={(e) => setBookingForm({ ...bookingForm, startTime: e.target.value })}
                  className="text-xs mt-1 font-mono"
                  required
                />
              </div>
              <div>
                <Label htmlFor="endTime" className="text-xs">End Time (HH:MM) *</Label>
                <Input
                  id="endTime"
                  type="time"
                  value={bookingForm.endTime}
                  onChange={(e) => setBookingForm({ ...bookingForm, endTime: e.target.value })}
                  className="text-xs mt-1 font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="bookNotes" className="text-xs">Operational Notes / Special Equipment</Label>
              <Textarea
                id="bookNotes"
                placeholder="e.g. Requires timing pads, shot clocks, and floor sweeping..."
                value={bookingForm.notes}
                onChange={(e) => setBookingForm({ ...bookingForm, notes: e.target.value })}
                className="text-xs mt-1"
                rows={2}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsBookOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-500">
                Confirm Reservation
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
