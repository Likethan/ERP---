import {
  DocumentItem,
  DocumentStatus,
  DocumentExpiryStatus,
  CertificateRequest,
  CertificateRequestStatus,
} from "@campusos/types";

/**
 * Calculates the verification rate as a percentage of uploaded/processed documents.
 * Formula: (Verified Documents / Total Processable Documents) * 100
 */
export function calculateVerificationRate(documents: DocumentItem[]): number {
  if (!documents || documents.length === 0) return 0;
  const processableDocs = documents.filter(
    (d) => d.status !== DocumentStatus.MISSING && d.status !== DocumentStatus.REQUIRED
  );
  if (processableDocs.length === 0) return 0;
  const verified = processableDocs.filter((d) => d.status === DocumentStatus.VERIFIED).length;
  return Number(((verified / processableDocs.length) * 100).toFixed(1));
}

/**
 * Calculates the rejection rate as a percentage of processed documents.
 * Formula: (Rejected Documents / Total Processable Documents) * 100
 */
export function calculateRejectionRate(documents: DocumentItem[]): number {
  if (!documents || documents.length === 0) return 0;
  const processableDocs = documents.filter(
    (d) => d.status !== DocumentStatus.MISSING && d.status !== DocumentStatus.REQUIRED
  );
  if (processableDocs.length === 0) return 0;
  const rejected = processableDocs.filter((d) => d.status === DocumentStatus.REJECTED).length;
  return Number(((rejected / processableDocs.length) * 100).toFixed(1));
}

/**
 * Calculates the document completion rate for an individual owner or cohort.
 * Formula: (Verified Required Documents / Total Required Documents) * 100
 */
export function calculateDocumentCompletionRate(requiredCount: number, verifiedCount: number): number {
  if (requiredCount <= 0) return 100;
  const rate = (verifiedCount / requiredCount) * 100;
  return Number(Math.min(100, Math.max(0, rate)).toFixed(1));
}

/**
 * Counts total documents pending review or under active verification.
 */
export function calculatePendingVerificationCount(documents: DocumentItem[]): number {
  if (!documents || documents.length === 0) return 0;
  return documents.filter(
    (d) => d.status === DocumentStatus.UPLOADED || d.status === DocumentStatus.UNDER_REVIEW
  ).length;
}

/**
 * Evaluates document expiry status relative to a reference date.
 */
export function getDocumentExpiryStatus(
  expiryDateStr?: string | null,
  referenceDateStr?: string
): DocumentExpiryStatus {
  if (!expiryDateStr) return DocumentExpiryStatus.NO_EXPIRY;

  const refDate = referenceDateStr ? new Date(referenceDateStr) : new Date("2026-10-02T00:00:00.000Z");
  const expDate = new Date(expiryDateStr);

  const diffTime = expDate.getTime() - refDate.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return DocumentExpiryStatus.EXPIRED;
  }
  if (diffDays <= 7) {
    return DocumentExpiryStatus.EXPIRING_7_DAYS;
  }
  if (diffDays <= 30) {
    return DocumentExpiryStatus.EXPIRING_30_DAYS;
  }
  if (diffDays <= 90) {
    return DocumentExpiryStatus.EXPIRING_90_DAYS;
  }
  return DocumentExpiryStatus.VALID;
}

/**
 * Counts expired documents based on status flag or passed expiry date.
 */
export function calculateExpiredDocumentCount(
  documents: DocumentItem[],
  referenceDateStr?: string
): number {
  if (!documents || documents.length === 0) return 0;
  return documents.filter((d) => {
    if (d.status === DocumentStatus.EXPIRED) return true;
    if (d.expiryDate) {
      return getDocumentExpiryStatus(d.expiryDate, referenceDateStr) === DocumentExpiryStatus.EXPIRED;
    }
    return false;
  }).length;
}

/**
 * Counts documents expiring within specified days (default 30 days).
 */
export function calculateExpiringDocumentCount(
  documents: DocumentItem[],
  withinDays: number = 30,
  referenceDateStr?: string
): number {
  if (!documents || documents.length === 0) return 0;
  return documents.filter((d) => {
    if (!d.expiryDate) return false;
    const status = getDocumentExpiryStatus(d.expiryDate, referenceDateStr);
    if (withinDays <= 7) {
      return status === DocumentExpiryStatus.EXPIRING_7_DAYS;
    }
    if (withinDays <= 30) {
      return status === DocumentExpiryStatus.EXPIRING_7_DAYS || status === DocumentExpiryStatus.EXPIRING_30_DAYS;
    }
    return (
      status === DocumentExpiryStatus.EXPIRING_7_DAYS ||
      status === DocumentExpiryStatus.EXPIRING_30_DAYS ||
      status === DocumentExpiryStatus.EXPIRING_90_DAYS
    );
  }).length;
}

/**
 * Calculates certificate approval rate across all resolved requests.
 */
export function calculateCertificateApprovalRate(requests: CertificateRequest[]): number {
  if (!requests || requests.length === 0) return 0;
  const resolved = requests.filter(
    (r) =>
      r.status === CertificateRequestStatus.APPROVED ||
      r.status === CertificateRequestStatus.ISSUED ||
      r.status === CertificateRequestStatus.REJECTED
  );
  if (resolved.length === 0) return 0;
  const approved = resolved.filter(
    (r) => r.status === CertificateRequestStatus.APPROVED || r.status === CertificateRequestStatus.ISSUED
  ).length;
  return Number(((approved / resolved.length) * 100).toFixed(1));
}

/**
 * Calculates certificate issuance rate across all submitted requests.
 */
export function calculateCertificateIssuanceRate(requests: CertificateRequest[]): number {
  if (!requests || requests.length === 0) return 0;
  const nonDraft = requests.filter((r) => r.status !== CertificateRequestStatus.DRAFT);
  if (nonDraft.length === 0) return 0;
  const issued = nonDraft.filter((r) => r.status === CertificateRequestStatus.ISSUED).length;
  return Number(((issued / nonDraft.length) * 100).toFixed(1));
}

/**
 * Calculates average verification turnaround time in hours from timeline timestamps.
 */
export function calculateAverageVerificationTime(documents: DocumentItem[]): number {
  if (!documents || documents.length === 0) return 0;
  const verifiedDocs = documents.filter((d) => d.status === DocumentStatus.VERIFIED && d.verifiedAt && d.uploadedAt);
  if (verifiedDocs.length === 0) return 24; // Standard SLA fallback

  let totalHours = 0;
  let count = 0;

  for (const doc of verifiedDocs) {
    const uploadTime = new Date(doc.uploadedAt).getTime();
    const verifiedTime = new Date(doc.verifiedAt!).getTime();
    const diffHours = (verifiedTime - uploadTime) / (1000 * 60 * 60);
    if (diffHours >= 0) {
      totalHours += diffHours;
      count++;
    }
  }

  return count > 0 ? Number((totalHours / count).toFixed(1)) : 24;
}

/**
 * Generates category distribution with count and percentage.
 */
export function calculateCategoryDistribution(
  documents: DocumentItem[]
): { category: string; count: number; percentage: number }[] {
  if (!documents || documents.length === 0) return [];
  const total = documents.length;
  const counts: Record<string, number> = {};

  for (const doc of documents) {
    counts[doc.category] = (counts[doc.category] || 0) + 1;
  }

  return Object.entries(counts).map(([cat, count]) => ({
    category: cat,
    count,
    percentage: Number(((count / total) * 100).toFixed(1)),
  }));
}

/**
 * Computes full breakdown of document expiry buckets.
 */
export function calculateExpiryBreakdown(
  documents: DocumentItem[],
  referenceDateStr?: string
): {
  expired: number;
  expiring7Days: number;
  expiring30Days: number;
  expiring90Days: number;
  valid: number;
  noExpiry: number;
} {
  const breakdown = {
    expired: 0,
    expiring7Days: 0,
    expiring30Days: 0,
    expiring90Days: 0,
    valid: 0,
    noExpiry: 0,
  };

  if (!documents) return breakdown;

  for (const doc of documents) {
    if (doc.status === DocumentStatus.EXPIRED) {
      breakdown.expired++;
      continue;
    }
    const status = getDocumentExpiryStatus(doc.expiryDate, referenceDateStr);
    switch (status) {
      case DocumentExpiryStatus.EXPIRED:
        breakdown.expired++;
        break;
      case DocumentExpiryStatus.EXPIRING_7_DAYS:
        breakdown.expiring7Days++;
        break;
      case DocumentExpiryStatus.EXPIRING_30_DAYS:
        breakdown.expiring30Days++;
        break;
      case DocumentExpiryStatus.EXPIRING_90_DAYS:
        breakdown.expiring90Days++;
        break;
      case DocumentExpiryStatus.VALID:
        breakdown.valid++;
        break;
      case DocumentExpiryStatus.NO_EXPIRY:
      default:
        breakdown.noExpiry++;
        break;
    }
  }

  return breakdown;
}
