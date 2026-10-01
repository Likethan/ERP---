export interface CampusMetricCard {
  label: string;
  value: string;
  change: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
  description: string;
  category: "ENROLLMENT" | "FINANCE" | "ATTENDANCE" | "PLACEMENT" | "ACADEMIC";
}

export interface OperationalAlertItem {
  id: string;
  level: "CRITICAL" | "WARNING" | "INFO";
  title: string;
  message: string;
  department: string;
  timestamp: string;
  actionHref?: string;
  actionText?: string;
}

export interface DepartmentKpiItem {
  department: string;
  facultyCount: number;
  studentsCount: number;
  avgAttendancePercent: number;
  avgCgpa: number;
  placementRatePercent: number;
  feeCollectionPercent: number;
}

export const MOCK_CAMPUS_METRICS: CampusMetricCard[] = [
  {
    label: "Total Enrolled Students",
    value: "2,280",
    change: { value: "+8.4% YoY", trend: "up" },
    description: "Active enrollment across UG & PG degree schemes",
    category: "ENROLLMENT",
  },
  {
    label: "Overall Campus Attendance",
    value: "87.6%",
    change: { value: "+1.2% this month", trend: "up" },
    description: "Consolidated lecture & lab presence across all semesters",
    category: "ATTENDANCE",
  },
  {
    label: "Annual Tuition Revenue",
    value: "₹31.2 Cr",
    change: { value: "92.4% collected", trend: "up" },
    description: "₹2.56 Cr outstanding across academic installments",
    category: "FINANCE",
  },
  {
    label: "Tier 1/2 Placement Rate",
    value: "84.2%",
    change: { value: "+5.6% vs 2025", trend: "up" },
    description: "Average CTC ₹12.4 LPA across accredited recruiters",
    category: "PLACEMENT",
  },
];

export const MOCK_OPERATIONAL_ALERTS: OperationalAlertItem[] = [
  {
    id: "alt-01",
    level: "CRITICAL",
    title: "Low Attendance Warning (18 Students <75%)",
    message: "18 students in 5th Sem CSE Sec B are currently falling below exam eligibility thresholds.",
    department: "Computer Science & Engineering",
    timestamp: "2 hours ago",
    actionHref: "/app/attendance",
    actionText: "Review Student Roster",
  },
  {
    id: "alt-02",
    level: "WARNING",
    title: "CIA-1 Marks Pending Submission (2 Faculty)",
    message: "Internal Assessment 1 marks for CS304 and ME401 await upload deadline in 48 hours.",
    department: "Examination Cell",
    timestamp: "Today, 09:15 AM",
    actionHref: "/app/examinations/marks",
    actionText: "Send Reminder",
  },
  {
    id: "alt-03",
    level: "INFO",
    title: "Hostel Occupancy at 94.2% Capacity",
    message: "Boys Hostel Block A has only 14 vacant beds remaining for the current academic session.",
    department: "Residential Facilities",
    timestamp: "Yesterday",
    actionHref: "/app/hostel",
    actionText: "View Allocations",
  },
];

export const MOCK_DEPARTMENT_KPIS: DepartmentKpiItem[] = [
  {
    department: "Computer Science & Engineering",
    facultyCount: 28,
    studentsCount: 720,
    avgAttendancePercent: 88.4,
    avgCgpa: 8.42,
    placementRatePercent: 92.5,
    feeCollectionPercent: 96.0,
  },
  {
    department: "Electronics & Communication",
    facultyCount: 22,
    studentsCount: 540,
    avgAttendancePercent: 89.1,
    avgCgpa: 8.25,
    placementRatePercent: 88.0,
    feeCollectionPercent: 94.5,
  },
  {
    department: "Mechanical Engineering",
    facultyCount: 18,
    studentsCount: 360,
    avgAttendancePercent: 85.2,
    avgCgpa: 7.90,
    placementRatePercent: 78.4,
    feeCollectionPercent: 91.0,
  },
  {
    department: "Information Technology",
    facultyCount: 16,
    studentsCount: 420,
    avgAttendancePercent: 87.0,
    avgCgpa: 8.15,
    placementRatePercent: 89.2,
    feeCollectionPercent: 93.8,
  },
];

export interface CohortDistributionItem {
  year: string;
  enrolled: number;
  retentionRate: number;
  avgAttendance: number;
  passPercentage: number;
}

export interface RiskRadarSummary {
  attendanceUnder75: number;
  feeOverdueHigh: number;
  cgpaUnder6: number;
  criticalDisciplinary: number;
  lastUpdated: string;
}

export const MOCK_COHORT_DATA: CohortDistributionItem[] = [
  { year: "1st Year (Batch 2026)", enrolled: 680, retentionRate: 98.4, avgAttendance: 91.2, passPercentage: 94.0 },
  { year: "2nd Year (Batch 2025)", enrolled: 610, retentionRate: 96.8, avgAttendance: 88.7, passPercentage: 89.5 },
  { year: "3rd Year (Batch 2024)", enrolled: 550, retentionRate: 95.2, avgAttendance: 86.4, passPercentage: 91.2 },
  { year: "4th Year (Batch 2023)", enrolled: 440, retentionRate: 94.9, avgAttendance: 84.1, passPercentage: 96.5 },
];

export const MOCK_RISK_RADAR: RiskRadarSummary = {
  attendanceUnder75: 48,
  feeOverdueHigh: 62,
  cgpaUnder6: 31,
  criticalDisciplinary: 3,
  lastUpdated: "Today at 05:30 PM",
};

