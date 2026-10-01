export interface DocumentVaultItem {
  id: string;
  name: string;
  category: "ACADEMIC" | "IDENTITY" | "CERTIFICATES" | "FINANCIAL" | "LEGAL";
  uploadedBy: string;
  ownerName: string;
  ownerRollNumber?: string;
  uploadDate: string;
  fileSize: string;
  fileType: string;
  verified: boolean;
  status: "ACTIVE" | "PENDING_VERIFICATION" | "REJECTED";
}

export interface DocumentRequestItem {
  id: string;
  studentName: string;
  rollNumber: string;
  program: string;
  certificateType: "BONAFIDE" | "TRANSCRIPT" | "STUDY_CERTIFICATE" | "NO_OBJECTION" | "PROVISIONAL_DEGREE";
  purpose: string;
  requestedDate: string;
  status: "PENDING_APPROVAL" | "ISSUED" | "REJECTED";
  processedBy?: string;
}

export interface IssuedCertificateItem {
  id: string;
  certificateNumber: string;
  studentName: string;
  rollNumber: string;
  certificateType: string;
  issueDate: string;
  qrVerificationUrl: string;
  digitalSignatureHash: string;
  status: "VALID" | "REVOKED";
}

export const MOCK_DOCUMENTS: DocumentVaultItem[] = [
  {
    id: "doc-vault-01",
    name: "Higher Secondary Certificate (10+2 Marksheet)",
    category: "IDENTITY",
    uploadedBy: "Aarav Patel",
    ownerName: "Aarav Patel",
    ownerRollNumber: "24CSE0101",
    uploadDate: "2024-08-05",
    fileSize: "2.4 MB",
    fileType: "PDF",
    verified: true,
    status: "ACTIVE",
  },
  {
    id: "doc-vault-02",
    name: "Semester 4 Official Grade Sheet",
    category: "ACADEMIC",
    uploadedBy: "Office of the Controller of Examinations",
    ownerName: "Priya Sundaram",
    ownerRollNumber: "24CSE0102",
    uploadDate: "2026-07-01",
    fileSize: "1.1 MB",
    fileType: "PDF",
    verified: true,
    status: "ACTIVE",
  },
  {
    id: "doc-vault-03",
    name: "Annual Academic Fee Receipt #REC-2026-0912",
    category: "FINANCIAL",
    uploadedBy: "Accounts Department",
    ownerName: "Aarav Patel",
    ownerRollNumber: "24CSE0101",
    uploadDate: "2026-08-14",
    fileSize: "480 KB",
    fileType: "PDF",
    verified: true,
    status: "ACTIVE",
  },
];

export const MOCK_DOCUMENT_REQUESTS: DocumentRequestItem[] = [
  {
    id: "dreq-01",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    program: "B.Tech CSE",
    certificateType: "BONAFIDE",
    purpose: "Application for Education Loan Renewal at State Bank of India",
    requestedDate: "2026-09-28",
    status: "ISSUED",
    processedBy: "Registrar Office",
  },
  {
    id: "dreq-02",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    program: "B.Tech CSE",
    certificateType: "NO_OBJECTION",
    purpose: "Off-campus summer internship application",
    requestedDate: "2026-09-30",
    status: "PENDING_APPROVAL",
  },
];

export const MOCK_ISSUED_CERTIFICATES: IssuedCertificateItem[] = [
  {
    id: "cert-bnf-2026-0041",
    certificateNumber: "CAMPUSOS/CERT/2026/0041",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    certificateType: "Institutional Bonafide Certificate",
    issueDate: "2026-09-29",
    qrVerificationUrl: "https://verify.campusos.edu/cert/CAMPUSOS-2026-0041",
    digitalSignatureHash: "SHA256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    status: "VALID",
  },
  {
    id: "cert-trn-2026-0019",
    certificateNumber: "CAMPUSOS/CERT/2026/0019",
    studentName: "Priya Sundaram",
    rollNumber: "24CSE0102",
    certificateType: "Official Academic Transcript (Sem 1 - 4)",
    issueDate: "2026-07-15",
    qrVerificationUrl: "https://verify.campusos.edu/cert/CAMPUSOS-2026-0019",
    digitalSignatureHash: "SHA256:cb837617c0a76ef48cfef49c8112d7d8e6a10065b3240e34c1b183fd8b53cf52",
    status: "VALID",
  },
];
