import { ApiResponse } from "@campusos/types";
import {
  IssuedCertificate,
  IssuedCertificateStatus,
  CertificateType,
} from "@campusos/types";
import { MOCK_ISSUED_CERTIFICATES } from "@/mocks/documents.mock";

class CertificatesService {
  private certificates: IssuedCertificate[] = [...MOCK_ISSUED_CERTIFICATES];

  async listIssuedCertificates(filters?: {
    recipientId?: string;
    certificateType?: string;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<IssuedCertificate[]>> {
    await new Promise((r) => setTimeout(r, 30));
    let items = [...this.certificates];

    if (filters) {
      if (filters.recipientId) {
        items = items.filter((c) => c.recipientId === filters.recipientId);
      }
      if (filters.certificateType && filters.certificateType !== "ALL") {
        items = items.filter((c) => c.certificateType === filters.certificateType);
      }
      if (filters.status && filters.status !== "ALL") {
        items = items.filter((c) => c.status === filters.status);
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        items = items.filter(
          (c) =>
            c.certificateNumber.toLowerCase().includes(q) ||
            c.recipientName.toLowerCase().includes(q) ||
            c.recipientRollNumber.toLowerCase().includes(q) ||
            c.certificateType.toLowerCase().includes(q)
        );
      }
    }

    return { success: true, data: items };
  }

  async getIssuedCertificateById(id: string): Promise<ApiResponse<IssuedCertificate | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const cert =
      this.certificates.find((c) => c.id === id || c.certificateNumber === id) || null;
    return { success: true, data: cert };
  }

  async verifyCertificate(certCode: string): Promise<ApiResponse<IssuedCertificate | null>> {
    await new Promise((r) => setTimeout(r, 50));
    const clean = certCode.trim().toLowerCase();
    const cert =
      this.certificates.find(
        (c) =>
          c.certificateNumber.toLowerCase().includes(clean) ||
          c.qrVerificationUrl.toLowerCase().includes(clean) ||
          c.digitalSignatureHash.toLowerCase().includes(clean)
      ) || null;
    return { success: true, data: cert };
  }

  async createIssuedCertificate(
    data: Partial<IssuedCertificate>
  ): Promise<ApiResponse<IssuedCertificate>> {
    await new Promise((r) => setTimeout(r, 60));
    const nextSeq = this.certificates.length + 42;
    const certNumber = `CAMPUSOS/CERT/2026/00${nextSeq}`;
    const newCert: IssuedCertificate = {
      id: `cert-${Date.now()}`,
      certificateNumber: certNumber,
      certificateType: data.certificateType || CertificateType.BONAFIDE,
      recipientId: data.recipientId || "stu-001",
      recipientName: data.recipientName || "Aarav Patel",
      recipientRollNumber: data.recipientRollNumber || "24CSE0101",
      recipientProgram: data.recipientProgram || "B.Tech Computer Science & Engineering",
      recipientDepartment: data.recipientDepartment || "Computer Science & Engineering",
      templateId: data.templateId || "tmpl-bonafide-01",
      templateVersion: data.templateVersion || "2.1",
      issuingAuthority: data.issuingAuthority || "Office of the Registrar",
      issueDate: data.issueDate || new Date().toISOString().split("T")[0],
      status: IssuedCertificateStatus.ISSUED,
      qrVerificationUrl: `https://verify.campusos.edu/cert/CAMPUSOS-2026-00${nextSeq}`,
      digitalSignatureHash: `SHA256:0x${Date.now().toString(16)}a9f77b21dc04`,
      downloadUrl: `#download-cert-00${nextSeq}`,
    };

    this.certificates.unshift(newCert);
    return { success: true, data: newCert };
  }

  async revokeCertificate(
    id: string,
    reason: string
  ): Promise<ApiResponse<IssuedCertificate>> {
    await new Promise((r) => setTimeout(r, 50));
    const cert = this.certificates.find((c) => c.id === id || c.certificateNumber === id);
    if (!cert) {
      throw new Error(`Issued certificate with ID ${id} not found`);
    }

    cert.status = IssuedCertificateStatus.REVOKED;
    cert.revokedDate = new Date().toISOString().split("T")[0];
    cert.revocationReason = reason;

    return { success: true, data: cert };
  }
}

export const certificatesService = new CertificatesService();
