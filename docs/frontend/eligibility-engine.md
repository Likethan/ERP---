# CampusOS — Placement Eligibility Engine

## 1. Architectural Philosophy

Eligibility evaluation is one of the most critical operational gates in institutional placements. Rather than reducing candidate qualification to a simplistic boolean flag (`true`/`false`), CampusOS implements a **Deterministic Rule-Based Eligibility Engine** (`apps/web/src/services/placement-calculator.ts`).

The engine:
1. Returns rich, structured evaluation snapshots detailing every configured requirement against the candidate's active academic record.
2. Isolates exact reasons for non-qualification (showing `required` threshold vs `actual` student metric).
3. Produces auditable `EligibilitySnapshot` objects that are immutably tied to the application at time of submission.

---

## 2. Rule Hierarchy & Evaluation Statuses

Candidates evaluated against a job drive position receive one of four lifecycle statuses:

| Status | Meaning | Criticality |
| :--- | :--- | :--- |
| `ELIGIBLE` | Candidate meets or exceeds all academic, graduation, and skill cutoffs. | Cleared |
| `CONDITIONALLY_ELIGIBLE` | Candidate passes critical criteria (Degree, Year, CGPA, Backlogs) but misses optional skill or attendance requirements. | Conditional Review |
| `INELIGIBLE` | Candidate fails one or more critical institutional cutoffs. | Hard Disqualification |
| `PENDING_REVIEW` | System evaluation flagged for placement officer / HOD manual determination. | Human Review Gate |

---

## 3. Pure Calculator Functions

The engine is built from composable, pure functions:

### 3.1 `checkProgramEligibility(studentProgram, targetPrograms)`
- **Rule**: Validates candidate degree program against target list.
- **Criticality**: **CRITICAL**. Mismatch results in `INELIGIBLE`.

### 3.2 `checkGraduationYearEligibility(studentGradYear, targetGradYear)`
- **Rule**: Verifies that the candidate belongs to the recruiting cohort batch.
- **Criticality**: **CRITICAL**. Mismatch results in `INELIGIBLE`.

### 3.3 `checkCgpaEligibility(studentCgpa, minCgpa)`
- **Rule**: Evaluates candidate cumulative GPA against cutoff.
- **Criticality**: **CRITICAL**. Returns `{ passed: studentCgpa >= minCgpa, required: minCgpa, actual: studentCgpa }`.

### 3.4 `checkBacklogEligibility(activeBacklogs, maxAllowedBacklogs)`
- **Rule**: Verifies candidate has $\le$ maximum active backlogs permitted (typically 0).
- **Criticality**: **CRITICAL**. Returns `{ passed: activeBacklogs <= maxAllowedBacklogs }`.

### 3.5 `checkAttendanceEligibility(attendancePercent, minAttendancePercent)`
- **Rule**: Optional campus policy gate (e.g., minimum 75% attendance).
- **Criticality**: **NON-CRITICAL**. Failure results in `CONDITIONALLY_ELIGIBLE` pending HOD condonation.

### 3.6 `checkSkillEligibility(studentSkills, requiredSkills)`
- **Rule**: Case-insensitive substring matching of candidate programming languages, technical competencies, and tools.
- **Criticality**: **NON-CRITICAL**. Incomplete matches flag conditional eligibility.

---

## 4. Combined Evaluation: `calculateEligibility(student, position)`

```ts
export function calculateEligibility(
  student: StudentPlacementProfile,
  position: Position
): EligibilitySnapshot {
  const rules: RuleEvaluationResult[] = [];

  // 1. Program check
  rules.push(checkProgramEligibility(student.program, position.targetPrograms));

  // 2. Graduation year check
  rules.push(checkGraduationYearEligibility(student.graduationYear, position.graduationYear));

  // 3. CGPA check
  rules.push(checkCgpaEligibility(student.cgpa, position.minCgpa));

  // 4. Backlogs check
  rules.push(checkBacklogEligibility(student.activeBacklogs, position.maxBacklogs));

  // 5. Attendance check
  if (position.minAttendancePercent) {
    rules.push(checkAttendanceEligibility(student.attendancePercent, position.minAttendancePercent));
  }

  // 6. Skills check
  if (position.requiredSkills.length > 0) {
    const allSkills = [
      ...student.skills.technical,
      ...student.skills.programmingLanguages,
      ...student.skills.toolsAndFrameworks,
    ];
    rules.push(checkSkillEligibility(allSkills, position.requiredSkills));
  }

  // Determine overall status
  const criticalFails = rules.filter(
    (r) => !r.passed && ["TARGET_PROGRAM", "GRADUATION_YEAR", "MIN_CGPA", "MAX_BACKLOGS"].includes(r.rule)
  );
  const nonCriticalFails = rules.filter((r) => !r.passed && !criticalFails.includes(r));

  let status: EligibilityStatus = "ELIGIBLE";
  if (criticalFails.length > 0) {
    status = "INELIGIBLE";
  } else if (nonCriticalFails.length > 0) {
    status = "CONDITIONALLY_ELIGIBLE";
  }

  return {
    id: `esnap-${Date.now()}`,
    studentId: student.studentId,
    studentName: student.studentName,
    rollNumber: student.rollNumber,
    driveId: position.driveId,
    positionId: position.id,
    status,
    rules,
    evaluatedAt: new Date().toISOString(),
  };
}
```

---

## 5. Eligibility Override Protocol

To preserve institutional accountability, automated eligibility results **cannot be silently modified**:
1. Any modification requires an explicit `overrideEligibility` action.
2. The override preserves the immutable original eligibility status.
3. Requires mandatory:
   - **Override Status**: `ELIGIBLE`, `CONDITIONALLY_ELIGIBLE`, or `INELIGIBLE`.
   - **Documented Reason**: Legal / institutional rationale (e.g., Dean's condonation).
   - **Authority Signature**: Name and designation of the approving authority.
   - **Audit Timestamp**: Exact UTC timestamp of the intervention.
