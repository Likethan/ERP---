/**
 * CampusOS Unified Sports, Athletics, Recreation & Student Fitness Client Service
 * Product Principle: "One Campus. One System. One Source of Truth."
 *
 * Connects to:
 * - /api/v1/sports/dashboard
 * - /api/v1/sports/departments
 * - /api/v1/sports/facilities & maintenance closures
 * - /api/v1/sports/facility-bookings & availability calendar
 * - /api/v1/sports/participants & health clearance
 * - /api/v1/sports/teams & roster capacity
 * - /api/v1/sports/coaches & official assignments
 * - /api/v1/sports/training-programs & recurring sessions
 * - /api/v1/sports/competitions & registrations
 * - /api/v1/sports/fixtures & match results
 * - /api/v1/sports/standings & achievements
 * - /api/v1/sports/equipment-assignments & return inspections
 * - /api/v1/sports/reports & analytics
 */

import { apiFetch } from "@/lib/api-client";
import { ApiResponse } from "@campusos/types";
import {
  SportsDepartmentItem,
  SportsFacilityItem,
  FacilityBookingItem,
  SportsParticipantItem,
  SportsTeamItem,
  TeamRosterMemberItem,
  CoachingAssignmentItem,
  TrainingProgramItem,
  TrainingSessionItem,
  TrainingAttendanceItem,
  SportsCompetitionItem,
  CompetitionRegistrationItem,
  MatchFixtureItem,
  MatchResultItem,
  CompetitionStandingItem,
  SportsAchievementItem,
  SportsEquipmentAssignmentItem,
  SportsFeeItem,
  SportsDashboardData,
} from "../types/sports";
import {
  MOCK_SPORTS_DEPARTMENTS,
  MOCK_SPORTS_FACILITIES,
  MOCK_FACILITY_BOOKINGS,
  MOCK_SPORTS_PARTICIPANTS,
  MOCK_SPORTS_TEAMS,
  MOCK_ROSTER_MEMBERS,
  MOCK_COACHING_ASSIGNMENTS,
  MOCK_TRAINING_PROGRAMS,
  MOCK_TRAINING_SESSIONS,
  MOCK_TRAINING_ATTENDANCE,
  MOCK_COMPETITIONS,
  MOCK_COMPETITION_REGISTRATIONS,
  MOCK_MATCH_FIXTURES,
  MOCK_COMPETITION_STANDINGS,
  MOCK_SPORTS_ACHIEVEMENTS,
  MOCK_EQUIPMENT_ASSIGNMENTS,
  MOCK_SPORTS_FEES,
  MOCK_SPORTS_DASHBOARD,
} from "../mocks/sports.mock";
import {
  detectFacilityBookingConflict,
  computeTournamentStandings,
  generateRoundRobinFixtures,
} from "./sports-calculator";

// In-memory state caches to preserve client-side actions during interactive session
const departmentsState: SportsDepartmentItem[] = [...MOCK_SPORTS_DEPARTMENTS];
const facilitiesState: SportsFacilityItem[] = [...MOCK_SPORTS_FACILITIES];
const bookingsState: FacilityBookingItem[] = [...MOCK_FACILITY_BOOKINGS];
const participantsState: SportsParticipantItem[] = [...MOCK_SPORTS_PARTICIPANTS];
const teamsState: SportsTeamItem[] = [...MOCK_SPORTS_TEAMS];
const rosterState: TeamRosterMemberItem[] = [...MOCK_ROSTER_MEMBERS];
const coachingState: CoachingAssignmentItem[] = [...MOCK_COACHING_ASSIGNMENTS];
const programsState: TrainingProgramItem[] = [...MOCK_TRAINING_PROGRAMS];
const sessionsState: TrainingSessionItem[] = [...MOCK_TRAINING_SESSIONS];
const attendanceState: TrainingAttendanceItem[] = [...MOCK_TRAINING_ATTENDANCE];
const competitionsState: SportsCompetitionItem[] = [...MOCK_COMPETITIONS];
const registrationsState: CompetitionRegistrationItem[] = [...MOCK_COMPETITION_REGISTRATIONS];
const fixturesState: MatchFixtureItem[] = [...MOCK_MATCH_FIXTURES];
const standingsState: CompetitionStandingItem[] = [...MOCK_COMPETITION_STANDINGS];
const achievementsState: SportsAchievementItem[] = [...MOCK_SPORTS_ACHIEVEMENTS];
const equipmentState: SportsEquipmentAssignmentItem[] = [...MOCK_EQUIPMENT_ASSIGNMENTS];
const feesState: SportsFeeItem[] = [...MOCK_SPORTS_FEES];

class SportsService {
  // =========================================================================
  // 1. DASHBOARD & OVERVIEW
  // =========================================================================

  async getSportsDashboard(campusId?: string): Promise<ApiResponse<SportsDashboardData>> {
    const qs = campusId && campusId !== "ALL" ? `?campus_id=${campusId}` : "";
    try {
      const res = await apiFetch<any>(`/api/v1/sports/dashboard${qs}`);
      if (res.success && res.data) {
        const d = res.data;
        return {
          success: true,
          data: {
            totalDepartments: d.total_departments ?? departmentsState.length,
            totalFacilities: d.total_facilities ?? facilitiesState.length,
            facilitiesAvailable: d.facilities_available ?? facilitiesState.filter(f => f.status === "AVAILABLE").length,
            facilitiesMaintenance: d.facilities_maintenance ?? facilitiesState.filter(f => f.status === "MAINTENANCE_CLOSED").length,
            totalParticipants: d.total_participants ?? participantsState.length,
            participantsCleared: d.participants_cleared ?? participantsState.filter(p => p.clearanceStatus === "CLEARED").length,
            clearanceComplianceRate: d.clearance_compliance_rate ?? 91.9,
            totalTeams: d.total_teams ?? teamsState.length,
            activeTournaments: d.active_tournaments ?? competitionsState.filter(c => c.status === "IN_PROGRESS").length,
            matchesScheduledToday: d.matches_scheduled_today ?? fixturesState.length,
            equipmentItemsCheckedOut: d.equipment_items_checked_out ?? equipmentState.filter(e => e.status === "ISSUED").length,
            equipmentOverdueCount: d.equipment_overdue_count ?? equipmentState.filter(e => e.status === "OVERDUE").length,
            upcomingTrainingSessionsCount: d.upcoming_training_sessions_count ?? sessionsState.length,
            todayFixtures: fixturesState.slice(0, 4),
            upcomingTrainingSessions: sessionsState.slice(0, 4),
            activeTournamentsList: competitionsState,
            overdueEquipmentList: equipmentState.filter(e => e.status === "OVERDUE"),
            facilitiesInMaintenanceList: facilitiesState.filter(f => f.status === "MAINTENANCE_CLOSED"),
          },
        };
      }
    } catch {
      // Fallback to local state
    }

    const availableFac = facilitiesState.filter(f => f.status === "AVAILABLE").length;
    const maintFac = facilitiesState.filter(f => f.status === "MAINTENANCE_CLOSED").length;
    const clearedPart = participantsState.filter(p => p.clearanceStatus === "CLEARED").length;

    return {
      success: true,
      data: {
        ...MOCK_SPORTS_DASHBOARD,
        totalDepartments: departmentsState.length,
        totalFacilities: facilitiesState.length,
        facilitiesAvailable: availableFac,
        facilitiesMaintenance: maintFac,
        totalParticipants: participantsState.length,
        participantsCleared: clearedPart,
        clearanceComplianceRate: participantsState.length ? Number(((clearedPart / participantsState.length) * 100).toFixed(1)) : 100,
        totalTeams: teamsState.length,
        todayFixtures: fixturesState.slice(0, 4),
        upcomingTrainingSessions: sessionsState.slice(0, 4),
        activeTournamentsList: competitionsState,
        overdueEquipmentList: equipmentState.filter(e => e.status === "OVERDUE"),
        facilitiesInMaintenanceList: facilitiesState.filter(f => f.status === "MAINTENANCE_CLOSED"),
      },
    };
  }

  // =========================================================================
  // 2. SPORTS DEPARTMENTS
  // =========================================================================

  async listDepartments(campusId?: string): Promise<ApiResponse<SportsDepartmentItem[]>> {
    const qs = campusId && campusId !== "ALL" ? `?campus_id=${campusId}` : "";
    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/departments${qs}`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(d => ({
            id: d.id,
            code: d.code,
            name: d.name,
            campusId: d.campus_id,
            description: d.description,
            status: d.status,
            headUserId: d.head_user_id,
            operatingHours: d.operating_hours,
            policies: d.policies,
            createdAt: d.created_at,
          })),
        };
      }
    } catch {}

    let list = [...departmentsState];
    if (campusId && campusId !== "ALL") {
      list = list.filter(d => d.campusId === campusId);
    }
    return { success: true, data: list };
  }

  async createDepartment(data: Partial<SportsDepartmentItem>): Promise<ApiResponse<SportsDepartmentItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/sports/departments", {
        method: "POST",
        body: JSON.stringify({
          code: data.code,
          name: data.name,
          campus_id: data.campusId,
          description: data.description,
          status: data.status || "ACTIVE",
          head_user_id: data.headUserId,
          operating_hours: data.operatingHours,
          policies: data.policies,
        }),
      });
      if (res.success && res.data) {
        const item: SportsDepartmentItem = {
          id: res.data.id,
          code: res.data.code,
          name: res.data.name,
          campusId: res.data.campus_id,
          description: res.data.description,
          status: res.data.status,
          headUserId: res.data.head_user_id,
          operatingHours: res.data.operating_hours,
          policies: res.data.policies,
          createdAt: res.data.created_at,
        };
        departmentsState.unshift(item);
        return { success: true, data: item };
      }
    } catch {}

    const newItem: SportsDepartmentItem = {
      id: `dept-sports-${Date.now()}`,
      code: data.code || `DEPT-${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "New Athletics Unit",
      campusId: data.campusId,
      description: data.description,
      status: data.status || "ACTIVE",
      headUserId: data.headUserId,
      headUserName: data.headUserName || "Assigned Officer",
      operatingHours: data.operatingHours,
      policies: data.policies,
      facilitiesCount: 0,
      teamsCount: 0,
      createdAt: new Date().toISOString(),
    };
    departmentsState.unshift(newItem);
    return { success: true, data: newItem };
  }

  async updateDepartment(id: string, data: Partial<SportsDepartmentItem>): Promise<ApiResponse<SportsDepartmentItem>> {
    const idx = departmentsState.findIndex(d => d.id === id);
    if (idx !== -1) {
      departmentsState[idx] = { ...departmentsState[idx], ...data };
      return { success: true, data: departmentsState[idx] };
    }
    return { success: false, data: {} as any, error: "Department not found" };
  }

  // =========================================================================
  // 3. SPORTS FACILITIES & COURTS
  // =========================================================================

  async listFacilities(campusId?: string, facilityType?: string): Promise<ApiResponse<SportsFacilityItem[]>> {
    const params = new URLSearchParams();
    if (campusId && campusId !== "ALL") params.append("campus_id", campusId);
    if (facilityType && facilityType !== "ALL") params.append("facility_type", facilityType);
    const qs = params.toString() ? `?${params.toString()}` : "";

    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/facilities${qs}`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(f => ({
            id: f.id,
            code: f.code,
            name: f.name,
            campusId: f.campus_id,
            departmentId: f.department_id,
            facilityType: f.facility_type,
            surface: f.surface,
            isIndoor: f.is_indoor,
            capacity: f.capacity,
            status: f.status,
            maintenanceNotes: f.maintenance_notes,
            equipmentAssetIds: f.equipment_asset_ids,
            operatingHours: f.operating_hours,
            accessibilityInfo: f.accessibility_info,
            createdAt: f.created_at,
          })),
        };
      }
    } catch {}

    let list = [...facilitiesState];
    if (campusId && campusId !== "ALL") list = list.filter(f => f.campusId === campusId);
    if (facilityType && facilityType !== "ALL") list = list.filter(f => f.facilityType === facilityType);
    return { success: true, data: list };
  }

  async createFacility(data: Partial<SportsFacilityItem>): Promise<ApiResponse<SportsFacilityItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/sports/facilities", {
        method: "POST",
        body: JSON.stringify({
          code: data.code,
          name: data.name,
          campus_id: data.campusId,
          department_id: data.departmentId,
          facility_type: data.facilityType,
          surface: data.surface,
          is_indoor: data.isIndoor ?? false,
          capacity: data.capacity ?? 100,
          operating_hours: data.operatingHours,
          accessibility_info: data.accessibilityInfo,
          equipment_asset_ids: data.equipmentAssetIds,
        }),
      });
      if (res.success && res.data) {
        const item: SportsFacilityItem = {
          id: res.data.id,
          code: res.data.code,
          name: res.data.name,
          campusId: res.data.campus_id,
          departmentId: res.data.department_id,
          facilityType: res.data.facility_type,
          surface: res.data.surface,
          isIndoor: res.data.is_indoor,
          capacity: res.data.capacity,
          status: res.data.status,
          maintenanceNotes: res.data.maintenance_notes,
          createdAt: res.data.created_at,
        };
        facilitiesState.unshift(item);
        return { success: true, data: item };
      }
    } catch {}

    const newItem: SportsFacilityItem = {
      id: `fac-${Date.now()}`,
      code: data.code || `FAC-${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "New Sports Facility",
      campusId: data.campusId,
      departmentId: data.departmentId,
      facilityType: data.facilityType || "OUTDOOR_GROUND",
      surface: data.surface || "GRASS",
      isIndoor: data.isIndoor ?? false,
      capacity: data.capacity ?? 200,
      status: "AVAILABLE",
      maintenanceNotes: data.maintenanceNotes,
      equipmentAssetIds: data.equipmentAssetIds || [],
      operatingHours: data.operatingHours || { open: "06:00", close: "20:00" },
      activeBookingsCount: 0,
      createdAt: new Date().toISOString(),
    };
    facilitiesState.unshift(newItem);
    return { success: true, data: newItem };
  }

  async setFacilityMaintenance(id: string, isMaintenance: boolean, notes?: string): Promise<ApiResponse<SportsFacilityItem>> {
    const idx = facilitiesState.findIndex(f => f.id === id);
    if (idx !== -1) {
      facilitiesState[idx].status = isMaintenance ? "MAINTENANCE_CLOSED" : "AVAILABLE";
      if (notes) facilitiesState[idx].maintenanceNotes = notes;
      return { success: true, data: facilitiesState[idx] };
    }
    return { success: false, data: {} as any, error: "Facility not found" };
  }

  async closeFacilityForMaintenance(id: string, notes?: string): Promise<ApiResponse<SportsFacilityItem>> {
    return this.setFacilityMaintenance(id, true, notes);
  }

  async reopenFacility(id: string): Promise<ApiResponse<SportsFacilityItem>> {
    return this.setFacilityMaintenance(id, false);
  }

  // =========================================================================
  // 4. FACILITY BOOKINGS & AVAILABILITY
  // =========================================================================

  async listBookings(facilityId?: string, date?: string): Promise<ApiResponse<FacilityBookingItem[]>> {
    const params = new URLSearchParams();
    if (facilityId) params.append("facility_id", facilityId);
    if (date) params.append("booking_date", date);
    const qs = params.toString() ? `?${params.toString()}` : "";

    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/facility-bookings${qs}`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(b => ({
            id: b.id,
            facilityId: b.facility_id,
            facilityName: facilitiesState.find(f => f.id === b.facility_id)?.name || "Facility",
            title: b.title,
            purpose: b.purpose,
            bookingDate: b.booking_date,
            startTime: b.start_time,
            endTime: b.end_time,
            status: b.status,
            reservedByUserId: b.reserved_by_user_id,
            teamId: b.team_id,
            participantCount: b.participant_count,
            notes: b.notes,
            createdAt: b.created_at,
          })),
        };
      }
    } catch {}

    let list = [...bookingsState];
    if (facilityId && facilityId !== "ALL") list = list.filter(b => b.facilityId === facilityId);
    if (date) list = list.filter(b => b.bookingDate === date);
    return { success: true, data: list };
  }

  async createBooking(data: Partial<FacilityBookingItem>): Promise<ApiResponse<FacilityBookingItem>> {
    // 1. Check for facility maintenance closure
    const facility = facilitiesState.find(f => f.id === data.facilityId);
    if (facility && facility.status === "MAINTENANCE_CLOSED" && data.purpose !== "MAINTENANCE") {
      return {
        success: false,
        data: {} as any,
        error: `Facility "${facility.name}" is currently closed for maintenance. Reservations cannot be scheduled.`,
      };
    }

    // 2. Client-side conflict detection
    const conflict = detectFacilityBookingConflict(
      bookingsState.map(b => ({
        id: b.id,
        facilityId: b.facilityId,
        bookingDate: b.bookingDate,
        startTime: b.startTime,
        endTime: b.endTime,
        status: b.status,
      })),
      {
        facilityId: data.facilityId!,
        bookingDate: data.bookingDate!,
        startTime: data.startTime!,
        endTime: data.endTime!,
      }
    );

    if (conflict.hasConflict) {
      return {
        success: false,
        data: {} as any,
        error: conflict.message || "Overlapping booking detected for this facility and time window.",
      };
    }

    try {
      const res = await apiFetch<any>("/api/v1/sports/facility-bookings", {
        method: "POST",
        body: JSON.stringify({
          facility_id: data.facilityId,
          booking_date: data.bookingDate,
          start_time: data.startTime,
          end_time: data.endTime,
          purpose: data.purpose,
          title: data.title,
          team_id: data.teamId,
          participant_count: data.participantCount,
          notes: data.notes,
        }),
      });
      if (res.success && res.data) {
        const item: FacilityBookingItem = {
          id: res.data.id,
          facilityId: res.data.facility_id,
          facilityName: facility?.name || "Facility",
          title: res.data.title,
          purpose: res.data.purpose,
          bookingDate: res.data.booking_date,
          startTime: res.data.start_time,
          endTime: res.data.end_time,
          status: res.data.status,
          reservedByUserId: res.data.reserved_by_user_id,
          teamId: res.data.team_id,
          participantCount: res.data.participant_count,
          notes: res.data.notes,
          createdAt: res.data.created_at,
        };
        bookingsState.unshift(item);
        return { success: true, data: item };
      }
    } catch (err: any) {
      if (err.message && err.message.includes("conflict")) {
        return { success: false, data: {} as any, error: err.message };
      }
    }

    const newBooking: FacilityBookingItem = {
      id: `book-${Date.now()}`,
      facilityId: data.facilityId!,
      facilityName: facility?.name || "Court Arena",
      title: data.title || "Facility Reservation",
      purpose: data.purpose || "TRAINING",
      bookingDate: data.bookingDate!,
      startTime: data.startTime!,
      endTime: data.endTime!,
      status: "CONFIRMED",
      reservedByUserName: "Sports Coordinator",
      teamId: data.teamId,
      teamName: data.teamName,
      participantCount: data.participantCount || 10,
      notes: data.notes,
      createdAt: new Date().toISOString(),
    };
    bookingsState.unshift(newBooking);
    return { success: true, data: newBooking };
  }

  async cancelBooking(id: string, reason?: string): Promise<ApiResponse<FacilityBookingItem>> {
    const idx = bookingsState.findIndex(b => b.id === id);
    if (idx !== -1) {
      bookingsState[idx].status = "CANCELLED";
      if (reason) bookingsState[idx].notes = `${bookingsState[idx].notes || ""} [Cancelled: ${reason}]`;
      return { success: true, data: bookingsState[idx] };
    }
    return { success: false, data: {} as any, error: "Booking not found" };
  }

  // =========================================================================
  // 5. PARTICIPANTS & ATHLETIC PROFILES
  // =========================================================================

  async listParticipants(sport?: string, clearanceStatus?: string): Promise<ApiResponse<SportsParticipantItem[]>> {
    const params = new URLSearchParams();
    if (sport && sport !== "ALL") params.append("sport", sport);
    if (clearanceStatus && clearanceStatus !== "ALL") params.append("clearance_status", clearanceStatus);
    const qs = params.toString() ? `?${params.toString()}` : "";

    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/participants${qs}`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(p => ({
            id: p.id,
            userId: p.user_id,
            userName: p.user_name || "Athlete",
            userEmail: p.user_email || "",
            participantCode: p.participant_code,
            primarySport: p.primary_sport,
            status: p.status,
            clearanceStatus: p.clearance_status,
            clearanceExpiry: p.clearance_expiry,
            consentRecorded: p.consent_recorded,
            consentDate: p.consent_date,
            operationalRestrictions: p.operational_restrictions,
            sportsHistory: p.sports_history,
            notes: p.notes,
            createdAt: p.created_at,
          })),
        };
      }
    } catch {}

    let list = [...participantsState];
    if (sport && sport !== "ALL") list = list.filter(p => p.primarySport.toLowerCase() === sport.toLowerCase());
    if (clearanceStatus && clearanceStatus !== "ALL") list = list.filter(p => p.clearanceStatus === clearanceStatus);
    return { success: true, data: list };
  }

  async createParticipant(data: Partial<SportsParticipantItem>): Promise<ApiResponse<SportsParticipantItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/sports/participants", {
        method: "POST",
        body: JSON.stringify({
          user_id: data.userId,
          participant_code: data.participantCode,
          primary_sport: data.primarySport,
          status: data.status || "ACTIVE",
          clearance_status: data.clearanceStatus || "CLEARED",
          clearance_expiry: data.clearanceExpiry,
          consent_recorded: data.consentRecorded ?? true,
          operational_restrictions: data.operationalRestrictions,
          sports_history: data.sportsHistory,
          notes: data.notes,
        }),
      });
      if (res.success && res.data) {
        const item: SportsParticipantItem = {
          id: res.data.id,
          userId: res.data.user_id,
          userName: data.userName || "Student Athlete",
          userEmail: data.userEmail || "",
          participantCode: res.data.participant_code,
          primarySport: res.data.primary_sport,
          status: res.data.status,
          clearanceStatus: res.data.clearance_status,
          clearanceExpiry: res.data.clearance_expiry,
          consentRecorded: res.data.consent_recorded,
          consentDate: res.data.consent_date,
          operationalRestrictions: res.data.operational_restrictions,
          sportsHistory: res.data.sports_history,
          notes: res.data.notes,
          createdAt: res.data.created_at,
        };
        participantsState.unshift(item);
        return { success: true, data: item };
      }
    } catch {}

    const newItem: SportsParticipantItem = {
      id: `part-${Date.now()}`,
      userId: data.userId || `user-${Date.now()}`,
      userName: data.userName || "Student Athlete",
      userEmail: data.userEmail || "athlete@campusos.edu",
      department: data.department || "Athletics",
      participantCode: data.participantCode || `ATH-2026-${Math.floor(100 + Math.random() * 900)}`,
      primarySport: data.primarySport || "Basketball",
      status: data.status || "ACTIVE",
      clearanceStatus: data.clearanceStatus || "CLEARED",
      clearanceExpiry: data.clearanceExpiry || "2027-06-30",
      consentRecorded: data.consentRecorded ?? true,
      consentDate: new Date().toISOString().split("T")[0],
      operationalRestrictions: data.operationalRestrictions || {},
      sportsHistory: data.sportsHistory || {},
      notes: data.notes,
      activeTeamsCount: 0,
      createdAt: new Date().toISOString(),
    };
    participantsState.unshift(newItem);
    return { success: true, data: newItem };
  }

  async updateParticipantClearance(
    id: string,
    status: string,
    restrictions?: Record<string, any>
  ): Promise<ApiResponse<SportsParticipantItem>> {
    const idx = participantsState.findIndex(p => p.id === id);
    if (idx !== -1) {
      participantsState[idx].clearanceStatus = status;
      if (restrictions) participantsState[idx].operationalRestrictions = restrictions;
      return { success: true, data: participantsState[idx] };
    }
    return { success: false, data: {} as any, error: "Participant not found" };
  }

  // =========================================================================
  // 6. TEAMS & ROSTERS
  // =========================================================================

  async listTeams(sport?: string, category?: string): Promise<ApiResponse<SportsTeamItem[]>> {
    const params = new URLSearchParams();
    if (sport && sport !== "ALL") params.append("sport", sport);
    if (category && category !== "ALL") params.append("category", category);
    const qs = params.toString() ? `?${params.toString()}` : "";

    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/teams${qs}`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(t => ({
            id: t.id,
            code: t.code,
            name: t.name,
            campusId: t.campus_id,
            departmentId: t.department_id,
            sport: t.sport,
            category: t.category,
            genderCategory: t.gender_category,
            captainParticipantId: t.captain_participant_id,
            captainName: t.captain_name,
            headCoachUserId: t.head_coach_user_id,
            headCoachName: t.head_coach_name,
            maxRosterSize: t.max_roster_size,
            activeRosterCount: t.active_roster_count ?? 0,
            status: t.status,
            createdAt: t.created_at,
          })),
        };
      }
    } catch {}

    let list = [...teamsState];
    if (sport && sport !== "ALL") list = list.filter(t => t.sport.toLowerCase() === sport.toLowerCase());
    if (category && category !== "ALL") list = list.filter(t => t.category === category);
    return { success: true, data: list };
  }

  async createTeam(data: Partial<SportsTeamItem>): Promise<ApiResponse<SportsTeamItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/sports/teams", {
        method: "POST",
        body: JSON.stringify({
          code: data.code,
          name: data.name,
          campus_id: data.campusId,
          department_id: data.departmentId,
          sport: data.sport,
          category: data.category,
          gender_category: data.genderCategory || "COED",
          captain_participant_id: data.captainParticipantId,
          head_coach_user_id: data.headCoachUserId,
          max_roster_size: data.maxRosterSize || 20,
        }),
      });
      if (res.success && res.data) {
        const item: SportsTeamItem = {
          id: res.data.id,
          code: res.data.code,
          name: res.data.name,
          campusId: res.data.campus_id,
          departmentId: res.data.department_id,
          sport: res.data.sport,
          category: res.data.category,
          genderCategory: res.data.gender_category,
          captainParticipantId: res.data.captain_participant_id,
          headCoachUserId: res.data.head_coach_user_id,
          maxRosterSize: res.data.max_roster_size,
          activeRosterCount: 0,
          status: res.data.status,
          createdAt: res.data.created_at,
        };
        teamsState.unshift(item);
        return { success: true, data: item };
      }
    } catch {}

    const newTeam: SportsTeamItem = {
      id: `team-${Date.now()}`,
      code: data.code || `TEAM-${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "University Sports Squad",
      campusId: data.campusId,
      departmentId: data.departmentId,
      sport: data.sport || "Football",
      category: data.category || "VARSITY",
      genderCategory: data.genderCategory || "COED",
      captainParticipantId: data.captainParticipantId,
      captainName: data.captainName,
      headCoachUserId: data.headCoachUserId,
      headCoachName: data.headCoachName,
      maxRosterSize: data.maxRosterSize || 20,
      activeRosterCount: 0,
      status: "ACTIVE",
      createdAt: new Date().toISOString(),
    };
    teamsState.unshift(newTeam);
    return { success: true, data: newTeam };
  }

  async getTeamRoster(teamId: string): Promise<ApiResponse<TeamRosterMemberItem[]>> {
    try {
      const res = await apiFetch<any[]>(`/api/v1/sports/teams/${teamId}/roster`);
      if (res.success && res.data) {
        return {
          success: true,
          data: res.data.map(m => ({
            id: m.id,
            teamId: m.team_id,
            participantId: m.participant_id,
            participantCode: m.participant_code,
            participantName: m.participant_name,
            role: m.role,
            jerseyNumber: m.jersey_number,
            position: m.position,
            status: m.status,
            joinedAt: m.joined_at,
            leftAt: m.left_at,
          })),
        };
      }
    } catch {}

    return {
      success: true,
      data: rosterState.filter(m => m.teamId === teamId && m.status === "ACTIVE"),
    };
  }

  async addTeamMember(teamId: string, data: Partial<TeamRosterMemberItem>): Promise<ApiResponse<TeamRosterMemberItem>> {
    // Check max roster limit
    const team = teamsState.find(t => t.id === teamId);
    const currentCount = rosterState.filter(m => m.teamId === teamId && m.status === "ACTIVE").length;
    if (team && currentCount >= team.maxRosterSize) {
      return {
        success: false,
        data: {} as any,
        error: `Team "${team.name}" has reached its maximum roster capacity of ${team.maxRosterSize} players.`,
      };
    }

    // Check participant clearance for Varsity teams
    const participant = participantsState.find(p => p.id === data.participantId);
    if (team?.category === "VARSITY" && participant) {
      if (!["CLEARED", "RESTRICTED"].includes(participant.clearanceStatus)) {
        return {
          success: false,
          data: {} as any,
          error: `Participant "${participant.participantCode}" does not hold active athletic clearance (${participant.clearanceStatus}).`,
        };
      }
    }

    try {
      const res = await apiFetch<any>(`/api/v1/sports/teams/${teamId}/roster`, {
        method: "POST",
        body: JSON.stringify({
          participant_id: data.participantId,
          role: data.role || "PLAYER",
          jersey_number: data.jerseyNumber,
          position: data.position,
        }),
      });
      if (res.success && res.data) {
        const item: TeamRosterMemberItem = {
          id: res.data.id,
          teamId: res.data.team_id,
          participantId: res.data.participant_id,
          participantCode: participant?.participantCode || "ATH-001",
          participantName: participant?.userName || "Athlete",
          role: res.data.role,
          jerseyNumber: res.data.jersey_number,
          position: res.data.position,
          status: res.data.status,
          joinedAt: res.data.joined_at,
        };
        rosterState.push(item);
        if (team) team.activeRosterCount += 1;
        return { success: true, data: item };
      }
    } catch {}

    const newMember: TeamRosterMemberItem = {
      id: `roster-${Date.now()}`,
      teamId,
      participantId: data.participantId!,
      participantCode: participant?.participantCode || "ATH-001",
      participantName: participant?.userName || "Athlete",
      role: data.role || "PLAYER",
      jerseyNumber: data.jerseyNumber,
      position: data.position,
      status: "ACTIVE",
      joinedAt: new Date().toISOString().split("T")[0],
      clearanceStatus: participant?.clearanceStatus || "CLEARED",
    };
    rosterState.push(newMember);
    if (team) team.activeRosterCount += 1;
    return { success: true, data: newMember };
  }

  // =========================================================================
  // 7. COACHES & OFFICIALS
  // =========================================================================

  async listCoachingAssignments(teamId?: string): Promise<ApiResponse<CoachingAssignmentItem[]>> {
    let list = [...coachingState];
    if (teamId && teamId !== "ALL") list = list.filter(c => c.teamId === teamId);
    return { success: true, data: list };
  }

  async assignCoach(data: Partial<CoachingAssignmentItem>): Promise<ApiResponse<CoachingAssignmentItem>> {
    const newItem: CoachingAssignmentItem = {
      id: `coach-asgn-${Date.now()}`,
      coachUserId: data.coachUserId || `coach-${Date.now()}`,
      coachName: data.coachName || "Coach Name",
      teamId: data.teamId,
      teamName: data.teamName,
      sport: data.sport || "Basketball",
      role: data.role || "HEAD_COACH",
      certificationLevel: data.certificationLevel || "Certified University Coach",
      isPrimary: data.isPrimary ?? true,
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      status: "ACTIVE",
    };
    coachingState.push(newItem);
    return { success: true, data: newItem };
  }

  // =========================================================================
  // 8. TRAINING PROGRAMS & ATTENDANCE
  // =========================================================================

  async listTrainingPrograms(sport?: string): Promise<ApiResponse<TrainingProgramItem[]>> {
    let list = [...programsState];
    if (sport && sport !== "ALL") list = list.filter(p => p.sport.toLowerCase() === sport.toLowerCase());
    return { success: true, data: list };
  }

  async createTrainingProgram(data: Partial<TrainingProgramItem>): Promise<ApiResponse<TrainingProgramItem>> {
    const newProg: TrainingProgramItem = {
      id: `prog-${Date.now()}`,
      code: data.code || `PROG-${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "Specialized Training Camp",
      programType: data.programType || "DEVELOPMENT",
      sport: data.sport || "Swimming",
      leadCoachUserId: data.leadCoachUserId,
      leadCoachName: data.leadCoachName || "Lead Coach",
      facilityId: data.facilityId,
      facilityName: facilitiesState.find(f => f.id === data.facilityId)?.name || "Facility",
      capacity: data.capacity || 25,
      enrolledCount: 0,
      startDate: data.startDate || new Date().toISOString().split("T")[0],
      endDate: data.endDate || new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
      feeAmount: data.feeAmount,
      status: "ACTIVE",
      createdAt: new Date().toISOString(),
    };
    programsState.unshift(newProg);
    return { success: true, data: newProg };
  }

  async listTrainingSessions(programId?: string): Promise<ApiResponse<TrainingSessionItem[]>> {
    let list = [...sessionsState];
    if (programId && programId !== "ALL") list = list.filter(s => s.programId === programId);
    return { success: true, data: list };
  }

  async recordSessionAttendance(
    sessionId: string,
    records: Array<{ participantId: string; status: string; notes?: string }>
  ): Promise<ApiResponse<TrainingAttendanceItem[]>> {
    const created: TrainingAttendanceItem[] = records.map(r => {
      const part = participantsState.find(p => p.id === r.participantId);
      return {
        id: `att-${Date.now()}-${Math.random().toString(36).substring(7)}`,
        sessionId,
        participantId: r.participantId,
        participantName: part?.userName || "Athlete",
        participantCode: part?.participantCode || "ATH-000",
        status: r.status,
        notes: r.notes,
        recordedAt: new Date().toISOString(),
        recordedByUserName: "Coach In Charge",
      };
    });
    attendanceState.push(...created);
    return { success: true, data: created };
  }

  // =========================================================================
  // 9. COMPETITIONS & TOURNAMENT ENGINE
  // =========================================================================

  async listCompetitions(sport?: string, status?: string): Promise<ApiResponse<SportsCompetitionItem[]>> {
    let list = [...competitionsState];
    if (sport && sport !== "ALL") list = list.filter(c => c.sport.toLowerCase() === sport.toLowerCase());
    if (status && status !== "ALL") list = list.filter(c => c.status === status);
    return { success: true, data: list };
  }

  async createCompetition(data: Partial<SportsCompetitionItem>): Promise<ApiResponse<SportsCompetitionItem>> {
    const newComp: SportsCompetitionItem = {
      id: `comp-${Date.now()}`,
      code: data.code || `COMP-${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "University Championship",
      campusId: data.campusId,
      departmentId: data.departmentId,
      competitionType: data.competitionType || "INTERNAL",
      tournamentFormat: data.tournamentFormat || "ROUND_ROBIN",
      sport: data.sport || "Football",
      registrationType: data.registrationType || "TEAM",
      standingRule: data.standingRule || "GOAL_DIFFERENCE",
      pointsForWin: data.pointsForWin ?? 3,
      pointsForDraw: data.pointsForDraw ?? 1,
      pointsForLoss: data.pointsForLoss ?? 0,
      startDate: data.startDate || new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0],
      endDate: data.endDate || new Date(Date.now() + 21 * 86400000).toISOString().split("T")[0],
      registrationDeadline: data.registrationDeadline || new Date(Date.now() + 5 * 86400000).toISOString().split("T")[0],
      maxParticipants: data.maxParticipants || 8,
      registeredCount: 0,
      feeAmount: data.feeAmount,
      status: "REGISTRATION_OPEN",
      fixturesCount: 0,
      createdAt: new Date().toISOString(),
    };
    competitionsState.unshift(newComp);
    return { success: true, data: newComp };
  }

  async listCompetitionRegistrations(competitionId: string): Promise<ApiResponse<CompetitionRegistrationItem[]>> {
    return {
      success: true,
      data: registrationsState.filter(r => r.competitionId === competitionId),
    };
  }

  async registerCompetitionEntry(
    competitionId: string,
    entry: { teamId?: string; participantId?: string }
  ): Promise<ApiResponse<CompetitionRegistrationItem>> {
    const team = teamsState.find(t => t.id === entry.teamId);
    const participant = participantsState.find(p => p.id === entry.participantId);

    const newReg: CompetitionRegistrationItem = {
      id: `reg-${Date.now()}`,
      competitionId,
      teamId: entry.teamId,
      teamName: team?.name,
      participantId: entry.participantId,
      participantName: participant?.userName,
      status: "CONFIRMED",
      paymentStatus: "PAID",
      registeredAt: new Date().toISOString(),
    };
    registrationsState.push(newReg);

    const comp = competitionsState.find(c => c.id === competitionId);
    if (comp) comp.registeredCount += 1;

    return { success: true, data: newReg };
  }

  async generateFixtures(
    competitionId: string,
    facilityIds: string[] = [],
    startDate: string = "2026-11-15",
    startTime: string = "15:00"
  ): Promise<ApiResponse<MatchFixtureItem[]>> {
    const comp = competitionsState.find(c => c.id === competitionId);
    let regs = registrationsState.filter(r => r.competitionId === competitionId);

    if (regs.length < 2) {
      // Auto-populate from active campus squads
      const fallbackTeams = teamsState.slice(0, 4);
      fallbackTeams.forEach((t, i) => {
        registrationsState.push({
          id: `reg-auto-${Date.now()}-${i}`,
          competitionId,
          teamId: t.id,
          teamName: t.name,
          status: "CONFIRMED",
          paymentStatus: "PAID",
          registeredAt: new Date().toISOString(),
        });
      });
      regs = registrationsState.filter(r => r.competitionId === competitionId);
    }

    const entrantIds = regs.map(r => r.teamId || r.participantId || r.id);
    const roundRobinSlots = generateRoundRobinFixtures(entrantIds);

    const generated: MatchFixtureItem[] = roundRobinSlots.map((slot, idx) => {
      const homeTeam = teamsState.find(t => t.id === slot.home);
      const awayTeam = teamsState.find(t => t.id === slot.away);
      const homePart = participantsState.find(p => p.id === slot.home);
      const awayPart = participantsState.find(p => p.id === slot.away);
      const facilityId = facilityIds.length ? facilityIds[idx % facilityIds.length] : facilitiesState[0]?.id;

      return {
        id: `fix-gen-${Date.now()}-${idx + 1}`,
        competitionId,
        competitionName: comp?.name,
        matchNumber: idx + 1,
        stage: "LEAGUE",
        roundNumber: slot.round,
        homeTeamId: homeTeam?.id,
        homeTeamName: homeTeam?.name,
        awayTeamId: awayTeam?.id,
        awayTeamName: awayTeam?.name,
        homeParticipantId: homePart?.id,
        homeParticipantName: homePart?.userName,
        awayParticipantId: awayPart?.id,
        awayParticipantName: awayPart?.userName,
        facilityId,
        facilityName: facilitiesState.find(f => f.id === facilityId)?.name || "Main Court",
        matchDate: startDate,
        startTime,
        endTime: "18:00",
        status: "SCHEDULED",
      };
    });

    fixturesState.push(...generated);
    if (comp) {
      comp.status = "SCHEDULED";
      comp.fixturesCount = generated.length;
    }

    return { success: true, data: generated };
  }

  async listFixtures(competitionId?: string, date?: string): Promise<ApiResponse<MatchFixtureItem[]>> {
    let list = [...fixturesState];
    if (competitionId && competitionId !== "ALL") list = list.filter(f => f.competitionId === competitionId);
    if (date) list = list.filter(f => f.matchDate === date);
    return { success: true, data: list };
  }

  async updateFixture(id: string, data: Partial<MatchFixtureItem>): Promise<ApiResponse<MatchFixtureItem>> {
    const idx = fixturesState.findIndex(f => f.id === id);
    if (idx !== -1) {
      fixturesState[idx] = { ...fixturesState[idx], ...data };
      return { success: true, data: fixturesState[idx] };
    }
    return { success: false, data: {} as any, error: "Fixture not found" };
  }

  async assignOfficial(fixtureId: string, officialUserId: string, role: string): Promise<ApiResponse<MatchFixtureItem>> {
    const fixture = fixturesState.find(f => f.id === fixtureId);
    if (!fixture) return { success: false, data: {} as any, error: "Fixture not found" };

    if (!fixture.officials) fixture.officials = [];
    fixture.officials.push({
      id: `off-${Date.now()}`,
      fixtureId,
      officialUserId,
      officialName: "Certified Official",
      role: role as any,
      isConfirmed: true,
    });

    return { success: true, data: fixture };
  }

  // =========================================================================
  // 10. MATCH RESULTS, VERIFICATION & STANDINGS
  // =========================================================================

  async recordMatchResult(
    fixtureId: string,
    dataOrHomeScore: Partial<MatchResultItem> | number,
    awayScoreVal?: number,
    auditNotesVal?: string
  ): Promise<ApiResponse<MatchResultItem>> {
    const fixture = fixturesState.find(f => f.id === fixtureId);
    if (!fixture) return { success: false, data: {} as any, error: "Fixture not found" };

    const data: Partial<MatchResultItem> =
      typeof dataOrHomeScore === "number"
        ? {
            homeScore: dataOrHomeScore,
            awayScore: awayScoreVal ?? 0,
            auditNotes: auditNotesVal,
          }
        : dataOrHomeScore;

    const isDraw = data.homeScore === data.awayScore;
    let winnerTeamId = data.winnerTeamId;
    if (!winnerTeamId && !isDraw) {
      winnerTeamId = (data.homeScore || 0) > (data.awayScore || 0) ? fixture.homeTeamId : fixture.awayTeamId;
    }

    const resultItem: MatchResultItem = {
      id: `res-${Date.now()}`,
      fixtureId,
      winnerTeamId,
      isDraw,
      isForfeit: data.isForfeit ?? false,
      isAbandoned: data.isAbandoned ?? false,
      homeScore: data.homeScore ?? 0,
      awayScore: data.awayScore ?? 0,
      scoreBreakdown: data.scoreBreakdown,
      verifiedByName: data.auditNotes ? "Verified with Notes" : "Pending Verification",
      auditNotes: data.auditNotes,
    };

    fixture.result = resultItem;
    fixture.status = "COMPLETED";

    return { success: true, data: resultItem };
  }

  async verifyMatchResult(
    fixtureId: string,
    verifiedByName: string,
    auditNotes?: string
  ): Promise<ApiResponse<MatchResultItem>> {
    const fixture = fixturesState.find(f => f.id === fixtureId);
    if (!fixture || !fixture.result) {
      return { success: false, data: {} as any, error: "Match result not found" };
    }

    fixture.result.verifiedByName = verifiedByName;
    fixture.result.verifiedAt = new Date().toISOString();
    fixture.result.auditNotes = auditNotes;

    return { success: true, data: fixture.result };
  }

  async getCompetitionStandings(competitionId: string): Promise<ApiResponse<CompetitionStandingItem[]>> {
    const compFixtures = fixturesState.filter(f => f.competitionId === competitionId && f.result);
    if (compFixtures.length === 0) {
      return {
        success: true,
        data: standingsState.filter(s => s.competitionId === competitionId),
      };
    }

    // Dynamic computation from recorded fixtures
    const competitors: Array<{ id: string; name: string }> = [];
    compFixtures.forEach(f => {
      if (f.homeTeamId && !competitors.some(c => c.id === f.homeTeamId)) {
        competitors.push({ id: f.homeTeamId, name: f.homeTeamName || "Team" });
      }
      if (f.awayTeamId && !competitors.some(c => c.id === f.awayTeamId)) {
        competitors.push({ id: f.awayTeamId, name: f.awayTeamName || "Team" });
      }
    });

    const computed = computeTournamentStandings(
      competitors,
      compFixtures.map(f => ({
        homeCompetitorId: f.homeTeamId || "",
        awayCompetitorId: f.awayTeamId || "",
        homeScore: f.result!.homeScore,
        awayScore: f.result!.awayScore,
        status: f.status,
      }))
    );

    const standings: CompetitionStandingItem[] = computed.map(row => ({
      id: `stand-${row.competitorId}`,
      competitionId,
      teamId: row.competitorId,
      teamName: row.competitorName,
      rank: row.rank,
      played: row.played,
      won: row.won,
      drawn: row.drawn,
      lost: row.lost,
      pointsFor: row.pointsFor,
      pointsAgainst: row.pointsAgainst,
      pointDifference: row.pointDifference,
      points: row.points,
      formGuide: row.formGuide,
    }));

    return { success: true, data: standings };
  }

  // =========================================================================
  // 11. ACHIEVEMENTS & RECORDS
  // =========================================================================

  async listAchievements(sport?: string): Promise<ApiResponse<SportsAchievementItem[]>> {
    let list = [...achievementsState];
    if (sport && sport !== "ALL") list = list.filter(a => a.sport.toLowerCase() === sport.toLowerCase());
    return { success: true, data: list };
  }

  async createAchievement(data: Partial<SportsAchievementItem>): Promise<ApiResponse<SportsAchievementItem>> {
    const newItem: SportsAchievementItem = {
      id: `ach-${Date.now()}`,
      recipientType: data.recipientType || "TEAM",
      teamId: data.teamId,
      teamName: data.teamName,
      participantId: data.participantId,
      participantName: data.participantName,
      sport: data.sport || "Basketball",
      title: data.title || "Championship Recognition",
      level: data.level || "INSTITUTIONAL",
      medal: data.medal || "GOLD",
      awardDate: data.awardDate || new Date().toISOString().split("T")[0],
      citation: data.citation,
      certificateNumber: data.certificateNumber || `CERT-${Date.now()}`,
    };
    achievementsState.unshift(newItem);
    return { success: true, data: newItem };
  }

  // =========================================================================
  // 12. EQUIPMENT ALLOCATION & ASSET INTEGRATION
  // =========================================================================

  async listEquipmentAssignments(status?: string): Promise<ApiResponse<SportsEquipmentAssignmentItem[]>> {
    let list = [...equipmentState];
    if (status && status !== "ALL") list = list.filter(e => e.status === status);
    return { success: true, data: list };
  }

  async checkoutEquipment(data: Partial<SportsEquipmentAssignmentItem>): Promise<ApiResponse<SportsEquipmentAssignmentItem>> {
    const newItem: SportsEquipmentAssignmentItem = {
      id: `eq-asgn-${Date.now()}`,
      assetId: data.assetId,
      equipmentName: data.equipmentName || "Sports Equipment Kit",
      itemCode: data.itemCode || `EQ-${Math.floor(100 + Math.random() * 900)}`,
      category: data.category || "GEAR_SET",
      allocatedQuantity: data.allocatedQuantity || 1,
      teamId: data.teamId,
      teamName: data.teamName,
      facilityId: data.facilityId,
      facilityName: data.facilityName,
      responsibleUserId: data.responsibleUserId || "user-coach-01",
      responsibleUserName: data.responsibleUserName || "Responsible Coach",
      checkoutDate: data.checkoutDate || new Date().toISOString().split("T")[0],
      dueDate: data.dueDate || new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
      status: "ISSUED",
      returnCondition: "EXCELLENT",
      conditionNotes: data.conditionNotes || "Checked out in clean operational state.",
    };
    equipmentState.unshift(newItem);
    return { success: true, data: newItem };
  }

  async returnEquipment(
    id: string,
    returnCondition: string,
    notesOrFee?: string | number,
    feeOrNotes?: number | string
  ): Promise<ApiResponse<SportsEquipmentAssignmentItem>> {
    const idx = equipmentState.findIndex(e => e.id === id);
    if (idx !== -1) {
      const notes = typeof notesOrFee === "string" ? notesOrFee : typeof feeOrNotes === "string" ? feeOrNotes : "";
      const replacementFee = typeof notesOrFee === "number" ? notesOrFee : typeof feeOrNotes === "number" ? feeOrNotes : undefined;

      equipmentState[idx].status = "RETURNED";
      equipmentState[idx].returnDate = new Date().toISOString().split("T")[0];
      equipmentState[idx].returnCondition = returnCondition as any;
      if (notes) equipmentState[idx].conditionNotes = notes;
      if (replacementFee !== undefined) equipmentState[idx].replacementFee = replacementFee;
      return { success: true, data: equipmentState[idx] };
    }
    return { success: false, data: {} as any, error: "Equipment record not found" };
  }

  // =========================================================================
  // 13. SPORTS FEES & FINANCIAL OPERATIONS
  // =========================================================================

  async listSportsFees(status?: string): Promise<ApiResponse<SportsFeeItem[]>> {
    let list = [...feesState];
    if (status && status !== "ALL") list = list.filter(f => f.status === status);
    return { success: true, data: list };
  }

  // =========================================================================
  // 14. REPORTS & ANALYTICS
  // =========================================================================

  async getReportsAnalytics(): Promise<
    ApiResponse<{
      facilityUtilization: Array<{ facilityName: string; bookedHours: number; availableHours: number; rate: number }>;
      participationDemographics: Array<{ sport: string; count: number; percentage: number }>;
      clearanceCompliance: { totalAthletes: number; cleared: number; restricted: number; suspended: number; rate: number };
      tournamentSummaries: Array<{ name: string; sport: string; format: string; teams: number; matches: number; status: string }>;
    }>
  > {
    const totalAthletes = participantsState.length;
    const cleared = participantsState.filter(p => p.clearanceStatus === "CLEARED").length;
    const restricted = participantsState.filter(p => p.clearanceStatus === "RESTRICTED").length;
    const suspended = participantsState.filter(p => p.clearanceStatus === "SUSPENDED").length;

    return {
      success: true,
      data: {
        facilityUtilization: facilitiesState.slice(0, 6).map(f => ({
          facilityName: f.name,
          bookedHours: 28,
          availableHours: 35,
          rate: 80,
        })),
        participationDemographics: [
          { sport: "Football", count: 42, percentage: 28.4 },
          { sport: "Basketball", count: 36, percentage: 24.3 },
          { sport: "Swimming", count: 25, percentage: 16.9 },
          { sport: "Badminton", count: 24, percentage: 16.2 },
          { sport: "Cricket", count: 21, percentage: 14.2 },
        ],
        clearanceCompliance: {
          totalAthletes,
          cleared,
          restricted,
          suspended,
          rate: totalAthletes ? Number(((cleared / totalAthletes) * 100).toFixed(1)) : 100,
        },
        tournamentSummaries: competitionsState.map(c => ({
          name: c.name,
          sport: c.sport,
          format: c.tournamentFormat,
          teams: c.registeredCount,
          matches: c.fixturesCount || 0,
          status: c.status,
        })),
      },
    };
  }

  // =========================================================================
  // CONVENIENCE ALIASES
  // =========================================================================
  async getCompetitions(sport?: string, status?: string) { return this.listCompetitions(sport, status); }
  async getFixtures(competitionId?: string, date?: string) { return this.listFixtures(competitionId, date); }
  async getStandings(competitionId: string) { return this.getCompetitionStandings(competitionId); }
  async getAchievements(sport?: string) { return this.listAchievements(sport); }
  async getEquipmentAssignments(status?: string) { return this.listEquipmentAssignments(status); }
  async rescheduleFixture(fixtureId: string, newDate: string, newTime: string, newVenue?: string) {
    return this.updateFixture(fixtureId, { matchDate: newDate, startTime: newTime, facilityName: newVenue });
  }
}

export const sportsService = new SportsService();
