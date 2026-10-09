# Predictive Intelligence & Explainable Student Support Framework

## 1. Overview

The Predictive Intelligence Engine (`StudentSupportPredictionService` in `app/domains/intelligence/services/student_support_service.py`) provides early academic intervention signals for faculty advisors and department chairs while upholding the highest ethical standards in educational AI.

---

## 2. Signal Formulation & Contributing Factors

All student indicators are calculated from authoritative, immutable ERP ledgers in PostgreSQL. No ungrounded statistical speculation or hallucinated data is permitted.

### Contributing Signals:
1. **Attendance Signals (`attendance_records`)**:
   - `attendance_percentage`: Percentage of scheduled academic sessions attended (`PRESENT` or `LATE`).
   - `shortage_flag`: Raised if attendance is below the mandatory university threshold (typically 75.0% or 65.0%).
2. **Examination & Assessment Signals (`examination_student_marks`)**:
   - `average_marks`: Mean score across internal assessments and term exams.
   - `failed_assessments_count`: Total number of assessments where `marks_obtained < 40.0%`.
3. **Institutional Provenance**:
   - Every indicator references the model version (`v1.2-rule-based`) and execution timestamp.

---

## 3. Risk Levels & Scoring Mechanics

| Risk Level | Score Range | Contributing Signals Summary | Recommended Staff Action |
|:---|:---:|:---|:---|
| **LOW** | 0.00 – 0.29 | Attendance ≥ 80%, No failed assessments, GPA ≥ 55% | Routine monitoring |
| **MEDIUM** | 0.30 – 0.49 | Attendance 75%–79% or 1 failed assessment | Proactive advisor check-in |
| **HIGH** | 0.50 – 0.74 | Attendance 65%–74% or 2+ failed assessments | Academic tutoring referral |
| **CRITICAL** | 0.75 – 1.00 | Attendance < 65% and multiple failed assessments | Immediate multi-stakeholder case conference |

---

## 4. Ethical & Legal Safeguards

1. **No Consequential Autonomous Decisions**:
   - Under no circumstances does the engine automatically fail, suspend, disqualify, or dismiss a student.
   - The flag `human_review_required = True` is permanently hardcoded and verified in the database schema.
2. **Review & Dispute Workflow**:
   - Authorized advisors can submit reviews (`PENDING_REVIEW` -> `REVIEWED` or `DISMISSED`) with documented audit notes.
   - Source attendance or examination marks can be corrected through formal administrative workflows (`AttendanceCorrectionRequest`, `MarkCorrectionRequest`), immediately updating the recalculated risk indicator.
3. **Protected Characteristics Excluded**:
   - No demographic, socio-economic, religious, gender, or caste attributes are ingested into predictive scoring models.
