import { ApiResponse } from "@campusos/types";
import {
  CertificateRequest,
  CertificateRequestStatus,
  CertificateType,
  IssuedCertificate,
} from "@campusos/types";
import { MOCK_CERTIFICATE_REQUESTS } from "@/mocks/documents.mock";
import { certificatesService } from "./certificates.service";

class CertificateRequestsService {
  private requests: CertificateRequest[] = [...MOCK_CERTIFICATE_REQUESTS];

  async listRequests(filters?: {
    status?: string;
    studentId?: string;
    certificateType?: string;
    search?: string;
  }): Promise<ApiResponse<CertificateRequest[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.requests];

    if (filters) {
      if (filters.status && filters.status !== "ALL") {
        items = items.filter((r) => r.status === filters.status);
      }
      if (filters.studentId) {
        items = items.filter((r) => r.studentId === filters.studentId);
      }
      if (filters.certificateType && filters.certificateType !== "ALL") {
        items = items.filter(
          (r) => r.certificateType === filters.certificateType,
        );
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        items = items.filter(
          (r) =>
            r.requestId.toLowerCase().includes(q) ||
            r.studentName.toLowerCase().includes(q) ||
            r.rollNumber.toLowerCase().includes(q) ||
            r.templateName.toLowerCase().includes(q),
        );
      }
    }

    return { success: true, data: items };
  }

  async getRequestById(
    id: string,
  ): Promise<ApiResponse<CertificateRequest | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const req =
      this.requests.find((r) => r.id === id || r.requestId === id) || null;
    return { success: true, data: req };
  }

  async createRequest(
    data: Partial<CertificateRequest>,
  ): Promise<ApiResponse<CertificateRequest>> {
    await new Promise((r) => setTimeout(r, 80));
    const nextSeq = this.requests.length + 86;
    const newReq: CertificateRequest = {
      id: `req-cert-${Date.now()}`,
      requestId: `REQ-2026-0${nextSeq}`,
      studentId: data.studentId || "stu-001",
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      certificateType: data.certificateType || CertificateType.BONAFIDE,
      templateId: data.templateId || "tmpl-bonafide-01",
      templateName:
        data.templateName || "Institutional Student Bonafide Certificate",
      purpose: data.purpose || "Official documentation and verification",
      requestedDate: new Date().toISOString(),
      requiredByDate: data.requiredByDate,
      status: CertificateRequestStatus.SUBMITTED,
      validationChecks: [
        {
          id: "chk-c1",
          title: "Active Enrollment Status",
          passed: true,
          details: "Verified in academic registry",
        },
        {
          id: "chk-c2",
          title: "Finance Dues Clearance",
          passed: true,
          details: "Accounts ledger in good standing",
        },
        {
          id: "chk-c3",
          title: "Disciplinary Standing Check",
          passed: true,
          details: "No active disciplinary proceedings",
        },
      ],
      timeline: [
        {
          id: `t-${Date.now()}`,
          status: CertificateRequestStatus.SUBMITTED,
          title: "Request Submitted",
          performedBy: data.studentName || "Aarav Patel",
          timestamp: new Date().toISOString(),
          notes: data.purpose,
        },
      ],
    };

    this.requests.unshift(newReq);
    return { success: true, data: newReq };
  }

  async approveRequest(
    id: string,
    reviewerId: string,
    reviewerName: string,
    notes?: string,
  ): Promise<ApiResponse<CertificateRequest>> {
    await new Promise((r) => setTimeout(r, 50));
    const req = this.requests.find((r) => r.id === id || r.requestId === id);
    if (!req) {
      throw new Error(`Certificate Request with ID ${id} not found`);
    }

    req.status = CertificateRequestStatus.APPROVED;
    req.reviewerId = reviewerId;
    req.reviewerName = reviewerName;
    req.reviewedAt = new Date().toISOString();

    req.timeline.unshift({
      id: `t-${Date.now()}`,
      status: CertificateRequestStatus.APPROVED,
      title: "Request Approved",
      performedBy: reviewerName,
      timestamp: new Date().toISOString(),
      notes: notes || "Clearance endorsed by authority.",
    });

    return { success: true, data: req };
  }

  async rejectRequest(
    id: string,
    reason: string,
    reviewerId: string,
    reviewerName: string,
  ): Promise<ApiResponse<CertificateRequest>> {
    if (!reason || reason.trim().length === 0) {
      throw new Error("A specific rejection reason is mandatory.");
    }

    await new Promise((r) => setTimeout(r, 50));
    const req = this.requests.find((r) => r.id === id || r.requestId === id);
    if (!req) {
      throw new Error(`Certificate Request with ID ${id} not found`);
    }

    req.status = CertificateRequestStatus.REJECTED;
    req.reviewerId = reviewerId;
    req.reviewerName = reviewerName;
    req.reviewedAt = new Date().toISOString();
    req.rejectionReason = reason;

    req.timeline.unshift({
      id: `t-${Date.now()}`,
      status: CertificateRequestStatus.REJECTED,
      title: "Request Rejected",
      performedBy: reviewerName,
      timestamp: new Date().toISOString(),
      notes: reason,
    });

    return { success: true, data: req };
  }

  async cancelRequest(
    id: string,
    reason?: string,
  ): Promise<ApiResponse<CertificateRequest>> {
    await new Promise((r) => setTimeout(r, 40));
    const req = this.requests.find((r) => r.id === id || r.requestId === id);
    if (!req) {
      throw new Error(`Certificate Request with ID ${id} not found`);
    }

    if (
      req.status !== CertificateRequestStatus.SUBMITTED &&
      req.status !== CertificateRequestStatus.UNDER_REVIEW
    ) {
      throw new Error(
        "Only submitted or under-review requests can be cancelled.",
      );
    }

    req.status = CertificateRequestStatus.CANCELLED;
    req.timeline.unshift({
      id: `t-${Date.now()}`,
      status: CertificateRequestStatus.CANCELLED,
      title: "Request Cancelled by Student",
      performedBy: req.studentName,
      timestamp: new Date().toISOString(),
      notes: reason || "Cancelled by applicant.",
    });

    return { success: true, data: req };
  }

  async issueCertificateForRequest(
    requestId: string,
    issuingAuthority: string,
  ): Promise<ApiResponse<IssuedCertificate>> {
    await new Promise((r) => setTimeout(r, 70));
    const req = this.requests.find(
      (r) => r.id === requestId || r.requestId === requestId,
    );
    if (!req) {
      throw new Error(`Certificate Request with ID ${requestId} not found`);
    }

    const issuedCertRes = await certificatesService.createIssuedCertificate({
      certificateType: req.certificateType,
      recipientId: req.studentId,
      recipientName: req.studentName,
      recipientRollNumber: req.rollNumber,
      recipientProgram: req.program,
      recipientDepartment: req.department,
      templateId: req.templateId,
      templateVersion: "2.1",
      issuingAuthority: issuingAuthority || "Office of the Registrar",
      issueDate: new Date().toISOString().split("T")[0],
    });

    const issuedCert = issuedCertRes.data!;
    req.status = CertificateRequestStatus.ISSUED;
    req.issuedCertificateId = issuedCert.id;
    req.issuedDate = issuedCert.issueDate;

    req.timeline.unshift({
      id: `t-${Date.now()}`,
      status: CertificateRequestStatus.ISSUED,
      title: "Certificate Issued & Dispatched",
      performedBy: issuingAuthority || "Office of the Registrar",
      timestamp: new Date().toISOString(),
      notes: `Certificate Number: ${issuedCert.certificateNumber}`,
    });

    return { success: true, data: issuedCert };
  }
}

export const certificateRequestsService = new CertificateRequestsService();
