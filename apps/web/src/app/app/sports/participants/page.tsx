"use client";

import React, { useState, useEffect } from "react";
import { sportsService } from "@/services/sports.service";
import { SportsParticipantItem } from "@/types/sports";
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
  Users,
  PlusCircle,
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  FileText,
  Activity,
  Edit,
  UserCheck,
} from "lucide-react";

export default function SportsParticipantsPage() {
  const { addToast } = useToast();
  const [participants, setParticipants] = useState<SportsParticipantItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [clearanceFilter, setClearanceFilter] = useState("ALL");
  const [sportFilter, setSportFilter] = useState("ALL");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [selectedAthlete, setSelectedAthlete] = useState<SportsParticipantItem | null>(null);
  const [isClearanceOpen, setIsClearanceOpen] = useState(false);
  const [newClearanceStatus, setNewClearanceStatus] = useState("CLEARED");
  const [restrictionNote, setRestrictionNote] = useState("");

  const [regForm, setRegForm] = useState({
    userName: "",
    userEmail: "",
    participantCode: "",
    primarySport: "Basketball",
    department: "Computer Science",
    clearanceStatus: "CLEARED",
    consentRecorded: true,
  });

  useEffect(() => {
    loadParticipants();
  }, [sportFilter, clearanceFilter]);

  async function loadParticipants() {
    setLoading(true);
    const res = await sportsService.listParticipants(sportFilter, clearanceFilter);
    if (res.success && res.data) {
      setParticipants(res.data);
    }
    setLoading(false);
  }

  const filtered = participants.filter((p) => {
    const term = search.toLowerCase();
    return (
      p.userName.toLowerCase().includes(term) ||
      p.participantCode.toLowerCase().includes(term) ||
      p.primarySport.toLowerCase().includes(term)
    );
  });

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!regForm.userName || !regForm.participantCode) {
      addToast({ type: "error", title: "Validation Error", message: "Name and Participant Code are required." });
      return;
    }

    const res = await sportsService.createParticipant({
      userName: regForm.userName,
      userEmail: regForm.userEmail || `${regForm.userName.toLowerCase().replace(" ", ".")}@campusos.edu`,
      participantCode: regForm.participantCode.toUpperCase(),
      primarySport: regForm.primarySport,
      department: regForm.department,
      clearanceStatus: regForm.clearanceStatus as any,
      consentRecorded: regForm.consentRecorded,
    });

    if (res.success) {
      addToast({ type: "success", title: "Athlete Registered", message: `${regForm.userName} added to participant directory.` });
      setIsRegisterOpen(false);
      setRegForm({
        userName: "",
        userEmail: "",
        participantCode: "",
        primarySport: "Basketball",
        department: "Computer Science",
        clearanceStatus: "CLEARED",
        consentRecorded: true,
      });
      loadParticipants();
    }
  }

  async function handleUpdateClearance() {
    if (!selectedAthlete) return;

    const restrictions = restrictionNote
      ? { operationalRestriction: restrictionNote, updatedOn: new Date().toISOString() }
      : undefined;

    const res = await sportsService.updateParticipantClearance(
      selectedAthlete.id,
      newClearanceStatus,
      restrictions
    );

    if (res.success) {
      addToast({
        type: "success",
        title: "Clearance Updated",
        message: `${selectedAthlete.userName}'s athletic clearance set to ${newClearanceStatus}.`,
      });
      setIsClearanceOpen(false);
      setSelectedAthlete(null);
      setRestrictionNote("");
      loadParticipants();
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Sports & Athletics", href: "/app/sports" },
          { label: "Participant Directory", href: "/app/sports/participants" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Student Athlete & Participant Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Participant profiles, athletic eligibility verification, privacy-preserving clearances, and consent records.
          </p>
        </div>

        <Button
          size="sm"
          className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500"
          onClick={() => setIsRegisterOpen(true)}
        >
          <PlusCircle className="h-3.5 w-3.5" />
          Register Athlete
        </Button>
      </div>

      <SportsNav />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <SearchInput
            placeholder="Search code, name, or sport..."
            value={search}
            onChange={(val) => setSearch(val)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={clearanceFilter}
            onChange={(e) => setClearanceFilter(e.target.value)}
            options={[
              { value: "ALL", label: "All Clearances" },
              { value: "CLEARED", label: "Cleared" },
              { value: "RESTRICTED", label: "Restricted" },
              { value: "SUSPENDED", label: "Suspended" },
              { value: "PENDING", label: "Pending Checkup" },
            ]}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={sportFilter}
            onChange={(e) => setSportFilter(e.target.value)}
            options={[
              { value: "ALL", label: "All Sports" },
              { value: "Basketball", label: "Basketball" },
              { value: "Football", label: "Football" },
              { value: "Swimming", label: "Swimming" },
              { value: "Badminton", label: "Badminton" },
              { value: "Cricket", label: "Cricket" },
              { value: "Volleyball", label: "Volleyball" },
            ]}
          />
        </div>
      </div>

      {/* Participants Table Card */}
      <Card className="border-slate-800 bg-slate-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="p-3.5">Athlete Code & Name</th>
                <th className="p-3.5">Primary Sport</th>
                <th className="p-3.5">Academic Department</th>
                <th className="p-3.5">Clearance Status</th>
                <th className="p-3.5">Operational Restrictions (Privacy Safe)</th>
                <th className="p-3.5">Consent Record</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((part) => {
                let badgeVariant: "success" | "warning" | "destructive" | "default" = "default";
                if (part.clearanceStatus === "CLEARED") badgeVariant = "success";
                if (part.clearanceStatus === "RESTRICTED") badgeVariant = "warning";
                if (part.clearanceStatus === "SUSPENDED") badgeVariant = "destructive";

                const restrictionsText = part.operationalRestrictions
                  ? Object.entries(part.operationalRestrictions)
                      .map(([k, v]) => `${k.replace(/([A-Z])/g, " $1")}: ${v}`)
                      .join(", ")
                  : "None";

                return (
                  <tr key={part.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3.5">
                      <div className="font-semibold text-white">{part.userName}</div>
                      <div className="font-mono text-[11px] text-indigo-400">{part.participantCode}</div>
                    </td>
                    <td className="p-3.5 font-medium text-slate-200">
                      {part.primarySport}
                    </td>
                    <td className="p-3.5 text-slate-400">
                      {part.department || "General Athletics"}
                    </td>
                    <td className="p-3.5">
                      <Badge variant={badgeVariant}>{part.clearanceStatus}</Badge>
                      {part.clearanceExpiry && (
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          Exp: {part.clearanceExpiry}
                        </div>
                      )}
                    </td>
                    <td className="p-3.5 max-w-xs truncate text-slate-300">
                      {restrictionsText !== "None" ? (
                        <span className="text-amber-300 bg-amber-950/30 border border-amber-500/20 px-2 py-0.5 rounded text-[11px]">
                          {restrictionsText}
                        </span>
                      ) : (
                        <span className="text-slate-500">Unrestricted</span>
                      )}
                    </td>
                    <td className="p-3.5">
                      {part.consentRecorded ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                          <CheckCircle className="h-3 w-3" /> Signed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 text-[11px]">
                          <AlertTriangle className="h-3 w-3" /> Missing
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 gap-1"
                        onClick={() => {
                          setSelectedAthlete(part);
                          setNewClearanceStatus(part.clearanceStatus);
                          setRestrictionNote(
                            part.operationalRestrictions?.operationalRestriction || ""
                          );
                          setIsClearanceOpen(true);
                        }}
                      >
                        <Edit className="h-3 w-3" />
                        Clearance
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Clearance Update Modal */}
      <Dialog open={isClearanceOpen} onOpenChange={setIsClearanceOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-indigo-400" />
              Update Athletic Clearance: {selectedAthlete?.userName}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <p className="text-xs text-slate-400">
              Only minimum necessary operational clearance and safety restrictions are exposed. Sensitive medical diagnoses remain strictly shielded in the clinical health record.
            </p>

            <div>
              <Label htmlFor="clStatus" className="text-xs">Clearance Status *</Label>
              <Select
                id="clStatus"
                value={newClearanceStatus}
                onChange={(e) => setNewClearanceStatus(e.target.value)}
                options={[
                  { value: "CLEARED", label: "CLEARED - Full Contact & Competition" },
                  { value: "RESTRICTED", label: "RESTRICTED - Modified Practice Only" },
                  { value: "SUSPENDED", label: "SUSPENDED - No Athletic Activity" },
                  { value: "PENDING", label: "PENDING - Medical Screening Required" },
                ]}
                className="text-xs mt-1"
              />
            </div>

            <div>
              <Label htmlFor="restrictions" className="text-xs">
                Authorized Operational Restrictions (e.g. Max Minutes, Protective Gear)
              </Label>
              <Textarea
                id="restrictions"
                placeholder="e.g. Max 45 minutes session, non-contact drills only, requires ankle brace..."
                value={restrictionNote}
                onChange={(e) => setRestrictionNote(e.target.value)}
                className="text-xs mt-1"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button variant="outline" size="sm" onClick={() => setIsClearanceOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-500" onClick={handleUpdateClearance}>
              Save Clearance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Register Participant Modal */}
      <Dialog open={isRegisterOpen} onOpenChange={setIsRegisterOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Users className="h-5 w-5 text-indigo-400" />
              Register Student Athlete
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleRegister} className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="partCode" className="text-xs">Athlete Code *</Label>
                <Input
                  id="partCode"
                  placeholder="e.g. ATH-2026-042"
                  value={regForm.participantCode}
                  onChange={(e) => setRegForm({ ...regForm, participantCode: e.target.value })}
                  className="font-mono uppercase text-xs mt-1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="primarySport" className="text-xs">Primary Sport *</Label>
                <Select
                  id="primarySport"
                  value={regForm.primarySport}
                  onChange={(e) => setRegForm({ ...regForm, primarySport: e.target.value })}
                  options={[
                    { value: "Basketball", label: "Basketball" },
                    { value: "Football", label: "Football" },
                    { value: "Swimming", label: "Swimming" },
                    { value: "Badminton", label: "Badminton" },
                    { value: "Cricket", label: "Cricket" },
                    { value: "Volleyball", label: "Volleyball" },
                    { value: "Athletics", label: "Athletics / Track" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="fullName" className="text-xs">Student Full Name *</Label>
              <Input
                id="fullName"
                placeholder="e.g. Anirban Roy"
                value={regForm.userName}
                onChange={(e) => setRegForm({ ...regForm, userName: e.target.value })}
                className="text-xs mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="email" className="text-xs">Campus Email</Label>
                <Input
                  id="email"
                  placeholder="e.g. anirban@campusos.edu"
                  value={regForm.userEmail}
                  onChange={(e) => setRegForm({ ...regForm, userEmail: e.target.value })}
                  className="text-xs mt-1"
                />
              </div>
              <div>
                <Label htmlFor="dept" className="text-xs">Academic Department</Label>
                <Input
                  id="dept"
                  placeholder="e.g. Mechanical Eng."
                  value={regForm.department}
                  onChange={(e) => setRegForm({ ...regForm, department: e.target.value })}
                  className="text-xs mt-1"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="consent"
                checked={regForm.consentRecorded}
                onChange={(e) => setRegForm({ ...regForm, consentRecorded: e.target.checked })}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
              />
              <Label htmlFor="consent" className="text-xs text-slate-300">
                Participation Consent & Emergency Contact Document Signed on File
              </Label>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsRegisterOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-500">
                Confirm Registration
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
