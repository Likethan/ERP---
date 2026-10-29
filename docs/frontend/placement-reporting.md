# CampusOS — Placement Reporting & Intelligence

## 1. Reporting Architecture

The **Placement Intelligence & Reporting** module (`/app/placement/reports`) delivers real-time operational and compliance analytics for university placement directorates, Academic Councils, Heads of Departments, and accreditation bodies (e.g., NAAC / NIRF).

All reporting metrics derive strictly from the centralized mock placement service (`placementService.generatePlacementReport(filter)`), ensuring complete internal consistency with candidate profiles, corporate drives, applications, offers, and verified outcomes.

---

## 2. Standard Institutional Report Types

### 2.1 Placement Operations & Cohort Conversion Summary (`SUMMARY`)
- **Objective**: Evaluates overall pipeline throughput across eligible graduating students.
- **Columns**: Student ID, Name, Roll Number, Department, Program, CGPA, Backlogs, Applications, Shortlists, Interviews, Offers, Placement Status, Appointed Company, Package (CTC).

### 2.2 Department-wise Placement Performance Audit (`DEPARTMENT`)
- **Objective**: Comparative departmental placement rates for academic leadership and HOD reviews.
- **Columns**: Department, Eligible Students, Placed Students, Placement Rate (%), Average Package (LPA), Highest Package (LPA).

### 2.3 Corporate Partners Hiring Ledger (`COMPANY`)
- **Objective**: Tracks institutional recruiter partnerships, loyalty, and hiring volume.
- **Columns**: Company Name, Industry Sector, Tier (TIER_1 / TIER_2 / TIER_3), Active Drives Count, Total Alumni Hired, Average CTC (LPA), Highest CTC (LPA), Partnership Status.

### 2.4 Compensation & Salary Slab Distribution (`PACKAGES`)
- **Objective**: Analyzes institutional package trends and CTC tier concentrations.
- **Slabs**:
  - `₹3.0 - ₹6.0 LPA` (Foundation / Mass Core)
  - `₹6.0 - ₹10.0 LPA` (Core Engineering)
  - `₹10.0 - ₹18.0 LPA` (Dream Tier)
  - `₹18.0+ LPA` (Super Dream / Product)
- **Columns**: Salary Slab, Min LPA, Max LPA, Number of Offers, Offer Percentage Share.

### 2.5 Candidate Placement Outcomes Ledger (`STATUS`)
- **Objective**: Final statutory ledger of placed candidates, corporate appointments, and joining commitments.
- **Columns**: Student ID, Name, Roll Number, Department, Company Name, Role, Package (CTC), Joining Date, Status, Confirmation Timestamp.

---

## 3. Client-Side Export Protocol

Every report view supports direct export to standard RFC 4180 Comma-Separated Values (CSV) format:
- Implemented with browser `Blob` object and `URL.createObjectURL`.
- Escapes special characters, commas, and internal quotation marks.
- Produces clean, ISO-timestamped filenames: `CampusOS_Placement_<REPORT_TYPE>_Report_<YYYY-MM-DD>.csv`.