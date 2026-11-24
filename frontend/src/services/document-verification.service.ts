import { ApiResponse } from "@campusos/types";
import {
  DocumentItem,
  DocumentStatus,
  VerificationChecklistItem,
} from "@campusos/types";
import { documentsService } from "./documents.service";

class DocumentVerificationService {
  async listVerificationQueue(filters?: {
    category?: string;
    priority?: string;
    status?: string;
    reviewerId?: string;
  }): Promise<ApiResponse<DocumentItem[]>> {
    const allDocsResponse = await documentsService.listDocuments();
    let queue = (allDocsResponse.data || []).filter(
      (d) =>
        d.status === DocumentStatus.UPLOADED ||
        d.status === DocumentStatus.UNDER_REVIEW ||
        d.status === DocumentStatus.REJECTED,
    );

    if (filters) {
      if (filters.category && filters.category !== "ALL") {
        queue = queue.filter((d) => d.category === filters.category);
      }
      if (filters.priority && filters.priority !== "ALL") {
        queue = queue.filter((d) => d.priority === filters.priority);
      }
      if (filters.status && filters.status !== "ALL") {
        queue = queue.filter((d) => d.status === filters.status);
      }
      if (filters.reviewerId && filters.reviewerId !== "ALL") {
        queue = queue.filter(
          (d) => d.assignedReviewerId === filters.reviewerId,
        );
      }
    }

    return { success: true, data: queue };
  }

  async startVerification(
    documentId: string,
    reviewerId: string,
    reviewerName: string,
  ): Promise<ApiResponse<DocumentItem>> {
    const docRes = await documentsService.getDocumentById(documentId);
    if (!docRes.data) {
      throw new Error(`Document with ID ${documentId} not found`);
    }

    const doc = docRes.data;
    doc.status = DocumentStatus.UNDER_REVIEW;
    doc.assignedReviewerId = reviewerId;
    doc.assignedReviewerName = reviewerName;
    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Review Commenced",
      description: `Assigned to ${reviewerName} for compliance review`,
      performedBy: reviewerName,
      role: "VERIFICATION_OFFICER",
      timestamp: new Date().toISOString(),
    });

    return { success: true, data: doc };
  }

  async verifyDocument(
    documentId: string,
    verifierName: string,
    notes?: string,
  ): Promise<ApiResponse<DocumentItem>> {
    const docRes = await documentsService.getDocumentById(documentId);
    if (!docRes.data) {
      throw new Error(`Document with ID ${documentId} not found`);
    }

    const doc = docRes.data;
    doc.status = DocumentStatus.VERIFIED;
    doc.verifiedAt = new Date().toISOString();
    doc.verifiedBy = verifierName;
    doc.rejectionReason = undefined;

    // Check all checklist items if present
    if (doc.verificationChecklist) {
      doc.verificationChecklist.forEach((chk: VerificationChecklistItem) => {
        chk.checked = true;
      });
    }

    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Document Verified",
      description: `Approved and verified by ${verifierName}`,
      performedBy: verifierName,
      role: "VERIFICATION_OFFICER",
      timestamp: new Date().toISOString(),
      notes:
        notes ||
        "Authenticated against official institutional and state guidelines.",
    });

    return { success: true, data: doc };
  }

  async rejectDocument(
    documentId: string,
    reason: string,
    verifierName: string,
  ): Promise<ApiResponse<DocumentItem>> {
    if (!reason || reason.trim().length === 0) {
      throw new Error(
        "A specific rejection reason is mandatory when rejecting a document.",
      );
    }

    const docRes = await documentsService.getDocumentById(documentId);
    if (!docRes.data) {
      throw new Error(`Document with ID ${documentId} not found`);
    }

    const doc = docRes.data;
    doc.status = DocumentStatus.REJECTED;
    doc.verifiedAt = new Date().toISOString();
    doc.verifiedBy = verifierName;
    doc.rejectionReason = reason;

    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Document Rejected",
      description: `Rejected by ${verifierName}: ${reason}`,
      performedBy: verifierName,
      role: "VERIFICATION_OFFICER",
      timestamp: new Date().toISOString(),
      notes: reason,
    });

    return { success: true, data: doc };
  }

  async requestReupload(
    documentId: string,
    instruction: string,
    verifierName: string,
  ): Promise<ApiResponse<DocumentItem>> {
    const docRes = await documentsService.getDocumentById(documentId);
    if (!docRes.data) {
      throw new Error(`Document with ID ${documentId} not found`);
    }

    const doc = docRes.data;
    doc.status = DocumentStatus.REJECTED;
    doc.rejectionReason = `Re-upload requested: ${instruction}`;

    doc.activityTimeline.unshift({
      id: `act-${Date.now()}`,
      action: "Re-upload Requested",
      description: `Candidate notified by ${verifierName} to supply a replacement scan: ${instruction}`,
      performedBy: verifierName,
      role: "VERIFICATION_OFFICER",
      timestamp: new Date().toISOString(),
      notes: instruction,
    });

    return { success: true, data: doc };
  }

  async updateChecklistItem(
    documentId: string,
    checklistItemId: string,
    checked: boolean,
    notes?: string,
  ): Promise<ApiResponse<DocumentItem>> {
    const docRes = await documentsService.getDocumentById(documentId);
    if (!docRes.data) {
      throw new Error(`Document with ID ${documentId} not found`);
    }

    const doc = docRes.data;
    if (doc.verificationChecklist) {
      const item = doc.verificationChecklist.find(
        (c: VerificationChecklistItem) => c.id === checklistItemId,
      );
      if (item) {
        item.checked = checked;
        if (notes) item.notes = notes;
      }
    }

    return { success: true, data: doc };
  }
}

export const documentVerificationService = new DocumentVerificationService();
