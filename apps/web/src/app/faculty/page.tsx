import { redirect } from "next/navigation";

export default function FacultyPortalEntryPage() {
  redirect("/login?role=faculty");
}

