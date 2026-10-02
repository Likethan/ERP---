# CampusOS — Timetable Scheduling & Matrix Documentation

## 1. Overview & Architecture

The **Timetable Scheduling Module** (`/app/academics/timetable`) is the real-time operational calendar of CampusOS. It orchestrates class scheduling across time, faculty instructors, student sections, and physical campus infrastructure.

### Scheduling Coordinates
Every scheduled period occupies a discrete 4-dimensional point:
$$\text{Entry} = (\text{Time Slot}, \text{Day of Week}, \text{Course Offering}, \text{Physical Room})$$

Where `Course Offering` inherently specifies:
$$\text{Course Offering} \implies (\text{Subject}, \text{Section Cohort}, \text{Primary Faculty})$$

---

## 2. Master Time Slot Topology

The system defines an 8-period institutional day structure:

| Slot # | Period Name | Time Window | Type | Operational Context |
| :---: | :--- | :---: | :---: | :--- |
| `P1` | Period 1 | `08:30 — 09:20` | `THEORY` | Morning lecture block 1 |
| `P2` | Period 2 | `09:20 — 10:10` | `THEORY` | Morning lecture block 2 |
| `P3` | Period 3 | `10:30 — 11:20` | `THEORY` | Mid-morning lecture block 1 (post-morning tea) |
| `P4` | Period 4 | `11:20 — 12:10` | `THEORY` | Mid-morning lecture block 2 |
| `LUNCH` | Lunch Break | `12:10 — 01:10` | `BREAK` | Non-schedulable institutional recess |
| `P5` | Period 5 | `01:10 — 02:00` | `LAB` / `THEORY` | Afternoon session / Lab practical block start |
| `P6` | Period 6 | `02:00 — 02:50` | `LAB` / `THEORY` | Afternoon session / Lab practical block middle |
| `P7` | Period 7 | `03:00 — 03:50` | `LAB` / `TUTORIAL` | Afternoon session / Lab practical block end |
| `P8` | Period 8 | `03:50 — 04:40` | `TUTORIAL` / `SEMINAR` | Remedial, mentoring, or library seminar |

---

## 3. Perspectives & Multi-Facet Views

The Timetable UI enables dynamic pivot filtering across four operational views:

### 3.1 By Section (Student Class Schedule)
- Select academic department (e.g. `Computer Science`) and section (e.g. `Section A`).
- Renders the exact weekly sequence of subjects, instructors, and rooms for students in that cohort.
- Directly exported or consumed by student portal views.

### 3.2 By Faculty (Instructor Workload & Free Periods)
- Select an individual faculty member (e.g. `Dr. Rajesh Kumar`).
- Highlights all assigned lecture and lab periods across all sections and departments.
- Visually surfaces non-teaching "Free Periods" to assist HODs in scheduling office hours, mentoring sessions, and departmental committee meetings.

### 3.3 By Room / Venue (Space Utilization & Contention)
- Filter by lecture hall or lab venue (e.g. `LH-101`, `CS-Lab-2`, `Audi-1`).
- Provides campus facility managers and HODs with real-time room occupancy maps.
- Highlights empty rooms available for extra classes, workshops, or exams.

### 3.4 Day View vs. Full Week Matrix
- **Full Week Matrix (Desktop / Tablet)**: Displays Monday through Saturday columns side-by-side with sticky slot rows.
- **Day View (Mobile / Smartphone)**: Offers single-day tab switching (`Mon`, `Tue`, `Wed`, etc.) preventing unreadable horizontal squeeze.

---

## 4. Conflict Detection & Visual Collision Engine

The frontend incorporates a preliminary collision detection algorithm (`recalculateConflicts`) that inspects scheduled entries for physical impossibilities:

### 4.1 Conflict Types
1. **`FACULTY_CONFLICT`**:
   $$\text{Entry}_A.\text{facultyId} == \text{Entry}_B.\text{facultyId} \land \text{Entry}_A.\text{day} == \text{Entry}_B.\text{day} \land \text{Entry}_A.\text{slotId} == \text{Entry}_B.\text{slotId}$$
   *Trigger*: The same professor is scheduled to teach two different classes at the exact same hour.
2. **`ROOM_CONFLICT`**:
   $$\text{Entry}_A.\text{room} == \text{Entry}_B.\text{room} \land \text{Entry}_A.\text{day} == \text{Entry}_B.\text{day} \land \text{Entry}_A.\text{slotId} == \text{Entry}_B.\text{slotId}$$
   *Trigger*: Two different course offerings or sections are assigned to the exact same lecture hall or laboratory.
3. **`SECTION_CONFLICT`**:
   $$\text{Entry}_A.\text{section} == \text{Entry}_B.\text{section} \land \text{Entry}_A.\text{day} == \text{Entry}_B.\text{day} \land \text{Entry}_A.\text{slotId} == \text{Entry}_B.\text{slotId}$$
   *Trigger*: A student section is double-booked for two concurrent subjects.

### 4.2 Visual Conflict States
- **Card Highlighting**: Conflicting timetable cards receive a pulsing red border (`border-red-500`), a red background tint (`bg-red-50/50`), and an urgent warning icon.
- **Banner Notification**: The top of the page displays an urgent notification summarizing the detected conflicts with a button to review affected entries.
- **Disclaimer**: The UI explicitly clarifies that frontend conflict detection is a client-side advisory tool and final collision arbitration occurs via backend validation.

---

## 5. Timetable Entry Editor

The interactive Entry Editor modal supports:
- **Offering Selection**: Dropdown linked to active course offerings (auto-populating Subject, Section, and Faculty).
- **Day & Slot Mapping**: Flexible assignment to standard time slots (P1–P8).
- **Room / Venue Assignment**: Text input or dropdown for classrooms and laboratories.
- **Session Type**: Categorization as `THEORY`, `LAB`, or `TUTORIAL`.
- **Live Collision Alerting**: Re-evaluates potential collisions upon entry creation or update.
- **Destructive Deletion**: Safe confirmation before removing a scheduled entry.

---

## 6. Role Behaviors

| Role | Viewing Rights | Editing Rights | Conflict Resolution |
| :--- | :--- | :--- | :--- |
| **Super Admin** | All Departments, Sections, Rooms | Full Create / Update / Delete | Authoritative override |
| **HOD** | Department Sections & Faculty | Department Course Entries | Authoritative for Department |
| **Faculty** | Read-Only (Workload view) | None | Request adjustment from HOD |
| **Student** | Read-Only (Enrolled section) | None | None |
