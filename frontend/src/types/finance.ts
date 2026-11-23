/**
 * CampusOS Finance, Fees & Billing Domain Types
 * Enterprise-grade definitions for Fee Structures, Invoices, Payments, Receipts,
 * Scholarships, Refunds, Allocations, Aging Buckets, and Audit Trails.
 */

export type Currency = "INR";

export interface AuditEntry {
  id: string;
  action: string;
  actor: string;
  actorRole?: string;
  timestamp: string;
  previousState?: string;
  newState?: string;
  notes?: string;
}

// ==========================================
// 1. Fee Categories & Items
// ==========================================

export type FeeCategoryType =
  | "TUITION"
  | "EXAMINATION"
  | "LABORATORY"
  | "LIBRARY"
  | "TRANSPORT"
  | "HOSTEL"
  | "DEVELOPMENT"
  | "SPORTS"
  | "OTHER";

export type FeeCategoryStatus = "ACTIVE" | "INACTIVE";

export interface FeeCategory {
  id: string;
  code: string;
  name: string;
  description: string;
  type: FeeCategoryType;
  isTaxable: boolean;
  isRefundable: boolean;
  status: FeeCategoryStatus;
  createdAt: string;
  updatedAt: string;
}

export interface FeeItem {
  id: string;
  categoryId: string;
  categoryName: string;
  code: string;
  name: string;
  description?: string;
  program: string;
  academicYear: string;
  semester: number;
  amount: number;
  isOptional: boolean;
  isRefundable: boolean;
  isActive: boolean;
  createdAt: string;
}

// ==========================================
// 2. Fee Structures & Components
// ==========================================

export type FeeStructureStatus =
  "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "ACTIVE" | "RETIRED";

export interface FeeStructureComponent {
  id: string;
  feeItemId?: string;
  title: string;
  categoryName: string;
  amount: number;
  isMandatory: boolean;
  description?: string;
}

export interface FeeStructure {
  id: string;
  code: string;
  name: string;
  program: string;
  department: string;
  academicYear: string;
  semester: number;
  components: FeeStructureComponent[];
  grossTotal: number;
  status: FeeStructureStatus;
  effectiveDate: string;
  approvedBy?: string;
  approvedAt?: string;
  notes?: string;
  totalStudentsAssigned?: number;
  createdAt: string;
  updatedAt: string;
  history: AuditEntry[];
}

// ==========================================
// 3. Student Fee Assignments
// ==========================================

export type FeeAssignmentStatus =
  "ACTIVE" | "EXEMPTED" | "ADJUSTED" | "CANCELLED";

export interface StudentFeeAssignment {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  academicYear: string;
  semester: number;
  feeStructureId: string;
  feeStructureName: string;
  grossAmount: number;
  scholarshipAmount: number;
  discountAmount: number;
  adjustmentAmount: number;
  netPayable: number;
  paidAmount: number;
  outstandingAmount: number;
  status: FeeAssignmentStatus;
  assignedDate: string;
  invoiceId?: string;
  notes?: string;
}

// ==========================================
// 4. Invoices & Line Items
// ==========================================

export type InvoiceStatus =
  "DRAFT" | "ISSUED" | "PARTIALLY_PAID" | "PAID" | "OVERDUE" | "CANCELLED";

export interface InvoiceLine {
  id: string;
  feeItemId?: string;
  title: string;
  categoryName: string;
  quantity: number;
  unitAmount: number;
  totalAmount: number;
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  semester: number;
  academicYear: string;
  issueDate: string;
  dueDate: string;
  lines: InvoiceLine[];
  grossAmount: number;
  scholarshipAmount: number;
  discountAmount: number;
  adjustmentAmount: number;
  netPayable: number;
  paidAmount: number;
  outstandingAmount: number;
  status: InvoiceStatus;
  feeAssignmentId?: string;
  paymentIds: string[];
  receiptIds: string[];
  cancelledReason?: string;
  cancelledBy?: string;
  cancelledAt?: string;
  createdAt: string;
  updatedAt: string;
  history: AuditEntry[];
}

// ==========================================
// 5. Payments & Allocations
// ==========================================

export type PaymentMethod =
  "CASH" | "UPI" | "CARD" | "BANK_TRANSFER" | "CHEQUE" | "ONLINE" | "OTHER";

export type PaymentStatus = "PENDING" | "SUCCESS" | "FAILED" | "REVERSED";

export interface PaymentAllocation {
  id: string;
  paymentId: string;
  invoiceId: string;
  invoiceNumber: string;
  allocatedAmount: number;
  allocatedAt: string;
}

export interface Payment {
  id: string;
  transactionRef: string;
  receiptNumber: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  invoiceId: string;
  invoiceNumber: string;
  amount: number;
  allocatedAmount: number;
  unallocatedAmount: number;
  paymentMethod: PaymentMethod;
  referenceNumber: string;
  bankName?: string;
  chequeNumber?: string;
  paymentDate: string;
  status: PaymentStatus;
  recordedBy: string;
  notes?: string;
  allocations: PaymentAllocation[];
  history: AuditEntry[];
}

// ==========================================
// 6. Receipts
// ==========================================

export interface Receipt {
  id: string;
  receiptNumber: string;
  paymentId: string;
  transactionRef: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  invoiceId: string;
  invoiceNumber: string;
  program: string;
  department: string;
  amount: number;
  paymentMethod: PaymentMethod;
  date: string;
  status: "ISSUED" | "CANCELLED";
  recordedBy: string;
  notes?: string;
}

// ==========================================
// 7. Scholarships & Financial Assistance
// ==========================================

export type ScholarshipType =
  | "MERIT"
  | "NEED_BASED"
  | "SPORTS"
  | "GOVERNMENT"
  | "INSTITUTIONAL"
  | "SPECIAL_WAIVER";

export type ScholarshipStatus =
  "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "EXPIRED";

export interface Scholarship {
  id: string;
  code: string;
  name: string;
  type: ScholarshipType;
  description: string;
  discountType: "PERCENTAGE" | "FIXED";
  value: number; // e.g. 20 for 20% or 25000 for ₹25,000
  maxDiscountAmount?: number;
  eligibilityCriteria: string;
  academicYear: string;
  status: ScholarshipStatus;
  totalRecipients: number;
  approvedBy?: string;
  approvedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StudentScholarship {
  id: string;
  scholarshipId: string;
  scholarshipName: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  originalFee: number;
  discountAmount: number;
  adjustedFee: number;
  status: "APPROVED" | "DISBURSED" | "REVOKED";
  academicYear: string;
  grantedDate: string;
  remarks?: string;
}

// ==========================================
// 8. Financial Adjustments
// ==========================================

export type AdjustmentType =
  "DISCOUNT" | "WAIVER" | "CREDIT" | "DEBIT" | "CORRECTION";

export interface FinancialAdjustment {
  id: string;
  invoiceId: string;
  invoiceNumber: string;
  studentId: string;
  studentName: string;
  type: AdjustmentType;
  originalValue: number;
  adjustmentAmount: number;
  newValue: number;
  reason: string;
  createdBy: string;
  createdAt: string;
  approvedBy?: string;
}

// ==========================================
// 9. Refunds
// ==========================================

export type RefundStatus =
  "REQUESTED" | "UNDER_REVIEW" | "APPROVED" | "PROCESSED" | "REJECTED";

export interface Refund {
  id: string;
  refundNumber: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  invoiceId: string;
  invoiceNumber: string;
  paymentId: string;
  paymentRef: string;
  originalPaymentAmount: number;
  requestedAmount: number;
  approvedAmount?: number;
  reason: string;
  status: RefundStatus;
  requestedBy: string;
  requestedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewerNotes?: string;
  processedAt?: string;
  timeline: AuditEntry[];
}

// ==========================================
// 10. Aging, Reports & Dashboard Summaries
// ==========================================

export type AgingBucket =
  "CURRENT" | "DAYS_1_30" | "DAYS_31_60" | "DAYS_61_90" | "DAYS_90_PLUS";

export interface AgingBucketSummary {
  bucket: AgingBucket;
  label: string;
  amount: number;
  invoiceCount: number;
  percentage: number;
}

export interface CollectionTrendPoint {
  month: string;
  billed: number;
  collected: number;
  rate: number;
}

export interface ProgramOutstandingSummary {
  program: string;
  department: string;
  billed: number;
  collected: number;
  outstanding: number;
  studentCount: number;
}

export interface RecentFinanceActivity {
  id: string;
  type:
    | "INVOICE_GENERATED"
    | "PAYMENT_RECORDED"
    | "RECEIPT_ISSUED"
    | "SCHOLARSHIP_APPROVED"
    | "REFUND_REQUESTED"
    | "REFUND_APPROVED"
    | "INVOICE_ADJUSTED";
  title: string;
  description: string;
  amount?: number;
  timestamp: string;
  entityId: string;
  href: string;
}

export interface FinanceDashboardSummary {
  totalBilled: number;
  totalCollected: number;
  totalOutstanding: number;
  totalOverdue: number;
  collectionRatePercent: number;
  currentMonthCollection: number;
  pendingRefundsCount: number;
  pendingRefundsAmount: number;
  unallocatedPaymentsCount: number;
  unallocatedPaymentsAmount: number;
  pendingScholarshipsCount: number;
  agingBuckets: AgingBucketSummary[];
  collectionTrends: CollectionTrendPoint[];
  programOutstandings: ProgramOutstandingSummary[];
  recentActivities: RecentFinanceActivity[];
  operationalQueues: {
    pendingPaymentsCount: number;
    overdueInvoicesCount: number;
    refundRequestsCount: number;
    scholarshipApprovalsCount: number;
    unallocatedPaymentsCount: number;
    recentlyIssuedReceiptsCount: number;
  };
}

export type ReportType =
  "COLLECTION" | "OUTSTANDING" | "AGING" | "PAYMENT_METHOD" | "SCHOLARSHIP";

export interface FinanceReportFilter {
  reportType: ReportType;
  startDate?: string;
  endDate?: string;
  program?: string;
  department?: string;
  semester?: number;
  academicYear?: string;
  paymentMethod?: PaymentMethod;
}
