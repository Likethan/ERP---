export interface UploadValidationResult {
  valid: boolean;
  errors: string[];
}

export interface SimulatedUploadResult {
  success: boolean;
  fileUrl: string;
  fileName: string;
  fileSize: string;
  fileType: string;
}

class DocumentUploadService {
  private allowedTypes = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  private maxSizeBytes = 15 * 1024 * 1024; // 15MB

  validateUpload(
    file: {
      name: string;
      size: number;
      type: string;
    },
    metadata?: {
      documentName?: string;
      category?: string;
      documentType?: string;
      issueDate?: string;
      expiryDate?: string;
      documentNumber?: string;
    },
  ): UploadValidationResult {
    const errors: string[] = [];

    if (!file.name) {
      errors.push("A file must be selected for upload.");
    }

    if (file.size > this.maxSizeBytes) {
      errors.push(
        `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the maximum allowed limit of 15 MB.`,
      );
    }

    if (file.type && !this.allowedTypes.includes(file.type.toLowerCase())) {
      errors.push(
        "Invalid file format. Only PDF, JPG, PNG, and DOCX documents are permitted.",
      );
    }

    if (metadata) {
      if (!metadata.documentName || metadata.documentName.trim().length === 0) {
        errors.push("Document title is required.");
      }
      if (!metadata.category) {
        errors.push("Document category must be selected.");
      }
      if (!metadata.documentType) {
        errors.push("Document type must be specified.");
      }
      if (metadata.expiryDate && metadata.issueDate) {
        if (new Date(metadata.expiryDate) <= new Date(metadata.issueDate)) {
          errors.push("Expiry date must be after the issue date.");
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  async simulateUpload(
    file: { name: string; size: number; type: string },
    onProgress?: (percent: number) => void,
  ): Promise<SimulatedUploadResult> {
    const steps = [15, 45, 75, 100];
    for (const step of steps) {
      await new Promise((r) => setTimeout(r, 60));
      if (onProgress) onProgress(step);
    }

    const sizeFormatted =
      file.size > 1024 * 1024
        ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
        : `${Math.round(file.size / 1024)} KB`;

    return {
      success: true,
      fileUrl: `/mock-storage/vault/${Date.now()}-${file.name.replace(/\s+/g, "_")}`,
      fileName: file.name,
      fileSize: sizeFormatted || "1.2 MB",
      fileType: file.type || "application/pdf",
    };
  }
}

export const documentUploadService = new DocumentUploadService();
