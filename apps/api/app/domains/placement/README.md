# Placement Domain (`app/domains/placement`)

## Purpose

Orchestrates campus recruitment drives, company relationships, automated criteria checks, interview stages, and placement offers.

## Key Entities

- `CorporatePartner`
- `JobDrive`
- `EligibilityRule` (Min CGPA, Max backlogs, Min attendance)
- `StudentApplication`
- `InterviewStage`
- `PlacementOffer`

## Boundaries & Constraints

- Evaluates student eligibility by querying Examination (CGPA, backlogs) and Attendance (presence %), never storing redundant copies of academic records.
