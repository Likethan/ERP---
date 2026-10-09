# CampusOS Authoritative Metric Definitions

## Canonical Business Formulas
CampusOS enforces a centralized Metric Registry to guarantee formula consistency across dashboards, reports, and AI query tools.

| Metric | Domain | Data Type | Canonical Formula |
| :--- | :--- | :--- | :--- |
| `total_students` | People | Integer | `COUNT(DISTINCT student.id)` |
| `active_students` | People | Integer | `COUNT(DISTINCT student.id WHERE status = 'ACTIVE')` |
| `faculty_count` | People | Integer | `COUNT(DISTINCT faculty.id WHERE employment_status = 'ACTIVE')` |
| `attendance_percentage` | Attendance | Percentage (%) | `(SUM(PRESENT + EXCUSED + 0.5*LATE) / TOTAL_SESSIONS) * 100` |
| `students_below_threshold` | Attendance | Integer | `COUNT(DISTINCT student.id HAVING attendance_pct < 75.0)` |
| `pass_percentage` | Examinations | Percentage (%) | `(COUNT(PASS_STUDENTS) / TOTAL_CANDIDATES) * 100` |
| `average_score` | Examinations | Decimal | `AVG(marks_obtained)` |
| `total_invoiced` | Finance | Currency (INR) | `SUM(invoice.net_payable)` |
| `total_collected` | Finance | Currency (INR) | `SUM(payment.amount WHERE status = 'SUCCESS')` |
| `total_outstanding` | Finance | Currency (INR) | `SUM(invoice.balance_amount WHERE status != 'PAID')` |
| `fee_collection_rate` | Finance | Percentage (%) | `(total_collected / total_invoiced) * 100` |
| `overdue_amount` | Finance | Currency (INR) | `SUM(balance_amount WHERE due_date < NOW() AND balance > 0)` |
| `eligible_students` | Placement | Integer | `COUNT(DISTINCT student.id WHERE status = 'ACTIVE')` |
| `placement_offers` | Placement | Integer | `COUNT(DISTINCT offer.id WHERE status IN ('OFFERED', 'ACCEPTED'))` |
| `placement_rate` | Placement | Percentage (%) | `(placed_students / eligible_students) * 100` |
| `hostel_occupancy_rate` | Infrastructure | Percentage (%) | `(OCCUPIED_BEDS / TOTAL_BEDS) * 100` |
| `document_compliance_rate` | Documents | Percentage (%) | `(VERIFIED_DOCS / TOTAL_DOCS) * 100` |
