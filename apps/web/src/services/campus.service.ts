import { ApiResponse } from "@campusos/types";
import {
  EventItem,
  ClubItem,
  AnnouncementItem,
  NotificationItem,
  MOCK_EVENTS,
  MOCK_CLUBS,
  MOCK_ANNOUNCEMENTS,
  MOCK_NOTIFICATIONS,
} from "@/mocks/campus.mock";

class CampusService {
  private events: EventItem[] = [...MOCK_EVENTS];
  private clubs: ClubItem[] = [...MOCK_CLUBS];
  private announcements: AnnouncementItem[] = [...MOCK_ANNOUNCEMENTS];
  private notifications: NotificationItem[] = [...MOCK_NOTIFICATIONS];

  async getEvents(): Promise<ApiResponse<EventItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.events };
  }

  async getEventById(id: string): Promise<ApiResponse<EventItem | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const ev = this.events.find((e) => e.id === id) || null;
    return { success: true, data: ev };
  }

  async getClubs(): Promise<ApiResponse<ClubItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.clubs };
  }

  async getClubById(id: string): Promise<ApiResponse<ClubItem | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const club = this.clubs.find((c) => c.id === id) || null;
    return { success: true, data: club };
  }

  async getAnnouncements(): Promise<ApiResponse<AnnouncementItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.announcements };
  }

  async getNotifications(): Promise<ApiResponse<NotificationItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.notifications };
  }

  async markNotificationAsRead(id: string): Promise<ApiResponse<{ success: boolean }>> {
    const notif = this.notifications.find((n) => n.id === id);
    if (notif) notif.isRead = true;
    return { success: true, data: { success: true } };
  }

  async markAllNotificationsAsRead(): Promise<ApiResponse<{ count: number }>> {
    this.notifications.forEach((n) => (n.isRead = true));
    return { success: true, data: { count: this.notifications.length } };
  }
}

export const campusService = new CampusService();
