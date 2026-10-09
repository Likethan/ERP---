import { ApiResponse, DocumentsDashboardSummary, DocumentStatus } from "@campusos/types";
import { documentsService } from "./documents.service";
import { certificateRequestsService } from "./certificate-requests.service";
import { certificatesService } from "./certificates.service";
import {
  calculateVerificationRate,
  calculateRejectionRate,
  calculatePendingVerificationCount,
  calculateExpiringDocumentCount,
  calculateAverageVerificationTime,
  calculateCategoryDistribution,
  calculateExpiryBreakdown,
} from "./document-calculator";

class DocumentReportsService {
  async getDashboardSummary(): Promise<ApiResponse<DocumentsDashboardSummary>> {
    const docsRes = await documentsService.listDocuments();
    const reqsRes = await certificateRequestsService.listRequests();
    const certsRes = await certificatesService.listIssuedCertificates();

    const docs = docsRes.data || [];
    const reqs = reqsRes.data || [];
    const certs = certsRes.data || [];

    const totalDocs = docs.length;
    const verifiedDocs = docs.filter((d) => d.status === DocumentStatus.VERIFIED).length;
    const pendingDocs = calculatePendingVerificationCount(docs);
    const rejectedDocs = docs.filter((d) => d.status === DocumentStatus.REJECTED).length;
    const missingDocs = docs.filter((d) => d.status === DocumentStatus.MISSING).length;
    const expiringDocs = calculateExpiringDocumentCount(docs, 30);

    const pendingReqs = reqs.filter(
      (r) => r.status === "SUBMITTED" || r.status === "UNDER_REVIEW"
    ).length;

    const verificationRate = calculateVerificationRate(docs);
    const rejectionRate = calculateRejectionRate(docs);
    const averageHours = calculateAverageVerificationTime(docs);
    const categoryDistribution = calculateCategoryDistribution(docs);
    const expiryBreakdown = calculateExpiryBreakdown(docs);

    // Dynamic metrics
    const uploadedThisMonth = docs.filter((d) => {
      const uploadDate = new Date(d.uploadedAt);
      return uploadDate.getFullYear() === 2026 && uploadDate.getMonth() >= 7; // recent
    }).length;

    const issuedThisMonth = certs.filter((c) => {
      const issueDate = new Date(c.issueDate);
      return issueDate.getFullYear() === 2026 && issueDate.getMonth() >= 7;
    }).length;

    const summary: DocumentsDashboardSummary = {
      totalDocuments: totalDocs,
      verifiedDocuments: verifiedDocs,
      pendingVerification: pendingDocs,
      rejectedDocuments: rejectedDocs,
      missingDocuments: missingDocs,
      expiringDocuments: expiringDocs,
      certificateRequests: reqs.length,
      pendingCertificateRequests: pendingReqs,
      verificationRate,
      rejectionRate,
      averageVerificationHours: averageHours,
      documentsUploadedThisMonth: uploadedThisMonth,
      certificatesIssuedThisMonth: issuedThisMonth,
      categoryDistribution,
      expiryBreakdown,
    };

    return { success: true, data: summary };
  }
}

export const documentReportsService = new DocumentReportsService();
