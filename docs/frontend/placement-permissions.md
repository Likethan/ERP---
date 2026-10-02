# CampusOS — Placement Role Permissions Matrix

## 1. Permission Architecture

CampusOS employs fine-grained Role-Based Access Control (RBAC) to enforce security boundaries across corporate relations, academic eligibility, and candidate selections.

---

## 2. Granular Permission Keys

| Permission Key | Description |
| :--- | :--- |
| `placement.view` | Base read access to view career portal / placement hub. |
| `placement.manage_profiles` | Access to edit candidate profiles, skills, and verify resume statuses. |
| `placement.manage_companies` | Authority to onboard, edit, tier, and transition corporate partners. |
| `placement.manage_drives` | Authority to create, configure, publish, and close recruitment drives. |
| `placement.manage_positions` | Authority to define job roles, vacancies, and compensation structures. |
| `placement.manage_eligibility` | Authority to configure eligibility cutoffs and perform manual overrides. |
| `placement.review_applications` | Authority to review candidate dossiers and execute shortlists or rejections. |
| `placement.manage_interviews` | Authority to schedule, reschedule, and submit panel evaluations. |
| `placement.manage_offers` | Authority to release, expire, or revoke formal corporate offers. |
| `placement.manage_outcomes` | Authority to confirm final graduate placement outcomes and CTC packages. |
| `placement.view_reports` | Authority to view institution-wide and department-level placement intelligence. |

---

## 3. Role-Based Access Matrix

| Operational Capability | Admin | Placement Officer | HOD | Faculty Coordinator | Student |
| :--- | :---: | :---: | :---: | :---: | :---: |
| View Operations Dashboard | ✔ | ✔ | ✔ (Dept) | ✔ | ✖ |
| View Student "My Placement" | ✔ | ✔ | ✖ | ✖ | ✔ |
| Onboard Corporate Partners | ✔ | ✔ | ✖ | ✖ | ✖ |
| Configure Job Drives | ✔ | ✔ | ✖ | ✖ | ✖ |
| Publish Recruitment Drives | ✔ | ✔ | ✖ | ✖ | ✖ |
| Define Positions & Slabs | ✔ | ✔ | ✖ | ✖ | ✖ |
| Override Eligibility | ✔ | ✔ | ✖ | ✖ | ✖ |
| Review Applications | ✔ | ✔ | ✔ (Dept) | ✔ (Assigned) | ✖ |
| Execute Shortlists | ✔ | ✔ | ✖ | ✖ | ✖ |
| Schedule Interviews | ✔ | ✔ | ✖ | ✔ | ✖ |
| Submit Panel Evaluation | ✔ | ✔ | ✖ | ✔ (Panel) | ✖ |
| Issue Corporate Offers | ✔ | ✔ | ✖ | ✖ | ✖ |
| Accept / Decline Offer | ✖ | ✖ | ✖ | ✖ | ✔ (Own) |
| Confirm Final Placement | ✔ | ✔ | ✖ | ✖ | ✖ |
| View Institutional Reports | ✔ | ✔ | ✔ (Dept) | ✖ | ✖ |

---

## 4. Student Role Boundaries (Strict Prohibitions)

The student experience is strictly sandboxed. Candidate users:
- **CANNOT** edit corporate partner records or view internal recruiter contacts.
- **CANNOT** modify job drive configurations or alter eligibility cutoff criteria.
- **CANNOT** self-shortlist or modify application statuses.
- **CANNOT** alter interview scores or view internal panel evaluators' confidential notes.
- **CANNOT** fabricate or issue job offers.
- **CANNOT** modify placement outcomes or alter compensation figures in the ledger.
- **CAN** view eligible drives matching their verified academic profile.
- **CAN** submit applications to open drives before the deadline.
- **CAN** update permitted personal skills and view verified resume status.
- **CAN** view their interview timings, modes, and meeting links.
- **CAN** formally Accept or Decline extended offers within the response window.
