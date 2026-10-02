/**
 * CampusOS Finance Mock Datasets
 * Coherent, relational financial graph linking canonical Students, Programs,
 * Fee Categories, Structures, Invoices, Payments, Allocations, Receipts,
 * Scholarships, Adjustments, and Refunds.
 */

import {
  FeeCategory,
  FeeItem,
  FeeStructure,
  StudentFeeAssignment,
  Invoice,
  Payment,
  Receipt,
  Scholarship,
  StudentScholarship,
  FinancialAdjustment,
  Refund,
  FinanceDashboardSummary,
} from "@/types/finance";

// ==========================================
// Legacy Interface Mirrors (Preserve Back-Compat)
// ==========================================

export interface FeeStructureItem {
  id: string;
  name: string;
  program: string;
  academicYear: string;
  totalAnnualFee: number;
  components: Array<{
    title: string;
    amount: number;
    mandatory: boolean;
  }>;
  status: "ACTIVE" | "DRAFT" | "ARCHIVED";
}

export interface InvoiceItem {
  id: string;
  invoiceNumber: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  dueDate: string;
  issueDate: string;
  totalAmount: number;
  paidAmount: number;
  balanceAmount: number;
  status: "PAID" | "PARTIALLY_PAID" | "ISSUED" | "OVERDUE" | "CANCELLED" | "DRAFT";
}

export interface PaymentTransactionItem {
  id: string;
  transactionRef: string;
  receiptNumber: string;
  studentName: string;
  rollNumber: string;
  invoiceNumber: string;
  amount: number;
  paymentMode: "UPI" | "NET_BANKING" | "NEFT_RTGS" | "DEMAND_DRAFT" | "CASH_COUNTER" | "CARD" | "CHEQUE";
  paymentDate: string;
  status: "SUCCESS" | "PENDING" | "REVERSED" | "FAILED";
}

export interface ScholarshipItem {
  id: string;
  studentName: string;
  rollNumber: string;
  scholarshipScheme: string;
  sanctionAmount: number;
  disbursedAmount: number;
  academicYear: string;
  status: "DISBURSED" | "APPROVED" | "PENDING_VERIFICATION";
}

// ==========================================
// 1. Canonical Fee Categories
// ==========================================

export const MOCK_FEE_CATEGORIES: FeeCategory[] = [
  {
    id: "cat-tuition",
    code: "TUI",
    name: "Tuition Fee",
    description: "Core academic instruction, curriculum delivery, and faculty hours.",
    type: "TUITION",
    isTaxable: false,
    isRefundable: false,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-exam",
    code: "EXM",
    name: "Examination & Evaluation Fee",
    description: "Midterm tests, end semester university question banks, and grading.",
    type: "EXAMINATION",
    isTaxable: false,
    isRefundable: false,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-lab",
    code: "LAB",
    name: "Laboratory & Computing Fee",
    description: "High performance GPU lab access, engineering workstations, and consumable kits.",
    type: "LABORATORY",
    isTaxable: false,
    isRefundable: false,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-lib",
    code: "LIB",
    name: "Library & E-Resources Fee",
    description: "IEEE Xplore, ACM Digital Library subscriptions, and book lending facility.",
    type: "LIBRARY",
    isTaxable: false,
    isRefundable: false,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-hostel",
    code: "HST",
    name: "Residential Hostel & Mess Fee",
    description: "Campus accommodation, electricity, hygiene maintenance, and catering.",
    type: "HOSTEL",
    isTaxable: false,
    isRefundable: true,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-trans",
    code: "TRN",
    name: "Campus Transport Fee",
    description: "Dedicated daily institutional commuter bus transit across designated routes.",
    type: "TRANSPORT",
    isTaxable: false,
    isRefundable: true,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
  {
    id: "cat-dev",
    code: "DEV",
    name: "Campus Development & Student Welfare",
    description: "Sports complexes, student clubs, incubation labs, and campus Wi-Fi infrastructure.",
    type: "DEVELOPMENT",
    isTaxable: false,
    isRefundable: false,
    status: "ACTIVE",
    createdAt: "2026-06-01T09:00:00Z",
    updatedAt: "2026-06-01T09:00:00Z",
  },
];

// ==========================================
// 2. Canonical Fee Items
// ==========================================

export const MOCK_FEE_ITEMS: FeeItem[] = [
  {
    id: "item-btech-tui-s5",
    categoryId: "cat-tuition",
    categoryName: "Tuition Fee",
    code: "TUI-BTECH-S5",
    name: "B.Tech Semester 5 Tuition Fee",
    description: "Core lecture and tutorial credit hours for engineering semester 5.",
    program: "B.Tech Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    amount: 55000,
    isOptional: false,
    isRefundable: false,
    isActive: true,
    createdAt: "2026-06-10T10:00:00Z",
  },
  {
    id: "item-btech-lab-s5",
    categoryId: "cat-lab",
    categoryName: "Laboratory & Computing Fee",
    code: "LAB-CSE-S5",
    name: "Advanced Database & OS Lab Practicals",
    description: "Laboratory equipment maintenance, software licenses, and cloud compute credits.",
    program: "B.Tech Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    amount: 15000,
    isOptional: false,
    isRefundable: false,
    isActive: true,
    createdAt: "2026-06-10T10:00:00Z",
  },
  {
    id: "item-btech-exam-s5",
    categoryId: "cat-exam",
    categoryName: "Examination & Evaluation Fee",
    code: "EXAM-S5",
    name: "University End Semester Examination Fee",
    description: "Formative evaluation, question paper encryption, external valuation, and grade sheets.",
    program: "B.Tech Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    amount: 3500,
    isOptional: false,
    isRefundable: false,
    isActive: true,
    createdAt: "2026-06-10T10:00:00Z",
  },
  {
    id: "item-btech-lib-s5",
    categoryId: "cat-lib",
    categoryName: "Library & E-Resources Fee",
    code: "LIB-ANNUAL",
    name: "Digital Library Access & Physical Journal Subscriptions",
    description: "Annual subscription to international technical repositories and lending access.",
    program: "B.Tech Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    amount: 2500,
    isOptional: false,
    isRefundable: false,
    isActive: true,
    createdAt: "2026-06-10T10:00:00Z",
  },
  {
    id: "item-hostel-double",
    categoryId: "cat-hostel",
    categoryName: "Residential Hostel & Mess Fee",
    code: "HST-DBL-ROOM",
    name: "Hostel Accommodation (Double Occupancy)",
    description: "Furnished room with power backup, Wi-Fi, and mess catering charges.",
    program: "All Programs",
    academicYear: "2026-2027",
    semester: 5,
    amount: 45000,
    isOptional: true,
    isRefundable: true,
    isActive: true,
    createdAt: "2026-06-10T10:00:00Z",
  },
];

// ==========================================
// 3. Canonical Fee Structures
// ==========================================

export const MOCK_CANONICAL_FEE_STRUCTURES: FeeStructure[] = [
  {
    id: "fs-btech-cse-s5",
    code: "FS-2026-CSE-S5",
    name: "B.Tech Computer Science & Engineering Semester 5 Standard Fee Scheme",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    components: [
      { id: "fsc-1", feeItemId: "item-btech-tui-s5", title: "Academic Tuition Fee", categoryName: "Tuition Fee", amount: 55000, isMandatory: true },
      { id: "fsc-2", feeItemId: "item-btech-lab-s5", title: "Advanced Computing Lab Levy", categoryName: "Laboratory Fee", amount: 15000, isMandatory: true },
      { id: "fsc-3", feeItemId: "item-btech-exam-s5", title: "Semester Examination Fee", categoryName: "Examination Fee", amount: 3500, isMandatory: true },
      { id: "fsc-4", feeItemId: "item-btech-lib-s5", title: "Library & E-Resource Subscriptions", categoryName: "Library Fee", amount: 2500, isMandatory: true },
    ],
    grossTotal: 76000,
    status: "ACTIVE",
    effectiveDate: "2026-07-01",
    approvedBy: "Finance Committee & Academic Senate",
    approvedAt: "2026-06-25T14:30:00Z",
    notes: "Mandatory semester scheme for all regular enrolled candidates in Section A and B.",
    totalStudentsAssigned: 68,
    createdAt: "2026-06-15T11:00:00Z",
    updatedAt: "2026-06-25T14:30:00Z",
    history: [
      { id: "h-1", action: "CREATED", actor: "Accounts Officer (B. K. Sharma)", timestamp: "2026-06-15T11:00:00Z", notes: "Draft fee schedule compiled." },
      { id: "h-2", action: "SUBMITTED_FOR_APPROVAL", actor: "Finance Dean", timestamp: "2026-06-20T10:00:00Z", notes: "Submitted to Senate committee." },
      { id: "h-3", action: "APPROVED", actor: "Registrar / Academic Senate", timestamp: "2026-06-25T14:30:00Z", notes: "Approved without fee revision." },
      { id: "h-4", action: "ACTIVATED", actor: "Chief Finance Officer", timestamp: "2026-07-01T09:00:00Z", notes: "Scheme activated for student billing." },
    ],
  },
  {
    id: "fs-btech-ece-s5",
    code: "FS-2026-ECE-S5",
    name: "B.Tech Electronics & Communication Engineering Semester 5 Standard Fee Scheme",
    program: "B.Tech Electronics & Communication",
    department: "Electronics & Communication Engineering",
    academicYear: "2026-2027",
    semester: 5,
    components: [
      { id: "fsc-ece-1", title: "Academic Tuition Fee", categoryName: "Tuition Fee", amount: 55000, isMandatory: true },
      { id: "fsc-ece-2", title: "VLSI & Embedded Systems Laboratory", categoryName: "Laboratory Fee", amount: 16000, isMandatory: true },
      { id: "fsc-ece-3", title: "Semester Examination Fee", categoryName: "Examination Fee", amount: 3500, isMandatory: true },
      { id: "fsc-ece-4", title: "Library & Technical Resources", categoryName: "Library Fee", amount: 2500, isMandatory: true },
    ],
    grossTotal: 77000,
    status: "ACTIVE",
    effectiveDate: "2026-07-01",
    approvedBy: "Finance Committee",
    approvedAt: "2026-06-25T15:00:00Z",
    totalStudentsAssigned: 54,
    createdAt: "2026-06-15T11:30:00Z",
    updatedAt: "2026-06-25T15:00:00Z",
    history: [
      { id: "h-ece-1", action: "CREATED", actor: "Accounts Officer", timestamp: "2026-06-15T11:30:00Z" },
      { id: "h-ece-2", action: "APPROVED", actor: "Finance Dean", timestamp: "2026-06-25T15:00:00Z" },
    ],
  },
  {
    id: "fs-hostel-mess-2026",
    code: "FS-2026-HOSTEL",
    name: "Residential Hostel Room & Central Mess Caterer Schedule 2026-27",
    program: "All Residential Students",
    department: "Campus Operations & Facilities",
    academicYear: "2026-2027",
    semester: 5,
    components: [
      { id: "fsc-h-1", title: "Hostel Room Rent (Double Occupancy)", categoryName: "Hostel Fee", amount: 25000, isMandatory: true },
      { id: "fsc-h-2", title: "Central Dining & Mess Catering", categoryName: "Hostel Fee", amount: 20000, isMandatory: true },
      { id: "fsc-h-3", title: "Hostel Amenities, Maintenance & Wi-Fi", categoryName: "Development Fee", amount: 5000, isMandatory: true },
    ],
    grossTotal: 50000,
    status: "ACTIVE",
    effectiveDate: "2026-07-01",
    approvedBy: "Hostel Warden & Chief Finance Officer",
    approvedAt: "2026-06-28T10:00:00Z",
    totalStudentsAssigned: 32,
    createdAt: "2026-06-18T10:00:00Z",
    updatedAt: "2026-06-28T10:00:00Z",
    history: [
      { id: "h-h-1", action: "CREATED", actor: "Hostel Manager", timestamp: "2026-06-18T10:00:00Z" },
      { id: "h-h-2", action: "APPROVED", actor: "CFO", timestamp: "2026-06-28T10:00:00Z" },
    ],
  },
  {
    id: "fs-btech-aids-s7",
    code: "FS-2026-AIDS-S7",
    name: "B.Tech AI & Data Science Semester 7 Capstone Scheme",
    program: "B.Tech AI & Data Science",
    department: "Artificial Intelligence & Data Science",
    academicYear: "2026-2027",
    semester: 7,
    components: [
      { id: "fsc-ai-1", title: "Tuition Fee", categoryName: "Tuition Fee", amount: 50000, isMandatory: true },
      { id: "fsc-ai-2", title: "Industry Capstone & GPU Lab", categoryName: "Laboratory Fee", amount: 18000, isMandatory: true },
      { id: "fsc-ai-3", title: "Placement & Evaluation Levy", categoryName: "Examination Fee", amount: 5000, isMandatory: true },
    ],
    grossTotal: 73000,
    status: "PENDING_APPROVAL",
    effectiveDate: "2026-11-01",
    notes: "Awaiting final review from Industrial Advisory Board.",
    totalStudentsAssigned: 0,
    createdAt: "2026-09-10T14:00:00Z",
    updatedAt: "2026-09-15T09:30:00Z",
    history: [
      { id: "h-ai-1", action: "CREATED", actor: "Dept Finance Coordinator", timestamp: "2026-09-10T14:00:00Z" },
      { id: "h-ai-2", action: "SUBMITTED_FOR_APPROVAL", actor: "HOD AI-DS", timestamp: "2026-09-15T09:30:00Z" },
    ],
  },
];

// ==========================================
// 4. Canonical Student Fee Assignments
// ==========================================

export const MOCK_STUDENT_FEE_ASSIGNMENTS: StudentFeeAssignment[] = [
  {
    id: "assign-std-001",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    feeStructureId: "fs-btech-cse-s5",
    feeStructureName: "B.Tech CSE Semester 5 Standard Fee Scheme",
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 76000,
    paidAmount: 76000,
    outstandingAmount: 0,
    status: "ACTIVE",
    assignedDate: "2026-07-05",
    invoiceId: "inv-2026-0001",
    notes: "Regular seat admission.",
  },
  {
    id: "assign-std-002",
    studentId: "std-002",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    feeStructureId: "fs-btech-cse-s5",
    feeStructureName: "B.Tech CSE Semester 5 Standard Fee Scheme",
    grossAmount: 76000,
    scholarshipAmount: 15200, // 20% Merit scholarship
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 60800,
    paidAmount: 60800,
    outstandingAmount: 0,
    status: "ACTIVE",
    assignedDate: "2026-07-05",
    invoiceId: "inv-2026-0002",
    notes: "University Merit Scholarship applied (20% waiver).",
  },
  {
    id: "assign-std-003",
    studentId: "std-003",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    feeStructureId: "fs-btech-cse-s5",
    feeStructureName: "B.Tech CSE Semester 5 Standard Fee Scheme",
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 76000,
    paidAmount: 40000,
    outstandingAmount: 36000,
    status: "ACTIVE",
    assignedDate: "2026-07-05",
    invoiceId: "inv-2026-0003",
    notes: "Partially settled; balance subject to installment plan.",
  },
  {
    id: "assign-std-004",
    studentId: "std-004",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    program: "B.Tech Electronics & Communication",
    department: "Electronics & Communication Engineering",
    academicYear: "2026-2027",
    semester: 5,
    feeStructureId: "fs-btech-ece-s5",
    feeStructureName: "B.Tech ECE Semester 5 Standard Fee Scheme",
    grossAmount: 77000,
    scholarshipAmount: 40000, // Fellowship
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 37000,
    paidAmount: 37000,
    outstandingAmount: 0,
    status: "ACTIVE",
    assignedDate: "2026-07-05",
    invoiceId: "inv-2026-0004",
    notes: "Women in Engineering fellowship applied.",
  },
  {
    id: "assign-std-005",
    studentId: "std-005",
    studentName: "Vikramaditya Rao",
    rollNumber: "24AI0301",
    program: "B.Tech AI & Data Science",
    department: "Computer Science & Engineering",
    academicYear: "2026-2027",
    semester: 5,
    feeStructureId: "fs-btech-cse-s5",
    feeStructureName: "B.Tech CSE Semester 5 Standard Fee Scheme",
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 5000, // Early bird discount
    adjustmentAmount: 0,
    netPayable: 71000,
    paidAmount: 0,
    outstandingAmount: 71000,
    status: "ACTIVE",
    assignedDate: "2026-07-05",
    invoiceId: "inv-2026-0005",
    notes: "Overdue invoice.",
  },
];

// ==========================================
// 5. Canonical Invoices
// ==========================================

export const MOCK_CANONICAL_INVOICES: Invoice[] = [
  {
    id: "inv-2026-0001",
    invoiceNumber: "INV-2026-0001",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-07-15",
    dueDate: "2026-08-15",
    lines: [
      { id: "line-1", title: "B.Tech Semester 5 Academic Tuition Fee", categoryName: "Tuition Fee", quantity: 1, unitAmount: 55000, totalAmount: 55000 },
      { id: "line-2", title: "Advanced Computing Laboratory Levy", categoryName: "Laboratory Fee", quantity: 1, unitAmount: 15000, totalAmount: 15000 },
      { id: "line-3", title: "Semester 5 Examination & Evaluation", categoryName: "Examination Fee", quantity: 1, unitAmount: 3500, totalAmount: 3500 },
      { id: "line-4", title: "Library & Technical Periodicals Subscription", categoryName: "Library Fee", quantity: 1, unitAmount: 2500, totalAmount: 2500 },
    ],
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 76000,
    paidAmount: 76000,
    outstandingAmount: 0,
    status: "PAID",
    feeAssignmentId: "assign-std-001",
    paymentIds: ["pay-2026-0001"],
    receiptIds: ["rec-2026-0001"],
    createdAt: "2026-07-15T09:00:00Z",
    updatedAt: "2026-08-02T11:30:00Z",
    history: [
      { id: "ih-1", action: "ISSUED", actor: "Billing Engine", timestamp: "2026-07-15T09:00:00Z", notes: "Invoice generated from assigned fee structure." },
      { id: "ih-2", action: "PAYMENT_RECORDED", actor: "Aarav Patel (UPI Gateway)", timestamp: "2026-08-02T11:30:00Z", notes: "Full payment of ₹76,000 received." },
      { id: "ih-3", action: "PAID", actor: "Finance System", timestamp: "2026-08-02T11:30:00Z", notes: "Invoice settled in full. Receipt REC-2026-0001 issued." },
    ],
  },
  {
    id: "inv-2026-0002",
    invoiceNumber: "INV-2026-0002",
    studentId: "std-002",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-07-15",
    dueDate: "2026-08-15",
    lines: [
      { id: "line-2-1", title: "B.Tech Semester 5 Academic Tuition Fee", categoryName: "Tuition Fee", quantity: 1, unitAmount: 55000, totalAmount: 55000 },
      { id: "line-2-2", title: "Advanced Computing Laboratory Levy", categoryName: "Laboratory Fee", quantity: 1, unitAmount: 15000, totalAmount: 15000 },
      { id: "line-2-3", title: "Semester 5 Examination & Evaluation", categoryName: "Examination Fee", quantity: 1, unitAmount: 3500, totalAmount: 3500 },
      { id: "line-2-4", title: "Library & Technical Periodicals Subscription", categoryName: "Library Fee", quantity: 1, unitAmount: 2500, totalAmount: 2500 },
    ],
    grossAmount: 76000,
    scholarshipAmount: 15200,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 60800,
    paidAmount: 60800,
    outstandingAmount: 0,
    status: "PAID",
    feeAssignmentId: "assign-std-002",
    paymentIds: ["pay-2026-0002"],
    receiptIds: ["rec-2026-0002"],
    createdAt: "2026-07-15T09:00:00Z",
    updatedAt: "2026-08-05T14:20:00Z",
    history: [
      { id: "ih-2-1", action: "ISSUED", actor: "Billing Engine", timestamp: "2026-07-15T09:00:00Z", notes: "Gross ₹76,000, Merit waiver ₹15,200 deducted." },
      { id: "ih-2-2", action: "PAYMENT_RECORDED", actor: "Priya Sundaram (Net Banking)", timestamp: "2026-08-05T14:20:00Z", notes: "Payment of ₹60,800 confirmed." },
    ],
  },
  {
    id: "inv-2026-0003",
    invoiceNumber: "INV-2026-0003",
    studentId: "std-003",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-07-15",
    dueDate: "2026-08-15",
    lines: [
      { id: "line-3-1", title: "B.Tech Semester 5 Academic Tuition Fee", categoryName: "Tuition Fee", quantity: 1, unitAmount: 55000, totalAmount: 55000 },
      { id: "line-3-2", title: "Advanced Computing Laboratory Levy", categoryName: "Laboratory Fee", quantity: 1, unitAmount: 15000, totalAmount: 15000 },
      { id: "line-3-3", title: "Semester 5 Examination & Evaluation", categoryName: "Examination Fee", quantity: 1, unitAmount: 3500, totalAmount: 3500 },
      { id: "line-3-4", title: "Library & Technical Periodicals Subscription", categoryName: "Library Fee", quantity: 1, unitAmount: 2500, totalAmount: 2500 },
    ],
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 76000,
    paidAmount: 40000,
    outstandingAmount: 36000,
    status: "PARTIALLY_PAID",
    feeAssignmentId: "assign-std-003",
    paymentIds: ["pay-2026-0003"],
    receiptIds: ["rec-2026-0003"],
    createdAt: "2026-07-15T09:00:00Z",
    updatedAt: "2026-08-10T16:15:00Z",
    history: [
      { id: "ih-3-1", action: "ISSUED", actor: "Billing Engine", timestamp: "2026-07-15T09:00:00Z" },
      { id: "ih-3-2", action: "PARTIAL_PAYMENT", actor: "Accounts Counter (Cash)", timestamp: "2026-08-10T16:15:00Z", notes: "₹40,000 received. Balance: ₹36,000." },
    ],
  },
  {
    id: "inv-2026-0004",
    invoiceNumber: "INV-2026-0004",
    studentId: "std-004",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    program: "B.Tech Electronics & Communication",
    department: "Electronics & Communication Engineering",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-07-15",
    dueDate: "2026-08-15",
    lines: [
      { id: "line-4-1", title: "Academic Tuition Fee", categoryName: "Tuition Fee", quantity: 1, unitAmount: 55000, totalAmount: 55000 },
      { id: "line-4-2", title: "VLSI & Embedded Systems Laboratory", categoryName: "Laboratory Fee", quantity: 1, unitAmount: 16000, totalAmount: 16000 },
      { id: "line-4-3", title: "Semester Examination Fee", categoryName: "Examination Fee", quantity: 1, unitAmount: 3500, totalAmount: 3500 },
      { id: "line-4-4", title: "Library & Technical Resources", categoryName: "Library Fee", quantity: 1, unitAmount: 2500, totalAmount: 2500 },
    ],
    grossAmount: 77000,
    scholarshipAmount: 40000,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 37000,
    paidAmount: 37000,
    outstandingAmount: 0,
    status: "PAID",
    feeAssignmentId: "assign-std-004",
    paymentIds: ["pay-2026-0004"],
    receiptIds: ["rec-2026-0004"],
    createdAt: "2026-07-15T09:00:00Z",
    updatedAt: "2026-08-12T10:00:00Z",
    history: [
      { id: "ih-4-1", action: "ISSUED", actor: "Billing Engine", timestamp: "2026-07-15T09:00:00Z" },
      { id: "ih-4-2", action: "PAID", actor: "Bank Transfer", timestamp: "2026-08-12T10:00:00Z" },
    ],
  },
  {
    id: "inv-2026-0005",
    invoiceNumber: "INV-2026-0005",
    studentId: "std-005",
    studentName: "Vikramaditya Rao",
    rollNumber: "24AI0301",
    program: "B.Tech AI & Data Science",
    department: "Computer Science & Engineering",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-07-15",
    dueDate: "2026-08-15",
    lines: [
      { id: "line-5-1", title: "B.Tech Semester 5 Academic Tuition Fee", categoryName: "Tuition Fee", quantity: 1, unitAmount: 55000, totalAmount: 55000 },
      { id: "line-5-2", title: "Advanced Computing Laboratory Levy", categoryName: "Laboratory Fee", quantity: 1, unitAmount: 15000, totalAmount: 15000 },
      { id: "line-5-3", title: "Semester 5 Examination & Evaluation", categoryName: "Examination Fee", quantity: 1, unitAmount: 3500, totalAmount: 3500 },
      { id: "line-5-4", title: "Library & Technical Periodicals Subscription", categoryName: "Library Fee", quantity: 1, unitAmount: 2500, totalAmount: 2500 },
    ],
    grossAmount: 76000,
    scholarshipAmount: 0,
    discountAmount: 5000,
    adjustmentAmount: 0,
    netPayable: 71000,
    paidAmount: 0,
    outstandingAmount: 71000,
    status: "OVERDUE",
    feeAssignmentId: "assign-std-005",
    paymentIds: [],
    receiptIds: [],
    createdAt: "2026-07-15T09:00:00Z",
    updatedAt: "2026-08-16T00:00:00Z",
    history: [
      { id: "ih-5-1", action: "ISSUED", actor: "Billing Engine", timestamp: "2026-07-15T09:00:00Z" },
      { id: "ih-5-2", action: "STATUS_CHANGED", actor: "Overdue Cron Service", timestamp: "2026-08-16T00:00:00Z", previousState: "ISSUED", newState: "OVERDUE", notes: "Due date passed with zero payments received." },
    ],
  },
  {
    id: "inv-2026-0006",
    invoiceNumber: "INV-2026-0006",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech Computer Science & Engineering",
    department: "Campus Operations & Facilities",
    semester: 5,
    academicYear: "2026-2027",
    issueDate: "2026-08-01",
    dueDate: "2026-08-25",
    lines: [
      { id: "line-6-1", title: "Hostel Room Rent (Double Occupancy)", categoryName: "Hostel Fee", quantity: 1, unitAmount: 25000, totalAmount: 25000 },
      { id: "line-6-2", title: "Central Dining & Mess Catering", categoryName: "Hostel Fee", quantity: 1, unitAmount: 20000, totalAmount: 20000 },
      { id: "line-6-3", title: "Hostel Maintenance & Amenities", categoryName: "Development Fee", quantity: 1, unitAmount: 5000, totalAmount: 5000 },
    ],
    grossAmount: 50000,
    scholarshipAmount: 0,
    discountAmount: 0,
    adjustmentAmount: 0,
    netPayable: 50000,
    paidAmount: 50000,
    outstandingAmount: 0,
    status: "PAID",
    paymentIds: ["pay-2026-0005"],
    receiptIds: ["rec-2026-0005"],
    createdAt: "2026-08-01T10:00:00Z",
    updatedAt: "2026-08-10T12:00:00Z",
    history: [
      { id: "ih-6-1", action: "ISSUED", actor: "Hostel Billing Unit", timestamp: "2026-08-01T10:00:00Z" },
      { id: "ih-6-2", action: "PAID", actor: "Aarav Patel", timestamp: "2026-08-10T12:00:00Z" },
    ],
  },
];

// ==========================================
// 6. Canonical Payments & Allocations
// ==========================================

export const MOCK_CANONICAL_PAYMENTS: Payment[] = [
  {
    id: "pay-2026-0001",
    transactionRef: "TXN-UPI-99881122",
    receiptNumber: "REC-2026-0001",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceId: "inv-2026-0001",
    invoiceNumber: "INV-2026-0001",
    amount: 76000,
    allocatedAmount: 76000,
    unallocatedAmount: 0,
    paymentMethod: "UPI",
    referenceNumber: "UPI/321876543210/PAYTM",
    paymentDate: "2026-08-02 11:30 AM",
    status: "SUCCESS",
    recordedBy: "Automated Payment Gateway",
    notes: "Full settlement for Semester 5 academic tuition.",
    allocations: [
      { id: "alloc-1", paymentId: "pay-2026-0001", invoiceId: "inv-2026-0001", invoiceNumber: "INV-2026-0001", allocatedAmount: 76000, allocatedAt: "2026-08-02T11:30:00Z" },
    ],
    history: [
      { id: "ph-1", action: "RECORDED", actor: "UPI Gateway", timestamp: "2026-08-02T11:30:00Z" },
    ],
  },
  {
    id: "pay-2026-0002",
    transactionRef: "TXN-NET-77443311",
    receiptNumber: "REC-2026-0002",
    studentId: "std-002",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    invoiceId: "inv-2026-0002",
    invoiceNumber: "INV-2026-0002",
    amount: 60800,
    allocatedAmount: 60800,
    unallocatedAmount: 0,
    paymentMethod: "BANK_TRANSFER",
    referenceNumber: "HDFC-N345229108",
    bankName: "HDFC Bank Ltd",
    paymentDate: "2026-08-05 02:45 PM",
    status: "SUCCESS",
    recordedBy: "Automated NetBanking Gateway",
    allocations: [
      { id: "alloc-2", paymentId: "pay-2026-0002", invoiceId: "inv-2026-0002", invoiceNumber: "INV-2026-0002", allocatedAmount: 60800, allocatedAt: "2026-08-05T14:20:00Z" },
    ],
    history: [
      { id: "ph-2", action: "RECORDED", actor: "NetBanking Gateway", timestamp: "2026-08-05T14:20:00Z" },
    ],
  },
  {
    id: "pay-2026-0003",
    transactionRef: "TXN-CSH-10293847",
    receiptNumber: "REC-2026-0003",
    studentId: "std-003",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    invoiceId: "inv-2026-0003",
    invoiceNumber: "INV-2026-0003",
    amount: 40000,
    allocatedAmount: 40000,
    unallocatedAmount: 0,
    paymentMethod: "CASH",
    referenceNumber: "RCPT-COUNTER-391",
    paymentDate: "2026-08-10 04:15 PM",
    status: "SUCCESS",
    recordedBy: "B. K. Sharma (Accounts Cashier)",
    notes: "Installment 1 paid at Main Block Cash Counter.",
    allocations: [
      { id: "alloc-3", paymentId: "pay-2026-0003", invoiceId: "inv-2026-0003", invoiceNumber: "INV-2026-0003", allocatedAmount: 40000, allocatedAt: "2026-08-10T16:15:00Z" },
    ],
    history: [
      { id: "ph-3", action: "RECORDED", actor: "Accounts Cashier", timestamp: "2026-08-10T16:15:00Z" },
    ],
  },
  {
    id: "pay-2026-0004",
    transactionRef: "TXN-NEFT-99112233",
    receiptNumber: "REC-2026-0004",
    studentId: "std-004",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    invoiceId: "inv-2026-0004",
    invoiceNumber: "INV-2026-0004",
    amount: 37000,
    allocatedAmount: 37000,
    unallocatedAmount: 0,
    paymentMethod: "BANK_TRANSFER",
    referenceNumber: "SBIN002938411",
    bankName: "State Bank of India",
    paymentDate: "2026-08-12 10:00 AM",
    status: "SUCCESS",
    recordedBy: "Accounts Officer",
    allocations: [
      { id: "alloc-4", paymentId: "pay-2026-0004", invoiceId: "inv-2026-0004", invoiceNumber: "INV-2026-0004", allocatedAmount: 37000, allocatedAt: "2026-08-12T10:00:00Z" },
    ],
    history: [
      { id: "ph-4", action: "RECORDED", actor: "Accounts Officer", timestamp: "2026-08-12T10:00:00Z" },
    ],
  },
  {
    id: "pay-2026-0005",
    transactionRef: "TXN-UPI-33445566",
    receiptNumber: "REC-2026-0005",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceId: "inv-2026-0006",
    invoiceNumber: "INV-2026-0006",
    amount: 50000,
    allocatedAmount: 50000,
    unallocatedAmount: 0,
    paymentMethod: "UPI",
    referenceNumber: "UPI/981273948123/GPAY",
    paymentDate: "2026-08-10 12:00 PM",
    status: "SUCCESS",
    recordedBy: "Hostel Finance Gateway",
    allocations: [
      { id: "alloc-5", paymentId: "pay-2026-0005", invoiceId: "inv-2026-0006", invoiceNumber: "INV-2026-0006", allocatedAmount: 50000, allocatedAt: "2026-08-10T12:00:00Z" },
    ],
    history: [
      { id: "ph-5", action: "RECORDED", actor: "Hostel Gateway", timestamp: "2026-08-10T12:00:00Z" },
    ],
  },
];

// ==========================================
// 7. Canonical Receipts
// ==========================================

export const MOCK_CANONICAL_RECEIPTS: Receipt[] = [
  {
    id: "rec-2026-0001",
    receiptNumber: "REC-2026-0001",
    paymentId: "pay-2026-0001",
    transactionRef: "TXN-UPI-99881122",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceId: "inv-2026-0001",
    invoiceNumber: "INV-2026-0001",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    amount: 76000,
    paymentMethod: "UPI",
    date: "2026-08-02 11:30 AM",
    status: "ISSUED",
    recordedBy: "Automated Payment Gateway",
    notes: "Official university receipt for Semester 5 tuition & laboratory fees.",
  },
  {
    id: "rec-2026-0002",
    receiptNumber: "REC-2026-0002",
    paymentId: "pay-2026-0002",
    transactionRef: "TXN-NET-77443311",
    studentId: "std-002",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    invoiceId: "inv-2026-0002",
    invoiceNumber: "INV-2026-0002",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    amount: 60800,
    paymentMethod: "BANK_TRANSFER",
    date: "2026-08-05 02:45 PM",
    status: "ISSUED",
    recordedBy: "Automated NetBanking Gateway",
  },
  {
    id: "rec-2026-0003",
    receiptNumber: "REC-2026-0003",
    paymentId: "pay-2026-0003",
    transactionRef: "TXN-CSH-10293847",
    studentId: "std-003",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    invoiceId: "inv-2026-0003",
    invoiceNumber: "INV-2026-0003",
    program: "B.Tech Computer Science & Engineering",
    department: "Computer Science & Engineering",
    amount: 40000,
    paymentMethod: "CASH",
    date: "2026-08-10 04:15 PM",
    status: "ISSUED",
    recordedBy: "B. K. Sharma (Accounts Cashier)",
    notes: "Part payment receipt (Counter 391). Balance due: ₹36,000.",
  },
  {
    id: "rec-2026-0004",
    receiptNumber: "REC-2026-0004",
    paymentId: "pay-2026-0004",
    transactionRef: "TXN-NEFT-99112233",
    studentId: "std-004",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    invoiceId: "inv-2026-0004",
    invoiceNumber: "INV-2026-0004",
    program: "B.Tech Electronics & Communication",
    department: "Electronics & Communication Engineering",
    amount: 37000,
    paymentMethod: "BANK_TRANSFER",
    date: "2026-08-12 10:00 AM",
    status: "ISSUED",
    recordedBy: "Accounts Officer",
  },
  {
    id: "rec-2026-0005",
    receiptNumber: "REC-2026-0005",
    paymentId: "pay-2026-0005",
    transactionRef: "TXN-UPI-33445566",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceId: "inv-2026-0006",
    invoiceNumber: "INV-2026-0006",
    program: "B.Tech Computer Science & Engineering",
    department: "Campus Operations & Facilities",
    amount: 50000,
    paymentMethod: "UPI",
    date: "2026-08-10 12:00 PM",
    status: "ISSUED",
    recordedBy: "Hostel Finance Gateway",
    notes: "Hostel double occupancy & mess catering fee settlement.",
  },
];

// ==========================================
// 8. Canonical Scholarships & Assistance
// ==========================================

export const MOCK_CANONICAL_SCHOLARSHIPS: Scholarship[] = [
  {
    id: "sch-merit-2026",
    code: "SCH-MERIT-20",
    name: "University Academic Merit Scholarship",
    type: "MERIT",
    description: "20% tuition concession for students securing top 5% SGPA/CGPA rank in previous semester.",
    discountType: "PERCENTAGE",
    value: 20,
    maxDiscountAmount: 25000,
    eligibilityCriteria: "CGPA >= 9.0 with zero course backlogs.",
    academicYear: "2026-2027",
    status: "APPROVED",
    totalRecipients: 14,
    approvedBy: "Academic Scholarship Council",
    approvedAt: "2026-06-20T10:00:00Z",
    createdAt: "2026-06-01T10:00:00Z",
    updatedAt: "2026-06-20T10:00:00Z",
  },
  {
    id: "sch-women-tech-2026",
    code: "SCH-WTECH-40K",
    name: "State Women in Engineering Fellowship",
    type: "GOVERNMENT",
    description: "Annual flat scholarship grant of ₹40,000 for women pursuing technical programs.",
    discountType: "FIXED",
    value: 40000,
    eligibilityCriteria: "Female candidate enrolled in B.Tech engineering disciplines.",
    academicYear: "2026-2027",
    status: "APPROVED",
    totalRecipients: 22,
    approvedBy: "State Higher Education Directorate",
    approvedAt: "2026-06-22T11:00:00Z",
    createdAt: "2026-06-05T09:00:00Z",
    updatedAt: "2026-06-22T11:00:00Z",
  },
  {
    id: "sch-sports-2026",
    code: "SCH-SPORTS-15K",
    name: "Inter-University Sports Excellence Award",
    type: "SPORTS",
    description: "Flat grant of ₹15,000 for university team representatives in AIU tournaments.",
    discountType: "FIXED",
    value: 15000,
    eligibilityCriteria: "University gold/silver medalists in zonal/national tournaments.",
    academicYear: "2026-2027",
    status: "APPROVED",
    totalRecipients: 8,
    approvedBy: "Physical Education Board",
    approvedAt: "2026-07-01T12:00:00Z",
    createdAt: "2026-06-15T10:00:00Z",
    updatedAt: "2026-07-01T12:00:00Z",
  },
  {
    id: "sch-need-2026",
    code: "SCH-NEED-50",
    name: "EWS & Need-Based Tuition Assistance Scheme",
    type: "NEED_BASED",
    description: "50% tuition waiver for students from families with annual income < ₹2.5 Lakhs.",
    discountType: "PERCENTAGE",
    value: 50,
    maxDiscountAmount: 35000,
    eligibilityCriteria: "Verified government income certificate with authentic revenue records.",
    academicYear: "2026-2027",
    status: "PENDING_APPROVAL",
    totalRecipients: 0,
    createdAt: "2026-08-01T10:00:00Z",
    updatedAt: "2026-08-10T11:00:00Z",
  },
];

export const MOCK_STUDENT_SCHOLARSHIPS: StudentScholarship[] = [
  {
    id: "ssch-001",
    scholarshipId: "sch-merit-2026",
    scholarshipName: "University Academic Merit Scholarship",
    studentId: "std-002",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    program: "B.Tech Computer Science & Engineering",
    originalFee: 76000,
    discountAmount: 15200,
    adjustedFee: 60800,
    status: "DISBURSED",
    academicYear: "2026-2027",
    grantedDate: "2026-07-10",
    remarks: "Top 1% rank in Semester 4 (SGPA 9.60).",
  },
  {
    id: "ssch-002",
    scholarshipId: "sch-women-tech-2026",
    scholarshipName: "State Women in Engineering Fellowship",
    studentId: "std-004",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    program: "B.Tech Electronics & Communication",
    originalFee: 77000,
    discountAmount: 40000,
    adjustedFee: 37000,
    status: "DISBURSED",
    academicYear: "2026-2027",
    grantedDate: "2026-07-12",
    remarks: "State government quota recipient.",
  },
];

// ==========================================
// 9. Canonical Adjustments
// ==========================================

export const MOCK_FINANCIAL_ADJUSTMENTS: FinancialAdjustment[] = [
  {
    id: "adj-2026-001",
    invoiceId: "inv-2026-0005",
    invoiceNumber: "INV-2026-0005",
    studentId: "std-005",
    studentName: "Vikramaditya Rao",
    type: "DISCOUNT",
    originalValue: 76000,
    adjustmentAmount: 5000,
    newValue: 71000,
    reason: "Early bird fee payment concession approved by Academic Dean.",
    createdBy: "Finance Officer (A. K. Menon)",
    createdAt: "2026-07-15T11:00:00Z",
    approvedBy: "Finance Dean",
  },
];

// ==========================================
// 10. Canonical Refunds
// ==========================================

export const MOCK_CANONICAL_REFUNDS: Refund[] = [
  {
    id: "ref-2026-0001",
    refundNumber: "REF-2026-0001",
    studentId: "std-001",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceId: "inv-2026-0006",
    invoiceNumber: "INV-2026-0006",
    paymentId: "pay-2026-0005",
    paymentRef: "TXN-UPI-33445566",
    originalPaymentAmount: 50000,
    requestedAmount: 5000,
    approvedAmount: 5000,
    reason: "Hostel security deposit excess collection reimbursement.",
    status: "PROCESSED",
    requestedBy: "Aarav Patel (Student)",
    requestedAt: "2026-08-15T10:00:00Z",
    reviewedBy: "Hostel Warden & Accounts Officer",
    reviewedAt: "2026-08-18T14:00:00Z",
    reviewerNotes: "Verified no hostel property damages. Sanctioned.",
    processedAt: "2026-08-20T11:30:00Z",
    timeline: [
      { id: "rh-1", action: "REQUESTED", actor: "Aarav Patel", timestamp: "2026-08-15T10:00:00Z", notes: "Refund application submitted." },
      { id: "rh-2", action: "APPROVED", actor: "Hostel Warden", timestamp: "2026-08-18T14:00:00Z", notes: "Inspection completed, approved ₹5,000." },
      { id: "rh-3", action: "PROCESSED", actor: "Accounts Bank Transfer", timestamp: "2026-08-20T11:30:00Z", notes: "Electronic credit processed to student bank account." },
    ],
  },
  {
    id: "ref-2026-0002",
    refundNumber: "REF-2026-0002",
    studentId: "std-003",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    invoiceId: "inv-2026-0003",
    invoiceNumber: "INV-2026-0003",
    paymentId: "pay-2026-0003",
    paymentRef: "TXN-CSH-10293847",
    originalPaymentAmount: 40000,
    requestedAmount: 3500,
    reason: "Duplicate examination fee charge refund request.",
    status: "UNDER_REVIEW",
    requestedBy: "Rohan Verghese",
    requestedAt: "2026-09-02T11:15:00Z",
    reviewerNotes: "Accounts clerk verifying ledger entries with exam cell.",
    timeline: [
      { id: "rh-2-1", action: "REQUESTED", actor: "Rohan Verghese", timestamp: "2026-09-02T11:15:00Z" },
      { id: "rh-2-2", action: "FLAGGED_FOR_AUDIT", actor: "Accounts Supervisor", timestamp: "2026-09-05T09:30:00Z", notes: "Cross-verifying with Examination Cell hall ticket rolls." },
    ],
  },
  {
    id: "ref-2026-0003",
    refundNumber: "REF-2026-0003",
    studentId: "std-005",
    studentName: "Vikramaditya Rao",
    rollNumber: "24AI0301",
    invoiceId: "inv-2026-0005",
    invoiceNumber: "INV-2026-0005",
    paymentId: "pay-none",
    paymentRef: "N/A",
    originalPaymentAmount: 0,
    requestedAmount: 10000,
    reason: "Requested refund on unbilled library caution deposit.",
    status: "REJECTED",
    requestedBy: "Vikramaditya Rao",
    requestedAt: "2026-09-10T15:00:00Z",
    reviewedBy: "Chief Accounts Officer",
    reviewedAt: "2026-09-12T16:00:00Z",
    reviewerNotes: "Caution deposit was never collected on this invoice. Ineligible.",
    timeline: [
      { id: "rh-3-1", action: "REQUESTED", actor: "Vikramaditya Rao", timestamp: "2026-09-10T15:00:00Z" },
      { id: "rh-3-2", action: "REJECTED", actor: "Chief Accounts Officer", timestamp: "2026-09-12T16:00:00Z", notes: "No underlying payment recorded." },
    ],
  },
];

// ==========================================
// 11. Canonical Operations Dashboard Summary
// ==========================================

export const MOCK_FINANCE_OPERATIONS_SUMMARY: FinanceDashboardSummary = {
  totalBilled: 405000, // 76k + 76k + 76k + 77k + 76k + 50k (minus discounts) = 380,800 net
  totalCollected: 263800, // 76k + 60.8k + 40k + 37k + 50k
  totalOutstanding: 107000, // 36k (Rohan) + 71k (Vikramaditya)
  totalOverdue: 71000, // Vikramaditya (INV-2026-0005)
  collectionRatePercent: 71.1,
  currentMonthCollection: 263800,
  pendingRefundsCount: 1,
  pendingRefundsAmount: 3500,
  unallocatedPaymentsCount: 0,
  unallocatedPaymentsAmount: 0,
  pendingScholarshipsCount: 1,
  agingBuckets: [
    { bucket: "CURRENT", label: "Current (Not Overdue)", amount: 36000, invoiceCount: 1, percentage: 34 },
    { bucket: "DAYS_1_30", label: "1–30 Days Overdue", amount: 0, invoiceCount: 0, percentage: 0 },
    { bucket: "DAYS_31_60", label: "31–60 Days Overdue", amount: 71000, invoiceCount: 1, percentage: 66 },
    { bucket: "DAYS_61_90", label: "61–90 Days Overdue", amount: 0, invoiceCount: 0, percentage: 0 },
    { bucket: "DAYS_90_PLUS", label: "90+ Days Overdue", amount: 0, invoiceCount: 0, percentage: 0 },
  ],
  collectionTrends: [
    { month: "Jun 2026", billed: 0, collected: 0, rate: 0 },
    { month: "Jul 2026", billed: 355000, collected: 0, rate: 0 },
    { month: "Aug 2026", billed: 50000, collected: 263800, rate: 65.1 },
    { month: "Sep 2026", billed: 0, collected: 0, rate: 65.1 },
    { month: "Oct 2026", billed: 0, collected: 0, rate: 65.1 },
  ],
  programOutstandings: [
    { program: "B.Tech Computer Science & Engineering", department: "Computer Science & Engineering", billed: 228000, collected: 176800, outstanding: 36000, studentCount: 3 },
    { program: "B.Tech Electronics & Communication", department: "Electronics & Communication Engineering", billed: 77000, collected: 37000, outstanding: 0, studentCount: 1 },
    { program: "B.Tech AI & Data Science", department: "Artificial Intelligence & Data Science", billed: 76000, collected: 0, outstanding: 71000, studentCount: 1 },
  ],
  recentActivities: [
    { id: "act-1", type: "PAYMENT_RECORDED", title: "Hostel Fee Payment Recorded", description: "₹50,000 received via UPI from Aarav Patel (24CSE0101)", amount: 50000, timestamp: "2026-08-10 12:00 PM", entityId: "pay-2026-0005", href: "/app/finance/payments/pay-2026-0005" },
    { id: "act-2", type: "PAYMENT_RECORDED", title: "Partial Cash Fee Received", description: "₹40,000 counter installment recorded for Rohan Verghese (24CSE0103)", amount: 40000, timestamp: "2026-08-10 04:15 PM", entityId: "pay-2026-0003", href: "/app/finance/payments/pay-2026-0003" },
    { id: "act-3", type: "RECEIPT_ISSUED", title: "Electronic Receipt REC-2026-0002 Generated", description: "Receipt issued for Priya Sundaram (Net Banking ₹60,800)", amount: 60800, timestamp: "2026-08-05 02:45 PM", entityId: "rec-2026-0002", href: "/app/finance/receipts/rec-2026-0002" },
    { id: "act-4", type: "SCHOLARSHIP_APPROVED", title: "Academic Merit Concession Approved", description: "20% waiver (₹15,200) granted to Priya Sundaram (24CSE0102)", amount: 15200, timestamp: "2026-07-10 10:00 AM", entityId: "sch-merit-2026", href: "/app/finance/scholarships/sch-merit-2026" },
    { id: "act-5", type: "REFUND_APPROVED", title: "Hostel Caution Refund Approved", description: "₹5,000 refund processed for Aarav Patel (24CSE0101)", amount: 5000, timestamp: "2026-08-20 11:30 AM", entityId: "ref-2026-0001", href: "/app/finance/refunds/ref-2026-0001" },
  ],
  operationalQueues: {
    pendingPaymentsCount: 0,
    overdueInvoicesCount: 1,
    refundRequestsCount: 1,
    scholarshipApprovalsCount: 1,
    unallocatedPaymentsCount: 0,
    recentlyIssuedReceiptsCount: 5,
  },
};

// ==========================================
// Legacy Array Aliases (Maintains Zero Breaks)
// ==========================================

export const MOCK_FEE_STRUCTURES: FeeStructureItem[] = MOCK_CANONICAL_FEE_STRUCTURES.map((fs) => ({
  id: fs.id,
  name: fs.name,
  program: fs.program,
  academicYear: fs.academicYear,
  totalAnnualFee: fs.grossTotal,
  components: fs.components.map((c) => ({
    title: c.title,
    amount: c.amount,
    mandatory: c.isMandatory,
  })),
  status: fs.status === "ACTIVE" ? "ACTIVE" : fs.status === "DRAFT" ? "DRAFT" : "ARCHIVED",
}));

export const MOCK_INVOICES: InvoiceItem[] = MOCK_CANONICAL_INVOICES.map((inv) => ({
  id: inv.id,
  invoiceNumber: inv.invoiceNumber,
  studentId: inv.studentId,
  studentName: inv.studentName,
  rollNumber: inv.rollNumber,
  program: inv.program,
  dueDate: inv.dueDate,
  issueDate: inv.issueDate,
  totalAmount: inv.netPayable,
  paidAmount: inv.paidAmount,
  balanceAmount: inv.outstandingAmount,
  status: inv.status,
}));

export const MOCK_PAYMENTS: PaymentTransactionItem[] = MOCK_CANONICAL_PAYMENTS.map((p) => ({
  id: p.id,
  transactionRef: p.transactionRef,
  receiptNumber: p.receiptNumber,
  studentName: p.studentName,
  rollNumber: p.rollNumber,
  invoiceNumber: p.invoiceNumber,
  amount: p.amount,
  paymentMode: p.paymentMethod === "UPI" ? "UPI" : p.paymentMethod === "CASH" ? "CASH_COUNTER" : "NET_BANKING",
  paymentDate: p.paymentDate,
  status: p.status,
}));

export const MOCK_SCHOLARSHIPS: ScholarshipItem[] = MOCK_STUDENT_SCHOLARSHIPS.map((s) => ({
  id: s.id,
  studentName: s.studentName,
  rollNumber: s.rollNumber,
  scholarshipScheme: s.scholarshipName,
  sanctionAmount: s.discountAmount,
  disbursedAmount: s.discountAmount,
  academicYear: s.academicYear,
  status: s.status === "DISBURSED" ? "DISBURSED" : "APPROVED",
}));
