/**
 * CampusOS Finance, Fees & Billing Service Layer
 * In-memory reactive mock adapter implementing all future FastAPI contracts:
 * Fee Categories, Structures, Student Assignments, Invoices, Payments,
 * Allocations, Receipts, Scholarships, Adjustments, Refunds, and Reports.
 */

import { ApiResponse } from "@campusos/types";
import {
  FeeCategory,
  FeeItem,
  FeeStructure,
  FeeStructureStatus,
  StudentFeeAssignment,
  Invoice,
  InvoiceStatus,
  Payment,
  PaymentMethod,
  Receipt,
  Scholarship,
  StudentScholarship,
  FinancialAdjustment,
  Refund,
  RefundStatus,
  FinanceDashboardSummary,
  FinanceReportFilter,
  AuditEntry,
} from "@/types/finance";
import {
  FeeStructureItem,
  InvoiceItem,
  PaymentTransactionItem,
  ScholarshipItem,
  MOCK_FEE_CATEGORIES,
  MOCK_FEE_ITEMS,
  MOCK_CANONICAL_FEE_STRUCTURES,
  MOCK_STUDENT_FEE_ASSIGNMENTS,
  MOCK_CANONICAL_INVOICES,
  MOCK_CANONICAL_PAYMENTS,
  MOCK_CANONICAL_RECEIPTS,
  MOCK_CANONICAL_SCHOLARSHIPS,
  MOCK_STUDENT_SCHOLARSHIPS,
  MOCK_FINANCIAL_ADJUSTMENTS,
  MOCK_CANONICAL_REFUNDS,
  MOCK_FINANCE_OPERATIONS_SUMMARY,
  MOCK_FEE_STRUCTURES,
  MOCK_INVOICES,
  MOCK_PAYMENTS,
  MOCK_SCHOLARSHIPS,
} from "@/mocks/finance.mock";
import {
  addMoney,
  subtractMoney,
  calculateInvoiceGross,
  calculateNetPayable,
  calculateOutstanding,
  calculateOverdueDays,
  calculateAgingBucket,
  calculateScholarshipImpact,
  compileAgingBuckets,
} from "./financial-calculator";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export interface StudentFeeStatement {
  student_id: string;
  student_name: string;
  roll_number: string;
  program: string;
  academic_year: string;
  total_billed: number;
  total_paid: number;
  total_due: number;
  invoices: Invoice[];
  receipts: Receipt[];
}

export interface InvoiceFilters {
  status?: InvoiceStatus | "ALL";
  program?: string;
  semester?: number;
  academicYear?: string;
  search?: string;
  studentId?: string;
}

export interface PaymentFilters {
  status?: string;
  paymentMethod?: PaymentMethod | "ALL";
  search?: string;
  studentId?: string;
}

export interface FeeStructureFilters {
  status?: FeeStructureStatus | "ALL";
  program?: string;
  academicYear?: string;
  semester?: number;
  search?: string;
}

class FinanceService {
  // In-memory canonical collections
  private categories: FeeCategory[] = [...MOCK_FEE_CATEGORIES];
  private feeItems: FeeItem[] = [...MOCK_FEE_ITEMS];
  private feeStructures: FeeStructure[] = [...MOCK_CANONICAL_FEE_STRUCTURES];
  private assignments: StudentFeeAssignment[] = [
    ...MOCK_STUDENT_FEE_ASSIGNMENTS,
  ];
  private invoices: Invoice[] = [...MOCK_CANONICAL_INVOICES];
  private payments: Payment[] = [...MOCK_CANONICAL_PAYMENTS];
  private receipts: Receipt[] = [...MOCK_CANONICAL_RECEIPTS];
  private scholarships: Scholarship[] = [...MOCK_CANONICAL_SCHOLARSHIPS];
  private studentScholarships: StudentScholarship[] = [
    ...MOCK_STUDENT_SCHOLARSHIPS,
  ];
  private adjustments: FinancialAdjustment[] = [...MOCK_FINANCIAL_ADJUSTMENTS];
  private refunds: Refund[] = [...MOCK_CANONICAL_REFUNDS];

  // ==========================================
  // 1. Dashboard & Telemetry
  // ==========================================

  async getDashboardSummary(): Promise<ApiResponse<FinanceDashboardSummary>> {
    await new Promise((r) => setTimeout(r, 40));

    // Dynamic aggregation over live state
    const totalBilled = this.invoices.reduce(
      (acc, i) => addMoney(acc, i.grossAmount),
      0,
    );
    const totalCollected = this.payments
      .filter((p) => p.status === "SUCCESS")
      .reduce((acc, p) => addMoney(acc, p.amount), 0);
    const totalOutstanding = this.invoices.reduce(
      (acc, i) => addMoney(acc, i.outstandingAmount),
      0,
    );

    const overdueInvoices = this.invoices.filter(
      (i) =>
        i.status === "OVERDUE" ||
        (i.outstandingAmount > 0 && calculateOverdueDays(i.dueDate) > 0),
    );
    const totalOverdue = overdueInvoices.reduce(
      (acc, i) => addMoney(acc, i.outstandingAmount),
      0,
    );
    const pendingRefunds = this.refunds.filter(
      (r) => r.status === "REQUESTED" || r.status === "UNDER_REVIEW",
    );

    const aging = compileAgingBuckets(this.invoices);

    const summary: FinanceDashboardSummary = {
      ...MOCK_FINANCE_OPERATIONS_SUMMARY,
      totalBilled,
      totalCollected,
      totalOutstanding,
      totalOverdue,
      collectionRatePercent:
        totalBilled > 0
          ? Math.round((totalCollected / totalBilled) * 1000) / 10
          : 0,
      pendingRefundsCount: pendingRefunds.length,
      pendingRefundsAmount: pendingRefunds.reduce(
        (acc, r) => addMoney(acc, r.requestedAmount),
        0,
      ),
      agingBuckets: aging,
      operationalQueues: {
        pendingPaymentsCount: this.payments.filter(
          (p) => p.status === "PENDING",
        ).length,
        overdueInvoicesCount: overdueInvoices.length,
        refundRequestsCount: pendingRefunds.length,
        scholarshipApprovalsCount: this.scholarships.filter(
          (s) => s.status === "PENDING_APPROVAL",
        ).length,
        unallocatedPaymentsCount: this.payments.filter(
          (p) => p.unallocatedAmount > 0,
        ).length,
        recentlyIssuedReceiptsCount: this.receipts.length,
      },
    };

    return { success: true, data: summary };
  }

  // Legacy dashboard support
  async getDashboard(): Promise<
    ApiResponse<{
      total_billed: number;
      total_collected: number;
      total_outstanding: number;
      collection_rate_percent: number;
      total_invoices_count: number;
      paid_invoices_count: number;
      pending_invoices_count: number;
      overdue_invoices_count: number;
      today_collections: number;
    }>
  > {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        total_billed: 405000,
        total_collected: 263800,
        total_outstanding: 107000,
        collection_rate_percent: 71.1,
        total_invoices_count: this.invoices.length,
        paid_invoices_count: this.invoices.filter((i) => i.status === "PAID")
          .length,
        pending_invoices_count: this.invoices.filter(
          (i) => i.status === "ISSUED" || i.status === "PARTIALLY_PAID",
        ).length,
        overdue_invoices_count: this.invoices.filter(
          (i) => i.status === "OVERDUE",
        ).length,
        today_collections: 50000,
      },
    };
  }

  // ==========================================
  // 2. Fee Categories
  // ==========================================

  async getFeeCategories(): Promise<ApiResponse<FeeCategory[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: [...this.categories] };
  }

  async getFeeCategoryById(id: string): Promise<ApiResponse<FeeCategory>> {
    await new Promise((r) => setTimeout(r, 30));
    const cat = this.categories.find((c) => c.id === id);
    if (!cat) throw new Error(`Fee Category '${id}' not found.`);
    return { success: true, data: cat };
  }

  async createFeeCategory(
    data: Partial<FeeCategory>,
  ): Promise<ApiResponse<FeeCategory>> {
    await new Promise((r) => setTimeout(r, 60));
    const newCat: FeeCategory = {
      id: `cat-${Date.now()}`,
      code: data.code || `CAT-${Date.now().toString().slice(-4)}`,
      name: data.name || "Institutional Fee",
      description:
        data.description || "General academic or facilities fee category.",
      type: data.type || "OTHER",
      isTaxable: Boolean(data.isTaxable),
      isRefundable: Boolean(data.isRefundable),
      status: "ACTIVE",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.categories.push(newCat);
    return { success: true, data: newCat };
  }

  async updateFeeCategory(
    id: string,
    updates: Partial<FeeCategory>,
  ): Promise<ApiResponse<FeeCategory>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.categories.findIndex((c) => c.id === id);
    if (idx === -1) throw new Error(`Fee Category '${id}' not found.`);
    this.categories[idx] = {
      ...this.categories[idx],
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    return { success: true, data: this.categories[idx] };
  }

  async toggleCategoryStatus(id: string): Promise<ApiResponse<FeeCategory>> {
    const cat = this.categories.find((c) => c.id === id);
    if (!cat) throw new Error(`Category '${id}' not found.`);
    cat.status = cat.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    cat.updatedAt = new Date().toISOString();
    return { success: true, data: cat };
  }

  // ==========================================
  // 3. Fee Items
  // ==========================================

  async getFeeItems(categoryId?: string): Promise<ApiResponse<FeeItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.feeItems];
    if (categoryId) {
      items = items.filter((item) => item.categoryId === categoryId);
    }
    return { success: true, data: items };
  }

  async createFeeItem(data: Partial<FeeItem>): Promise<ApiResponse<FeeItem>> {
    await new Promise((r) => setTimeout(r, 50));
    const newItem: FeeItem = {
      id: `item-${Date.now()}`,
      categoryId: data.categoryId || "cat-tuition",
      categoryName: data.categoryName || "Tuition Fee",
      code: data.code || `ITEM-${Date.now().toString().slice(-4)}`,
      name: data.name || "Semester Academic Fee",
      description: data.description,
      program: data.program || "B.Tech Computer Science & Engineering",
      academicYear: data.academicYear || "2026-2027",
      semester: data.semester || 5,
      amount: data.amount || 25000,
      isOptional: Boolean(data.isOptional),
      isRefundable: Boolean(data.isRefundable),
      isActive: true,
      createdAt: new Date().toISOString(),
    };
    this.feeItems.push(newItem);
    return { success: true, data: newItem };
  }

  // ==========================================
  // 4. Fee Structures & Lifecycle
  // ==========================================

  async getFeeStructures(
    filters?: FeeStructureFilters,
  ): Promise<ApiResponse<FeeStructure[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.feeStructures];

    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((fs) => fs.status === filters.status);
    }
    if (filters?.program) {
      items = items.filter((fs) =>
        fs.program.toLowerCase().includes(filters.program!.toLowerCase()),
      );
    }
    if (filters?.semester) {
      items = items.filter((fs) => fs.semester === filters.semester);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (fs) =>
          fs.name.toLowerCase().includes(q) ||
          fs.code.toLowerCase().includes(q) ||
          fs.program.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getFeeStructureById(id: string): Promise<ApiResponse<FeeStructure>> {
    await new Promise((r) => setTimeout(r, 30));
    const found = this.feeStructures.find((fs) => fs.id === id);
    if (!found) throw new Error(`Fee Structure '${id}' not found.`);
    return { success: true, data: found };
  }

  async createFeeStructure(
    data: Partial<FeeStructure>,
  ): Promise<ApiResponse<FeeStructure>> {
    await new Promise((r) => setTimeout(r, 80));

    const components = data.components || [
      {
        id: "c-1",
        title: "Academic Tuition",
        categoryName: "Tuition Fee",
        amount: 50000,
        isMandatory: true,
      },
      {
        id: "c-2",
        title: "Computing Lab",
        categoryName: "Laboratory Fee",
        amount: 15000,
        isMandatory: true,
      },
    ];
    const grossTotal = components.reduce(
      (acc, c) => addMoney(acc, c.amount),
      0,
    );

    const newFs: FeeStructure = {
      id: `fs-${Date.now()}`,
      code: data.code || `FS-${Date.now().toString().slice(-4)}`,
      name: data.name || "Semester Fee Schedule",
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      academicYear: data.academicYear || "2026-2027",
      semester: data.semester || 5,
      components,
      grossTotal,
      status: "DRAFT",
      effectiveDate:
        data.effectiveDate || new Date().toISOString().split("T")[0],
      notes:
        data.notes || "Draft fee structure created for departmental review.",
      totalStudentsAssigned: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      history: [
        {
          id: `h-${Date.now()}`,
          action: "DRAFT_CREATED",
          actor: "Finance Officer",
          timestamp: new Date().toISOString(),
          notes: "Initial draft configured with components.",
        },
      ],
    };

    this.feeStructures.unshift(newFs);
    return { success: true, data: newFs };
  }

  async submitFeeStructureForApproval(
    id: string,
  ): Promise<ApiResponse<FeeStructure>> {
    const fs = this.feeStructures.find((f) => f.id === id);
    if (!fs) throw new Error(`Fee Structure '${id}' not found.`);
    fs.status = "PENDING_APPROVAL";
    fs.updatedAt = new Date().toISOString();
    fs.history.push({
      id: `h-${Date.now()}`,
      action: "SUBMITTED_FOR_APPROVAL",
      actor: "Finance Officer",
      timestamp: new Date().toISOString(),
      notes: "Submitted for Academic Council & Finance Committee review.",
    });
    return { success: true, data: fs };
  }

  async approveFeeStructure(
    id: string,
    approvedBy = "Academic Senate",
  ): Promise<ApiResponse<FeeStructure>> {
    const fs = this.feeStructures.find((f) => f.id === id);
    if (!fs) throw new Error(`Fee Structure '${id}' not found.`);
    fs.status = "APPROVED";
    fs.approvedBy = approvedBy;
    fs.approvedAt = new Date().toISOString();
    fs.updatedAt = new Date().toISOString();
    fs.history.push({
      id: `h-${Date.now()}`,
      action: "APPROVED",
      actor: approvedBy,
      timestamp: new Date().toISOString(),
      notes: "Formally approved by council without revision.",
    });
    return { success: true, data: fs };
  }

  async activateFeeStructure(id: string): Promise<ApiResponse<FeeStructure>> {
    const fs = this.feeStructures.find((f) => f.id === id);
    if (!fs) throw new Error(`Fee Structure '${id}' not found.`);
    fs.status = "ACTIVE";
    fs.updatedAt = new Date().toISOString();
    fs.history.push({
      id: `h-${Date.now()}`,
      action: "ACTIVATED",
      actor: "Chief Finance Officer",
      timestamp: new Date().toISOString(),
      notes: "Activated for student fee assignment and invoice generation.",
    });
    return { success: true, data: fs };
  }

  async retireFeeStructure(id: string): Promise<ApiResponse<FeeStructure>> {
    const fs = this.feeStructures.find((f) => f.id === id);
    if (!fs) throw new Error(`Fee Structure '${id}' not found.`);
    fs.status = "RETIRED";
    fs.updatedAt = new Date().toISOString();
    fs.history.push({
      id: `h-${Date.now()}`,
      action: "RETIRED",
      actor: "Chief Finance Officer",
      timestamp: new Date().toISOString(),
      notes: "Structure retired from new student assignments.",
    });
    return { success: true, data: fs };
  }

  // ==========================================
  // 5. Student Fee Assignments
  // ==========================================

  async getFeeAssignments(): Promise<ApiResponse<StudentFeeAssignment[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...this.assignments] };
  }

  async createFeeAssignment(data: {
    studentId: string;
    feeStructureId: string;
    discountAmount?: number;
    scholarshipAmount?: number;
    notes?: string;
  }): Promise<ApiResponse<StudentFeeAssignment>> {
    await new Promise((r) => setTimeout(r, 80));

    const student = MOCK_STUDENTS.find((s) => s.id === data.studentId);
    const fs = this.feeStructures.find((f) => f.id === data.feeStructureId);

    if (!student) throw new Error(`Student '${data.studentId}' not found.`);
    if (!fs)
      throw new Error(`Fee Structure '${data.feeStructureId}' not found.`);

    const grossAmount = fs.grossTotal;
    const scholarshipAmount = data.scholarshipAmount || 0;
    const discountAmount = data.discountAmount || 0;
    const netPayable = calculateNetPayable(
      grossAmount,
      scholarshipAmount,
      discountAmount,
      0,
    );

    const newAssign: StudentFeeAssignment = {
      id: `assign-${Date.now()}`,
      studentId: student.id,
      studentName: `${student.firstName} ${student.lastName}`,
      rollNumber: student.rollNumber,
      program: student.program?.name || fs.program,
      department: student.program?.department || fs.department,
      academicYear: fs.academicYear,
      semester: fs.semester,
      feeStructureId: fs.id,
      feeStructureName: fs.name,
      grossAmount,
      scholarshipAmount,
      discountAmount,
      adjustmentAmount: 0,
      netPayable,
      paidAmount: 0,
      outstandingAmount: netPayable,
      status: "ACTIVE",
      assignedDate: new Date().toISOString().split("T")[0],
      notes: data.notes,
    };

    this.assignments.unshift(newAssign);

    // Increment assigned count on structure
    fs.totalStudentsAssigned = (fs.totalStudentsAssigned || 0) + 1;

    // Automatically generate draft/issued invoice
    const invRes = await this.createInvoice({
      studentId: student.id,
      studentName: newAssign.studentName,
      rollNumber: student.rollNumber,
      program: newAssign.program,
      department: newAssign.department,
      semester: newAssign.semester,
      academicYear: newAssign.academicYear,
      feeAssignmentId: newAssign.id,
      lines: fs.components.map((c) => ({
        id: `line-${Date.now()}-${c.id}`,
        title: c.title,
        categoryName: c.categoryName,
        quantity: 1,
        unitAmount: c.amount,
        totalAmount: c.amount,
      })),
      grossAmount,
      scholarshipAmount,
      discountAmount,
      adjustmentAmount: 0,
      netPayable,
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
    });

    newAssign.invoiceId = invRes.data.id;
    return { success: true, data: newAssign };
  }

  async bulkAssignFees(data: {
    feeStructureId: string;
    studentIds: string[];
  }): Promise<ApiResponse<{ assignedCount: number }>> {
    let count = 0;
    for (const sId of data.studentIds) {
      await this.createFeeAssignment({
        studentId: sId,
        feeStructureId: data.feeStructureId,
      });
      count++;
    }
    return { success: true, data: { assignedCount: count } };
  }

  // ==========================================
  // 6. Invoices
  // ==========================================

  async getInvoices(filters?: InvoiceFilters): Promise<ApiResponse<Invoice[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.invoices];

    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((inv) => inv.status === filters.status);
    }
    if (filters?.studentId) {
      items = items.filter((inv) => inv.studentId === filters.studentId);
    }
    if (filters?.program) {
      items = items.filter((inv) =>
        inv.program.toLowerCase().includes(filters.program!.toLowerCase()),
      );
    }
    if (filters?.semester) {
      items = items.filter((inv) => inv.semester === filters.semester);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (inv) =>
          inv.invoiceNumber.toLowerCase().includes(q) ||
          inv.studentName.toLowerCase().includes(q) ||
          inv.rollNumber.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getInvoiceById(id: string): Promise<ApiResponse<Invoice>> {
    await new Promise((r) => setTimeout(r, 30));
    const inv = this.invoices.find(
      (i) => i.id === id || i.invoiceNumber === id,
    );
    if (!inv) throw new Error(`Invoice '${id}' not found.`);
    return { success: true, data: inv };
  }

  async createInvoice(data: Partial<Invoice>): Promise<ApiResponse<Invoice>> {
    await new Promise((r) => setTimeout(r, 70));

    const gross =
      data.grossAmount ||
      (data.lines ? calculateInvoiceGross(data.lines) : 75000);
    const scholarship = data.scholarshipAmount || 0;
    const discount = data.discountAmount || 0;
    const adjustment = data.adjustmentAmount || 0;
    const net = calculateNetPayable(gross, scholarship, discount, adjustment);

    const newInv: Invoice = {
      id: `inv-${Date.now()}`,
      invoiceNumber: `INV-2026-${(this.invoices.length + 10).toString().padStart(4, "0")}`,
      studentId: data.studentId || "std-001",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      semester: data.semester || 5,
      academicYear: data.academicYear || "2026-2027",
      issueDate: data.issueDate || new Date().toISOString().split("T")[0],
      dueDate:
        data.dueDate ||
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split("T")[0],
      lines: data.lines || [
        {
          id: "l-1",
          title: "Semester Tuition",
          categoryName: "Tuition Fee",
          quantity: 1,
          unitAmount: gross,
          totalAmount: gross,
        },
      ],
      grossAmount: gross,
      scholarshipAmount: scholarship,
      discountAmount: discount,
      adjustmentAmount: adjustment,
      netPayable: net,
      paidAmount: 0,
      outstandingAmount: net,
      status: "ISSUED",
      feeAssignmentId: data.feeAssignmentId,
      paymentIds: [],
      receiptIds: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      history: [
        {
          id: `ih-${Date.now()}`,
          action: "ISSUED",
          actor: "Billing Engine",
          timestamp: new Date().toISOString(),
          notes: "Invoice dispatched to student portal.",
        },
      ],
    };

    this.invoices.unshift(newInv);
    return { success: true, data: newInv };
  }

  async cancelInvoice(
    id: string,
    reason: string,
  ): Promise<ApiResponse<Invoice>> {
    await new Promise((r) => setTimeout(r, 60));
    const inv = this.invoices.find((i) => i.id === id);
    if (!inv) throw new Error(`Invoice '${id}' not found.`);

    if (inv.paidAmount > 0) {
      throw new Error(
        `Cannot cancel invoice '${inv.invoiceNumber}': payments of ₹${inv.paidAmount} are already allocated. Process a refund first.`,
      );
    }

    inv.status = "CANCELLED";
    inv.cancelledReason = reason;
    inv.cancelledBy = "Accounts Officer";
    inv.cancelledAt = new Date().toISOString();
    inv.updatedAt = new Date().toISOString();
    inv.history.push({
      id: `ih-${Date.now()}`,
      action: "CANCELLED",
      actor: "Accounts Officer",
      timestamp: new Date().toISOString(),
      notes: `Invoice cancelled. Reason: ${reason}`,
    });

    return { success: true, data: inv };
  }

  // ==========================================
  // 7. Payments & Receipts
  // ==========================================

  async getPayments(filters?: PaymentFilters): Promise<ApiResponse<Payment[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.payments];

    if (filters?.paymentMethod && filters.paymentMethod !== "ALL") {
      items = items.filter((p) => p.paymentMethod === filters.paymentMethod);
    }
    if (filters?.studentId) {
      items = items.filter((p) => p.studentId === filters.studentId);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      items = items.filter(
        (p) =>
          p.transactionRef.toLowerCase().includes(q) ||
          p.studentName.toLowerCase().includes(q) ||
          p.invoiceNumber.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getPaymentById(id: string): Promise<ApiResponse<Payment>> {
    await new Promise((r) => setTimeout(r, 30));
    const p = this.payments.find(
      (pay) => pay.id === id || pay.transactionRef === id,
    );
    if (!p) throw new Error(`Payment '${id}' not found.`);
    return { success: true, data: p };
  }

  async recordPayment(data: {
    invoiceId: string;
    amount: number;
    paymentMethod: PaymentMethod;
    referenceNumber?: string;
    bankName?: string;
    chequeNumber?: string;
    notes?: string;
    recordedBy?: string;
  }): Promise<ApiResponse<{ payment: Payment; receipt: Receipt }>> {
    await new Promise((r) => setTimeout(r, 100));

    if (data.amount <= 0) {
      throw new Error("Payment amount must be greater than zero.");
    }

    const inv = this.invoices.find((i) => i.id === data.invoiceId);
    if (!inv) throw new Error(`Invoice '${data.invoiceId}' not found.`);

    if (inv.status === "CANCELLED") {
      throw new Error("Cannot record payment against a cancelled invoice.");
    }

    if (data.amount > inv.outstandingAmount) {
      throw new Error(
        `Payment amount of ₹${data.amount} exceeds invoice outstanding balance of ₹${inv.outstandingAmount}.`,
      );
    }

    const paymentId = `pay-${Date.now()}`;
    const receiptId = `rec-${Date.now()}`;
    const receiptNumber = `REC-2026-${(this.receipts.length + 10).toString().padStart(4, "0")}`;
    const transactionRef =
      data.referenceNumber ||
      `TXN-${data.paymentMethod}-${Date.now().toString().slice(-6)}`;

    // Create Payment Allocation
    const allocation = {
      id: `alloc-${Date.now()}`,
      paymentId,
      invoiceId: inv.id,
      invoiceNumber: inv.invoiceNumber,
      allocatedAmount: data.amount,
      allocatedAt: new Date().toISOString(),
    };

    // Create Payment Record
    const newPayment: Payment = {
      id: paymentId,
      transactionRef,
      receiptNumber,
      studentId: inv.studentId,
      studentName: inv.studentName,
      rollNumber: inv.rollNumber,
      invoiceId: inv.id,
      invoiceNumber: inv.invoiceNumber,
      amount: data.amount,
      allocatedAmount: data.amount,
      unallocatedAmount: 0,
      paymentMethod: data.paymentMethod,
      referenceNumber: transactionRef,
      bankName: data.bankName,
      chequeNumber: data.chequeNumber,
      paymentDate: new Date().toLocaleString(),
      status: "SUCCESS",
      recordedBy: data.recordedBy || "Accounts Cashier",
      notes: data.notes || "Official institutional fee settlement.",
      allocations: [allocation],
      history: [
        {
          id: `ph-${Date.now()}`,
          action: "PAYMENT_RECORDED",
          actor: data.recordedBy || "Accounts Cashier",
          timestamp: new Date().toISOString(),
          notes: `Recorded ₹${data.amount} via ${data.paymentMethod}.`,
        },
      ],
    };

    // Update Invoice state
    inv.paidAmount = addMoney(inv.paidAmount, data.amount);
    inv.outstandingAmount = calculateOutstanding(
      inv.netPayable,
      inv.paidAmount,
    );
    inv.status = inv.outstandingAmount === 0 ? "PAID" : "PARTIALLY_PAID";
    inv.paymentIds.push(newPayment.id);
    inv.receiptIds.push(receiptId);
    inv.updatedAt = new Date().toISOString();
    inv.history.push({
      id: `ih-${Date.now()}`,
      action: inv.status === "PAID" ? "SETTLED_IN_FULL" : "PARTIAL_PAYMENT",
      actor: newPayment.recordedBy,
      timestamp: new Date().toISOString(),
      notes: `Allocated ₹${data.amount} from payment ${transactionRef}. Remaining: ₹${inv.outstandingAmount}`,
    });

    // Create Receipt
    const newReceipt: Receipt = {
      id: receiptId,
      receiptNumber,
      paymentId,
      transactionRef,
      studentId: inv.studentId,
      studentName: inv.studentName,
      rollNumber: inv.rollNumber,
      invoiceId: inv.id,
      invoiceNumber: inv.invoiceNumber,
      program: inv.program,
      department: inv.department,
      amount: data.amount,
      paymentMethod: data.paymentMethod,
      date: new Date().toLocaleString(),
      status: "ISSUED",
      recordedBy: newPayment.recordedBy,
      notes: `Settlement for ${inv.invoiceNumber}`,
    };

    this.payments.unshift(newPayment);
    this.receipts.unshift(newReceipt);

    return {
      success: true,
      data: { payment: newPayment, receipt: newReceipt },
    };
  }

  async getReceipts(): Promise<ApiResponse<Receipt[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: [...this.receipts] };
  }

  async getReceiptById(id: string): Promise<ApiResponse<Receipt>> {
    await new Promise((r) => setTimeout(r, 30));
    const r = this.receipts.find(
      (rc) => rc.id === id || rc.receiptNumber === id,
    );
    if (!r) throw new Error(`Receipt '${id}' not found.`);
    return { success: true, data: r };
  }

  // ==========================================
  // 8. Scholarships & Assistance
  // ==========================================

  async getScholarships(): Promise<ApiResponse<Scholarship[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: [...this.scholarships] };
  }

  async getScholarshipById(id: string): Promise<ApiResponse<Scholarship>> {
    await new Promise((r) => setTimeout(r, 30));
    const s = this.scholarships.find((sch) => sch.id === id);
    if (!s) throw new Error(`Scholarship '${id}' not found.`);
    return { success: true, data: s };
  }

  async createScholarship(
    data: Partial<Scholarship>,
  ): Promise<ApiResponse<Scholarship>> {
    await new Promise((r) => setTimeout(r, 60));
    const newSch: Scholarship = {
      id: `sch-${Date.now()}`,
      code: data.code || `SCH-${Date.now().toString().slice(-4)}`,
      name: data.name || "Tuition Grant",
      type: data.type || "INSTITUTIONAL",
      description: data.description || "Student fee assistance scheme.",
      discountType: data.discountType || "PERCENTAGE",
      value: data.value || 10,
      maxDiscountAmount: data.maxDiscountAmount,
      eligibilityCriteria:
        data.eligibilityCriteria || "Satisfies academic eligibility.",
      academicYear: data.academicYear || "2026-2027",
      status: "APPROVED",
      totalRecipients: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.scholarships.unshift(newSch);
    return { success: true, data: newSch };
  }

  async approveScholarship(id: string): Promise<ApiResponse<Scholarship>> {
    const s = this.scholarships.find((sch) => sch.id === id);
    if (!s) throw new Error(`Scholarship '${id}' not found.`);
    s.status = "APPROVED";
    s.approvedBy = "Scholarship Board";
    s.approvedAt = new Date().toISOString();
    return { success: true, data: s };
  }

  async getStudentScholarships(
    studentId?: string,
  ): Promise<ApiResponse<StudentScholarship[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.studentScholarships];
    if (studentId) {
      items = items.filter((s) => s.studentId === studentId);
    }
    return { success: true, data: items };
  }

  async applyScholarshipToInvoice(
    invoiceId: string,
    scholarshipId: string,
  ): Promise<ApiResponse<Invoice>> {
    await new Promise((r) => setTimeout(r, 70));
    const inv = this.invoices.find((i) => i.id === invoiceId);
    const sch = this.scholarships.find((s) => s.id === scholarshipId);

    if (!inv) throw new Error(`Invoice '${invoiceId}' not found.`);
    if (!sch) throw new Error(`Scholarship '${scholarshipId}' not found.`);

    const { discountAmount } = calculateScholarshipImpact(inv.grossAmount, sch);
    inv.scholarshipAmount = discountAmount;
    inv.netPayable = calculateNetPayable(
      inv.grossAmount,
      inv.scholarshipAmount,
      inv.discountAmount,
      inv.adjustmentAmount,
    );
    inv.outstandingAmount = calculateOutstanding(
      inv.netPayable,
      inv.paidAmount,
    );
    inv.status =
      inv.outstandingAmount === 0
        ? "PAID"
        : inv.paidAmount > 0
          ? "PARTIALLY_PAID"
          : "ISSUED";
    inv.updatedAt = new Date().toISOString();
    inv.history.push({
      id: `ih-${Date.now()}`,
      action: "SCHOLARSHIP_APPLIED",
      actor: "Finance Committee",
      timestamp: new Date().toISOString(),
      notes: `Applied ${sch.name} (-₹${discountAmount}). Net Payable revised to ₹${inv.netPayable}.`,
    });

    return { success: true, data: inv };
  }

  // ==========================================
  // 9. Refunds
  // ==========================================

  async getRefunds(filters?: {
    status?: RefundStatus | "ALL";
  }): Promise<ApiResponse<Refund[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.refunds];
    if (filters?.status && filters.status !== "ALL") {
      items = items.filter((r) => r.status === filters.status);
    }
    return { success: true, data: items };
  }

  async getRefundById(id: string): Promise<ApiResponse<Refund>> {
    await new Promise((r) => setTimeout(r, 30));
    const ref = this.refunds.find((r) => r.id === id || r.refundNumber === id);
    if (!ref) throw new Error(`Refund '${id}' not found.`);
    return { success: true, data: ref };
  }

  async requestRefund(data: {
    studentId: string;
    invoiceId: string;
    paymentId?: string;
    requestedAmount: number;
    reason: string;
    requestedBy?: string;
  }): Promise<ApiResponse<Refund>> {
    await new Promise((r) => setTimeout(r, 80));

    if (data.requestedAmount <= 0) {
      throw new Error("Refund requested amount must be positive.");
    }

    const inv = this.invoices.find((i) => i.id === data.invoiceId);
    if (!inv) throw new Error(`Invoice '${data.invoiceId}' not found.`);

    const newRef: Refund = {
      id: `ref-${Date.now()}`,
      refundNumber: `REF-2026-${(this.refunds.length + 10).toString().padStart(4, "0")}`,
      studentId: inv.studentId,
      studentName: inv.studentName,
      rollNumber: inv.rollNumber,
      invoiceId: inv.id,
      invoiceNumber: inv.invoiceNumber,
      paymentId: data.paymentId || "pay-general",
      paymentRef: "REF-ALLOC",
      originalPaymentAmount: inv.paidAmount,
      requestedAmount: data.requestedAmount,
      reason: data.reason,
      status: "REQUESTED",
      requestedBy: data.requestedBy || `${inv.studentName} (Student)`,
      requestedAt: new Date().toISOString(),
      timeline: [
        {
          id: `rt-${Date.now()}`,
          action: "REFUND_REQUESTED",
          actor: data.requestedBy || inv.studentName,
          timestamp: new Date().toISOString(),
          notes: data.reason,
        },
      ],
    };

    this.refunds.unshift(newRef);
    return { success: true, data: newRef };
  }

  async reviewRefund(
    refundId: string,
    action: "APPROVE" | "REJECT",
    notes: string,
    approvedAmount?: number,
  ): Promise<ApiResponse<Refund>> {
    await new Promise((r) => setTimeout(r, 70));

    const ref = this.refunds.find((r) => r.id === refundId);
    if (!ref) throw new Error(`Refund petition '${refundId}' not found.`);

    if (action === "APPROVE") {
      ref.status = "APPROVED";
      ref.approvedAmount = approvedAmount || ref.requestedAmount;
      ref.reviewedBy = "Finance Committee Reviewer";
      ref.reviewedAt = new Date().toISOString();
      ref.reviewerNotes = notes;
      ref.timeline.push({
        id: `rt-${Date.now()}`,
        action: "REFUND_APPROVED",
        actor: "Finance Committee",
        timestamp: new Date().toISOString(),
        notes: `Approved ₹${ref.approvedAmount}. ${notes}`,
      });
    } else {
      ref.status = "REJECTED";
      ref.reviewedBy = "Finance Committee Reviewer";
      ref.reviewedAt = new Date().toISOString();
      ref.reviewerNotes = notes;
      ref.timeline.push({
        id: `rt-${Date.now()}`,
        action: "REFUND_REJECTED",
        actor: "Finance Committee",
        timestamp: new Date().toISOString(),
        notes: `Rejected. Rationale: ${notes}`,
      });
    }

    return { success: true, data: ref };
  }

  async processRefund(refundId: string): Promise<ApiResponse<Refund>> {
    await new Promise((r) => setTimeout(r, 70));

    const ref = this.refunds.find((r) => r.id === refundId);
    if (!ref) throw new Error(`Refund '${refundId}' not found.`);

    if (ref.status !== "APPROVED") {
      throw new Error("Cannot process refund that has not been approved.");
    }

    ref.status = "PROCESSED";
    ref.processedAt = new Date().toISOString();
    ref.timeline.push({
      id: `rt-${Date.now()}`,
      action: "PROCESSED",
      actor: "Bank Disbursement Unit",
      timestamp: new Date().toISOString(),
      notes: `Electronic disbursement of ₹${ref.approvedAmount || ref.requestedAmount} released.`,
    });

    return { success: true, data: ref };
  }

  // ==========================================
  // 10. Multi-Format Finance Reports
  // ==========================================

  async generateReport(filter: FinanceReportFilter): Promise<
    ApiResponse<{
      title: string;
      generatedAt: string;
      totalRecords: number;
      rows: Record<string, unknown>[];
    }>
  > {
    await new Promise((r) => setTimeout(r, 60));

    let title = "Institutional Finance Summary Report";
    let rows: Record<string, unknown>[] = [];

    switch (filter.reportType) {
      case "COLLECTION":
        title = "Fee Collection & Realization Ledger";
        rows = this.payments.map((p) => ({
          TransactionRef: p.transactionRef,
          ReceiptNo: p.receiptNumber,
          StudentName: p.studentName,
          RollNumber: p.rollNumber,
          InvoiceNo: p.invoiceNumber,
          Amount: p.amount,
          PaymentMethod: p.paymentMethod,
          Date: p.paymentDate,
          Status: p.status,
        }));
        break;

      case "OUTSTANDING":
        title = "Student Fee Outstanding & Due Register";
        rows = this.invoices
          .filter((i) => i.outstandingAmount > 0)
          .map((i) => ({
            InvoiceNo: i.invoiceNumber,
            StudentName: i.studentName,
            RollNumber: i.rollNumber,
            Program: i.program,
            Semester: i.semester,
            NetPayable: i.netPayable,
            PaidAmount: i.paidAmount,
            Outstanding: i.outstandingAmount,
            DueDate: i.dueDate,
            Status: i.status,
          }));
        break;

      case "AGING":
        title = "Overdue Fee Aging & Debt Analysis";
        rows = this.invoices
          .filter((i) => i.outstandingAmount > 0)
          .map((i) => ({
            InvoiceNo: i.invoiceNumber,
            StudentName: i.studentName,
            RollNumber: i.rollNumber,
            Outstanding: i.outstandingAmount,
            DueDate: i.dueDate,
            OverdueDays: calculateOverdueDays(i.dueDate),
            AgingBucket: calculateAgingBucket(i.dueDate),
          }));
        break;

      case "PAYMENT_METHOD":
        title = "Payment Channel Distribution Summary";
        rows = this.payments.map((p) => ({
          PaymentMethod: p.paymentMethod,
          Amount: p.amount,
          Student: p.studentName,
          Date: p.paymentDate,
        }));
        break;

      case "SCHOLARSHIP":
      default:
        title = "Scholarship & Fee Concession Audit";
        rows = this.studentScholarships.map((s) => ({
          StudentName: s.studentName,
          RollNumber: s.rollNumber,
          Scholarship: s.scholarshipName,
          OriginalFee: s.originalFee,
          DiscountAmount: s.discountAmount,
          AdjustedFee: s.adjustedFee,
          Status: s.status,
          GrantedDate: s.grantedDate,
        }));
        break;
    }

    return {
      success: true,
      data: {
        title,
        generatedAt: new Date().toLocaleString(),
        totalRecords: rows.length,
        rows,
      },
    };
  }

  // ==========================================
  // 11. Student Financial Statement
  // ==========================================

  async getStudentStatement(
    studentId?: string,
  ): Promise<ApiResponse<StudentFeeStatement>> {
    await new Promise((r) => setTimeout(r, 40));

    const sId = studentId || "std-001";
    const studentInvoices = this.invoices.filter(
      (i) => i.studentId === sId || i.rollNumber === "24CSE0101",
    );
    const studentReceipts = this.receipts.filter(
      (r) => r.studentId === sId || r.rollNumber === "24CSE0101",
    );

    const totalBilled = studentInvoices.reduce(
      (acc, i) => addMoney(acc, i.grossAmount),
      0,
    );
    const totalPaid = studentInvoices.reduce(
      (acc, i) => addMoney(acc, i.paidAmount),
      0,
    );
    const totalDue = studentInvoices.reduce(
      (acc, i) => addMoney(acc, i.outstandingAmount),
      0,
    );

    return {
      success: true,
      data: {
        student_id: sId,
        student_name: studentInvoices[0]?.studentName || "Aarav Patel",
        roll_number: studentInvoices[0]?.rollNumber || "24CSE0101",
        program:
          studentInvoices[0]?.program ||
          "B.Tech Computer Science & Engineering",
        academic_year: "2026-2027",
        total_billed: totalBilled,
        total_paid: totalPaid,
        total_due: totalDue,
        invoices: studentInvoices,
        receipts: studentReceipts,
      },
    };
  }
}

export const financeService = new FinanceService();
