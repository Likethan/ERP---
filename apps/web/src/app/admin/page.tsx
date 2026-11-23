import { redirect } from "next/navigation";

export default function AdminPortalEntryPage() {
  redirect("/login?role=admin");
}
