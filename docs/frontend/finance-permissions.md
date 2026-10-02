# CampusOS — Finance Role-Based Access Control (RBAC) Matrix

This document defines the security permissions and access authorization matrix across user roles in the Finance, Fees & Billing module.

---

## 1. Role Definitions

- **SUPER_ADMIN**: Full administrative and financial control across the institution.
- **ACCOUNTS_OFFICER**: Operational cashier and accountant responsible for billing, recording payments, managing student fee assignments, and issuing receipts.
- **HOD (Head of Department)**: Department head with read-only visibility into departmental student dues and course fees, but prohibited from direct transaction recording.
- **FACULTY**: Academic instructor with no access to financial records.
- **STUDENT**: Self-service student role restricted exclusively to viewing their own invoices, payment receipts, and applied scholarship concessions.

---

## 2. Permissions Matrix

| Functional Capability | Super Admin | Accounts Officer | HOD | Student |
| :--- | :---: | :---: | :---: | :---: |
| **View Institutional Financial Dashboard** | ✅ | ✅ | ❌ | ❌ |
| **Manage Fee Categories (Create/Edit/Status)** | ✅ | ✅ | ❌ | ❌ |
| **Create Fee Structures (6-Step Wizard)** | ✅ | ✅ | ❌ | ❌ |
| **Approve / Activate Fee Structures** | ✅ | ❌ | ❌ | ❌ |
| **Assign Fee Structures to Students** | ✅ | ✅ | ❌ | ❌ |
| **Generate & Cancel Invoices** | ✅ | ✅ | ❌ | ❌ |
| **Record Inbound Payments & Allocations** | ✅ | ✅ | ❌ | ❌ |
| **Issue & Print Official Receipts** | ✅ | ✅ | ❌ | ❌ |
| **Create Scholarship Schemes** | ✅ | ✅ | ❌ | ❌ |
| **Approve Scholarship Grants** | ✅ | ❌ | ❌ | ❌ |
| **Review & Approve Refund Petitions** | ✅ | ❌ | ❌ | ❌ |
| **Process Electronic Refund Disbursement**| ✅ | ✅ | ❌ | ❌ |
| **Generate & Export Financial Audit Reports**| ✅ | ✅ | ❌ | ❌ |
| **View "My Finance" (Personal Dues & Invoices)** | ❌ | ❌ | ❌ | ✅ |
| **Download Personal Payment Receipts** | ❌ | ❌ | ❌ | ✅ |

---

## 3. Student Self-Service Separation

When a user logged in as `STUDENT` navigates to `/app/finance`:
1. The dashboard automatically switches into **"My Student Account"** mode.
2. Executive institution metrics (total campus collection, aging debt bars, operational action queues) are hidden.
3. The student sees:
   - Personal Total Outstanding dues.
   - Active Semester Invoices with status badges (`PAID`, `PARTIALLY_PAID`, `OVERDUE`).
   - Official Payment Receipts available for instant browser printing and PDF generation.
   - Active Scholarship Concessions granted to their student record.

---

## 4. UI Safeguards & Enforcement

- **Button Disablement**: Interactive buttons for `Record Payment`, `Approve Refund`, `Activate Fee Structure`, and `Cancel Invoice` are conditionally rendered or disabled based on `hasPermission(...)`.
- **Global Search Filtering**: Financial transactions and audit logs are filtered from search results for unauthorized roles.
- **Navigation Guard**: In `sidebar.tsx`, institutional finance submodules are hidden from users with the student role.
