# CampusOS — Notification Center & Communication Preferences

## 1. Overview

The **Notification Center** aggregates operational alerts, academic notices, financial payment reminders, placement interview schedules, and campus event passes into a centralized, actionable inbox.

---

## 2. Notification Model

Every notification item maintains:
- `id`: Unique identifier
- `title`: Short summary header
- `message`: Contextual description
- `category`: `ACADEMIC`, `FINANCE`, `PLACEMENT`, `EVENT`, `CLUB`, `SYSTEM`, `GENERAL`
- `priority`: `URGENT`, `HIGH`, `NORMAL`, `LOW`
- `status`: `UNREAD`, `READ`, `ARCHIVED`
- `relatedEntity`: Polymorphic reference with `type`, `id`, and canonical `url`
- `createdAt` / `readAt`: ISO-8601 timestamps

---

## 3. Deep-Link Resolution Architecture

Every notification contains a direct navigation deep link resolving to the canonical source entity across CampusOS modules:

| Category | Example Trigger | Target Route |
| :--- | :--- | :--- |
| `FINANCE` | Tuition fee invoice overdue reminder | `/app/finance` |
| `PLACEMENT` | Technical interview scheduled with Microsoft | `/app/placement/drives/drv-01` |
| `EVENT` | HackCampus registration pass confirmed | `/app/campus/events/evt-01` |
| `CLUB` | ACE Club membership application approved | `/app/campus/clubs/club-ace` |
| `ACADEMIC` | End-semester examination timetable released | `/app/campus/announcements/anc-01` |
| `SYSTEM` | Two-factor security preference updated | `/app/campus/preferences` |

---

## 4. Topbar Notification Bell & Drawer

- **Dynamic Badge**: Computes real-time unread alerts using pure calculator `calculateUnreadNotificationCount()`.
- **Slide-Over Drawer**:
  - Filter tabs: `All` vs `Unread`
  - 1-Click "Mark All as Read"
  - Categorical visual cues (Lucide icons and thematic color badges)
  - Direct CTA to navigate to full inbox `/app/campus/notifications`

---

## 5. Communication Preferences Matrix

Located at `/app/campus/preferences`:

Users can configure delivery channels across all 6 core categories:
1. `Academic Notifications`
2. `Finance Notifications`
3. `Placement Notifications`
4. `Events & Activities`
5. `Clubs & Societies`
6. `System & Security Alerts`

### Available Channels
- **In-App** (Mandatory for critical system security alerts)
- **Email** (Daily digest or instant message)
- **SMS** (Urgent alerts and OTP verification)
- **Push** (Mobile app notifications)

All preference toggles are persisted in memory through `campusService.updateNotificationPreferences()`.
