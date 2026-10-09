/**
 * CampusOS Documents & Digital Records — Comprehensive Test Suite
 * Validates domain contracts, pure calculators, document lifecycle transitions,
 * verification queues, checklist evaluations, certificate templates, request pipelines,
 * digital credentials authentication, institutional records catalog, and role-based permissions.
 */

import {
  documentsService,
  documentCategoriesService,
  documentVerificationService,
  documentUploadService,
  certificateTemplatesService,
  certificateRequestsService,
  certificatesService,
  institutionalRecordsService,
  documentReportsService,
} from "../services";

import {
  calculateVerificationRate,
  calculateRejectionRate,
  calculateDocumentCompletionRate,
  calculatePendingVerificationCount,
  calculateExpiredDocumentCount,
  calculateExpiringDocumentCount,
  calculateCertificateApprovalRate,
  calculateCertificateIssuanceRate,
  calculateAverageVerificationTime,
  calculateCategoryDistribution,
  calculateExpiryBreakdown,
  getDocumentExpiryStatus,
} from "../services/document-calculator";

import {
  DocumentStatus,
  DocumentCategoryCode,
  DocumentOwnerType,
  DocumentExpiryStatus,
  CertificateType,
  CertificateTemplateStatus,
  CertificateRequestStatus,
  IssuedCertificateStatus,
  InstitutionalRecordStatus,
  ConfidentialityLevel,
  VerificationPriority,
  DocumentItem,
  CertificateRequest,
} from "@campusos/types";

import { DEMO_PERSONAS } from "../mocks/auth.mock";

export async function runDocumentsModuleTests(): Promise<{
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
    // 1. Executive Dashboard Telemetry
    // ==========================================
    const dashRes = await documentReportsService.getDashboardSummary();
    assert(dashRes.success === true, "1. Documents dashboard telemetry returns success");
    assert(dashRes.data.totalDocuments >= 10, "1. Total registered documents tracked correctly");
    assert(dashRes.data.verifiedDocuments > 0, "1. Verified documents count tracked");
    assert(dashRes.data.verificationRate > 0, "1. Verification rate percentage calculated");
    assert(dashRes.data.certificateRequests > 0, "1. Certificate requests tracked");
    assert(dashRes.data.averageVerificationHours > 0, "1. Average verification SLA hours tracked");
    assert(dashRes.data.categoryDistribution.length >= 5, "1. Category distribution breakdown populated");
    assert(dashRes.data.expiryBreakdown.valid >= 0, "1. Expiry radar breakdown computed");

    // ==========================================
    // 2. Centralized Pure Arithmetic Calculators
    // ==========================================
    // Verification Rate
    const mockCalcDocs: Partial<DocumentItem>[] = [
      { id: "d1", status: DocumentStatus.VERIFIED, uploadedAt: "2026-08-01T10:00:00Z", verifiedAt: "2026-08-02T10:00:00Z", category: DocumentCategoryCode.ACADEMIC },
      { id: "d2", status: DocumentStatus.VERIFIED, uploadedAt: "2026-08-01T10:00:00Z", verifiedAt: "2026-08-02T16:00:00Z", category: DocumentCategoryCode.IDENTITY },
      { id: "d3", status: DocumentStatus.UNDER_REVIEW, uploadedAt: "2026-08-01T10:00:00Z", category: DocumentCategoryCode.PLACEMENT },
      { id: "d4", status: DocumentStatus.REJECTED, uploadedAt: "2026-08-01T10:00:00Z", category: DocumentCategoryCode.FINANCIAL },
    ];

    const vRate = calculateVerificationRate(mockCalcDocs as DocumentItem[]);
    assert(vRate === 50, `2. calculateVerificationRate(2 verified / 4 processable) = 50% (got ${vRate})`);

    const rRate = calculateRejectionRate(mockCalcDocs as DocumentItem[]);
    assert(rRate === 25, `2. calculateRejectionRate(1 rejected / 4 processable) = 25% (got ${rRate})`);

    // Document Completion Rate
    const compRate1 = calculateDocumentCompletionRate(5, 4);
    assert(compRate1 === 80, `2. calculateDocumentCompletionRate(5, 4) = 80% (got ${compRate1})`);
    const compRateZero = calculateDocumentCompletionRate(0, 0);
    assert(compRateZero === 100, "2. calculateDocumentCompletionRate handles zero required as 100%");

    // Pending Verification Count
    const pendCount = calculatePendingVerificationCount(mockCalcDocs as DocumentItem[]);
    assert(pendCount === 1, `2. calculatePendingVerificationCount computes 1 under review (got ${pendCount})`);

    // Average Verification Time in Hours
    const avgHours = calculateAverageVerificationTime(mockCalcDocs as DocumentItem[]);
    assert(avgHours === 27, `2. calculateAverageVerificationTime avg(24h, 30h) = 27h (got ${avgHours})`);

    // Expiry Status Determinations
    const refDate = "2026-10-02T00:00:00.000Z";
    const expNull = getDocumentExpiryStatus(null, refDate);
    assert(expNull === DocumentExpiryStatus.NO_EXPIRY, "2. getDocumentExpiryStatus(null) = NO_EXPIRY");

    const expPast = getDocumentExpiryStatus("2026-09-15", refDate);
    assert(expPast === DocumentExpiryStatus.EXPIRED, "2. getDocumentExpiryStatus(past date) = EXPIRED");

    const exp7d = getDocumentExpiryStatus("2026-10-06", refDate);
    assert(exp7d === DocumentExpiryStatus.EXPIRING_7_DAYS, "2. getDocumentExpiryStatus(in 4 days) = EXPIRING_7_DAYS");

    const exp30d = getDocumentExpiryStatus("2026-10-25", refDate);
    assert(exp30d === DocumentExpiryStatus.EXPIRING_30_DAYS, "2. getDocumentExpiryStatus(in 23 days) = EXPIRING_30_DAYS");

    const exp90d = getDocumentExpiryStatus("2026-12-15", refDate);
    assert(exp90d === DocumentExpiryStatus.EXPIRING_90_DAYS, "2. getDocumentExpiryStatus(in 74 days) = EXPIRING_90_DAYS");

    const expValid = getDocumentExpiryStatus("2027-10-01", refDate);
    assert(expValid === DocumentExpiryStatus.VALID, "2. getDocumentExpiryStatus(in 364 days) = VALID");

    const testExpDocs: Partial<DocumentItem>[] = [
      { id: "d1", expiryDate: "2026-09-01" },
      { id: "d2", expiryDate: "2026-10-06" },
      { id: "d3", expiryDate: "2027-10-01" },
      { id: "d4", category: DocumentCategoryCode.IDENTITY },
    ];
    const expCount = calculateExpiredDocumentCount(testExpDocs as DocumentItem[], refDate);
    assert(expCount === 1, "2. calculateExpiredDocumentCount finds 1 expired");
    const expSoonCount = calculateExpiringDocumentCount(testExpDocs as DocumentItem[], 30, refDate);
    assert(expSoonCount === 1, "2. calculateExpiringDocumentCount finds 1 expiring within 30d");
    const catDist = calculateCategoryDistribution(testExpDocs as DocumentItem[]);
    assert(Array.isArray(catDist), "2. calculateCategoryDistribution returns array");
    const expBreakdown = calculateExpiryBreakdown(testExpDocs as DocumentItem[], refDate);
    assert(expBreakdown.expired === 1, "2. calculateExpiryBreakdown computes expired count");

    // Certificate Approval & Issuance Rates
    const mockReqs: Partial<CertificateRequest>[] = [
      { id: "r1", status: CertificateRequestStatus.APPROVED },
      { id: "r2", status: CertificateRequestStatus.ISSUED },
      { id: "r3", status: CertificateRequestStatus.REJECTED },
      { id: "r4", status: CertificateRequestStatus.SUBMITTED },
    ];
    const certAppRate = calculateCertificateApprovalRate(mockReqs as CertificateRequest[]);
    assert(certAppRate === 66.7, `2. calculateCertificateApprovalRate(2/3 resolved) = 66.7% (got ${certAppRate})`);

    const certIssueRate = calculateCertificateIssuanceRate(mockReqs as CertificateRequest[]);
    assert(certIssueRate === 25, `2. calculateCertificateIssuanceRate(1/4 non-draft) = 25% (got ${certIssueRate})`);

    // ==========================================
    // 3. Document Categories Catalog
    // ==========================================
    const catsRes = await documentCategoriesService.listCategories();
    assert(catsRes.success === true, "3. listCategories returns success");
    assert(catsRes.data.length >= 10, "3. All 10+ standard document categories configured");

    const identityCat = await documentCategoriesService.getCategoryByCode(DocumentCategoryCode.IDENTITY);
    assert(identityCat.data?.required === true, "3. Identity category marked mandatory");
    assert(identityCat.data?.verificationRequired === true, "3. Identity requires verification");
    assert(identityCat.data?.expiryRequired === true, "3. Identity category requires expiry monitoring");

    const academicCat = await documentCategoriesService.getCategoryByCode(DocumentCategoryCode.ACADEMIC);
    assert(academicCat.data?.applicableDocumentTypes.includes("10th Standard Marksheet"), "3. Academic includes 10th marksheet");
    assert(academicCat.data?.applicableDocumentTypes.includes("12th Standard Marksheet"), "3. Academic includes 12th marksheet");

    // Create New Category
    const newCatRes = await documentCategoriesService.createCategory({
      name: "Research Grants & Patents",
      code: DocumentCategoryCode.OTHER,
      description: "Intellectual property filings, patents, and sponsored grants.",
      required: false,
      applicableRoles: ["FACULTY"],
      applicableDocumentTypes: ["Patent Application", "Grant Award Letter"],
      verificationRequired: true,
      expiryRequired: false,
    });
    assert(newCatRes.success === true, "3. createCategory successfully creates new category");
    assert(newCatRes.data.id.startsWith("cat-"), "3. New category assigned canonical ID");

    // ==========================================
    // 4. Document Vault & Lifecycle Transitions
    // ==========================================
    // List all
    const allDocsRes = await documentsService.listDocuments();
    assert(allDocsRes.success === true, "4. listDocuments returns success");
    assert(allDocsRes.data.length >= 10, "4. Mock documents seeded correctly");

    // Owner filtering
    const aaravDocs = await documentsService.getDocumentsByOwner("stu-001");
    assert(aaravDocs.success === true, "4. getDocumentsByOwner returns success");
    assert(aaravDocs.data.length >= 3, "4. Student Aarav Patel has 3+ documents in vault");

    // Upload New Document
    const uploadRes = await documentsService.uploadDocument({
      name: "TNEA Engineering Admission Allotment Order 2024",
      category: DocumentCategoryCode.ADMISSION,
      documentType: "TNEA Allotment Order",
      ownerType: DocumentOwnerType.STUDENT,
      ownerId: "stu-001",
      ownerName: "Aarav Patel",
      ownerRollNumber: "24CSE0101",
      ownerDepartment: "Computer Science & Engineering",
      confidentiality: ConfidentialityLevel.INTERNAL,
      documentNumber: "TNEA-2024-ALLOC-9921",
      issuingAuthority: "Directorate of Technical Education, Tamil Nadu",
      issueDate: "2024-07-28",
      priority: VerificationPriority.NORMAL,
    });
    assert(uploadRes.success === true, "4. uploadDocument creates new record");
    assert(uploadRes.data.status === DocumentStatus.UPLOADED, "4. Newly uploaded document status is UPLOADED");
    assert(uploadRes.data.activityTimeline.length >= 1, "4. Upload action recorded in activity timeline");

    // Submit for Verification
    const submitRes = await documentsService.submitForVerification(uploadRes.data.id);
    assert(submitRes.data.status === DocumentStatus.UNDER_REVIEW, "4. submitForVerification transitions status to UNDER_REVIEW");

    // Update Metadata
    const updateMetaRes = await documentsService.updateDocumentMetadata(uploadRes.data.id, {
      documentNumber: "TNEA-2024-ALLOC-9921-REVISED",
    });
    assert(updateMetaRes.data.documentNumber === "TNEA-2024-ALLOC-9921-REVISED", "4. updateDocumentMetadata modifies fields");

    // ==========================================
    // 5. Verification Desk & Review Workflows
    // ==========================================
    const queueRes = await documentVerificationService.listVerificationQueue();
    assert(queueRes.success === true, "5. listVerificationQueue returns success");
    assert(queueRes.data.length >= 2, "5. Verification queue contains unverified records");

    // Start Verification Review
    const testDocId = uploadRes.data.id;
    const startReviewRes = await documentVerificationService.startVerification(
      testDocId,
      "user-super-admin-01",
      "Dr. Arvind Swaminathan (Registrar)"
    );
    assert(startReviewRes.data.assignedReviewerName === "Dr. Arvind Swaminathan (Registrar)", "5. Reviewer assigned to document");

    // Reject Document (Requires Reason)
    let threwWithoutReason = false;
    try {
      await documentVerificationService.rejectDocument(testDocId, "", "Dr. Arvind Swaminathan");
    } catch {
      threwWithoutReason = true;
    }
    assert(threwWithoutReason === true, "5. rejectDocument enforces mandatory rejection reason");

    const rejectRes = await documentVerificationService.rejectDocument(
      testDocId,
      "Official allotment stamp unreadable; upload original high resolution scan.",
      "Dr. Arvind Swaminathan"
    );
    assert(rejectRes.data.status === DocumentStatus.REJECTED, "5. rejectDocument transitions status to REJECTED");
    assert(Boolean(rejectRes.data.rejectionReason), "5. Official rejection reason persisted");

    // Verify Document
    const verifyRes = await documentVerificationService.verifyDocument(
      testDocId,
      "Dr. Arvind Swaminathan",
      "Resubmitted allotment order authenticated against DOTE portal."
    );
    assert(verifyRes.data.status === DocumentStatus.VERIFIED, "5. verifyDocument transitions status to VERIFIED");
    assert(Boolean(verifyRes.data.verifiedAt), "5. verifiedAt timestamp populated");
    assert(verifyRes.data.verifiedBy === "Dr. Arvind Swaminathan", "5. verifiedBy signatory set");

    // Request Re-upload
    const reuploadRes = await documentVerificationService.requestReupload(
      testDocId,
      "Please upload reverse page with counter-signature.",
      "Dr. Arvind Swaminathan"
    );
    assert(reuploadRes.data.status === DocumentStatus.REJECTED, "5. requestReupload sets status to REJECTED with instructions");

    // ==========================================
    // 6. Certificate Templates Management
    // ==========================================
    const tmplsRes = await certificateTemplatesService.listTemplates();
    assert(tmplsRes.success === true, "6. listTemplates returns success");
    assert(tmplsRes.data.length >= 4, "6. Standard certificate templates loaded");
    assert(
      tmplsRes.data[0].status === CertificateTemplateStatus.ACTIVE ||
      tmplsRes.data[0].status === CertificateTemplateStatus.DRAFT,
      "6. Template status conforms to CertificateTemplateStatus"
    );

    const bonafideTmpl = tmplsRes.data.find((t) => t.certificateType === CertificateType.BONAFIDE);
    assert(Boolean(bonafideTmpl), "6. Bonafide certificate template exists");
    assert(bonafideTmpl?.fields.some((f) => f.name === "student_name"), "6. Bonafide template contains student_name field");
    assert(bonafideTmpl?.fields.some((f) => f.name === "roll_number"), "6. Bonafide template contains roll_number field");

    // Create Template
    const createTmplRes = await certificateTemplatesService.createTemplate({
      templateName: "Merit Scholarship Certificate",
      certificateType: CertificateType.OTHER,
      description: "Annual academic excellence scholarship certification.",
      applicableAudience: ["STUDENT"],
      fields: [
        { id: "f-name", name: "student_name", label: "Student Name", type: "SYSTEM_VARIABLE", required: true },
        { id: "f-cgpa", name: "cgpa", label: "CGPA", type: "NUMBER", required: true },
      ],
    });
    assert(createTmplRes.success === true, "6. createTemplate returns success");
    assert(createTmplRes.data.version === "1.0", "6. Newly created template starts at v1.0");

    // ==========================================
    // 7. Certificate Requests Pipeline
    // ==========================================
    const reqsRes = await certificateRequestsService.listRequests();
    assert(reqsRes.success === true, "7. listRequests returns success");
    assert(reqsRes.data.length >= 3, "7. Seeded certificate requests loaded");

    // Submit New Student Request
    const createReqRes = await certificateRequestsService.createRequest({
      studentId: "stu-001",
      studentName: "Aarav Patel",
      rollNumber: "24CSE0101",
      program: "B.Tech Computer Science & Engineering",
      department: "Computer Science & Engineering",
      certificateType: CertificateType.BONAFIDE,
      templateId: "tmpl-bonafide-01",
      templateName: "Institutional Student Bonafide Certificate",
      purpose: "Bank of Baroda Education Loan Interest Subsidy Verification",
    });
    assert(createReqRes.success === true, "7. createRequest returns success");
    assert(createReqRes.data.status === CertificateRequestStatus.SUBMITTED, "7. New request status is SUBMITTED");
    assert(createReqRes.data.requestId.startsWith("REQ-2026-"), "7. Request assigned standardized tracking ID");

    const newReqId = createReqRes.data.id;

    // Approve Request
    const approveReqRes = await certificateRequestsService.approveRequest(
      newReqId,
      "user-super-admin-01",
      "Dr. Arvind Swaminathan (Registrar)",
      "Accounts clearance and enrollment confirmed."
    );
    assert(approveReqRes.data.status === CertificateRequestStatus.APPROVED, "7. approveRequest transitions to APPROVED");

    // Issue Digital Certificate from Request
    const issueCertRes = await certificateRequestsService.issueCertificateForRequest(
      newReqId,
      "Office of the Registrar"
    );
    assert(issueCertRes.success === true, "7. issueCertificateForRequest returns success");
    assert(issueCertRes.data.status === IssuedCertificateStatus.ISSUED, "7. Issued certificate status is ISSUED");
    assert(issueCertRes.data.certificateNumber.startsWith("CAMPUSOS/CERT/2026/"), "7. Formatted certificate number generated");
    assert(Boolean(issueCertRes.data.qrVerificationUrl), "7. QR verification URL generated");
    assert(issueCertRes.data.digitalSignatureHash.startsWith("SHA256:"), "7. Cryptographic SHA256 integrity hash applied");

    // Check request updated to ISSUED
    const updatedReqRes = await certificateRequestsService.getRequestById(newReqId);
    assert(updatedReqRes.data?.status === CertificateRequestStatus.ISSUED, "7. Parent request status updated to ISSUED");

    // Reject Request (with reason)
    const testRejectReq = await certificateRequestsService.createRequest({
      studentId: "stu-003",
      studentName: "Rohan Verghese",
      rollNumber: "24CSE0103",
      certificateType: CertificateType.COURSE_COMPLETION,
      templateId: "tmpl-course-comp-01",
      templateName: "Course Completion",
      purpose: "Premature issuance",
    });
    const rejReqRes = await certificateRequestsService.rejectRequest(
      testRejectReq.data.id,
      "Candidate in Semester 5; incomplete credits.",
      "user-faculty-01",
      "Dr. Rajesh Sharma"
    );
    assert(rejReqRes.data.status === CertificateRequestStatus.REJECTED, "7. rejectRequest transitions to REJECTED");
    assert(Boolean(rejReqRes.data.rejectionReason), "7. Rejection reason recorded in request");

    // ==========================================
    // 8. Issued Certificates & Verification Lookup
    // ==========================================
    const certsRes = await certificatesService.listIssuedCertificates();
    assert(certsRes.success === true, "8. listIssuedCertificates returns success");
    assert(certsRes.data.length >= 2, "8. Issued certificates loaded");

    // Verify Certificate by Number
    const verifyCertRes = await certificatesService.verifyCertificate("CAMPUSOS/CERT/2026/0041");
    assert(verifyCertRes.success === true, "8. verifyCertificate lookup returns success");
    assert(verifyCertRes.data !== null, "8. Valid certificate found by code");
    assert(verifyCertRes.data?.recipientName === "Aarav Patel", "8. Recipient authenticated as Aarav Patel");

    // Verify Non-existent Certificate returns null
    const verifyFake = await certificatesService.verifyCertificate("FAKE-INVALID-CERT-9999");
    assert(verifyFake.data === null, "8. verifyCertificate returns null for invalid certificate number");

    // Revoke Certificate
    const revokeRes = await certificatesService.revokeCertificate(
      "cert-bnf-2026-0041",
      "Superseded by updated degree certificate."
    );
    assert(revokeRes.data.status === IssuedCertificateStatus.REVOKED, "8. revokeCertificate transitions status to REVOKED");
    assert(Boolean(revokeRes.data.revocationReason), "8. Revocation reason recorded");

    // ==========================================
    // 9. Institutional Records & Compliance
    // ==========================================
    const recsRes = await institutionalRecordsService.listRecords();
    assert(recsRes.success === true, "9. listRecords returns success");
    assert(recsRes.data.length >= 5, "9. Institutional gazettes and regulatory approvals loaded");

    const nbaRecord = recsRes.data.find((r) => r.code === "NBA-CSE-2024-2027");
    assert(Boolean(nbaRecord), "9. NBA Tier-1 accreditation record present");
    assert(nbaRecord?.confidentiality === ConfidentialityLevel.PUBLIC, "9. NBA accreditation marked PUBLIC");
    assert(nbaRecord?.status === InstitutionalRecordStatus.ACTIVE, "9. NBA accreditation status is ACTIVE");

    const confidentialRecord = recsRes.data.find((r) => r.confidentiality === ConfidentialityLevel.RESTRICTED);
    assert(Boolean(confidentialRecord), "9. Restricted governing council minutes cataloged");

    // Create New Institutional Record
    const newInstRes = await institutionalRecordsService.createRecord({
      recordName: "Campus Safety & Environmental Audit Compliance 2026-27",
      code: "AUD-ENV-2026",
      category: "Policies & Governance",
      ownerDepartment: "Estate & Physical Infrastructure",
      confidentiality: ConfidentialityLevel.INTERNAL,
      validUntil: "2027-12-31",
      referenceNumber: "ENV/TNPCB/2026/014",
    });
    assert(newInstRes.success === true, "9. createRecord returns success");
    assert(newInstRes.data.id.startsWith("rec-inst-"), "9. Record assigned canonical ID");

    // ==========================================
    // 10. Document Upload Validation Logic
    // ==========================================
    // Valid File
    const validUpload = documentUploadService.validateUpload(
      { name: "tenth_marksheet.pdf", size: 2 * 1024 * 1024, type: "application/pdf" },
      { documentName: "10th Marksheet", category: "ACADEMIC", documentType: "10th Standard Marksheet" }
    );
    assert(validUpload.valid === true, "10. validateUpload passes for standard PDF");

    // Oversized File (> 15MB)
    const oversizedUpload = documentUploadService.validateUpload(
      { name: "huge_video.pdf", size: 20 * 1024 * 1024, type: "application/pdf" },
      { documentName: "Large File", category: "ACADEMIC", documentType: "Marksheet" }
    );
    assert(oversizedUpload.valid === false, "10. validateUpload rejects files exceeding 15MB");

    // Disallowed Format (.exe)
    const invalidTypeUpload = documentUploadService.validateUpload(
      { name: "script.exe", size: 1024, type: "application/x-msdownload" },
      { documentName: "Malicious File", category: "ACADEMIC", documentType: "Marksheet" }
    );
    assert(invalidTypeUpload.valid === false, "10. validateUpload rejects unsupported file types");

    // Expiry before Issue Date
    const invalidDatesUpload = documentUploadService.validateUpload(
      { name: "doc.pdf", size: 1024, type: "application/pdf" },
      { documentName: "Date Test", category: "IDENTITY", documentType: "ID", issueDate: "2026-10-01", expiryDate: "2026-09-01" }
    );
    assert(invalidDatesUpload.valid === false, "10. validateUpload rejects expiry dates preceding issue date");

    // ==========================================
    // 11. Role-Based Permissions & Guardrails
    // ==========================================
    const student = DEMO_PERSONAS.find((p) => p.role === "STUDENT");
    const registrar = DEMO_PERSONAS.find((p) => p.role === "SUPER_ADMIN");
    const hod = DEMO_PERSONAS.find((p) => p.role === "HOD");
    const faculty = DEMO_PERSONAS.find((p) => p.role === "FACULTY");

    assert(student?.role === "STUDENT", "11. Student persona verified");
    assert(student?.permissions.includes("documents:self:read"), "11. Student authorized to read own documents");
    assert(!student?.permissions.includes("documents:verify"), "11. Student NOT permitted to verify documents");

    assert(registrar?.role === "SUPER_ADMIN", "11. Super Admin / Registrar persona verified");
    assert(registrar?.permissions.includes("*"), "11. Registrar has complete governance authorization");

    assert(hod?.role === "HOD", "11. HOD persona verified for department academic oversight");
    assert(faculty?.role === "FACULTY", "11. Faculty persona verified for personal teaching credentials");

  } catch (err: any) {
    results.push({ testName: "Global Execution Catch", passed: false, message: err.message });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

if (typeof process !== "undefined" && process.argv[1]?.includes("documents-module.test")) {
  runDocumentsModuleTests().then((res) => {
    console.log(`\n======================================================`);
    console.log(`CampusOS Documents & Digital Records Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`======================================================`);
    res.results.forEach((r) => {
      console.log(`${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`);
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
