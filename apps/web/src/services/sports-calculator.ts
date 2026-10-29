/**
 * CampusOS Pure Sports & Athletics Domain Calculations & Scheduling Engine
 * Product Principle: "One Campus. One System. One Source of Truth."
 *
 * Implements deterministic calculation logic for:
 * 1. Facility utilization rates & clearance compliance percentages
 * 2. Overlapping venue reservation conflict detection
 * 3. Participant schedule conflict detection
 * 4. Academic & health eligibility verification rules
 * 5. Automated Round Robin & Knockout tournament fixture generation
 * 6. League table standings computation with goal/point differential sorting
 */

export interface BookingSlot {
  id?: string;
  facilityId: string;
  bookingDate: string;
  startTime: string; // "HH:MM" or "HH:MM:SS"
  endTime: string;   // "HH:MM" or "HH:MM:SS"
  status?: string;
}

export interface SessionSlot {
  id?: string;
  sessionDate: string;
  startTime: string;
  endTime: string;
  title?: string;
}

export interface AthleteEligibilityCriteria {
  minCgpa?: number;
  minAttendancePercentage?: number;
  requireClearedStatus?: boolean;
  maxDisciplinaryActions?: number;
}

export interface AthleteProfileData {
  cgpa?: number;
  attendancePercentage?: number;
  clearanceStatus: string;
  disciplinaryActionsCount?: number;
}

export interface MatchScoreRecord {
  homeCompetitorId: string;
  awayCompetitorId: string;
  homeScore: number;
  awayScore: number;
  status: string; // e.g. "COMPLETED"
}

export interface StandingsConfig {
  pointsForWin?: number;
  pointsForDraw?: number;
  pointsForLoss?: number;
}

export interface ComputedStandingRow {
  competitorId: string;
  competitorName: string;
  rank: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  pointsFor: number;
  pointsAgainst: number;
  pointDifference: number;
  points: number;
  formGuide: string;
}

/**
 * Calculates facility utilization percentage given booked hours and operating hours.
 */
export function calculateFacilityUtilizationRate(
  bookedHours: number,
  operatingHours: number,
): number {
  if (operatingHours <= 0) return 0;
  if (bookedHours <= 0) return 0;
  const rate = (bookedHours / operatingHours) * 100;
  return Number(Math.min(100, Math.max(0, rate)).toFixed(1));
}

/**
 * Calculates athletic medical clearance compliance rate.
 */
export function calculateClearanceComplianceRate(
  clearedCount: number,
  totalAthletes: number,
): number {
  if (totalAthletes <= 0) return 100;
  if (clearedCount <= 0) return 0;
  const rate = (clearedCount / totalAthletes) * 100;
  return Number(Math.min(100, Math.max(0, rate)).toFixed(1));
}

/**
 * Calculates match win rate percentage.
 */
export function calculateWinRate(won: number, totalPlayed: number): number {
  if (totalPlayed <= 0) return 0;
  if (won <= 0) return 0;
  const rate = (won / totalPlayed) * 100;
  return Number(Math.min(100, Math.max(0, rate)).toFixed(1));
}

/**
 * Calculates score / goal difference.
 */
export function calculateGoalDifference(pointsFor: number, pointsAgainst: number): number {
  return pointsFor - pointsAgainst;
}

function normalizeTime(t: string): number {
  const parts = t.split(":");
  const h = parseInt(parts[0], 10) || 0;
  const m = parseInt(parts[1], 10) || 0;
  return h * 60 + m;
}

/**
 * Detects whether a proposed facility booking overlaps with existing confirmed reservations.
 */
export function detectFacilityBookingConflict(
  existingBookings: BookingSlot[],
  newBooking: BookingSlot,
): { hasConflict: boolean; conflictingBooking?: BookingSlot; message?: string } {
  const newStart = normalizeTime(newBooking.startTime);
  const newEnd = normalizeTime(newBooking.endTime);

  if (newEnd <= newStart) {
    return {
      hasConflict: true,
      message: `Invalid booking duration: end time (${newBooking.endTime}) must be after start time (${newBooking.startTime}).`,
    };
  }

  for (const existing of existingBookings) {
    // Skip self when updating
    if (newBooking.id && existing.id === newBooking.id) continue;
    // Only check same facility and same date
    if (existing.facilityId !== newBooking.facilityId) continue;
    if (existing.bookingDate !== newBooking.bookingDate) continue;
    // Skip cancelled or rejected bookings
    if (existing.status === "CANCELLED" || existing.status === "REJECTED") continue;

    const existStart = normalizeTime(existing.startTime);
    const existEnd = normalizeTime(existing.endTime);

    // Overlap condition: startA < endB and startB < endA
    if (newStart < existEnd && existStart < newEnd) {
      return {
        hasConflict: true,
        conflictingBooking: existing,
        message: `Facility conflict: Time slot ${newBooking.startTime}-${newBooking.endTime} on ${newBooking.bookingDate} overlaps with an existing reservation (${existing.startTime}-${existing.endTime}).`,
      };
    }
  }

  return { hasConflict: false };
}

/**
 * Detects participant/trainer scheduling conflicts across sessions.
 */
export function detectParticipantScheduleConflict(
  existingSessions: SessionSlot[],
  newSession: SessionSlot,
): { hasConflict: boolean; conflictingSession?: SessionSlot; message?: string } {
  const newStart = normalizeTime(newSession.startTime);
  const newEnd = normalizeTime(newSession.endTime);

  if (newEnd <= newStart) {
    return {
      hasConflict: true,
      message: "End time must be after start time.",
    };
  }

  for (const existing of existingSessions) {
    if (newSession.id && existing.id === newSession.id) continue;
    if (existing.sessionDate !== newSession.sessionDate) continue;

    const existStart = normalizeTime(existing.startTime);
    const existEnd = normalizeTime(existing.endTime);

    if (newStart < existEnd && existStart < newEnd) {
      return {
        hasConflict: true,
        conflictingSession: existing,
        message: `Schedule conflict: Session overlaps with existing commitment "${existing.title || "Session"}" from ${existing.startTime} to ${existing.endTime} on ${existing.sessionDate}.`,
      };
    }
  }

  return { hasConflict: false };
}

/**
 * Validates athlete eligibility against institutional policies (CGPA, attendance, clearance).
 */
export function validateAthleteEligibility(
  athlete: AthleteProfileData,
  criteria: AthleteEligibilityCriteria = {},
): { isEligible: boolean; failureReasons: string[] } {
  const failureReasons: string[] = [];

  const minCgpa = criteria.minCgpa ?? 2.0;
  if (athlete.cgpa !== undefined && athlete.cgpa < minCgpa) {
    failureReasons.push(
      `Academic CGPA of ${athlete.cgpa.toFixed(2)} is below minimum threshold of ${minCgpa.toFixed(2)}.`,
    );
  }

  const minAtt = criteria.minAttendancePercentage ?? 75;
  if (athlete.attendancePercentage !== undefined && athlete.attendancePercentage < minAtt) {
    failureReasons.push(
      `Academic attendance of ${athlete.attendancePercentage.toFixed(1)}% is below required ${minAtt.toFixed(1)}%.`,
    );
  }

  const requireCleared = criteria.requireClearedStatus ?? true;
  if (requireCleared) {
    const validStatuses = ["CLEARED", "RESTRICTED"];
    if (!validStatuses.includes(athlete.clearanceStatus.toUpperCase())) {
      failureReasons.push(
        `Athletic medical clearance status is "${athlete.clearanceStatus}". Must be CLEARED or RESTRICTED to participate.`,
      );
    }
  }

  const maxDisciplinary = criteria.maxDisciplinaryActions ?? 0;
  if (
    athlete.disciplinaryActionsCount !== undefined &&
    athlete.disciplinaryActionsCount > maxDisciplinary
  ) {
    failureReasons.push(
      `Participant has ${athlete.disciplinaryActionsCount} active disciplinary incident(s) on record. Max allowed is ${maxDisciplinary}.`,
    );
  }

  return {
    isEligible: failureReasons.length === 0,
    failureReasons,
  };
}

/**
 * Generates round-robin fixtures using Berger algorithm.
 */
export function generateRoundRobinFixtures<T>(
  competitors: T[],
): Array<{ round: number; home: T; away: T }> {
  if (competitors.length < 2) return [];

  const list: (T | null)[] = [...competitors];
  // If odd count, append dummy competitor for bye
  if (list.length % 2 !== 0) {
    list.push(null);
  }

  const n = list.length;
  const totalRounds = n - 1;
  const matchesPerRound = n / 2;
  const fixtures: Array<{ round: number; home: T; away: T }> = [];

  for (let r = 0; r < totalRounds; r++) {
    for (let m = 0; m < matchesPerRound; m++) {
      const home = list[m];
      const away = list[n - 1 - m];

      // If neither is null (not a bye), create fixture
      if (home !== null && away !== null) {
        // Alternate home/away to ensure fairness
        if (r % 2 === 1) {
          fixtures.push({ round: r + 1, home: away, away: home });
        } else {
          fixtures.push({ round: r + 1, home, away });
        }
      }
    }

    // Rotate array elements keeping index 0 fixed
    const fixed = list[0];
    const last = list.pop()!;
    list.splice(1, 0, last);
    list[0] = fixed;
  }

  return fixtures;
}

/**
 * Generates single-elimination knockout tournament bracket.
 */
export function generateKnockoutFixtures<T>(
  competitors: T[],
): Array<{
  matchNumber: number;
  round: number;
  stage: string;
  home?: T;
  away?: T;
}> {
  if (competitors.length < 2) return [];

  // Determine stage name by competitors count
  function getStageName(competitorsRemaining: number): string {
    if (competitorsRemaining === 2) return "FINAL";
    if (competitorsRemaining === 4) return "SEMI_FINAL";
    if (competitorsRemaining === 8) return "QUARTER_FINAL";
    if (competitorsRemaining === 16) return "ROUND_OF_16";
    return "KNOCKOUT_ROUND";
  }

  // Next power of two
  const power = Math.pow(2, Math.ceil(Math.log2(competitors.length)));
  const bracket: (T | undefined)[] = [...competitors];
  while (bracket.length < power) {
    bracket.push(undefined); // Bye slot
  }

  const fixtures: Array<{
    matchNumber: number;
    round: number;
    stage: string;
    home?: T;
    away?: T;
  }> = [];

  let matchNum = 1;
  const firstRoundMatches = bracket.length / 2;
  const stageName = getStageName(bracket.length);

  for (let i = 0; i < firstRoundMatches; i++) {
    const home = bracket[i * 2];
    const away = bracket[i * 2 + 1];

    fixtures.push({
      matchNumber: matchNum++,
      round: 1,
      stage: stageName,
      home,
      away,
    });
  }

  return fixtures;
}

/**
 * Computes official league table standings from match scores.
 */
export function computeTournamentStandings(
  competitors: Array<{ id: string; name: string }>,
  matches: MatchScoreRecord[],
  config: StandingsConfig = {},
): ComputedStandingRow[] {
  const winPts = config.pointsForWin ?? 3;
  const drawPts = config.pointsForDraw ?? 1;
  const lossPts = config.pointsForLoss ?? 0;

  const tableMap = new Map<
    string,
    {
      name: string;
      played: number;
      won: number;
      drawn: number;
      lost: number;
      pointsFor: number;
      pointsAgainst: number;
      points: number;
      form: string[];
    }
  >();

  for (const c of competitors) {
    tableMap.set(c.id, {
      name: c.name,
      played: 0,
      won: 0,
      drawn: 0,
      lost: 0,
      pointsFor: 0,
      pointsAgainst: 0,
      points: 0,
      form: [],
    });
  }

  for (const match of matches) {
    if (match.status !== "COMPLETED") continue;

    const home = tableMap.get(match.homeCompetitorId);
    const away = tableMap.get(match.awayCompetitorId);

    if (home) {
      home.played += 1;
      home.pointsFor += match.homeScore;
      home.pointsAgainst += match.awayScore;
    }

    if (away) {
      away.played += 1;
      away.pointsFor += match.awayScore;
      away.pointsAgainst += match.homeScore;
    }

    if (match.homeScore > match.awayScore) {
      if (home) {
        home.won += 1;
        home.points += winPts;
        home.form.push("W");
      }
      if (away) {
        away.lost += 1;
        away.points += lossPts;
        away.form.push("L");
      }
    } else if (match.homeScore < match.awayScore) {
      if (away) {
        away.won += 1;
        away.points += winPts;
        away.form.push("W");
      }
      if (home) {
        home.lost += 1;
        home.points += lossPts;
        home.form.push("L");
      }
    } else {
      if (home) {
        home.drawn += 1;
        home.points += drawPts;
        home.form.push("D");
      }
      if (away) {
        away.drawn += 1;
        away.points += drawPts;
        away.form.push("D");
      }
    }
  }

  // Convert to array and sort
  const rows: ComputedStandingRow[] = Array.from(tableMap.entries()).map(([id, data]) => {
    const pointDifference = data.pointsFor - data.pointsAgainst;
    const formGuide = data.form.slice(-5).join("");
    return {
      competitorId: id,
      competitorName: data.name,
      rank: 1,
      played: data.played,
      won: data.won,
      drawn: data.drawn,
      lost: data.lost,
      pointsFor: data.pointsFor,
      pointsAgainst: data.pointsAgainst,
      pointDifference,
      points: data.points,
      formGuide: formGuide || "-",
    };
  });

  // Sort by Points DESC -> Point Difference DESC -> Points For DESC
  rows.sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    if (b.pointDifference !== a.pointDifference) return b.pointDifference - a.pointDifference;
    return b.pointsFor - a.pointsFor;
  });

  // Assign ranks
  rows.forEach((row, idx) => {
    row.rank = idx + 1;
  });

  return rows;
}
