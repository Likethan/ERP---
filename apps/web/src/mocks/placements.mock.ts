export interface CompanyProfileItem {
  id: string;
  name: string;
  tier: "TIER_1_SUPER_DREAM" | "TIER_2_DREAM" | "TIER_3_MASS";
  industry: string;
  website: string;
  headquarters: string;
  hrContact: {
    name: string;
    email: string;
    phone: string;
  };
  activeDrivesCount: number;
  totalHiredAlumni: number;
  status: "ACTIVE" | "EMPANELLED" | "BLACKLISTED";
}

export interface JobDriveItem {
  id: string;
  companyName: string;
  roleTitle: string;
  packageLPA: number;
  driveDate: string;
  applicationDeadline: string;
  targetPrograms: string[];
  minimumCGPA: number;
  maxBacklogsAllowed: number;
  minAttendancePercent: number;
  location: string;
  totalApplicants: number;
  shortlistedCount: number;
  offersMadeCount: number;
  status: "APPLICATIONS_OPEN" | "SHORTLISTING" | "INTERVIEWS_ACTIVE" | "COMPLETED" | "DRAFT";
}

export interface PlacementOfferItem {
  id: string;
  studentName: string;
  rollNumber: string;
  program: string;
  companyName: string;
  designation: string;
  packageLPA: number;
  offerDate: string;
  acceptanceStatus: "ACCEPTED" | "PENDING_DECISION" | "DECLINED";
}

export const MOCK_COMPANIES: CompanyProfileItem[] = [
  {
    id: "comp-cisco",
    name: "Cisco Systems India",
    tier: "TIER_1_SUPER_DREAM",
    industry: "Enterprise Networking & Cloud Infrastructure",
    website: "https://www.cisco.com",
    headquarters: "Bengaluru, Karnataka",
    hrContact: {
      name: "Siddharth Verma",
      email: "siddharth.v@cisco.com",
      phone: "+91 80 4426 0000",
    },
    activeDrivesCount: 1,
    totalHiredAlumni: 42,
    status: "ACTIVE",
  },
  {
    id: "comp-msft",
    name: "Microsoft India R&D",
    tier: "TIER_1_SUPER_DREAM",
    industry: "Cloud & AI Software",
    website: "https://careers.microsoft.com",
    headquarters: "Hyderabad / Bengaluru",
    hrContact: {
      name: "Divya Nambiar",
      email: "divya.n@microsoft.com",
      phone: "+91 80 6787 0000",
    },
    activeDrivesCount: 1,
    totalHiredAlumni: 28,
    status: "ACTIVE",
  },
  {
    id: "comp-tcs",
    name: "Tata Consultancy Services (Digital)",
    tier: "TIER_2_DREAM",
    industry: "Global IT Consulting",
    website: "https://www.tcs.com",
    headquarters: "Mumbai, Maharashtra",
    hrContact: {
      name: "Arun K. Pillai",
      email: "arun.kp@tcs.com",
      phone: "+91 22 6778 9999",
    },
    activeDrivesCount: 1,
    totalHiredAlumni: 185,
    status: "ACTIVE",
  },
];

export const MOCK_JOB_DRIVES: JobDriveItem[] = [
  {
    id: "drive-cisco-2026",
    companyName: "Cisco Systems India",
    roleTitle: "Software Development Engineer — Core Network OS",
    packageLPA: 18.5,
    driveDate: "2026-10-08",
    applicationDeadline: "2026-10-04",
    targetPrograms: ["B.Tech CSE", "B.Tech AIML", "B.Tech ECE"],
    minimumCGPA: 8.0,
    maxBacklogsAllowed: 0,
    minAttendancePercent: 80,
    location: "Bengaluru Campus / Hybrid",
    totalApplicants: 142,
    shortlistedCount: 28,
    offersMadeCount: 4,
    status: "INTERVIEWS_ACTIVE",
  },
  {
    id: "drive-msft-2026",
    companyName: "Microsoft India R&D",
    roleTitle: "Cloud Solution & Systems Engineer",
    packageLPA: 24.0,
    driveDate: "2026-09-28",
    applicationDeadline: "2026-09-20",
    targetPrograms: ["B.Tech CSE", "B.Tech AIML"],
    minimumCGPA: 8.5,
    maxBacklogsAllowed: 0,
    minAttendancePercent: 85,
    location: "Bengaluru Technology Center",
    totalApplicants: 98,
    shortlistedCount: 14,
    offersMadeCount: 3,
    status: "COMPLETED",
  },
  {
    id: "drive-tcs-2026",
    companyName: "Tata Consultancy Services (Digital)",
    roleTitle: "Systems Associate / Digital Engineer",
    packageLPA: 7.5,
    driveDate: "2026-10-25",
    applicationDeadline: "2026-10-18",
    targetPrograms: ["B.Tech CSE", "B.Tech ECE", "B.Tech ME"],
    minimumCGPA: 7.0,
    maxBacklogsAllowed: 1,
    minAttendancePercent: 75,
    location: "Pan-India",
    totalApplicants: 215,
    shortlistedCount: 0,
    offersMadeCount: 0,
    status: "APPLICATIONS_OPEN",
  },
];

export const MOCK_OFFERS: PlacementOfferItem[] = [
  {
    id: "ofr-01",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    program: "B.Tech CSE",
    companyName: "Microsoft India R&D",
    designation: "Cloud Solution Engineer",
    packageLPA: 24.0,
    offerDate: "2026-09-29",
    acceptanceStatus: "ACCEPTED",
  },
  {
    id: "ofr-02",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech CSE",
    companyName: "Cisco Systems India",
    designation: "Software Development Engineer",
    packageLPA: 18.5,
    offerDate: "2026-09-28",
    acceptanceStatus: "ACCEPTED",
  },
  {
    id: "ofr-03",
    studentName: "Ananya Deshmukh",
    rollNumber: "24ECE0201",
    program: "B.Tech ECE",
    companyName: "Texas Instruments",
    designation: "Embedded Firmware Engineer",
    packageLPA: 16.0,
    offerDate: "2026-09-26",
    acceptanceStatus: "ACCEPTED",
  },
];
