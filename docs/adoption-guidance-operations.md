# CampusOS Enterprise Product Adoption, Training, In-App Guidance & Change Management (Step 37)

## 1. Overview & Architectural Scope

The **Product Adoption, Training, In-App Guidance & Change Management** module (Step 37) provides an enterprise-grade adoption and enablement framework for CampusOS. As a multi-tenant college ERP SaaS platform serving students, faculty, department heads, finance staff, placement officers, institution administrators, and tenant operators, CampusOS requires structured onboarding, contextual guidance, training compliance, and controlled feature change management.

### Key Capabilities
1. **Role-Aware Adoption Journeys**: Structured, multi-step checklists tailored to specific user roles (e.g., student profile & timetable discovery, faculty attendance & gradebook onboarding, finance ledger setup).
2. **Training Programs & Learning Assignments**: Lightweight learning path orchestration supporting text, approved documentation, and external resources with deadline enforcement and certified completion records.
3. **Contextual In-App Guidance**: Route- and semantic-feature-aware tooltips and walkthrough banners with dismiss, snooze, and completion tracking.
4. **Product Announcements & Change Rollouts**: Rich change notices with audience targeting (roles, departments, institutions), priority levels, scheduled publication, and mandatory user read/acknowledgement tracking.
5. **Feature Adoption Milestones & Rollout Analytics**: Server-validated adoption tracking (discovery, first use, repeated use, workflow completion) measuring feature adoption across target cohorts.
6. **Aggregate Analytics & Measurement**: Rigorous metric calculations (journey completion rate, step drop-off analysis, training compliance, announcement acknowledgements) with documented denominators.
7. **Scheduled Processing**: Automated evaluation of training deadlines, reminders, overdue flags, and announcement expirations integrated with the existing scheduler.

---

## 2. Domain Entities & Database Schema

All entities reside in the `adoption` schema and inherit standard multi-tenant isolation principles (`tenant_id`, `created_at`, `updated_at`).

```
                    ┌──────────────────────────────┐
                    │  AdoptionJourneyDefinition   │
                    │  (role, status, version)     │
                    └──────────────┬───────────────┘
                                   │ 1:N
                    ┌──────────────▼───────────────┐
                    │     AdoptionJourneyStep      │
                    │  (step_key, order, criteria) │
                    └──────────────┬───────────────┘
                                   │
                                   │ 1:N (via journey_id & step_id)
                    ┌──────────────▼───────────────┐
                    │     UserJourneyProgress      │
                    │  (user_id, status, progress%)│
                    └──────────────────────────────┘

┌──────────────────────────────┐        ┌──────────────────────────────┐
│       TrainingProgram        │        │      ContextualGuidance      │
│  (title, role, duration)     │        │  (route_pattern, step_order) │
└──────────────┬───────────────┘        └──────────────┬───────────────┘
               │ 1:N                                   │ 1:N
┌──────────────▼───────────────┐        ┌──────────────▼───────────────┐
│        TrainingModule        │        │      UserGuidanceState       │
│  (type, resource_url, est_min)       │  (dismissed, completed_at)    │
└──────────────┬───────────────┘        └──────────────────────────────┘
               │ 1:N
┌──────────────▼───────────────┐        ┌──────────────────────────────┐
│      TrainingAssignment      │        │      ProductAnnouncement     │
│  (due_date, certified, score)│        │  (priority, scheduled_at)    │
└──────────────────────────────┘        └──────────────┬───────────────┘
                                                       │ 1:N
┌──────────────────────────────┐        ┌──────────────▼───────────────┐
│    FeatureAdoptionTarget     │        │    UserAnnouncementReceipt   │
│  (feature_key, target_pct)   │        │  (acknowledged, ack_notes)   │
└──────────────┬───────────────┘        └──────────────────────────────┘
               │ 1:N
┌──────────────▼───────────────┐
│   FeatureAdoptionMilestone   │
│  (milestone_type, metadata)  │
└──────────────────────────────┘
```

### Table Definitions
- `adoption_journey_definitions`: Journey configurations scoped to tenant, institution, and target role (`JourneyStatus`: `draft`, `published`, `archived`, `deprecated`).
- `adoption_journey_steps`: Ordered milestone steps with completion criteria (`manual_confirmation`, `route_navigation`, `action_verified`, `external_certification`).
- `user_journey_progress`: User-level completion state tracking started, completed, and current step index with persistent progress percentages.
- `training_programs`: Learning path bundles with target roles, validity durations, and certificate eligibility.
- `training_modules`: Individual educational items (text instructions, CampusOS docs, approved external URLs).
- `training_assignments`: User enrollments with due dates, completion verification, and certificate hashes.
- `contextual_guidance`: Semantic route-matched guidance items with target role filters and optional/mandatory enforcement.
- `user_guidance_states`: Per-user guidance interaction history (impressions, dismissals, completions).
- `product_announcements`: Change notices and broadcast alerts with scheduled publication, target roles, departments, and acknowledgement requirements.
- `user_announcement_receipts`: Read receipts and cryptographic/timestamped acknowledgements.
- `feature_adoption_targets`: Rollout adoption targets with target percentage, target dates, and feature keys.
- `feature_adoption_milestones`: Server-validated telemetry recording discovery, first use, and repeated usage.

---

## 3. Role-Aware Journeys & Seed Data

The platform comes with standard seed journeys for standard CampusOS roles:

| Role | Journey Code | Focus Areas | Key Steps |
|---|---|---|---|
| **Student** | `student_onboarding_v1` | Profile, Schedule, Fees, Exams | 1. Complete Profile<br>2. Discover Timetable<br>3. Check Fee Invoices<br>4. Review Placement Readiness |
| **Faculty** | `faculty_onboarding_v1` | Classes, Attendance, Gradebook | 1. Review Course Allocations<br>2. Configure Attendance Rules<br>3. Initialize Gradebook Assessment |
| **Finance Staff** | `finance_onboarding_v1` | Ledgers, Invoicing, Reconciliation | 1. Fee Structure Review<br>2. Payment Gateway Reconciliation<br>3. Generate Arrears Report |
| **Institution Admin** | `admin_onboarding_v1` | Users, Permissions, Integrations | 1. Verify Academic Term<br>2. Audit Staff RBAC Permissions<br>3. Check Service Desk SLA Rules |

Administrators can seed default templates via `POST /api/v1/adoption/journeys/seed-defaults`.

---

## 4. API Endpoints & Permissions Reference

All endpoints are authenticated and enforce tenant isolation through `get_current_active_user`.

### User-Facing Endpoints
| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `GET` | `/api/v1/adoption/journeys/my` | List published journeys applicable to the authenticated user's role | All authenticated |
| `POST` | `/api/v1/adoption/journeys/{journey_id}/start` | Initialize or resume progress on a journey | All authenticated |
| `POST` | `/api/v1/adoption/journeys/{journey_id}/steps/{step_id}/complete` | Mark a journey step as completed | All authenticated |
| `GET` | `/api/v1/adoption/training/my` | View assigned training programs and completion status | All authenticated |
| `POST` | `/api/v1/adoption/training/assignments/{assignment_id}/complete` | Submit completion verification for training | All authenticated |
| `GET` | `/api/v1/adoption/guidance/contextual` | Retrieve guidance tooltips for current route | All authenticated |
| `POST` | `/api/v1/adoption/guidance/{guidance_id}/interact` | Record impression, dismissal, or completion of guidance | All authenticated |
| `GET` | `/api/v1/adoption/announcements/active` | Get active announcements targeted to current user | All authenticated |
| `POST` | `/api/v1/adoption/announcements/{announcement_id}/acknowledge` | Submit mandatory acknowledgement or read receipt | All authenticated |
| `POST` | `/api/v1/adoption/features/milestones` | Record verified feature usage milestone | All authenticated |

### Administrative & Reporting Endpoints
| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `GET` | `/api/v1/adoption/journeys` | List all journey definitions with step counts | Admin, Staff |
| `POST` | `/api/v1/adoption/journeys` | Create new draft journey definition | Admin |
| `POST` | `/api/v1/adoption/journeys/{journey_id}/steps` | Append step to journey | Admin |
| `POST` | `/api/v1/adoption/journeys/{journey_id}/publish` | Publish journey and optionally notify eligible users | Admin |
| `POST` | `/api/v1/adoption/training/programs` | Create training program and learning modules | Admin, Faculty |
| `POST` | `/api/v1/adoption/training/programs/{program_id}/assign` | Assign training program to user with due date | Admin |
| `POST` | `/api/v1/adoption/guidance` | Author contextual in-app guidance for route | Admin |
| `POST` | `/api/v1/adoption/announcements` | Author, schedule, or publish announcements | Admin |
| `POST` | `/api/v1/adoption/features/targets` | Configure feature adoption targets | Admin |
| `GET` | `/api/v1/adoption/analytics/overview` | Fetch aggregate adoption dashboard metrics | Admin, Staff |

---

## 5. Adoption Analytics & Metric Definitions

Adoption metrics avoid vanity counters by using rigorous, verifiable denominators:

1. **Journey Completion Rate**:
   $$\text{Completion Rate} = \frac{\text{Users who completed all required steps}}{\text{Users who started or were assigned the journey}} \times 100$$
2. **Step Drop-Off Rate**:
   $$\text{Drop-Off at Step } i = \frac{\text{Users completing step } i - \text{Users completing step } i+1}{\text{Users completing step } i} \times 100$$
3. **Training Compliance Rate**:
   $$\text{Training Compliance} = \frac{\text{Completed Assignments with verified completion}}{\text{Total Active Assignments}} \times 100$$
4. **Announcement Acknowledgement Rate**:
   $$\text{Ack Rate} = \frac{\text{Unique User Receipts with } \text{acknowledged}=\text{True}}{\text{Eligible Target User Cohort}} \times 100$$
5. **Feature Adoption Percentage**:
   $$\text{Feature Adoption} = \frac{\text{Unique Users with recorded milestones for } \text{feature\_key}}{\text{Total Active Users in Target Role}} \times 100$$

---

## 6. Scheduled Jobs & Background Processing

Step 37 registers the `evaluate_adoption_deadlines_and_expirations` job handler in `apps/api/app/scheduler.py`.

### Execution Cadence
- **Frequency**: Runs hourly in production (`every(1).hours`).
- **Idempotency**: All notification generation checks existing delivery history to avoid duplicate emails/in-app notifications.

### Sweeper Tasks
1. **Training Reminders & Overdue Tracking**:
   - Queries `TrainingAssignment` where `status in ('assigned', 'in_progress')`.
   - If `due_date < now()` and `status != 'overdue'`: transitions status to `overdue` and fires notification.
   - If `due_date <= now() + 48h` and reminder not sent: emits `training_deadline_approaching` notification.
2. **Announcement Lifecycle**:
   - Publishes `scheduled` announcements whose `scheduled_at <= now()`.
   - Expires `published` announcements whose `expires_at <= now()`.

---

## 7. Migration & Rollback Guide

### Applying Migrations
```powershell
cd "apps/api"
poetry run alembic upgrade head
```

### Validating Current Revision
```powershell
poetry run alembic current
# Expected output: 023_enterprise_product_adoption_training_guidance (head)
```

### Rollback Procedure
If required, roll back Step 37 migration safely to Step 36 (`022_enterprise_customer_support_service_desk`):
```powershell
cd "apps/api"
poetry run alembic downgrade -1
```
The downgrade script cleanly drops all 12 tables in reverse dependency order and removes the associated PostgreSQL ENUM types.
