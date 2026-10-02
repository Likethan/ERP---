/**
 * CampusOS Financial Calculator & Money Utilities
 * Pure deterministic functions for integer minor-unit financial arithmetic,
 * formatting, overdue aging, scholarship discounts, and invoice totals.
 */

import { AgingBucket, AgingBucketSummary, Scholarship } from "@/types/finance";

/**
 * Formats a numeric currency amount into standard Indian Rupee string: ₹25,000.00
 */
export function formatMoney(
  amount: number | null | undefined,
  options?: { hideDecimals?: boolean; currency?: string }
): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "₹0.00";
  }

  const fractionDigits = options?.hideDecimals ? 0 : 2;
  const formatted = new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(amount);

  return `₹${formatted}`;
}

/**
 * Parses user input currency string back into a numeric amount.
 * e.g. "₹25,000.50" -> 25000.5
 */
export function parseMoney(input: string): number {
  if (!input) return 0;
  const clean = input.replace(/[^0-9.-]+/g, "");
  const val = parseFloat(clean);
  return isNaN(val) ? 0 : Math.round(val * 100) / 100;
}

/**
 * Adds two monetary amounts using rounded precision to avoid floating-point drift.
 */
export function addMoney(a: number, b: number): number {
  const minorA = Math.round(a * 100);
  const minorB = Math.round(b * 100);
  return (minorA + minorB) / 100;
}

/**
 * Subtracts monetary amount b from a using rounded precision.
 */
export function subtractMoney(a: number, b: number): number {
  const minorA = Math.round(a * 100);
  const minorB = Math.round(b * 100);
  return (minorA - minorB) / 100;
}

/**
 * Calculates gross invoice total by summing line item amounts.
 */
export function calculateInvoiceGross(lines: { totalAmount: number }[]): number {
  if (!lines || lines.length === 0) return 0;
  const sumMinor = lines.reduce((acc, line) => acc + Math.round((line.totalAmount || 0) * 100), 0);
  return sumMinor / 100;
}

/**
 * Calculates discount amount given type (percentage vs fixed) and maximum ceiling.
 */
export function calculateDiscountAmount(
  gross: number,
  discountType: "PERCENTAGE" | "FIXED",
  value: number,
  maxDiscount?: number
): number {
  if (gross <= 0 || value <= 0) return 0;

  let computed = 0;
  if (discountType === "PERCENTAGE") {
    computed = (gross * value) / 100;
  } else {
    computed = value;
  }

  if (maxDiscount !== undefined && maxDiscount > 0) {
    computed = Math.min(computed, maxDiscount);
  }

  return Math.min(Math.round(computed * 100) / 100, gross);
}

/**
 * Evaluates scholarship impact on original fee.
 */
export function calculateScholarshipImpact(
  originalFee: number,
  scholarship: Pick<Scholarship, "discountType" | "value" | "maxDiscountAmount">
): { discountAmount: number; adjustedFee: number } {
  const discountAmount = calculateDiscountAmount(
    originalFee,
    scholarship.discountType,
    scholarship.value,
    scholarship.maxDiscountAmount
  );
  const adjustedFee = subtractMoney(originalFee, discountAmount);
  return { discountAmount, adjustedFee };
}

/**
 * Calculates Net Payable: Gross - Scholarship - Discount - Adjustments (or + Debit adjustments).
 */
export function calculateNetPayable(
  gross: number,
  scholarship = 0,
  discount = 0,
  adjustments = 0
): number {
  const deductions = addMoney(addMoney(scholarship, discount), adjustments);
  const net = subtractMoney(gross, deductions);
  return Math.max(0, net);
}

/**
 * Calculates outstanding balance: Net Payable - Paid Amount.
 */
export function calculateOutstanding(netPayable: number, paidAmount: number): number {
  const balance = subtractMoney(netPayable, paidAmount);
  return Math.max(0, balance);
}

/**
 * Calculates days overdue from a given due date. Returns 0 if not overdue.
 */
export function calculateOverdueDays(dueDate: string, referenceDate?: string): number {
  const due = new Date(dueDate).getTime();
  const ref = referenceDate ? new Date(referenceDate).getTime() : Date.now();

  if (isNaN(due) || isNaN(ref)) return 0;

  const diffMs = ref - due;
  if (diffMs <= 0) return 0;

  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Classifies an invoice into an overdue aging bucket.
 */
export function calculateAgingBucket(dueDate: string, referenceDate?: string): AgingBucket {
  const days = calculateOverdueDays(dueDate, referenceDate);

  if (days === 0) return "CURRENT";
  if (days <= 30) return "DAYS_1_30";
  if (days <= 60) return "DAYS_31_60";
  if (days <= 90) return "DAYS_61_90";
  return "DAYS_90_PLUS";
}

/**
 * Calculates overall collection efficiency rate percentage.
 */
export function calculateCollectionRate(billed: number, collected: number): number {
  if (billed <= 0) return 0;
  const rate = (collected / billed) * 100;
  return Math.round(rate * 10) / 10;
}

/**
 * Aggregates invoices into aging bucket summaries.
 */
export function compileAgingBuckets(
  invoices: { dueDate: string; outstandingAmount: number }[],
  referenceDate?: string
): AgingBucketSummary[] {
  const buckets: Record<
    AgingBucket,
    { label: string; amount: number; invoiceCount: number }
  > = {
    CURRENT: { label: "Current (Not Overdue)", amount: 0, invoiceCount: 0 },
    DAYS_1_30: { label: "1–30 Days Overdue", amount: 0, invoiceCount: 0 },
    DAYS_31_60: { label: "31–60 Days Overdue", amount: 0, invoiceCount: 0 },
    DAYS_61_90: { label: "61–90 Days Overdue", amount: 0, invoiceCount: 0 },
    DAYS_90_PLUS: { label: "90+ Days Overdue", amount: 0, invoiceCount: 0 },
  };

  let totalOutstanding = 0;

  invoices.forEach((inv) => {
    if (inv.outstandingAmount > 0) {
      const bucket = calculateAgingBucket(inv.dueDate, referenceDate);
      buckets[bucket].amount = addMoney(buckets[bucket].amount, inv.outstandingAmount);
      buckets[bucket].invoiceCount++;
      totalOutstanding = addMoney(totalOutstanding, inv.outstandingAmount);
    }
  });

  return (Object.keys(buckets) as AgingBucket[]).map((key) => {
    const item = buckets[key];
    const percentage = totalOutstanding > 0 ? Math.round((item.amount / totalOutstanding) * 100) : 0;
    return {
      bucket: key,
      label: item.label,
      amount: item.amount,
      invoiceCount: item.invoiceCount,
      percentage,
    };
  });
}
