import { ApiResponse } from "@campusos/types";
import {
  DocumentItem,
  DocumentStatus,
  DocumentCategoryCode,
  DocumentOwnerType,
  ConfidentialityLevel,
  VerificationPriority,
} from "@campusos/types";
import { MOCK_DOCUMENTS } from "@/mocks/documents.mock";
import { DocumentFilterState } from "@/types/documents";

class DocumentsService {
  private documents: DocumentItem[] = [...MOCK_DOCUMENTS];

  async listDocuments(
    filters?: DocumentFilterState,
  ): Promise<ApiResponse<DocumentItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.documents];

    if (filters) {
      if (filters.search) {
        const q = filters.search.toLowerCase();
        items = items.filter(
          (d) =>
            d.name.toLowerCase().includes(q) ||
            d.documentType.toLowerCase().includes(q) ||
            d.ownerName.toLowerCase().includes(q) ||
            (d.ownerRollNumber &&
              d.ownerRollNumber.toLowerCase().includes(q)) ||
            (d.documentNumber && d.documentNumber.toLowerCase().includes(q)),
        );
      }
      if (filters.category && filters.category !== "ALL") {
        items = items.filter((d) => d.category === filters.category);
      }
      if (filters.status && filters.status !== "ALL") {
        items = items.filter((d) => d.status === filters.status);
      }
      if (filters.ownerType && filters.ownerType !== "ALL") {
        items = items.filter((d) => d.ownerType === filters.ownerType);
      }
      if (filters.department && filters.department !== "ALL") {
        items = items.filter((d) => d.ownerDepartment === filters.department);
      }
      if (filters.program && filters.program !== "ALL") {
        items = items.filter((d) => d.program === filters.program);
      }
      if (filters.priority && filters.priority !== "ALL") {
        items = items.filter((d) => d.priority === filters.priority);
      }
      if (filters.reviewerId && filters.reviewerId !== "ALL") {
        items = items.filter(
          (d) => d.assignedReviewerId === filters.reviewerId,
        );
      }
    }

    return { success: true, data: items };
  }

  async getDocumentById(id: string): Promise<ApiResponse<DocumentItem | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const doc = this.documents.find((d) => d.id === id) || null;
    return { success: true, data: doc };
  }

  async getDocumentsByOwner(
    ownerId: string,
  ): Promise<ApiResponse<DocumentItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    const items = this.documents.filter((d) => d.ownerId === ownerId);
    return { success: true, data: items };
  }

  async uploadDocument(
    data: Partial<DocumentItem>,
  ): Promise<ApiResponse<DocumentItem>> {
    await new Promise((r) => setTimeout(r, 80));
    const newDoc: DocumentItem = {
      id: `doc-${Date.now()}`,
      name: data.name || "Uploaded Document",
      category: data.category || DocumentCategoryCode.OTHER,
      documentType: data.documentType || "Standard Document",
      ownerType: data.ownerType || DocumentOwnerType.STUDENT,
      ownerId: data.ownerId || "stu-001",
      ownerName: data.ownerName || "Aarav Patel",
      ownerRollNumber: data.ownerRollNumber || "24CSE0101",
      ownerDepartment: data.ownerDepartment || "Computer Science & Engineering",
      program: data.program || "B.Tech Computer Science & Engineering",
      status: DocumentStatus.UPLOADED,
      uploadedAt: new Date().toISOString(),
      confidentiality: data.confidentiality || ConfidentialityLevel.INTERNAL,
      fileSize: data.fileSize || "1.2 MB",
      fileType: data.fileType || "application/pdf",
      documentNumber: data.documentNumber,
      issuingAuthority: data.issuingAuthority,
      issueDate: data.issueDate,
      expiryDate: data.expiryDate,
      priority: data.priority || VerificationPriority.NORMAL,
      activityTimeline: [
        {
          id: `act-${Date.now()}`,
          action: "Document Uploaded",
          description: `Document submitted by ${data.ownerName || "student"}`,
          performedBy: data.ownerName || "Aarav Patel",
          role: String(data.ownerType || "STUDENT"),
          timestamp: new Date().toISOString(),
        },
      ],
      relatedRecord: data.relatedRecord,
    };

    this.documents.unshift(newDoc);
    return { success: true, data: newDoc };
  }

  async updateDocumentMetadata(
    id: string,
    metadata: Partial<DocumentItem>,
  ): Promise<ApiResponse<DocumentItem>> {
    await new Promise((r) => setTimeout(r, 50));
    const doc = this.documents.find((d) => d.id === id);
    if (!doc) {
      throw new Error(`Document with ID ${id} not found`);
    }

    Object.assign(doc, metadata);
    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Metadata Updated",
      description: "Document details or validity metadata edited",
      performedBy: "Dr. Arvind Swaminathan (Registrar)",
      role: "REGISTRAR",
      timestamp: new Date().toISOString(),
    });

    return { success: true, data: doc };
  }

  async submitForVerification(id: string): Promise<ApiResponse<DocumentItem>> {
    await new Promise((r) => setTimeout(r, 50));
    const doc = this.documents.find((d) => d.id === id);
    if (!doc) {
      throw new Error(`Document with ID ${id} not found`);
    }

    doc.status = DocumentStatus.UNDER_REVIEW;
    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Submitted for Verification",
      description: "Moved to institutional review desk",
      performedBy: doc.ownerName,
      role: doc.ownerType,
      timestamp: new Date().toISOString(),
    });

    return { success: true, data: doc };
  }

  async deleteDocument(
    studentIdOrDocId: string,
    documentId?: string,
  ): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 50));
    if (documentId) {
      const { studentsService } = await import("./students.service");
      return studentsService.deleteDocument(studentIdOrDocId, documentId);
    }
    const index = this.documents.findIndex((d) => d.id === studentIdOrDocId);
    if (index !== -1) {
      this.documents.splice(index, 1);
      return { success: true, data: true };
    }
    return { success: false, data: false, error: "Document not found" };
  }

  // Backwards compatibility methods for legacy caller components
  async getDocuments(category?: string) {
    const filter = category ? { category } : undefined;
    return this.listDocuments(filter);
  }

  async getStudentDocuments(studentId: string) {
    const { studentsService } = await import("./students.service");
    return studentsService.getDocuments(studentId);
  }

  async uploadStudentDocument(studentId: string, data: any) {
    const { studentsService } = await import("./students.service");
    return studentsService.uploadDocument(studentId, data);
  }

  async verifyDocument(
    studentId: string,
    documentId: string,
    verifierName?: string,
  ) {
    const { studentsService } = await import("./students.service");
    return studentsService.verifyDocument(studentId, documentId, verifierName);
  }

  async rejectDocument(studentId: string, documentId: string, reason: string) {
    const { studentsService } = await import("./students.service");
    return studentsService.rejectDocument(studentId, documentId, reason);
  }
}

export const documentsService = new DocumentsService();
