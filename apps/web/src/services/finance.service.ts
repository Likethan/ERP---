import { ApiResponse } from "@campusos/types";
import {
  FeeStructureItem,
  InvoiceItem,
  PaymentTransactionItem,
  ScholarshipItem,
  MOCK_FEE_STRUCTURES,
  MOCK_INVOICES,
  MOCK_PAYMENTS,
  MOCK_SCHOLARSHIPS,
} from "@/mocks/finance.mock";

class FinanceService {
  private feeStructures: FeeStructureItem[] = [...MOCK_FEE_STRUCTURES];
  private invoices: InvoiceItem[] = [...MOCK_INVOICES];
  private payments: PaymentTransactionItem[] = [...MOCK_PAYMENTS];
  private scholarships: ScholarshipItem[] = [...MOCK_SCHOLARSHIPS];

  async getFeeStructures(): Promise<ApiResponse<FeeStructureItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.feeStructures };
  }

  async getInvoices(status?: string): Promise<ApiResponse<InvoiceItem[]>> {
    await new Promise((r) => setTimeout(r, 50));
    let items = [...this.invoices];
    if (status) {
      items = items.filter((inv) => inv.status === status);
    }
    return { success: true, data: items };
  }

  async getInvoiceById(id: string): Promise<ApiResponse<InvoiceItem | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const inv = this.invoices.find((i) => i.id === id || i.invoiceNumber === id) || null;
    return { success: true, data: inv };
  }

  async getPayments(): Promise<ApiResponse<PaymentTransactionItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.payments };
  }

  async getScholarships(): Promise<ApiResponse<ScholarshipItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.scholarships };
  }

  async recordPayment(data: {
    invoiceId: string;
    amount: number;
    paymentMode: PaymentTransactionItem["paymentMode"];
  }): Promise<ApiResponse<PaymentTransactionItem>> {
    await new Promise((r) => setTimeout(r, 120));
    const inv = this.invoices.find((i) => i.id === data.invoiceId);
    if (inv) {
      inv.paidAmount += data.amount;
      inv.balanceAmount = Math.max(0, inv.totalAmount - inv.paidAmount);
      inv.status = inv.balanceAmount === 0 ? "PAID" : "PARTIALLY_PAID";
    }

    const newPayment: PaymentTransactionItem = {
      id: `pay-${Date.now()}`,
      transactionRef: `TXN-DEMO-${Date.now().toString().slice(-6)}`,
      receiptNumber: `REC-2026-0${this.payments.length + 915}`,
      studentName: inv ? inv.studentName : "Student",
      rollNumber: inv ? inv.rollNumber : "24CSE0101",
      invoiceNumber: inv ? inv.invoiceNumber : "INV-2026-0000",
      amount: data.amount,
      paymentMode: data.paymentMode,
      paymentDate: new Date().toLocaleString(),
      status: "SUCCESS",
    };

    this.payments.unshift(newPayment);
    return { success: true, data: newPayment };
  }

  async getDashboard(): Promise<ApiResponse<{
    total_billed: number;
    total_collected: number;
    total_outstanding: number;
    collection_rate_percent: number;
    total_invoices_count: number;
    paid_invoices_count: number;
    pending_invoices_count: number;
    overdue_invoices_count: number;
    today_collections: number;
  }>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        total_billed: 18450000,
        total_collected: 15280000,
        total_outstanding: 3170000,
        collection_rate_percent: 82.8,
        total_invoices_count: this.invoices.length || 240,
        paid_invoices_count: 188,
        pending_invoices_count: 38,
        overdue_invoices_count: 14,
        today_collections: 285000,
      },
    };
  }

  async getStudentStatement(studentId?: string): Promise<ApiResponse<any>> {
    await new Promise((r) => setTimeout(r, 40));
    return {
      success: true,
      data: {
        student_id: studentId || "stu-24cse0101",
        student_name: "Aarav Patel",
        roll_number: "24CSE0101",
        program: "B.Tech Computer Science & Engineering",
        academic_year: "2026-2027",
        total_billed: 165000,
        total_paid: 165000,
        total_due: 0,
        invoices: this.invoices.filter((i) => i.rollNumber === "24CSE0101"),
        receipts: this.payments.filter((p) => p.rollNumber === "24CSE0101"),
      },
    };
  }

  async createFeeStructure(data: Partial<FeeStructureItem>): Promise<ApiResponse<FeeStructureItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newFs: FeeStructureItem = {
      id: `fee-struct-${Date.now()}`,
      name: data.name || "Tuition & Lab Fee Scheme",
      academicYear: data.academicYear || "2026-2027",
      program: data.program || "B.Tech Computer Science & Engineering",
      totalAnnualFee: data.totalAnnualFee || 85000,
      components: data.components || [
        { title: "Tuition Fee", amount: 65000, mandatory: true },
        { title: "Lab & Infrastructure", amount: 20000, mandatory: true },
      ],
      status: data.status || "ACTIVE",
    };
    this.feeStructures.unshift(newFs);
    return { success: true, data: newFs };
  }

  async createInvoice(data: Partial<InvoiceItem>): Promise<ApiResponse<InvoiceItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newInv: InvoiceItem = {
      id: `inv-${Date.now()}`,
      invoiceNumber: `INV-2026-0${this.invoices.length + 100}`,
      studentId: data.studentId || "stu-1",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      program: data.program || "B.Tech Computer Science & Engineering",
      totalAmount: data.totalAmount || 85000,
      paidAmount: 0,
      balanceAmount: data.totalAmount || 85000,
      dueDate: data.dueDate || "2026-10-31",
      issueDate: data.issueDate || new Date().toISOString().split("T")[0],
      status: "ISSUED",
    };
    this.invoices.unshift(newInv);
    return { success: true, data: newInv };
  }
}

export const financeService = new FinanceService();
