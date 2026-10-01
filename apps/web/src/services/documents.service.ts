import { ApiResponse } from "@campusos/types";
import {
  DocumentVaultItem,
  DocumentRequestItem,
  IssuedCertificateItem,
  MOCK_DOCUMENTS,
  MOCK_DOCUMENT_REQUESTS,
  MOCK_ISSUED_CERTIFICATES,
} from "@/mocks/documents.mock";

class DocumentsService {
  private documents: DocumentVaultItem[] = [...MOCK_DOCUMENTS];
  private requests: DocumentRequestItem[] = [...MOCK_DOCUMENT_REQUESTS];
  private certificates: IssuedCertificateItem[] = [...MOCK_ISSUED_CERTIFICATES];

  async getDocuments(category?: string): Promise<ApiResponse<DocumentVaultItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.documents];
    if (category) {
      items = items.filter((d) => d.category === category);
    }
    return { success: true, data: items };
  }

  async getRequests(): Promise<ApiResponse<DocumentRequestItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.requests };
  }

  async submitRequest(data: Partial<DocumentRequestItem>): Promise<ApiResponse<DocumentRequestItem>> {
    await new Promise((r) => setTimeout(r, 90));
    const newReq: DocumentRequestItem = {
      id: `dreq-${Date.now()}`,
      studentName: data.studentName || "Aarav Patel",
      rollNumber: data.rollNumber || "24CSE0101",
      program: data.program || "B.Tech CSE",
      certificateType: data.certificateType || "BONAFIDE",
      purpose: data.purpose || "Official documentation",
      requestedDate: new Date().toISOString().split("T")[0],
      status: "PENDING_APPROVAL",
    };
    this.requests.unshift(newReq);
    return { success: true, data: newReq };
  }

  async getIssuedCertificates(): Promise<ApiResponse<IssuedCertificateItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.certificates };
  }

  async verifyCertificate(certCode: string): Promise<ApiResponse<IssuedCertificateItem | null>> {
    await new Promise((r) => setTimeout(r, 80));
    const cert = this.certificates.find(
      (c) =>
        c.certificateNumber.toLowerCase().includes(certCode.toLowerCase()) ||
        c.qrVerificationUrl.toLowerCase().includes(certCode.toLowerCase())
    ) || null;
    return { success: true, data: cert };
  }

  async approveRequest(id: string): Promise<ApiResponse<IssuedCertificateItem>> {
    await new Promise((r) => setTimeout(r, 90));
    const req = this.requests.find((r) => r.id === id);
    if (req) {
      req.status = "ISSUED";
    }
    const newCert: IssuedCertificateItem = {
      id: `cert-${Date.now()}`,
      certificateNumber: `CERT-2026-0${this.certificates.length + 881}`,
      certificateType: `${req ? req.certificateType : "BONAFIDE"} Certificate`,
      studentName: req ? req.studentName : "Aarav Patel",
      rollNumber: req ? req.rollNumber : "24CSE0101",
      issueDate: new Date().toISOString().split("T")[0],
      qrVerificationUrl: `https://verify.campusos.edu/cert/2026-${Date.now().toString().slice(-6)}`,
      digitalSignatureHash: `sha256:0x${Date.now().toString(16)}fa98bc`,
      status: "VALID",
    };
    this.certificates.unshift(newCert);
    return { success: true, data: newCert };
  }
}

export const documentsService = new DocumentsService();
