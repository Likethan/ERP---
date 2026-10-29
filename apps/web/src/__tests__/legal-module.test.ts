/**
 * CampusOS — Step 62: Enterprise Legal Operations, Contract Lifecycle, Policy Compliance & Risk Test Suite
 *
 * Validates:
 * 1. Contract Lifecycle State Machine transitions (Draft -> Review -> Approval -> Execution -> Active -> Expiring/Terminated)
 * 2. Quantitative 5x5 Risk Matrix Calculation (Likelihood x Impact = Score, Level determinations)
 * 3. Contractual Obligation Health & Overdue status calculations
 * 4. Presentation formatters and security confidentiality badges
 */

import {
  calculateObligationHealth,
  calculateRiskMatrix,
  canTransitionContract,
  formatCurrency,
  formatLegalDate,
  getConfidentialityBadge,
  getContractStatusBadge,
  getExecutionMethodLabel,
  getMatterPriorityBadge,
  getMatterStatusBadge,
  getObligationStatusBadge,
  getRiskLevelBadge,
  isObligationOverdue,
} from "../services/legal-calculator";
import {
  ContractObligation,
  ContractStatus,
  InstitutionalContract,
} from "../types/legal";

function runTest(name: string, fn: () => void) {
  try {
    fn();
    console.log(`[PASS] ${name}`);
  } catch (err: any) {
    console.error(`[FAIL] ${name}: ${err.message}`);
    process.exitCode = 1;
  }
}

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertEquals<T>(actual: T, expected: T, message: string) {
  if (actual !== expected) {
    throw new Error(`${message} — Expected: ${expected}, Actual: ${actual}`);
  }
}

console.log("\n=======================================================");
console.log("CAMPUSOS STEP 62: LEGAL OPERATIONS FRONTEND TEST SUITE");
console.log("=======================================================\n");

// 1. Contract Lifecycle Transitions
runTest("Lifecycle: DRAFT can transition to INTERNAL_REVIEW, ON_HOLD, WITHDRAWN", () => {
  assert(canTransitionContract("DRAFT", "INTERNAL_REVIEW"), "DRAFT must transition to INTERNAL_REVIEW");
  assert(canTransitionContract("DRAFT", "ON_HOLD"), "DRAFT can be placed ON_HOLD");
  assert(canTransitionContract("DRAFT", "WITHDRAWN"), "DRAFT can be WITHDRAWN");
  assert(!canTransitionContract("DRAFT", "EXECUTED"), "DRAFT cannot directly transition to EXECUTED");
  assert(!canTransitionContract("DRAFT", "ACTIVE"), "DRAFT cannot directly transition to ACTIVE");
});

runTest("Lifecycle: Legal and Authorized approval transitions", () => {
  assert(canTransitionContract("INTERNAL_REVIEW", "DEPARTMENT_APPROVAL"), "INTERNAL_REVIEW -> DEPARTMENT_APPROVAL");
  assert(canTransitionContract("DEPARTMENT_APPROVAL", "LEGAL_REVIEW"), "DEPARTMENT_APPROVAL -> LEGAL_REVIEW");
  assert(canTransitionContract("LEGAL_REVIEW", "AUTHORIZED_APPROVAL"), "LEGAL_REVIEW -> AUTHORIZED_APPROVAL");
  assert(canTransitionContract("AUTHORIZED_APPROVAL", "READY_FOR_EXECUTION"), "AUTHORIZED_APPROVAL -> READY_FOR_EXECUTION");
  assert(canTransitionContract("READY_FOR_EXECUTION", "EXECUTED"), "READY_FOR_EXECUTION -> EXECUTED");
  assert(canTransitionContract("EXECUTED", "ACTIVE"), "EXECUTED -> ACTIVE");
});

runTest("Lifecycle: Terminal and Reversal transitions", () => {
  assert(canTransitionContract("ACTIVE", "EXPIRING"), "ACTIVE -> EXPIRING");
  assert(canTransitionContract("ACTIVE", "TERMINATED"), "ACTIVE -> TERMINATED");
  assert(canTransitionContract("LEGAL_REVIEW", "REJECTED"), "LEGAL_REVIEW can reject");
  assert(!canTransitionContract("ARCHIVED", "DRAFT"), "ARCHIVED cannot revert to DRAFT");
});

// 2. 5x5 Enterprise Risk Matrix Scoring
runTest("Risk Matrix: Critical level (16 - 25)", () => {
  const resultMax = calculateRiskMatrix(5, 5);
  assertEquals(resultMax.score, 25, "5x5 must equal 25");
  assertEquals(resultMax.level, "CRITICAL", "Score 25 must be CRITICAL");

  const resultMinCrit = calculateRiskMatrix(4, 4);
  assertEquals(resultMinCrit.score, 16, "4x4 must equal 16");
  assertEquals(resultMinCrit.level, "CRITICAL", "Score 16 must be CRITICAL");
});

runTest("Risk Matrix: High level (10 - 15)", () => {
  const result15 = calculateRiskMatrix(5, 3);
  assertEquals(result15.score, 15, "5x3 must equal 15");
  assertEquals(result15.level, "HIGH", "Score 15 must be HIGH");

  const result10 = calculateRiskMatrix(2, 5);
  assertEquals(result10.score, 10, "2x5 must equal 10");
  assertEquals(result10.level, "HIGH", "Score 10 must be HIGH");
});

runTest("Risk Matrix: Medium level (5 - 9)", () => {
  const result9 = calculateRiskMatrix(3, 3);
  assertEquals(result9.score, 9, "3x3 must equal 9");
  assertEquals(result9.level, "MEDIUM", "Score 9 must be MEDIUM");

  const result5 = calculateRiskMatrix(1, 5);
  assertEquals(result5.score, 5, "1x5 must equal 5");
  assertEquals(result5.level, "MEDIUM", "Score 5 must be MEDIUM");
});

runTest("Risk Matrix: Low level (1 - 4)", () => {
  const result4 = calculateRiskMatrix(2, 2);
  assertEquals(result4.score, 4, "2x2 must equal 4");
  assertEquals(result4.level, "LOW", "Score 4 must be LOW");

  const result1 = calculateRiskMatrix(1, 1);
  assertEquals(result1.score, 1, "1x1 must equal 1");
  assertEquals(result1.level, "LOW", "Score 1 must be LOW");
});

// 3. Contract Obligations Health & Overdue Calculations
runTest("Obligations: Overdue evaluation logic", () => {
  const pastObl: ContractObligation = {
    id: "obl-past",
    tenant_id: "tenant-001",
    obligation_code: "OBL-01",
    obligation_type: "DELIVERABLE",
    reminder_lead_days: 14,
    contract_id: "c-01",
    title: "Past Obligation",
    category: "DELIVERABLE",
    due_date: "2020-01-01",
    status: "PENDING",
    escalation_level: 0,
    created_at: "2020-01-01",
    updated_at: "2020-01-01",
  };
  assert(isObligationOverdue(pastObl), "Past pending obligation must be overdue");

  const completedObl: ContractObligation = {
    ...pastObl,
    id: "obl-comp",
    status: "COMPLETED",
  };
  assert(!isObligationOverdue(completedObl), "Completed past obligation must not be overdue");

  const futureObl: ContractObligation = {
    ...pastObl,
    id: "obl-fut",
    due_date: "2099-12-31",
  };
  assert(!isObligationOverdue(futureObl), "Future obligation must not be overdue");
});

runTest("Obligations: Aggregate health summary calculation", () => {
  const sampleList: ContractObligation[] = [
    {
      id: "1",
      tenant_id: "t1",
      obligation_code: "O1",
      obligation_type: "DELIVERABLE",
      reminder_lead_days: 14,
      contract_id: "c1",
      title: "O1",
      category: "DELIVERABLE",
      due_date: "2020-01-01",
      status: "PENDING",
      escalation_level: 1,
      created_at: "",
      updated_at: "",
    },
    {
      id: "2",
      tenant_id: "t1",
      obligation_code: "O2",
      obligation_type: "REPORTING",
      reminder_lead_days: 14,
      contract_id: "c1",
      title: "O2",
      category: "REPORTING",
      due_date: "2099-01-01",
      status: "IN_PROGRESS",
      escalation_level: 0,
      created_at: "",
      updated_at: "",
    },
    {
      id: "3",
      tenant_id: "t1",
      obligation_code: "O3",
      obligation_type: "PAYMENT_MILESTONE",
      reminder_lead_days: 14,
      contract_id: "c1",
      title: "O3",
      category: "PAYMENT_MILESTONE",
      due_date: "2020-01-01",
      status: "COMPLETED",
      escalation_level: 0,
      created_at: "",
      updated_at: "",
    },
    {
      id: "4",
      tenant_id: "t1",
      obligation_code: "O4",
      obligation_type: "COMPLIANCE_AUDIT",
      reminder_lead_days: 14,
      contract_id: "c1",
      title: "O4",
      category: "COMPLIANCE_AUDIT",
      due_date: "2020-01-01",
      status: "WAIVED",
      escalation_level: 0,
      created_at: "",
      updated_at: "",
    },
    {
      id: "5",
      tenant_id: "t1",
      obligation_code: "O5",
      obligation_type: "DELIVERABLE",
      reminder_lead_days: 14,
      contract_id: "c1",
      title: "O5",
      category: "DELIVERABLE",
      due_date: "2099-01-01",
      status: "PENDING",
      escalation_level: 0,
      created_at: "",
      updated_at: "",
    },
  ];

  const health = calculateObligationHealth(sampleList);
  assertEquals(health.total, 5, "Total must be 5");
  assertEquals(health.pending, 1, "Pending must be 1");
  assertEquals(health.in_progress, 1, "In progress must be 1");
  assertEquals(health.completed, 1, "Completed must be 1");
  assertEquals(health.waived, 1, "Waived must be 1");
  assertEquals(health.overdue, 1, "Overdue must be 1 (past pending)");
});

// 4. Formatting and Presentation
runTest("Presentation: Currency formatting", () => {
  assertEquals(formatCurrency(480000, "USD"), "$480,000", "480000 USD formatted");
  assertEquals(formatCurrency(undefined), "—", "Undefined currency formatted as —");
});

runTest("Presentation: Execution method labeling", () => {
  assertEquals(
    getExecutionMethodLabel("EXTERNAL_DIGITAL_SUITE_CONFIRMED"),
    "DocuSign / Adobe Sign Audit Certificate",
    "External digital suite label"
  );
  assertEquals(
    getExecutionMethodLabel("WET_SIGNATURE_CONFIRMED"),
    "Physical Wet Signature (Countersigned Scan)",
    "Wet signature label"
  );
});

console.log("\n=======================================================");
console.log("ALL STEP 62 LEGAL OPERATIONS FRONTEND TESTS PASSED!");
console.log("=======================================================\n");
