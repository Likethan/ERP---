import { redirect } from "next/navigation";

export default function StudentPortalEntryPage() {
  redirect("/login?role=student");
}
