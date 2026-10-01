export interface EventItem {
  id: string;
  title: string;
  category: "TECHNICAL" | "CULTURAL" | "SPORTS" | "ACADEMIC" | "WORKSHOP";
  description: string;
  venue: string;
  startDate: string;
  endDate: string;
  organizer: string;
  registeredCount: number;
  capacity: number;
  status: "UPCOMING" | "ONGOING" | "COMPLETED" | "CANCELLED";
}

export interface ClubItem {
  id: string;
  name: string;
  code: string;
  category: "TECHNICAL" | "CULTURAL" | "LITERARY" | "SPORTS";
  leadName: string;
  facultyAdvisor: string;
  membersCount: number;
  establishedYear: number;
  status: "ACTIVE" | "INACTIVE";
}

export interface AnnouncementItem {
  id: string;
  title: string;
  category: "ACADEMIC" | "EXAMINATION" | "HOSTEL" | "GENERAL" | "URGENT";
  content: string;
  publishedAt: string;
  author: string;
  audience: "ALL" | "STUDENTS" | "FACULTY" | "STAFF";
  isPinned: boolean;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: "ACADEMIC" | "FINANCE" | "ATTENDANCE" | "PLACEMENT" | "SECURITY";
  timestamp: string;
  isRead: boolean;
  link?: string;
}

export const MOCK_EVENTS: EventItem[] = [
  {
    id: "evt-01",
    title: "HackCampus 2026: 36-Hour National Autonomous Hackathon",
    category: "TECHNICAL",
    description: "Annual university flagship hackathon focused on distributed systems, AI campus utilities, and edge computing.",
    venue: "Main Indoor Sports Complex & CS Labs",
    startDate: "2026-10-16 09:00 AM",
    endDate: "2026-10-17 09:00 PM",
    organizer: "Association of Computer Engineers (ACE)",
    registeredCount: 380,
    capacity: 450,
    status: "UPCOMING",
  },
  {
    id: "evt-02",
    title: "Symposium on Scalable High-Performance Architecture",
    category: "ACADEMIC",
    description: "Keynote talks by distinguished researchers from IISc Bangalore and Industry leaders.",
    venue: "Sir C. V. Raman Memorial Auditorium",
    startDate: "2026-10-22 10:00 AM",
    endDate: "2026-10-22 04:30 PM",
    organizer: "Dean Academics & Dept of CSE",
    registeredCount: 195,
    capacity: 250,
    status: "UPCOMING",
  },
];

export const MOCK_CLUBS: ClubItem[] = [
  {
    id: "club-ace",
    name: "Association of Computer Engineers",
    code: "ACE",
    category: "TECHNICAL",
    leadName: "Aarav Patel",
    facultyAdvisor: "Dr. Rajesh Sharma",
    membersCount: 165,
    establishedYear: 2012,
    status: "ACTIVE",
  },
  {
    id: "club-robotics",
    name: "Autonomous Robotics & Embedded Systems Club",
    code: "ROBO",
    category: "TECHNICAL",
    leadName: "Vikramaditya Rao",
    facultyAdvisor: "Dr. Ananya Mukherjee",
    membersCount: 88,
    establishedYear: 2016,
    status: "ACTIVE",
  },
  {
    id: "club-cultural",
    name: "Dhwani Cultural & Fine Arts Guild",
    code: "DHWANI",
    category: "CULTURAL",
    leadName: "Priya Sundaram",
    facultyAdvisor: "Prof. Savita Hebbar",
    membersCount: 140,
    establishedYear: 2010,
    status: "ACTIVE",
  },
];

export const MOCK_ANNOUNCEMENTS: AnnouncementItem[] = [
  {
    id: "anc-01",
    title: "Schedule for Continuous Internal Assessment (CIA-1) Published",
    category: "EXAMINATION",
    content: "All undergraduate and postgraduate students are requested to inspect the official CIA-1 timetable commencing 12th October 2026.",
    publishedAt: "Today, 08:30 AM",
    author: "Controller of Examinations",
    audience: "STUDENTS",
    isPinned: true,
  },
  {
    id: "anc-02",
    title: "Cisco Systems On-Campus Recruitment Drive: Shortlisted Candidates",
    category: "ACADEMIC",
    content: "Round 2 Technical Interview schedules for Cisco Systems have been assigned. Selected students must report to Placement Suite 201.",
    publishedAt: "Yesterday, 05:00 PM",
    author: "Head of Corporate Relations",
    audience: "STUDENTS",
    isPinned: true,
  },
  {
    id: "anc-03",
    title: "Central Library Extended Hours During Mid-Semester Evaluations",
    category: "GENERAL",
    content: "Central Library reading rooms will remain accessible until 11:00 PM daily throughout the examination period.",
    publishedAt: "28 Sep 2026",
    author: "Chief Librarian",
    audience: "ALL",
    isPinned: false,
  },
];

export const MOCK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-01",
    title: "Attendance Session CS301 Marked",
    message: "Your attendance was verified as PRESENT for CS301 Data Structures at 10:15 AM.",
    category: "ATTENDANCE",
    timestamp: "10 mins ago",
    isRead: false,
    link: "/app/attendance",
  },
  {
    id: "notif-02",
    title: "Placement Round 2 Scheduled",
    message: "Interview time confirmed: Cisco Systems, Room 204 at 02:30 PM tomorrow.",
    category: "PLACEMENT",
    timestamp: "1 hour ago",
    isRead: false,
    link: "/app/placement",
  },
  {
    id: "notif-03",
    title: "Fee Receipt #REC-2026-0912 Ready",
    message: "Your tuition fee receipt has been digitally stamped and archived in your Document Vault.",
    category: "FINANCE",
    timestamp: "Yesterday",
    isRead: true,
    link: "/app/finance/receipts",
  },
  {
    id: "notif-04",
    title: "CIA-1 Schedule Published",
    message: "Continuous Internal Assessment timetable has been released by Exam Cell.",
    category: "ACADEMIC",
    timestamp: "2 days ago",
    isRead: true,
    link: "/app/examinations/schedules",
  },
];
