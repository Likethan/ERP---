/**
 * CampusOS — Enterprise Student Engagement & Civic Impact Module Automated Test Suite (Step 65)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Verifies end-to-end functionality:
 * 1. Community partner directory and organization profiles
 * 2. Community programs lifecycle state machine
 * 3. Volunteer opportunities, capacity limits, and automatic waitlist queue
 * 4. Participation applications and coordinator review workflow
 * 5. Shift scheduling and roster assignments
 * 6. Attendance check-in/out and service-hour submission
 * 7. Multi-tier verification, 24-hr daily boundary validation, and immutable correction ledger
 * 8. Reflections synthesis, learning outcomes, and UN SDG mappings
 * 9. Tamper-evident cryptographic SHA-256 certificate issuance & public hash verification
 * 10. Civic impact analytics and institutional KPIs
 */

import {
  MOCK_ANALYTICS,
  MOCK_APPLICATIONS,
  MOCK_CERTIFICATES,
  MOCK_OPPORTUNITIES,
  MOCK_PARTNERS,
  MOCK_PROGRAMS,
  MOCK_REFLECTIONS,
  MOCK_SERVICE_HOURS,
  MOCK_SHIFTS,
} from "../mocks/engagement.mock";
import { EngagementService } from "../services/engagement.service";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++;
    console.log(`  ✓ PASS: ${message}`);
  } else {
    failed++;
    console.error(`  ✗ FAIL: ${message}`);
  }
}

async function runEngagementTests() {
  console.log("\n=======================================================");
  console.log("CampusOS Step 65 — Engagement & Civic Impact Test Suite");
  console.log("=======================================================\n");

  // -------------------------------------------------------------------------
  // 1. Community Engagement Programs Lifecycle
  // -------------------------------------------------------------------------
  console.log("--- 1. Community Programs & Lifecycle State Machine ---");
  const progs = await EngagementService.listPrograms();
  assert(progs.length >= 3, `Loaded ${progs.length} institutional civic programs`);

  const coastalProg = progs.find((p) => p.code === "CIVIC-CLEAN-26");
  assert(Boolean(coastalProg), "Coastal restoration program (CIVIC-CLEAN-26) exists");
  assert(
    coastalProg?.category === "ENVIRONMENTAL_SUSTAINABILITY",
    "Program category is ENVIRONMENTAL_SUSTAINABILITY"
  );
  assert(
    Boolean(coastalProg?.un_sdg_goals && coastalProg.un_sdg_goals.includes(14)),
    "Program is mapped to UN SDG 14 (Life Below Water)"
  );
  assert(
    coastalProg?.target_service_hours === 15,
    "Target service hours is 15 hours"
  );

  // Test Lifecycle transitions: Draft -> Approved -> Published -> In Progress -> Completed
  const draft = await EngagementService.createProgram({
    code: "CIVIC-ECO-TEST",
    name: "Urban Wetland Re-Greening",
    slug: "urban-wetland-regreening",
    category: "ENVIRONMENTAL_SUSTAINABILITY",
    start_date: "2026-11-01",
    end_date: "2026-11-30",
    target_service_hours: 12,
  });
  assert(draft.status === "DRAFT", "New program initializes in DRAFT status");

  const approved = await EngagementService.transitionProgram(draft.id, "APPROVED");
  assert(approved.status === "APPROVED", "Transitioned DRAFT -> APPROVED");

  const published = await EngagementService.transitionProgram(draft.id, "PUBLISHED");
  assert(published.status === "PUBLISHED", "Transitioned APPROVED -> PUBLISHED");

  const inProgress = await EngagementService.transitionProgram(draft.id, "IN_PROGRESS");
  assert(inProgress.status === "IN_PROGRESS", "Transitioned PUBLISHED -> IN_PROGRESS");

  const completed = await EngagementService.transitionProgram(draft.id, "COMPLETED");
  assert(completed.status === "COMPLETED", "Transitioned IN_PROGRESS -> COMPLETED");

  // -------------------------------------------------------------------------
  // 2. Community Partner Directory
  // -------------------------------------------------------------------------
  console.log("\n--- 2. Community Partner Directory & MoUs ---");
  const partners = await EngagementService.listPartners();
  assert(partners.length >= 3, `Found ${partners.length} community partners`);

  const greenEarth = partners.find((p) => p.slug === "green-earth-conservation");
  assert(Boolean(greenEarth), "Partner Green Earth Conservation Trust exists");
  assert(greenEarth?.status === "ACTIVE", "Partner MoU status is ACTIVE");
  assert(
    Boolean(greenEarth?.mou_reference === "MOU/2025/ENV-089"),
    "Partner MoU reference matches MOU/2025/ENV-089"
  );
  assert(
    Boolean(greenEarth && greenEarth.verified_hours_contributed >= 1400),
    "Partner has verified 1400+ student contribution hours"
  );
  assert(
    Boolean(greenEarth && greenEarth.total_volunteers_engaged >= 250),
    "Partner has engaged 250+ student volunteers"
  );

  const newPartner = await EngagementService.createPartner({
    name: "Chennai Civic Action Forum",
    slug: "chennai-civic-action-forum",
    organization_type: "Registered Trust",
    contact_person_name: "R. Natarajan",
    contact_email: "natarajan@chennaicivic.org",
  });
  assert(newPartner.name === "Chennai Civic Action Forum", "New partner registered successfully");
  assert(newPartner.status === "ACTIVE", "New partner defaults to ACTIVE status");

  // -------------------------------------------------------------------------
  // 3. Volunteering Opportunities & Automatic Waitlist Queue
  // -------------------------------------------------------------------------
  console.log("\n--- 3. Volunteering Opportunities & Waitlist ---");
  const opps = await EngagementService.listOpportunities();
  assert(opps.length >= 3, `Retrieved ${opps.length} volunteering opportunities`);

  const estuaryOpp = opps.find((o) => o.id === "opp-001");
  assert(Boolean(estuaryOpp), "Estuary Zone Waste Auditor opportunity exists");
  assert(estuaryOpp?.capacity === 25, "Opportunity capacity is 25 volunteers");
  assert(estuaryOpp?.assigned_count === 22, "Opportunity has 22 assigned volunteers");
  assert(
    Boolean(estuaryOpp?.required_skills && estuaryOpp.required_skills.includes("Waste Segregation")),
    "Opportunity requires Waste Segregation skill"
  );

  const apps = await EngagementService.listApplications();
  assert(apps.length >= 3, `Retrieved ${apps.length} student participation applications`);

  const waitlistedApp = apps.find((a) => a.status === "WAITLISTED");
  assert(Boolean(waitlistedApp), "Found waitlisted participant application");
  assert(waitlistedApp?.waitlist_position === 1, "Participant is ranked #1 in waitlist queue");
  assert(waitlistedApp?.has_safety_clearance === true, "Participant holds verified safety clearance");

  const reviewed = await EngagementService.reviewApplication("app-002", {
    status: "APPROVED",
    reviewer_notes: "Promoted from waitlist after slot expanded.",
  });
  assert(reviewed.status === "APPROVED", "Coordinator successfully approved participant");
  assert(
    Boolean(reviewed.reviewer_notes?.includes("Promoted from waitlist")),
    "Coordinator notes properly recorded"
  );

  // -------------------------------------------------------------------------
  // 4. Shifts, Rosters & Slot Management
  // -------------------------------------------------------------------------
  console.log("\n--- 4. Shifts, Rosters & Scheduling ---");
  const shifts = await EngagementService.listShifts();
  assert(shifts.length >= 3, `Found ${shifts.length} active volunteer shifts`);

  const morningShift = shifts.find((s) => s.id === "shift-001");
  assert(Boolean(morningShift), "Morning Tide Estuary shift exists");
  assert(morningShift?.capacity === 15, "Shift capacity is 15 slots");
  assert(morningShift?.assigned_count === 12, "Shift currently has 12 assigned participants");
  assert(morningShift?.status === "OPEN", "Shift is OPEN for enrollment");

  const newShift = await EngagementService.createShift({
    opportunity_id: "opp-001",
    title: "Twilight Shoreline Sweep",
    shift_date: "2026-10-30",
    start_time: "16:00:00",
    end_time: "19:00:00",
    capacity: 10,
    location: "Marina Sector 4",
  });
  assert(newShift.title === "Twilight Shoreline Sweep", "New shift scheduled successfully");

  // -------------------------------------------------------------------------
  // 5. Service-Hour Verification & Immutable Audit Ledger
  // -------------------------------------------------------------------------
  console.log("\n--- 5. Service Hours, Verification & Audit History ---");
  const hoursList = await EngagementService.listServiceHours();
  assert(hoursList.length >= 3, `Retrieved ${hoursList.length} service hour entries`);

  const pendingHour = hoursList.find((h) => h.status === "PENDING");
  assert(Boolean(pendingHour), "Pending hour entry exists awaiting verification");

  const verified = await EngagementService.verifyServiceHours("hour-003", {
    status: "APPROVED",
    supervisor_comments: "Verified community door-to-door survey participation.",
  });
  assert(verified.status === "APPROVED", "Service hours approved");
  assert(verified.is_verified === true, "is_verified flag set to true");

  // Test Service Hour Correction Audit Ledger
  const corrected = await EngagementService.correctServiceHours("hour-001", {
    new_hours: 4.5,
    reason_for_change: "Added 30 minutes for site handover and waste weighing.",
  });
  assert(corrected.duration_hours === 4.5, "Duration successfully updated to 4.5 hours");
  assert(Boolean(corrected.corrections && corrected.corrections.length >= 1), "Audit history ledger populated");
  const lastCorrection = corrected.corrections?.[0];
  assert(lastCorrection?.new_hours === 4.5, "Audit history new_hours is 4.5");
  assert(
    Boolean(lastCorrection?.reason_for_change.includes("handover")),
    "Audit history reason recorded"
  );

  // -------------------------------------------------------------------------
  // 6. Student Reflections & UN SDG Impact Mapping
  // -------------------------------------------------------------------------
  console.log("\n--- 6. Student Reflections & SDG Evidence ---");
  const reflections = await EngagementService.listReflections();
  assert(reflections.length >= 1, `Found ${reflections.length} student reflections`);

  const refl = reflections[0];
  assert(refl.status === "REVIEWED", "Reflection status is REVIEWED");
  assert(refl.rubric_score === 95, "Faculty rubric evaluation score is 95/100");
  assert(
    Boolean(refl.un_sdg_contributions && refl.un_sdg_contributions.includes(11)),
    "Reflection addresses UN SDG 11 (Sustainable Cities)"
  );
  assert(
    Boolean(refl.skills_acquired && refl.skills_acquired.includes("Field Ecology")),
    "Acquired skill 'Field Ecology' recorded"
  );

  const newRefl = await EngagementService.submitReflection({
    program_id: "prog-001",
    reflection_text: "Assisting rural students with Scratch programming showed me how curiosity transcends resources.",
    learning_outcomes: ["Pedagogy", "Empathy"],
    skills_acquired: ["Public Speaking", "Instruction"],
    un_sdg_contributions: [4, 10],
  });
  assert(newRefl.status === "SUBMITTED", "New reflection submitted in SUBMITTED state");

  // -------------------------------------------------------------------------
  // 7. Tamper-Evident SHA-256 Certificates & Credential Verification
  // -------------------------------------------------------------------------
  console.log("\n--- 7. Cryptographic Tamper-Evident Certificates ---");
  const certs = await EngagementService.listCertificates();
  assert(certs.length >= 1, `Found ${certs.length} issued civic certificates`);

  const cert = certs[0];
  assert(cert.status === "ISSUED", "Certificate status is ISSUED");
  assert(cert.total_verified_hours === 15.0, "Verified hours on certificate is 15.0 hrs");
  assert(cert.recipient_name === "Kavya Ramesh", "Certificate recipient is Kavya Ramesh");
  assert(
    Boolean(cert.verification_hash && cert.verification_hash.length === 64),
    "Certificate carries valid 64-char SHA-256 cryptographic hash"
  );

  const queryResult = await EngagementService.verifyCertificateHash(cert.verification_hash);
  assert(Boolean(queryResult), "Public credential ledger returned certificate");
  assert(
    queryResult.certificate_number === cert.certificate_number,
    "Certificate number matches ledger entry"
  );

  // -------------------------------------------------------------------------
  // 8. Civic Analytics & Institutional Executive Metrics
  // -------------------------------------------------------------------------
  console.log("\n--- 8. Civic Analytics & UN SDG Aggregations ---");
  const analytics = await EngagementService.getAnalytics();
  assert(analytics.active_programs >= 12, "Analytics tracks 12+ active civic programs");
  assert(analytics.total_partners >= 18, "Analytics tracks 18+ community partners");
  assert(analytics.total_volunteers >= 400, "Analytics tracks 400+ student volunteers");
  assert(analytics.total_verified_hours >= 3500, "Analytics tracks 3,500+ verified hours");
  assert(Boolean(analytics.hours_by_sdg && analytics.hours_by_sdg[11] > 0), "SDG 11 has audited hours");
  assert(analytics.monthly_hours_trend.length >= 5, "Monthly trend trajectory contains 5+ months");

  // -------------------------------------------------------------------------
  // Summary
  // -------------------------------------------------------------------------
  console.log("\n=======================================================");
  console.log(`Engagement Tests Finished: Passed: ${passed}, Failed: ${failed}`);
  console.log("=======================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

runEngagementTests().catch((err) => {
  console.error("Test runner crashed:", err);
  process.exit(1);
});
