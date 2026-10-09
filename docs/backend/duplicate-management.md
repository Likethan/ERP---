# Duplicate Detection & Controlled Merge Architecture

CampusOS incorporates an automated, deterministic duplicate detection and controlled merge framework to consolidate redundant records while safeguarding historical referential integrity and audit trails.

---

## 1. Matching Strategies by Entity

Duplicate matching uses normalized attributes (case-insensitive, whitespace-collapsed, punctuation-stripped) without using non-deterministic ML:

### Student
Signals:
- **Admission Number**: Exact match on normalized admission number (100% confidence).
- **Email**: Exact match on normalized email (90% confidence).
- **Phone**: Exact match on normalized 10-digit phone (85% confidence).
- **Name**: Normalized first and last name similarity (70% confidence).

### Company
Signals:
- **Web Domain**: Exact match on root domain (e.g. `google.com`) (95% confidence).
- **Company Name**: Normalized text comparison (80% confidence).

### Department
Signals:
- **Department Code**: Normalized code collision (90% confidence).
- **Department Name**: Normalized title comparison (75% confidence).

Candidates with a match score exceeding 70% are inserted into `duplicate_candidates` with status `PENDING`.

---

## 2. Stewardship Review Workflow

Stewards review candidates via the duplicate queue:
- **CONFIRMED_DUPLICATE**: Confirmed as true positive; eligible for controlled merge.
- **NOT_DUPLICATE**: Legitimate distinct entities; candidate is closed.
- **DISMISSED**: Anomaly ignored.

---

## 3. Controlled Merge Workflow & Whitelist

Merging alters relational dependencies and is strictly whitelisted:
- **Allowed Entities**: `STUDENT`, `COMPANY`, `DEPARTMENT`
- Any attempt to merge an unsupported master entity (e.g. `DOCUMENT_CATEGORY`) raises `MasterDataMergeUnsupportedException`.

### Survivorship Rules

When two records merge, attribute resolution follows a survivorship policy:
1. `KEEP_CANONICAL`: Preserve survivor attributes, discard merged record fields.
2. `KEEP_MOST_RECENT`: Keep values from the most recently updated record.
3. `KEEP_NON_EMPTY`: Fill any missing/null fields in survivor with non-empty values from merged record.
4. `EXPLICIT_FIELD_SELECTION`: Field-by-field manual attribute assignment provided by steward.

---

## 4. Relationship Reassignment

During a merge, child relational foreign keys are safely migrated:
- **Student**:
  - `AttendanceRecord` foreign keys point to survivor.
  - `StudentLeaveRequest` reassigned to survivor.
  - `StudentAssessmentMark` examination marks reassigned.
  - `Invoice` fee records reassigned.
- **Company**:
  - `CompanyContact` reassigned to survivor company.
  - `JobDrive` placement drives reassigned to survivor company.
- **Department**:
  - `Program` curricula reassigned.
  - `FacultyProfile` departmental appointments reassigned.

After reassignment, the merged entity has `status = MERGED` (or `is_active = False`) and is never hard-deleted.

---

## 5. Rollback & Audit Provenance

Every merge records a forensic snapshot in `master_data_merge_operations`:
- `survivor_record_id` and `merged_record_id`
- `field_decisions_json`
- `reassigned_counts_json`
- `is_reversible`: Boolean flag indicating whether rollback is safe.
- **Rollback Operation**: Can reverse the merge by restoring the merged entity status and recording an audit trail, provided downstream changes have not invalidated reversal.
