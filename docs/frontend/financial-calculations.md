# CampusOS — Financial Calculations, Minor-Unit Arithmetic & Rounding Policies

This document specifies the exact numerical invariants and calculation formulas implemented by `financial-calculator.ts` to prevent precision drift and guarantee audit consistency across all finance screens.

---

## 1. Minor-Unit Integer Arithmetic (Zero Precision Drift)

In financial applications, binary floating-point representation (`0.1 + 0.2 = 0.30000000000000004`) causes unacceptable roundoff errors in multi-line transactions.

CampusOS converts all monetary values into minor units (paise: `1 INR = 100 paise`) internally before performing arithmetic, then converts back to decimal:

```typescript
// Addition
export function addMoney(a: number, b: number): number {
  return Math.round((a + Number.EPSILON) * 100 + (b + Number.EPSILON) * 100) / 100;
}

// Subtraction
export function subtractMoney(a: number, b: number): number {
  return Math.round((a + Number.EPSILON) * 100 - (b + Number.EPSILON) * 100) / 100;
}
```

---

## 2. Currency Formatting Standards

- **Symbol**: Indian Rupee (`₹`).
- **Locale**: English (India) (`en-IN`), using standard Indian numbering format (Lakhs and Crores, e.g., `₹1,25,000.00`).
- **Decimal Digits**: Always 2 decimal places.

```typescript
export function formatMoney(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}
```

---

## 3. Invoice Calculation Formulas

### A. Gross Total
$$\text{GrossAmount} = \sum_{i=1}^{n} \text{LineItemAmount}_i$$

### B. Net Payable
$$\text{NetPayable} = \max(0, \text{GrossAmount} - \text{ScholarshipDiscount} - \text{ConcessionDiscount} - \text{CreditAdjustments})$$

### C. Outstanding Balance
$$\text{OutstandingBalance} = \max(0, \text{NetPayable} - \text{PaidAmount})$$

### D. Invoice Status Transitions
- If $\text{PaidAmount} = 0$: `ISSUED` (or `OVERDUE` if $\text{CurrentDate} > \text{DueDate}$)
- If $0 < \text{PaidAmount} < \text{NetPayable}$: `PARTIALLY_PAID`
- If $\text{PaidAmount} \ge \text{NetPayable}$: `PAID`
- Manual Administrative Override: `CANCELLED`

---

## 4. Scholarship Impact Calculation

Scholarships support both percentage-based and fixed lump-sum concessions with optional maximum capping:

```typescript
export function calculateScholarshipImpact(
  grossAmount: number,
  scholarship: Scholarship
): { discountAmount: number; adjustedFee: number } {
  let discount = 0;
  if (scholarship.discountType === "PERCENTAGE") {
    discount = (grossAmount * scholarship.value) / 100;
    if (scholarship.maxDiscountAmount && scholarship.maxDiscountAmount > 0) {
      discount = Math.min(discount, scholarship.maxDiscountAmount);
    }
  } else {
    discount = scholarship.value;
  }
  discount = Math.min(discount, grossAmount);
  return {
    discountAmount: Math.round(discount),
    adjustedFee: Math.max(0, grossAmount - Math.round(discount)),
  };
}
```

---

## 5. Delinquency & Aging Buckets

Debt aging classifies overdue balances relative to the invoice `dueDate`:

$$\text{OverdueDays} = \max\left(0, \left\lfloor \frac{\text{CurrentDate} - \text{DueDate}}{86,400,000} \right\rfloor\right)$$

| Aging Bucket | Days Overdue | Severity Level | Color Representation |
| :--- | :--- | :--- | :--- |
| `CURRENT` | $\le 0$ days | Normal | Green (`emerald-500`) |
| `DAYS_1_30` | 1 – 30 days | Low Delinquency | Amber (`amber-500`) |
| `DAYS_31_60` | 31 – 60 days | Moderate Delinquency | Orange (`orange-500`) |
| `DAYS_61_90` | 61 – 90 days | Elevated Risk | Rose (`rose-500`) |
| `DAYS_90_PLUS`| $\ge 91$ days | Severe Default Risk | Red (`red-600`) |

---

## 6. Collection Rate Formula

$$\text{CollectionRate (\%)} = \begin{cases} 0 & \text{if Gross} = 0 \\ \min\left(100, \text{round}\left(\frac{\text{TotalCollected}}{\text{TotalBilled}} \times 100\right)\right) & \text{if Gross} > 0 \end{cases}$$
