/**
 * CampusOS Enterprise Student Counselling, Mentoring & Personal Development Types (Step 59)
 * Product Principle: "One Campus. One System. One Source of Truth."
 */

export type MentorAssignmentType = "MANUAL" | "RULE_BASED" | "REASSIGNED" | "TEMPORARY_COVERAGE";
export type MentorAssignmentStatus = "ACTIVE" | "INACTIVE" | "REASSIGNED" | "COMPLETED";

export type SessionType = "ONE_ON_ONE" | "GROUP" | "CHECK_IN" | "ACADEMIC_REVIEW" | "CAREER_DISCUSSIONS";
export type SessionStatus = "SCHEDULED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED" | "NO_SHOW";
export type SessionAttendanceStatus = "PRESENT" | "ABSENT" | "EXCUSED" | "PENDING";

export type AppointmentCategory = "ACADEMIC_STRESS" | "PERSONAL_WELLBEING" | "CAREER_COUNSELLING" | "CRISIS_SUPPORT" | "ADAPTATION_SUPPORT" | "GENERAL_COUNSELLING" | "CAREER_ANXIETY" | "PEER_RELATIONSHIPS" | "TIME_MANAGEMENT" | "OTHER";
export type AppointmentMode = "IN_PERSON" | "ONLINE_VIDEO" | "ONLINE" | "TELEPHONIC";
export type AppointmentStatus = "REQUESTED" | "BOOKED" | "CONFIRMED" | "RESCHEDULED" | "CANCELLED" | "CHECKED_IN" | "COMPLETED" | "NO_SHOW";
export type InterventionType = "INITIAL_INTAKE" | "SOLUTION_FOCUSED" | "COGNITIVE_GUIDANCE" | "STRESS_MANAGEMENT" | "CRISIS_DE_ESCALATION" | "REFERRAL_CONSULTATION" | "FOLLOW_UP_REVIEW";

export type PlanStatus = "DRAFT" | "ACTIVE" | "UNDER_REVIEW" | "COMPLETED" | "ARCHIVED";
export type GoalCategory = "ACADEMIC" | "ACADEMIC_EXCELLENCE" | "PROFESSIONAL_SKILLS" | "COMMUNICATION" | "LEADERSHIP" | "PERSONAL_WELLBEING" | "CAREER_EXPLORATION" | "CAREER" | "TECHNICAL" | "PERSONAL";
export type GoalStatus = "PENDING" | "ACTIVE" | "IN_PROGRESS" | "COMPLETED" | "DEFERRED";
export type ActionItemStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "BLOCKED";

export type SupportServiceCategory = "ACADEMIC_ADVISING" | "CAREER_SERVICES" | "COUNSELLING_SERVICES" | "DISABILITY_SUPPORT" | "FINANCIAL_AID" | "STUDENT_AFFAIRS" | "HEALTH_SERVICES";
export type ReferralPriority = "LOW" | "STANDARD" | "MEDIUM" | "HIGH" | "URGENT" | "IMMEDIATE";
export type ReferralStatus = "PENDING" | "ACCEPTED" | "IN_PROGRESS" | "COMPLETED" | "DECLINED" | "CANCELLED";
export type FollowUpStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "OVERDUE" | "CANCELLED";

// =============================================================================
// ENTITY INTERFACES (Dual CamelCase & SnakeCase Compatible)
// =============================================================================

export interface MentorAssignmentItem {
  id: string;
  tenantId?: string;
  studentId?: string;
  student_id?: string;
  studentName?: string;
  student_name?: string;
  studentRoll?: string;
  student_reg_no?: string;
  studentDepartment?: string;
  studentProgram?: string;
  mentorUserId?: string;
  faculty_id?: string;
  faculty_staff_id?: string;
  faculty_name?: string;
  faculty_email?: string;
  department_name?: string;
  program_name?: string;
  faculty_workload_count?: number;
  assigned_at?: string;
  mentorName?: string;
  mentorEmail?: string;
  departmentId?: string | null;
  programId?: string | null;
  academicYear?: string;
  academic_year?: string;
  assignmentType?: MentorAssignmentType | string;
  assignment_type?: MentorAssignmentType | string;
  isPrimary?: boolean;
  is_primary?: boolean;
  status: MentorAssignmentStatus | string;
  assignedDate?: string;
  endDate?: string | null;
  notes?: string | null;
  reassignedFromId?: string | null;
  reassignmentReason?: string | null;
  reassignment_reason?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface MenteeItem {
  studentId?: string;
  student_id?: string;
  studentName?: string;
  student_name?: string;
  rollNumber?: string;
  student_reg_no?: string;
  departmentName?: string;
  department_name?: string;
  programName?: string;
  program_name?: string;
  academicYear?: string;
  current_year_semester?: string;
  assignmentId?: string;
  assignedDate?: string;
  cgpa?: number;
  academic_status?: string;
  lastSessionDate?: string | null;
  last_mentoring_date?: string | null;
  activePlanId?: string | null;
  hasActivePlan?: boolean;
  has_active_development_plan?: boolean;
  planProgressPct?: number;
  development_progress_pct?: number;
  openFollowUpsCount?: number;
  pending_action_items_count?: number;
}

export interface SessionAttendeeItem {
  id: string;
  sessionId: string;
  studentId: string;
  studentName?: string;
  attendanceStatus: SessionAttendanceStatus;
  studentFeedback?: string | null;
  studentReflection?: string | null;
}

export interface MentoringSessionItem {
  id: string;
  tenantId?: string;
  assignmentId?: string | null;
  mentorUserId?: string;
  mentorName?: string;
  mentor_name?: string;
  title?: string;
  sessionTitle?: string;
  sessionType?: SessionType | string;
  session_type?: SessionType | string;
  sessionDate?: string;
  startTime?: string;
  endTime?: string;
  scheduled_start?: string;
  scheduled_end?: string;
  locationOrLink?: string | null;
  location?: string | null;
  discussion_points?: string | null;
  status: SessionStatus | string;
  summary?: string | null;
  summary_notes?: string | null;
  student_reflection?: string | null;
  actionItems?: Array<{ title: string; assignee?: string; dueDate?: string }>;
  action_items_count?: number;
  attendees_count?: number;
  followUpDate?: string | null;
  createdByUserId?: string;
  attendees?: SessionAttendeeItem[];
  createdAt?: string;
  updatedAt?: string;
}

export interface CounsellingAppointmentItem {
  id: string;
  tenantId?: string;
  studentId?: string;
  student_id?: string;
  appointmentNumber?: string;
  appointment_number?: string;
  studentName?: string;
  student_name?: string;
  counsellorUserId?: string | null;
  counsellorName?: string | null;
  counsellor_name?: string | null;
  category: AppointmentCategory | string;
  appointmentDate?: string;
  startTime?: string;
  endTime?: string;
  scheduled_start?: string;
  scheduled_end?: string;
  durationMinutes?: number;
  mode?: AppointmentMode | string;
  appointment_mode?: AppointmentMode | string;
  venueOrLink?: string | null;
  location?: string | null;
  virtual_meeting_link?: string | null;
  status: AppointmentStatus | string;
  requestReason?: string | null;
  reason_summary?: string | null;
  bookedByUserId?: string;
  cancellationReason?: string | null;
  cancellation_reason?: string | null;
  check_in_time?: string | null;
  completed_at?: string | null;
  isConfidential?: boolean;
  hasConfidentialNotes?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface ConfidentialCounsellingRecordItem {
  id: string;
  tenantId?: string;
  appointmentId?: string | null;
  appointment_id?: string | null;
  studentId?: string;
  student_id?: string;
  studentName?: string;
  student_name?: string;
  counsellorUserId?: string;
  counsellor_staff_id?: string;
  counsellorName?: string;
  sessionNotesRestricted?: string;
  session_observations?: string;
  interventionType?: InterventionType | string;
  interventions_applied?: string;
  clinicalObservations?: string | null;
  follow_up_recommended?: boolean;
  followUpRecommended?: boolean;
  followUpTargetDate?: string | null;
  consentConfirmed?: boolean;
  consent_verified?: boolean;
  disclose_to_student?: boolean;
  disclosed_summary?: string;
  accessCount?: number;
  lastAccessedAt?: string | null;
  recorded_at?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface DevelopmentActionItemItem {
  id: string;
  tenantId?: string;
  goalId?: string;
  title: string;
  dueDate?: string | null;
  status: ActionItemStatus | string;
  assignedToRole?: string | null;
  assigned_to_role?: string | null;
  completedAt?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface DevelopmentGoalItem {
  id: string;
  tenantId?: string;
  planId: string;
  plan_id?: string;
  category: GoalCategory | string;
  title: string;
  description?: string | null;
  targetDate?: string | null;
  target_completion_date?: string;
  status: GoalStatus | string;
  progressPct?: number;
  progress_pct?: number;
  measurableMilestones?: string[];
  successMetric?: string | null;
  success_metric?: string | null;
  mentorNotes?: string | null;
  studentReflection?: string | null;
  actionItems?: DevelopmentActionItemItem[];
  action_items?: DevelopmentActionItemItem[];
  createdAt?: string;
  updatedAt?: string;
}

export interface StudentDevelopmentPlanItem {
  id: string;
  tenantId?: string;
  studentId?: string;
  student_id?: string;
  studentName?: string;
  mentorUserId?: string | null;
  mentorName?: string | null;
  title: string;
  academicYear?: string;
  academic_year?: string;
  status: PlanStatus | string;
  overallProgressPct?: number;
  overall_progress_pct?: number;
  reviewFrequency?: "MONTHLY" | "QUARTERLY" | "SEMESTER" | string;
  review_frequency?: "MONTHLY" | "QUARTERLY" | "SEMESTER" | string;
  lastReviewedAt?: string | null;
  nextReviewDate?: string | null;
  next_review_date?: string | null;
  strengthsSummary?: string | null;
  strengths_summary?: string | null;
  areasForGrowth?: string | null;
  growth_areas_summary?: string | null;
  careerAspirations?: string | null;
  goals?: DevelopmentGoalItem[];
  createdAt?: string;
  updatedAt?: string;
}

export interface SupportFollowUpItem {
  id: string;
  tenantId?: string;
  referralId?: string | null;
  planId?: string | null;
  appointmentId?: string | null;
  assignedUserId?: string;
  assigned_to_user_id?: string;
  assignedUserName?: string | null;
  assigned_to_name?: string | null;
  title: string;
  dueDate?: string;
  due_date?: string;
  priority?: "LOW" | "MEDIUM" | "HIGH" | "URGENT" | string;
  notes?: string | null;
  status: FollowUpStatus | string;
  completedAt?: string | null;
  completed_at?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface SupportReferralItem {
  id: string;
  tenantId?: string;
  referralCode?: string;
  referral_number?: string;
  studentId?: string;
  student_id?: string;
  studentName?: string;
  student_name?: string;
  student_reg_no?: string;
  referringUserId?: string;
  referringUserName?: string | null;
  referringRole?: string;
  referring_role?: string;
  referrer_role?: string;
  targetService?: SupportServiceCategory | string;
  target_service?: SupportServiceCategory | string;
  reasonCategory?: string;
  reason_category?: string;
  priority?: ReferralPriority | string;
  summaryNotes?: string | null;
  status: ReferralStatus | string;
  assignedStaffUserId?: string | null;
  assignedStaffName?: string | null;
  consentObtained?: boolean;
  student_consent_obtained?: boolean;
  outcomeNotes?: string | null;
  closedAt?: string | null;
  followUps?: SupportFollowUpItem[];
  createdAt?: string;
  updatedAt?: string;
}

export interface SupportPolicyConfigItem {
  id?: string;
  tenantId?: string;
  maxMenteesPerMentor?: number;
  max_mentees_per_mentor?: number;
  allowCrossDepartmentMentors?: boolean;
  appointmentAdvanceBookingDays?: number;
  advance_booking_window_days?: number;
  appointmentCancellationLeadHours?: number;
  cancellation_lead_hours?: number;
  defaultSessionDurationMinutes?: number;
  enableConfidentialCounselling?: boolean;
  requireStudentConsentForReferral?: boolean;
  require_referral_consent?: boolean;
  privacy_suppression_threshold?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface SupportTelemetryMetrics {
  totalActiveMentorAssignments?: number;
  active_mentor_assignments?: number;
  totalUnassignedStudents?: number;
  unassigned_students_count?: number;
  mentoringSessionsCompletedThisMonth?: number;
  mentoring_sessions_completed?: number;
  appointmentUtilizationRatePct?: number;
  appointment_utilization_rate_pct?: number;
  pendingSupportReferrals?: number;
  pending_support_referrals?: number;
  overdueFollowUps?: number;
  overdue_follow_up_actions?: number;
  developmentPlanCompletionRatePct?: number;
  development_goals_completed?: number;
  average_development_progress_pct?: number;
  referralsByService?: Record<string, number>;
  goalsByCategory?: Record<string, number>;
}
