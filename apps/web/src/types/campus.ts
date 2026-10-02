/**
 * CampusOS Campus Operations & Engagement — Domain Types
 * Unified typing for Events, Clubs, Registrations, Attendance,
 * Announcements, Notifications, Preferences, Audience Targeting, and Communication.
 *
 * "One Campus. One System. One Source of Truth."
 */

export interface CampusAuditEntry {
  id: string;
  action: string;
  actor: string;
  timestamp: string;
  details?: string;
  fromStatus?: string;
  toStatus?: string;
}

// ==========================================
// 1. Events Domain Types
// ==========================================

export type EventCategory =
  | "Academic"
  | "Technical"
  | "Cultural"
  | "Sports"
  | "Workshop"
  | "Seminar"
  | "Hackathon"
  | "Symposium"
  | "Club Activity"
  | "Placement"
  | "Orientation"
  | "Institutional";

export type EventStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "PUBLISHED"
  | "REGISTRATION_OPEN"
  | "REGISTRATION_CLOSED"
  | "ONGOING"
  | "COMPLETED"
  | "CANCELLED";

export type EventAudienceType =
  | "ALL_STUDENTS"
  | "ALL_USERS"
  | "SPECIFIC_DEPARTMENT"
  | "SPECIFIC_PROGRAM"
  | "SPECIFIC_SEMESTER"
  | "SPECIFIC_SECTION"
  | "FACULTY"
  | "STAFF"
  | "CLUB_MEMBERS"
  | "CUSTOM";

export interface EventAudienceTarget {
  type: EventAudienceType;
  departmentId?: string;
  departmentName?: string;
  programId?: string;
  programName?: string;
  semester?: number;
  section?: string;
  clubId?: string;
  clubName?: string;
  estimatedCount: number;
  customDescription?: string;
}

export interface EventVenueInfo {
  id: string;
  name: string;
  building: string;
  campus: string;
  roomNumber: string;
  capacity: number;
  hasAudioVisual: boolean;
  hasAirConditioning: boolean;
  isAvailable?: boolean;
}

export interface CampusEventItem {
  id: string;
  title: string;
  slug: string;
  category: EventCategory;
  description: string;
  organizer: string;
  organizerType: "DEPARTMENT" | "CLUB" | "INSTITUTION" | "FACULTY" | "STUDENT_BODY";
  departmentId?: string;
  clubId?: string;
  startDate: string;
  endDate: string;
  startTime: string;
  endTime: string;
  venue: string;
  venueId?: string;
  venueDetails?: EventVenueInfo;
  capacity: number;
  registeredCount: number;
  attendedCount: number;
  requiresRegistration: boolean;
  registrationOpenDate?: string;
  registrationCloseDate?: string;
  allowWaitlist: boolean;
  waitlistCount: number;
  requiresAttendance: boolean;
  targetAudience: EventAudienceTarget;
  status: EventStatus;
  featuredImageUrl?: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
  timeline: CampusAuditEntry[];
}

// ==========================================
// 2. Event Registration & Attendance Types
// ==========================================

export type RegistrationStatus =
  | "REGISTERED"
  | "CONFIRMED"
  | "WAITLISTED"
  | "CANCELLED"
  | "ATTENDED"
  | "ABSENT";

export interface EventRegistrationItem {
  id: string;
  eventId: string;
  eventTitle: string;
  eventCategory: EventCategory;
  eventDate: string;
  eventTime: string;
  eventVenue: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  email: string;
  department: string;
  program: string;
  semester: number;
  registrationDate: string;
  status: RegistrationStatus;
  ticketCode: string;
  attendanceMarked: boolean;
  attendanceStatus?: EventAttendanceStatus;
  attendanceMarkedAt?: string;
  cancellationReason?: string;
  timeline: CampusAuditEntry[];
}

export type EventAttendanceStatus =
  | "PRESENT"
  | "ABSENT"
  | "EXCUSED"
  | "PENDING";

export interface EventAttendanceItem {
  id: string;
  eventId: string;
  registrationId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  department: string;
  program: string;
  status: EventAttendanceStatus;
  markedAt?: string;
  markedBy?: string;
  verificationMethod: "MANUAL" | "PORTAL" | "COORDINATOR";
  remarks?: string;
}

export interface EventAttendanceSummary {
  eventId: string;
  eventTitle: string;
  totalRegistered: number;
  presentCount: number;
  absentCount: number;
  excusedCount: number;
  pendingCount: number;
  attendanceRate: number; // percentage
  capacityUsageRate: number; // percentage
}

// ==========================================
// 3. Clubs & Organizations Domain Types
// ==========================================

export type ClubStatus =
  | "DRAFT"
  | "ACTIVE"
  | "INACTIVE"
  | "SUSPENDED";

export type ClubRole =
  | "FACULTY_COORDINATOR"
  | "CLUB_PRESIDENT"
  | "VICE_PRESIDENT"
  | "SECRETARY"
  | "TREASURER"
  | "EVENT_COORDINATOR"
  | "MEMBER";

export type ClubMembershipStatus =
  | "ACTIVE"
  | "PENDING"
  | "SUSPENDED"
  | "LEFT";

export interface ClubMemberItem {
  id: string;
  clubId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  email: string;
  department: string;
  program: string;
  semester: number;
  role: ClubRole;
  status: ClubMembershipStatus;
  joinedDate: string;
  approvedBy?: string;
  approvedAt?: string;
  rejectionReason?: string;
  timeline: CampusAuditEntry[];
}

export interface ClubItem {
  id: string;
  name: string;
  code: string;
  category: "TECHNICAL" | "CULTURAL" | "LITERARY" | "SPORTS" | "ENTREPRENEURSHIP" | "SOCIAL";
  description: string;
  facultyCoordinator: string;
  facultyCoordinatorEmail: string;
  studentLead: string;
  studentLeadRollNo: string;
  meetingSchedule: string;
  meetingVenue: string;
  establishedYear: number;
  status: ClubStatus;
  membersCount: number;
  activeEventsCount: number;
  upcomingEventTitles: string[];
  bannerUrl?: string;
  createdAt: string;
  updatedAt: string;
  timeline: CampusAuditEntry[];
}

// ==========================================
// 4. Announcements Domain Types
// ==========================================

export type AnnouncementStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "PUBLISHED"
  | "EXPIRED"
  | "ARCHIVED";

export type AnnouncementPriority =
  | "LOW"
  | "NORMAL"
  | "HIGH"
  | "URGENT";

export interface AnnouncementAudienceTarget {
  type:
    | "ALL_USERS"
    | "STUDENTS"
    | "FACULTY"
    | "STAFF"
    | "SPECIFIC_DEPARTMENT"
    | "SPECIFIC_PROGRAM"
    | "SPECIFIC_SEMESTER"
    | "SPECIFIC_SECTION"
    | "CLUB_MEMBERS"
    | "CUSTOM";
  departmentName?: string;
  programName?: string;
  semester?: number;
  section?: string;
  clubName?: string;
  estimatedRecipientCount: number;
  description: string;
}

export interface AnnouncementItem {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: "ACADEMIC" | "EXAMINATION" | "HOSTEL" | "GENERAL" | "URGENT" | "PLACEMENT" | "CLUB";
  priority: AnnouncementPriority;
  status: AnnouncementStatus;
  publisher: string;
  publisherRole: string;
  audience: AnnouncementAudienceTarget;
  isPinned: boolean;
  publishDate: string;
  expiryDate?: string;
  createdDate: string;
  updatedDate: string;
  deliveredCount: number;
  viewCount: number;
  timeline: CampusAuditEntry[];
}

// ==========================================
// 5. Notifications & Preferences Domain Types
// ==========================================

export type NotificationCategory =
  | "ACADEMIC"
  | "FINANCE"
  | "PLACEMENT"
  | "EVENT"
  | "CLUB"
  | "SYSTEM"
  | "GENERAL";

export type NotificationStatus =
  | "UNREAD"
  | "READ"
  | "ARCHIVED";

export type NotificationPriority =
  | "LOW"
  | "NORMAL"
  | "HIGH"
  | "URGENT";

export type NotificationChannel =
  | "IN_APP"
  | "EMAIL"
  | "SMS"
  | "PUSH";

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  status: NotificationStatus;
  timestamp: string;
  readAt?: string;
  archivedAt?: string;
  recipientId: string;
  actionUrl?: string;
  relatedEntityType?: "EVENT" | "CLUB" | "ANNOUNCEMENT" | "INVOICE" | "PLACEMENT_DRIVE" | "EXAMINATION" | "ATTENDANCE";
  relatedEntityId?: string;
  relatedEntityTitle?: string;
}

export interface CategoryNotificationPreference {
  category: NotificationCategory;
  categoryLabel: string;
  inApp: boolean;
  email: boolean;
  sms: boolean;
  push: boolean;
}

export interface NotificationDeliverySummary {
  announcementId?: string;
  title: string;
  audienceSize: number;
  inAppDelivered: number;
  emailDelivered: number;
  emailFailed: number;
  smsDelivered: number;
  smsFailed: number;
  status: "PENDING" | "PROCESSING" | "DELIVERED" | "FAILED";
  timestamp: string;
}

export interface CommunicationRecord {
  id: string;
  title: string;
  type: "ANNOUNCEMENT" | "BROADCAST_NOTIFICATION" | "EVENT_ALERT";
  category: string;
  audience: string;
  recipientCount: number;
  publisher: string;
  deliveryStatus: "DELIVERED" | "PROCESSING" | "PARTIAL" | "FAILED";
  deliveredRate: number; // percentage
  timestamp: string;
  channelSummary: string;
}

// ==========================================
// 6. Campus Operations Dashboard Types
// ==========================================

export interface CampusDashboardSummary {
  activeEventsCount: number;
  upcomingEventsCount: number;
  openRegistrationsCount: number;
  activeClubsCount: number;
  registeredParticipantsCount: number;
  attendanceTodayCount: number;
  unreadAnnouncementsCount: number;
  unreadNotificationsCount: number;
  overallAttendanceRate: number;
  activeClubMembershipsCount: number;
  announcementsDeliveredCount: number;
  notificationEngagementRate: number;
}
