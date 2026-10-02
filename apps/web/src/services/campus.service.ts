/**
 * CampusOS Campus Operations & Engagement — Unified Service Layer & Mock Adapter
 * Simulates future FastAPI endpoints with reactive in-memory state,
 * cross-entity relational synchronization, and audit logging.
 *
 * "One Campus. One System. One Source of Truth."
 */

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  meta?: Record<string, unknown>;
}
import {
  CampusEventItem,
  EventCategory,
  EventStatus,
  EventAudienceTarget,
  EventVenueInfo,
  EventRegistrationItem,
  RegistrationStatus,
  EventAttendanceItem,
  EventAttendanceStatus,
  EventAttendanceSummary,
  ClubItem,
  ClubStatus,
  ClubMemberItem,
  ClubRole,
  AnnouncementItem,
  AnnouncementStatus,
  AnnouncementPriority,
  NotificationItem,
  NotificationCategory,
  NotificationStatus,
  CategoryNotificationPreference,
  NotificationDeliverySummary,
  CommunicationRecord,
  CampusDashboardSummary,
} from "@/types/campus";
import {
  MOCK_VENUES,
  MOCK_CLUBS,
  MOCK_CLUB_MEMBERS,
  MOCK_EVENTS,
  MOCK_EVENT_REGISTRATIONS,
  MOCK_EVENT_ATTENDANCE,
  MOCK_ANNOUNCEMENTS,
  MOCK_NOTIFICATIONS,
  MOCK_NOTIFICATION_PREFERENCES,
  MOCK_DELIVERY_SUMMARIES,
  MOCK_COMMUNICATION_HISTORY,
  MOCK_CAMPUS_DASHBOARD,
} from "@/mocks/campus.mock";
import {
  calculateEventAttendanceRate,
  calculateEventCapacityUsage,
  calculateAudienceSize,
  calculateUnreadNotificationCount,
} from "./campus-calculator";

class CampusService {
  private venues: EventVenueInfo[] = [...MOCK_VENUES];
  private clubs: ClubItem[] = [...MOCK_CLUBS];
  private clubMembers: ClubMemberItem[] = [...MOCK_CLUB_MEMBERS];
  private events: CampusEventItem[] = [...MOCK_EVENTS];
  private registrations: EventRegistrationItem[] = [...MOCK_EVENT_REGISTRATIONS];
  private attendanceRecords: EventAttendanceItem[] = [...MOCK_EVENT_ATTENDANCE];
  private announcements: AnnouncementItem[] = [...MOCK_ANNOUNCEMENTS];
  private notifications: NotificationItem[] = [...MOCK_NOTIFICATIONS];
  private preferences: CategoryNotificationPreference[] = [...MOCK_NOTIFICATION_PREFERENCES];
  private deliverySummaries: NotificationDeliverySummary[] = [...MOCK_DELIVERY_SUMMARIES];
  private communicationHistory: CommunicationRecord[] = [...MOCK_COMMUNICATION_HISTORY];
  private dashboard: CampusDashboardSummary = { ...MOCK_CAMPUS_DASHBOARD };

  private delay(ms = 30): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }

  // ==========================================
  // 1. Dashboard & Venues
  // ==========================================

  async getCampusSummary(): Promise<ApiResponse<CampusDashboardSummary>> {
    await this.delay(20);
    // Dynamically recalculate key figures
    const activeEvents = this.events.filter(
      (e) => e.status === "REGISTRATION_OPEN" || e.status === "ONGOING" || e.status === "PUBLISHED"
    ).length;
    const upcomingEvents = this.events.filter(
      (e) => e.status !== "COMPLETED" && e.status !== "CANCELLED"
    ).length;
    const openRegistrations = this.events.filter((e) => e.status === "REGISTRATION_OPEN").length;
    const activeClubs = this.clubs.filter((c) => c.status === "ACTIVE").length;
    const totalRegistrations = this.registrations.filter((r) => r.status !== "CANCELLED").length;
    const unreadAnnouncements = this.announcements.filter((a) => a.status === "PUBLISHED").length;
    const unreadNotifications = calculateUnreadNotificationCount(this.notifications);

    const summary: CampusDashboardSummary = {
      ...this.dashboard,
      activeEventsCount: activeEvents,
      upcomingEventsCount: upcomingEvents,
      openRegistrationsCount: openRegistrations,
      activeClubsCount: activeClubs,
      registeredParticipantsCount: totalRegistrations,
      unreadAnnouncementsCount: Math.min(unreadAnnouncements, 3),
      unreadNotificationsCount: unreadNotifications,
    };
    return { success: true, data: summary };
  }

  async getVenues(): Promise<ApiResponse<EventVenueInfo[]>> {
    await this.delay(15);
    return { success: true, data: [...this.venues] };
  }

  // ==========================================
  // 2. Events Management
  // ==========================================

  async getEvents(filters?: {
    category?: EventCategory | "ALL";
    status?: EventStatus | "ALL";
    organizer?: string;
    venue?: string;
    search?: string;
  }): Promise<ApiResponse<CampusEventItem[]>> {
    await this.delay(30);
    let result = [...this.events];

    if (filters?.category && filters.category !== "ALL") {
      result = result.filter((e) => e.category === filters.category);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((e) => e.status === filters.status);
    }
    if (filters?.organizer) {
      const orgQuery = filters.organizer.toLowerCase();
      result = result.filter((e) => e.organizer.toLowerCase().includes(orgQuery));
    }
    if (filters?.venue) {
      const venQuery = filters.venue.toLowerCase();
      result = result.filter((e) => e.venue.toLowerCase().includes(venQuery));
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase().trim();
      result = result.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          e.description.toLowerCase().includes(q) ||
          e.organizer.toLowerCase().includes(q) ||
          e.venue.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getEventById(id: string): Promise<ApiResponse<CampusEventItem | null>> {
    await this.delay(20);
    const ev = this.events.find((e) => e.id === id);
    if (!ev) {
      return { success: false, data: null, error: "Event not found" };
    }
    return { success: true, data: { ...ev } };
  }

  async createEvent(
    payload: Omit<
      CampusEventItem,
      "id" | "slug" | "status" | "registeredCount" | "attendedCount" | "waitlistCount" | "createdAt" | "updatedAt" | "timeline"
    >
  ): Promise<ApiResponse<CampusEventItem>> {
    await this.delay(50);
    const newId = `evt-${Date.now().toString(36)}`;
    const slug = payload.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

    const newEvent: CampusEventItem = {
      ...payload,
      id: newId,
      slug,
      status: "DRAFT", // Strict Rule: Never automatically publish an event
      registeredCount: 0,
      attendedCount: 0,
      waitlistCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Event Created as Draft",
          actor: payload.createdBy || "Administrator",
          timestamp: new Date().toISOString(),
          details: "Pending administrative review and publication approval.",
          toStatus: "DRAFT",
        },
      ],
    };

    this.events.unshift(newEvent);
    return { success: true, data: newEvent };
  }

  async updateEvent(
    id: string,
    payload: Partial<CampusEventItem>,
    actor = "Administrator"
  ): Promise<ApiResponse<CampusEventItem>> {
    await this.delay(40);
    const idx = this.events.findIndex((e) => e.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Event not found" };
    }

    const prev = this.events[idx];
    const updated: CampusEventItem = {
      ...prev,
      ...payload,
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Event Specifications Updated",
          actor,
          timestamp: new Date().toISOString(),
        },
        ...prev.timeline,
      ],
    };

    this.events[idx] = updated;
    return { success: true, data: updated };
  }

  async publishEvent(id: string, actor = "Dean Academics"): Promise<ApiResponse<CampusEventItem>> {
    await this.delay(40);
    const idx = this.events.findIndex((e) => e.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Event not found" };
    }

    const prev = this.events[idx];
    const newStatus: EventStatus = prev.requiresRegistration ? "REGISTRATION_OPEN" : "PUBLISHED";

    const updated: CampusEventItem = {
      ...prev,
      status: newStatus,
      publishedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Event Formally Approved & Published",
          actor,
          timestamp: new Date().toISOString(),
          fromStatus: prev.status,
          toStatus: newStatus,
          details: `Event registration status is now: ${newStatus}`,
        },
        ...prev.timeline,
      ],
    };

    this.events[idx] = updated;

    // Create a notification for the campus community
    this.notifications.unshift({
      id: `notif-${Date.now()}`,
      title: `New Event Published: ${updated.title}`,
      message: `${updated.title} is now open for registration. Venue: ${updated.venue}.`,
      category: "EVENT",
      priority: "NORMAL",
      status: "UNREAD",
      timestamp: "Just now",
      recipientId: "all-students",
      actionUrl: `/app/campus/events/${updated.id}`,
      relatedEntityType: "EVENT",
      relatedEntityId: updated.id,
      relatedEntityTitle: updated.title,
    });

    return { success: true, data: updated };
  }

  async cancelEvent(id: string, reason: string, actor = "Administrator"): Promise<ApiResponse<CampusEventItem>> {
    await this.delay(40);
    const idx = this.events.findIndex((e) => e.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Event not found" };
    }

    const prev = this.events[idx];
    const updated: CampusEventItem = {
      ...prev,
      status: "CANCELLED",
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Event Formally Cancelled",
          actor,
          timestamp: new Date().toISOString(),
          fromStatus: prev.status,
          toStatus: "CANCELLED",
          details: `Reason: ${reason}`,
        },
        ...prev.timeline,
      ],
    };

    this.events[idx] = updated;
    return { success: true, data: updated };
  }

  // ==========================================
  // 3. Event Registrations
  // ==========================================

  async getRegistrations(filters?: {
    eventId?: string;
    studentId?: string;
    status?: RegistrationStatus | "ALL";
    search?: string;
  }): Promise<ApiResponse<EventRegistrationItem[]>> {
    await this.delay(30);
    let result = [...this.registrations];

    if (filters?.eventId) {
      result = result.filter((r) => r.eventId === filters.eventId);
    }
    if (filters?.studentId) {
      result = result.filter((r) => r.studentId === filters.studentId);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((r) => r.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase().trim();
      result = result.filter(
        (r) =>
          r.studentName.toLowerCase().includes(q) ||
          r.rollNumber.toLowerCase().includes(q) ||
          r.eventTitle.toLowerCase().includes(q) ||
          r.ticketCode.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getEventRegistrations(eventId: string): Promise<ApiResponse<EventRegistrationItem[]>> {
    return this.getRegistrations({ eventId });
  }

  async registerForEvent(
    eventId: string,
    student: {
      id: string;
      name: string;
      rollNumber: string;
      email: string;
      department: string;
      program: string;
      semester: number;
    }
  ): Promise<ApiResponse<EventRegistrationItem>> {
    await this.delay(50);
    const ev = this.events.find((e) => e.id === eventId);
    if (!ev) {
      return { success: false, data: null as any, error: "Event not found" };
    }

    if (ev.status !== "REGISTRATION_OPEN") {
      return {
        success: false,
        data: null as any,
        error: `Registration is ${ev.status}. Event is not accepting registrations.`,
      };
    }

    // Check duplicate
    const existing = this.registrations.find(
      (r) => r.eventId === eventId && r.studentId === student.id && r.status !== "CANCELLED"
    );
    if (existing) {
      return {
        success: false,
        data: null as any,
        error: "Student is already registered for this event.",
      };
    }

    const isFull = ev.registeredCount >= ev.capacity;
    if (isFull && !ev.allowWaitlist) {
      return {
        success: false,
        data: null as any,
        error: "Event capacity reached. Registrations are full.",
      };
    }

    const status: RegistrationStatus = isFull ? "WAITLISTED" : "CONFIRMED";
    const ticketCode = `${isFull ? "WL" : "TKT"}-${ev.id.slice(0, 6).toUpperCase()}-${Math.floor(1000 + Math.random() * 9000)}`;

    const newReg: EventRegistrationItem = {
      id: `reg-${Date.now().toString(36)}`,
      eventId,
      eventTitle: ev.title,
      eventCategory: ev.category,
      eventDate: ev.startDate,
      eventTime: ev.startTime,
      eventVenue: ev.venue,
      studentId: student.id,
      studentName: student.name,
      rollNumber: student.rollNumber,
      email: student.email,
      department: student.department,
      program: student.program,
      semester: student.semester,
      registrationDate: new Date().toLocaleString(),
      status,
      ticketCode,
      attendanceMarked: false,
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: isFull ? "Placed on Event Waitlist" : "Event Registration Confirmed",
          actor: student.name,
          timestamp: new Date().toISOString(),
          toStatus: status,
        },
      ],
    };

    this.registrations.unshift(newReg);

    // Update event counter
    if (isFull) {
      ev.waitlistCount = (ev.waitlistCount || 0) + 1;
    } else {
      ev.registeredCount += 1;
    }

    // Create Notification
    this.notifications.unshift({
      id: `notif-${Date.now()}`,
      title: `Event Registration Confirmed: ${ev.title}`,
      message: `Pass #${ticketCode} generated for ${student.name}. Venue: ${ev.venue}, Date: ${ev.startDate}.`,
      category: "EVENT",
      priority: "NORMAL",
      status: "UNREAD",
      timestamp: "Just now",
      recipientId: student.id,
      actionUrl: `/app/campus/events/${ev.id}`,
      relatedEntityType: "EVENT",
      relatedEntityId: ev.id,
      relatedEntityTitle: ev.title,
    });

    return { success: true, data: newReg };
  }

  async cancelRegistration(
    registrationId: string,
    reason?: string,
    actor = "Student"
  ): Promise<ApiResponse<EventRegistrationItem>> {
    await this.delay(30);
    const reg = this.registrations.find((r) => r.id === registrationId);
    if (!reg) {
      return { success: false, data: null as any, error: "Registration record not found" };
    }

    reg.status = "CANCELLED";
    reg.cancellationReason = reason || "Cancelled by participant";
    reg.timeline.push({
      id: `tl-${Date.now()}`,
      action: "Registration Cancelled",
      actor,
      timestamp: new Date().toISOString(),
      toStatus: "CANCELLED",
      details: reason,
    });

    // Decrement event count
    const ev = this.events.find((e) => e.id === reg.eventId);
    if (ev && ev.registeredCount > 0) {
      ev.registeredCount -= 1;
    }

    return { success: true, data: reg };
  }

  // ==========================================
  // 4. Event Attendance
  // ==========================================

  async getEventAttendance(eventId: string): Promise<
    ApiResponse<{
      items: EventAttendanceItem[];
      summary: EventAttendanceSummary;
    }>
  > {
    await this.delay(30);
    const ev = this.events.find((e) => e.id === eventId);
    const eventRegistrations = this.registrations.filter(
      (r) => r.eventId === eventId && r.status !== "CANCELLED"
    );

    // Merge existing attendance records or create pending entries
    const items: EventAttendanceItem[] = eventRegistrations.map((reg) => {
      const existing = this.attendanceRecords.find(
        (a) => a.eventId === eventId && a.studentId === reg.studentId
      );
      if (existing) return existing;

      return {
        id: `att-${reg.id}`,
        eventId,
        registrationId: reg.id,
        studentId: reg.studentId,
        studentName: reg.studentName,
        rollNumber: reg.rollNumber,
        department: reg.department,
        program: reg.program,
        status: "PENDING",
        verificationMethod: "COORDINATOR",
      };
    });

    let present = 0;
    let absent = 0;
    let excused = 0;
    let pending = 0;

    for (const it of items) {
      if (it.status === "PRESENT") present++;
      else if (it.status === "ABSENT") absent++;
      else if (it.status === "EXCUSED") excused++;
      else pending++;
    }

    const attendanceRate = calculateEventAttendanceRate(present, items.length);
    const capacityUsageRate = calculateEventCapacityUsage(items.length, ev?.capacity || 100);

    const summary: EventAttendanceSummary = {
      eventId,
      eventTitle: ev?.title || "Event",
      totalRegistered: items.length,
      presentCount: present,
      absentCount: absent,
      excusedCount: excused,
      pendingCount: pending,
      attendanceRate,
      capacityUsageRate,
    };

    return { success: true, data: { items, summary } };
  }

  async markEventAttendance(
    eventId: string,
    records: Array<{
      studentId: string;
      status: EventAttendanceStatus;
      remarks?: string;
    }>,
    actor = "Coordinator"
  ): Promise<ApiResponse<{ updatedCount: number; summary: EventAttendanceSummary }>> {
    await this.delay(50);
    const ev = this.events.find((e) => e.id === eventId);
    let presentCount = 0;

    for (const rec of records) {
      const existingIdx = this.attendanceRecords.findIndex(
        (a) => a.eventId === eventId && a.studentId === rec.studentId
      );

      const reg = this.registrations.find(
        (r) => r.eventId === eventId && r.studentId === rec.studentId
      );

      const attendanceItem: EventAttendanceItem = {
        id: existingIdx !== -1 ? this.attendanceRecords[existingIdx].id : `att-${Date.now()}-${rec.studentId}`,
        eventId,
        registrationId: reg?.id || `reg-${rec.studentId}`,
        studentId: rec.studentId,
        studentName: reg?.studentName || "Student",
        rollNumber: reg?.rollNumber || "CS23B000",
        department: reg?.department || "CSE",
        program: reg?.program || "B.Tech",
        status: rec.status,
        markedAt: new Date().toLocaleTimeString(),
        markedBy: actor,
        verificationMethod: "COORDINATOR",
        remarks: rec.remarks,
      };

      if (existingIdx !== -1) {
        this.attendanceRecords[existingIdx] = attendanceItem;
      } else {
        this.attendanceRecords.push(attendanceItem);
      }

      // Sync registration record
      if (reg) {
        reg.attendanceMarked = true;
        reg.attendanceStatus = rec.status;
        reg.attendanceMarkedAt = new Date().toLocaleTimeString();
      }

      if (rec.status === "PRESENT") presentCount++;
    }

    // Update event attendedCount
    if (ev) {
      ev.attendedCount = presentCount;
    }

    const res = await this.getEventAttendance(eventId);
    return {
      success: true,
      data: {
        updatedCount: records.length,
        summary: res.data.summary,
      },
    };
  }

  async bulkMarkAttendance(
    eventId: string,
    status: EventAttendanceStatus,
    studentIds: string[],
    actor = "Coordinator"
  ): Promise<ApiResponse<{ updatedCount: number; summary: EventAttendanceSummary }>> {
    const payload = studentIds.map((id) => ({ studentId: id, status }));
    return this.markEventAttendance(eventId, payload, actor);
  }

  // ==========================================
  // 5. Clubs & Organizations
  // ==========================================

  async getClubs(filters?: {
    category?: string;
    status?: ClubStatus | "ALL";
    search?: string;
  }): Promise<ApiResponse<ClubItem[]>> {
    await this.delay(30);
    let result = [...this.clubs];

    if (filters?.category && filters.category !== "ALL") {
      result = result.filter((c) => c.category === filters.category);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((c) => c.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase().trim();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.code.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q) ||
          c.facultyCoordinator.toLowerCase().includes(q) ||
          c.studentLead.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getClubById(id: string): Promise<
    ApiResponse<{
      club: ClubItem;
      members: ClubMemberItem[];
      events: CampusEventItem[];
      announcements: AnnouncementItem[];
    } | null>
  > {
    await this.delay(25);
    const club = this.clubs.find((c) => c.id === id);
    if (!club) {
      return { success: false, data: null, error: "Club not found" };
    }

    const members = this.clubMembers.filter((m) => m.clubId === id);
    const events = this.events.filter((e) => e.clubId === id);
    const announcements = this.announcements.filter((a) => a.audience.clubName === club.name);

    return {
      success: true,
      data: {
        club: { ...club },
        members,
        events,
        announcements,
      },
    };
  }

  async createClub(
    payload: Omit<ClubItem, "id" | "membersCount" | "activeEventsCount" | "upcomingEventTitles" | "createdAt" | "updatedAt" | "timeline">,
    actor = "Dean of Student Affairs"
  ): Promise<ApiResponse<ClubItem>> {
    await this.delay(50);
    const newClub: ClubItem = {
      ...payload,
      id: `club-${payload.code.toLowerCase()}`,
      membersCount: 1, // Faculty advisor / lead
      activeEventsCount: 0,
      upcomingEventTitles: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Club Charter Created",
          actor,
          timestamp: new Date().toISOString(),
          toStatus: payload.status,
        },
      ],
    };

    this.clubs.push(newClub);
    return { success: true, data: newClub };
  }

  async updateClub(
    id: string,
    payload: Partial<ClubItem>,
    actor = "Faculty Coordinator"
  ): Promise<ApiResponse<ClubItem>> {
    await this.delay(40);
    const idx = this.clubs.findIndex((c) => c.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Club not found" };
    }

    const updated: ClubItem = {
      ...this.clubs[idx],
      ...payload,
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Club Charter Modified",
          actor,
          timestamp: new Date().toISOString(),
        },
        ...this.clubs[idx].timeline,
      ],
    };

    this.clubs[idx] = updated;
    return { success: true, data: updated };
  }

  async getClubMembers(clubId: string): Promise<ApiResponse<ClubMemberItem[]>> {
    await this.delay(20);
    const list = this.clubMembers.filter((m) => m.clubId === clubId);
    return { success: true, data: list };
  }

  async requestMembership(
    clubId: string,
    student: {
      id: string;
      name: string;
      rollNumber: string;
      email: string;
      department: string;
      program: string;
      semester: number;
    }
  ): Promise<ApiResponse<ClubMemberItem>> {
    await this.delay(40);
    const club = this.clubs.find((c) => c.id === clubId);
    if (!club) {
      return { success: false, data: null as any, error: "Club not found" };
    }

    const existing = this.clubMembers.find(
      (m) => m.clubId === clubId && m.studentId === student.id && m.status !== "LEFT"
    );
    if (existing) {
      return {
        success: false,
        data: null as any,
        error: `Membership already exists with status: ${existing.status}`,
      };
    }

    const newMember: ClubMemberItem = {
      id: `cm-${Date.now().toString(36)}`,
      clubId,
      studentId: student.id,
      studentName: student.name,
      rollNumber: student.rollNumber,
      email: student.email,
      department: student.department,
      program: student.program,
      semester: student.semester,
      role: "MEMBER",
      status: "PENDING", // Do not allow students to approve their own membership
      joinedDate: new Date().toISOString().split("T")[0],
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Membership Request Submitted",
          actor: student.name,
          timestamp: new Date().toISOString(),
          toStatus: "PENDING",
        },
      ],
    };

    this.clubMembers.push(newMember);

    // Create Notification for the club coordinator
    this.notifications.unshift({
      id: `notif-${Date.now()}`,
      title: `New Club Join Request: ${club.name}`,
      message: `${student.name} (${student.rollNumber}) has requested to join ${club.name}.`,
      category: "CLUB",
      priority: "NORMAL",
      status: "UNREAD",
      timestamp: "Just now",
      recipientId: "club-lead",
      actionUrl: `/app/campus/clubs/${club.id}`,
      relatedEntityType: "CLUB",
      relatedEntityId: club.id,
      relatedEntityTitle: club.name,
    });

    return { success: true, data: newMember };
  }

  async approveMembership(
    clubId: string,
    membershipId: string,
    actor = "Club Coordinator"
  ): Promise<ApiResponse<ClubMemberItem>> {
    await this.delay(35);
    const member = this.clubMembers.find((m) => m.id === membershipId);
    if (!member) {
      return { success: false, data: null as any, error: "Membership record not found" };
    }

    member.status = "ACTIVE";
    member.approvedBy = actor;
    member.approvedAt = new Date().toISOString();
    member.timeline.push({
      id: `tl-${Date.now()}`,
      action: "Membership Approved",
      actor,
      timestamp: new Date().toISOString(),
      fromStatus: "PENDING",
      toStatus: "ACTIVE",
    });

    // Increment club active count
    const club = this.clubs.find((c) => c.id === clubId);
    if (club) {
      club.membersCount += 1;
    }

    // Notify student
    this.notifications.unshift({
      id: `notif-${Date.now()}`,
      title: `Club Membership Approved: ${club?.name}`,
      message: `Congratulations! Your membership for ${club?.name} has been approved by ${actor}.`,
      category: "CLUB",
      priority: "NORMAL",
      status: "UNREAD",
      timestamp: "Just now",
      recipientId: member.studentId,
      actionUrl: `/app/campus/clubs/${clubId}`,
      relatedEntityType: "CLUB",
      relatedEntityId: clubId,
    });

    return { success: true, data: member };
  }

  async rejectMembership(
    clubId: string,
    membershipId: string,
    reason: string,
    actor = "Club Coordinator"
  ): Promise<ApiResponse<ClubMemberItem>> {
    await this.delay(35);
    const member = this.clubMembers.find((m) => m.id === membershipId);
    if (!member) {
      return { success: false, data: null as any, error: "Membership record not found" };
    }

    member.status = "LEFT";
    member.rejectionReason = reason;
    member.timeline.push({
      id: `tl-${Date.now()}`,
      action: "Membership Request Rejected",
      actor,
      timestamp: new Date().toISOString(),
      details: reason,
      toStatus: "LEFT",
    });

    return { success: true, data: member };
  }

  async leaveClub(
    clubId: string,
    membershipId: string,
    actor = "Student"
  ): Promise<ApiResponse<ClubMemberItem>> {
    await this.delay(30);
    const member = this.clubMembers.find((m) => m.id === membershipId);
    if (!member) {
      return { success: false, data: null as any, error: "Membership record not found" };
    }

    member.status = "LEFT";
    member.timeline.push({
      id: `tl-${Date.now()}`,
      action: "Member Left Club",
      actor,
      timestamp: new Date().toISOString(),
      toStatus: "LEFT",
    });

    const club = this.clubs.find((c) => c.id === clubId);
    if (club && club.membersCount > 0) {
      club.membersCount -= 1;
    }

    return { success: true, data: member };
  }

  async updateMemberRole(
    clubId: string,
    membershipId: string,
    role: ClubRole,
    actor = "Faculty Coordinator"
  ): Promise<ApiResponse<ClubMemberItem>> {
    await this.delay(30);
    const member = this.clubMembers.find((m) => m.id === membershipId);
    if (!member) {
      return { success: false, data: null as any, error: "Membership record not found" };
    }

    const prevRole = member.role;
    member.role = role;
    member.timeline.push({
      id: `tl-${Date.now()}`,
      action: `Role Elevated to ${role}`,
      actor,
      timestamp: new Date().toISOString(),
      details: `Changed from ${prevRole} to ${role}`,
    });

    return { success: true, data: member };
  }

  // ==========================================
  // 6. Announcements Management
  // ==========================================

  async getAnnouncements(filters?: {
    category?: string;
    priority?: AnnouncementPriority | "ALL";
    status?: AnnouncementStatus | "ALL";
    search?: string;
  }): Promise<ApiResponse<AnnouncementItem[]>> {
    await this.delay(25);
    let result = [...this.announcements];

    if (filters?.category && filters.category !== "ALL") {
      result = result.filter((a) => a.category === filters.category);
    }
    if (filters?.priority && filters.priority !== "ALL") {
      result = result.filter((a) => a.priority === filters.priority);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((a) => a.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase().trim();
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.content.toLowerCase().includes(q) ||
          a.publisher.toLowerCase().includes(q)
      );
    }

    return { success: true, data: result };
  }

  async getAnnouncementById(id: string): Promise<ApiResponse<AnnouncementItem | null>> {
    await this.delay(20);
    const anc = this.announcements.find((a) => a.id === id);
    if (!anc) {
      return { success: false, data: null, error: "Announcement not found" };
    }
    return { success: true, data: { ...anc } };
  }

  async createAnnouncement(
    payload: Omit<AnnouncementItem, "id" | "status" | "deliveredCount" | "viewCount" | "createdDate" | "updatedDate" | "timeline">,
    actor = "Administrator"
  ): Promise<ApiResponse<AnnouncementItem>> {
    await this.delay(45);
    const newAnc: AnnouncementItem = {
      ...payload,
      id: `anc-${Date.now().toString(36)}`,
      status: "DRAFT", // Require explicit confirmation to publish
      deliveredCount: 0,
      viewCount: 0,
      createdDate: new Date().toLocaleString(),
      updatedDate: new Date().toLocaleString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Announcement Draft Created",
          actor,
          timestamp: new Date().toISOString(),
          toStatus: "DRAFT",
        },
      ],
    };

    this.announcements.unshift(newAnc);
    return { success: true, data: newAnc };
  }

  async publishAnnouncement(
    id: string,
    actor = "Authorized Publisher"
  ): Promise<ApiResponse<AnnouncementItem>> {
    await this.delay(50);
    const idx = this.announcements.findIndex((a) => a.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Announcement not found" };
    }

    const anc = this.announcements[idx];
    const estimatedCount = anc.audience.estimatedRecipientCount || calculateAudienceSize(anc.audience as any);

    const updated: AnnouncementItem = {
      ...anc,
      status: "PUBLISHED",
      publishDate: new Date().toLocaleString(),
      updatedDate: new Date().toLocaleString(),
      deliveredCount: estimatedCount,
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Announcement Formally Published",
          actor,
          timestamp: new Date().toISOString(),
          fromStatus: anc.status,
          toStatus: "PUBLISHED",
          details: `Dispatched to ${estimatedCount} recipients. Priority: ${anc.priority}.`,
        },
        ...anc.timeline,
      ],
    };

    this.announcements[idx] = updated;

    // Record in communication history
    this.communicationHistory.unshift({
      id: `com-${Date.now()}`,
      title: updated.title,
      type: "ANNOUNCEMENT",
      category: updated.category,
      audience: `${updated.audience.description || "Campus Community"} (${estimatedCount} recipients)`,
      recipientCount: estimatedCount,
      publisher: actor,
      deliveryStatus: "DELIVERED",
      deliveredRate: 98.8,
      timestamp: new Date().toLocaleString(),
      channelSummary: `In-App (${estimatedCount}) • Push (${Math.round(estimatedCount * 0.95)})`,
    });

    // Record simulated delivery summary
    this.deliverySummaries.unshift({
      announcementId: updated.id,
      title: updated.title,
      audienceSize: estimatedCount,
      inAppDelivered: estimatedCount,
      emailDelivered: Math.round(estimatedCount * 0.98),
      emailFailed: Math.round(estimatedCount * 0.02),
      smsDelivered: updated.priority === "URGENT" ? Math.round(estimatedCount * 0.97) : 0,
      smsFailed: updated.priority === "URGENT" ? Math.round(estimatedCount * 0.03) : 0,
      status: "DELIVERED",
      timestamp: new Date().toLocaleString(),
    });

    // Generate broadcast notification
    this.notifications.unshift({
      id: `notif-${Date.now()}`,
      title: updated.title,
      message: updated.summary || updated.content.slice(0, 120),
      category: "ACADEMIC",
      priority: updated.priority,
      status: "UNREAD",
      timestamp: "Just now",
      recipientId: "all-recipients",
      actionUrl: `/app/campus/announcements/${updated.id}`,
      relatedEntityType: "ANNOUNCEMENT",
      relatedEntityId: updated.id,
      relatedEntityTitle: updated.title,
    });

    return { success: true, data: updated };
  }

  async archiveAnnouncement(id: string, actor = "Administrator"): Promise<ApiResponse<AnnouncementItem>> {
    await this.delay(35);
    const idx = this.announcements.findIndex((a) => a.id === id);
    if (idx === -1) {
      return { success: false, data: null as any, error: "Announcement not found" };
    }

    const updated: AnnouncementItem = {
      ...this.announcements[idx],
      status: "ARCHIVED",
      updatedDate: new Date().toLocaleString(),
      timeline: [
        {
          id: `tl-${Date.now()}`,
          action: "Announcement Archived",
          actor,
          timestamp: new Date().toISOString(),
          toStatus: "ARCHIVED",
        },
        ...this.announcements[idx].timeline,
      ],
    };

    this.announcements[idx] = updated;
    return { success: true, data: updated };
  }

  // ==========================================
  // 7. Notifications & Communication Preferences
  // ==========================================

  async getNotifications(filters?: {
    category?: NotificationCategory | "ALL";
    status?: NotificationStatus | "ALL";
  }): Promise<ApiResponse<NotificationItem[]>> {
    await this.delay(20);
    let result = [...this.notifications];

    if (filters?.category && filters.category !== "ALL") {
      result = result.filter((n) => n.category === filters.category);
    }
    if (filters?.status && filters.status !== "ALL") {
      result = result.filter((n) => n.status === filters.status);
    }

    return { success: true, data: result };
  }

  async getNotificationById(id: string): Promise<ApiResponse<NotificationItem | null>> {
    await this.delay(15);
    const notif = this.notifications.find((n) => n.id === id);
    if (!notif) return { success: false, data: null, error: "Notification not found" };
    return { success: true, data: { ...notif } };
  }

  async markNotificationRead(id: string): Promise<ApiResponse<NotificationItem>> {
    await this.delay(15);
    const notif = this.notifications.find((n) => n.id === id);
    if (!notif) {
      return { success: false, data: null as any, error: "Notification not found" };
    }
    notif.status = "READ";
    notif.readAt = new Date().toISOString();
    return { success: true, data: { ...notif } };
  }

  async markAllNotificationsRead(): Promise<ApiResponse<{ count: number }>> {
    await this.delay(20);
    let count = 0;
    this.notifications.forEach((n) => {
      if (n.status === "UNREAD") {
        n.status = "READ";
        n.readAt = new Date().toISOString();
        count++;
      }
    });
    return { success: true, data: { count } };
  }

  async archiveNotification(id: string): Promise<ApiResponse<NotificationItem>> {
    await this.delay(15);
    const notif = this.notifications.find((n) => n.id === id);
    if (!notif) {
      return { success: false, data: null as any, error: "Notification not found" };
    }
    notif.status = "ARCHIVED";
    notif.archivedAt = new Date().toISOString();
    return { success: true, data: { ...notif } };
  }

  async getNotificationPreferences(): Promise<ApiResponse<CategoryNotificationPreference[]>> {
    await this.delay(20);
    return { success: true, data: [...this.preferences] };
  }

  async updateNotificationPreferences(
    newPreferences: CategoryNotificationPreference[]
  ): Promise<ApiResponse<CategoryNotificationPreference[]>> {
    await this.delay(30);
    this.preferences = [...newPreferences];
    return { success: true, data: [...this.preferences] };
  }

  async getDeliverySummaries(): Promise<ApiResponse<NotificationDeliverySummary[]>> {
    await this.delay(25);
    return { success: true, data: [...this.deliverySummaries] };
  }

  async getCommunicationHistory(): Promise<ApiResponse<CommunicationRecord[]>> {
    await this.delay(30);
    return { success: true, data: [...this.communicationHistory] };
  }

  // ==========================================
  // 8. Audience Calculator Helper
  // ==========================================

  estimateAudience(target: EventAudienceTarget | { type: string; departmentName?: string; semester?: number }): number {
    return calculateAudienceSize(target);
  }
}

export const campusService = new CampusService();

// Re-export specialized handles for modularity
export const eventsService = campusService;
export const clubsService = campusService;
export const announcementsService = campusService;
export const notificationsService = campusService;
