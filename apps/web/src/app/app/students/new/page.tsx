"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type {
  Program,
  Batch,
  Semester,
  Section,
  StudentDetail,
} from "@campusos/types";
import { apiFetch } from "@/lib/api-client";

export default function NewStudentAdmissionPage() {
  const router = useRouter();

  // Reference data
  const [programs, setPrograms] = useState<Program[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [loadingRefs, setLoadingRefs] = useState(true);

  // Form State
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("Welcome@123");
  const [phone, setPhone] = useState("");

  const [admissionNumber, setAdmissionNumber] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("2006-05-15");
  const [gender, setGender] = useState("MALE");
  const [bloodGroup, setBloodGroup] = useState("O+");
  const [admissionDate, setAdmissionDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [expectedGradDate, setExpectedGradDate] = useState(
    `${new Date().getFullYear() + 4}-05-31`,
  );

  const [programId, setProgramId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [sectionId, setSectionId] = useState("");

  const [emergencyName, setEmergencyName] = useState("");
  const [emergencyPhone, setEmergencyPhone] = useState("");

  // Submitting state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load programs, semesters, batches
  useEffect(() => {
    const loadPrerequisites = async () => {
      try {
        setLoadingRefs(true);
        const [progRes, semRes, batchRes] = await Promise.all([
          apiFetch<Program[]>("/api/v1/programs"),
          apiFetch<Semester[]>("/api/v1/academic-structure/semesters"),
          apiFetch<Batch[]>("/api/v1/academic-structure/batches"),
        ]);
        setPrograms(progRes.data);
        setSemesters(semRes.data);
        setBatches(batchRes.data);

        if (progRes.data.length > 0) {
          setProgramId(progRes.data[0].id);
        }
        if (semRes.data.length > 0) {
          setSemesterId(semRes.data[0].id);
        }
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load academic options",
        );
      } finally {
        setLoadingRefs(false);
      }
    };
    loadPrerequisites();
  }, []);

  // Update batch selection when program changes
  useEffect(() => {
    if (programId && batches.length > 0) {
      const filteredBatches = batches.filter((b) => b.program_id === programId);
      if (filteredBatches.length > 0) {
        setBatchId(filteredBatches[0].id);
      } else {
        setBatchId("");
      }
    }
  }, [programId, batches]);

  // Load sections when program, batch, or semester changes
  useEffect(() => {
    const loadSections = async () => {
      if (!programId) return;
      try {
        const params = new URLSearchParams();
        params.append("program_id", programId);
        if (batchId) params.append("batch_id", batchId);
        if (semesterId) params.append("semester_id", semesterId);
        const res = await apiFetch<Section[]>(
          `/api/v1/academic-structure/sections?${params.toString()}`,
        );
        setSections(res.data);
        if (res.data.length > 0) {
          setSectionId(res.data[0].id);
        } else {
          setSectionId("");
        }
      } catch {
        setSections([]);
      }
    };
    loadSections();
  }, [programId, batchId, semesterId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        email: email.trim().toLowerCase(),
        password: password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone_number: phone.trim() || undefined,
        admission_number: admissionNumber.trim().toUpperCase(),
        roll_number: rollNumber.trim().toUpperCase() || undefined,
        registration_number:
          registrationNumber.trim().toUpperCase() || undefined,
        date_of_birth: dateOfBirth,
        gender,
        blood_group: bloodGroup || undefined,
        admission_date: admissionDate,
        expected_graduation_date: expectedGradDate,
        program_id: programId,
        batch_id: batchId,
        current_semester_id: semesterId || undefined,
        current_section_id: sectionId || undefined,
        emergency_contact_name: emergencyName.trim() || undefined,
        emergency_contact_phone: emergencyPhone.trim() || undefined,
      };

      const res = await apiFetch<StudentDetail>("/api/v1/students", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      router.push(`/app/students/${res.data.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to admit student");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link
              href="/app/students"
              className="hover:text-blue-400 transition-colors"
            >
              ← Back to Student Directory
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Student Admission
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Create canonical identity, academic enrollment ledger, and baseline
            profile for a new student.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-sm flex items-start gap-3">
          <svg
            className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <div className="font-semibold">Admission Error</div>
            <div className="text-xs mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {loadingRefs ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500">
          Loading academic structures and programs...
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* SECTION 1: Personal & Identity Information */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="w-6 h-6 rounded-md bg-blue-950 border border-blue-800 text-blue-400 text-xs flex items-center justify-center font-mono">
                1
              </span>
              Personal Identity & Authentication
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  First Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Last Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Doe"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Institutional Email *
                </label>
                <input
                  type="email"
                  required
                  placeholder="john.doe@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Initial Password *
                </label>
                <input
                  type="text"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
                />
                <span className="text-[11px] text-slate-500">
                  Student will be prompted to change on first login.
                </span>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="+91 9876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Date of Birth *
                  </label>
                  <input
                    type="date"
                    required
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Gender *
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: Institutional Identifiers */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="w-6 h-6 rounded-md bg-blue-950 border border-blue-800 text-blue-400 text-xs flex items-center justify-center font-mono">
                2
              </span>
              Institutional Identifiers
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Admission Number *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ADM-2025-0101"
                  value={admissionNumber}
                  onChange={(e) => setAdmissionNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Roll Number
                </label>
                <input
                  type="text"
                  placeholder="25CS101"
                  value={rollNumber}
                  onChange={(e) => setRollNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Registration / Univ Number
                </label>
                <input
                  type="text"
                  placeholder="710025104001"
                  value={registrationNumber}
                  onChange={(e) => setRegistrationNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Admission Date *
                </label>
                <input
                  type="date"
                  required
                  value={admissionDate}
                  onChange={(e) => setAdmissionDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Expected Graduation Date *
                </label>
                <input
                  type="date"
                  required
                  value={expectedGradDate}
                  onChange={(e) => setExpectedGradDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Blood Group
                </label>
                <select
                  value={bloodGroup}
                  onChange={(e) => setBloodGroup(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            </div>
          </div>

          {/* SECTION 3: Academic Affiliation & Initial Enrollment */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="w-6 h-6 rounded-md bg-blue-950 border border-blue-800 text-blue-400 text-xs flex items-center justify-center font-mono">
                3
              </span>
              Academic Affiliation & Enrollment
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Degree Program *
                </label>
                <select
                  required
                  value={programId}
                  onChange={(e) => setProgramId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select Program</option>
                  {programs.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code} - {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Batch / Cohort *
                </label>
                <select
                  required
                  value={batchId}
                  onChange={(e) => setBatchId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select Batch</option>
                  {batches
                    .filter((b) => !programId || b.program_id === programId)
                    .map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} ({b.admission_year} - {b.graduation_year})
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Current Semester
                </label>
                <select
                  value={semesterId}
                  onChange={(e) => setSemesterId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select Semester</option>
                  {semesters.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} (Sem {s.semester_number})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Current Section
                </label>
                <select
                  value={sectionId}
                  onChange={(e) => setSectionId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Unassigned</option>
                  {sections.map((s) => (
                    <option key={s.id} value={s.id}>
                      Section {s.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* SECTION 4: Emergency Contacts */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="w-6 h-6 rounded-md bg-blue-950 border border-blue-800 text-blue-400 text-xs flex items-center justify-center font-mono">
                4
              </span>
              Emergency Contact & Guardian Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Emergency Contact / Guardian Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Robert Doe (Parent)"
                  value={emergencyName}
                  onChange={(e) => setEmergencyName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Emergency Contact Phone
                </label>
                <input
                  type="tel"
                  placeholder="+91 9876500000"
                  value={emergencyPhone}
                  onChange={(e) => setEmergencyPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-4 pt-2">
            <Link
              href="/app/students"
              className="px-5 py-2.5 rounded-lg border border-slate-700 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-semibold text-white transition-colors disabled:opacity-50 shadow-md flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8H4z"
                    />
                  </svg>
                  Admitting Student...
                </>
              ) : (
                "Admit Student & Create Identity"
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
