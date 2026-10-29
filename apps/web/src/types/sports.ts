/**
 * CampusOS Sports, Athletics, Recreation & Student Fitness Domain Types
 * Product Tagline: "One Campus. One System. One Source of Truth."
 */

export * from "@campusos/types";

import type {
  SportsDepartmentStatus,
  SportsActivityCategory,
  SportsFacilityType,
  SportsFacilitySurface,
  SportsFacilityStatus,
  FacilityBookingPurpose,
  FacilityBookingStatus,
  SportsParticipantStatus,
  SportsClearanceStatus,
  SportsMemberRole,
  SportsRosterStatus,
  SportsCoachingRole,
  SportsProgramType,
  SportsAttendanceStatus,
  SportsCompetitionType,
  SportsTournamentFormat,
  SportsRegistrationType,
  SportsStandingRule,
  SportsCompetitionStatus,
  SportsFixtureStatus,
  SportsMatchStage,
  SportsOfficialRole,
  SportsMedal,
  SportsRecognitionLevel,
  SportsCheckoutStatus,
  SportsEquipmentCondition,
} from "@campusos/types";

// =============================================================================
// FRONTEND VIEW MODELS & INTERFACES
// =============================================================================

export interface SportsDepartmentItem {
  id: string;
  code: string;
  name: string;
  campusId?: string | null;
  campusName?: string;
  description?: string;
  status: SportsDepartmentStatus | string;
  headUserId?: string | null;
  headUserName?: string;
  operatingHours?: Record<string, any>;
  policies?: Record<string, any>;
  createdAt?: string;
  facilitiesCount?: number;
  teamsCount?: number;
}

export interface SportsFacilityItem {
  id: string;
  code: string;
  name: string;
  campusId?: string | null;
  campusName?: string;
  departmentId?: string | null;
  departmentName?: string;
  facilityType: SportsFacilityType | string;
  surface: SportsFacilitySurface | string;
  isIndoor: boolean;
  capacity: number;
  status: SportsFacilityStatus | string;
  maintenanceNotes?: string;
  equipmentAssetIds?: string[];
  operatingHours?: Record<string, any>;
  accessibilityInfo?: Record<string, any>;
  activeBookingsCount?: number;
  createdAt?: string;
}

export interface FacilityBookingItem {
  id: string;
  facilityId: string;
  facilityName: string;
  campusId?: string | null;
  title: string;
  purpose: FacilityBookingPurpose | string;
  bookingDate: string;
  startTime: string;
  endTime: string;
  status: FacilityBookingStatus | string;
  reservedByUserId?: string | null;
  reservedByUserName?: string;
  teamId?: string | null;
  teamName?: string;
  trainingSessionId?: string | null;
  matchFixtureId?: string | null;
  participantCount?: number;
  notes?: string;
  createdAt?: string;
}

export interface SportsParticipantItem {
  id: string;
  userId: string;
  userName: string;
  userEmail: string;
  userRole?: string;
  department?: string;
  participantCode: string;
  primarySport: string;
  status: SportsParticipantStatus | string;
  clearanceStatus: SportsClearanceStatus | string;
  clearanceExpiry?: string;
  consentRecorded: boolean;
  consentDate?: string;
  operationalRestrictions?: Record<string, any>;
  sportsHistory?: Record<string, any>;
  notes?: string;
  activeTeamsCount?: number;
  createdAt?: string;
}

export interface SportsTeamItem {
  id: string;
  code: string;
  name: string;
  campusId?: string | null;
  campusName?: string;
  departmentId?: string | null;
  departmentName?: string;
  sport: string;
  category: SportsActivityCategory | string;
  genderCategory: string;
  captainParticipantId?: string | null;
  captainName?: string;
  headCoachUserId?: string | null;
  headCoachName?: string;
  maxRosterSize: number;
  activeRosterCount: number;
  status: string;
  createdAt?: string;
}

export interface TeamRosterMemberItem {
  id: string;
  teamId: string;
  participantId: string;
  participantCode: string;
  participantName: string;
  role: SportsMemberRole | string;
  jerseyNumber?: number | null;
  position?: string | null;
  status: SportsRosterStatus | string;
  joinedAt: string;
  leftAt?: string | null;
  clearanceStatus?: string;
}

export interface CoachingAssignmentItem {
  id: string;
  coachUserId: string;
  coachName: string;
  coachEmail?: string;
  teamId?: string | null;
  teamName?: string;
  sport: string;
  role: SportsCoachingRole | string;
  certificationLevel?: string;
  isPrimary: boolean;
  startDate: string;
  endDate?: string | null;
  status: string;
}

export interface TrainingProgramItem {
  id: string;
  code: string;
  name: string;
  campusId?: string | null;
  departmentId?: string | null;
  programType: SportsProgramType | string;
  sport: string;
  leadCoachUserId?: string | null;
  leadCoachName?: string;
  facilityId?: string | null;
  facilityName?: string;
  capacity: number;
  enrolledCount: number;
  startDate: string;
  endDate: string;
  registrationDeadline?: string;
  feeAmount?: number | null;
  status: string;
  createdAt?: string;
}

export interface TrainingSessionItem {
  id: string;
  programId: string;
  programName?: string;
  facilityId?: string | null;
  facilityName?: string;
  sessionDate: string;
  startTime: string;
  endTime: string;
  title: string;
  focusArea?: string;
  drillsPlan?: Record<string, any>;
  status: string;
  attendanceCount?: number;
}

export interface TrainingAttendanceItem {
  id: string;
  sessionId: string;
  participantId: string;
  participantName: string;
  participantCode: string;
  status: SportsAttendanceStatus | string;
  notes?: string;
  recordedAt: string;
  recordedByUserName?: string;
}

export interface SportsCompetitionItem {
  id: string;
  code: string;
  name: string;
  campusId?: string | null;
  departmentId?: string | null;
  competitionType: SportsCompetitionType | string;
  tournamentFormat: SportsTournamentFormat | string;
  sport: string;
  registrationType: SportsRegistrationType | string;
  standingRule: SportsStandingRule | string;
  pointsForWin: number;
  pointsForDraw: number;
  pointsForLoss: number;
  startDate: string;
  endDate: string;
  registrationDeadline: string;
  maxParticipants: number;
  registeredCount: number;
  feeAmount?: number | null;
  status: SportsCompetitionStatus | string;
  rulesConfig?: Record<string, any>;
  fixturesCount?: number;
  createdAt?: string;
}

export interface CompetitionRegistrationItem {
  id: string;
  competitionId: string;
  teamId?: string | null;
  teamName?: string;
  participantId?: string | null;
  participantName?: string;
  status: string;
  seedNumber?: number | null;
  invoiceId?: string | null;
  paymentStatus: string;
  registeredAt: string;
}

export interface MatchResultItem {
  id: string;
  fixtureId: string;
  winnerTeamId?: string | null;
  winnerParticipantId?: string | null;
  isDraw: boolean;
  isForfeit: boolean;
  isAbandoned: boolean;
  homeScore: number;
  awayScore: number;
  scoreBreakdown?: Record<string, any>;
  verifiedByUserId?: string | null;
  verifiedByName?: string;
  verifiedAt?: string;
  auditNotes?: string;
}

export interface MatchOfficialAssignmentItem {
  id: string;
  fixtureId: string;
  officialUserId: string;
  officialName: string;
  role: SportsOfficialRole | string;
  isConfirmed: boolean;
}

export interface MatchFixtureItem {
  id: string;
  competitionId: string;
  competitionName?: string;
  matchNumber: number;
  stage: SportsMatchStage | string;
  roundNumber: number;
  homeTeamId?: string | null;
  homeTeamName?: string;
  awayTeamId?: string | null;
  awayTeamName?: string;
  homeParticipantId?: string | null;
  homeParticipantName?: string;
  awayParticipantId?: string | null;
  awayParticipantName?: string;
  facilityId?: string | null;
  facilityName?: string;
  matchDate: string;
  startTime: string;
  endTime: string;
  status: SportsFixtureStatus | string;
  postponementReason?: string;
  officials?: MatchOfficialAssignmentItem[];
  result?: MatchResultItem;
}

export interface CompetitionStandingItem {
  id: string;
  competitionId: string;
  teamId?: string | null;
  teamName?: string;
  participantId?: string | null;
  participantName?: string;
  rank: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  pointsFor: number;
  pointsAgainst: number;
  pointDifference: number;
  points: number;
  formGuide?: string;
}

export interface SportsAchievementItem {
  id: string;
  recipientType: "TEAM" | "PARTICIPANT";
  teamId?: string | null;
  teamName?: string;
  participantId?: string | null;
  participantName?: string;
  sport: string;
  title: string;
  level: SportsRecognitionLevel | string;
  medal?: SportsMedal | string | null;
  awardDate: string;
  competitionId?: string | null;
  competitionName?: string;
  citation?: string;
  certificateNumber?: string;
}

export interface SportsEquipmentAssignmentItem {
  id: string;
  assetId?: string | null;
  equipmentName: string;
  itemCode: string;
  category: string;
  allocatedQuantity: number;
  teamId?: string | null;
  teamName?: string;
  facilityId?: string | null;
  facilityName?: string;
  responsibleUserId: string;
  responsibleUserName: string;
  checkoutDate: string;
  dueDate: string;
  returnDate?: string | null;
  status: SportsCheckoutStatus | string;
  returnCondition?: SportsEquipmentCondition | string | null;
  conditionNotes?: string;
  replacementFee?: number | null;
  invoiceId?: string | null;
}

export interface SportsFeeItem {
  id: string;
  title: string;
  activityType: "COMPETITION" | "TRAINING_PROGRAM" | "FACILITY_HIRE" | "EQUIPMENT_DAMAGE";
  referenceId: string;
  targetName: string;
  payerName: string;
  payerRole: string;
  amount: number;
  status: "PAID" | "PENDING" | "WAIVED" | "REFUNDED";
  invoiceReference: string;
  dueDate: string;
  paidAt?: string;
}

export interface SportsDashboardData {
  totalDepartments: number;
  totalFacilities: number;
  facilitiesAvailable: number;
  facilitiesMaintenance: number;
  totalParticipants: number;
  participantsCleared: number;
  clearanceComplianceRate: number;
  totalTeams: number;
  activeTournaments: number;
  matchesScheduledToday: number;
  equipmentItemsCheckedOut: number;
  equipmentOverdueCount: number;
  upcomingTrainingSessionsCount: number;
  todayFixtures: MatchFixtureItem[];
  upcomingTrainingSessions: TrainingSessionItem[];
  activeTournamentsList: SportsCompetitionItem[];
  overdueEquipmentList: SportsEquipmentAssignmentItem[];
  facilitiesInMaintenanceList: SportsFacilityItem[];
}
