# CampusOS — Interactive Curriculum Builder & Versioning Documentation

## 1. Overview & Conceptual Model

The **Curriculum Builder** (`/app/academics/curricula/[id]`) provides academic deans, board of studies chairs, and HODs with an institutional tool to author, structure, and publish multi-year academic regulations.

A Curriculum Scheme is more than a list of courses; it defines the complete graduation roadmap for a cohort, establishing:
- Semester-by-semester progression
- Minimum credit requirements for degree conferral
- Core foundational vs. advanced specialization balance
- Choice-Based Credit System (CBCS) elective baskets

---

## 2. Regulation Versioning Philosophy

To preserve academic integrity and transcript authenticity, CampusOS enforces an immutable historical versioning model:

```
B.Tech Computer Science & Engineering
   │
   ├── R-2024 (Regulation 2024 - v1.2) [STATUS: PUBLISHED / ACTIVE]
   │      └── Governs Cohort 2024–2028 (Total Credits: 160)
   │
   ├── R-2025 (Regulation 2025 - v2.0) [STATUS: UNDER REVIEW]
   │      └── Planned for Cohort 2025–2029 (Total Credits: 162)
   │
   └── R-2026 (Regulation 2026 - v0.1) [STATUS: DRAFT]
          └── Experimental syllabus incorporating Generative AI credits
```

### Key Versioning Rules
1. **Never Overwrite Historical Schemes**: Graduated or active cohorts remain linked to their original matriculation regulation.
2. **Distinct Lifecycle States**:
   - `DRAFT`: Initial syllabus design; open to departmental faculty input.
   - `UNDER_REVIEW`: Submitted to Board of Studies and Academic Council.
   - `APPROVED`: Formally ratified by institutional leadership.
   - `PUBLISHED`: Operationalized for term course offerings and student enrollment. Changes are locked.
   - `RETIRED`: Historical scheme no longer accepting new admissions.

---

## 3. Builder Capabilities & Component Breakdown

### 3.1 Semester Accordion Matrix
- Renders Semesters 1 through 8 as expandable sections.
- Shows total credits per semester, number of assigned subjects, and weekly contact hours.
- Expandable subject table with Subject Code, Name, Department, Type (`Theory`, `Laboratory`, etc.), Category (`Basic Science`, `Core`, `Elective`), and Credits.

### 3.2 Subject Catalog Assignment Modal
- Dynamic subject picker linked to the Master Subject Catalog.
- Real-time search across subject code, title, and department.
- Displays credit value and contact hours before assignment.
- Instantly recalculates total curriculum credits upon addition.

### 3.3 Elective Basket Management
- Configure Choice-Based Credit System (CBCS) groupings:
  - **Group Name**: e.g., *Professional Elective I (Cloud & Security)*, *Open Elective II (Humanities)*.
  - **Semester**: Semester where the basket is offered.
  - **Selection Constraints**: Minimum choices required (e.g. `1`) and Maximum choices allowed (e.g. `1`).
  - **Available Course Pool**: Multi-subject selection from the catalog that students can choose from during course enrollment.

---

## 4. Preliminary Frontend Validation Engine

Before an academic scheme can transition from `DRAFT` to `APPROVED` or `PUBLISHED`, the builder executes an automated sanity audit:

| Check Name | Severity | Condition | Advisory Message |
| :--- | :---: | :--- | :--- |
| **Duplicate Subject** | `ERROR` | A subject appears in multiple semesters within the same scheme | *"{Subject Code} is assigned to multiple semesters. A course cannot be repeated in a single degree scheme."* |
| **Empty Semester** | `WARNING` | A semester has 0 assigned subjects | *"Semester {N} currently has no assigned subjects. Undergraduate programs typically require 18–24 credits per semester."* |
| **Credit Discrepancy** | `WARNING` | Calculated total credits does not match the target total credits | *"Target total credits ({Target}) diverges from calculated sum of assigned subjects ({Actual})."* |
| **Invalid Elective Basket** | `WARNING` | An elective group has 0 subjects or `minChoices > maxChoices` | *"Elective Group '{Name}' has invalid selection constraints or empty subject pool."* |

> **Advisory Labeling**: All frontend validation warnings are explicitly branded as preliminary checks. Final degree audit and Board of Studies certification is performed authoritatively on the backend.

---

## 5. Audit Trail & Version History

The Curriculum Detail page includes a dedicated **Version History** tab providing full lineage:
- Version sequence (`v1.0` ➔ `v1.1` ➔ `v2.0`)
- Modification author (Dean of Academics / Department Chair)
- Timestamp of change
- Summary changelog (e.g., *"Replaced CS204 with CS208; adjusted total credits from 160 to 162"*).

---

## 6. Role Permissions

| Role | Create Scheme | Edit Semesters / Electives | Submit for Review | Publish Scheme |
| :--- | :---: | :---: | :---: | :---: |
| **Super Admin** | Yes | Yes | Yes | Yes |
| **Dean of Academics** | Yes | Yes | Yes | Yes |
| **HOD** | Yes (Dept) | Yes (Dept) | Yes | Requires Dean Approval |
| **Faculty** | No | Read-Only | No | No |
| **Student** | No | View Scheme Only | No | No |
