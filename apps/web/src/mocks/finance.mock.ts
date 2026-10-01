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
  status: "PAID" | "PARTIALLY_PAID" | "ISSUED" | "OVERDUE" | "CANCELLED";
}

export interface PaymentTransactionItem {
  id: string;
  transactionRef: string;
  receiptNumber: string;
  studentName: string;
  rollNumber: string;
  invoiceNumber: string;
  amount: number;
  paymentMode: "UPI" | "NET_BANKING" | "NEFT_RTGS" | "DEMAND_DRAFT" | "CASH_COUNTER";
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

export const MOCK_FEE_STRUCTURES: FeeStructureItem[] = [
  {
    id: "fs-btech-2026",
    name: "B.Tech Standard Tuition & Academic Fee Schedule 2026-27",
    program: "B.Tech Computer Science & Engineering",
    academicYear: "2026-2027",
    totalAnnualFee: 145000,
    components: [
      { title: "Academic Tuition Fee", amount: 95000, mandatory: true },
      { title: "Laboratory & Computing Levy", amount: 20000, mandatory: true },
      { title: "Library & Digital Journal Access", amount: 8000, mandatory: true },
      { title: "Examination & Assessment Fee", amount: 12000, mandatory: true },
      { title: "Campus Development & Student Welfare", amount: 10000, mandatory: true },
    ],
    status: "ACTIVE",
  },
  {
    id: "fs-hostel-2026",
    name: "Residential Hostel & Mess Levy 2026-27",
    program: "All Programs (Residential Students)",
    academicYear: "2026-2027",
    totalAnnualFee: 78000,
    components: [
      { title: "Hostel Room Rent (Double Occupancy)", amount: 38000, mandatory: true },
      { title: "Central Dining & Mess Facility", amount: 36000, mandatory: true },
      { title: "Hostel Amenities & Maintenance", amount: 4000, mandatory: true },
    ],
    status: "ACTIVE",
  },
];

export const MOCK_INVOICES: InvoiceItem[] = [
  {
    id: "inv-2026-0891",
    invoiceNumber: "INV-2026-0891",
    studentId: "stu-24cse0101",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech CSE",
    issueDate: "2026-08-01",
    dueDate: "2026-08-30",
    totalAmount: 145000,
    paidAmount: 145000,
    balanceAmount: 0,
    status: "PAID",
  },
  {
    id: "inv-2026-0892",
    invoiceNumber: "INV-2026-0892",
    studentId: "stu-24cse0102",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    program: "B.Tech CSE",
    issueDate: "2026-08-01",
    dueDate: "2026-08-30",
    totalAmount: 145000,
    paidAmount: 145000,
    balanceAmount: 0,
    status: "PAID",
  },
  {
    id: "inv-2026-0893",
    invoiceNumber: "INV-2026-0893",
    studentId: "stu-24cse0103",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    program: "B.Tech CSE",
    issueDate: "2026-08-01",
    dueDate: "2026-08-30",
    totalAmount: 145000,
    paidAmount: 110000,
    balanceAmount: 35000,
    status: "PARTIALLY_PAID",
  },
];

export const MOCK_PAYMENTS: PaymentTransactionItem[] = [
  {
    id: "pay-tx-01",
    transactionRef: "TXN-UPI-99881122",
    receiptNumber: "REC-2026-0912",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    invoiceNumber: "INV-2026-0891",
    amount: 145000,
    paymentMode: "UPI",
    paymentDate: "2026-08-14 11:24 AM",
    status: "SUCCESS",
  },
  {
    id: "pay-tx-02",
    transactionRef: "TXN-NET-77443311",
    receiptNumber: "REC-2026-0913",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    invoiceNumber: "INV-2026-0892",
    amount: 145000,
    paymentMode: "NET_BANKING",
    paymentDate: "2026-08-16 02:45 PM",
    status: "SUCCESS",
  },
];

export const MOCK_SCHOLARSHIPS: ScholarshipItem[] = [
  {
    id: "sch-01",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    scholarshipScheme: "University Merit Scholarship (Top 1% Rank)",
    sanctionAmount: 50000,
    disbursedAmount: 50000,
    academicYear: "2026-2027",
    status: "DISBURSED",
  },
  {
    id: "sch-02",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    scholarshipScheme: "State Women in Engineering Fellowship",
    sanctionAmount: 40000,
    disbursedAmount: 40000,
    academicYear: "2026-2027",
    status: "DISBURSED",
  },
];
