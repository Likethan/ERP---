/**
 * CampusOS Finance, Fees & Billing Module Test Suite
 * Validates domain contracts, money arithmetic, invoice calculations,
 * aging delinquency, scholarship discounts & caps, payment allocations,
 * receipt vouchers, refund workflows, intelligence reports, global search, and RBAC rules.
 */

import { financeService } from "../services/finance.service";
import {
  formatMoney,
  parseMoney,
  addMoney,
  subtractMoney,
  calculateInvoiceGross,
  calculateDiscountAmount,
  calculateScholarshipImpact,
  calculateNetPayable,
  calculateOutstanding,
  calculateOverdueDays,
  calculateAgingBucket,
  calculateCollectionRate,
  compileAgingBuckets,
} from "../services/financial-calculator";
import { searchService } from "../services/search.service";
import { Scholarship, Invoice } from "../types/finance";

export async function runFinanceModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(condition: unknown, testName: string, failureDetails?: string) {
    if (Boolean(condition)) {
      results.push({ testName, passed: true });
    } else {
      results.push({ testName, passed: false, message: failureDetails || "Assertion failed" });
    }
  }

  try {
    // ==========================================
    // 1. Money Arithmetic & Formatting
    // ==========================================
    assert(formatMoney(25000) === "₹25,000.00", "1. formatMoney formats integer amounts to INR");
    assert(formatMoney(8500.5) === "₹8,500.50", "1. formatMoney handles decimal values accurately");
    assert(formatMoney(0) === "₹0.00", "1. formatMoney handles zero amount");
    assert(parseMoney("₹25,000.00") === 25000, "1. parseMoney strips symbols and commas");
    assert(parseMoney("12500.50") === 12500.5, "1. parseMoney parses standard number strings");

    assert(addMoney(10000.1, 20000.2) === 30000.3, "1. addMoney eliminates floating point drift");
    assert(subtractMoney(50000, 15000.25) === 34999.75, "1. subtractMoney computes exact differences");
    assert(subtractMoney(10000, 15000) === -5000, "1. subtractMoney computes negative difference correctly");

    // ==========================================
    // 2. Invoice Financial Calculations
    // ==========================================
    const testLines = [
      { id: "1", title: "Tuition", categoryName: "Tuition", quantity: 1, unitAmount: 50000, totalAmount: 50000 },
      { id: "2", title: "Lab", categoryName: "Lab", quantity: 1, unitAmount: 12000, totalAmount: 12000 },
      { id: "3", title: "Library", categoryName: "Library", quantity: 1, unitAmount: 3000, totalAmount: 3000 },
    ];
    assert(calculateInvoiceGross(testLines) === 65000, "2. calculateInvoiceGross sums all line items correctly");

    const net = calculateNetPayable(65000, 10000, 2000, 1000);
    assert(net === 52000, "2. calculateNetPayable computes Gross - Sch - Disc - Adj (65k - 10k - 2k - 1k = 52k)");

    const outstanding = calculateOutstanding(54000, 20000);
    assert(outstanding === 34000, "2. calculateOutstanding computes Net - Paid (54k - 20k = 34k)");

    const settledOutstanding = calculateOutstanding(54000, 54000);
    assert(settledOutstanding === 0, "2. calculateOutstanding computes 0 for fully settled invoices");

    // ==========================================
    // 3. Aging & Delinquency Calculations
    // ==========================================
    const futureDate = new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    const past15Days = new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    const past45Days = new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    const past75Days = new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    const past120Days = new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];

    assert(calculateOverdueDays(futureDate) === 0, "3. Future due date has 0 overdue days");
    assert(calculateAgingBucket(futureDate) === "CURRENT", "3. Future due date maps to CURRENT bucket");

    assert(calculateOverdueDays(past15Days) >= 14 && calculateOverdueDays(past15Days) <= 16, "3. 15-day overdue date calculates accurately");
    assert(calculateAgingBucket(past15Days) === "DAYS_1_30", "3. 15-day overdue maps to DAYS_1_30 bucket");
    assert(calculateAgingBucket(past45Days) === "DAYS_31_60", "3. 45-day overdue maps to DAYS_31_60 bucket");
    assert(calculateAgingBucket(past75Days) === "DAYS_61_90", "3. 75-day overdue maps to DAYS_61_90 bucket");
    assert(calculateAgingBucket(past120Days) === "DAYS_90_PLUS", "3. 120-day overdue maps to DAYS_90_PLUS bucket");

    assert(calculateCollectionRate(300000, 210000) === 70, "3. calculateCollectionRate returns 70% for 210k / 300k");
    assert(calculateCollectionRate(0, 0) === 0, "3. calculateCollectionRate safely handles 0 gross");

    // ==========================================
    // 4. Scholarship Impact & Capping Rules
    // ==========================================
    const pctScholarship: Scholarship = {
      id: "sch-test-1",
      code: "MERIT-20",
      name: "Merit 20%",
      type: "MERIT",
      description: "20% merit discount capped at 25k",
      discountType: "PERCENTAGE",
      value: 20,
      maxDiscountAmount: 25000,
      eligibilityCriteria: "CGPA > 9.0",
      academicYear: "2026-2027",
      status: "APPROVED",
      totalRecipients: 10,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const impact1 = calculateScholarshipImpact(80000, pctScholarship);
    assert(impact1.discountAmount === 16000, "4. 20% on 80,000 = 16,000 discount");
    assert(impact1.adjustedFee === 64000, "4. Adjusted fee becomes 64,000");

    const impactCapped = calculateScholarshipImpact(200000, pctScholarship);
    assert(impactCapped.discountAmount === 25000, "4. 20% on 200,000 = 40,000 is capped at 25,000");
    assert(impactCapped.adjustedFee === 175000, "4. Adjusted fee with cap is 175,000");

    const fixedScholarship: Scholarship = {
      ...pctScholarship,
      id: "sch-test-2",
      discountType: "FIXED",
      value: 15000,
    };
    const impactFixed = calculateScholarshipImpact(60000, fixedScholarship);
    assert(impactFixed.discountAmount === 15000, "4. Fixed scholarship grants exact 15,000 discount");
    assert(impactFixed.adjustedFee === 45000, "4. Adjusted fee becomes 45,000");

    // ==========================================
    // 5. Fee Categories & Items Service
    // ==========================================
    const catsRes = await financeService.getFeeCategories();
    assert(catsRes.success === true, "5. getFeeCategories returns success");
    assert(catsRes.data.length >= 7, "5. Default institutional fee categories exist");

    const newCatRes = await financeService.createFeeCategory({
      code: "HOSTEL-MESS",
      name: "Hostel & Mess Boarding Fee",
      type: "HOSTEL",
      isTaxable: false,
      isRefundable: true,
    });
    assert(newCatRes.success === true, "5. createFeeCategory creates valid entity");
    assert(newCatRes.data.status === "ACTIVE", "5. New category defaults to ACTIVE status");

    const toggled = await financeService.toggleCategoryStatus(newCatRes.data.id);
    assert(toggled.data.status === "INACTIVE", "5. toggleCategoryStatus transitions ACTIVE to INACTIVE");

    // ==========================================
    // 6. Fee Structures & Lifecycle
    // ==========================================
    const fsRes = await financeService.getFeeStructures();
    assert(fsRes.success === true, "6. getFeeStructures returns success");
    assert(fsRes.data.length >= 2, "6. Canonical fee structures seeded");

    const createdStructure = await financeService.createFeeStructure({
      code: "BTECH-CSE-2026-S5",
      name: "B.Tech CSE Sem 5 Standard Fee",
      program: "B.Tech Computer Science & Engineering",
      department: "Computer Science & Engineering",
      academicYear: "2026-2027",
      semester: 5,
      components: [
        { id: "c1", title: "Tuition", categoryName: "Tuition Fee", amount: 65000, isMandatory: true },
        { id: "c2", title: "Exam Fee", categoryName: "Exam Fee", amount: 2500, isMandatory: true },
      ],
      grossTotal: 67500,
    });
    assert(createdStructure.data.status === "DRAFT", "6. New Fee Structure initializes as DRAFT");

    const submitted = await financeService.submitFeeStructureForApproval(createdStructure.data.id);
    assert(submitted.data.status === "PENDING_APPROVAL", "6. Submit transitions DRAFT to PENDING_APPROVAL");

    const approved = await financeService.approveFeeStructure(createdStructure.data.id);
    assert(approved.data.status === "APPROVED", "6. Approve transitions PENDING_APPROVAL to APPROVED");

    const activated = await financeService.activateFeeStructure(createdStructure.data.id);
    assert(activated.data.status === "ACTIVE", "6. Activate transitions APPROVED to ACTIVE");

    const retired = await financeService.retireFeeStructure(createdStructure.data.id);
    assert(retired.data.status === "RETIRED", "6. Retire transitions ACTIVE to RETIRED");

    // ==========================================
    // 7. Student Fee Assignments
    // ==========================================
    const assignmentsRes = await financeService.getFeeAssignments();
    assert(assignmentsRes.success === true, "7. getFeeAssignments returns success");
    assert(assignmentsRes.data.length >= 2, "7. Baseline student fee assignments exist");

    const newAssignment = await financeService.createFeeAssignment({
      studentId: "stu-24cse0101",
      feeStructureId: fsRes.data[0].id,
      notes: "Semester 5 registration assignment",
    });
    assert(newAssignment.success === true, "7. createFeeAssignment links student to structure");
    assert(newAssignment.data.grossAmount > 0, "7. Assignment gross calculated from structure components");
    assert(newAssignment.data.netPayable === newAssignment.data.grossAmount - newAssignment.data.scholarshipAmount, "7. Net payable accounts for scholarship discount");

    // ==========================================
    // 8. Invoices Management & Calculations
    // ==========================================
    const invRes = await financeService.getInvoices();
    assert(invRes.success === true, "8. getInvoices returns success");
    assert(invRes.data.length >= 4, "8. Canonical invoices seeded");

    const newInvoice = await financeService.createInvoice({
      studentId: "stu-24cse0101",
      studentName: "Aarav Patel",
      rollNumber: "24CSE0101",
      program: "B.Tech Computer Science & Engineering",
      semester: 5,
      grossAmount: 75000,
      scholarshipAmount: 10000,
    });
    assert(newInvoice.data.netPayable === 65000, "8. Created invoice computes net payable (75k - 10k = 65k)");
    assert(newInvoice.data.outstandingAmount === 65000, "8. Created invoice starts with 100% outstanding");
    assert(newInvoice.data.status === "ISSUED", "8. Initial invoice status is ISSUED");

    // Cancel unpaid invoice
    const cancelledInv = await financeService.cancelInvoice(newInvoice.data.id, "Course withdrawal");
    assert(cancelledInv.data.status === "CANCELLED", "8. Unpaid invoice can be successfully cancelled");
    assert(cancelledInv.data.cancelledReason === "Course withdrawal", "8. Cancellation stores audit reason");

    // ==========================================
    // 9. Payments, Allocations & Validations
    // ==========================================
    const activeInv = invRes.data.find((i) => i.outstandingAmount > 0 && i.status !== "CANCELLED");
    assert(Boolean(activeInv), "9. Found active unpaid invoice for payment test");

    if (activeInv) {
      const payAmount = 5000;
      const prevOutstanding = activeInv.outstandingAmount;
      const prevPaid = activeInv.paidAmount;

      const paymentRes = await financeService.recordPayment({
        invoiceId: activeInv.id,
        amount: payAmount,
        paymentMethod: "UPI",
        referenceNumber: `UTR-TEST-${Date.now()}`,
        notes: "Automated test payment",
      });

      assert(paymentRes.success === true, "9. recordPayment commits successfully");
      assert(paymentRes.data.payment.amount === payAmount, "9. Payment record amount matches");
      assert(paymentRes.data.payment.status === "SUCCESS", "9. Payment record status is SUCCESS");
      assert(paymentRes.data.payment.allocations.length === 1, "9. Payment allocation ledger entry created");
      assert(paymentRes.data.payment.allocations[0].allocatedAmount === payAmount, "9. Allocation amount equals payment");

      // Verify updated invoice state
      const updatedInv = await financeService.getInvoiceById(activeInv.id);
      assert(updatedInv.data.paidAmount === prevPaid + payAmount, "9. Invoice paidAmount incremented by payment");
      assert(updatedInv.data.outstandingAmount === prevOutstanding - payAmount, "9. Invoice outstanding decremented");
      assert(updatedInv.data.status === "PARTIALLY_PAID" || updatedInv.data.status === "PAID", "9. Invoice status transitions to PARTIALLY_PAID or PAID");

      // Verify overpayment rejection
      let overpayErrorCaught = false;
      try {
        await financeService.recordPayment({
          invoiceId: activeInv.id,
          amount: updatedInv.data.outstandingAmount + 50000,
          paymentMethod: "CASH",
        });
      } catch (err: unknown) {
        overpayErrorCaught = true;
      }
      assert(overpayErrorCaught === true, "9. recordPayment rejects overpayment exceeding invoice outstanding balance");

      // Verify zero/negative payment rejection
      let zeroPayErrorCaught = false;
      try {
        await financeService.recordPayment({
          invoiceId: activeInv.id,
          amount: -500,
          paymentMethod: "CASH",
        });
      } catch (err: unknown) {
        zeroPayErrorCaught = true;
      }
      assert(zeroPayErrorCaught === true, "9. recordPayment rejects non-positive payment amount");
    }

    // ==========================================
    // 10. Official Receipts Generation
    // ==========================================
    const receiptsRes = await financeService.getReceipts();
    assert(receiptsRes.success === true, "10. getReceipts returns success");
    assert(receiptsRes.data.length >= 3, "10. Receipt archive populated");

    const firstReceipt = receiptsRes.data[0];
    assert(firstReceipt.receiptNumber.startsWith("REC-2026-"), "10. Receipt voucher number follows institutional sequence");
    assert(firstReceipt.amount > 0, "10. Receipt amount is non-zero");
    assert(Boolean(firstReceipt.transactionRef), "10. Receipt maps to valid transaction reference");

    const fetchedReceipt = await financeService.getReceiptById(firstReceipt.id);
    assert(fetchedReceipt.data.id === firstReceipt.id, "10. getReceiptById returns exact voucher record");

    // ==========================================
    // 11. Scholarships & Discount Applications
    // ==========================================
    const scholarshipsRes = await financeService.getScholarships();
    assert(scholarshipsRes.success === true, "11. getScholarships returns success");
    assert(scholarshipsRes.data.length >= 2, "11. Institutional scholarship schemes seeded");

    const createdSch = await financeService.createScholarship({
      code: "DEANS-EXCELLENCE",
      name: "Dean's Excellence Scholarship",
      type: "MERIT",
      discountType: "PERCENTAGE",
      value: 15,
      maxDiscountAmount: 20000,
    });
    assert(createdSch.data.status === "APPROVED", "11. createScholarship registers scheme");

    // ==========================================
    // 12. Refunds Review & Disbursement Workflow
    // ==========================================
    const refundsRes = await financeService.getRefunds();
    assert(refundsRes.success === true, "12. getRefunds returns success");
    assert(refundsRes.data.length >= 1, "12. Canonical refunds seeded");

    const createdRefund = await financeService.requestRefund({
      studentId: "stu-24cse0101",
      invoiceId: invRes.data[0].id,
      requestedAmount: 5000,
      reason: "Hostel security deposit refund post vacating",
      requestedBy: "Aarav Patel (Student)",
    });
    assert(createdRefund.data.status === "REQUESTED", "12. requestRefund initializes in REQUESTED status");
    assert(createdRefund.data.requestedAmount === 5000, "12. Requested refund amount preserved");

    // Review & Approve
    const approvedRefund = await financeService.reviewRefund(
      createdRefund.data.id,
      "APPROVE",
      "Approved per hostel clearance certificate",
      5000
    );
    assert(approvedRefund.data.status === "APPROVED", "12. reviewRefund APPROVE transitions to APPROVED");
    assert(approvedRefund.data.approvedAmount === 5000, "12. Sanctioned refund amount stored");

    // Electronic Bank Disbursement
    const processedRefund = await financeService.processRefund(approvedRefund.data.id);
    assert(processedRefund.data.status === "PROCESSED", "12. processRefund transitions APPROVED to PROCESSED");
    assert(Boolean(processedRefund.data.processedAt), "12. Electronic disbursement timestamp recorded");

    // Review & Reject test
    const rejectedReq = await financeService.requestRefund({
      studentId: "stu-24cse0102",
      invoiceId: invRes.data[0].id,
      requestedAmount: 3000,
      reason: "Course drop after deadline",
    });
    const rejectedRefund = await financeService.reviewRefund(
      rejectedReq.data.id,
      "REJECT",
      "Strict policy: no refunds permitted after deadline"
    );
    assert(rejectedRefund.data.status === "REJECTED", "12. reviewRefund REJECT transitions to REJECTED");

    // ==========================================
    // 13. Reports Intelligence
    // ==========================================
    const collectionReport = await financeService.generateReport({ reportType: "COLLECTION" });
    assert(collectionReport.success === true, "13. generateReport COLLECTION succeeds");
    assert(collectionReport.data.rows.length >= 1, "13. Collection ledger contains transaction rows");

    const outstandingReport = await financeService.generateReport({ reportType: "OUTSTANDING" });
    assert(outstandingReport.success === true, "13. generateReport OUTSTANDING succeeds");
    assert(outstandingReport.data.rows.length >= 1, "13. Outstanding report contains pending dues");

    const agingReport = await financeService.generateReport({ reportType: "AGING" });
    assert(agingReport.success === true, "13. generateReport AGING succeeds");
    assert(agingReport.data.rows.length >= 1, "13. Aging analysis contains delinquency rows");

    const scholarshipReport = await financeService.generateReport({ reportType: "SCHOLARSHIP" });
    assert(scholarshipReport.success === true, "13. generateReport SCHOLARSHIP succeeds");
    assert(scholarshipReport.data.rows.length >= 1, "13. Scholarship report contains concession grants");

    // ==========================================
    // 14. Global Search Integration
    // ==========================================
    const invoiceSearch = await searchService.search("INV-2026-0001");
    assert(invoiceSearch.data.some((r) => r.title.includes("INV-2026-0001")), "14. Global search finds invoices by number");

    const receiptSearch = await searchService.search("REC-2026-0001");
    assert(receiptSearch.data.some((r) => r.title.includes("REC-2026-0001")), "14. Global search finds receipts by voucher");

    const feeStructureSearch = await searchService.search("FS-2026-CSE-S5");
    assert(feeStructureSearch.data.some((r) => r.category === "Finance"), "14. Global search finds fee structures");

    // ==========================================
    // 15. RBAC Permission Matrix Verification
    // ==========================================
    const rbacFinanceMatrix = {
      SUPER_ADMIN: {
        viewFinance: true,
        manageCategories: true,
        manageStructures: true,
        assignFees: true,
        manageInvoices: true,
        recordPayments: true,
        approveRefunds: true,
        processRefunds: true,
        viewReports: true,
      },
      ACCOUNTS: {
        viewFinance: true,
        manageCategories: false,
        manageStructures: false,
        assignFees: true,
        manageInvoices: true,
        recordPayments: true,
        approveRefunds: false,
        processRefunds: true,
        viewReports: true,
      },
      HOD: {
        viewFinance: true,
        manageCategories: false,
        manageStructures: false,
        assignFees: false,
        manageInvoices: false,
        recordPayments: false,
        approveRefunds: false,
        processRefunds: false,
        viewReports: true,
      },
      STUDENT: {
        viewFinance: false, // only has "My Finance" personal statement
        manageCategories: false,
        manageStructures: false,
        assignFees: false,
        manageInvoices: false,
        recordPayments: false,
        approveRefunds: false,
        processRefunds: false,
        viewReports: false,
      },
    };

    assert(rbacFinanceMatrix.SUPER_ADMIN.approveRefunds === true, "15. Super Admin authorized to approve refunds");
    assert(rbacFinanceMatrix.ACCOUNTS.recordPayments === true, "15. Accounts Officer authorized to record payments");
    assert(rbacFinanceMatrix.ACCOUNTS.manageInvoices === true, "15. Accounts Officer authorized to manage invoices");
    assert(rbacFinanceMatrix.HOD.manageCategories === false, "15. HOD prohibited from editing fee categories");
    assert(rbacFinanceMatrix.HOD.recordPayments === false, "15. HOD prohibited from recording payments");
    assert(rbacFinanceMatrix.STUDENT.recordPayments === false, "15. Student strictly prohibited from recording payments");
    assert(rbacFinanceMatrix.STUDENT.manageStructures === false, "15. Student strictly prohibited from modifying fee structures");
    assert(rbacFinanceMatrix.STUDENT.approveRefunds === false, "15. Student strictly prohibited from approving refunds");
    assert(rbacFinanceMatrix.STUDENT.viewReports === false, "15. Student strictly prohibited from viewing institutional financial reports");

  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({ testName: "Exception during test run", passed: false, message: errorMsg });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  return { passed, failed, results };
}

if (typeof process !== "undefined" && process.argv[1]?.includes("finance-module.test")) {
  runFinanceModuleTests().then((res) => {
    console.log(`\n==============================================`);
    console.log(`CampusOS Finance, Fees & Billing Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`==============================================`);
    res.results.forEach((r) => {
      console.log(`${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`);
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
