/**
 * Comprehensive Automated Test Suite for Campus Physical Security, Visitor Management & Emergency Response (Step 68).
 * CampusOS — "One Campus. One System. One Source of Truth."
 *
 * Verifies:
 * 1. Executive Operations Overview & Security Readiness Index
 * 2. Gate Checkpoints & Ingress Infrastructure
 * 3. Perimeter Security Clearance Zones
 * 4. Visitor Pre-registration, Host Approval & Pass Issuance
 * 5. Cryptographic Token Verification & Gate Operations (Check-in, Duplicate Prevention, Check-out, Revocation)
 * 6. Contractor Access Profiles & Safety Induction Certification
 * 7. Logical Access Grants & Auditable Revocation
 * 8. Security Incident Lifecycle (Report, Escalate, Resolve)
 * 9. Emergency Response Protocols (Initiation, Checklist Tasks, AAR Archival, Closure)
 * 10. Guard Patrol Routes, NFC Checkpoint Scans & Supervisor Review Sign-Off
 */

import { CampusSecurityService } from "../services/campus-security.service";

async function runCampusSecurityModuleTests() {
  console.log("================================================================================");
  console.log("STARTING AUTOMATED TEST SUITE: CAMPUS SECURITY, ACCESS CONTROL & EMERGENCY RESPONSE (STEP 68)");
  console.log("================================================================================\n");

  let passedTests = 0;
  let totalTests = 0;

  function assert(condition: boolean, testName: string, detail?: string) {
    totalTests++;
    if (condition) {
      passedTests++;
      console.log(`  ✓ [PASS] ${testName}`);
    } else {
      console.error(`  ✗ [FAIL] ${testName}${detail ? ` - ${detail}` : ""}`);
      throw new Error(`Assertion failed: ${testName}`);
    }
  }

  // ---------------------------------------------------------------------------
  // 1. EXECUTIVE OPERATIONS OVERVIEW & COMPOSITE READINESS SCORECARD
  // ---------------------------------------------------------------------------
  console.log("\n[1] Testing Executive Operations Overview & Composite Readiness Scorecard...");
  const overview = await CampusSecurityService.getOverview();
  assert(typeof overview === "object" && overview !== null, "Overview payload is returned");
  assert(overview.security_readiness_score >= 0 && overview.security_readiness_score <= 100, "Readiness score is bounded [0, 100]");
  assert(overview.manned_checkpoints_count >= 0, "Manned checkpoints count is non-negative");
  assert(overview.patrol_completion_rate_pct >= 0 && overview.patrol_completion_rate_pct <= 100, "Patrol rate is bounded [0, 100]");
  assert(overview.open_security_incidents >= 0, "Open security incidents count is non-negative");

  // ---------------------------------------------------------------------------
  // 2. CHECKPOINTS CONFIGURATION
  // ---------------------------------------------------------------------------
  console.log("\n[2] Testing Gate Checkpoints & Ingress Portals...");
  const initialCheckpoints = await CampusSecurityService.listCheckpoints();
  assert(Array.isArray(initialCheckpoints) && initialCheckpoints.length >= 3, "Initial checkpoint seed contains >= 3 checkpoints");

  const newCheckpoint = await CampusSecurityService.createCheckpoint({
    code: "GATE-TEST-NORTH",
    name: "North Testing Barrier Gate",
    checkpoint_type: "VEHICLE_BARRIER",
    location_description: "North test zone perimeter",
    is_manned: true,
    operating_hours: "24x7",
    guard_post_phone: "+91-44-2200-9999",
  });
  assert(newCheckpoint.code === "GATE-TEST-NORTH", "Checkpoint registered with correct uppercase code");
  assert(newCheckpoint.is_manned === true, "Checkpoint is marked manned");

  const mannedCheckpoints = await CampusSecurityService.listCheckpoints(true);
  assert(mannedCheckpoints.some((c) => c.code === "GATE-TEST-NORTH"), "Manned filter includes newly created checkpoint");

  // ---------------------------------------------------------------------------
  // 3. SECURITY CLEARANCE ZONES
  // ---------------------------------------------------------------------------
  console.log("\n[3] Testing Perimeter Demarcation & Clearance Zones...");
  const initialZones = await CampusSecurityService.listZones();
  assert(Array.isArray(initialZones) && initialZones.length >= 4, "Initial clearance zones contain >= 4 zones");

  const newZone = await CampusSecurityService.createZone({
    code: "ZONE-TEST-VAULT",
    name: "Secure Quantum Research Vault",
    clearance_level: "HIGH_SECURITY",
    building_name: "Research Complex Omega",
    floor_number: -1,
    requires_escort: true,
    max_occupancy: 10,
    emergency_assembly_point: "Sub-ground Assembly Bunker 1",
  });
  assert(newZone.code === "ZONE-TEST-VAULT", "High security zone created with correct code");
  assert(newZone.requires_escort === true, "Requires escort flag properly recorded");
  assert(newZone.clearance_level === "HIGH_SECURITY", "Clearance level verified as HIGH_SECURITY");

  const highSecZones = await CampusSecurityService.listZones("HIGH_SECURITY");
  assert(highSecZones.some((z) => z.code === "ZONE-TEST-VAULT"), "Clearance filter returns newly created high security zone");

  // ---------------------------------------------------------------------------
  // 4. VISITOR PRE-REGISTRATION & APPROVAL WORKFLOW
  // ---------------------------------------------------------------------------
  console.log("\n[4] Testing Visitor Pre-Registration & Host Approval...");
  const visitorProfile = await CampusSecurityService.createVisitorProfile({
    full_name: "Dr. Gregory House",
    email: "ghouse@princeton-plainsboro.edu",
    phone: "+1-609-555-0199",
    organization: "Diagnostics Institute",
    id_document_type: "PASSPORT",
    id_document_number_masked: "P*****9942",
    is_vip: true,
  });
  assert(visitorProfile.full_name === "Dr. Gregory House", "Visitor profile created successfully");
  assert(visitorProfile.is_vip === true, "VIP designation saved");

  const arrival = new Date(Date.now() + 3600 * 1000).toISOString();
  const departure = new Date(Date.now() + 5 * 3600 * 1000).toISOString();

  const visitorReq = await CampusSecurityService.createVisitorRequest({
    visitor_id: visitorProfile.id,
    visitor_name: visitorProfile.full_name,
    visitor_phone: visitorProfile.phone,
    visitor_email: visitorProfile.email,
    visitor_category: "VIP",
    host_name: "Prof. Dean Cuddy",
    host_department: "Executive Medical Administration",
    visit_purpose: "Keynote presentation on diagnostic immunology",
    destination_description: "Main Auditorium Block A",
    expected_arrival_at: arrival,
    expected_departure_at: departure,
    has_vehicle: true,
    vehicle_number: "TN-09-CD-1982",
    accompanying_count: 1,
  });
  assert(visitorReq.status === "PENDING", "Newly created visitor request is PENDING");
  assert(visitorReq.has_vehicle === true, "Vehicle details recorded");

  const approvedReq = await CampusSecurityService.approveVisitorRequest(visitorReq.id, "ADMIN-SUPERVISOR-01");
  assert(approvedReq.status === "APPROVED", "Visitor request transitioned to APPROVED");
  assert(approvedReq.approved_by_user_id === "ADMIN-SUPERVISOR-01", "Approver recorded in audit trail");

  // ---------------------------------------------------------------------------
  // 5. CRYPTOGRAPHIC VISITOR PASS TOKEN & GATE OPERATIONS
  // ---------------------------------------------------------------------------
  console.log("\n[5] Testing Pass Generation, Cryptographic Token & Gate Operations...");
  const visitorPass = await CampusSecurityService.generateVisitorPass(approvedReq.id, 8);
  assert(visitorPass.status === "ISSUED", "Visitor pass status is ISSUED");
  assert(Boolean(visitorPass.signed_token), "Cryptographically signed token is generated");
  assert(visitorPass.pass_number.startsWith("VPASS-"), "Pass number follows institutional VPASS prefix");

  // Token Verification
  const verifyResult = await CampusSecurityService.verifyVisitorPassToken(visitorPass.signed_token);
  assert(verifyResult.valid === true, "Signed pass token verified valid");
  assert(verifyResult.pass?.id === visitorPass.id, "Verified pass matches generated pass ID");

  // Check-In
  const checkInResult = await CampusSecurityService.checkInVisitor(
    visitorPass.signed_token,
    newCheckpoint.id,
    "OFFICER-BOOTH-01"
  );
  assert(checkInResult.success === true, "Visitor successfully checked in at gate");
  assert(checkInResult.pass?.status === "CHECKED_IN", "Pass status updated to CHECKED_IN");
  assert(Boolean(checkInResult.pass?.check_in_at), "Check-in timestamp recorded");

  // Duplicate Check-In Prevention
  const duplicateCheckIn = await CampusSecurityService.checkInVisitor(
    visitorPass.signed_token,
    newCheckpoint.id,
    "OFFICER-BOOTH-01"
  );
  assert(
    duplicateCheckIn.success === false,
    "Duplicate check-in blocked when visitor is already checked in"
  );
  assert(
    duplicateCheckIn.message.includes("Already checked in"),
    "Proper duplicate check-in rejection message provided"
  );

  // Check-Out
  const checkOutResult = await CampusSecurityService.checkOutVisitor(
    visitorPass.signed_token,
    newCheckpoint.id,
    "OFFICER-BOOTH-01"
  );
  assert(checkOutResult.success === true, "Visitor successfully checked out at gate");
  assert(checkOutResult.pass?.status === "CHECKED_OUT", "Pass status updated to CHECKED_OUT");
  assert(Boolean(checkOutResult.pass?.check_out_at), "Check-out timestamp recorded");

  // Revocation
  const revokePassResult = await CampusSecurityService.revokeVisitorPass(
    visitorPass.id,
    "End of visit / safety audit closure"
  );
  assert(revokePassResult.status === "REVOKED", "Visitor pass successfully revoked");
  assert(revokePassResult.revocation_reason?.includes("safety audit closure") === true, "Revocation reason logged");

  // ---------------------------------------------------------------------------
  // 6. CONTRACTOR PROFILES & SAFETY INDUCTION
  // ---------------------------------------------------------------------------
  console.log("\n[6] Testing Contractor Profiles & Safety Induction Certification...");
  const validUntil = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();
  const contractor = await CampusSecurityService.registerContractor({
    organization_name: "Apex High-Voltage Engineering Ltd",
    contractor_name: "Marcus Vance",
    contractor_phone: "+91-98840-77112",
    service_type: "Substation Transformer Overhaul",
    work_order_reference: "WO-2026-HV-091",
    valid_from: new Date().toISOString(),
    valid_until: validUntil,
    authorized_zone_ids: [newZone.id],
    emergency_contact_phone: "+91-98840-77000",
  });
  assert(contractor.contractor_code.startsWith("CONT-"), "Contractor code follows CONT- format");
  assert(contractor.is_safety_induction_completed === false, "New contractor initial safety induction is false");

  // Verify Safety Induction
  const verifiedContractor = await CampusSecurityService.verifyContractorSafetyInduction(contractor.id);
  assert(verifiedContractor.is_safety_induction_completed === true, "Safety induction verified successfully");
  assert(Boolean(verifiedContractor.safety_induction_date), "Safety induction timestamp recorded");

  // ---------------------------------------------------------------------------
  // 7. LOGICAL ACCESS GRANTS & AUDITABLE REVOCATION
  // ---------------------------------------------------------------------------
  console.log("\n[7] Testing Logical Access Grants & Auditable Revocation...");
  const accessGrant = await CampusSecurityService.createAccessGrant({
    zone_id: newZone.id,
    grantee_type: "STAFF",
    grantee_id: "USR-STAFF-902",
    grantee_name: "Dr. Elena Rostova",
    valid_from: new Date().toISOString(),
    valid_until: validUntil,
    is_temporary: true,
    grant_reason: "Primary investigator for quantum cryptanalysis grant",
  });
  assert(accessGrant.grant_number.startsWith("AG-"), "Access grant assigned AG- sequence");
  assert(accessGrant.status === "ACTIVE", "Access grant status initialized to ACTIVE");

  const revokedGrant = await CampusSecurityService.revokeAccessGrant(
    accessGrant.id,
    "Grant transferred to new lab supervisor"
  );
  assert(revokedGrant.status === "REVOKED", "Access grant revoked successfully");
  assert(revokedGrant.revocation_reason?.includes("transferred") === true, "Revocation reason recorded");

  // ---------------------------------------------------------------------------
  // 8. SECURITY INCIDENT REPORTING, ESCALATION & RESOLUTION
  // ---------------------------------------------------------------------------
  console.log("\n[8] Testing Security Incident Lifecycle (Report, Escalate, Resolve)...");
  const incident = await CampusSecurityService.reportIncident({
    title: "Suspicious RFID Cloning Attempt at Substation",
    category: "UNAUTHORIZED_ACCESS",
    severity: "HIGH",
    reported_location: "Electrical Substation Alpha",
    zone_id: newZone.id,
    description: "Access control telemetry detected repeat rapid badge scan anomalies.",
    assigned_team: "CAMPUS_PATROL_ALPHA",
  });
  assert(incident.incident_number.startsWith("SEC-INC-"), "Incident assigned SEC-INC- number");
  assert(incident.status === "REPORTED" || incident.status === "ASSIGNED", "Incident initial status valid");
  assert(incident.is_escalated === false, "Incident initially not escalated");

  // Escalate
  const escalatedIncident = await CampusSecurityService.escalateIncident(
    incident.id,
    "Potential coordinated breach attempt; notify Institutional Director."
  );
  assert(escalatedIncident.is_escalated === true, "Incident marked as escalated");
  assert(escalatedIncident.status === "ESCALATED", "Incident status transitioned to ESCALATED");

  // Resolve
  const resolvedIncident = await CampusSecurityService.resolveIncident(
    incident.id,
    "Telemetry isolated to faulty badge reader hardware component. Reader replaced and firmware updated.",
    "Hardware diagnostics audit scheduled for all perimeter readers within 48 hours."
  );
  assert(resolvedIncident.status === "RESOLVED", "Incident status transitioned to RESOLVED");
  assert(Boolean(resolvedIncident.resolved_at), "Resolution timestamp captured");
  assert(
    resolvedIncident.corrective_action_notes?.includes("Hardware diagnostics audit") === true,
    "Corrective action notes archived"
  );

  // ---------------------------------------------------------------------------
  // 9. EMERGENCY RESPONSE PROTOCOLS & AFTER-ACTION REPORTS
  // ---------------------------------------------------------------------------
  console.log("\n[9] Testing Emergency Response Protocol & Crisis Coordination...");
  const emergencyEvent = await CampusSecurityService.initiateEmergencyEvent({
    title: "High-Temperature Electrical Arcing Alert",
    event_type: "INFRASTRUCTURE_FAILURE",
    severity: "EMERGENCY",
    affected_campus_areas: "Electrical Substation Alpha & Surrounding Perimeter",
    coordinator_name: "Chief Safety Officer R. Chen",
    emergency_broadcast_message: "Substation Alpha alert: Maintain 100m standoff perimeter immediately.",
  });
  assert(emergencyEvent.event_code.startsWith("EMG-"), "Emergency event code generated");
  assert(emergencyEvent.status === "ACTIVE", "Emergency event initialized to ACTIVE status");
  assert(
    Array.isArray(emergencyEvent.tasks) && emergencyEvent.tasks.length > 0,
    "Checklist response tasks automatically spawned"
  );

  // Complete a checklist task
  const firstTask = emergencyEvent.tasks![0];
  const completedTask = await CampusSecurityService.completeEmergencyTask(
    firstTask.id,
    "Substation feed isolated via high-voltage disconnect switches."
  );
  assert(completedTask.status === "COMPLETED", "Emergency response task signed off as COMPLETED");
  assert(Boolean(completedTask.completed_at), "Task completion timestamp recorded");

  // Submit After-Action Report
  const aarEvent = await CampusSecurityService.submitAfterActionReport(
    emergencyEvent.id,
    "Power safely rerouted via secondary transformer within 18 minutes. No injuries or collateral asset loss. Recommendation: Quarterly infrared thermal inspection of main bus bars."
  );
  assert(
    aarEvent.after_action_report?.includes("secondary transformer") === true,
    "After-Action Report successfully archived"
  );

  // Close Event
  const closedEvent = await CampusSecurityService.closeEmergencyEvent(emergencyEvent.id);
  assert(closedEvent.status === "CLOSED", "Emergency event transitioned to CLOSED status");
  assert(Boolean(closedEvent.closed_at), "Emergency event closing timestamp recorded");

  // ---------------------------------------------------------------------------
  // 10. PATROL ROUTES, NFC CHECKPOINT SCANS & SUPERVISOR REVIEWS
  // ---------------------------------------------------------------------------
  console.log("\n[10] Testing Guard Patrol Routes, NFC Scans & Supervisor Sign-Off...");
  const patrolPlan = await CampusSecurityService.createPatrolPlan({
    title: "Night Perimeter Security & Perimeter Fence Verification",
    shift_name: "NIGHT_SHIFT",
    frequency_hours: 2,
    assigned_team_name: "Night Watch Guard Unit 3",
    checkpoints_sequence: [newCheckpoint.id],
  });
  assert(patrolPlan.plan_code.startsWith("PATROL-"), "Patrol plan code follows PATROL- prefix");
  assert(patrolPlan.shift_name === "NIGHT_SHIFT", "Shift recorded correctly");

  // Record Checkpoint Scan
  const patrolScan = await CampusSecurityService.scanPatrolCheckpoint({
    plan_id: patrolPlan.id,
    checkpoint_id: newCheckpoint.id,
    officer_name: "Officer D. Miller",
    scheduled_round_time: new Date().toISOString(),
    status: "COMPLETED",
    verification_token: "NFC-TEST-TAG-9092",
    observations: "Perimeter fence intact, exterior floodlights operational, barrier secured.",
  });
  assert(patrolScan.status === "COMPLETED", "Patrol checkpoint scan recorded as COMPLETED");
  assert(patrolScan.verification_token === "NFC-TEST-TAG-9092", "Verification token preserved");
  assert(patrolScan.supervisor_reviewed === false, "New scan initial review status is false");

  // Supervisor Review Sign-Off
  const reviewedScan = await CampusSecurityService.reviewPatrolRecord(
    patrolScan.id,
    "Time elapsed between posts verified against CCTV feed. All clear."
  );
  assert(reviewedScan.supervisor_reviewed === true, "Supervisor sign-off recorded");
  assert(
    reviewedScan.supervisor_review_notes?.includes("CCTV feed") === true,
    "Supervisor review notes saved"
  );

  // ---------------------------------------------------------------------------
  // SUMMARY
  // ---------------------------------------------------------------------------
  console.log("\n================================================================================");
  console.log(`TEST SUITE COMPLETED: ${passedTests}/${totalTests} ASSERTIONS PASSED (100% SUCCESS)`);
  console.log("================================================================================\n");
}

runCampusSecurityModuleTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
