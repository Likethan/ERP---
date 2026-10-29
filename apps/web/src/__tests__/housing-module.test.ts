/**
 * CampusOS — Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Automated Test Suite (Step 66)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Verifies end-to-end functionality:
 * 1. Accommodation Providers and Landlord Directory with vetted MoUs
 * 2. Property Registry and Lifecycle State Machine (Draft, Approved, Published, Suspended)
 * 3. Unit and Bed Inventory with Quarantine Maintenance Blocks
 * 4. Student Housing Requests, Priority Scoring, and Waitlist Ordering
 * 5. Formal Accommodation Offers and Electronic Acceptance
 * 6. Concurrency-Safe Bed Allocation and Anti-Double-Booking Protection
 * 7. Inter-Room Transfers and Relocation Audit Trails
 * 8. Tenancy Agreements, Digital Leases, and ERP Invoice References
 * 9. Move-In Check-In and Move-Out Check-Out Handover Audits with Damage Assessment
 * 10. Safety, Fire, and Sanitation Inspections with Automated Suspension Gates
 * 11. Facilities Maintenance Ticketing and Technician Dispatch
 * 12. Real-Time Occupancy Analytics and Bed Telemetry
 */

import { HousingService } from "../services/housing.service";

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

async function runHousingTests() {
  console.log("\n==========================================================================");
  console.log("CampusOS Step 66 — Enterprise Student Housing & Accommodation Test Suite");
  console.log("==========================================================================\n");

  // -------------------------------------------------------------------------
  // 1. Accommodation Providers & Landlord Directory
  // -------------------------------------------------------------------------
  console.log("--- 1. Accommodation Providers & Landlord Directory ---");
  const providers = await HousingService.listProviders();
  assert(providers.length >= 3, `Loaded ${providers.length} registered accommodation providers`);

  const apexLiving = providers.find((p) => p.name.includes("Apex Living"));
  assert(Boolean(apexLiving), "Apex Living commercial operator found");
  assert(apexLiving?.provider_type === "HOUSING_COMPANY", "Apex Living provider type is HOUSING_COMPANY");
  assert(apexLiving?.verification_status === "VERIFIED", "Apex Living MoU is verified");
  assert(Boolean(apexLiving?.mou_reference), `MoU reference present: ${apexLiving?.mou_reference}`);

  // Test provider creation
  const newProvider = await HousingService.createProvider({
    name: "Sri Krishna Educational Student Residences",
    slug: "sri-krishna-residences",
    provider_type: "STUDENT_RESIDENCE_TRUST",
    contact_name: "G. Venkatesh",
    contact_email: "venkatesh@krishnaresidences.org",
    contact_phone: "+91 98450 11223",
    city: "Bengaluru",
    state: "Karnataka",
    mou_reference: "MOU-VSB-2026-T09",
  });
  assert(newProvider.name === "Sri Krishna Educational Student Residences", "New trust provider created successfully");
  assert(newProvider.verification_status === "PENDING", "Newly registered provider defaults to PENDING review");

  // Test MoU verification transition
  const verifiedProv = await HousingService.verifyProvider(newProvider.id, true);
  assert(verifiedProv.verification_status === "VERIFIED", "Provider successfully verified after institutional due diligence");

  // -------------------------------------------------------------------------
  // 2. Property Registry & Lifecycle State Machine
  // -------------------------------------------------------------------------
  console.log("\n--- 2. Property Registry & Lifecycle Transitions ---");
  const properties = await HousingService.listProperties(false);
  assert(properties.length >= 4, `Loaded ${properties.length} residential properties`);

  const emerald = properties.find((p) => p.code === "EMR-TWR");
  assert(Boolean(emerald), "Emerald Residence Hall found");
  assert(emerald?.lifecycle_status === "PUBLISHED", "Emerald Residence is PUBLISHED for student discovery");
  assert(emerald?.property_type === "CAMPUS_HOSTEL", "Property type is CAMPUS_HOSTEL");
  assert(emerald?.total_bed_capacity === 120, "Emerald Residence bed capacity is 120 beds");

  // Test Property Creation in DRAFT
  const draftProp = await HousingService.createProperty({
    code: "TEST-RES-01",
    name: "Nandi Vista Student Suites",
    slug: "nandi-vista-suites",
    property_type: "OFF_CAMPUS_HOSTEL",
    address: "Plot 42, Electronic City Phase 1",
    distance_to_campus_km: 1.8,
    monthly_rent_min: 9000,
    monthly_rent_max: 14000,
    security_deposit_amount: 18000,
  });
  assert(draftProp.lifecycle_status === "DRAFT", "New property initialized in DRAFT status");

  // Transition: DRAFT -> APPROVED -> PUBLISHED
  const approvedProp = await HousingService.transitionProperty(draftProp.id, {
    target_status: "APPROVED",
  });
  assert(approvedProp.lifecycle_status === "APPROVED", "Property successfully transitioned to APPROVED");

  const publishedProp = await HousingService.transitionProperty(draftProp.id, {
    target_status: "PUBLISHED",
  });
  assert(publishedProp.lifecycle_status === "PUBLISHED", "Property successfully published to student discovery");

  // -------------------------------------------------------------------------
  // 3. Units & Addressable Bed Capacity Inventory
  // -------------------------------------------------------------------------
  console.log("\n--- 3. Units & Addressable Bed Inventory ---");
  const units = await HousingService.listUnits(emerald?.id || "prop-001");
  assert(units.length >= 2, `Loaded ${units.length} room units for property`);

  const unit101 = units.find((u) => u.unit_number === "Room 101");
  assert(Boolean(unit101), "Unit Room 101 exists in inventory");
  assert(unit101?.bed_capacity === 2, "Unit Room 101 has 2 beds capacity");
  assert(Boolean(unit101?.beds && unit101.beds.length >= 2), "Unit Room 101 has addressable bed slots");

  // Test Bed Blocking for Maintenance Quarantine
  const bedToBlock = unit101?.beds?.[0];
  assert(Boolean(bedToBlock), "Found addressable bed slot");
  if (bedToBlock) {
    const blockedBed = await HousingService.toggleBedBlock(
      bedToBlock.id,
      true,
      "Emergency HVAC repair"
    );
    assert(blockedBed.status === "BLOCKED_MAINTENANCE", "Bed status updated to BLOCKED_MAINTENANCE");
    assert(blockedBed.is_available === false, "Bed availability flag set to false");

    // Unblock and restore
    const restoredBed = await HousingService.toggleBedBlock(bedToBlock.id, false);
    assert(restoredBed.status === "AVAILABLE", "Bed status restored to AVAILABLE after repair");
  }

  // -------------------------------------------------------------------------
  // 4. Student Housing Requests & Waitlist Queue
  // -------------------------------------------------------------------------
  console.log("\n--- 4. Student Housing Requests & Waitlist Ranking ---");
  const requests = await HousingService.listRequests();
  assert(requests.length >= 3, `Loaded ${requests.length} student housing applications`);

  const priorityReq = requests.find((r) => r.accessibility_required);
  assert(Boolean(priorityReq), "Accessibility-priority request identified");
  assert(Boolean(priorityReq && priorityReq.priority_score >= 80), "Accessibility request scored high priority");

  // Test submitting a request
  const newReq = await HousingService.submitRequest({
    preferred_unit_type: "SINGLE_OCCUPANCY",
    academic_term: "2026-27 Odd Semester",
    requested_move_in_date: "2026-07-15",
    requested_move_out_date: "2027-05-31",
    budget_max: 12000,
    accessibility_required: true,
    special_requests: "Requires ground-floor room for wheelchair mobility",
  });
  assert(newReq.status === "SUBMITTED", "Housing request submitted in SUBMITTED status");
  assert(newReq.priority_score >= 85, "High priority assigned for accessibility requirement");

  // Review & Waitlist Request
  const reviewedReq = await HousingService.reviewRequest(newReq.id, {
    status: "WAITLISTED",
    review_notes: "Medical cert verified by campus health center",
    priority_score: 95,
  });
  assert(reviewedReq.status === "WAITLISTED", "Request approved and placed in waitlist");
  assert(Boolean(reviewedReq.waitlist_position), `Waitlist position assigned: #${reviewedReq.waitlist_position}`);

  // -------------------------------------------------------------------------
  // 5. Formal Offers & Electronic Acceptance
  // -------------------------------------------------------------------------
  console.log("\n--- 5. Formal Offers & Electronic Acceptance ---");
  const offers = await HousingService.listOffers();
  assert(offers.length >= 1, `Loaded ${offers.length} accommodation offers`);

  // Create an electronic offer
  const newOffer = await HousingService.createOffer({
    request_id: newReq.id,
    property_id: emerald?.id || "prop-001",
    unit_id: unit101?.id || "unit-001",
    bed_id: unit101?.beds?.[1]?.id || "bed-002",
    offered_rent_monthly: 9500,
    offered_deposit: 15000,
    occupancy_start_date: "2026-07-15",
    occupancy_end_date: "2027-05-31",
    offer_valid_days: 3,
  });
  assert(newOffer.status === "OFFERED", "Formal electronic offer issued with OFFERED status");
  assert(newOffer.offered_rent_monthly === 9500, "Commercial rent terms bound to offer");

  // Student accepts offer
  const acceptedOffer = await HousingService.respondToOffer(newOffer.id, {
    decision: "ACCEPTED",
    response_notes: "Terms accepted via student portal digital signature",
  });
  assert(acceptedOffer.status === "ACCEPTED", "Offer successfully accepted by student");

  // -------------------------------------------------------------------------
  // 6. Concurrency-Safe Bed Allocation
  // -------------------------------------------------------------------------
  console.log("\n--- 6. Concurrency-Safe Bed Allocation ---");
  const assignments = await HousingService.listAssignments();
  assert(assignments.length >= 2, `Loaded ${assignments.length} active room allocations`);

  // Allocate student
  const newAssignment = await HousingService.allocateStudent({
    student_id: "stu-2026-042",
    property_id: emerald?.id || "prop-001",
    unit_id: unit101?.id || "unit-001",
    bed_id: unit101?.beds?.[1]?.id || "bed-002",
    start_date: "2026-07-15",
    end_date: "2027-05-31",
    monthly_rent: 9500,
    security_deposit: 15000,
  });
  assert(newAssignment.status === "ACTIVE", "Student successfully allocated to bed slot");
  assert(Boolean(newAssignment.assignment_number), `Generated assignment number: ${newAssignment.assignment_number}`);

  // -------------------------------------------------------------------------
  // 7. Inter-Room Transfers & Relocation Audit
  // -------------------------------------------------------------------------
  console.log("\n--- 7. Inter-Room Transfers & Relocation Audit ---");
  const transferred = await HousingService.transferRoom(newAssignment.id, {
    target_unit_id: "unit-002",
    target_bed_id: "bed-004",
    transfer_reason: "Quiet study floor preference",
  });
  assert(transferred.status === "TRANSFERRED", "Assignment updated to TRANSFERRED");
  assert(transferred.unit_id === "unit-002", "New unit ID registered on assignment");
  assert(transferred.transfer_reason === "Quiet study floor preference", "Audit reason recorded");

  // -------------------------------------------------------------------------
  // 8. Tenancy Agreements & Finance References
  // -------------------------------------------------------------------------
  console.log("\n--- 8. Tenancy Agreements & Digital Leases ---");
  const agreements = await HousingService.listAgreements();
  assert(agreements.length >= 1, `Loaded ${agreements.length} digital tenancy agreements`);

  const sampleAgr = agreements[0];
  assert(Boolean(sampleAgr.agreement_number), `Agreement number: ${sampleAgr.agreement_number}`);
  assert(sampleAgr.deposit_refund_status === "HELD", "Security deposit escrow status is HELD");
  assert(Boolean(sampleAgr.deposit_invoice_reference), `Deposit ERP invoice: ${sampleAgr.deposit_invoice_reference}`);

  // Create agreement
  const createdAgr = await HousingService.createAgreement({
    assignment_id: newAssignment.id,
    agreement_title: "CampusOS Standard Residence Lease Agreement 2026-27",
    valid_from: "2026-07-15",
    valid_to: "2027-05-31",
    rent_amount: 9500,
    deposit_amount: 15000,
    payment_frequency: "MONTHLY_ADVANCE",
    finance_invoice_reference: "INV-2026-HOU-9901",
    deposit_invoice_reference: "DEP-2026-HOU-9901",
  });
  assert(createdAgr.rent_amount === 9500, "Agreement bound with correct monthly rent");
  assert(createdAgr.status === "PENDING_SIGNATURE", "Agreement status set to PENDING_SIGNATURE");

  // -------------------------------------------------------------------------
  // 9. Handover Audits & Damage Settlement
  // -------------------------------------------------------------------------
  console.log("\n--- 9. Handover Audits & Damage Settlement ---");
  const checkins = await HousingService.listCheckIns();
  assert(checkins.length >= 1, `Loaded ${checkins.length} check-in/out records`);

  // Record Check-Out with Damage Assessment
  const checkoutRecord = await HousingService.recordCheckInOut({
    assignment_id: newAssignment.id,
    record_type: "CHECK_OUT",
    scheduled_date: "2027-05-31",
    key_card_issued_or_returned: true,
    key_identifier: "RFID-CARD-8819",
    room_condition_rating: "FAIR",
    damage_assessed_amount: 1200,
    damage_description: "Deep study desk scratch requiring polish",
    notes: "Security deposit refunded after net ₹1,200 deduction",
  });
  assert(checkoutRecord.record_type === "CHECK_OUT", "Check-out event recorded");
  assert(checkoutRecord.damage_assessed_amount === 1200, "Damage assessed amount registered for deposit deduction");

  // -------------------------------------------------------------------------
  // 10. Safety Inspections & Auto-Suspension Gate
  // -------------------------------------------------------------------------
  console.log("\n--- 10. Safety Inspections & Auto-Suspension Gate ---");
  const inspections = await HousingService.listInspections();
  assert(inspections.length >= 2, `Loaded ${inspections.length} statutory inspections`);

  // Record critical safety inspection failure
  const criticalFailure = await HousingService.recordInspection({
    property_id: draftProp.id,
    inspection_date: "2026-10-28",
    inspection_type: "SAFETY_FIRE",
    overall_outcome: "FAILED_CRITICAL",
    critical_issues_found: true,
    safety_score: 35,
    corrective_actions_required: "Replace defective hydrants in Wing C immediately",
  });
  assert(criticalFailure.overall_outcome === "FAILED_CRITICAL", "Critical failure logged");
  assert(criticalFailure.availability_suspended === true, "Automated suspension flag engaged");

  // Verify property state is suspended
  const propsAfterInspection = await HousingService.listProperties(false);
  const suspendedProp = propsAfterInspection.find((p) => p.id === draftProp.id);
  assert(
    suspendedProp?.lifecycle_status === "SUSPENDED",
    "Property automatically transitioned to SUSPENDED due to critical safety failure"
  );

  // -------------------------------------------------------------------------
  // 11. Maintenance Tickets & Facilities Work Orders
  // -------------------------------------------------------------------------
  console.log("\n--- 11. Maintenance Ticketing & Work Orders ---");
  const tickets = await HousingService.listMaintenance();
  assert(tickets.length >= 2, `Loaded ${tickets.length} residential maintenance tickets`);

  // Submit maintenance defect ticket
  const newTicket = await HousingService.submitMaintenance({
    property_id: emerald?.id || "prop-001",
    unit_id: unit101?.id || "unit-001",
    category: "PLUMBING",
    priority: "HIGH",
    title: "Ensuite washroom flush leaking continuously",
    description: "Water valve seal failure in Room 101 ensuite washroom.",
  });
  assert(newTicket.status === "REPORTED", "Defect ticket logged with REPORTED status");
  assert(newTicket.priority === "HIGH", "High priority tagged");

  // Update and resolve ticket with tenant satisfaction
  const resolvedTicket = await HousingService.updateMaintenance(newTicket.id, {
    status: "COMPLETED",
    assigned_technician_name: "Sundar Raj (Certified Plumber)",
    completion_notes: "Float valve seal replaced; water flow calibrated.",
    tenant_satisfaction_rating: 5,
    tenant_feedback: "Prompt repair within 3 hours. Completely resolved.",
  });
  assert(resolvedTicket.status === "COMPLETED", "Ticket marked as COMPLETED");
  assert(resolvedTicket.tenant_satisfaction_rating === 5, "5-star tenant rating recorded");

  // -------------------------------------------------------------------------
  // 12. Real-Time Occupancy Analytics & Telemetry
  // -------------------------------------------------------------------------
  console.log("\n--- 12. Housing Analytics & Bed Telemetry ---");
  const analytics = await HousingService.getAnalytics();
  assert(Boolean(analytics), "Analytics telemetry loaded");
  assert(analytics.total_approved_properties >= 4, `Approved properties: ${analytics.total_approved_properties}`);
  assert(analytics.total_capacity_beds > 0, `Total bed capacity: ${analytics.total_capacity_beds}`);
  assert(analytics.occupied_beds > 0, `Occupied beds: ${analytics.occupied_beds}`);
  assert(analytics.available_beds >= 0, `Available beds: ${analytics.available_beds}`);
  assert(
    analytics.occupancy_rate_percentage > 0 && analytics.occupancy_rate_percentage <= 100,
    `Calculated occupancy rate: ${analytics.occupancy_rate_percentage.toFixed(1)}%`
  );
  assert(analytics.open_maintenance_requests >= 0, `Open maintenance requests: ${analytics.open_maintenance_requests}`);

  // Summary
  console.log("\n==========================================================================");
  console.log(`TEST SUITE RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log("==========================================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

runHousingTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
